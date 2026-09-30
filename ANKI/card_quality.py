#!/usr/bin/env python3
"""Cross-deck quality gate: coverage, leakage, ambiguity, duplicates and preservation of captured records."""

from __future__ import annotations

import html
import json
import re
from collections import defaultdict
from pathlib import Path

from deck_data import BLANK, LEGACY_V2_FILE, Card, Data, normalize

WORD_RE = re.compile(r"[A-Za-zÄÖÜäöüß]+")
DETERMINERS = r"(?:ein|eine|einen|einem|einer|eines|mein|meine|meinen|meinem|meiner|dein|deine|deinen|deinem|deiner|" \
              r"sein|seine|seinen|seinem|seiner|ihr|ihre|ihren|ihrem|ihrer|Ihr|Ihre|Ihren|Ihrem|Ihrer|unser|unsere|" \
              r"euer|eure|kein|keine|keinen|keinem|keiner|dies\w*|welch\w*)"
FUNCTION_WORDS = set("""
der die das den dem des ein eine einen einem einer eines kein keine keinen mein meine meinen meinem meiner dein deine
sein seine seinen seinem seiner ihr ihre ihren ihrem ihrer unser unsere euer eure im am ins zum zur vom beim an auf aus
bei mit nach von zu für in um und oder aber doch auch nicht noch so sehr ja nein da dann also nur schon hier dort wo
wie was wer ich du er sie es wir ihr mir dir ihm ihn uns euch man bitte danke mal denn gerade jetzt ist sind bin bist
seid war hat habe hast haben habt gut
""".split())


def plain(text: str) -> str:
    return normalize(re.sub(r"<[^>]+>", " ", html.unescape(text)))


def known_lexicon(data: Data) -> set[str]:
    words = set(FUNCTION_WORDS)
    for entry in data.entries:
        for field in ("german", "plural", "forms", "present", "lemma"):
            words |= {token.casefold() for token in WORD_RE.findall(str(entry.raw.get(field, "")))}
        if entry.pos == "verb":
            stem = re.sub(r"(e?n)$", "", entry.lemma.split()[-1])
            words |= {stem + ending for ending in ("e", "st", "t", "en", "est", "et")}
    return words


def check(data: Data, cards: list[Card]) -> tuple[list[str], dict[str, list[str]]]:
    """Return (errors, warnings per card key)."""
    errors: list[str] = []
    warnings: dict[str, list[str]] = defaultdict(list)
    by_deck = defaultdict(list)
    for card in cards:
        by_deck[card.deck].append(card)
        warnings[card.key].extend(card.warnings)

    # Coverage ledger: every captured entry reaches at least one card in its home deck.
    covered = defaultdict(set)
    for card in cards:
        for ref in card.covers:
            covered[ref].add(card.deck)
    for entry in data.entries:
        home = entry.raw.get("home")
        if home not in {"vocabulary", "sentences"}:
            errors.append(f"{entry.ref}: home must be vocabulary or sentences")
        elif home not in covered[entry.ref]:
            errors.append(f"Coverage: {entry.ref} ({entry.raw['german']!r}) has no {home} card")

    # Captured v2 records are preserved in schema 3.
    if not LEGACY_V2_FILE.exists():
        errors.append(f"Missing {LEGACY_V2_FILE.name}: the v2 preservation check cannot run")
    else:
        legacy = json.loads(LEGACY_V2_FILE.read_text(encoding="utf-8"))
        v3 = defaultdict(set)
        for entry in data.entries:
            if entry.lesson.record.get("legacyId"):
                v3[entry.lesson.record["legacyId"]].add(normalize(entry.raw["german"]))
        for lesson in legacy["lessons"]:
            for item in lesson["entries"]:
                if normalize(item["german"]) not in v3[lesson["id"]] and item["german"] != "der Deutschlehrerin":
                    errors.append(f"Preservation: v2 entry {lesson['id']}:{item['german']!r} is missing from schema 3")

    # Answer policy.
    for card in cards:
        if not card.answer or card.answer != card.answer.strip() or "’" in card.answer or "\n" in card.answer:
            errors.append(f"{card.key}: typed answer must be one trimmed line using the keyboard apostrophe")
        if not card.fields.get(next(iter(card.fields))):
            errors.append(f"{card.key}: first field is empty")

    # Leakage.
    for card in by_deck["vocabulary"]:
        answer = normalize(card.answer).casefold().strip(".!?")
        if len(answer) < 3:
            continue
        stem = answer[:max(4, len(answer) - 2)] if len(answer) > 4 else answer
        context = plain(card.fields["Context"].replace(BLANK, " ")).casefold()
        if re.search(rf"(?<![a-zäöüß]){re.escape(stem)}", context):
            errors.append(f"{card.key}: answer or its stem {stem!r} appears in the context")
        # English cognates (hotel → Hotel) are legitimate but easy, so cue matches are warnings, not errors.
        cue = plain(card.fields["Cue"]).casefold()
        if re.search(rf"(?<![a-zäöüß]){re.escape(answer)}(?![a-zäöüß])", cue):
            warnings[card.key].append("cue contains the answer word (cognate or loanword)")
        elif answer in cue:
            warnings[card.key].append(f"cue contains {answer!r} inside another word — check it does not give the answer away")
    for card in by_deck["articles"]:
        noun = card.fields["Noun"]
        front = plain(card.fields["Context"])
        if front:
            if re.search(rf"{DETERMINERS}\s+(?:\w+\s+)?{re.escape(noun)}\b", front):
                errors.append(f"{card.key}: a gender-marking determiner stands before the noun on the front")
            if front.count(noun) != 1:
                errors.append(f"{card.key}: the noun must appear exactly once on the front")
        display = plain(card.fields["Display"])
        plural = display.split(", ", 1)[1] if ", " in display else ""
        plural_word = plural.split(" ", 1)[1] if plural.startswith("die ") else ""
        if plural_word and plural_word != noun and re.search(rf"\b{re.escape(plural_word)}\b", front + " " + card.cue):
            errors.append(f"{card.key}: the plural form appears on the front")

    # Ambiguity: two Vocabulary cues sharing a meaning ("surname" vs "last name; surname") must not ask for different answers.
    meanings = defaultdict(set)
    for card in by_deck["vocabulary"]:
        for part in re.split(r"[;/]", normalize(card.cue).casefold()):
            part = part.strip(" .!?")
            if part:
                meanings[part].add(card.answer)
    for part, answers in sorted(meanings.items()):
        if len(answers) > 1:
            errors.append(f"Ambiguous cue meaning {part!r} → {sorted(answers)}; add a disambiguating cue")

    # Front-sentence registry across the cumulative decks.
    fronts = defaultdict(list)
    for card in cards:
        if card.front_german:
            fronts[normalize(card.front_german).casefold()].append(card.key)
    for text, keys in fronts.items():
        if len(keys) > 1:
            errors.append(f"Same German front on several cards {keys}: {text!r}")

    # A context on another card must not show a whole Sentences answer (it would prime or give that card away).
    def bare(text: str) -> str:
        return re.sub(r"[^\wäöüß ]+", "", normalize(text).casefold()).strip()
    sentence_answers = {bare(card.fields["Display"]): card.key for card in by_deck["sentences"]}
    for card in cards:
        if card.front_german:
            front = f" {bare(card.front_german)} "
            for answer, key in sentence_answers.items():
                if key != card.key and len(answer.split()) >= 3 and f" {answer} " in front:
                    if "kind::response" in card.tags:
                        card.interferes.append(key)  # a reply prompt is input, not a cue; keep the pair apart
                    else:
                        errors.append(f"{card.key}: its context contains the answer of {key}")

    # A Vocabulary target must not be repeated as a whole Sentences target.
    vocabulary_answers = {normalize(card.answer).casefold(): card.key for card in by_deck["vocabulary"]}
    for card in by_deck["sentences"]:
        match = vocabulary_answers.get(normalize(card.answer).casefold())
        if match:
            errors.append(f"{card.key}: same target as {match}")

    # Known-word check (warning): context words should already be captured somewhere.
    lexicon = known_lexicon(data)
    names = {token.casefold() for entry in data.entries if entry.pos in {"name", "place"}
             for token in WORD_RE.findall(entry.raw["german"])}
    for card in cards:
        if not card.front_german:
            continue
        unknown = sorted({token for token in WORD_RE.findall(card.front_german)
                          if token.casefold() not in lexicon and token.casefold() not in names and not token[0].isupper()})
        unknown_nouns = sorted({token for token in WORD_RE.findall(card.front_german)
                                if token[0].isupper() and token.casefold() not in lexicon and token.casefold() not in names})
        if unknown or unknown_nouns:
            warnings[card.key].append("words not yet captured: " + ", ".join(unknown + unknown_nouns))
    errors.extend(check_glosses(data, cards))
    errors.extend(check_vocabulary_pages(data))

    # Curated settings must still point at a card (a changed sense would otherwise drop a context silently).
    vocabulary_keys = {card.key.removeprefix("vocab:") for card in by_deck["vocabulary"]}
    for key in data.vocabulary_cards:
        if key not in vocabulary_keys:
            errors.append(f"vocabulary-cards.json: {key!r} matches no card (lemma|sense changed?)")
    article_lemmas = {card.fields["Noun"] for card in by_deck["articles"]}
    for key in data.articles_cards:
        if key not in article_lemmas:
            errors.append(f"articles-cards.json: {key!r} matches no Articles card")
    return errors, warnings


def vocabulary_page_key(text: str) -> str:
    """Comparison form of a DW vocabulary-page item or a captured form: no article, plural, placeholder or end punctuation."""
    text = re.sub(r"\s*\((?:Plural|Singular)\)", "", normalize(text))
    text = re.split(r",\s*die\s", text)[0]
    text = re.sub(r"^(?:der|die|das)\s+|\((?:etwas|jemanden|jemandem)\)\s*|^(?:etwas|jemanden|jemandem)\s+", "", text)
    return re.sub(r"[\s.,!?]+$", "", text).strip()


def check_vocabulary_pages(data: Data) -> list[str]:
    """Every item on a studied lesson's DW vocabulary page is recorded in that lesson (entry, pending or declined)."""
    errors = []
    for lesson in data.lessons:
        page = data.snapshots.vocabulary.get(lesson.id)
        if not page:
            continue
        recorded = {vocabulary_page_key(item.get(field) or "")
                    for bucket in ("entries", "pendingEntries", "declinedEntries") for item in lesson.record.get(bucket, [])
                    for field in ("german", "lemma", "vocabularyPageForm")} - {""}
        for item in page["items"]:
            if vocabulary_page_key(item["german"]) not in recorded:
                errors.append(f"Vocabulary page: {lesson.id} {item['german']!r} ({item['english']}) is not captured; "
                              f"add an entry, or set vocabularyPageForm on the entry it matches ({page['url']})")
    return errors


# --- English meanings that no official glossary supplies are checked against the en.wiktionary snapshot ---
GLOSS_SNAPSHOT_FILE = Path(__file__).resolve().parent / "gloss-snapshot.json"
OFFICIAL_GLOSS_ORIGINS = {"dw-glossary", "dw-culture-page", "vhs-vocabulary-trainer"}
NUMBER_WORDS = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six", "7": "seven",
                "8": "eight", "9": "nine", "10": "ten", "11": "eleven", "12": "twelve", "13": "thirteen",
                "14": "fourteen", "15": "fifteen", "16": "sixteen", "17": "seventeen", "18": "eighteen",
                "19": "nineteen", "20": "twenty", "21": "twenty-one", "30": "thirty", "70": "seventy", "100": "hundred"}
GLOSS_STOPWORDS = {"a", "an", "the", "to", "of", "in", "on", "for", "with", "and", "or", "someone", "something",
                   "not", "short", "form", "e.g.", "eg"}


def gloss_terms(entry) -> list[str]:
    return list(entry.raw.get("glossLookup") or [re.sub(r"[.!?]+$", "", entry.lemma).strip()])


def gloss_check(entry, snapshot: dict) -> str | None:
    """Return None when a meaning part of the English gloss is found in the dictionary definitions, else a reason."""
    if entry.raw.get("glossVerification"):
        return None
    records = [snapshot.get(term) for term in gloss_terms(entry)]
    if any(record is None for record in records):
        return "not looked up yet (run ANKI/harvest_sources.py --glosses)"
    definitions = " ; ".join(item["text"] for record in records for item in record["definitions"]).casefold()
    if not definitions:
        return "no German dictionary entry found"
    for part in re.split(r"[;/]", entry.raw["english"]):
        part = re.sub(r"\([^)]*\)", " ", part).strip().casefold()
        part = NUMBER_WORDS.get(part, part)
        words = [word for word in re.findall(r"[a-z][a-z'-]*", part) if word not in GLOSS_STOPWORDS]
        def found(word: str) -> bool:
            if len(word) < 5:
                return bool(re.search(rf"\b{re.escape(word)}\b", definitions))
            return word[:max(5, len(word) - 3) if len(word) >= 6 else -1] in definitions  # stem: annulled ~ annulment
        if words and all(found(word) for word in words):
            return None
    return f"English {entry.raw['english']!r} not found in: {definitions[:160]}"


def check_glosses(data: Data, cards: list[Card]) -> list[str]:
    snapshot = json.loads(GLOSS_SNAPSHOT_FILE.read_text(encoding="utf-8"))["terms"] if GLOSS_SNAPSHOT_FILE.exists() else {}
    errors = []
    by_ref = {entry.ref: entry for entry in data.entries}
    for card in cards:
        if card.deck != "vocabulary":
            continue
        group = [by_ref[ref] for ref in card.covers]
        if any(OFFICIAL_GLOSS_ORIGINS & set(entry.raw.get("origin", [])) for entry in group):
            continue
        entry = group[0]
        problem = gloss_check(entry, snapshot)
        if problem:
            errors.append(f"Meaning of {card.key} unverified: {problem}")
    return errors
