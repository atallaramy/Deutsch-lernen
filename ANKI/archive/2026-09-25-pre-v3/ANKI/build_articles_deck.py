#!/usr/bin/env python3
"""Build the cumulative typed German-article deck from durable lesson data."""

from __future__ import annotations

import hashlib
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
OUT = ANKI / "articles.apkg"
INDEX = ANKI / "articles-scan-index.json"
LESSONS = ANKI / "lesson-vocabulary.json"
SEP = "\x1f"
ARTICLE_RE = re.compile(r"^(der|die|das)\s+(.+?)\s*$")
DECK_NAME = "DW A1 — Articles"
MODEL_NAME = "German Articles — typed answers"

QUESTION_FORMAT = "<div class=instruction>Type der, die, or das</div><div class=prompt>{{Prompt}}</div>{{type:Answer}}"
ANSWER_FORMAT = "{{FrontSide}}<hr id=answer><div class=answer>{{Answer}} {{Prompt}}</div>{{#Extra}}<div class=extra>{{Extra}}</div>{{/Extra}}<div class=source>{{Instruction}}</div>"
CARD_CSS = """
.card { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; font-size: 23px; text-align: center; color: #20242b; background: #fff; }
.instruction { font-size: 13px; font-weight: 700; color: #687386; text-transform: uppercase; letter-spacing: .08em; margin: 20px 0 10px; }
.prompt { font-size: 34px; font-weight: 700; margin: 14px 0 24px; }
.answer { font-size: 32px; font-weight: 750; margin: 12px 0 18px; }
.extra { font-size: 17px; line-height: 1.5; color: #465161; margin: 12px auto; max-width: 38em; }
.source { font-size: 13px; color: #7b8490; margin: 16px auto; }
input { font-size: 23px; padding: 9px; max-width: 92%; }
"""


def gender_hint(word: str, article: str) -> str:
    lower = word.casefold()
    feminine = {
        "ung": "Nouns ending in -ung are normally die.",
        "heit": "Nouns ending in -heit are die.",
        "keit": "Nouns ending in -keit are die.",
        "schaft": "Nouns ending in -schaft are die.",
        "ion": "Nouns ending in -ion are normally die.",
        "tät": "Nouns ending in -tät are die.",
        "ik": "Nouns ending in -ik are normally die.",
        "ur": "Nouns ending in -ur are normally die.",
    }
    neuter = {
        "chen": "Diminutives ending in -chen are das.",
        "lein": "Diminutives ending in -lein are das.",
        "ment": "Nouns ending in -ment are normally das.",
        "um": "Nouns ending in -um are normally das.",
        "ma": "Nouns ending in -ma are normally das.",
    }
    patterns = feminine if article == "die" else neuter if article == "das" else {}
    return next((hint for suffix, hint in patterns.items() if lower.endswith(suffix)), "")


def records() -> tuple[list[dict], list[dict]]:
    lessons = json.loads(LESSONS.read_text(encoding="utf-8"))["lessons"]
    nouns: dict[str, dict] = {}
    source_summary = []
    for lesson in lessons:
        found = 0
        for entry in lesson["entries"]:
            match = ARTICLE_RE.match(entry["german"])
            if not match:
                continue
            found += 1
            article, word = match.group(1).casefold(), match.group(2).strip()
            key = word.casefold()
            plural = entry.get("plural", "").strip()
            if key in nouns:
                prior = nouns[key]
                if prior["article"] != article:
                    raise RuntimeError(f"Conflicting articles for {word}: {prior['article']} / {article}")
                if plural and prior["plural"] and plural != prior["plural"]:
                    raise RuntimeError(f"Conflicting plurals for {word}: {prior['plural']} / {plural}")
                if plural:
                    prior["plural"] = plural
                if lesson["id"] not in prior["source_ids"]:
                    prior["source_ids"].append(lesson["id"])
                    prior["source_titles"].append(lesson["title"])
                continue
            nouns[key] = {"word": word, "article": article, "plural": plural,
                          "source_ids": [lesson["id"]], "source_titles": [lesson["title"]]}
        source_summary.append({"id": lesson["id"], "title": lesson["title"],
                               "url": lesson["url"], "nouns": found})
    return sorted(nouns.values(), key=lambda item: item["word"].casefold()), source_summary


def model_and_deck(now: int) -> tuple[int, int, str, str]:
    model_id, deck_id = now, now + 1
    model = {
        str(model_id): {
            "id": str(model_id), "name": MODEL_NAME, "type": 0, "mod": now // 1000,
            "usn": -1, "sortf": 0, "did": deck_id, "latexPre": "", "latexPost": "", "latexsvg": False,
            "flds": [{"name": name, "ord": index, "sticky": False, "rtl": False,
                      "font": "Arial", "size": 20, "media": []}
                     for index, name in enumerate(["Prompt", "Answer", "Instruction", "Extra"])],
            "tmpls": [{"name": "Type the article", "ord": 0, "did": None,
                        "qfmt": QUESTION_FORMAT, "afmt": ANSWER_FORMAT, "bqfmt": "", "bafmt": "", "bfont": "", "bsize": 0}],
            "css": CARD_CSS, "req": [[0, "all", [0, 1]]], "tags": [], "vers": [],
        }
    }
    decks = {
        "1": {"id": 1, "name": "Default", "mod": now // 1000, "usn": 0, "collapsed": False,
              "browserCollapsed": False, "newToday": [0, 0], "revToday": [0, 0], "lrnToday": [0, 0],
              "timeToday": [0, 0], "conf": 1, "dyn": 0, "extendNew": 10, "extendRev": 50, "desc": ""},
        str(deck_id): {"id": deck_id, "name": DECK_NAME, "mod": now // 1000, "usn": -1,
                       "collapsed": False, "browserCollapsed": False, "newToday": [0, 0],
                       "revToday": [0, 0], "lrnToday": [0, 0], "timeToday": [0, 0],
                       "conf": 1, "dyn": 0, "extendNew": 20, "extendRev": 50,
                       "desc": "Type each noun’s article; see its plural and reliable gender clues after answering. No audio."},
    }
    return model_id, deck_id, json.dumps(model), json.dumps(decks)


def initialise(collection: Path) -> None:
    template = ANKI / "vocabulary.apkg"
    if not template.exists():
        raise SystemExit("vocabulary.apkg is needed to initialise the Anki collection schema.")
    with zipfile.ZipFile(template) as archive, archive.open("collection.anki2") as source, collection.open("wb") as target:
        shutil.copyfileobj(source, target)
    now = int(time.time() * 1000)
    _, _, models, decks = model_and_deck(now)
    db = sqlite3.connect(collection)
    with db:
        for table in ("cards", "notes", "revlog", "graves"):
            db.execute(f"DELETE FROM {table}")
        db.execute("UPDATE col SET mod = ?, models = ?, decks = ?", (now // 1000, models, decks))
    db.close()


def ids_and_sync(db: sqlite3.Connection) -> tuple[int, int]:
    models_raw, decks_raw = db.execute("SELECT models, decks FROM col").fetchone()
    models, decks = json.loads(models_raw), json.loads(decks_raw)
    model_id = next(int(key) for key, value in models.items() if value["name"] == MODEL_NAME)
    deck_id = next(int(key) for key, value in decks.items() if value["name"] in {DECK_NAME, "German Articles"})
    current = models[str(model_id)]
    current["flds"] = [{"name": name, "ord": index, "sticky": False, "rtl": False,
                        "font": "Arial", "size": 20, "media": []}
                       for index, name in enumerate(["Prompt", "Answer", "Instruction", "Extra"])]
    current["tmpls"] = [{"name": "Type the article", "ord": 0, "did": None,
                          "qfmt": QUESTION_FORMAT, "afmt": ANSWER_FORMAT,
                          "bqfmt": "", "bafmt": "", "bfont": "", "bsize": 0}]
    current["css"] = CARD_CSS
    current["req"] = [[0, "all", [0, 1]]]
    current["mod"] = int(time.time())
    decks[str(deck_id)]["name"] = DECK_NAME
    decks[str(deck_id)]["desc"] = "Type each noun’s article; see its plural and reliable gender clues after answering. No audio."
    decks[str(deck_id)]["mod"] = int(time.time())
    db.execute("UPDATE col SET models = ?, decks = ?", (json.dumps(models), json.dumps(decks)))
    return model_id, deck_id


def checksum(text: str) -> int:
    return int(hashlib.sha1(text.encode("utf-8")).hexdigest()[:8], 16)


def sync_records(collection: Path, noun_records: list[dict]) -> dict[str, int]:
    db = sqlite3.connect(collection)
    model_id, deck_id = ids_and_sync(db)
    existing = {guid: note_id for note_id, guid in db.execute("SELECT id, guid FROM notes WHERE mid = ?", (model_id,))}
    desired_guids = {hashlib.sha1(f"german-articles:{item['word'].casefold()}".encode("utf-8")).hexdigest()[:10] for item in noun_records}
    next_note = db.execute("SELECT coalesce(max(id), 0) + 1 FROM notes").fetchone()[0]
    next_card = db.execute("SELECT coalesce(max(id), 0) + 1 FROM cards").fetchone()[0]
    next_due = db.execute("SELECT coalesce(max(due), -1) + 1 FROM cards WHERE did = ? AND queue = 0", (deck_id,)).fetchone()[0]
    now = int(time.time())
    added = removed = retired = 0
    with db:
        for item in noun_records:
            guid = hashlib.sha1(f"german-articles:{item['word'].casefold()}".encode("utf-8")).hexdigest()[:10]
            back = []
            if item["plural"]:
                back.append(f"Plural: {item['plural']}")
            hint = gender_hint(item["word"], item["article"])
            if hint:
                back.append(f"Gender pattern: {hint}")
            source = "; ".join(item["source_titles"])
            fields = SEP.join([item["word"], item["article"], source, "<br>".join(back)])
            tags = " ".join(f"source::{source_id}" for source_id in item["source_ids"])
            if guid in existing:
                note_id = existing[guid]
                db.execute("UPDATE notes SET mod = ?, tags = ?, flds = ?, sfld = ?, csum = ? WHERE id = ?",
                           (now, tags, fields, item["word"], checksum(item["word"]), note_id))
                db.execute("UPDATE cards SET did = ?, ord = 0, mod = ? WHERE nid = ?", (deck_id, now, note_id))
                continue
            db.execute("INSERT INTO notes VALUES (?, ?, ?, ?, -1, ?, ?, ?, ?, 0, '')",
                       (next_note, guid, model_id, now, tags, fields, item["word"], checksum(item["word"])))
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
    return {"added": added, "removed": removed, "retired": retired}


def package(collection: Path) -> None:
    temporary = OUT.with_suffix(".apkg.tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(collection, "collection.anki2")
        archive.writestr("media", "{}")
    temporary.replace(OUT)


def main() -> None:
    noun_records, source_summary = records()
    with tempfile.TemporaryDirectory() as temp_name:
        collection = Path(temp_name) / "collection.anki2"
        if OUT.exists():
            with zipfile.ZipFile(OUT) as archive, archive.open("collection.anki2") as source, collection.open("wb") as target:
                shutil.copyfileobj(source, target)
        else:
            initialise(collection)
        changes = sync_records(collection, noun_records)
        package(collection)
    result = validate_package(OUT, expected_cards=len(noun_records) + changes["retired"])
    INDEX.write_text(json.dumps({
        "deck": "articles.apkg",
        "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "qualityPolicy": "Typed article recall only; plural and dependable gender patterns appear after answering; no audio.",
        "sources": source_summary,
        "lastRun": {**changes, **result},
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created/updated {OUT.name}: {result['cards']} article cards; added {changes['added']}, removed {changes['removed']}.")


if __name__ == "__main__":
    main()
