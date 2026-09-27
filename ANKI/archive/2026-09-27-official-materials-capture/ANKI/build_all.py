#!/usr/bin/env python3
"""Single entry point for the German decks.

  python3 ANKI/build_all.py check                  validate data, verify sources, write the review preview
  python3 ANKI/build_all.py approve --all          the learner approves the previewed cards (or --lesson ID / --deck NAME)
  python3 ANKI/build_all.py package                build every deck; refuses unless all checks pass and all cards are approved

Builds are deterministic: the same data produces byte-identical packages.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import time
from collections import OrderedDict
from pathlib import Path

import build_articles_deck
import build_sentences_deck
import build_vocabulary_decks
import card_quality
import review_preview
from anki_package_utils import DeckSpec, Note, package_ids, validate_package, write_package
from deck_data import ANKI, APPROVALS_FILE, ROOT, Card, Data, DataError, load, normalize

DECKS = OrderedDict([
    ("vocabulary", (build_vocabulary_decks, "Vocabulary", "vocabulary",
                    "One typed German word or fixed expression per card, in a verified context where one exists. No audio.")),
    ("articles", (build_articles_deck, "Articles", "articles",
                  "Typed der/die/das for singular nouns. Plural and dependable gender patterns after answering. No audio.")),
    ("sentences", (build_sentences_deck, "Sentences", "sentences",
                   "Productive sentences, replies, register switches and contextual forms from the lessons. No audio.")),
])
PRONUNCIATION_FILES = [
    ROOT / "DW Deutsch lernen/A1/01_Intro_zu_A1/04_Von A bis Z/build_phonetic_alphabet_deck.py",
    ROOT / "DW Deutsch lernen/A1/01_Intro_zu_A1/04_Von A bis Z/phonetic-alphabet.json",
    ROOT / "DW Deutsch lernen/A1/01_Intro_zu_A1/04_Von A bis Z/Von A bis Z_Phonetic Alphabet_Pronunciation.apkg",
]
INTERFERENCE_GAP = 12
REVIEW_DIR = ANKI / "review"


def collect(data: Data) -> tuple[list[Card], list[str], dict[str, list[str]]]:
    cards, errors = [], []
    for module, *_ in DECKS.values():
        deck_cards, deck_errors = module.build(data)
        cards.extend(deck_cards)
        errors.extend(deck_errors)
    quality_errors, warnings = card_quality.check(data, cards)
    return cards, errors + quality_errors, warnings


def card_hash(card: Card) -> str:
    visible = {name: value for name, value in card.fields.items() if name != "Key"}
    return hashlib.sha256(json.dumps([card.deck, visible], ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def ordered(cards: list[Card]) -> list[Card]:
    """Lesson order, with interfering cards (same answer, curated pairs) kept apart in the new-card queue."""
    pending = sorted(cards, key=lambda card: card.order)
    by_answer: dict[str, set[str]] = {}
    for card in pending:
        by_answer.setdefault(normalize(card.answer), set()).add(card.key)
    conflicts = {card.key: set(card.interferes) | (by_answer[normalize(card.answer)] - {card.key}) for card in pending}
    for card in pending:
        for other in card.interferes:
            conflicts.setdefault(other, set()).add(card.key)
    placed: list[Card] = []
    waiting: list[Card] = []
    while pending or waiting:
        recent = {card.key for card in placed[-INTERFERENCE_GAP:]}
        ready = next((card for card in waiting if not conflicts.get(card.key, set()) & recent), None)
        if ready:
            waiting.remove(ready)
            placed.append(ready)
            continue
        if not pending:
            placed.append(waiting.pop(0))
            continue
        card = pending.pop(0)
        (waiting if conflicts.get(card.key, set()) & recent else placed).append(card)
    return placed


def to_notes(cards: list[Card]) -> list[Note]:
    notes = []
    for position, card in enumerate(ordered(cards), start=1):
        note_type = DECKS[card.deck][0].NOTE_TYPE
        notes.append(Note(key=card.key, note_type=note_type, fields=card.fields, tags=card.tags, due=position,
                          suspended=bool(card.retired)))
    return notes


def level_of(data: Data, card: Card) -> str:
    return data.lesson(card.lessons[0]).record["level"]


def deck_specs(data: Data, cards: list[Card]) -> list[DeckSpec]:
    specs = []
    levels = sorted({level_of(data, card) for card in cards})
    for deck, (_, title, stem, description) in DECKS.items():
        for level in levels:
            deck_cards = [card for card in cards if card.deck == deck and level_of(data, card) == level]
            if not deck_cards:
                continue
            output = ANKI / (f"{stem}.apkg" if level == "A1" else f"{stem}-{level}.apkg")
            specs.append(DeckSpec(name=f"German {level} — {title}", description=description, output=output,
                                  guid_namespace=f"cumulative:{deck}", notes=to_notes(deck_cards)))
    for lesson in data.lessons:
        refs = {f"{lesson.id}:{entry['id']}" for entry in lesson.record.get("entries", [])}
        lesson_cards = [card for card in cards if card.deck in {"vocabulary", "sentences"} and refs & set(card.covers)]
        if not lesson_cards:
            continue
        deck_info = lesson.record["lessonDeck"]
        specs.append(DeckSpec(name=deck_info["deck"], output=ROOT / deck_info["file"],
                              description=f"Typed introduction to {lesson.label}: its vocabulary and the sentence "
                                          f"cards for its phrases. No audio.",
                              guid_namespace=f"lesson:{lesson.id}", notes=to_notes(lesson_cards)))
    return specs


def load_approvals() -> dict:
    if APPROVALS_FILE.exists():
        return json.loads(APPROVALS_FILE.read_text(encoding="utf-8"))
    return {"description": "Card content hashes the learner approved after reviewing ANKI/review/preview.html. "
                           "A card whose content changes needs approval again.", "approved": {}, "log": []}


def report(errors: list[str]) -> None:
    for error in errors:
        print(f"ERROR  {error}")


def cmd_check(data: Data) -> int:
    cards, errors, warnings = collect(data)
    approvals = load_approvals()
    REVIEW_DIR.mkdir(exist_ok=True)
    hashes = {card.key: card_hash(card) for card in cards}
    review_preview.write(REVIEW_DIR / "preview.html", data, cards, errors, warnings, hashes, approvals["approved"])
    ledger = {entry.ref: sorted(card.key for card in cards if entry.ref in card.covers) for entry in data.entries}
    (REVIEW_DIR / "coverage-ledger.json").write_text(json.dumps(
        {"revision": data.revision, "entries": ledger,
         "pending": [{"lesson": lesson.id, **item} for lesson, item in data.pending]},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    counts = {deck: sum(card.deck == deck for card in cards) for deck in DECKS}
    unapproved = sum(hashes[card.key] not in approvals["approved"] for card in cards)
    report(errors)
    print(f"Cards: {counts}; entries: {len(data.entries)}; pending yes/no: {len(data.pending)}; "
          f"warnings: {sum(bool(items) for items in warnings.values())} cards; unapproved: {unapproved}")
    print(f"Preview: {REVIEW_DIR / 'preview.html'}")
    return 1 if errors else 0


def cmd_approve(data: Data, args: argparse.Namespace) -> int:
    cards, errors, _ = collect(data)
    if errors:
        report(errors)
        print("Nothing approved: fix the errors first.")
        return 1
    scope = [card for card in cards
             if args.all or (args.deck and card.deck == args.deck) or (args.lesson and args.lesson in card.lessons)]
    approvals = load_approvals()
    for card in scope:
        approvals["approved"][card_hash(card)] = card.key
    approvals["log"].append({"date": time.strftime("%Y-%m-%d"), "scope": "all" if args.all else (args.deck or args.lesson),
                             "cards": len(scope)})
    APPROVALS_FILE.parent.mkdir(exist_ok=True)
    APPROVALS_FILE.write_text(json.dumps(approvals, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Approved {len(scope)} card(s).")
    return 0


def file_hashes(paths: list[Path]) -> dict[str, str]:
    return {str(path): hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "missing" for path in paths}


def write_indexes(data: Data, cards: list[Card], results: dict[str, dict]) -> None:
    lessons_info = []
    for lesson in data.lessons:
        refs = {f"{lesson.id}:{entry['id']}" for entry in lesson.record.get("entries", [])}
        lessons_info.append({
            "id": lesson.id, "course": lesson.course["id"], "title": lesson.record["title"], "url": lesson.record["url"],
            "notesFile": lesson.record["notesFile"], "capturedEntries": len(refs),
            "cards": {deck: sum(card.deck == deck and bool(refs & set(card.covers)) for card in cards) for deck in DECKS},
        })
    for deck, (_, title, stem, description) in DECKS.items():
        index = {
            "deck": f"German A1 — {title}", "revision": data.revision, "qualityPolicy": description,
            "cards": sum(card.deck == deck for card in cards), "sources": lessons_info,
            "packages": {path: result for path, result in results.items()
                         if Path(path).name.startswith(stem) or (deck == "vocabulary" and path.endswith("_Vocabulary.apkg"))},
        }
        (ANKI / f"{stem}-scan-index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cmd_package(data: Data) -> int:
    cards, errors, _ = collect(data)
    if errors:
        report(errors)
        print("Not packaged: fix the errors first.")
        return 1
    approved = load_approvals()["approved"]
    unapproved = [card.key for card in cards if card_hash(card) not in approved]
    if unapproved:
        print(f"Not packaged: {len(unapproved)} card(s) are not approved yet. Review ANKI/review/preview.html, then run "
              f"`python3 ANKI/build_all.py approve --all` (or per lesson/deck).")
        return 1
    before = file_hashes(PRONUNCIATION_FILES)
    specs = deck_specs(data, cards)
    results: dict[str, dict] = {}
    all_ids: set = set()
    with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
        for spec in specs:
            a, b = Path(first) / f"{len(results)}.apkg", Path(second) / f"{len(results)}.apkg"
            write_package(spec, data.revision, a)
            write_package(spec, data.revision, b)
            if a.read_bytes() != b.read_bytes():
                raise RuntimeError(f"{spec.name}: build is not deterministic")
            counts = validate_package(a, expected_cards=len(spec.notes))
            ids = package_ids(a)
            if all_ids & ids:
                raise RuntimeError(f"{spec.name}: note/card IDs collide with another package")
            all_ids |= ids
            results[str(spec.output.relative_to(ROOT))] = {**counts, "sha256": hashlib.sha256(a.read_bytes()).hexdigest()}
            spec.output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(a, spec.output)
    if file_hashes(PRONUNCIATION_FILES) != before:
        raise RuntimeError("The pronunciation resource changed during the build")
    write_indexes(data, cards, results)
    for path, result in results.items():
        print(f"{path}: {result['cards']} cards")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("check")
    approve = sub.add_parser("approve")
    group = approve.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--lesson")
    group.add_argument("--deck", choices=list(DECKS))
    sub.add_parser("package")
    args = parser.parse_args(argv)
    try:
        data = load()
    except DataError as problem:
        print(f"ERROR  {problem}")
        return 1
    if args.command == "approve":
        return cmd_approve(data, args)
    if args.command == "package":
        return cmd_package(data)
    return cmd_check(data)


if __name__ == "__main__":
    sys.exit(main())
