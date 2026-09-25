#!/usr/bin/env python3
"""Build the curated cumulative sentence/grammar deck without audio."""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import tempfile
import time
import zipfile
from collections import Counter
from pathlib import Path

from anki_package_utils import validate_package


ROOT = Path(__file__).resolve().parent.parent
ANKI = ROOT / "ANKI"
OUT = ANKI / "sentences.apkg"
SOURCES = ANKI / "sentence-sources.json"
INDEX = ANKI / "sentences-scan-index.json"
SEP = "\x1f"
DECK_NAME = "DW A1 — Sentences"

MODEL_NAMES = {
    "production": "German Sentences — contextual production",
    "completion": "German Sentences — contextual completion",
}
LEGACY_MODEL_NAMES = {
    "production": {"German Sentences — type German"},
    "completion": {"German Sentences — complete", "German Sentences — conjugate"},
}
ALL_MANAGED_MODEL_NAMES = {
    "German Sentences — understand", "German Sentences — type German",
    "German Sentences — listen", "German Sentences — complete",
    "German Sentences — choose", "German Sentences — conjugate",
    *MODEL_NAMES.values(),
}

BASE_CSS = """
.card { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; font-size: 22px; text-align: center; color: #20242b; background: #fff; }
.instruction { font-size: 13px; font-weight: 700; color: #687386; letter-spacing: .08em; text-transform: uppercase; margin: 20px 0 10px; }
.prompt { font-size: 28px; font-weight: 650; line-height: 1.4; margin: 12px auto 22px; max-width: 31em; }
.answer { font-size: 29px; font-weight: 700; line-height: 1.4; margin: 10px auto; max-width: 31em; }
.meaning, .note, .source { font-size: 16px; line-height: 1.5; margin: 12px auto; max-width: 38em; }
.meaning { color: #374151; } .note { color: #5d6775; } .source { color: #7b8490; font-size: 13px; }
input { font-size: 22px; padding: 9px; max-width: 92%; }
"""


def now_ms() -> int:
    return int(time.time() * 1000)


def package_template() -> Path:
    for candidate in (ANKI / "vocabulary.apkg", ANKI / "articles.apkg"):
        if candidate.exists():
            return candidate
    raise SystemExit("A cumulative .apkg is needed to initialise the collection schema.")


def model(model_id: int, kind: str, now: int) -> dict:
    if kind == "production":
        fields = ["Cue", "German", "Meaning", "Note", "Source"]
        qfmt = "<div class=instruction>Say it in German</div><div class=prompt>{{Cue}}</div>{{type:German}}"
        afmt = "{{FrontSide}}<hr id=answer><div class=answer>{{German}}</div><div class=meaning>{{Meaning}}</div>{{#Note}}<div class=note>{{Note}}</div>{{/Note}}<div class=source>{{Source}}</div>"
    else:
        fields = ["Prompt", "Answer", "Meaning", "Note", "Source"]
        qfmt = "<div class=instruction>Complete the German</div><div class=prompt>{{Prompt}}</div>{{type:Answer}}"
        afmt = "{{FrontSide}}<hr id=answer><div class=answer>{{Answer}}</div><div class=meaning>{{Meaning}}</div>{{#Note}}<div class=note>{{Note}}</div>{{/Note}}<div class=source>{{Source}}</div>"
    return {
        "id": str(model_id), "name": MODEL_NAMES[kind], "type": 0,
        "mod": now // 1000, "usn": -1, "sortf": 0, "did": None,
        "latexPre": "", "latexPost": "", "latexsvg": False,
        "flds": [{"name": name, "ord": index, "sticky": False, "rtl": False,
                  "font": "Arial", "size": 20, "media": []}
                 for index, name in enumerate(fields)],
        "tmpls": [{"name": "Context → German", "ord": 0, "did": None,
                    "qfmt": qfmt, "afmt": afmt, "bqfmt": "", "bafmt": "",
                    "bfont": "", "bsize": 0}],
        "css": BASE_CSS, "req": [[0, "all", [0, 1]]], "tags": [], "vers": [],
    }


def initialise(collection: Path) -> None:
    with zipfile.ZipFile(package_template()) as archive, archive.open("collection.anki2") as source, collection.open("wb") as target:
        shutil.copyfileobj(source, target)
    now = now_ms()
    deck_id = now + 100
    models = {str(now + index): model(now + index, kind, now) for index, kind in enumerate(MODEL_NAMES)}
    decks = {
        "1": {"id": 1, "name": "Default", "mod": now // 1000, "usn": 0,
              "collapsed": False, "browserCollapsed": False, "newToday": [0, 0],
              "revToday": [0, 0], "lrnToday": [0, 0], "timeToday": [0, 0],
              "conf": 1, "dyn": 0, "extendNew": 10, "extendRev": 50, "desc": ""},
        str(deck_id): {"id": deck_id, "name": DECK_NAME, "mod": now // 1000,
                       "usn": -1, "collapsed": False, "browserCollapsed": False,
                       "newToday": [0, 0], "revToday": [0, 0], "lrnToday": [0, 0],
                       "timeToday": [0, 0], "conf": 1, "dyn": 0,
                       "extendNew": 20, "extendRev": 50,
                       "desc": "Curated source-based German production and grammar in context. No audio or multiple choice."},
    }
    db = sqlite3.connect(collection)
    with db:
        for table in ("cards", "notes", "revlog", "graves"):
            db.execute(f"DELETE FROM {table}")
        db.execute("UPDATE col SET mod = ?, models = ?, decks = ?", (now // 1000, json.dumps(models), json.dumps(decks)))
    db.close()


def sync_models_and_deck(db: sqlite3.Connection) -> tuple[dict[str, int], int, set[int]]:
    models_raw, decks_raw = db.execute("SELECT models, decks FROM col").fetchone()
    models, decks = json.loads(models_raw), json.loads(decks_raw)
    managed_ids = {int(key) for key, value in models.items() if value["name"] in ALL_MANAGED_MODEL_NAMES}
    selected: dict[str, int] = {}
    for kind, current_name in MODEL_NAMES.items():
        current = next((int(key) for key, value in models.items() if value["name"] == current_name), None)
        legacy = next((int(key) for key, value in models.items() if value["name"] in LEGACY_MODEL_NAMES[kind]), None)
        if current is not None:
            selected[kind] = current
        elif legacy is not None and legacy not in selected.values():
            selected[kind] = legacy
        else:
            selected[kind] = max((int(key) for key in models), default=now_ms()) + 1
        models[str(selected[kind])] = model(selected[kind], kind, now_ms())

    for key in list(models):
        if int(key) in managed_ids and int(key) not in selected.values():
            del models[key]

    deck_id = next((int(key) for key, value in decks.items() if value["name"] in {DECK_NAME, "German Sentences — cumulative practice"}), None)
    if deck_id is None:
        raise RuntimeError("Could not find the sentence deck in the package")
    decks[str(deck_id)]["name"] = DECK_NAME
    decks[str(deck_id)]["desc"] = "Curated source-based German production and grammar in context. No audio or multiple choice."
    decks[str(deck_id)]["mod"] = int(time.time())
    db.execute("UPDATE col SET models = ?, decks = ?, mod = ?", (json.dumps(models), json.dumps(decks), int(time.time())))
    return selected, deck_id, managed_ids | set(selected.values())


def note_records() -> list[dict]:
    data = json.loads(SOURCES.read_text(encoding="utf-8"))
    records: list[dict] = []
    seen_keys: set[str] = set()
    seen_targets: set[tuple[str, str]] = set()
    for source in data["sources"]:
        for card in source.get("cards", []):
            kind = card["kind"]
            key = card.get("legacyKey", f"{source['id']}:{card['id']}:{kind}")
            target = (kind, card["answer"].casefold())
            if key in seen_keys or target in seen_targets:
                raise RuntimeError(f"Duplicate sentence-card key or target: {key}")
            seen_keys.add(key)
            seen_targets.add(target)
            first = card["cue"] if kind == "production" else card["prompt"]
            fields = [first, card["answer"], card["meaning"], card.get("note", ""), source["title"]]
            records.append({"key": key, "kind": kind, "skill": card["skill"],
                            "fields": fields, "source": source["id"]})
    return records


def checksum(text: str) -> int:
    return int(hashlib.sha1(text.encode("utf-8")).hexdigest()[:8], 16)


def merge(collection: Path) -> tuple[Counter, int, int]:
    records = note_records()
    db = sqlite3.connect(collection)
    model_ids, deck_id, managed_ids = sync_models_and_deck(db)
    placeholders = ",".join("?" * len(managed_ids))
    existing = {guid: note_id for note_id, guid in db.execute(
        f"SELECT id, guid FROM notes WHERE mid IN ({placeholders})", tuple(managed_ids)
    )}
    desired_guids = {hashlib.sha1(f"german-sentences:{record['key']}".encode("utf-8")).hexdigest()[:10] for record in records}
    next_note = db.execute("SELECT coalesce(max(id), 0) + 1 FROM notes").fetchone()[0]
    next_card = db.execute("SELECT coalesce(max(id), 0) + 1 FROM cards").fetchone()[0]
    next_due = db.execute("SELECT coalesce(max(due), -1) + 1 FROM cards WHERE did = ? AND queue = 0", (deck_id,)).fetchone()[0]
    added: Counter = Counter()
    removed = retired = 0
    now = int(time.time())
    with db:
        for record in records:
            kind, fields = record["kind"], record["fields"]
            guid = hashlib.sha1(f"german-sentences:{record['key']}".encode("utf-8")).hexdigest()[:10]
            field_text = SEP.join(fields)
            tags = f"source::{record['source']} skill::{record['skill'].replace(' ', '-')} interaction::{kind}"
            if guid in existing:
                note_id = existing[guid]
                db.execute("UPDATE notes SET mid = ?, mod = ?, flds = ?, tags = ?, sfld = ?, csum = ? WHERE id = ?",
                           (model_ids[kind], now, field_text, tags, fields[0], checksum(fields[0]), note_id))
                db.execute("UPDATE cards SET did = ?, ord = 0, mod = ? WHERE nid = ?", (deck_id, now, note_id))
                continue
            db.execute("INSERT INTO notes VALUES (?, ?, ?, ?, -1, ?, ?, ?, ?, 0, '')",
                       (next_note, guid, model_ids[kind], now, tags, field_text, fields[0], checksum(fields[0])))
            db.execute("INSERT INTO cards VALUES (?, ?, ?, 0, ?, -1, 0, 0, ?, 0, 2500, 0, 0, 0, 0, 0, 0, '')",
                       (next_card, next_note, deck_id, now, next_due))
            next_note, next_card, next_due = next_note + 1, next_card + 1, next_due + 1
            added[kind] += 1

        stale = [(note_id, guid) for guid, note_id in existing.items() if guid not in desired_guids]
        for note_id, _ in stale:
            card_ids = [row[0] for row in db.execute("SELECT id FROM cards WHERE nid = ?", (note_id,))]
            review_count = 0
            if card_ids:
                marks = ",".join("?" * len(card_ids))
                review_count = db.execute(f"SELECT count(*) FROM revlog WHERE cid IN ({marks})", card_ids).fetchone()[0]
            if review_count:
                db.execute("UPDATE cards SET queue = -1, mod = ? WHERE nid = ?", (now, note_id))
                db.execute("UPDATE notes SET tags = trim(tags || ' retired::quality-overhaul') WHERE id = ?", (note_id,))
                retired += 1
            else:
                db.execute("DELETE FROM cards WHERE nid = ?", (note_id,))
                db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
                removed += 1
        db.execute("UPDATE col SET mod = ?", (now,))
    db.close()
    return added, removed, retired


def package(collection: Path) -> None:
    temporary = OUT.with_suffix(".apkg.tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(collection, "collection.anki2")
        archive.writestr("media", "{}")
    temporary.replace(OUT)


def main() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        collection = Path(temporary) / "collection.anki2"
        if OUT.exists():
            with zipfile.ZipFile(OUT) as archive, archive.open("collection.anki2") as source, collection.open("wb") as target:
                shutil.copyfileobj(source, target)
        else:
            initialise(collection)
        added, removed, retired = merge(collection)
        package(collection)

    result = validate_package(OUT)
    source_data = json.loads(SOURCES.read_text(encoding="utf-8"))["sources"]
    INDEX.write_text(json.dumps({
        "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "deck": DECK_NAME,
        "qualityPolicy": "Manual selection; one distinct retrieval target; no audio, TTS, recognition mirrors, or multiple choice.",
        "sources": [{"id": source["id"], "title": source["title"], "url": source["url"],
                     "cards": len(source.get("cards", []))} for source in source_data],
        "lastRun": {"cardsAdded": dict(added), "obsoleteCardsRemoved": removed,
                    "reviewedObsoleteCardsSuspended": retired, **result},
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created/updated {OUT.name}: {result['cards']} curated cards; added {dict(added)}, removed {removed}, retired {retired}.")


if __name__ == "__main__":
    main()
