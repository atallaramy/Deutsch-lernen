# Maintenance note — project instructions, 2026-09-25

## Changed files

| File | Change |
|---|---|
| `AGENTS.md` | Rewritten for the v3 system and the learner's decisions (D1–D5, Q1–Q5). Still the shared rulebook for every agent. |
| `CLAUDE.md` (new) | Imports `@AGENTS.md` and adds Claude-specific rules: answering lesson questions, the approval gate, safety, commands. |

Why the import: Claude Code reads `AGENTS.md` only when a project has no
`CLAUDE.md`. Once `CLAUDE.md` exists, the import keeps a single shared source
of truth instead of two competing copies (Claude Code memory docs, checked
2026-09-25).

## Where every old rule went

| Old rule (AGENTS.md before 2026-09-25) | Now |
|---|---|
| Folder structure; `ANKI/` holds cumulative decks; per-lesson folders with Markdown, deck, `Materials/`; download DW PDFs | AGENTS.md → *Folder structure*, extended to VHS and Easy German, plus the new no-move/rename/delete rule and `docs/` |
| Capture vocabulary in `ANKI/lesson-vocabulary.json` with lesson ID, title, URL, Markdown path, entries | AGENTS.md → *Capture records* (schema 3: course grouping, provenance, `learnerForm`, never remove) |
| One cumulative Nico’s Weg review system in three skill decks; `DW A1 —` label reserved | AGENTS.md → *Cumulative decks*. Changed by D1-A: all courses, `German A1 —` names |
| Articles: noun alone on the front, typed recall, no multiple choice, plural and dependable hint after answering | AGENTS.md → *Cumulative decks → Articles*, now with leak-free sentence contexts when verbatim |
| Vocabulary: precise English/context front, one typed item; noun without article; infinitive without placeholders; merge exact repeats | AGENTS.md → *Vocabulary*. Merging is now "identical lemma + sense" |
| Sentences: selective, curated, one target, corrective feedback, no mirrors or multiple choice; home for verbs and grammar | AGENTS.md → *Sentences* and *Card-quality gate* |
| Quality over count; no duplicate recall; fixed expressions in Vocabulary, patterns in Sentences, gender in Articles | AGENTS.md → *Cumulative decks* (ownership, D5-A) |
| No audio/TTS/sound in the review decks; the pronunciation resource is outside the rule | AGENTS.md → *Cumulative decks* (unchanged; images added to the ban) |
| Preserve notes, IDs and scheduling; never recreate from scratch unless asked | AGENTS.md → *Identity and scheduling*. The learner asked for this one clean rebuild; stable keys and retirement apply from now on |
| Maintain scan indexes | Written by `build_all.py package` (docs/data-model.md) |
| Lesson decks: `<Lesson>_Vocabulary.apkg`, `DW — <Lesson> Vocabulary (typed)`, typed production, no duplicate of Sentences items | AGENTS.md → *Lesson-specific decks*. Now complete lesson coverage (never remove captured items), including the lesson's Sentences cards |
| When processing a lesson: 5 steps | AGENTS.md → *When processing a lesson* (gradual trigger, snapshots, approval) and `docs/processing-a-lesson.md` |
| Card-quality gate (6 points); 2–5 sentence cards per lesson as a guide | AGENTS.md → *Card-quality gate* (7 points; no quotas for Vocabulary/Articles) |
| Development status; ask before new enduring rules; `ANKI/anki-card-design-reference.md` for implementation choices | AGENTS.md → *Development status* (unchanged, plus `docs/decisions.md`) |

## Validation

- Static: the `@AGENTS.md` import sits on its own line outside code
  blocks. Every path mentioned in `CLAUDE.md` exists. The commands were run in
  this session: `check` gives 0 errors, the tests pass (17), and `package`
  refuses without approval.
- Loading: not tested in a fresh session. To confirm, run `/context` in a new
  Claude Code session and check that `CLAUDE.md` and `AGENTS.md` appear under
  Memory files.
- No model-specific profile was added; the global instructions already cover
  model tuning.

## Backup and rollback

The original `AGENTS.md` is at
`ANKI/archive/2026-09-25-pre-v3/AGENTS.md.orig` (SHA-256 in that folder's
`MANIFEST.json`), along with the replaced builders, data and packages. To roll
back, copy each backup to its original path and delete `CLAUDE.md`. Do not
restore the old builders on their own: they expect the schema-2 data.
