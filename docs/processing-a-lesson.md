# Processing a lesson (when you say "I have studied lesson X")

Read this before capturing or building any lesson. It is the procedure behind
`AGENTS.md` → *When processing a lesson*. Build gradually: only lessons you
have studied, one at a time, so the deck never grows faster than your
learning.

## 0. Trigger and scope

- Start only when you say you have studied a specific lesson, or you ask for
  it. For a lesson you have not studied, answer questions from
  [`course-index/`](course-index/) and [links.md](links.md) and do not build cards.
- Do not move, rename or delete existing notes, folders, PDFs or legacy
  packages. If a notes file lives somewhere unusual (for example inside
  `Materials/`), leave it there and ask before changing anything.

## 1. Read

- Your Markdown notes for the lesson, all of it: vocabulary lists, glossed
  items, exercise answers, errors.
- The official materials. For DW, the script/vocabulary PDF in `Materials/`
  (download it if missing). For VHS, the word list, film script and grammar list
  ([links.md](links.md)). For Easy German, the method in
  [easy-german-transcripts.md](easy-german-transcripts.md) (auto-generated
  captions locate items but are never used as contexts).
- The lesson row in the course index (goal and grammar topic).

## 2. Snapshot the official sources (network, run once per lesson)

1. Add the lesson to `ANKI/lesson-vocabulary.json` (course, id, title, URLs,
   notes file, lesson-deck file, snapshot path, sources) with an empty entry
   list.
2. Run `python3 ANKI/harvest_sources.py --lesson <lesson-id>`.
   - For DW this snapshots the script PDF text plus every exercise, grammar and culture page.
   - For VHS it downloads the course PDFs into `VHS-Lernportal/<level>/Materials/` and snapshots them.
3. Check the snapshot contains the lesson's script and exercises.
4. For VHS, also capture the lesson's vocabulary trainer with English (official
   meanings) through the browser ([access.md](access.md)).

## 3. Capture (faithful, never remove)

For each item, add an entry with:
- `german` in the official spelling
- `english`, taken from the official gloss when there is one
- `pos`, `lemma` and `sense`
- `plural`, `forms` and `note` from the glossary
- `origin`
- `learnerForm` when your spelling differs

English meanings: use the official gloss when there is one. Otherwise run
`python3 ANKI/harvest_sources.py --glosses`. The build accepts only meanings
the dictionary confirms. For phrases, set `glossLookup` to their component
words, and use the dictionary's wording.

Which items to capture:
- **Captured:** items in a vocabulary list in your notes, items you wrote with a meaning, and the official lesson glossary.
- **Borderline:** put in `pendingEntries` with a reason and ask you yes or no.
- **Home deck:** fixed formulas → `home: vocabulary`; patterns and grammatical choices (du/Sie, verb forms, W-questions) → `home: sentences`. Names → Sentences.
- **Merging:** a new sense of a known word gets its own `sense`. Identical lemma + sense merges automatically.

## 4. Curate

- **Contexts** (`ANKI/vocabulary-cards.json`, `ANKI/articles-cards.json`):
  - only exact excerpts from the lesson snapshots (or another official snapshot), with a `target` that occurs once
  - Articles contexts need the gender article directly before the noun
  - no context is better than a forced one
- **Cues:** precise English; add a disambiguator when two cards could share an answer.
- **Sentences** (`ANKI/sentence-sources.json`):
  - cover every `home: sentences` entry
  - add a few useful extras (replies, forms, register switches)
  - German on the front must be verbatim
  - answers must be verbatim in a snapshot or be your own captured sentence

## 5. Check and preview

```sh
python3 ANKI/build_all.py check
python3 -m unittest discover -s ANKI/tests
```

Fix every error. Open `ANKI/review/preview.html`, read the cards flagged with
notes first, and look at merges and senses kept separate.

## 6. Approve (your step)

You review the preview, then:

```sh
python3 ANKI/build_all.py approve --lesson <lesson-id>   # or --all / --deck vocabulary|articles|sentences
```

Claude runs this only when you explicitly say in the conversation which cards
you approve.

## 7. Package and import

```sh
python3 ANKI/build_all.py package
```

This refuses unless every check passes and every card is approved. It builds
every package twice to prove the output is identical, validates each one, and
confirms the pronunciation deck is untouched. It then writes the `.apkg` files
and scan indexes. Import them into Anki ([anki-import.md](anki-import.md)).

## 8. Record

- New rules or decisions go to `AGENTS.md` and [decisions.md](decisions.md).
- New useful links go to [links.md](links.md). If a course changes, rerun
  `python3 docs/tools/build_course_index.py`.
