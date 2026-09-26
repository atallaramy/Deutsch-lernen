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
sys.path.insert(0, str(ROOT / "ANKI"))

import deck_data  # noqa: E402

LINK_RE = re.compile(r"\[([^\]]*)\]\((<[^>]*>|[^)\s]*)\)")
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
class Report:
    errors: list[str] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=lambda: {"pages": 0, "quotes": 0, "learner quotes": 0,
                                                             "verb forms": 0, "card keys": 0, "links": 0})


def plain(cell: str) -> str:
    """Visible text of a Markdown cell: link texts, no emphasis or code marks."""
    text = LINK_RE.sub(lambda m: m.group(1), cell)
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


def check(book: Path = BOOK, data: deck_data.Data | None = None, snapshot: Path | None = None) -> Report:
    data = data or deck_data.load()
    snapshot = snapshot or book / "Materials" / "wiktionary-snapshot.json"
    verbs = json.loads(snapshot.read_text(encoding="utf-8")).get("verbs", {}) if snapshot.exists() else {}
    labels, cards = lesson_labels(data), {card["key"]: card for card in data.sentence_cards}
    report = Report()
    index = (book / "README.md").read_text(encoding="utf-8") if (book / "README.md").exists() else ""
    for page_path in sorted(book.rglob("*.md")):
        if "Materials" in page_path.relative_to(book).parts:
            continue
        page, where = page_path.read_text(encoding="utf-8"), str(page_path.relative_to(book))
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
        check_cards(page, cards, where, report)
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
