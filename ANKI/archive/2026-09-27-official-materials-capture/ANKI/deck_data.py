#!/usr/bin/env python3
"""Load capture records, curated card data and source snapshots for the deck builders."""

from __future__ import annotations

import html
import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANKI = ROOT / "ANKI"
LESSONS_FILE = ANKI / "lesson-vocabulary.json"
VOCABULARY_CARDS_FILE = ANKI / "vocabulary-cards.json"
ARTICLES_CARDS_FILE = ANKI / "articles-cards.json"
SENTENCES_FILE = ANKI / "sentence-sources.json"
APPROVALS_FILE = ANKI / "review" / "approvals.json"
LEGACY_V2_FILE = ANKI / "archive" / "2026-09-25-pre-v3" / "ANKI" / "lesson-vocabulary.json"
GLOSS_SNAPSHOT_FILE = ANKI / "gloss-snapshot.json"

BLANK = "＿＿＿"
ARTICLE_RE = re.compile(r"^(der|die|das)\s+(.+)$")
PLACEHOLDER_RE = re.compile(r"\((?:etwas|jemanden|jemandem)\)\s*|^(?:etwas|jemanden|jemandem)\s+")
GENDER_ARTICLE = {"m": "der", "f": "die", "n": "das"}
ARTICLE_GENDER = {value: key for key, value in GENDER_ARTICLE.items()}
POS_INSTRUCTION = {
    "noun": "Type the German noun (without der/die/das)",
    "verb": "Type the German verb (infinitive)",
}
ORIGIN_LABEL = {
    "dw-glossary": "official glossary", "learner-notes": "your notes", "dw-culture-page": "DW culture page",
    "vhs-wordlist": "VHS word list", "vhs-vocabulary-trainer": "VHS vocabulary trainer (English)", "easy-german-video": "Easy German video",
}


class DataError(RuntimeError):
    pass


def normalize(text: str) -> str:
    """Comparison form: NFC, plain quotes/apostrophes/dashes, single spaces."""
    text = unicodedata.normalize("NFC", html.unescape(text))
    text = text.translate(str.maketrans({"’": "'", "‘": "'", "‚": "'", "„": '"', "“": '"', "”": '"', "–": "-", "—": "-",
                                         " ": " ", "…": "..."}))
    return re.sub(r"\s+", " ", text).strip()


def typed_form(text: str) -> str:
    """Typed answers use the apostrophe of the German Mac keyboard (Shift+#); everything else stays strict."""
    return text.replace("’", "'").strip()


@dataclass
class Lesson:
    course: dict
    record: dict
    order: int

    @property
    def id(self) -> str:
        return self.record["id"]

    @property
    def label(self) -> str:
        course, lesson = self.course, self.record
        if course["id"] == "dw-nicos-weg":
            return f"DW Nicos Weg {lesson['level']} · {lesson['title']} (E{lesson['unit']} L{lesson['lesson']})"
        if course["id"] == "vhs-lernportal":
            return f"VHS {lesson['level']} · {lesson['title']}"
        return f"{course['title']} · {lesson['title']}"


@dataclass
class Entry:
    lesson: Lesson
    raw: dict

    @property
    def ref(self) -> str:
        return f"{self.lesson.id}:{self.raw['id']}"

    @property
    def lemma(self) -> str:
        return self.raw["lemma"]

    @property
    def sense(self) -> str:
        return self.raw["sense"]

    @property
    def pos(self) -> str:
        return self.raw["pos"]

    @property
    def gender(self) -> str | None:
        match = ARTICLE_RE.match(self.raw["german"])
        return ARTICLE_GENDER[match.group(1)] if match else None


@dataclass
class Snapshots:
    texts: dict[tuple[str, str], str] = field(default_factory=dict)
    labels: dict[tuple[str, str], str] = field(default_factory=dict)

    def contains(self, lesson_id: str, source_id: str, text: str) -> bool:
        haystack = self.texts.get((lesson_id, source_id))
        return haystack is not None and normalize(text) in haystack


@dataclass
class Data:
    revision: str
    lessons: list[Lesson]
    entries: list[Entry]
    pending: list[tuple[Lesson, dict]]
    vocabulary_cards: dict
    articles_cards: dict
    sentence_cards: list[dict]
    snapshots: Snapshots

    def lesson(self, lesson_id: str) -> Lesson:
        for lesson in self.lessons:
            if lesson.id == lesson_id:
                return lesson
        raise DataError(f"Unknown lesson id: {lesson_id}")

    def entry(self, ref: str) -> Entry:
        for entry in self.entries:
            if entry.ref == ref:
                return entry
        raise DataError(f"Unknown entry reference: {ref}")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gloss_snapshot() -> dict:
    return read_json(GLOSS_SNAPSHOT_FILE)["terms"] if GLOSS_SNAPSHOT_FILE.exists() else {}


def load_snapshots(lessons: list[Lesson]) -> Snapshots:
    snapshots = Snapshots()
    for lesson in lessons:
        path = ROOT / lesson.record["snapshot"]
        if not lesson.record.get("sources"):
            continue
        if not path.exists():
            raise DataError(f"{lesson.id}: missing source snapshot {lesson.record['snapshot']}; run ANKI/harvest_sources.py")
        for source in read_json(path)["sources"]:
            if "lines" in source:
                text = " ".join(source["lines"])
            else:
                items = [t for item in source.get("exercises", []) + source.get("pages", []) for t in item["texts"]]
                text = " ¶ ".join(line for item in items for line in item.split("\n"))
            snapshots.texts[(lesson.id, source["id"])] = normalize(text)
            snapshots.labels[(lesson.id, source["id"])] = source.get("url", "")
    return snapshots


def load() -> Data:
    raw = read_json(LESSONS_FILE)
    if raw.get("schemaVersion") != 3:
        raise DataError("lesson-vocabulary.json must use schemaVersion 3")
    lessons, entries, pending = [], [], []
    for course in raw["courses"]:
        for record in course["lessons"]:
            lesson = Lesson({key: value for key, value in course.items() if key != "lessons"}, record, len(lessons))
            lessons.append(lesson)
            entries.extend(Entry(lesson, item) for item in record.get("entries", []))
            pending.extend((lesson, item) for item in record.get("pendingEntries", []))
    vocabulary = read_json(VOCABULARY_CARDS_FILE) if VOCABULARY_CARDS_FILE.exists() else {"cards": {}}
    articles = read_json(ARTICLES_CARDS_FILE) if ARTICLES_CARDS_FILE.exists() else {"cards": {}}
    sentences = read_json(SENTENCES_FILE)
    if sentences.get("schemaVersion") != 3:
        raise DataError("sentence-sources.json must use schemaVersion 3")
    return Data(raw["revision"], lessons, entries, pending, vocabulary["cards"], articles["cards"],
                sentences["cards"], load_snapshots(lessons))


def lemma_answer(entry: Entry) -> str:
    """The typed target for a Vocabulary card: citation form without article or placeholders."""
    german = entry.raw.get("answer") or entry.raw["german"]
    if entry.pos == "noun" or entry.pos in {"verb", "place"}:
        return typed_form(entry.lemma)
    if entry.raw.get("answer"):
        return typed_form(german)
    if entry.pos == "word" and "," in german:
        return typed_form(entry.lemma)
    return typed_form(PLACEHOLDER_RE.sub("", german))


def display_form(entry: Entry) -> str:
    german = entry.raw["german"]
    if entry.pos == "noun":
        plural = entry.raw.get("plural")
        suffix = "nur Plural" if entry.raw.get("pluralOnly") else plural
        return f"{german}, {suffix}" if suffix and suffix != german else german
    return german


def source_label(entry: Entry) -> str:
    origins = ", ".join(ORIGIN_LABEL.get(origin, origin) for origin in entry.raw.get("origin", []))
    ref = f" {entry.raw['ref']}" if entry.raw.get("ref") else ""
    return f"{entry.lesson.label} — {origins}{ref}"


def course_tag(lesson: Lesson) -> str:
    return f"course::{lesson.course['tag']}"


def context_parts(context: dict, target: str) -> tuple[str, str]:
    """Split a verified context into (front with blank, back with the target in bold)."""
    text = context["text"]
    pattern = re.compile(rf"(?<![\wÄÖÜäöüß]){re.escape(target)}(?![\wÄÖÜäöüß])")
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise DataError(f"Context target {target!r} must occur exactly once in {text!r} (found {len(matches)})")
    start, end = matches[0].span()
    front = html.escape(text[:start]) + f"<span class=gap>{BLANK}</span>" + html.escape(text[end:])
    back = html.escape(text[:start]) + f"<b>{html.escape(target)}</b>" + html.escape(text[end:])
    return front, back


BASE_CSS = """
.card { font-family: -apple-system, "Segoe UI", Roboto, Arial, sans-serif; font-size: 21px; line-height: 1.45;
  text-align: center; color: #1f2328; background: #fbfaf7; padding: 10px; }
.kind { font-size: 12px; letter-spacing: .12em; text-transform: uppercase; color: #8a6d1f; margin-top: 6px; }
.instr { font-size: 13px; color: #6b7280; margin: 4px 0 14px; }
.context { font-size: 25px; font-weight: 600; margin: 8px auto 12px; max-width: 30em; }
.gap { color: #b45309; letter-spacing: .04em; }
.cue { font-size: 19px; color: #374151; margin: 6px auto 16px; max-width: 30em; }
.noun { font-size: 34px; font-weight: 700; margin: 6px 0; }
.display { font-size: 27px; font-weight: 700; margin: 12px auto 6px; }
.filled { font-size: 19px; margin: 6px auto; max-width: 32em; }
.details { font-size: 15px; color: #4b5563; margin: 10px auto; max-width: 34em; text-align: left; display: inline-block; }
.details div { margin: 3px 0; }
.source { font-size: 12px; color: #9ca3af; margin: 14px auto 0; max-width: 40em; }
input#typeans { font-size: 22px; padding: 8px; width: 90%; max-width: 20em; }
.nightMode.card, .night_mode .card { color: #e5e7eb; background: #1f2023; }
.nightMode .cue, .nightMode .details, .night_mode .cue, .night_mode .details { color: #cbd5e1; }
.nightMode .kind, .night_mode .kind { color: #e0b45a; }
.nightMode .gap, .night_mode .gap { color: #f59e0b; }
"""

BACK_TEMPLATE = ("{{FrontSide}}<hr id=answer><div class=display>{{Display}}</div>"
                 "{{#Filled}}<div class=filled>{{Filled}}</div>{{/Filled}}"
                 "{{#Details}}<div class=details>{{Details}}</div>{{/Details}}<div class=source>{{Source}}</div>")


@dataclass
class Card:
    deck: str
    key: str
    fields: dict[str, str]
    covers: list[str]
    lessons: list[str]
    order: tuple
    answer: str
    cue: str
    front_german: str = ""
    tags: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    interferes: list[str] = field(default_factory=list)
    retired: str = ""


def details_html(lines: list[str]) -> str:
    seen, unique = set(), []
    for line in lines:
        if line and line not in seen:
            seen.add(line)
            unique.append(line)
    return "".join(f"<div>{line}</div>" for line in unique)


def context_source(data: "Data", context: dict) -> str:
    lesson = data.lesson(context["lesson"])
    return f"Context: {lesson.label} · {context['source']}"


def verify_context(data: "Data", context: dict, where: str) -> list[str]:
    errors = []
    if "#p" in context.get("text", ""):
        errors.append(f"{where}: context contains an exercise placeholder")
    if not data.snapshots.contains(context.get("lesson", ""), context.get("source", ""), context.get("text", "")):
        errors.append(f"{where}: context is not verbatim in snapshot {context.get('lesson')}/{context.get('source')}: "
                      f"{context.get('text')!r}")
    return errors
