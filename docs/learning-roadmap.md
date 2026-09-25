# Learning roadmap: A1 → A2 → B1

This is how the system grows with you. Nothing here is built ahead of time.
A lesson becomes cards only after you say you have studied it
([processing-a-lesson.md](processing-a-lesson.md)). The lesson-by-lesson detail
for every level is in [`course-index/`](course-index/).

## The shape of the system (all levels)

- **One capture record, grouped by course → lesson.** What you studied stays
  attributable to DW, VHS or Easy German and to the exact lesson.
- **Three decks by skill, not by course:**
  - Vocabulary: the word or fixed phrase
  - Articles: der/die/das
  - Sentences: using the language — replies, forms, patterns, du/Sie
- **One card per lemma + sense.** A word you meet again in another course
  or level joins its existing card (new source tag), so you never review it twice.
  A new meaning of a known word gets its own card.
- **Lesson decks** are a short typed introduction to each lesson. The
  cumulative decks are the long-term review.

## Levels and deck names

| Level | Cumulative decks | Files |
|---|---|---|
| A1 (now) | `German A1 — Vocabulary`, `German A1 — Articles`, `German A1 — Sentences` | `ANKI/vocabulary.apkg`, `ANKI/articles.apkg`, `ANKI/sentences.apkg` |
| A2 (default plan) | `German A2 — …` | `ANKI/vocabulary-A2.apkg`, … |
| B1 (default plan) | `German B1 — …` | `ANKI/vocabulary-B1.apkg`, … |

A card belongs to the level of the lesson where its lemma + sense first appeared.
Repeats from later levels merge into the existing card and add a source tag.
**Decide when you start A2:** keep separate level decks (the default, already
supported by `build_all.py`), or move to three level-independent decks
(`German — Vocabulary`, …) with level tags. Separate decks let you pause one
level; one set of decks keeps daily study to three decks.

## A1 — where you are (DW Nicos Weg A1 + VHS A1 + Easy German)

Studied so far: DW E0 L1–L4 and E1 L1–L4, VHS Lektion 2, and Easy German SEG 274
(not yet captured; decision D7).

Grammar ahead in DW A1 (from DW's own lesson data):
- **E2–E4:** numbers, W-questions, noun gender, vowel change e→i, simple past of *sein*, *man*
- **E5–E6:** definite and indefinite articles, sentence structure, adjectives after *sein*, *nicht*, possessive determiners
- **E7–E9:** clock times, separable verbs, *können*, simple past of *haben*, modal verbs, the dative
- **E10–E12:** prepositions (place, *mit*, two-case), *nicht/kein*, comparison, instructions
- **E13–E15:** perfect tense with *haben/sein*, adjective declension, dative objects, accusative pronouns, *sollen*
- **E16–E18:** informal imperative, *müssen/dürfen*, dative pronouns, wishes with the subjunctive

VHS A1 runs in parallel over 12 lessons, from *Hallo! Wie geht's?* to
*Jahreszeiten und Wetter* ([vhs-a1.md](course-index/vhs-a1.md)). Both tracks
cover the same A1 core in a different order, so expect many merged cards.

How the decks respond at A1:
- Vocabulary and Articles grow with every lesson; contexts come from DW
  scripts/exercises and the VHS word lists and film scripts.
- Sentences focuses on du/Sie, present-tense forms (including irregular
  *sein/haben/sprechen*), W-questions, and fixed replies. It moves to
  separable verbs, modal verbs and the perfect tense as those lessons arrive.

Check: the official Goethe A1 word list
(<https://www.goethe.de/pro/relaunch/prf/de/A1_SD1_Wortliste_02.pdf>) is a
useful yardstick for what an A1 exam expects. Use it for gap-spotting, not as
a card source; cards come only from what you studied.

## A2 (DW Nicos Weg A2 + VHS A2)

DW A2 grammar ([dw-nicos-weg-a2.md](course-index/dw-nicos-weg-a2.md)):
- subordinate clauses (*dass*, *wenn*, indirect questions with *ob*)
- verbs and adjectives with prepositions
- reflexive verbs
- relative clauses (nominative, accusative, with prepositions)
- simple past of modal and regular verbs
- genitive, passive, *um … zu*

VHS A2 has 12 lessons, from *Was machen wir am Wochenende* to *Sport, Spaß und
Spiel* ([vhs-a2.md](course-index/vhs-a2.md)).

Planned changes when A2 starts:
- **Sentences** takes on word order: verb-final subordinate clauses, relative
  clauses, and verbs with a fixed preposition (*warten auf* + Akk.). Completion cards for
  case endings are added only when a lesson makes them useful.
- **Vocabulary** records the preposition and case of verbs and adjectives on
  the back (*sich interessieren für* + Akk.). The typed answer stays the core
  word unless the preposition is the learning target.
- **Articles** continues unchanged. Adjective-ending practice belongs to
  Sentences, never Articles.

## B1 (DW Nicos Weg B1 — German interface; VHS B1)

DW B1 is only available in German, with German-language scripts and
glossaries ([dw-nicos-weg-b1.md](course-index/dw-nicos-weg-b1.md)). Grammar:
nominalisation, indirect speech, simple past vs perfect, subjunctive II, paired
conjunctions (*entweder … oder*, *zwar … aber*), *obwohl*, *während*, future I,
past perfect, passive, n-declension, *lassen* + infinitive.

VHS B1 has 12 lessons, from *Rund um den Urlaub* to *Die Sprachprüfung*
([vhs-b1.md](course-index/vhs-b1.md)).

Planned changes when B1 starts:
- **Cues move from English to German** where a German paraphrase is precise
  (for example a German definition or a synonym), because at B1 you can
  retrieve from German. English stays wherever German would be ambiguous.
- **Sentences** adds register work (formal letter phrases, *Konjunktiv II*
  politeness) and connectors, matching the exam's writing tasks.
- Goethe B1 word list:
  <https://www.goethe.de/pro/relaunch/prf/de/Goethe-Zertifikat_B1_Wortliste.pdf>

## Outside Anki (all levels)

Anki is for keeping what you have met. The learning itself happens in the
lessons, the videos, reading and speaking. Your lesson template
(`_Vorlage - Nicos Weg A1.md`) already includes shadowing and active recall.
Keep using it; the decks are built from those notes.

Recommended Anki settings: FSRS on, desired retention 0.90, about 10–15
new cards a day across the three decks (see [anki-import.md](anki-import.md)).
