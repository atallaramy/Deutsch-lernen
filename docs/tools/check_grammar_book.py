#!/usr/bin/env python3
"""Check the grammar book (Grammatik/) against the lesson snapshots, the learner's notes and the Sentences cards.

Offline check: `python3 docs/tools/check_grammar_book.py` (exit status 1 on any error).
Network step: `python3 docs/tools/check_grammar_book.py fetch` snapshots the Wiktionary present-tense
table of every verb used in a conjugation table into Grammatik/Materials/wiktionary-snapshot.json.

Page conventions the check relies on (see Grammatik/README.md):
- A table whose last column is "Source" quotes German verbatim in every column headed "German…".
  Its Source cell names the lesson snapshot, e.g. "[DW A1 E1 L3 · script](…)" or "VHS A1 L2 · phrase trainer".
- A table with "Wrong" and "From" columns quotes the learner's own error from the notes file linked in "From".
- A table whose first column is "Person" is a conjugation table; each verb column must match Wiktionary.
- Backticked keys under "## Sentences cards" must be live cards in ANKI/sentence-sources.json.
- Every DW grammar page (gr-) in a studied lesson's snapshot must be linked from some topic page.
- A Sentences card with a grammarPage is listed under "## Sentences cards" on a topic page that links that page.
- A page's "German terms" list gives each word as in Grammatikbegriffe.md: its synonyms together
  (split by " / ") and, in parentheses, the same English cell (English and a short description).
  Every word there is in the "German terms" of the page its row links to.
- Every word in a studied DW lesson's "Grammatical terms in German" box is in Grammatikbegriffe.md, and its
  description there is a verbatim excerpt of the box's description.
- Grammatikbegriffe.md's first column lists the same words as the cheatsheet Spickzettel/Grammatikbegriffe.md.
"""

from __future__ import annotations

import datetime
import html
import json
import re
import sys
import time
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOOK = ROOT / "Grammatik"
SNAPSHOT = BOOK / "Materials" / "wiktionary-snapshot.json"
GLOSSARY = "Grammatikbegriffe.md"
MISTAKES = "Meine-Fehler.md"  # the learner's recurring mistakes; printed just before GLOSSARY
SHEETS = ROOT / "Spickzettel"
COLOUR_RULES = SHEETS / "Farben.md"  # the colour rules: a cheatsheet that also opens the grammar book
# One colour, one meaning, in the grammar book and every cheatsheet. A new one needs the learner's yes.
COLOURS = {
    "nom": ("Nominativ", "#1f5f8b"),
    "akk": ("Akkusativ", "#a33b20"),
    "dat": ("Dativ", "#2e7d4f"),
    "gen": ("Genitiv", "#6b3fa0"),
    "verb": ("Verb", "#d97706"),
}
HTML_TAGS = {"b", "i", "small", "div", "h2", "br"}
LAYOUT_CLASSES = {"case", "foot"}
TAG_RE = re.compile(r"<\s*/?\s*([A-Za-z][A-Za-z0-9]*)([^>]*)>")
CHEATSHEET = ROOT / "Spickzettel" / GLOSSARY
sys.path.insert(0, str(ROOT / "ANKI"))

import deck_data  # noqa: E402

LINK_RE = re.compile(r"\[([^\]]*)\]\((<[^>]*>|[^)\s]*)\)")
TERMS_RE = re.compile(r"^German terms.*?(?=\n\s*\n|\Z)", re.S | re.M)
ITALIC_RE = re.compile(r"\*([^*]+)\*")
# One "German terms" entry: *word* / *synonym* (English: description), one nested pair of parentheses allowed.
ENTRY_RE = re.compile(r"(\*[^*]+\*(?:\s*/\s*\*[^*]+\*)*)\s*\(((?:[^()]|\([^()]*\))*)\)")
BOX = "Grammatical terms in German:"  # DW grammar pages end with this box of "word: description" lines
BOX_TERM_RE = re.compile(r"^(?:(?:der|die|das) \S.*|[a-zäöü]+)$")
SOURCE_RE = re.compile(r"^(DW|VHS) (A1|A2|B1) (?:E(\d+) )?L(\d+) · (.+)$")
# Source label kind → snapshot source id (DW ids) or id suffix (VHS ids such as vhs-a1-filmskripte).
SOURCE_KINDS = {
    "script": "script", "exercise": "exercises", "grammar page": "exercises", "culture page": "exercises",
    "film script": "filmskripte", "word list": "wortschatzlisten", "phrase trainer": "phrasentrainer",
    "vocabulary trainer": "vokabeltrainer",
}
PERSONS = {"ich": ["1s"], "du": ["2s"], "er/sie/es": ["3s"], "wir": ["1p"], "ihr": ["2p"], "sie": ["3p"],
           "Sie": ["3p"], "sie/Sie": ["3p"]}
WIKTIONARY_PERSONS = {"1. Person Singular": "1s", "2. Person Singular": "2s", "3. Person Singular": "3s",
                      "1. Person Plural": "1p", "2. Person Plural": "2p", "3. Person Plural": "3p"}


@dataclass
class Table:
    header: list[str]
    rows: list[list[str]]
    section: str


@dataclass
class Word:
    terms: tuple[str, ...]
    english: str
    page: str


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=lambda: {"pages": 0, "quotes": 0, "learner quotes": 0,
                                                             "verb forms": 0, "card keys": 0, "links": 0,
                                                             "grammar words": 0})


def plain(cell: str) -> str:
    """Visible text of a Markdown cell: link texts, no emphasis, colour tags or code marks."""
    text = LINK_RE.sub(lambda m: m.group(1), cell)
    text = re.sub(r"</?[A-Za-z][^>]*>", "", text)
    return re.sub(r"[*_`]", "", text).strip()


def link_targets(cell: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2).strip("<>")) for m in LINK_RE.finditer(cell)]


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def tables(page: str) -> list[Table]:
    found, section, lines = [], "", page.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].startswith("## "):
            section = lines[i][3:].strip()
        if lines[i].startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|?$", lines[i + 1].strip()):
            header, rows, i = split_row(lines[i]), [], i + 2
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            found.append(Table(header, rows, section))
            continue
        i += 1
    return found


def section_text(page: str, title: str) -> str:
    match = re.search(rf"^## {re.escape(title)}\n(.*?)(?=^## |\Z)", page, re.S | re.M)
    return match.group(1) if match else ""


def listed_terms(page: str) -> set[str]:
    """Grammar words in the first column of a page's tables."""
    return {term.strip() for table in tables(page) for row in table.rows for term in plain(row[0]).split(" / ")}


def words_text(text: str) -> str:
    return " ".join(plain(text).split())


def glossary_words(page: str) -> dict[str, Word]:
    """Grammatikbegriffe.md rows by word: the row's synonyms, its English cell and the page it links to."""
    words = {}
    for table in tables(page):
        for row in table.rows:
            terms = tuple(term.strip() for term in plain(row[0]).split(" / "))
            links = link_targets(row[2]) if len(row) > 2 else []
            word = Word(terms, words_text(row[1]) if len(row) > 1 else "", links[0][1] if links else "")
            words.update(dict.fromkeys(terms, word))
    return words


def check_terms(page: str, words: dict[str, Word], where: str, report: Report) -> set[str]:
    """Each word in a page's "German terms" list is written as in Grammatikbegriffe.md; returns the words."""
    match = TERMS_RE.search(page)
    if not match:
        return set()
    block, listed = match.group(0).split(":", 1)[-1], set()
    for entry in ENTRY_RE.finditer(block):
        terms = [" ".join(term.split()) for term in ITALIC_RE.findall(entry.group(1))]
        listed.update(terms)
        missing = [term for term in terms if term not in words]
        for term in missing:
            report.errors.append(f"{where}: grammar word {term!r} is missing from {GLOSSARY}")
        if missing:
            continue
        word = words[terms[0]]
        listed.update(word.terms)  # one error for a missing synonym, not a second one from check_word_pages
        if sorted(terms) != sorted(word.terms):
            report.errors.append(f"{where}: give {' / '.join(word.terms)!r} together, as in {GLOSSARY}")
        elif words_text(entry.group(2)) != word.english:
            report.errors.append(f"{where}: {terms[0]!r} needs its {GLOSSARY} description: ({word.english})")
    for term in ITALIC_RE.findall(ENTRY_RE.sub("", block)):
        term = " ".join(term.split())
        listed.add(term)
        report.errors.append(f"{where}: grammar word {term!r} needs its {GLOSSARY} description in parentheses")
    return listed


def comparable(text: str) -> str:
    """Comparison form for descriptions; DW sometimes puts a space before a full stop."""
    return re.sub(r"\s+([.,;:!?])", r"\1", deck_data.normalize(text))


def lesson_descriptions(data: deck_data.Data) -> dict[str, list[tuple[str, str]]]:
    """Word → (description, lesson id) from the "Grammatical terms in German" boxes of the studied lessons."""
    found: dict[str, list[tuple[str, str]]] = {}
    for lesson in data.lessons:
        path = ROOT / lesson.record.get("snapshot", "")
        if not lesson.record.get("sources") or not path.is_file():
            continue
        for source in json.loads(path.read_text(encoding="utf-8"))["sources"]:
            for item in source.get("exercises", []) + source.get("pages", []):
                for text in item["texts"]:
                    for line in text.partition(BOX)[2].split("\n"):
                        term, sep, description = (part.strip() for part in line.partition(": "))
                        if sep and BOX_TERM_RE.match(term):
                            found.setdefault(term, []).append((comparable(description), lesson.id))
    return found


def check_lesson_descriptions(words: dict[str, Word], boxes: dict[str, list[tuple[str, str]]],
                              report: Report) -> None:
    """A word the lessons describe is in Grammatikbegriffe.md with (an excerpt of) the lesson's description."""
    for term, found in sorted(boxes.items()):
        lessons = ", ".join(sorted({lesson for _, lesson in found}))
        if term not in words:
            report.errors.append(f"{GLOSSARY}: grammar word {term!r} ({lessons}) is missing")
            continue
        own = comparable(words[term].english.partition(": ")[2] or words[term].english)
        if not any(own in description for description, _ in found):
            report.errors.append(f"{GLOSSARY}: {term!r} must use the lesson's description ({lessons}): "
                                 f"{found[0][0]!r}")


def check_word_pages(words: dict[str, Word], glossary_path: Path, described: dict[Path, set[str]],
                     report: Report) -> None:
    """Every grammar word is in the "German terms" list of the page its row links to."""
    for term, word in sorted(words.items()):
        if not word.page or word.page.startswith(("http://", "https://")):
            continue
        path = (glossary_path.parent / urllib.parse.unquote(word.page.split("#")[0])).resolve()
        if path in described and term not in described[path]:
            report.errors.append(f"{GLOSSARY}: {term!r} is not in the German terms of {word.page}")


def check_cheatsheet(glossary: set[str], cheatsheet: Path, report: Report) -> None:
    where = f"Spickzettel/{cheatsheet.name}"
    if not cheatsheet.exists():
        report.errors.append(f"{where}: missing")
        return
    listed = listed_terms(cheatsheet.read_text(encoding="utf-8"))
    for term in sorted(glossary - listed):
        report.errors.append(f"{where}: missing grammar word {term!r} (in Grammatik/{GLOSSARY})")
    for term in sorted(listed - glossary):
        report.errors.append(f"{where}: grammar word {term!r} is not in Grammatik/{GLOSSARY}")


def lesson_labels(data: deck_data.Data) -> dict[str, str]:
    labels = {}
    for lesson in data.lessons:
        record = lesson.record
        if lesson.course["id"] == "dw-nicos-weg":
            labels[f"DW {record['level']} E{record['unit']} L{record['lesson']}"] = lesson.id
        elif lesson.course["id"] == "vhs-lernportal":
            labels[f"VHS {record['level']} L{record['lesson']}"] = lesson.id
    return labels


def source_ids(data: deck_data.Data, label: str, labels: dict[str, str]) -> tuple[str, list[str]] | str:
    """Snapshot (lesson id, source ids) for a source label, or an error message."""
    match = SOURCE_RE.match(label)
    if not match:
        return f"unreadable source label {label!r}"
    course, level, unit, number, kind = match.groups()
    key = f"{course} {level} E{unit} L{number}" if course == "DW" else f"{course} {level} L{number}"
    if key not in labels:
        return f"{key} is not a captured lesson (only studied lessons can be quoted)"
    if kind not in SOURCE_KINDS:
        return f"unknown source kind {kind!r} in {label!r}"
    lesson_id, wanted = labels[key], SOURCE_KINDS[kind]
    ids = [sid for lid, sid in data.snapshots.texts if lid == lesson_id and (sid == wanted or sid.endswith("-" + wanted))]
    return (lesson_id, ids) if ids else f"{key} has no {kind} snapshot"


def check_quotes(data, table: Table, labels, where: str, report: Report) -> None:
    columns = [i for i, name in enumerate(table.header) if plain(name).startswith("German")]
    for row in table.rows:
        sources = []
        for text, _ in link_targets(row[-1]) or [(plain(row[-1]), "")]:
            resolved = source_ids(data, text, labels)
            if isinstance(resolved, str):
                report.errors.append(f"{where}: {resolved}")
            else:
                sources.append(resolved)
        for i in columns:
            quote = plain(row[i]) if i < len(row) else ""
            if not quote or quote == "—":
                continue
            report.counts["quotes"] += 1
            if sources and not any(data.snapshots.contains(lid, sid, quote) for lid, ids in sources for sid in ids):
                report.errors.append(f"{where}: not verbatim in {plain(row[-1])}: {quote!r}")


def check_learner_quotes(table: Table, page_path: Path, where: str, report: Report) -> None:
    wrong, source = table.header.index("Wrong"), table.header.index("From")
    for row in table.rows:
        notes = [target for _, target in link_targets(row[source]) if not target.startswith("http")]
        if not notes:
            continue
        report.counts["learner quotes"] += 1
        quote = deck_data.normalize(plain(row[wrong]))
        texts = []
        for target in notes:
            path = (page_path.parent / urllib.parse.unquote(target)).resolve()
            if path.exists():
                texts.append(deck_data.normalize(path.read_text(encoding="utf-8")))
        if not any(quote in text for text in texts):
            report.errors.append(f"{where}: {quote!r} is not in the linked notes")


def check_conjugation(table: Table, verbs: dict, where: str, report: Report) -> None:
    for column, name in enumerate(table.header[1:], start=1):
        verb = plain(name)
        if verb == "Endung":
            continue
        if verb not in verbs:
            report.errors.append(f"{where}: no Wiktionary snapshot for {verb!r}; run check_grammar_book.py fetch")
            continue
        for row in table.rows:
            person = plain(row[0])
            if person not in PERSONS:
                report.errors.append(f"{where}: unknown person {person!r}")
                continue
            form = plain(row[column]) if column < len(row) else ""
            report.counts["verb forms"] += 1
            allowed = {alt for key in PERSONS[person] for alt in verbs[verb]["praesens"].get(key, [])}
            if form not in allowed:
                report.errors.append(f"{where}: {verb}, {person}: {form!r} (Wiktionary: {sorted(allowed)})")


def check_colours(page: str, where: str, report: Report) -> None:
    """Colour only through the fixed COLOURS tags and classes; never a style or a colour of its own."""
    text = re.sub(r"<https?://[^>]*>", "", LINK_RE.sub(lambda m: m.group(1), page))
    for tag, attributes in TAG_RE.findall(text):
        if tag.lower() not in COLOURS and tag.lower() not in HTML_TAGS:
            report.errors.append(f"{where}: <{tag}> is not on the colour list ({', '.join(COLOURS)})")
        if re.search(r"style\s*=|colou?r", attributes, re.I):
            report.errors.append(f"{where}: <{tag}{attributes}>: colours come only from the colour list")
        for name in " ".join(re.findall(r'class\s*=\s*"([^"]*)"', attributes)).split():
            if name not in COLOURS and name not in LAYOUT_CLASSES:
                report.errors.append(f"{where}: class {name!r} is not on the colour list")


def check_colour_rules(report: Report, rules: Path = COLOUR_RULES) -> None:
    text = rules.read_text(encoding="utf-8") if rules.exists() else ""
    for tag, (meaning, _) in COLOURS.items():
        if f"<{tag}>" not in text or meaning not in text:
            report.errors.append(f"Spickzettel/{rules.name}: the colour rules must show {meaning} (<{tag}>)")


def check_links(page: str, page_path: Path, where: str, report: Report) -> None:
    for _, target in LINK_RE.findall(page):
        target = target.strip("<>")
        if not target or target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        report.counts["links"] += 1
        if not (page_path.parent / urllib.parse.unquote(target.split("#")[0])).exists():
            report.errors.append(f"{where}: broken link {target}")


def check_cards(page: str, cards: dict, where: str, report: Report) -> None:
    for key in re.findall(r"`([^`]+)`", section_text(page, "Sentences cards")):
        report.counts["card keys"] += 1
        if key not in cards:
            report.errors.append(f"{where}: unknown Sentences card {key!r}")
        elif cards[key].get("retired"):
            report.errors.append(f"{where}: Sentences card {key!r} is retired")


def check_grammar_pages(data: deck_data.Data, linked: set[str], report: Report) -> None:
    """Every DW grammar page (gr-) of a studied lesson is linked from a topic page."""
    for lesson in data.lessons:
        for page in data.snapshots.pages.get(lesson.id, []):
            if page["id"].startswith("gr-") and page["id"] not in linked:
                report.errors.append(f"DW grammar page {page['title'].strip()!r} of {lesson.id} is not linked from any "
                                     f"topic page: {page['url']}")


def check_page_cards(cards: dict, listed: dict[str, set[str]], report: Report) -> None:
    """A Sentences card that practises a DW grammar page is listed on a topic page that links that page."""
    for key, card in cards.items():
        page = card.get("grammarPage")
        if page and not card.get("retired") and key not in listed.get(page, set()):
            report.errors.append(f"Sentences card {key!r} practises DW grammar page {page} but is not listed under "
                                 f"'Sentences cards' on the topic page that links it")


def check(book: Path = BOOK, data: deck_data.Data | None = None, snapshot: Path | None = None,
          grammar_pages: bool = True, cheatsheet: Path = CHEATSHEET) -> Report:
    data = data or deck_data.load()
    snapshot = snapshot or book / "Materials" / "wiktionary-snapshot.json"
    verbs = json.loads(snapshot.read_text(encoding="utf-8")).get("verbs", {}) if snapshot.exists() else {}
    labels, cards = lesson_labels(data), {card["key"]: card for card in data.sentence_cards}
    report = Report()
    index = (book / "README.md").read_text(encoding="utf-8") if (book / "README.md").exists() else ""
    linked: set[str] = set()
    listed: dict[str, set[str]] = {}  # gr- page id → card keys listed on the topic pages that link it
    glossary_path = book / GLOSSARY
    words = glossary_words(glossary_path.read_text(encoding="utf-8")) if glossary_path.exists() else {}
    report.counts["grammar words"] = len(words)
    described: dict[Path, set[str]] = {}
    for page_path in sorted(book.rglob("*.md")):
        if "Materials" in page_path.relative_to(book).parts:
            continue
        page, where = page_path.read_text(encoding="utf-8"), str(page_path.relative_to(book))
        if page_path != glossary_path:  # its DW links stand in for topic pages not written yet
            page_links = set(re.findall(r"/(gr-\d+)\b", " ".join(target for _, target in LINK_RE.findall(page))))
            linked |= page_links
            keys = set(re.findall(r"`([^`]+)`", section_text(page, "Sentences cards")))
            for gr in page_links:
                listed.setdefault(gr, set()).update(keys)
        report.counts["pages"] += 1
        if page_path.name != "README.md" and where not in {urllib.parse.unquote(t.strip("<>")) for _, t in LINK_RE.findall(index)}:
            report.errors.append(f"{where}: not listed in Grammatik/README.md")
        for table in tables(page):
            if plain(table.header[-1]) == "Source":
                check_quotes(data, table, labels, where, report)
            if "Wrong" in table.header and "From" in table.header:
                check_learner_quotes(table, page_path, where, report)
            if plain(table.header[0]) == "Person":
                check_conjugation(table, verbs, where, report)
        check_links(page, page_path, where, report)
        check_colours(page, where, report)
        check_cards(page, cards, where, report)
        described[page_path.resolve()] = check_terms(page, words, where, report)
    if glossary_path.exists():
        check_word_pages(words, glossary_path, described, report)
        check_cheatsheet(set(words), cheatsheet, report)
    for sheet in sorted(cheatsheet.parent.glob("*.md")):
        check_colours(sheet.read_text(encoding="utf-8"), f"Spickzettel/{sheet.name}", report)
    if cheatsheet == CHEATSHEET:
        check_colour_rules(report)
    if grammar_pages:
        check_grammar_pages(data, linked, report)
        check_page_cards(cards, listed, report)
        check_lesson_descriptions(words, lesson_descriptions(data), report)
    return report


def wiktionary_praesens(verb: str) -> dict:
    """Present indicative (active) forms from the de.wiktionary conjugation page."""
    from harvest_sources import fetch  # network helper; only needed here

    url = "https://de.wiktionary.org/wiki/Flexion:" + verb
    page = re.sub(r"<style.*?</style>", "", fetch(url).decode("utf-8"), flags=re.S)
    forms, inside = {}, False
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", page, flags=re.S):
        cells = [html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", c))).strip()
                 for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", row, flags=re.S)]
        if cells == ["Präsens"]:
            inside = True
        elif inside and cells == ["Präteritum"]:
            break
        elif inside and len(cells) > 1 and cells[0] in WIKTIONARY_PERSONS:
            alternatives = [a.strip() for a in cells[1].split(",") if "veraltet" not in a]
            forms[WIKTIONARY_PERSONS[cells[0]]] = [a.split(" ", 1)[1].strip() if " " in a else a for a in alternatives]
    if len(forms) != 6:
        raise RuntimeError(f"Could not read the present tense of {verb!r} at {url}")
    return {"url": url, "fetchedOn": datetime.date.today().isoformat(), "praesens": forms}


def fetch_verbs(book: Path = BOOK) -> None:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8")) if SNAPSHOT.exists() else {
        "description": "Dictionary evidence for the grammar book. 'verbs' is written by "
                       "docs/tools/check_grammar_book.py fetch; 'evidence' records one-off checks."}
    verbs = snapshot.setdefault("verbs", {})
    wanted = sorted({plain(name) for page in book.rglob("*.md") for table in tables(page.read_text(encoding="utf-8"))
                     if plain(table.header[0]) == "Person" for name in table.header[1:] if plain(name) != "Endung"})
    for verb in wanted:
        if verb not in verbs:
            verbs[verb] = wiktionary_praesens(verb)
            print(f"fetched {verb}")
            time.sleep(0.5)
    snapshot["verbs"] = dict(sorted(verbs.items()))
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main() -> None:
    if sys.argv[1:] == ["fetch"]:
        fetch_verbs()
        return
    report = check()
    for error in report.errors:
        print("ERROR", error)
    summary = ", ".join(f"{count} {name}" for name, count in report.counts.items())
    print(f"Grammar book: {summary}; {len(report.errors)} errors")
    sys.exit(1 if report.errors else 0)


if __name__ == "__main__":
    main()
