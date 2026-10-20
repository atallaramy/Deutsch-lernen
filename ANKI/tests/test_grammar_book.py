"""Grammar book check (docs/tools/check_grammar_book.py) on the real book plus synthetic faulty pages."""

import copy
import shutil
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ANKI"))
sys.path.insert(0, str(ROOT / "docs" / "tools"))

import build_grammar_pdf  # noqa: E402
import check_grammar_book  # noqa: E402
from deck_data import load  # noqa: E402

GOOD_PAGE = """\
# Test page

## Table

| Person | kommen |
|---|---|
| ich | komme |
| sie/Sie | kommen |

## Examples from my lessons

| German | Source |
|---|---|
| Ich **wohne** in Sevilla. | [DW A1 E1 L3 · script](https://example.org) |

## Common mistakes

| Wrong | Right | Why | From |
|---|---|---|---|
| Wo kommen Sie? | Woher kommen Sie? | woher | [notes](<../../notes/my notes.md>) |
| du heißst | du heißt | stem | rule |

## Sentences cards

- `from-spain`
"""


class GrammarBook(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load()

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.book = self.tmp / "Grammatik"
        (self.book / "A1").mkdir(parents=True)
        (self.book / "Materials").mkdir()
        shutil.copy(check_grammar_book.SNAPSHOT, self.book / "Materials" / "wiktionary-snapshot.json")
        (self.tmp / "notes").mkdir()
        (self.tmp / "notes" / "my notes.md").write_text("- Wo kommen Sie? \n", encoding="utf-8")
        (self.book / "README.md").write_text("[Test](A1/Test.md)\n", encoding="utf-8")

    def errors(self, page, data=None, grammar_pages=False):
        (self.book / "A1" / "Test.md").write_text(textwrap.dedent(page), encoding="utf-8")
        return check_grammar_book.check(self.book, data or self.data, grammar_pages=grammar_pages,
                                        cheatsheet=self.tmp / "Grammatikbegriffe.md").errors

    def write_glossary(self, rows, cheatsheet_rows=None):
        (self.book / "Grammatikbegriffe.md").write_text("| Term | English | Page |\n|---|---|---|\n" + rows,
                                                        encoding="utf-8")
        (self.book / "README.md").write_text("[Test](A1/Test.md) [Words](Grammatikbegriffe.md)\n", encoding="utf-8")
        (self.tmp / "Grammatikbegriffe.md").write_text(
            "| German | English | Example |\n|---|---|---|\n" + (cheatsheet_rows or rows), encoding="utf-8")

    def assertOneError(self, page, fragment, data=None):
        errors = self.errors(page, data)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn(fragment, errors[0])

    def test_real_book_passes(self):
        report = check_grammar_book.check(data=self.data)
        self.assertEqual(report.errors, [])
        self.assertGreater(report.counts["quotes"], 0)
        self.assertGreater(report.counts["learner quotes"], 0)
        self.assertGreater(report.counts["verb forms"], 0)

    def test_good_page_passes(self):
        self.assertEqual(self.errors(GOOD_PAGE), [])

    def test_quote_must_be_verbatim(self):
        page = GOOD_PAGE.replace("Ich **wohne** in Sevilla.", "Ich wohne in Madrid.")
        self.assertOneError(page, "not verbatim")

    def test_quote_must_come_from_the_named_source(self):
        page = GOOD_PAGE.replace("DW A1 E1 L3 · script", "DW A1 E0 L1 · script")
        self.assertOneError(page, "not verbatim")

    def test_unstudied_lesson_cannot_be_quoted(self):
        page = GOOD_PAGE.replace("DW A1 E1 L3 · script", "DW B1 E1 L1 · script")
        self.assertOneError(page, "not a captured lesson")

    def test_learner_quote_must_be_in_the_linked_notes(self):
        page = GOOD_PAGE.replace("| Wo kommen Sie? |", "| Wo wohnen Sie? |")
        self.assertOneError(page, "not in the linked notes")

    def test_rule_rows_are_not_looked_up(self):
        self.assertEqual(self.errors(GOOD_PAGE.replace("du heißst", "du heißest")), [])

    def test_verb_form_must_match_wiktionary(self):
        page = GOOD_PAGE.replace("| ich | komme |", "| ich | kommer |")
        self.assertOneError(page, "kommen, ich: 'kommer'")

    def test_verb_needs_a_snapshot(self):
        page = GOOD_PAGE.replace("| Person | kommen |", "| Person | fliegen |")
        self.assertOneError(page, "no Wiktionary snapshot for 'fliegen'")

    def test_unknown_card_key(self):
        self.assertOneError(GOOD_PAGE.replace("`from-spain`", "`from-italy`"), "unknown Sentences card")

    def test_retired_card_key(self):
        data = copy.copy(self.data)
        data.sentence_cards = [dict(card, retired="test") if card["key"] == "from-spain" else card
                               for card in self.data.sentence_cards]
        self.assertOneError(GOOD_PAGE, "is retired", data)

    def test_broken_link(self):
        self.assertOneError(GOOD_PAGE + "\n[gone](missing.md)\n", "broken link missing.md")

    def test_page_must_be_in_the_index(self):
        (self.book / "README.md").write_text("# empty\n", encoding="utf-8")
        self.assertOneError(GOOD_PAGE, "not listed in Grammatik/README.md")

    def with_terms(self, *entries):
        return GOOD_PAGE.replace("## Table", "German terms:\n" + "\n".join(f"- {e}" for e in entries) + "\n\n## Table")

    def test_described_grammar_words_pass(self):
        self.write_glossary("| *das Subjekt* | subject: who or what does the action (*Wer? Was?*) | [Test](A1/Test.md) |\n"
                            "| *das Nomen* / *das Substantiv* | noun: a word for a person or thing | [Test](A1/Test.md) |\n")
        page = self.with_terms("*das Subjekt* (subject: who or what does the action (*Wer? Was?*))",
                               "*das Nomen* / *das Substantiv* (noun: a word for a person or thing)")
        self.assertEqual(self.errors(page), [])

    def test_grammar_word_must_be_in_the_glossary(self):
        self.write_glossary("| *das Subjekt* | subject: who or what does the action | [Test](A1/Test.md) |\n")
        page = self.with_terms("*das Verb* (verb: a word for an activity)",
                               "*das Subjekt* (subject: who or what does the action)")
        self.assertOneError(page, "'das Verb' is missing from Grammatikbegriffe.md")

    def test_grammar_word_needs_the_glossary_description(self):
        self.write_glossary("| *das Subjekt* | subject: who or what does the action | [Test](A1/Test.md) |\n")
        self.assertOneError(self.with_terms("*das Subjekt* (subject)"),
                            "'das Subjekt' needs its Grammatikbegriffe.md description: "
                            "(subject: who or what does the action)")
        self.assertOneError(self.with_terms("*das Subjekt*"), "'das Subjekt' needs its Grammatikbegriffe.md description")

    def test_synonyms_are_given_together(self):
        self.write_glossary("| *das Nomen* / *das Substantiv* | noun: a word for a person or thing | [Test](A1/Test.md) |\n")
        page = self.with_terms("*das Nomen* (noun: a word for a person or thing)")
        self.assertOneError(page, "give 'das Nomen / das Substantiv' together")

    def test_grammar_word_is_described_on_its_page(self):
        self.write_glossary("| *das Subjekt* | subject: who or what does the action | [Test](A1/Test.md) |\n")
        self.assertOneError(GOOD_PAGE, "'das Subjekt' is not in the German terms of A1/Test.md")

    def test_lesson_description_is_used(self):
        own = "| *das Verb* | verb: a word for an action | [DW](https://example.org) |\n"
        lesson = ("| *das Verb* | verb: Verbs are words that describe activities, occurrences or a situation, "
                  "e.g. walk, eat, play. | [DW](https://example.org) |\n")
        self.write_glossary(own)
        errors = self.errors(GOOD_PAGE, grammar_pages=True)
        self.assertTrue(any("'das Verb' must use the lesson's description (dw-a1-e1-l3)" in e for e in errors), errors)
        self.assertTrue(any("'die Präposition' (dw-a1-e2-l3" in e and e.endswith("is missing") for e in errors), errors)
        self.write_glossary(lesson)
        self.assertFalse(any("'das Verb'" in e for e in self.errors(GOOD_PAGE, grammar_pages=True)))

    def test_cheatsheet_lists_the_same_words(self):
        self.write_glossary("| *das Nomen* / *das Substantiv* | noun | [DW](https://example.org) |\n",
                            cheatsheet_rows="| das Nomen / das Hauptwort | noun | der Stift |\n")
        errors = self.errors(GOOD_PAGE)
        self.assertEqual(len(errors), 2, errors)
        self.assertIn("missing grammar word 'das Substantiv'", errors[0])
        self.assertIn("'das Hauptwort' is not in Grammatik/Grammatikbegriffe.md", errors[1])

    def test_glossary_links_do_not_cover_dw_grammar_pages(self):
        self.write_glossary("| *das Verb* | verb | "
                            "[DW](https://learngerman.dw.com/en/conjugation-haben/l-37265543/gr-38310825) |\n")
        errors = self.errors(GOOD_PAGE, grammar_pages=True)
        self.assertTrue(any("gr-38310825" in error for error in errors), errors)

    def test_every_studied_dw_grammar_page_is_linked(self):
        linked = GOOD_PAGE + "\n[haben](https://learngerman.dw.com/en/conjugation-haben/l-37265543/gr-38310825)\n"
        errors = self.errors(linked, grammar_pages=True)
        self.assertFalse(any("gr-38310825" in error and "not linked" in error for error in errors), errors)
        self.assertTrue(any("'Numbers from 11 to 19'" in error and "gr-38307006" in error for error in errors), errors)

    def test_grammar_page_card_is_listed_on_the_topic_page(self):
        data = copy.copy(self.data)
        data.sentence_cards = [dict(card, grammarPage="gr-38310825") if card["key"] == "from-spain" else card
                               for card in self.data.sentence_cards]
        linked = GOOD_PAGE + "\n[haben](https://learngerman.dw.com/en/conjugation-haben/l-37265543/gr-38310825)\n"
        self.assertFalse(any("'from-spain'" in error for error in self.errors(linked, data, grammar_pages=True)))
        errors = self.errors(GOOD_PAGE, data, grammar_pages=True)
        self.assertTrue(any("'from-spain' practises DW grammar page gr-38310825" in error for error in errors), errors)


class GrammarPdf(unittest.TestCase):
    def test_pdf_matches_the_pages(self):
        self.assertIsNone(build_grammar_pdf.stale_reason(),
                          "rebuild with: python3 docs/tools/build_grammar_pdf.py")

    def test_every_studied_page_is_in_the_pdf_once(self):
        pages = build_grammar_pdf.book_pages()
        self.assertTrue(pages)
        self.assertEqual(len({page.slug for page in pages}), len(pages))
        self.assertTrue(all(page.path.exists() for page in pages))

    def test_the_grammar_words_close_the_book(self):
        self.assertEqual(build_grammar_pdf.book_pages()[-1].path.name, check_grammar_book.GLOSSARY)

    def test_my_mistakes_come_just_before_the_grammar_words(self):
        self.assertEqual(build_grammar_pdf.book_pages()[-2].path.name, check_grammar_book.MISTAKES)

    def test_cheatsheet_is_one_page(self):
        self.assertEqual(build_grammar_pdf.page_count(b"<</Type /Pages /Count 2>> <</Type /Page>> <</Type/Page>>"), 2)
        self.assertEqual(build_grammar_pdf.page_count(build_grammar_pdf.CHEATSHEET_PDF.read_bytes()), 1)
        for sheet in build_grammar_pdf.sheets():
            self.assertEqual(build_grammar_pdf.page_count(sheet.with_suffix(".pdf").read_bytes()), 1, sheet.name)

    def test_links_in_the_pdf(self):
        book = check_grammar_book.BOOK
        page = build_grammar_pdf.Page("A1", "Test", book / "A1" / "Test.md", "")
        slugs = {(book / "A1" / "heissen.md").resolve(): "A1-heissen"}
        fragment = ('<a href="heissen.md">heißen</a> <a href="https://learngerman.dw.com/x">DW</a> '
                    '<a href="../../notes/my%20notes.md">my notes</a> <a href="#table">table</a>')
        result = build_grammar_pdf.rewrite_links(fragment, page, slugs)
        self.assertIn('<a href="#A1-heissen">heißen</a>', result)
        self.assertIn('<a href="https://learngerman.dw.com/x">DW</a>', result)
        self.assertIn('<span class="local">my notes</span>', result)
        self.assertIn('<a href="#A1-Test-table">table</a>', result)


if __name__ == "__main__":
    unittest.main()
