#!/usr/bin/env python3
"""Shared validation helpers for the workspace's Anki packages."""

from __future__ import annotations

import json
import sqlite3
import tempfile
import zipfile
from pathlib import Path


AUDIO_MARKERS = ("[sound:", "{{tts ", "{{tts-voices:", "<audio", "autoplay")


def validate_package(path: Path, *, expected_cards: int | None = None) -> dict[str, int]:
    """Validate structure, SQLite integrity, card links, count, and the audio ban."""
    if not path.exists():
        raise RuntimeError(f"Missing Anki package: {path}")

    with tempfile.TemporaryDirectory() as temp_name, zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        if "collection.anki2" not in names:
            raise RuntimeError(f"{path.name} has no collection.anki2")
        collection = Path(temp_name) / "collection.anki2"
        collection.write_bytes(archive.read("collection.anki2"))

        media = json.loads(archive.read("media") if "media" in names else b"{}")
        if media:
            raise RuntimeError(f"{path.name} contains media despite the workspace audio/media ban")

        db = sqlite3.connect(collection)
        try:
            integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise RuntimeError(f"{path.name} SQLite integrity check failed: {integrity}")
            note_count = db.execute("SELECT count(*) FROM notes").fetchone()[0]
            card_count = db.execute("SELECT count(*) FROM cards").fetchone()[0]
            orphan_cards = db.execute(
                "SELECT count(*) FROM cards LEFT JOIN notes ON notes.id = cards.nid WHERE notes.id IS NULL"
            ).fetchone()[0]
            if orphan_cards:
                raise RuntimeError(f"{path.name} contains {orphan_cards} orphan card(s)")

            models_raw = db.execute("SELECT models FROM col").fetchone()[0]
            template_text = models_raw.casefold()
            note_text = "\n".join(row[0] for row in db.execute("SELECT flds FROM notes")).casefold()
            marker = next((item for item in AUDIO_MARKERS if item in template_text or item in note_text), None)
            if marker:
                raise RuntimeError(f"{path.name} contains forbidden audio/TTS marker: {marker}")
        finally:
            db.close()

    if expected_cards is not None and card_count != expected_cards:
        raise RuntimeError(f"{path.name}: expected {expected_cards} cards, found {card_count}")
    if note_count != card_count:
        raise RuntimeError(f"{path.name}: expected one card per note, found {note_count} notes and {card_count} cards")
    return {"notes": note_count, "cards": card_count}

