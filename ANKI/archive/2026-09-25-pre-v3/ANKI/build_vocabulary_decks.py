#!/usr/bin/env python3
"""Build curated cumulative and lesson-specific German vocabulary decks."""

from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
import sqlite3
import tempfile
import time
import zipfile
from pathlib import Path

from anki_package_utils import validate_package


ROOT = Path(__file__).resolve().parent.parent
ANKI = ROOT / "ANKI"
LESSONS = ANKI / "lesson-vocabulary.json"
SENTENCE_SOURCES = ANKI / "sentence-sources.json"
INDEX = ANKI / "vocabulary-scan-index.json"
SEP = "\x1f"
ARTICLE_RE = re.compile(r"^(der|die|das)\s+(.+)$")
VERB_PREFIX_RE = re.compile(r"^(?:\((?:etwas|jemanden|jemandem)\)|etwas|jemanden|jemandem)\s+", re.IGNORECASE)


def source_package() -> Path:
    packages = [path for path in ROOT.rglob("*.apkg") if ANKI not in path.parents and ".git" not in path.parts]
    if not packages:
        raise SystemExit("A source .apkg file is needed to create the Anki collection schema.")
    return sorted(packages)[0]


def load_lessons() -> list[dict]:
    return json.loads(LESSONS.read_text(encoding="utf-8"))["lessons"]


def delegated_sentence_answers() -> set[str]:
    if not SENTENCE_SOURCES.exists():
        return set()
    data = json.loads(SENTENCE_SOURCES.read_text(encoding="utf-8"))
    delegated = set()
    for source in data.get("sources", []):
        for card in source.get("cards", []):
            if card.get("kind") == "production":
                delegated.add(semantic_key(card["answer"]))
            elif card.get("kind") == "completion" and card.get("prompt", "").count("____") == 1:
                delegated.add(semantic_key(card["prompt"].replace("____", card["answer"])))
    return delegated


def semantic_key(text: str) -> str:
    return re.sub(r"[\s.!?…]+$", "", text.strip()).casefold()


def include_entry(entry: dict, delegated: set[str]) -> bool:
    german = entry["german"].strip()
    if semantic_key(german) in delegated:
        return False
    if "(a name)" in entry.get("english", "").casefold():
        return False
    if "..." in german or "…" in german:
        return False
    if german in {"Brauchst du?", "Willst du?"}:
        return False
    return True


def classify_entry(entry: dict) -> tuple[str, str]:
    """Return the short typed answer and a learner-facing category."""
    german = entry["german"].strip()
    noun = ARTICLE_RE.match(german)
    if noun:
        return noun.group(2), "noun"
    if german == "ins (in das)":
        return "ins", "contraction"
    without_object = VERB_PREFIX_RE.sub("", german)
    if entry.get("conjugation") or entry.get("english", "").strip().casefold().startswith("to "):
        return without_object, "verb"
    if " " in german or re.search(r"[.!?…]$", german):
        return german, "fixed expression"
    if german.casefold() in {"ich", "du", "er", "sie", "es", "wir", "ihr", "sie", "wer", "das"}:
        return german, "pronoun"
    return german, "word"


def precise_prompt(entry: dict, category: str) -> str:
    if entry.get("prompt"):
        return entry["prompt"]
    meaning = entry["english"].strip().rstrip(".")
    overrides = {
        "auch": "also / too — adding another fact",
        "das": "that — demonstrative pronoun",
        "in dem": "in the — uncontracted dative form",
        "ins (in das)": "into the — contraction of in das",
    }
    if entry["german"] in overrides:
        return overrides[entry["german"]]
    if category == "noun":
        return f"{meaning} — noun; type the German noun without its article"
    if category == "verb":
        return f"{meaning} — type the German infinitive"
    if category == "pronoun":
        return f"{meaning} — pronoun"
    if category == "fixed expression":
        return f"{meaning} — fixed expression"
    return meaning


def prepare_entry(entry: dict, source_ids: list[str], source_titles: list[str]) -> dict:
    answer, category = classify_entry(entry)
    extras = []
    if entry.get("plural"):
        extras.append(f"Plural: {html.escape(entry['plural'])}")
    if entry.get("conjugation"):
        extras.append(f"Source forms: {html.escape(entry['conjugation'])}")
    source_form = entry["german"].strip()
    if source_form != answer:
        extras.insert(0, f"Source form: {html.escape(source_form)}")
    return {
        "key": source_form.casefold(),
        "prompt": precise_prompt(entry, category),
        "answer": answer,
        "german": source_form,
        "english": entry["english"].strip(),
        "extra": "<br>".join(extras),
        "source_ids": source_ids,
        "source": "; ".join(source_titles),
        "category": category,
    }


def merge_entries(lessons: list[dict], delegated: set[str]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for lesson in lessons:
        for entry in lesson["entries"]:
            if not include_entry(entry, delegated):
                continue
            answer, category = classify_entry(entry)
            key = f"{category}:{answer.casefold()}"
            if key not in grouped:
                grouped[key] = {**entry, "meanings": [entry["english"].strip()],
                                "source_ids": [lesson["id"]], "source_titles": [lesson["title"]]}
                continue
            item = grouped[key]
            if entry["english"].strip() not in item["meanings"]:
                item["meanings"].append(entry["english"].strip())
            if lesson["id"] not in item["source_ids"]:
                item["source_ids"].append(lesson["id"])
                item["source_titles"].append(lesson["title"])
            for field in ("plural", "conjugation"):
                new_value = entry.get(field, "")
                old_value = item.get(field, "")
                if new_value and old_value and new_value != old_value:
                    raise RuntimeError(f"Conflicting {field} for {entry['german']}: {old_value!r} / {new_value!r}")
                if new_value:
                    item[field] = new_value

    prepared = []
    for item in grouped.values():
        item["english"] = "; ".join(item.pop("meanings"))
        prepared.append(prepare_entry(item, item.pop("source_ids"), item.pop("source_titles")))
    return sorted(prepared, key=lambda item: item["german"].casefold())


def lesson_entries(lesson: dict, delegated: set[str]) -> list[dict]:
    return [
        prepare_entry(entry, [lesson["id"]], [lesson["title"]])
        for entry in lesson["entries"] if include_entry(entry, delegated)
    ]


def card_templates() -> tuple[str, str, str]:
    question = "<div class=instruction>Produce one German item</div><div class=prompt>{{Prompt}}</div>{{type:Answer}}"
    answer = "{{FrontSide}}<hr id=answer><div class=answer>{{Answer}}</div>{{#German}}<div class=source-form>{{German}}</div>{{/German}}<div class=meaning>{{English}}</div>{{#Extra}}<div class=extra>{{Extra}}</div>{{/Extra}}<div class=source>{{Source}}</div>"
    css = """
.card { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; font-size: 22px; text-align: center; color: #20242b; background: #fff; }
.instruction { font-size: 13px; font-weight: 700; color: #687386; text-transform: uppercase; letter-spacing: .08em; margin: 20px 0 10px; }
.prompt { font-size: 28px; font-weight: 650; line-height: 1.4; margin: 12px auto 22px; max-width: 32em; }
.answer { font-size: 30px; font-weight: 700; margin: 12px auto 6px; }
.source-form { font-size: 20px; font-weight: 600; color: #374151; margin: 8px auto; }
.meaning, .extra, .source { font-size: 15px; line-height: 1.5; margin: 11px auto; max-width: 40em; }
.meaning { color: #374151; } .extra { color: #5d6775; } .source { color: #7b8490; font-size: 13px; }
input { font-size: 22px; padding: 9px; max-width: 92%; }
"""
    return question, answer, css


def model_and_decks(now: int, model_name: str, deck_name: str, description: str) -> tuple[str, str]:
    model_id, deck_id = now, now + 1
    question, answer, css = card_templates()
    model = {
        str(model_id): {
            "id": str(model_id), "name": model_name, "type": 0, "mod": now // 1000,
            "usn": -1, "sortf": 0, "did": deck_id, "latexPre": "", "latexPost": "", "latexsvg": False,
            "flds": [{"name": name, "ord": index, "sticky": False, "rtl": False,
                      "font": "Arial", "size": 20, "media": []}
                     for index, name in enumerate(["Prompt", "Answer", "German", "English", "Extra", "Source"])],
            "tmpls": [{"name": "Meaning/context → German", "ord": 0, "did": None,
                        "qfmt": question, "afmt": answer, "bqfmt": "", "bafmt": "", "bfont": "", "bsize": 0}],
            "css": css, "req": [[0, "all", [0, 1]]], "tags": [], "vers": [],
        }
    }
    decks = {
        "1": {"id": 1, "name": "Default", "mod": now // 1000, "usn": 0, "collapsed": False,
              "browserCollapsed": False, "newToday": [0, 0], "revToday": [0, 0], "lrnToday": [0, 0],
              "timeToday": [0, 0], "conf": 1, "dyn": 0, "extendNew": 10, "extendRev": 50, "desc": ""},
        str(deck_id): {"id": deck_id, "name": deck_name, "mod": now // 1000, "usn": -1,
                       "collapsed": False, "browserCollapsed": False, "newToday": [0, 0],
                       "revToday": [0, 0], "lrnToday": [0, 0], "timeToday": [0, 0],
                       "conf": 1, "dyn": 0, "extendNew": 20, "extendRev": 50, "desc": description},
    }
    return json.dumps(model), json.dumps(decks)


def initialise(collection: Path, model_name: str, deck_name: str, description: str) -> None:
    with zipfile.ZipFile(source_package()) as archive, archive.open("collection.anki2") as src, collection.open("wb") as dst:
        shutil.copyfileobj(src, dst)
    now = int(time.time() * 1000)
    models, decks = model_and_decks(now, model_name, deck_name, description)
    db = sqlite3.connect(collection)
    with db:
        for table in ("cards", "notes", "revlog", "graves"):
            db.execute(f"DELETE FROM {table}")
        db.execute("UPDATE col SET mod = ?, models = ?, decks = ?", (now // 1000, models, decks))
    db.close()


def ids(db: sqlite3.Connection, model_name: str, deck_name: str) -> tuple[int, int]:
    models, decks = db.execute("SELECT models, decks FROM col").fetchone()
    model_data, deck_data = json.loads(models), json.loads(decks)
    model_id = next((key for key, value in model_data.items() if value["name"] == model_name), None)
    if model_id is None:
        model_id = next(key for key, value in model_data.items() if value["name"] != "Basic")
    deck_id = next((key for key, value in deck_data.items() if value["name"] == deck_name), None)
    if deck_id is None:
        deck_id = next(key for key, value in deck_data.items() if value["name"] != "Default")
    return int(model_id), int(deck_id)


def sync_layout(db: sqlite3.Connection, model_id: int, deck_id: int, model_name: str, deck_name: str, description: str) -> None:
    models_raw, decks_raw = db.execute("SELECT models, decks FROM col").fetchone()
    models, decks = json.loads(models_raw), json.loads(decks_raw)
    question, answer, css = card_templates()
    current = models[str(model_id)]
    current["name"] = model_name
    current["flds"] = [{"name": name, "ord": index, "sticky": False, "rtl": False,
                        "font": "Arial", "size": 20, "media": []}
                       for index, name in enumerate(["Prompt", "Answer", "German", "English", "Extra", "Source"])]
    current["tmpls"] = [{"name": "Meaning/context → German", "ord": 0, "did": None,
                          "qfmt": question, "afmt": answer, "bqfmt": "", "bafmt": "", "bfont": "", "bsize": 0}]
    current["css"] = css
    current["req"] = [[0, "all", [0, 1]]]
    current["mod"] = int(time.time())
    decks[str(deck_id)]["name"] = deck_name
    decks[str(deck_id)]["desc"] = description
    decks[str(deck_id)]["mod"] = int(time.time())
    db.execute("UPDATE col SET models = ?, decks = ?", (json.dumps(models), json.dumps(decks)))


def package(collection: Path, output: Path) -> None:
    temporary = output.with_suffix(".apkg.tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(collection, "collection.anki2")
        archive.writestr("media", "{}")
    temporary.replace(output)


def sync_cards(output: Path, entries: list[dict], scope: str, model_name: str,
               deck_name: str, description: str) -> dict[str, int]:
    with tempfile.TemporaryDirectory() as temp_name:
        collection = Path(temp_name) / "collection.anki2"
        if output.exists():
            with zipfile.ZipFile(output) as archive, archive.open("collection.anki2") as src, collection.open("wb") as dst:
                shutil.copyfileobj(src, dst)
        else:
            initialise(collection, model_name, deck_name, description)

        db = sqlite3.connect(collection)
        model_id, deck_id = ids(db, model_name, deck_name)
        sync_layout(db, model_id, deck_id, model_name, deck_name, description)
        existing = {guid: note_id for note_id, guid in db.execute("SELECT id, guid FROM notes WHERE mid = ?", (model_id,))}
        desired_guids = {hashlib.sha1(f"{scope}:{entry['key']}".encode("utf-8")).hexdigest()[:10] for entry in entries}
        next_note = db.execute("SELECT coalesce(max(id), 0) + 1 FROM notes").fetchone()[0]
        next_card = db.execute("SELECT coalesce(max(id), 0) + 1 FROM cards").fetchone()[0]
        next_due = db.execute("SELECT coalesce(max(due), -1) + 1 FROM cards WHERE did = ? AND queue = 0", (deck_id,)).fetchone()[0]
        now = int(time.time())
        added = removed = retired = 0
        with db:
            for entry in entries:
                guid = hashlib.sha1(f"{scope}:{entry['key']}".encode("utf-8")).hexdigest()[:10]
                fields = SEP.join([entry["prompt"], entry["answer"], entry["german"], entry["english"], entry["extra"], entry["source"]])
                tags = " ".join([*(f"source::{source_id}" for source_id in entry["source_ids"]), f"type::{entry['category'].replace(' ', '-')}"])
                if guid in existing:
                    note_id = existing[guid]
                    db.execute("UPDATE notes SET mod = ?, tags = ?, flds = ?, sfld = ?, csum = ? WHERE id = ?",
                               (now, tags, fields, entry["prompt"], checksum(entry["prompt"]), note_id))
                    db.execute("UPDATE cards SET did = ?, ord = 0, mod = ? WHERE nid = ?", (deck_id, now, note_id))
                    continue
                db.execute("INSERT INTO notes VALUES (?, ?, ?, ?, -1, ?, ?, ?, ?, 0, '')",
                           (next_note, guid, model_id, now, tags, fields, entry["prompt"], checksum(entry["prompt"])))
                db.execute("INSERT INTO cards VALUES (?, ?, ?, 0, ?, -1, 0, 0, ?, 0, 2500, 0, 0, 0, 0, 0, 0, '')",
                           (next_card, next_note, deck_id, now, next_due))
                next_note, next_card, next_due = next_note + 1, next_card + 1, next_due + 1
                added += 1

            for guid, note_id in existing.items():
                if guid in desired_guids:
                    continue
                card_ids = [row[0] for row in db.execute("SELECT id FROM cards WHERE nid = ?", (note_id,))]
                marks = ",".join("?" * len(card_ids))
                reviews = db.execute(f"SELECT count(*) FROM revlog WHERE cid IN ({marks})", card_ids).fetchone()[0] if card_ids else 0
                if reviews:
                    db.execute("UPDATE cards SET queue = -1, mod = ? WHERE nid = ?", (now, note_id))
                    db.execute("UPDATE notes SET tags = trim(tags || ' retired::quality-overhaul') WHERE id = ?", (note_id,))
                    retired += 1
                else:
                    db.execute("DELETE FROM cards WHERE nid = ?", (note_id,))
                    db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
                    removed += 1
            db.execute("UPDATE col SET mod = ?", (now,))
        db.close()
        package(collection, output)
    result = validate_package(output)
    return {"added": added, "removed": removed, "retired": retired, **result}


def checksum(text: str) -> int:
    return int(hashlib.sha1(text.encode("utf-8")).hexdigest()[:8], 16)


def main() -> None:
    lessons = load_lessons()
    delegated = delegated_sentence_answers()
    cumulative_entries = merge_entries(lessons, delegated)
    general = sync_cards(
        ANKI / "vocabulary.apkg", cumulative_entries, "general-vocabulary",
        "German Vocabulary — precise production", "DW A1 — Vocabulary",
        "Curated DW Nico’s Weg A1 lexical production. Noun gender is tested separately in Articles; no audio.",
    )
    lesson_results = {}
    for lesson in lessons:
        lesson_file = ROOT / lesson["sourceFile"]
        lesson_output = lesson_file.with_name(f"{lesson_file.stem}_Vocabulary.apkg")
        legacy_output = lesson_file.with_suffix(".apkg")
        if not lesson_output.exists() and legacy_output.exists():
            # Migrate a pre-rule filename by copying its collection first, so
            # stable note/card IDs and any review history carry into the
            # correctly named lesson deck.
            shutil.copy2(legacy_output, lesson_output)
        lesson_results[lesson["title"]] = sync_cards(
            lesson_output, lesson_entries(lesson, delegated), f"lesson:{lesson['id']}",
            f"DW {lesson['title']} — Precise production",
            f"DW — {lesson['title']} Vocabulary (typed)",
            f"Curated lexical vocabulary from the DW lesson {lesson['title']}; no audio.",
        )
    INDEX.write_text(json.dumps({
        "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "qualityPolicy": "One lexical target per card; noun answer excludes article; sentence-pattern targets delegated; exact cross-lesson repeats merged; no audio.",
        "sources": [{"id": lesson["id"], "title": lesson["title"], "url": lesson["url"],
                     "sourceEntries": len(lesson["entries"]),
                     "vocabularyCards": len(lesson_entries(lesson, delegated))} for lesson in lessons],
        "lastRun": {"cumulative": general, "lessons": lesson_results},
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created/updated vocabulary decks: {general['cards']} cumulative cards across {len(lessons)} lessons.")


if __name__ == "__main__":
    main()
