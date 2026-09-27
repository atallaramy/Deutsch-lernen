# German Anki decks (v3)

Three cumulative decks by retrieval skill, for every course you study (DW,
VHS, Easy German):

| Package | Deck | Tests |
|---|---|---|
| `vocabulary.apkg` | German A1 — Vocabulary | one German word or fixed phrase, typed, in a verified context where a good one exists |
| `articles.apkg` | German A1 — Articles | der / die / das, typed |
| `sentences.apkg` | German A1 — Sentences | replies, forms, du/Sie switches and useful patterns, typed |

Each processed lesson also gets a typed introduction deck next to its notes
(`<notes name>_Vocabulary.apkg`). There is no audio, TTS, images or multiple
choice. The rules are in `../AGENTS.md`, the reasons in `../docs/card-design.md`.

## Workflow

```sh
python3 ANKI/build_all.py check                 # validate data, verify every context, write review/preview.html
python3 ANKI/build_all.py approve --all         # after you have reviewed the preview (or --lesson ID / --deck NAME)
python3 ANKI/build_all.py package               # build all packages; refuses unless checks pass and every card is approved
python3 -m unittest discover -s ANKI/tests      # tests
python3 ANKI/harvest_sources.py --lesson ID     # network: snapshot a lesson's official sources into Materials/
python3 ANKI/harvest_sources.py --pages         # offline: rewrite each DW lesson's Materials/lesson-pages.md
```

`package` builds every deck twice and requires identical bytes. It validates
SQLite integrity, note/card links and counts, empty media, the audio/TTS ban,
one typed answer per template, and unique IDs across packages. It also
confirms the pronunciation deck is unchanged, then writes the scan indexes.

## Data

- `lesson-vocabulary.json`: what you studied, per course and lesson, with provenance (schema 3)
- `vocabulary-cards.json`, `articles-cards.json`: curated cues and verbatim contexts
- `sentence-sources.json`: curated Sentences cards
- `review/`: preview, coverage ledger, your approvals
- `archive/`: backups of replaced files

Details: `../docs/data-model.md`. Procedure for a new lesson:
`../docs/processing-a-lesson.md`.
