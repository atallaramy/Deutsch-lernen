#!/usr/bin/env python3
"""Build an offline MP3 pronunciation deck for DW's phonetic alphabet."""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import subprocess
import tempfile
import time
import urllib.parse
import zipfile
from pathlib import Path


LESSON = Path(__file__).resolve().parent
SOURCE = LESSON / "phonetic-alphabet.json"
OUT = LESSON / "Von A bis Z_Phonetic Alphabet_Pronunciation.apkg"
MEDIA_DIR = LESSON / "Materials" / "Phonetic alphabet audio"
STANDALONE = MEDIA_DIR / "Phonetisches Alphabet — pronunciation.mp3"
SEP = "\x1f"
MODEL_NAME = "DW Von A bis Z — Phonetic Alphabet Pronunciation"
DECK_NAME = "DW German — Von A bis Z Phonetic Alphabet (pronunciation)"
QFMT = "<div class=instruction>Say the code word aloud</div><div class=prompt>{{Prompt}}</div><div class=hint>Reveal the answer, then listen and repeat.</div>"
AFMT = "{{FrontSide}}<hr id=answer><div class=label>German pronunciation</div><div class=answer>{{Answer}}</div><div class=spoken>{{Spoken}}</div>{{Audio}}"
CSS = ".card { font-family: -apple-system, Arial, sans-serif; text-align: center; color: #20242b; background: #fff; } .instruction, .label { font-size: 14px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: #546170; margin: 22px 0 10px; } .prompt { font-size: 68px; font-weight: 750; line-height: 1; margin: 24px 0; } .answer { font-size: 34px; font-weight: 700; margin: 14px 0 8px; } .spoken { font-size: 21px; color: #4d5662; margin-bottom: 18px; } .hint { font-size: 16px; color: #68717d; margin: 12px auto; }"


def load_entries() -> tuple[dict, list[dict]]:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    return source, source["entries"]


def audio_name(entry: dict) -> str:
    return f"phonetic-{entry['id']}.mp3"


def valid_mp3(output: Path) -> bool:
    if not output.exists() or output.stat().st_size <= 128:
        return False
    check = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(output)],
        capture_output=True,
        text=True,
    )
    try:
        return check.returncode == 0 and float(check.stdout.strip()) > 0
    except ValueError:
        return False


def create_mp3(text: str, output: Path) -> None:
    if valid_mp3(output):
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    url = "https://translate.googleapis.com/translate_tts?ie=UTF-8&client=tw-ob&tl=de&q=" + urllib.parse.quote(text)
    subprocess.run(["curl", "-sS", "-L", "--connect-timeout", "15", "--max-time", "30", "-o", str(output), url], check=True)
    if not valid_mp3(output):
        raise RuntimeError(f"Audio generation failed: {output}")


def create_audio(entries: list[dict]) -> None:
    for entry in entries:
        create_mp3(entry["spoken"], MEDIA_DIR / audio_name(entry))
    if valid_mp3(STANDALONE):
        return
    with tempfile.NamedTemporaryFile("w", suffix=".txt", encoding="utf-8", delete=False) as temporary:
        playlist = Path(temporary.name)
        for entry in entries:
            path = (MEDIA_DIR / audio_name(entry)).resolve().as_posix().replace("'", "'\\\"'\\\"'")
            temporary.write(f"file '{path}'\n")
    try:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(playlist), "-c", "copy", str(STANDALONE)], check=True)
    finally:
        playlist.unlink(missing_ok=True)
    if not valid_mp3(STANDALONE):
        raise RuntimeError(f"Audio generation failed: {STANDALONE}")


def model_and_decks(now: int) -> tuple[int, int, str, str]:
    model_id, deck_id = now, now + 1
    model = {str(model_id): {"id": str(model_id), "name": MODEL_NAME, "type": 0, "mod": now // 1000, "usn": -1, "sortf": 0, "did": deck_id, "latexPre": "", "latexPost": "", "latexsvg": False,
        "flds": [{"name": name, "ord": index, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": []} for index, name in enumerate(["Prompt", "Answer", "Spoken", "Audio", "Source"])],
        "tmpls": [{"name": "Pronounce", "ord": 0, "did": None, "qfmt": QFMT, "afmt": AFMT, "bqfmt": "", "bafmt": "", "bfont": "", "bsize": 0}],
        "css": CSS, "req": [[0, "all", [0, 1]]], "tags": [], "vers": []}}
    decks = {"1": {"id": 1, "name": "Default", "mod": now // 1000, "usn": 0, "collapsed": False, "browserCollapsed": False, "newToday": [0, 0], "revToday": [0, 0], "lrnToday": [0, 0], "timeToday": [0, 0], "conf": 1, "dyn": 0, "extendNew": 10, "extendRev": 50, "desc": ""},
        str(deck_id): {"id": deck_id, "name": DECK_NAME, "mod": now // 1000, "usn": -1, "collapsed": False, "browserCollapsed": False, "newToday": [0, 0], "revToday": [0, 0], "lrnToday": [0, 0], "timeToday": [0, 0], "conf": 1, "dyn": 0, "extendNew": 20, "extendRev": 50, "desc": "Pronounce and listen to DW's phonetic alphabet and symbol names."}}
    return model_id, deck_id, json.dumps(model), json.dumps(decks)


def initialise(collection: Path) -> None:
    template = LESSON / "Von A bis Z_Vocabulary.apkg"
    with zipfile.ZipFile(template) as archive, archive.open("collection.anki2") as source, collection.open("wb") as target:
        shutil.copyfileobj(source, target)
    now = int(time.time() * 1000)
    _, _, models, decks = model_and_decks(now)
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
    deck_id = next(int(key) for key, value in decks.items() if value["name"] == DECK_NAME)
    model_data = models[str(model_id)]
    model_data["tmpls"][0]["qfmt"] = QFMT
    model_data["tmpls"][0]["afmt"] = AFMT
    model_data["css"] = CSS
    db.execute("UPDATE col SET models = ?", (json.dumps(models),))
    return model_id, deck_id


def package(collection: Path, entries: list[dict]) -> None:
    temporary = OUT.with_suffix(".apkg.tmp")
    media_map = {}
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(collection, "collection.anki2")
        for index, entry in enumerate(entries):
            filename = audio_name(entry)
            archive.write(MEDIA_DIR / filename, str(index))
            media_map[str(index)] = filename
        archive.writestr("media", json.dumps(media_map))
    temporary.replace(OUT)


def merge(collection: Path, source: dict, entries: list[dict]) -> int:
    db = sqlite3.connect(collection)
    model_id, deck_id = ids_and_sync(db)
    existing = {guid: note_id for note_id, guid in db.execute("SELECT id, guid FROM notes")}
    next_note = db.execute("SELECT coalesce(max(id), 0) + 1 FROM notes").fetchone()[0]
    next_card = db.execute("SELECT coalesce(max(id), 0) + 1 FROM cards").fetchone()[0]
    next_due = db.execute("SELECT coalesce(max(due), -1) + 1 FROM cards WHERE did = ? AND queue = 0", (deck_id,)).fetchone()[0]
    now = int(time.time())
    added = 0
    with db:
        for entry in entries:
            guid = hashlib.sha1(f"dw-phonetic:{entry['id']}".encode("utf-8")).hexdigest()[:10]
            fields = SEP.join([entry["prompt"], entry["answer"], entry["spoken"], f"[sound:{audio_name(entry)}]", source["sourceUrl"]])
            csum = int(hashlib.sha1(entry["prompt"].encode("utf-8")).hexdigest()[:8], 16)
            if guid in existing:
                db.execute("UPDATE notes SET mod = ?, flds = ?, sfld = ?, csum = ? WHERE id = ?", (now, fields, entry["prompt"], csum, existing[guid]))
                continue
            db.execute("INSERT INTO notes VALUES (?, ?, ?, ?, -1, 'source::dw interaction::pronunciation', ?, ?, ?, 0, '')", (next_note, guid, model_id, now, fields, entry["prompt"], csum))
            db.execute("INSERT INTO cards VALUES (?, ?, ?, 0, ?, -1, 0, 0, ?, 0, 2500, 0, 0, 0, 0, 0, 0, '')", (next_card, next_note, deck_id, now, next_due))
            next_note, next_card, next_due, added = next_note + 1, next_card + 1, next_due + 1, added + 1
        db.execute("UPDATE col SET mod = ?", (now,))
    db.close()
    return added


def verify(entries: list[dict]) -> tuple[int, int]:
    with tempfile.TemporaryDirectory() as folder:
        collection = Path(folder) / "collection.anki2"
        with zipfile.ZipFile(OUT) as archive:
            archive.extract("collection.anki2", folder)
            media = json.loads(archive.read("media"))
            if len(media) != len(entries):
                raise RuntimeError(f"Expected {len(entries)} deck audio files, found {len(media)}.")
        db = sqlite3.connect(collection)
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
        notes = db.execute("SELECT count(*) FROM notes").fetchone()[0]
        cards = db.execute("SELECT count(*) FROM cards").fetchone()[0]
        db.close()
    if integrity != "ok" or notes != len(entries) or cards != len(entries):
        raise RuntimeError(f"Deck verification failed: integrity={integrity}, notes={notes}, cards={cards}")
    return notes, cards


def main() -> None:
    source, entries = load_entries()
    create_audio(entries)
    with tempfile.TemporaryDirectory() as folder:
        collection = Path(folder) / "collection.anki2"
        if OUT.exists():
            with zipfile.ZipFile(OUT) as archive, archive.open("collection.anki2") as source_file, collection.open("wb") as target:
                shutil.copyfileobj(source_file, target)
        else:
            initialise(collection)
        added = merge(collection, source, entries)
        package(collection, entries)
    notes, cards = verify(entries)
    print(f"Created/updated {OUT.name}: {notes} notes, {cards} cards; added {added} cards.")
    print(f"Standalone iPhone-compatible MP3: {STANDALONE}")


if __name__ == "__main__":
    main()
