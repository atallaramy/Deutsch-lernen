# Data model and tools

## Files in `ANKI/`

| File | Role |
|---|---|
| `lesson-vocabulary.json` | Capture record (schema 3): courses → lessons → `entries` and `pendingEntries`. |
| `vocabulary-cards.json` | Curated cues, verified contexts and interference pairs for Vocabulary cards, keyed `lemma|sense`. |
| `articles-cards.json` | Curated verified contexts and hints for Articles cards, keyed by lemma. |
| `sentence-sources.json` | Curated Sentences cards (schema 3). |
| `gloss-snapshot.json` | Dictionary definitions (en.wiktionary, else dict.cc) for meanings that no official course source supplies (from `harvest_sources.py --glosses`). |
| `legacy-v2-lesson-vocabulary.json` | The capture record from before the v3 redesign; the check requires every v2 word to survive. |
| `review/coverage-ledger.json` | Which card covers each captured entry, plus the pending items. |
| `A1/vocabulary.apkg`, `A1/articles.apkg`, `A1/sentences.apkg` | The cumulative decks (later levels: `A2/`, `B1/`). |
| `A1/Lessons.apkg` | Every lesson deck of the level, copied unchanged; grows with each lesson. |
| `*-scan-index.json` | Written by `package`: lessons, counts, package hashes. |

## Files in a lesson's `Materials/` (written by `harvest_sources.py`)

| File | Role |
|---|---|
| `source-snapshot.json` | Official source text. DW `script`: the PDF's lines. DW `exercises`: `vocabulary` (the vocabulary page `/lv`: `url`, `items` with `id`, `german`, `english`, `forms`), `exercises` (correct texts, sorted answers, read-aloud lines and tips) and `pages` (grammar `gr-` and culture `rs-` pages: `texts`, plus `html` for the readable copy; a grammar page's image text is kept as an *Image:* list, since DW puts examples there). Contexts are verified against the script, exercise and page texts; vocabulary items are not contexts. |
| `Teacher guide and exercises (German).pdf` | DW only: the lesson's teacher guide from its *Other tools* page (activities before, during and after the video, worksheets). Read for the offer after a lesson; not a context source. The A1–B1 activity book is kept once in `DW Deutsch lernen/Materials/`. |
| `lesson-pages.md` | DW only: readable copy of the vocabulary page (German, English, forms) and the grammar and culture pages, rendered with pandoc from the snapshot. Never edited by hand; `harvest_sources.py --pages` rewrites it offline, and the tests fail while it lags the snapshot. |

## Code

| File | Role |
|---|---|
| `build_all.py` | CLI: `check` (`--lesson ID` lists that lesson's cards), `package` (writes only the files whose cards changed, a lesson deck once; `--refresh-lesson ID` rebuilds one; copies every lesson deck of a level, unchanged, into `ANKI/<level>/Lessons.apkg`; ends with `Import: …`). |
| `deck_data.py` | Loads data and snapshots; verification helpers; shared card style. |
| `build_vocabulary_decks.py`, `build_articles_deck.py`, `build_sentences_deck.py` | Card construction for each deck (lesson decks reuse Vocabulary and Sentences cards). |
| `card_quality.py` | Cross-deck gate: coverage, preservation of the v2 records, leakage, ambiguity, the front-sentence registry, sentence priming, known words, and every DW vocabulary-page item recorded in its lesson. |
| `anki_package_utils.py` | Deterministic `.apkg` writer (embedded schema 11), the merge that combines lesson decks, and the validator. |
| `harvest_sources.py` | Network step: snapshots official sources into `Materials/source-snapshot.json` and writes a DW lesson's `Materials/lesson-pages.md` (`--pages`: rewrite those offline; `--glosses`: dictionary check; `--tools`: save the DW teacher guides and the activity book). |
| `tests/` | `python3 -m unittest discover -s ANKI/tests` |
| `download_nicos_weg_a1_materials.py` | Old DW PDF downloader; do not rerun without the fix listed in [known-issues.md](known-issues.md). |

`docs/tools/build_course_index.py` (network) rebuilds `docs/course-index/`.

## Grammar book (`Grammatik/`)

| File | Role |
|---|---|
| `Grammatik/README.md` | Index by level and topic, the *coming* list and the page conventions. |
| `Grammatik/<level>/<Topic>.md` | One page per studied topic. |
| `Grammatik/Grammatikbegriffe.md` | Every grammar word from the studied lessons (term, English, the page that explains it); the last page of the PDF. |
| `Grammatik/Materials/wiktionary-snapshot.json` | `verbs`: de.wiktionary present-tense tables, written by `check_grammar_book.py fetch`. `evidence`: one-off checks (DW grammar pages from later lessons, numbers, declension tables, genders, register labels). |
| `Grammatik/Grammatik.pdf` | The whole book in one printable, clickable PDF (contents, bookmarks, a box for *My rule in my own words*). Built, never edited by hand. |
| `Grammatik/Materials/pdf-build.json` | Written by `build_grammar_pdf.py`: fingerprint of the builder, index, pages and cheatsheet, the SHA-256 of both PDFs, page order and tool versions. The tests compare it with the current pages. |
| `docs/tools/build_grammar_pdf.py` | Builds the book PDF and the one-page cheatsheet `Spickzettel/Grammatikbegriffe.pdf` with pandoc (Markdown → HTML) and headless Chrome (HTML → PDF), offline. Refuses while the grammar check has errors or the cheatsheet needs a second page; builds twice and requires identical bytes (Chrome's build time is replaced by the newest *checked* date). `--check` reports whether the PDF is current. Tested in `ANKI/tests/test_grammar_book.py`. |
| `docs/tools/check_grammar_book.py` | Offline check. Quotes in *Source* tables must be verbatim in the named lesson snapshot; *Wrong … From* rows linking to notes must quote them; *Person* tables must match the verb snapshot; card keys must be live; links must resolve; every page must be in the index; every DW grammar page of a studied lesson must be linked from a topic page; every der/die/das word in a page's *German terms* line must be in `Grammatikbegriffe.md`, which must list the same words as the cheatsheet. Tested in `ANKI/tests/test_grammar_book.py`. |

`Spickzettel/` holds the learner's own cheatsheets. Tools touch only `Grammatikbegriffe.md` (read by the grammar check) and `Grammatikbegriffe.pdf` (written by `build_grammar_pdf.py`).

## Capture entry (schema 3)

```json
{
  "id": "der-sprachkurs",
  "german": "der Sprachkurs", "plural": "die Sprachkurse", "english": "language course",
  "pos": "noun", "lemma": "Sprachkurs", "sense": "language-course",
  "origin": ["dw-glossary", "learner-notes"],
  "learnerForm": "der Sparchkurz, die Sprachkurze",
  "home": "vocabulary"
}
```

Optional fields:
- `forms`, `present`, `note`
- `pluralOnly`, `articles: "exempt:<reason>"`, `articleSource`
- `level` (e.g. `beyond-A1`), `glossSource: "editor"` (the source gives German only)
- `ref` (VHS item number), `answer`, `learnerError {wrong, why}`
- `glossLookup` (dictionary terms to check, e.g. component words of a phrase), `glossEvidence` (extra source note)
- `inLessonDeck: false` (added after the lesson deck was built: cumulative decks only), `genderEvidence` (dictionary page for a noun's gender and plural when no glossary gives them)
- `vocabularyPageForm` (the DW vocabulary page's own wording of this item when it differs from `german`, e.g. `Es ist 09:00 Uhr.`; the vocabulary-page check matches it)

Merge key for Vocabulary: `lemma` (case-sensitive) + `sense`.

## Curated context

```json
{"lesson": "dw-a1-e1-l4", "source": "exercises", "text": "Nico, hast du einen Pass?", "target": "Pass"}
```

- `text` must occur in that lesson's snapshot, compared after normalising quotes, dashes and whitespace.
- `target` must occur exactly once in `text`.
- For Articles, the blank is the article before the noun, and it must be the noun's gender article.

## Sentences card

```json
{"key": "reply-formal", "kind": "response", "lesson": "dw-a1-e0-l1", "skill": "conversation response",
 "scene": "…", "prompt": {"lesson": "dw-a1-e0-l1", "source": "script", "text": "Guten Tag! Wie geht es Ihnen?"},
 "answer": "Sehr gut, danke. Und Ihnen?", "answerSource": {"lesson": "dw-a1-e0-l1", "source": "script"},
 "covers": ["dw-a1-e0-l1:und-ihnen"], "accept": [], "note": "Informal: Und dir?"}
```

- `kind`: `production`, `response`, `completion` (needs `prompt.target`), `table` (one row of an article table, needs `prompt.target`; may share a Vocabulary answer), `register` or `rule` (a DW tip the learner asked to keep; the answer is verbatim in a snapshot).
- `answerSource` is a snapshot reference or `"learner-notes"`. With `"learner-notes"`, the answer must equal a covered entry.
- `retired: "<reason>"` keeps a card in the package, tagged and suspended.

## Revision and identity

- `lesson-vocabulary.json` → `revision` drives every timestamp in the packages.
  Bump it when you change content that is already imported, so Anki treats the
  notes as newer and updates them.
- GUIDs and note/card IDs come from card keys (`vocab:<lemma>|<sense>`,
  `article:<lemma>|<gender>`, `sentence:<key>`) plus the deck namespace. Keep
  keys stable when the learning target stays the same.
