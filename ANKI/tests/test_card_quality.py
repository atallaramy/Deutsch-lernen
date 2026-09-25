"""Quality-gate tests against the real data plus synthetic leak fixtures. Run: python3 -m unittest discover -s ANKI/tests"""

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import build_all  # noqa: E402
import build_articles_deck  # noqa: E402
import card_quality  # noqa: E402
from deck_data import BLANK, Card, DataError, context_parts, load, verify_context  # noqa: E402


class RealData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load()
        cls.cards, cls.errors, cls.warnings = build_all.collect(cls.data)

    def card(self, key):
        return next(card for card in self.cards if card.key == key)

    def test_no_errors(self):
        self.assertEqual(self.errors, [])

    def test_every_captured_entry_has_a_card(self):
        covered = {ref for card in self.cards for ref in card.covers}
        self.assertEqual({entry.ref for entry in self.data.entries} - covered, set())

    def test_identical_lemma_and_sense_merge_across_courses(self):
        tante = self.card("vocab:Tante|aunt")
        self.assertIn("dw-a1-e0-l4:die-tante", tante.covers)
        self.assertIn("vhs-a1-l02:die-tante", tante.covers)

    def test_distinct_senses_stay_separate(self):
        self.assertNotEqual(self.card("vocab:Mann|man").covers, self.card("vocab:Mann|husband").covers)
        self.assertNotEqual(self.card("vocab:bitte|please").covers, self.card("vocab:bitte|here-you-go").covers)

    def test_typed_answers_keep_german_punctuation_and_keyboard_apostrophe(self):
        self.assertEqual(self.card("vocab:Mach’s gut!|so-long").answer, "Mach's gut!")
        self.assertEqual(self.card("vocab:Vielen Dank!|many-thanks").answer, "Vielen Dank!")
        self.assertFalse(any("’" in card.answer for card in self.cards))

    def test_capture_fields_reach_the_cards(self):
        self.assertIn("Wo kommen Sie?", self.card("sentence:where-from-formal").fields["Details"])
        self.assertIn("level::beyond-A1", self.card("vocab:verwitwet|widowed").tags)
        self.assertIn("VHS vocabulary trainer", self.card("vocab:Kind|child").fields["Source"])
        self.assertIn("Meaning checked in", self.card("vocab:Schwiegermutter|mother-in-law").fields["Source"])

    def test_plural_only_nouns_have_no_article_card(self):
        keys = {card.key for card in self.cards if card.deck == "articles"}
        self.assertNotIn("article:Spaghetti|f", keys)
        self.assertNotIn("article:Eltern|f", keys)

    def test_pending_items_are_not_built(self):
        pending = {item["german"] for _, item in self.data.pending}
        built = {card.fields.get("Display") for card in self.cards}
        self.assertFalse(pending & built)

    def test_leaking_context_is_rejected(self):
        bad = copy.deepcopy(self.card("vocab:Tasche|bag"))
        bad.key = "vocab:test-leak"
        bad.fields["Context"] = f"Die Tasche? Welche <span class=gap>{BLANK}</span>?"
        bad.front_german = "Die Tasche? Welche Tasche?"
        errors, _ = card_quality.check(self.data, self.cards + [bad])
        self.assertTrue(any("test-leak" in error and "appears in the context" in error for error in errors))

    def test_duplicate_front_sentence_is_rejected(self):
        dup = copy.deepcopy(self.card("vocab:Tasche|bag"))
        dup.key = "vocab:test-dup"
        dup.answer = "Tasche-dup"
        errors, _ = card_quality.check(self.data, self.cards + [dup])
        self.assertTrue(any("Same German front" in error for error in errors))

    def test_ambiguous_cues_are_rejected(self):
        twin = copy.deepcopy(self.card("vocab:Mutter|mother"))
        twin.key, twin.answer, twin.front_german = "vocab:test-twin", "Mama2", ""
        errors, _ = card_quality.check(self.data, self.cards + [twin])
        self.assertTrue(any("Ambiguous cue" in error for error in errors))


class GlossRules(unittest.TestCase):
    def test_unconfirmed_meaning_is_rejected(self):
        data = load()
        entry = next(entry for entry in data.entries if entry.raw["german"] == "die Tochter")
        snapshot = {"Tochter": {"definitions": [{"text": "daughter"}]}}
        self.assertIsNone(card_quality.gloss_check(entry, snapshot))
        wrong = copy.deepcopy(entry)
        wrong.raw = {**entry.raw, "english": "grandmother"}
        self.assertIsNotNone(card_quality.gloss_check(wrong, snapshot))


class ContextRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load()

    def test_non_verbatim_context_fails_verification(self):
        context = {"lesson": "dw-a1-e1-l2", "source": "script", "text": "Die Tasche ist nicht im Auto."}
        self.assertTrue(verify_context(self.data, context, "test"))

    def test_verbatim_context_passes(self):
        context = {"lesson": "dw-a1-e1-l2", "source": "script", "text": "Die Tasche ist nicht im Taxi."}
        self.assertEqual(verify_context(self.data, context, "test"), [])

    def test_target_must_occur_once(self):
        with self.assertRaises(DataError):
            context_parts({"text": "Die Tasche? Welche Tasche?"}, "Tasche")

    def test_article_blank_must_be_the_gender_article(self):
        context = {"lesson": "dw-a1-e1-l4", "source": "exercises", "text": "Ja, ich habe einen Pass."}
        *_, errors = build_articles_deck.article_context(self.data, context, "Pass", "m", "test")
        self.assertTrue(errors)
        accusative = {"lesson": "dw-a1-e1-l4", "source": "exercises", "text": "Der Pass ist in Nicos Tasche."}
        front, _, article, errors = build_articles_deck.article_context(self.data, accusative, "Pass", "m", "test")
        self.assertEqual((errors, article), ([], "Der"))
        self.assertIn(BLANK, front)


if __name__ == "__main__":
    unittest.main()
