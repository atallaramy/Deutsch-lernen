#!/usr/bin/env python3
"""Deterministic Anki package writer and validator shared by every deck builder.

Packages use the Anki schema 11 `collection.anki2` layout, built from embedded DDL so no
other package is ever copied. IDs derive from stable keys; timestamps derive from the data
revision, so identical inputs produce byte-identical `.apkg` files.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

FIELD_SEP = "\x1f"
AUDIO_MARKERS = ("[sound:", "{{tts", "tts-voices", "<audio", "<video", "<img")
ID_BASE_MS = 1_735_689_600_000  # 2025-01-01T00:00:00Z; hashed IDs fall within the following ~115 days.
ID_SPAN = 10_000_000_000

SCHEMA_SQL = """
CREATE TABLE col (id integer primary key, crt integer not null, mod integer not null, scm integer not null,
  ver integer not null, dty integer not null, usn integer not null, ls integer not null, conf text not null,
  models text not null, decks text not null, dconf text not null, tags text not null);
CREATE TABLE notes (id integer primary key, guid text not null, mid integer not null, mod integer not null,
  usn integer not null, tags text not null, flds text not null, sfld integer not null, csum integer not null,
  flags integer not null, data text not null);
CREATE TABLE cards (id integer primary key, nid integer not null, did integer not null, ord integer not null,
  mod integer not null, usn integer not null, type integer not null, queue integer not null, due integer not null,
  ivl integer not null, factor integer not null, reps integer not null, lapses integer not null, left integer not null,
  odue integer not null, odid integer not null, flags integer not null, data text not null);
CREATE TABLE revlog (id integer primary key, cid integer not null, usn integer not null, ease integer not null,
  ivl integer not null, lastIvl integer not null, factor integer not null, time integer not null, type integer not null);
CREATE TABLE graves (usn integer not null, oid integer not null, type integer not null);
CREATE INDEX ix_notes_usn on notes (usn);
CREATE INDEX ix_cards_usn on cards (usn);
CREATE INDEX ix_revlog_usn on revlog (usn);
CREATE INDEX ix_cards_nid on cards (nid);
CREATE INDEX ix_cards_sched on cards (did, queue, due);
CREATE INDEX ix_revlog_cid on revlog (cid);
CREATE INDEX ix_notes_csum on notes (csum);
"""


@dataclass(frozen=True)
class NoteType:
    name: str
    fields: tuple[str, ...]
    qfmt: str
    afmt: str
    css: str


@dataclass
class Note:
    key: str
    note_type: NoteType
    fields: dict[str, str]
    tags: list[str] = field(default_factory=list)
    due: int = 0
    suspended: bool = False


@dataclass
class DeckSpec:
    name: str
    description: str
    output: Path
    guid_namespace: str
    notes: list[Note]


def stable_int(key: str) -> int:
    return ID_BASE_MS + int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:15], 16) % ID_SPAN


def guid_for(key: str) -> str:
    return hashlib.sha1(f"german-anki-v3:{key}".encode("utf-8")).hexdigest()[:10]


def checksum(text: str) -> int:
    return int(hashlib.sha1(text.encode("utf-8")).hexdigest()[:8], 16)


def revision_epoch(revision: str) -> int:
    return int(datetime.fromisoformat(revision.replace("Z", "+00:00")).timestamp())


def _model_json(note_type: NoteType, deck_id: int, mod: int) -> dict:
    model_id = stable_int(f"notetype:{note_type.name}")
    return {
        "id": model_id, "name": note_type.name, "type": 0, "mod": mod, "usn": -1, "sortf": 0, "did": deck_id,
        "latexPre": "", "latexPost": "", "latexsvg": False, "tags": [], "vers": [], "css": note_type.css,
        "flds": [{"name": name, "ord": index, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": []}
                 for index, name in enumerate(note_type.fields)],
        "tmpls": [{"name": "Card 1", "ord": 0, "did": None, "qfmt": note_type.qfmt, "afmt": note_type.afmt,
                   "bqfmt": "", "bafmt": "", "bfont": "", "bsize": 0}],
        "req": [[0, "any", [0]]],
    }


def write_package(spec: DeckSpec, revision: str, path: Path) -> None:
    """Write `spec` to `path` deterministically (same inputs → same bytes)."""
    mod = revision_epoch(revision)
    deck_id = stable_int(f"deck:{spec.name}")
    note_types = {note.note_type.name: note.note_type for note in spec.notes}
    models = {str(stable_int(f"notetype:{name}")): _model_json(nt, deck_id, mod) for name, nt in sorted(note_types.items())}
    deck_common = {"collapsed": False, "browserCollapsed": False, "newToday": [0, 0], "revToday": [0, 0],
                   "lrnToday": [0, 0], "timeToday": [0, 0], "conf": 1, "dyn": 0, "extendNew": 10, "extendRev": 50}
    decks = {"1": {"id": 1, "name": "Default", "mod": mod, "usn": 0, "desc": "", **deck_common},
             str(deck_id): {"id": deck_id, "name": spec.name, "mod": mod, "usn": -1, "desc": spec.description, **deck_common}}
    dconf = {"1": {"id": 1, "name": "Default", "mod": 0, "usn": 0, "maxTaken": 60, "timer": 0, "autoplay": False,
                   "replayq": False, "new": {"bury": True, "delays": [1, 10], "initialFactor": 2500, "ints": [1, 4, 7],
                                             "order": 1, "perDay": 20, "separate": True},
                   "lapse": {"delays": [10], "leechAction": 1, "leechFails": 8, "minInt": 1, "mult": 0},
                   "rev": {"bury": True, "ease4": 1.3, "fuzz": 0.05, "ivlFct": 1, "maxIvl": 36500, "minSpace": 1, "perDay": 200}}}
    conf = {"activeDecks": [1], "addToCur": True, "collapseTime": 1200, "curDeck": 1,
            "curModel": next(iter(models)), "dueCounts": True, "estTimes": True, "newBury": True, "newSpread": 0,
            "nextPos": len(spec.notes) + 1, "sortBackwards": False, "sortType": "noteFld", "timeLim": 0}

    rows = []
    for note in spec.notes:
        key = f"{spec.guid_namespace}:{note.key}"
        values = [note.fields.get(name, "") for name in note.note_type.fields]
        rows.append((stable_int(f"note:{key}"), guid_for(key), stable_int(f"notetype:{note.note_type.name}"),
                     " ".join(sorted(set(note.tags))), FIELD_SEP.join(values), values[0], stable_int(f"card:{key}"), note.due,
                     -1 if note.suspended else 0))
    ids = [row[0] for row in rows] + [row[6] for row in rows]
    if len(set(ids)) != len(ids):
        raise RuntimeError(f"{spec.name}: hashed note/card ID collision; change a card key")

    with tempfile.TemporaryDirectory() as temp_name:
        collection = Path(temp_name) / "collection.anki2"
        db = sqlite3.connect(collection)
        db.executescript(SCHEMA_SQL)
        db.execute("INSERT INTO col VALUES (1, ?, ?, ?, 11, 0, 0, 0, ?, ?, ?, ?, '{}')",
                   (mod - mod % 86400, mod, mod * 1000, json.dumps(conf, sort_keys=True), json.dumps(models, sort_keys=True),
                    json.dumps(decks, sort_keys=True), json.dumps(dconf, sort_keys=True)))
        for note_id, guid, model_id, tags, flds, sfld, card_id, due, queue in sorted(rows):
            db.execute("INSERT INTO notes VALUES (?, ?, ?, ?, -1, ?, ?, ?, ?, 0, '')",
                       (note_id, guid, model_id, mod, f" {tags} " if tags else "", flds, sfld, checksum(sfld)))
            db.execute("INSERT INTO cards VALUES (?, ?, ?, 0, ?, -1, 0, ?, ?, 0, 0, 0, 0, 0, 0, 0, 0, '')",
                       (card_id, note_id, deck_id, mod, queue, due))
        db.commit()
        db.execute("VACUUM")
        db.close()
        date_time = datetime.fromtimestamp(mod, tz=timezone.utc).timetuple()[:6]
        path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, "w") as archive:
            for name, payload in (("collection.anki2", collection.read_bytes()), ("media", b"{}")):
                info = zipfile.ZipInfo(name, date_time=date_time)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, payload)


def validate_package(path: Path, *, expected_cards: int | None = None) -> dict[str, int]:
    """Validate SQLite integrity, links, counts, one typed answer per template, empty media, and the audio ban."""
    if not path.exists():
        raise RuntimeError(f"Missing Anki package: {path}")
    with tempfile.TemporaryDirectory() as temp_name, zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        if names != {"collection.anki2", "media"}:
            raise RuntimeError(f"{path.name}: unexpected archive members {sorted(names)}")
        if json.loads(archive.read("media")):
            raise RuntimeError(f"{path.name} contains media despite the no-media rule")
        collection = Path(temp_name) / "collection.anki2"
        collection.write_bytes(archive.read("collection.anki2"))
        db = sqlite3.connect(collection)
        try:
            if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError(f"{path.name}: SQLite integrity check failed")
            notes = db.execute("SELECT count(*) FROM notes").fetchone()[0]
            cards = db.execute("SELECT count(*) FROM cards").fetchone()[0]
            orphans = db.execute("SELECT count(*) FROM cards LEFT JOIN notes ON notes.id = cards.nid WHERE notes.id IS NULL").fetchone()[0]
            childless = db.execute("SELECT count(*) FROM notes LEFT JOIN cards ON cards.nid = notes.id WHERE cards.id IS NULL").fetchone()[0]
            if orphans or childless:
                raise RuntimeError(f"{path.name}: {orphans} orphan card(s), {childless} note(s) without a card")
            if db.execute("SELECT count(*) FROM revlog").fetchone()[0]:
                raise RuntimeError(f"{path.name}: a freshly built package must not contain review history")
            models = json.loads(db.execute("SELECT models FROM col").fetchone()[0])
            for model in models.values():
                for template in model["tmpls"]:
                    if template["qfmt"].count("{{type:") != 1:
                        raise RuntimeError(f"{path.name}: template {model['name']} needs exactly one typed answer")
            text = (json.dumps(models) + "\n".join(row[0] for row in db.execute("SELECT flds FROM notes"))).casefold()
            marker = next((item for item in AUDIO_MARKERS if item in text), None)
            if marker:
                raise RuntimeError(f"{path.name} contains forbidden audio/TTS/media marker: {marker}")
            empty_first = db.execute("SELECT count(*) FROM notes WHERE sfld = ''").fetchone()[0]
            if empty_first:
                raise RuntimeError(f"{path.name}: {empty_first} note(s) with an empty first field")
        finally:
            db.close()
    if notes != cards:
        raise RuntimeError(f"{path.name}: expected one card per note, found {notes} notes and {cards} cards")
    if expected_cards is not None and cards != expected_cards:
        raise RuntimeError(f"{path.name}: expected {expected_cards} cards, found {cards}")
    return {"notes": notes, "cards": cards}


def content_digest(path: Path) -> str:
    """Hash of what Anki imports (notes, tags, suspension, note types, deck names), ignoring timestamps."""
    with tempfile.TemporaryDirectory() as temp_name, zipfile.ZipFile(path) as archive:
        collection = Path(temp_name) / "collection.anki2"
        collection.write_bytes(archive.read("collection.anki2"))
        db = sqlite3.connect(collection)
        try:
            models_json, decks_json = db.execute("SELECT models, decks FROM col").fetchone()
            notes = db.execute("SELECT n.guid, n.flds, n.tags, c.queue FROM notes n JOIN cards c ON c.nid = n.id "
                               "ORDER BY n.guid").fetchall()
        finally:
            db.close()
    models = sorted((m["name"], m["css"], [f["name"] for f in m["flds"]], [(t["qfmt"], t["afmt"]) for t in m["tmpls"]])
                    for m in json.loads(models_json).values())
    decks = sorted((d["name"], d["desc"]) for d in json.loads(decks_json).values())
    return hashlib.sha256(json.dumps([models, decks, notes], ensure_ascii=False).encode("utf-8")).hexdigest()


def package_ids(path: Path) -> set[tuple[str, int]]:
    """Note and card IDs in a package, for cross-package uniqueness checks."""
    with tempfile.TemporaryDirectory() as temp_name, zipfile.ZipFile(path) as archive:
        collection = Path(temp_name) / "collection.anki2"
        collection.write_bytes(archive.read("collection.anki2"))
        db = sqlite3.connect(collection)
        try:
            return {("note", row[0]) for row in db.execute("SELECT id FROM notes")} | \
                   {("card", row[0]) for row in db.execute("SELECT id FROM cards")}
        finally:
            db.close()
