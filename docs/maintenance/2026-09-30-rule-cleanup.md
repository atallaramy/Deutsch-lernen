# 2026-09-30: rule cleanup (learner's "go for all")

**Why:** the same rules sat in 4–6 files, and history was mixed into them; a
rule change on 2026-09-28 got lost that way. Goal: each rule in one place, no
change to lessons, cards, decks or the grammar book.

| Old place | New place |
|---|---|
| `AGENTS.md` step list 0–9 | `docs/processing-a-lesson.md` (AGENTS keeps a read trigger and the order) |
| `CLAUDE.md` Git, Files and safety, Open decisions, "never weaken a check", "report results as they came out" | `AGENTS.md` → *Files, safety and git*, *Shipping gate*, *Open decisions and new rules* |
| `CLAUDE.md` top-priority line | `AGENTS.md` → *Top priority* (CLAUDE keeps the Claude-specific *Replies* rules) |
| Dates and quotes inside rules | `docs/decisions.md`, now one line per decision |
| Backup rule (`ANKI/archive/` copies) | Git only: commit before changing builders, data format or rule files |
| Old global no-attribution reminder in `CLAUDE.md` | Removed: the global instructions already apply |

**Code with the same change:** `ANKI/archive/` deleted (in git history); the v2
record moved to `ANKI/legacy-v2-lesson-vocabulary.json` and a missing file is
now an error; noise warnings removed; `package` ends with `Import: …`.

**Checked:** deck check, grammar check, PDF check, unit tests, a rebuild with
unchanged packages. Not tested: a new session following the new files.

**Rollback:** `git revert` the cleanup commit (git holds every earlier version).
