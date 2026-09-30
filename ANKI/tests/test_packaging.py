"""Deterministic packaging into a temporary folder (never the workspace). Run: python3 -m unittest discover -s ANKI/tests"""

import hashlib
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import build_all  # noqa: E402
from anki_package_utils import package_ids, validate_package, write_package  # noqa: E402
from deck_data import load  # noqa: E402


class Packaging(unittest.TestCase):
    def test_all_decks_build_deterministically_and_validate(self):
        data = load()
        cards, errors, _ = build_all.collect(data)
        self.assertEqual(errors, [])
        before = build_all.file_hashes(build_all.PRONUNCIATION_FILES)
        seen_ids = set()
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            for index, spec in enumerate(build_all.deck_specs(data, cards)):
                a, b = Path(first) / f"{index}.apkg", Path(second) / f"{index}.apkg"
                write_package(spec, data.revision, a)
                write_package(spec, data.revision, b)
                self.assertEqual(hashlib.sha256(a.read_bytes()).digest(), hashlib.sha256(b.read_bytes()).digest(), spec.name)
                self.assertEqual(validate_package(a, expected_cards=len(spec.notes))["cards"], len(spec.notes))
                with zipfile.ZipFile(a) as archive:
                    self.assertEqual(sorted(archive.namelist()), ["collection.anki2", "media"])
                ids = package_ids(a)
                self.assertFalse(seen_ids & ids, spec.name)
                seen_ids |= ids
        self.assertEqual(build_all.file_hashes(build_all.PRONUNCIATION_FILES), before)

    def test_retired_cards_are_packaged_suspended(self):
        import sqlite3
        from anki_package_utils import DeckSpec, Note
        data = load()
        cards, _, _ = build_all.collect(data)
        card = next(card for card in cards if card.deck == "vocabulary")
        note_type = build_all.DECKS["vocabulary"][0].NOTE_TYPE
        spec = DeckSpec("Test", "", Path("x.apkg"), "test", [Note(card.key, note_type, card.fields, ["retired::test"], 1, True)])
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "t.apkg"
            write_package(spec, data.revision, path)
            with zipfile.ZipFile(path) as archive:
                (Path(temp) / "c").write_bytes(archive.read("collection.anki2"))
            queue = sqlite3.connect(Path(temp) / "c").execute("SELECT queue FROM cards").fetchone()[0]
        self.assertEqual(queue, -1)

    def test_content_digest_ignores_revision_but_not_fields(self):
        from anki_package_utils import DeckSpec, Note, content_digest
        data = load()
        cards, _, _ = build_all.collect(data)
        card = next(card for card in cards if card.deck == "vocabulary")
        note_type = build_all.DECKS["vocabulary"][0].NOTE_TYPE
        spec = DeckSpec("Test", "", Path("x.apkg"), "test", [Note(card.key, note_type, dict(card.fields), [], 1)])
        with tempfile.TemporaryDirectory() as temp:
            a, b, c = (Path(temp) / name for name in ("a.apkg", "b.apkg", "c.apkg"))
            write_package(spec, "2026-01-01T00:00:00Z", a)
            write_package(spec, "2026-02-01T00:00:00Z", b)
            spec.notes[0].fields["Cue"] += " (changed)"
            write_package(spec, "2026-02-01T00:00:00Z", c)
            self.assertNotEqual(a.read_bytes(), b.read_bytes())
            self.assertEqual(content_digest(a), content_digest(b))
            self.assertNotEqual(content_digest(b), content_digest(c))

    def test_entries_outside_lesson_deck_stay_in_cumulative_deck(self):
        data = load()
        cards, _, _ = build_all.collect(data)
        refs = {f"{lesson.id}:{entry['id']}": (lesson, entry) for lesson in data.lessons for entry in lesson.record.get("entries", [])}
        card = next(card for card in cards if card.deck == "vocabulary" and len(card.covers) == 1)
        lesson, entry = refs[card.covers[0]]
        entry["inLessonDeck"] = False
        specs = {spec.guid_namespace: {note.key for note in spec.notes} for spec in build_all.deck_specs(data, cards)}
        self.assertIn(card.key, specs["cumulative:vocabulary"])
        self.assertNotIn(card.key, specs.get(f"lesson:{lesson.id}", set()))


if __name__ == "__main__":
    unittest.main()
