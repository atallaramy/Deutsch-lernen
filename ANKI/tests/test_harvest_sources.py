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

    def test_grammar_examples_in_image_alt_text_are_kept(self):
        html = ('<p>Time detail: <em>jetzt</em></p><figure class="x"><img data-id="1" alt="Subject first: Ich bin '
                'jetzt in Deutschland.Time first: Jetzt bin ich in Deutschland."><figcaption><small>null DW</small>'
                '</figcaption></figure>')
        self.assertEqual(harvest_sources.clean_text(harvest_sources.figure_alt_paragraphs(html)),
                         "Time detail: jetzt\nImage:\nSubject first: Ich bin jetzt in Deutschland.\n"
                         "Time first: Jetzt bin ich in Deutschland.")


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

    def test_sorting_answer_is_the_alternatives_in_order(self):
        state = {
            "Exercise:1": {"name": "Offering drinks", "inputText": None},
            "Inquiry:2": {"inquiryType": "SORTING", "inquiryText": "Sortiere die Wörter.",
                          "alternatives": [{"__ref": "Alternative:4"}, {"__ref": "Alternative:3"}]},
            "Alternative:3": {"order": 2, "alternativeText": "trinkst du?"},
            "Alternative:4": {"order": 1, "alternativeText": "Was"},
        }
        self.assertEqual(harvest_sources.exercise_texts(state), ["Sortiere die Wörter.", "Was trinkst du?"])


class OtherTools(unittest.TestCase):
    def test_teacher_guide_and_activity_book_links_are_picked(self):
        page = ('<a href="https://static.dw.com/downloads/1/nicos-weg-a1-e5-l1-manuskript-und-wortschatz-englisch.pdf">'
                '<a href="https://static.dw.com/downloads/2/nicos-weg-a1-e5-l1-lehrerhandreichung-und-uebungen.pdf">'
                '<a href="https://learngerman.dw.com/downloads/3/grammar-overview-nicos-weg-a1.pdf">'
                '"url":"https://static.dw.com/downloads/4/nicos-weg-a1-b1-arbeitsbuch.pdf"')
        self.assertEqual(harvest_sources.tool_links(page), {
            "teacherGuide": "https://static.dw.com/downloads/2/nicos-weg-a1-e5-l1-lehrerhandreichung-und-uebungen.pdf",
            "activityBook": "https://static.dw.com/downloads/4/nicos-weg-a1-b1-arbeitsbuch.pdf"})

    def test_every_dw_lesson_has_its_teacher_guide_and_the_activity_book(self):
        data = json.loads(harvest_sources.LESSONS.read_text(encoding="utf-8"))
        for lesson in next(course for course in data["courses"] if course["id"] == "dw-nicos-weg")["lessons"]:
            materials = (ROOT / lesson["snapshot"]).parent
            self.assertTrue(any(materials.glob(f"*{harvest_sources.TEACHER_GUIDE}")),
                            f"{lesson['id']}: no teacher guide; run python3 ANKI/harvest_sources.py --tools")
        self.assertTrue(harvest_sources.ACTIVITY_BOOK.exists(), "run python3 ANKI/harvest_sources.py --tools")


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
