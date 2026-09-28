"""Offline tests of the DW page parsing in ANKI/harvest_sources.py and of the saved Materials/lesson-pages.md copies."""

import json
import shutil
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ANKI"))

import harvest_sources  # noqa: E402

STATE = {
    "Lesson:1": {"vocabularies": [{"__ref": "Knowledge:3"}, {"__ref": "Knowledge:2"}]},
    "Knowledge:2": {"id": 2, "name": "das Handy, die Handys ", "text": "<p>cell phone;&#160;mobile phone</p>\n",
                    "subTitle": None},
    "Knowledge:3": {"id": 3, "name": "(etwas) hören", "text": "<p>to listen to; to hear</p>\n",
                    "subTitle": "hört, hörte, hat gehört"},
    "Knowledge:4": {"id": 4, "name": "Lost and found", "knowledgeType": "REGIONAL_STUDIES"},
}
RECORD = {
    "vocabulary": {"url": "https://example.org/l-1/lv",
                   "items": [{"id": 5, "german": "ja | nein", "english": "yes | no", "forms": ""}]},
    "pages": [{"id": "rs-7", "url": "https://example.org/rs-7", "title": "Culture", "texts": [], "html": "<p>Kultur</p>"},
              {"id": "gr-6", "url": "https://example.org/gr-6", "title": " Grammar ", "texts": [],
               "html": "<table><tr><td><p>ich</p><p>du</p></td><td>habe<br />hast</td></tr></table>"}],
}


class VocabularyPage(unittest.TestCase):
    def test_items_keep_page_order_and_official_english(self):
        items = harvest_sources.dw_vocabulary(STATE)
        self.assertEqual([item["id"] for item in items], [3, 2])
        self.assertEqual(items[1]["german"], "das Handy, die Handys")
        self.assertEqual(items[1]["english"], "cell phone; mobile phone")
        self.assertEqual((items[0]["forms"], items[1]["forms"]), ("hört, hörte, hat gehört", ""))

    def test_photo_credits_are_not_lesson_text(self):
        html = '<p>Hallo!</p><figure class="x"><img alt="a"><figcaption><small>null DW</small></figcaption></figure>'
        self.assertEqual(harvest_sources.clean_text(html), "Hallo!")


class ExerciseTexts(unittest.TestCase):
    def test_read_aloud_lines_tips_and_correct_answers_are_kept(self):
        state = {
            "Exercise:1": {"name": "I live in ...", "inputText": None},
            "Inquiry:2": {"inquiryText": "Play audio", "inquiryDescription": "Ich wohne in Hamburg."},
            "Inquiry:3": {"inquiryText": "Wo ist die Polizei?",
                          "inquiryDescription": "<p>Careful! &quot;Ich wohne am Markt.&quot;</p>\n"},
            "Alternative:4": {"isCorrect": True, "alternativeText": "Die Hausnummer ist 144."},
            "Alternative:5": {"isCorrect": False, "alternativeText": "Die Hausnummer ist 44."},
        }
        self.assertEqual(harvest_sources.exercise_texts(state),
                         ["Die Hausnummer ist 144.", "Play audio", "Ich wohne in Hamburg.", "Wo ist die Polizei?",
                          'Careful! "Ich wohne am Markt."'])


@unittest.skipUnless(shutil.which("pandoc"), "pandoc is needed for lesson-pages.md")
class LessonPages(unittest.TestCase):
    def test_vocabulary_table_grammar_before_culture(self):
        text = harvest_sources.lesson_pages_markdown("DW A1 E9 L9 · Test", RECORD, "2026-09-27")
        self.assertIn("| ja \\| nein | yes \\| no |  |", text)
        self.assertLess(text.index("## Grammar: Grammar"), text.index("## Culture: Culture"))
        self.assertIn("ich · du", text)
        self.assertIn("habe hast", text)
        self.assertNotIn("<t", text)

    def test_saved_copies_match_their_snapshots(self):
        data = json.loads(harvest_sources.LESSONS.read_text(encoding="utf-8"))
        checked = 0
        for lesson in next(course for course in data["courses"] if course["id"] == "dw-nicos-weg")["lessons"]:
            rendered = harvest_sources.lesson_pages_for(lesson)
            self.assertIsNotNone(rendered, f"{lesson['id']}: snapshot has no vocabulary page; run harvest_sources.py")
            path, content = rendered
            self.assertTrue(path.exists() and path.read_text(encoding="utf-8") == content,
                            f"{path} lags its snapshot; run python3 ANKI/harvest_sources.py --pages")
            checked += 1
        self.assertGreater(checked, 0)


if __name__ == "__main__":
    unittest.main()
