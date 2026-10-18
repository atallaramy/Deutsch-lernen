# Processing a lesson (when you say "I have studied lesson X")

Read this in full before capturing or building any lesson. These are the
steps; the rules they apply are in `AGENTS.md`. Only lessons you have studied,
one at a time, so the deck never grows faster than your learning.

## 0. Trigger and scope

- Start only when you say you have studied a specific lesson, or you ask for
  it. For a lesson you have not studied, answer questions from
  [`course-index/`](course-index/) and [links.md](links.md) and do not build cards.
  For grammar you have studied, start from [`Grammatik/`](../Grammatik/README.md).

## Before step 1: your mistake rounds (default)

The first step of every finished lesson. If you say something else in a session, for example
"correct the spelling and finalize", that wins for the session: Claude saves the
mistakes, corrects the notes itself and continues.

1. Claude checks your notes against the lesson's official script, exercises and
   glossary, then dictionaries. It counts spelling, capitals, umlauts, missing or
   wrong words, word forms, articles, and punctuation that changes the sentence
   (a missing question mark, a stray comma or full stop). A line from audio with no
   official transcript is listed separately when it cannot be checked. Parts of
   the lesson you left out of your notes are not mistakes.
   Accents in non-German names (*Nicolás González*) are not your work: Claude
   corrects them in your notes and says so in `mistakes.md`.
2. **Round 1:** Claude saves the list in the lesson's `Materials/mistakes.md`, then
   shows you its table: the wrong words exactly as you wrote them, with line
   numbers. No comments, except one line naming the mistakes that are already
   in [`Grammatik/Meine-Fehler.md`](../Grammatik/Meine-Fehler.md) (*Again: is → ist, 7×*).
   Claude raises their counts there and adds a mistake that reaches 3× (`AGENTS.md`
   → *Grammar book*).
3. You fix your notes and say so.
4. **Round 2:** Claude checks again and adds what is still wrong to `mistakes.md`
   as *wrong → correct*, and shows you that table.
5. You fix those and say so. Then step 1 starts.

Cards (`learnerForm`) and the grammar book quote your mistakes from
`mistakes.md`, so correcting the notes loses nothing.

## 1. Read

- Your Markdown notes for the lesson, all of it: vocabulary lists, glossed
  items, exercise answers, errors, Anki instructions.
- The official materials. For DW, the script/vocabulary PDF in `Materials/`
  (download it if missing), and after step 2 the vocabulary, grammar and culture
  pages in `Materials/lesson-pages.md`. For VHS, the word list, film script and grammar list
  ([links.md](links.md)). For Easy German, the method in
  [easy-german-transcripts.md](easy-german-transcripts.md) (auto-generated
  captions locate items but are never used as contexts).
- The lesson row in the course index (goal and grammar topic).

## 2. Snapshot the official sources (network, run once per lesson)

1. Add the lesson to `ANKI/lesson-vocabulary.json` (course, id, title, URLs,
   notes file, lesson-deck file, snapshot path, sources) with an empty entry
   list.
2. Run `python3 ANKI/harvest_sources.py --lesson <lesson-id>`.
   - For DW this snapshots the script PDF text, the vocabulary page (German, official English, forms) and every
     exercise, grammar and culture page. It also writes `Materials/lesson-pages.md`, a readable copy of the
     vocabulary, grammar and culture pages (never edited by hand; `--pages` rewrites it offline).
     From the lesson's *Other tools* page it saves the teacher guide (`Materials/Teacher guide and exercises
     (German).pdf`) and, once, the activity book (`DW Deutsch lernen/Materials/`).
   - For VHS it downloads the course PDFs into `VHS-Lernportal/<level>/Materials/` and snapshots them.
3. Check the snapshot contains the lesson's script, exercises and (DW) vocabulary page. Read `lesson-pages.md`.
4. For VHS, also capture the lesson's vocabulary trainer with English (official
   meanings) through the browser ([access.md](access.md)).

## 3. Capture (faithful, never remove)

For each item, add an entry with:
- `german` in the official spelling
- `english`, taken from the official gloss when there is one
- `pos`, `lemma` and `sense`
- `plural`, `forms` and `note` from the glossary
- `origin`
- `learnerForm` when your spelling differs (from `Materials/mistakes.md`)

English meanings: use the official gloss when there is one. Otherwise run
`python3 ANKI/harvest_sources.py --glosses`. The build accepts only meanings
the dictionary confirms. For phrases, set `glossLookup` to their component
words, and use the dictionary's wording.

Which items to capture:
- **What:** see `AGENTS.md` → *Capture records*. `origin` codes: `learner-notes`, `dw-glossary`, `dw-script`, `dw-exercises`, `dw-grammar-page`, `dw-culture-page`, `vhs-wordlist`, `vhs-vocabulary-trainer`, `vhs-film-script`. Their sentences are used as contexts.
- **Vocabulary page:** every item on it is recorded in this lesson, even when an earlier lesson already has it (the cards merge). The PDF glossary and the page usually list the same items; when the page writes one differently (`Es ist 09:00 Uhr.` for `Es ist neun Uhr.`), set `vocabularyPageForm` on the entry. `build_all.py check` reports every page item that is not recorded yet, so run it once right after capturing.
- **Grammar pages:** new words, forms and example phrases from them are captured like script items; their rule goes to the grammar book (§7) and, when useful, to Sentences cards.
- **Above A1** (not on the Goethe A1 word list): captured without asking, `level: beyond-A1`.
- **Borderline** (anything else unclear): put in `pendingEntries` with a reason and ask you yes or no.
- **Home deck:** fixed formulas → `home: vocabulary`; patterns and grammatical choices (du/Sie, verb forms, W-questions) → `home: sentences`. Names → Sentences.
- **Merging:** a new sense of a known word gets its own `sense`. Identical lemma + sense merges automatically.

## 4. Curate

- **Contexts** (`ANKI/vocabulary-cards.json`, `ANKI/articles-cards.json`):
  - only exact excerpts from the lesson snapshots (or another official snapshot), with a `target` that occurs once
  - Articles contexts need the gender article directly before the noun
  - no context is better than a forced one
- **Cues:** precise English; add a disambiguator when two cards could share an answer.
- **Sentences** (`ANKI/sentence-sources.json`), in this order (`AGENTS.md` →
  *Sentences per lesson*):
  1. cover every `home: sentences` entry
  2. teacher guide page 1: note the situations it practises
  3. script: a card for every reusable line
  4. grammar pages: 1–2 cards each, with `grammarPage`
  5. tables: one `table` card per row; the prompt is the row's cells as the
     snapshot joins them (` ¶ `, e.g. `2nd person ¶ du hast`), the form blanked
  6. exercises: 1–2 gap cards for grammar not yet practised
  - German on the front must be verbatim
  - answers must be verbatim in a snapshot or be your own captured sentence

## 5. Check

```sh
python3 ANKI/build_all.py check --lesson <lesson-id>
python3 -m unittest discover -s ANKI/tests
```

Fix every error. Claude reads the lesson's cards in the `--lesson` list (flagged
ones first, merges and senses kept separate) and fixes what is unclear. You do
not review cards.

## 6. Package and import

```sh
python3 ANKI/build_all.py package
```

This refuses while the check has errors. It builds
each package twice to prove the output is identical, validates it, and
confirms the pronunciation deck is untouched. It writes only the files whose
cards changed (a lesson deck only once), adds the new lesson deck to
`ANKI/A1/Lessons.apkg`, and ends with `Import: …`, listing the files to import.
Claude tells you that line; import those files into Anki
([anki-import.md](anki-import.md)).

## 7. Update the grammar book

The rules are in `AGENTS.md` → *Grammar book*; the layout is in
[`Grammatik/README.md`](../Grammatik/README.md).

- Topics: the lesson's grammar (its course-index row and its DW grammar pages or
  VHS grammar list). Add to the existing topic page, or start a new page with the
  layout of an existing one, list it in the index and remove it from *coming*.
- Every DW grammar page of the lesson (in `Materials/lesson-pages.md`) is covered by
  a topic page and linked from it under *Official pages*; the grammar check fails
  while one is missing.
- Examples: add useful new ones, copied verbatim from the new snapshot, with a
  source label such as `DW A1 E2 L1 · script`.
- Mistakes: quote your new errors exactly from `Materials/mistakes.md` (or your
  notes) and link that file.
- Cards: add the lesson's new Sentences card keys.
- Grammar words: add the lesson's new grammar terms to `Grammatik/Grammatikbegriffe.md`
  (term; English with a short description of what it is; the topic page, a DW link
  until it exists), with the same text in the topic page's *German terms* list, and to
  `Spickzettel/Grammatikbegriffe.md` (term, English, a short example). The description
  is the lesson's own, copied verbatim: a DW grammar page's *Grammatical terms in
  German* box (*das Adjektiv: Adjectives are used to describe people or things.*), or
  another lesson sentence that says what the word is. Write your own only when no
  studied lesson gives one, and replace it once a lesson does. The grammar check fails
  while a box word is missing or lacks the box's description, the two lists differ,
  or a page's description differs.
- Leave "My rule in my own words" and the rest of `Spickzettel/` to you.
- A new verb in a verb table needs `python3 docs/tools/check_grammar_book.py fetch`
  (network) first.
- Run `python3 docs/tools/check_grammar_book.py` and fix every error. If a grammar
  check shows a card is wrong, fix the card through steps 5–6.
- Rebuild the PDFs: `python3 docs/tools/build_grammar_pdf.py` (the book and the
  one-page cheatsheet `Spickzettel/Grammatikbegriffe.pdf`). It refuses while the
  grammar check has errors or the cheatsheet needs a second page, and the tests
  fail if a PDF lags its pages. A new topic page joins the PDF by being listed in
  the index's *studied* table.
- Colours: new tables and examples follow [`Spickzettel/Farben.md`](../Spickzettel/Farben.md).
- Cheatsheets: in the final reply, suggest in one line an update to an existing
  cheatsheet, an addition, or a new sheet when the lesson's grammar needs it
  (`AGENTS.md` → *Cheatsheets*). Write only what you say yes to.

## 8. Extra tasks (DW)

Claude adds a short list of extra tasks to the end of your notes file, under the
heading *Extra tasks*, read from the teacher guide (page 1: before, during and
after watching, more activities) and, for the unit, the activity book. Only tasks
you can do alone or with Claude (a short own text, a dialogue, a role-play); skip
class-only games and worksheets that repeat the online exercises. After the tasks,
one line: *Activity book (unit N Title: the activity in a few words): how it works
p. X, worksheet p. Y.* Nothing is built from them. When you do one, write your
answers under the task and tell Claude; Claude marks it there as `AGENTS.md` →
*Processing a lesson* says.

## 9. Commit

Claude commits when the lesson is done, without asking. Commit everything the lesson
changed (notes are yours; commit them only as they are). Use one clear message,
e.g. `Add DW A1 E2 L1 Zahlen von 1 bis 100`, and never push unless you ask.

## 10. Record

- New rules go to `AGENTS.md`, with one line in [decisions.md](decisions.md).
- New useful links go to [links.md](links.md), with the date checked. If a course changes, rerun
  `python3 docs/tools/build_course_index.py`.
