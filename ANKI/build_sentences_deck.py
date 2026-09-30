#!/usr/bin/env python3
"""Sentences cards: productive utterances, responses, register switches and contextual forms.

Every card is curated in sentence-sources.json. German on the front must be verbatim source
text; answers are verified in a source snapshot or are the learner's own captured sentence.
Run `python3 ANKI/build_all.py`.
"""

from __future__ import annotations

import html
import re
from collections import OrderedDict

from anki_package_utils import NoteType
from deck_data import (BACK_TEMPLATE, BASE_CSS, Card, Data, DataError, context_parts, context_source, course_tag,
                       details_html, normalize, source_label, typed_form, verify_context)

NOTE_TYPE = NoteType(
    name="German · Sentences v3",
    fields=("Scene", "Instruction", "Prompt", "Answer", "Display", "Filled", "Details", "Source", "Key"),
    qfmt=("<div class=kind>Sentences</div><div class=instr>{{Instruction}}</div><div class=cue>{{Scene}}</div>"
          "{{#Prompt}}<div class=context>{{Prompt}}</div>{{/Prompt}}{{type:Answer}}"),
    afmt=BACK_TEMPLATE,
    css=BASE_CSS,
)

INSTRUCTIONS = {
    "production": "Say it in German — type the whole sentence",
    "response": "Reply in German — type your answer",
    "completion": "Type the missing German form",
    "register": "Switch the register — type the sentence",
}


def build(data: Data) -> tuple[list[Card], list[str]]:
    errors: list[str] = []
    cards: list[Card] = []
    seen_keys: set[str] = set()
    for spec in data.sentence_cards:
        key = f"sentence:{spec['key']}"
        where = f"sentence {spec['key']}"
        if key in seen_keys:
            errors.append(f"{where}: duplicate key")
            continue
        seen_keys.add(key)
        kind = spec["kind"]
        if kind not in INSTRUCTIONS:
            errors.append(f"{where}: unknown kind {kind!r}")
            continue
        try:
            covered = [data.entry(ref) for ref in spec.get("covers", [])]
        except DataError as problem:
            errors.append(f"{where}: {problem}")
            continue
        for entry in covered:
            if entry.raw.get("home") != "sentences":
                errors.append(f"{where}: covers {entry.ref}, whose home deck is {entry.raw.get('home')}")

        answer_display = spec["answer"]
        answer = typed_form(answer_display)
        sources, warnings = [], []
        prompt_front = prompt_back = ""
        prompt = spec.get("prompt")
        if prompt:
            problems = verify_context(data, prompt, where)
            errors.extend(problems)
            if not problems:
                if kind == "completion":
                    try:
                        prompt_front, prompt_back = context_parts(prompt, prompt["target"])
                    except Exception as problem:
                        errors.append(f"{where}: {problem}")
                    if normalize(prompt.get("target", "")) != normalize(answer_display):
                        errors.append(f"{where}: completion answer must equal the blanked source text")
                else:
                    prompt_front = html.escape(prompt["text"])
                sources.append(context_source(data, prompt))
        elif kind in {"response", "completion"}:
            errors.append(f"{where}: {kind} cards need a verified German prompt")

        answer_source = spec.get("answerSource")
        if kind != "completion":
            if answer_source == "learner-notes":
                if not any(normalize(entry.raw["german"]) == normalize(answer_display) for entry in covered):
                    errors.append(f"{where}: a learner-notes answer must equal a covered entry exactly")
                sources.append("Answer: your notes")
            elif isinstance(answer_source, dict):
                if data.snapshots.contains(answer_source["lesson"], answer_source["source"], answer_display):
                    sources.append(context_source(data, answer_source).replace("Context:", "Answer:"))
                else:
                    errors.append(f"{where}: answer is not verbatim in {answer_source['lesson']}/{answer_source['source']}: "
                                  f"{answer_display!r}")
            else:
                errors.append(f"{where}: answerSource must be a snapshot reference or 'learner-notes'")

        details = []
        if spec.get("accept"):
            details.append("Also correct: " + " · ".join(html.escape(item) for item in spec["accept"]))
        errors_seen = [spec.get("learnerError")] + [entry.raw.get("learnerError") for entry in covered]
        for learner_error in filter(None, errors_seen):
            details.append(f"Not: <s>{html.escape(learner_error['wrong'])}</s> — {html.escape(learner_error['why'])}")
        if spec.get("note"):
            details.append(html.escape(spec["note"]))
        for entry in covered:
            learner = entry.raw.get("learnerForm")
            if learner and normalize(learner) != normalize(entry.raw["german"]):
                details.append(f"In your notes: “{html.escape(learner)}”")

        lesson = data.lesson(spec["lesson"])
        sources.extend(source_label(entry) for entry in covered)
        if not covered:
            sources.append(f"Pattern practice from {lesson.label}")
        lessons = list(OrderedDict.fromkeys([spec["lesson"]] + [entry.lesson.id for entry in covered]))
        tags = {"deck::sentences", f"kind::{kind}", f"skill::{re.sub(r'[^a-z0-9]+', '-', spec['skill'].casefold())}",
                course_tag(lesson), *(f"lesson::{item}" for item in lessons)}
        tags |= {"type::name" for entry in covered if entry.pos == "name"}
        fields = {
            "Scene": html.escape(spec["scene"]),
            "Instruction": INSTRUCTIONS[kind],
            "Prompt": prompt_front,
            "Answer": html.escape(answer, quote=False),
            "Display": html.escape(answer_display),
            "Filled": prompt_back if kind == "completion" else "",
            "Details": details_html(details),
            "Source": "<br>".join(html.escape(item) for item in OrderedDict.fromkeys(sources)),
            "Key": key,
        }
        position = lesson.record["entries"].index(covered[0].raw) if covered and covered[0].lesson is lesson else 999
        cards.append(Card(
            deck="sentences", key=key, fields=fields, covers=[entry.ref for entry in covered], lessons=lessons,
            order=(lesson.order, position, spec["key"]), answer=answer, cue=spec["scene"],
            front_german=prompt["text"] if prompt_front else "", warnings=warnings, retired=spec.get("retired", ""),
            tags=sorted(tags | ({f"retired::{spec['retired']}"} if spec.get("retired") else set())),
        ))
    return cards, errors
