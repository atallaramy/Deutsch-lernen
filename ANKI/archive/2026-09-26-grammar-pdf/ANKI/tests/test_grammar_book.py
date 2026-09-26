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

    def errors(self, page, data=None):
        (self.book / "A1" / "Test.md").write_text(textwrap.dedent(page), encoding="utf-8")
        return check_grammar_book.check(self.book, data or self.data).errors

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


if __name__ == "__main__":
    unittest.main()
