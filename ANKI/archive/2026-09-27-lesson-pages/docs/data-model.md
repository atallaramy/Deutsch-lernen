# Data model and tools

## Files in `ANKI/`

| File | Role |
|---|---|
| `lesson-vocabulary.json` | Capture record (schema 3): courses → lessons → `entries` and `pendingEntries`. |
| `vocabulary-cards.json` | Curated cues, verified contexts and interference pairs for Vocabulary cards, keyed `lemma|sense`. |
| `articles-cards.json` | Curated verified contexts and hints for Articles cards, keyed by lemma. |
| `sentence-sources.json` | Curated Sentences cards (schema 3). |
| `gloss-snapshot.json` | Dictionary definitions (en.wiktionary, else dict.cc) for meanings that no official course source supplies (from `harvest_sources.py --glosses`). |
| `review/preview.html` | Every card's front and back, with flags. Written by `check`. |
| `review/coverage-ledger.json` | Which card covers each captured entry, plus the pending items. |
| `review/approvals.json` | Content hashes of the cards you approved. A card whose content changes needs approval again. |
| `*-scan-index.json` | Written by `package`: lessons, counts, package hashes. |
| `archive/2026-09-25-pre-v3/` | Backup of every file replaced by the v3 redesign, with a SHA-256 manifest. |
| `archive/2026-09-26-grammar-book/` | Backup of the instruction and doc files edited when the grammar book was added, with a SHA-256 manifest. |
| `archive/2026-09-26-grammar-pdf/` | Backup of the instruction, doc and test files edited when the grammar-book PDF was added, with a SHA-256 manifest. |
| `archive/2026-09-26-dw-a1-e2-l1/` | Backup of the data, builder, test, grammar and doc files edited when DW A1 E2 L1 was processed, with a SHA-256 manifest. |
| `archive/2026-09-26-notes-out-of-materials/` | Backup of the data, grammar and doc files edited when three notes files moved out of `Materials/`, with a SHA-256 manifest. |
| `archive/2026-09-27-dw-a1-e2-l2/` | Backup of the data, grammar and doc files edited when DW A1 E2 L2 was processed, with a SHA-256 manifest. |
| `archive/2026-09-27-official-materials-capture/` | Backup of the data, builder, test and doc files edited when the official scripts and exercises became a capture source, with a SHA-256 manifest. |

## Code

| File | Role |
|---|---|
| `build_all.py` | CLI: `check`, `approve`, `package`. |
| `deck_data.py` | Loads data and snapshots; verification helpers; shared card style. |
| `build_vocabulary_decks.py`, `build_articles_deck.py`, `build_sentences_deck.py` | Card construction for each deck (lesson decks reuse Vocabulary and Sentences cards). |
| `card_quality.py` | Cross-deck gate: coverage, preservation of the v2 records, leakage, ambiguity, the front-sentence registry, sentence priming, known words. |
| `review_preview.py` | Renders the preview. |
| `anki_package_utils.py` | Deterministic `.apkg` writer (embedded schema 11) and validator. |
| `harvest_sources.py` | Network step: snapshots official sources into `Materials/source-snapshot.json`. |
| `tests/` | `python3 -m unittest discover -s ANKI/tests` |
| `download_nicos_weg_a1_materials.py` | Old DW PDF downloader; do not rerun without the fix listed in [known-issues.md](known-issues.md). |

`docs/tools/build_course_index.py` (network) rebuilds `docs/course-index/`.

## Grammar book (`Grammatik/`)

| File | Role |
|---|---|
| `Grammatik/README.md` | Index by level and topic, the *coming* list and the page conventions. |
| `Grammatik/<level>/<Topic>.md` | One page per studied topic. |
| `Grammatik/Materials/wiktionary-snapshot.json` | `verbs`: de.wiktionary present-tense tables, written by `check_grammar_book.py fetch`. `evidence`: one-off checks (DW grammar pages from later lessons, numbers, declension tables, genders, register labels). |
| `Grammatik/Grammatik.pdf` | The whole book in one printable, clickable PDF (contents, bookmarks, a box for *My rule in my own words*). Built, never edited by hand. |
| `Grammatik/Materials/pdf-build.json` | Written by `build_grammar_pdf.py`: fingerprint of the builder, index and pages, the PDF's SHA-256, page order and tool versions. The tests compare it with the current pages. |
| `docs/tools/build_grammar_pdf.py` | Builds the PDF with pandoc (Markdown → HTML) and headless Chrome (HTML → PDF), offline. Refuses while the grammar check has errors; builds twice and requires identical bytes (Chrome's build time is replaced by the newest *checked* date). `--check` reports whether the PDF is current. Tested in `ANKI/tests/test_grammar_book.py`. |
| `docs/tools/check_grammar_book.py` | Offline check. Quotes in *Source* tables must be verbatim in the named lesson snapshot; *Wrong … From* rows linking to notes must quote them; *Person* tables must match the verb snapshot; card keys must be live; links must resolve; every page must be in the index. Tested in `ANKI/tests/test_grammar_book.py`. |

`Spickzettel/` holds the learner's own cheatsheets. No tool reads or writes it.

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

- `kind`: `production`, `response`, `completion` (needs `prompt.target`) or `register`.
- `answerSource` is a snapshot reference or `"learner-notes"`. With `"learner-notes"`, the answer must equal a covered entry.
- `retired: "<reason>"` keeps a card in the package, tagged and suspended.

## Revision and identity

- `lesson-vocabulary.json` → `revision` drives every timestamp in the packages.
  Bump it when you change content that is already imported, so Anki treats the
  notes as newer and updates them.
- GUIDs and note/card IDs come from card keys (`vocab:<lemma>|<sense>`,
  `article:<lemma>|<gender>`, `sentence:<key>`) plus the deck namespace. Keep
  keys stable when the learning target stays the same.
