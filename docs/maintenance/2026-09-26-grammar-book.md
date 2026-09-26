# Maintenance note: grammar book, 2026-09-26

## Changed files

| File | Change |
|---|---|
| `AGENTS.md` | Folder list gains `Grammatik/` and `Spickzettel/`. New sections *Grammar book* and *Cheatsheets and printing*. *When processing a lesson* gains step 7 (update the grammar book); tests and commit move to steps 8 and 9. |
| `CLAUDE.md` | Grammar questions also read the topic page in `Grammatik/`. The command list gains `docs/tools/check_grammar_book.py`. |
| `docs/processing-a-lesson.md` | New §8 *Update the grammar book*; *Commit* and *Record* renumbered to §9 and §10. §0 points grammar questions to `Grammatik/`. |
| `docs/README.md`, `docs/data-model.md`, `docs/links.md`, `docs/decisions.md` | New rows and sections for the grammar book, its tool and snapshot, the grammar references and the decisions of 2026-09-26. |

New files: `Grammatik/` (index, 12 A1 pages, `Materials/wiktionary-snapshot.json`),
`Spickzettel/.gitkeep`, `docs/tools/check_grammar_book.py`, `ANKI/tests/test_grammar_book.py`.

## Preservation

No existing rule was removed or weakened. The deck rules, the approval gate, the
source rules and the file-safety rules are unchanged. The only renumbering is in
the lesson steps (`AGENTS.md` 7–8 → 8–9; `processing-a-lesson.md` §8–9 → §9–10).
The deck builders and deck data were not changed.

## Validation (2026-09-26)

- `python3 docs/tools/check_grammar_book.py`: 0 errors.
- `python3 -m unittest discover -s ANKI/tests`: all pass; the one skip is the existing
  "every card is approved" case.
- `python3 ANKI/build_all.py check`: exit 0, no errors; card counts unchanged (255 · 97 · 52).

## Rollback

Copy each backup in `ANKI/archive/2026-09-26-grammar-book/` (hashes in its
`MANIFEST.json`) to its original path, then delete the new files listed above.
