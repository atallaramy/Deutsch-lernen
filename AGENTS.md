# German-learning workspace rules

The current rules for this German-learning system (A1 now, then A2 and B1).
They change only when the learner decides: then update this file and add one
line to `docs/decisions.md`. Do not turn a one-off request into a lasting rule
without the learner's confirmation. The steps for a lesson are in
`docs/processing-a-lesson.md`.

## Top priority

The only goal: make studying German easier and save the learner's time. Keep
everything short and simple. Never hand the learner reports, reviews or checking
work: say what is done and what is needed from them. Apply every rule below in
this spirit.

## Folders

- `ANKI/`: the cumulative decks, their builders, data files, scan indexes and
  coverage ledger. Kept long term; grows with each lesson.
- Lesson folders per course: `DW Deutsch lernen/<level>/…`,
  `VHS-Lernportal/<level>/…`, `EasyGerman/…`. A lesson folder holds the
  learner's Markdown notes (directly in the folder, never inside `Materials/`),
  its lesson deck and a `Materials/` folder.
- `Materials/` holds official materials (the DW script/vocabulary PDF of every
  DW lesson, other verified official PDFs), `source-snapshot.json`,
  `lesson-pages.md` and `mistakes.md`. New verified materials may be added.
  `lesson-pages.md` is the harvester's readable copy of a DW lesson's
  vocabulary, grammar and culture pages; never edit it by hand. A notes file
  found in `Materials/` moves up only after the learner's yes.
- `docs/`: the reference library (links, lesson-by-lesson course index in
  `docs/course-index/`, learning roadmap, research, decision log).
- `Grammatik/`: the learner's grammar book. `Spickzettel/`: the learner's
  cheatsheets.

## Files, safety and git

- Do not move, rename or delete existing folders, Markdown notes, legacy
  packages or PDFs without the learner's explicit approval for that item. Open
  items are in `docs/known-issues.md`.
- Leave the pronunciation resource untouched:
  `DW Deutsch lernen/A1/01_Intro_zu_A1/04_Von A bis Z/build_phonetic_alphabet_deck.py`,
  `phonetic-alphabet.json` and `Von A bis Z_Phonetic Alphabet_Pronunciation.apkg`.
- Do not rerun `ANKI/download_nicos_weg_a1_materials.py`: its manifest uses old
  folder names and would create duplicate folders.
- Git (`main`) is the only backup; make no copies. Commit when a lesson is
  done, without asking, and before changing builders, the data format or rule
  files. Other commits when the learner asks. Never push unless asked. Never
  commit secrets (`.env` is ignored).

## Capture records

- `ANKI/lesson-vocabulary.json` (schema 3) is the faithful record of what the
  learner studied, grouped course → lesson → entry. Every entry keeps its
  provenance (`origin`), the lesson it came from and the source URLs.
- A captured entry is: an item in a vocabulary/Wortschatz list in the
  learner's notes; an item the learner wrote with a meaning; an item of the
  official glossary, vocabulary page or word list of a lesson the learner has
  notes for; or a word or fixed phrase worth learning from that lesson's
  official script, exercises, grammar pages or culture pages (their sentences
  are context candidates). Words above A1 are captured without asking and
  tagged `beyond-A1` (Goethe-Zertifikat A1 word list). Other borderline items
  go to `pendingEntries` until the learner says yes or no; pending items are
  never built.
- Nothing on a studied lesson's vocabulary page or grammar pages is left out.
  Every item on a DW vocabulary page is recorded in that lesson (entry, pending
  or declined), with `vocabularyPageForm` when the page writes it differently.
  Every DW grammar page is covered by a grammar-book topic page that links to
  it. `build_all.py check` and `check_grammar_book.py` fail otherwise. For VHS
  the equivalents are the word list, the vocabulary trainer and the grammar list.
- Every English meaning comes from an official course source (DW glossary or
  culture page, VHS vocabulary trainer) or is verified against the dictionary
  snapshot (`ANKI/gloss-snapshot.json`: en.wiktionary, else dict.cc); the build
  rejects any other.
- Auto-generated captions (e.g. YouTube) may be used to find items, never as
  card text.
- Never remove a captured entry. Official spelling is canonical; the learner's
  own spelling is kept as `learnerForm` and shown as feedback, never as the
  answer. The learner's original errors are saved in the lesson's
  `Materials/mistakes.md` before the notes are corrected.
- Keep each course/lesson record separate even when cumulative cards merge.

## Deck types

### Cumulative decks (all courses)

- One cumulative system for every course (DW, VHS, Easy German), divided by
  retrieval skill into `German A1 — Vocabulary`, `German A1 — Articles` and
  `German A1 — Sentences` (`ANKI/vocabulary.apkg`, `articles.apkg`,
  `sentences.apkg`). Provenance lives in tags (`course::…`, `lesson::…`). Later
  levels follow `docs/learning-roadmap.md`.
- Merge only records with an identical lemma and sense, across lessons and
  courses. Distinct meanings stay separate cards. Articles cards key on
  lemma + gender.
- **Vocabulary** tests retrieval of one lexical item or fixed expression. Front:
  a precise English meaning or situation, plus a verified German context with
  the target blanked when a good one exists. Nouns are typed without their
  article; verbs as the infinitive without placeholders such as `(etwas)`.
  Back: the canonical form (article + plural, principal parts), the filled
  context, one useful note, the source.
- **Articles** tests only `der`, `die` or `das`, by typed recall. A sentence
  context is allowed only when the blank is the gender article directly before
  the noun (a nominative slot for masculine nouns). Nothing else on the front
  may reveal gender (no ein/eine, possessives, kein/keine, adjective endings,
  back-referring pronouns or plural). Otherwise show the noun and its gloss.
  Plural-only nouns, forms of address and names used without an article get no
  Articles card. After answering: the full noun with plural and a gender
  pattern only when it is dependable, or an exception warning.
- **Sentences** tests productive language: fixed situations, replies to a
  German line, register switches (du/Sie), contextual verb and case forms, and
  useful patterns. It owns utterance entries whose value is a pattern or a
  grammatical choice, and how names are used (first name ↔ du/Tschüss,
  Herr/Frau + surname ↔ Sie/Auf Wiedersehen). Unanalysed formulas (greetings,
  thanks, *Kein Problem*) belong to Vocabulary.
- Quality and retrieval purpose outrank card count. Do not make two cards that
  test substantially the same recall. A source sentence may appear on the front
  of only one card. A context must not contain another card's Sentences answer;
  a German reply prompt is the only exception, and such pairs are kept apart in
  the new-card order.
- Typed answers are strict about spelling, capitalisation, umlauts and
  punctuation. The one normalisation is the apostrophe typed on the German Mac
  keyboard (`'`); the back shows the typographic form. With a context, the
  answer is exactly the blanked text.
- No recorded or synthetic audio, text-to-speech, sound fields, images or
  audio-only cards in the cumulative or lesson decks. The phonetic-alphabet deck
  in *Von A bis Z* is outside this rule and stays untouched. Audio returns only
  if the learner changes this rule.
- No ordinary multiple choice, recognition-only cards or unneeded
  forward/reverse duplicates.

### Lesson decks

- One per processed lesson, in its lesson folder, named after the lesson title,
  e.g. file `DW A1 E1L3 Woher kommst du - Vocabulary.apkg` and Anki deck
  `Lessons::DW A1::E1 L3 Woher kommst du?`; VHS: `VHS A1 L02 Meine Familie und
  ich - Vocabulary.apkg` / `Lessons::VHS A1::L02 Meine Familie und ich`; Easy
  German: `Lessons::Easy German::SEG 274 Greetings & Farewells`. All sit under
  one collapsible `Lessons` deck in Anki. Older lesson-deck files keep their
  names and are not deleted.
- A lesson deck covers every captured entry of its lesson with the same card
  content as the cumulative decks (its Vocabulary cards plus the Sentences cards
  for its phrases). It is a typed introduction, not a second long-term queue.
  Entries added to a lesson after its deck was built (`inLessonDeck: false`)
  go into the cumulative decks only.

## Identity and scheduling

- Packages are deterministic: IDs and GUIDs come from stable card keys and the
  data revision, so the same data gives identical files.
- Keep card keys stable when a learning target stays the same. Never delete a
  shipped card key; to retire one, mark it retired in the data so it is tagged
  `retired::…` and suspended, never silently dropped.

## Shipping gate

- No context may ship unless it is verbatim (or an exact contiguous excerpt)
  from a local source snapshot. English cues and scenes are prompts, not
  contexts.
- Packages are built only after `python3 ANKI/build_all.py check` reports no
  errors. Never weaken or skip a check to make a build pass: fix the data, or
  ask.
- No preview and no approval step: the learner does not review cards. The agent
  reads the lesson's new cards (`check --lesson <id>`) before packaging and
  fixes any card the learner reports while studying.
- Report checks and tests as passed only when the actual results support it.

## Processing a lesson

Process a lesson only after the learner says they have studied it, one lesson
at a time. Before capturing or building, read `docs/processing-a-lesson.md` in
full and follow it: mistake rounds, read, snapshot, capture, curate, check,
package, grammar book, tests, commit.

## Card-quality gate

Before adding a card, confirm all of the following:

1. The target is a captured, source-backed entry and appropriate to the
   learner's level (items beyond the level are kept and tagged `beyond-A1`).
2. The prompt makes one answer reasonably clear; add a register, grammatical
   or situational cue when English alone is ambiguous.
3. The card tests active recall rather than recognition or guessing, and
   nothing on the front gives the answer away.
4. The answer is the smallest natural unit that fulfils the learning goal.
5. No existing card already tests the same knowledge in substantially the same
   way.
6. The back gives concise corrective feedback: canonical answer first, then
   only a useful form, plural, contrast, the learner's own error, or source.
7. A context earns its place (usage, collocation, register or situation);
   otherwise use a bare, precise cue. No context is better than a forced one.

Most short lessons contribute a handful of curated Sentences cards beyond the
ones needed for coverage; none is fine. Vocabulary and Articles have no quotas:
every captured entry is covered.

## Grammar book (`Grammatik/`)

- A personal reference that grows with the studied lessons, not a deck.
  Sentences cards stay the home of grammar practice.
- One short Markdown page per topic, grouped by level (`Grammatik/A1/…`) and
  indexed in `Grammatik/README.md`. Only topics from studied lessons get a page;
  later topics are listed there as coming (from `docs/course-index/`).
- Each page: the rule in simple English with the German terms; a table;
  examples copied verbatim from studied lessons' snapshots, with the source
  named; common mistakes, the learner's own quoted exactly from the notes or the
  lesson's `Materials/mistakes.md`; links to the official DW/VHS pages; the
  Sentences card keys that practise the topic; and a "My rule in my own words"
  line. That line is the learner's; agents never write it.
- Rules and tables come from official DW/VHS material first, then dictionaries
  (Wiktionary conjugation tables in `Grammatik/Materials/wiktionary-snapshot.json`).
  A DW grammar page from a later lesson may confirm a rule, but examples come
  only from studied lessons. `python3 docs/tools/check_grammar_book.py` must
  report no errors; it also requires every DW grammar page of a studied lesson
  to be linked from a topic page.
- No audio. The grammar book never changes the decks. If a grammar check finds
  a card error, fix the card through check → package.
- `Grammatik/Grammatik.pdf` is the whole book in one printable, clickable file.
  The Markdown pages stay the source; page order follows the index.
  `python3 docs/tools/build_grammar_pdf.py` rebuilds it (only after the grammar
  check passes, byte-identical for the same pages), and the tests fail while it
  lags the pages.

## Cheatsheets (`Spickzettel/`) and printing

- `Spickzettel/` is the learner's folder. A cheatsheet holds the keys to the
  knowledge in the learner's head: minimal, built to the learner's own taste and
  way of understanding. When it holds too much, it is no longer a cheatsheet.
- Agents do not create, edit or restructure cheatsheets on their own. An agent
  may suggest one, but asks first, and writes only what the learner decides.
- Collect grammar pages or lessons into a printable file only when the learner
  asks. The grammar-book PDF is the standing exception: it is rebuilt after
  every lesson.

## Open decisions and new rules

- Open decisions (D6 VHS portal content, D7 Easy German capture, the pending
  yes/no items, the E1 L2/L3 deck names) are in `docs/known-issues.md`. Raise
  one when it blocks the work at hand; never decide it silently.
- Ask before introducing a new lasting study rule when the learner's intent is
  unclear. When a rule changes, adapt the builders so it applies in future
  sessions.
- For Anki *implementation* choices only (card templates, question/answer
  formats, media, interaction), consult
  [`ANKI/anki-card-design-reference.md`](ANKI/anki-card-design-reference.md).
  It is not a rule for choosing sources, vocabulary or curriculum.
