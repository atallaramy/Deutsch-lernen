#!/usr/bin/env python3
"""Articles cards: typed der/die/das recall for singular nouns with a source-given article.

A context is used only when its blank is a definite-article slot that equals the noun's gender
(nominative for masculine). Otherwise the card shows the noun and its gloss. Gender is a
property of the noun form, so one card serves every sense of the same lemma+gender.
Run `python3 ANKI/build_all.py`.
"""

from __future__ import annotations

import html
import re
from collections import OrderedDict

from anki_package_utils import NoteType
from deck_data import (BACK_TEMPLATE, BASE_CSS, BLANK, GENDER_ARTICLE, Card, Data, Entry, context_source, course_tag,
                       details_html, display_form, source_label, verify_context)

NOTE_TYPE = NoteType(
    name="German · Articles v3",
    fields=("Noun", "Gloss", "Instruction", "Context", "Answer", "Display", "Filled", "Details", "Source", "Key"),
    qfmt=("<div class=kind>Articles</div><div class=instr>{{Instruction}}</div>"
          "{{#Context}}<div class=context>{{Context}}</div>{{/Context}}{{^Context}}<div class=noun>{{Noun}}</div>{{/Context}}"
          "<div class=cue>{{Gloss}}</div>{{type:Answer}}"),
    afmt=BACK_TEMPLATE,
    css=BASE_CSS,
)

SUFFIX_RULES = [
    ("ung", "f", "Nouns ending in -ung are die."), ("heit", "f", "Nouns ending in -heit are die."),
    ("keit", "f", "Nouns ending in -keit are die."), ("schaft", "f", "Nouns ending in -schaft are die."),
    ("tät", "f", "Nouns ending in -tät are die."), ("ion", "f", "Nouns ending in -ion are normally die."),
    ("ik", "f", "Nouns ending in -ik are normally die."), ("ur", "f", "Nouns ending in -ur are normally die."),
    ("chen", "n", "Diminutives ending in -chen are das."), ("lein", "n", "Diminutives ending in -lein are das."),
    ("ment", "n", "Nouns ending in -ment are normally das."), ("um", "n", "Nouns ending in -um are normally das."),
]
MALE = ("(male)", "father", "man", "husband", "son", "brother", "uncle", "dad", "grandfather", "father-in-law")
FEMALE = ("(female)", "mother", "woman", "wife", "daughter", "sister", "aunt", "mom", "grandmother", "mother-in-law")


def eligible(entry: Entry) -> bool:
    return (entry.pos == "noun" and entry.gender is not None and not entry.raw.get("pluralOnly")
            and not str(entry.raw.get("articles", "")).startswith("exempt"))


def person_gender(english: str) -> str | None:
    words = english.casefold()
    if any(re.search(rf"(?<![\w-]){re.escape(term)}(?![\w-])", words) for term in FEMALE):
        return "f"
    if any(re.search(rf"(?<![\w-]){re.escape(term)}(?![\w-])", words) for term in MALE):
        return "m"
    return None


def gender_hints(lemma: str, gender: str, english: str, nouns: dict[str, str]) -> list[str]:
    hints = []
    natural = person_gender(english)
    if natural == gender:
        hints.append("A male person is der, a female person is die." if gender in "mf" else "")
    if gender == "f" and lemma.endswith("in") and natural == "f":
        hints.append("Female person ending in -in: always die.")
    for suffix, suffix_gender, text in SUFFIX_RULES:
        if lemma.casefold().endswith(suffix) and suffix_gender == gender:
            hints.append(text)
            break
    for other, other_gender in sorted(nouns.items(), key=lambda item: -len(item[0])):
        if other != lemma and len(other) >= 3 and lemma.endswith(other.casefold()) and other_gender == gender:
            hints.append(f"Compound: the last part decides — {GENDER_ARTICLE[gender]} {other} → {GENDER_ARTICLE[gender]} {lemma}.")
            break
    if lemma.endswith("e") and gender == "m":
        hints.append("⚠ Ends in -e but is der (exception to the usual -e → die).")
    elif lemma.endswith("e") and gender == "f" and not hints:
        hints.append("Nouns ending in -e are usually die.")
    return [hint for hint in hints if hint]


def article_context(data: Data, context: dict, lemma: str, gender: str, where: str) -> tuple[str, str, str, list[str]]:
    errors = verify_context(data, context, where)
    if errors:
        return "", "", "", errors
    text = context["text"]
    pattern = re.compile(rf"(?<![\wÄÖÜäöüß])(der|die|das|Der|Die|Das) {re.escape(lemma)}(?![\wÄÖÜäöüß])")
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        return "", "", "", [f"{where}: need exactly one 'der/die/das {lemma}' in the context, found {len(matches)}"]
    article = matches[0].group(1)
    if article.casefold() != GENDER_ARTICLE[gender]:
        return "", "", "", [f"{where}: the blank's article {article!r} is not the gender article "
                            f"{GENDER_ARTICLE[gender]!r} (case form or wrong gender)"]
    start, end = matches[0].span(1)
    front = html.escape(text[:start]) + f"<span class=gap>{BLANK}</span>" + html.escape(text[end:])
    back = html.escape(text[:start]) + f"<b>{article}</b>" + html.escape(text[end:])
    return front, back, article, []


def build(data: Data) -> tuple[list[Card], list[str]]:
    errors: list[str] = []
    groups: OrderedDict[tuple[str, str], list[Entry]] = OrderedDict()
    for entry in data.entries:
        if eligible(entry):
            groups.setdefault((entry.lemma, entry.gender), []).append(entry)
    genders_by_lemma: dict[str, set[str]] = {}
    for lemma, gender in groups:
        genders_by_lemma.setdefault(lemma, set()).add(gender)
    nouns = {lemma: gender for lemma, gender in groups}

    cards = []
    for (lemma, gender), group in groups.items():
        canonical = group[0]
        key = f"article:{lemma}|{gender}"
        curated = data.articles_cards.get(lemma, {})
        glosses = list(OrderedDict.fromkeys(entry.raw["english"] for entry in group))
        warnings, sources = [], []
        front = back = ""
        answer = GENDER_ARTICLE[gender]
        if curated.get("context"):
            front, back, article, problems = article_context(data, curated["context"], lemma, gender, f"articles {lemma}")
            errors.extend(problems)
            if front:
                answer = article
                sources.append(context_source(data, curated["context"]))
                if re.search(r"(?<![\wÄÖÜäöüß])(er|sie|es|ihn|ihm)(?![\wÄÖÜäöüß])", curated["context"]["text"]):
                    warnings.append("context has a pronoun — confirm it does not refer back to the noun")
        else:
            warnings.append("bare noun (no leak-free verified context)")
        if len(genders_by_lemma[lemma]) > 1:
            warnings.append("same lemma with different genders — separate cards")
        hints = curated.get("hints") or gender_hints(lemma, gender, " ".join(glosses), nouns)
        details = list(hints)
        details += [html.escape(entry.raw["note"]) for entry in group if entry.raw.get("note")]
        if canonical.raw.get("articleSource"):
            details.append(f"Article from the {html.escape(canonical.raw['articleSource'])} (compound rule).")
        sources.extend(source_label(entry) for entry in group)
        tags = {"deck::articles", f"gender::{gender}", "context::verified" if front else "context::none"}
        tags |= {course_tag(entry.lesson) for entry in group} | {f"lesson::{entry.lesson.id}" for entry in group}
        fields = {
            "Noun": html.escape(lemma),
            "Gloss": html.escape(" / ".join(glosses)),
            "Instruction": ("Type der, die or das — exactly as it fits the sentence" if front
                            else "Type der, die or das"),
            "Context": front,
            "Answer": answer,
            "Display": html.escape(display_form(canonical)),
            "Filled": back,
            "Details": details_html(details),
            "Source": "<br>".join(html.escape(item) for item in OrderedDict.fromkeys(sources)),
            "Key": key,
        }
        cards.append(Card(
            deck="articles", key=key, fields=fields, covers=[entry.ref for entry in group],
            lessons=list(OrderedDict.fromkeys(entry.lesson.id for entry in group)),
            order=(canonical.lesson.order, canonical.lesson.record["entries"].index(canonical.raw)),
            answer=answer, cue=" / ".join(glosses), front_german=curated["context"]["text"] if front else "",
            tags=sorted(tags | ({f"retired::{curated['retired']}"} if curated.get("retired") else set())), warnings=warnings,
            retired=curated.get("retired", ""),
        ))
    return cards, errors
