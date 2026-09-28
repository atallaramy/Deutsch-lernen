#!/usr/bin/env python3
"""Vocabulary cards (cumulative deck) and the per-lesson typed introduction decks.

One card per lemma+sense. Captured records with an identical lemma and sense merge across
lessons and courses; distinct senses stay separate cards. Run `python3 ANKI/build_all.py`.
"""

from __future__ import annotations

import html
import re
from collections import OrderedDict

from anki_package_utils import NoteType
from deck_data import (BACK_TEMPLATE, BASE_CSS, POS_INSTRUCTION, Card, Data, Entry, context_parts, context_source,
                       course_tag, details_html, display_form, gloss_snapshot, lemma_answer, normalize, source_label, typed_form,
                       verify_context)

NOTE_TYPE = NoteType(
    name="German · Vocabulary v3",
    fields=("Cue", "Instruction", "Context", "Answer", "Display", "Filled", "Details", "Source", "Key"),
    qfmt=("<div class=kind>Vocabulary</div><div class=instr>{{Instruction}}</div>"
          "{{#Context}}<div class=context>{{Context}}</div>{{/Context}}<div class=cue>{{Cue}}</div>{{type:Answer}}"),
    afmt=BACK_TEMPLATE,
    css=BASE_CSS,
)


def merge_key(entry: Entry) -> tuple[str, str]:
    return entry.lemma, entry.sense


def card_key(lemma: str, sense: str) -> str:
    return f"vocab:{lemma}|{sense}"


def default_cue(entry: Entry) -> str:
    english = entry.raw["english"].strip().rstrip(".")
    if entry.pos == "number":
        # Number senses are digits ("8"); DW glosses spell them out, VHS gives digits.
        prompt = entry.sense if entry.sense.isdigit() else english
        return f"{prompt} — write the number as a word"
    if entry.pos == "abbreviation":
        return f"{english} — the German abbreviation"
    if entry.pos == "place":
        return f"{english} — the German name"
    return english


def grouped_entries(data: Data) -> "OrderedDict[tuple[str, str], list[Entry]]":
    groups: OrderedDict[tuple[str, str], list[Entry]] = OrderedDict()
    for entry in data.entries:
        if entry.raw.get("home") == "vocabulary":
            groups.setdefault(merge_key(entry), []).append(entry)
    return groups


def merge_conflicts(key: tuple[str, str], group: list[Entry]) -> list[str]:
    errors = []
    for attribute in ("plural", "pos"):
        values = {entry.raw.get(attribute) for entry in group if entry.raw.get(attribute)}
        if len(values) > 1:
            errors.append(f"Vocabulary merge {key}: conflicting {attribute} {sorted(values)}")
    genders = {entry.gender for entry in group}
    if len(genders) > 1:
        errors.append(f"Vocabulary merge {key}: conflicting genders {sorted(map(str, genders))}")
    return errors


def build(data: Data) -> tuple[list[Card], list[str]]:
    errors: list[str] = []
    cards: list[Card] = []
    groups = grouped_entries(data)
    glosses = gloss_snapshot()
    senses_by_lemma: dict[str, list[str]] = {}
    for lemma, sense in groups:
        senses_by_lemma.setdefault(lemma, []).append(sense)

    for (lemma, sense), group in groups.items():
        errors.extend(merge_conflicts((lemma, sense), group))
        canonical = group[0]
        curated = data.vocabulary_cards.get(f"{lemma}|{sense}", {})
        context = curated.get("context")
        if context and not context.get("target"):
            context = {**context, "target": lemma_answer(canonical).rstrip(".!?")}
        # With a context you type exactly what fills the blank; without one, the full expression with its punctuation.
        answer = typed_form(context["target"] if context else curated.get("answer") or lemma_answer(canonical))
        cue = curated.get("cue") or default_cue(canonical)
        warnings = []
        context_front = context_back = ""
        sources = []
        if context:
            where = f"vocabulary {lemma}|{sense}"
            problems = verify_context(data, context, where)
            if problems:
                errors.extend(problems)
            else:
                try:
                    context_front, context_back = context_parts(context, context["target"])
                    sources.append(context_source(data, context))
                except Exception as problem:  # malformed curated context is a data error
                    errors.append(f"{where}: {problem}")
        else:
            warnings.append("bare cue (no verified context yet)")

        details = []
        for entry in group:
            if entry.raw.get("forms"):
                details.append(f"Forms: {html.escape(entry.raw['forms'])}")
            if entry.raw.get("present"):
                details.append(f"Präsens: {html.escape(entry.raw['present'])}")
        for entry in group:
            if entry.raw.get("note"):
                details.append(html.escape(entry.raw["note"]))
        if curated.get("note"):
            details.append(html.escape(curated["note"]))
        for other in senses_by_lemma[lemma]:
            if other != sense:
                other_entry = groups[(lemma, other)][0]
                details.append(f"Other meaning (separate card): {html.escape(other_entry.raw['english'])}")
        for entry in group:
            learner = entry.raw.get("learnerForm")
            if learner and normalize(learner) != normalize(entry.raw["german"]):
                details.append(f"In your notes: “{html.escape(learner)}”")
        if any(entry.raw.get("level") == "beyond-A1" for entry in group):
            details.append("Beyond A1.")
            warnings.append("beyond A1")
        if not any({"dw-glossary", "dw-culture-page", "vhs-vocabulary-trainer"} & set(entry.raw.get("origin", [])) for entry in group):
            terms = canonical.raw.get("glossLookup") or [canonical.lemma.rstrip(".!?")]
            dictionaries = sorted({glosses.get(term, {}).get("dictionary", "en.wiktionary") for term in terms})
            sources.append(f"Meaning checked in {' and '.join(dictionaries)} ({', '.join(terms)})")
        if normalize(cue).casefold().strip("!?.") == normalize(answer).casefold().strip("!?."):
            warnings.append("cue equals the answer (cognate or loanword)")

        sources.extend(source_label(entry) for entry in group)
        lessons = list(OrderedDict.fromkeys(entry.lesson.id for entry in group))
        tags = {"deck::vocabulary", f"pos::{canonical.pos}", "context::verified" if context_front else "context::none"}
        tags |= {course_tag(entry.lesson) for entry in group} | {f"lesson::{entry.lesson.id}" for entry in group}
        tags |= {f"level::{entry.raw.get('level', entry.lesson.record['level'])}" for entry in group}
        fields = {
            "Cue": html.escape(cue),
            "Instruction": "Type the missing German word" if context_front else POS_INSTRUCTION.get(canonical.pos, "Type the German"),
            "Context": context_front,
            "Answer": html.escape(answer, quote=False),
            "Display": html.escape(curated.get("display") or display_form(canonical)),
            "Filled": context_back,
            "Details": details_html(details),
            "Source": "<br>".join(html.escape(item) for item in OrderedDict.fromkeys(sources)),
            "Key": card_key(lemma, sense),
        }
        cards.append(Card(
            deck="vocabulary", key=card_key(lemma, sense), fields=fields,
            covers=[entry.ref for entry in group], lessons=lessons,
            order=(canonical.lesson.order, canonical.lesson.record["entries"].index(canonical.raw)),
            answer=answer, cue=cue, front_german=context["text"] if context_front else "",
            tags=sorted(tags | ({f"retired::{curated['retired']}"} if curated.get("retired") else set())), warnings=warnings,
            retired=curated.get("retired", ""),
            interferes=[card_key(*item.split("|", 1)) for item in curated.get("interferesWith", [])],
        ))
    return cards, errors
