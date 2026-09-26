# Docs: reference library for learning German

Everything worth keeping from the research, so it can be reused at A1, A2 and
B1. Ask Claude about any lesson ("what grammar is in DW A1 E5 L2?", "what does
VHS Lektion 4 cover?"). The answer starts from here.

| File | What it is for |
|---|---|
| [../Grammatik/](../Grammatik/README.md) | My grammar book: one short page per studied topic (rule, table, verified examples, my mistakes, official links, Sentences cards). Start here for grammar questions. |
| [../Spickzettel/](../Spickzettel/) | My cheatsheets. My folder; Claude writes there only when I ask. |
| [links.md](links.md) | Every useful link, checked 2026-09-25 (grammar sources 2026-09-26): DW, VHS, Easy German, Goethe word lists, CEFR, dictionaries, Anki, research. |
| [course-index/](course-index/) | Lesson by lesson: title, goal, grammar topic, lesson page, script PDF for DW Nicos Weg A1, A2, B1; topics and grammar per lesson for VHS A1, A2, B1. |
| [learning-roadmap.md](learning-roadmap.md) | How the system grows from A1 to A2 and B1, and what changes in the decks at each level. |
| [processing-a-lesson.md](processing-a-lesson.md) | The step-by-step procedure when you say "I have studied lesson X". |
| [card-design.md](card-design.md) | Why the cards look the way they do, with real examples and the leakage checks. |
| [research.md](research.md) | The evidence behind the design. |
| [decisions.md](decisions.md) | Every confirmed decision, with date. |
| [access.md](access.md) | What access Claude needs for each course (DW public; VHS through your logged-in Chrome). |
| [easy-german-transcripts.md](easy-german-transcripts.md) | How to get YouTube transcripts and what they can be used for. |
| [anki-import.md](anki-import.md) | Importing, recommended settings, typing German on the Mac. |
| [data-model.md](data-model.md) | The data files, tools and schemas. |
| [known-issues.md](known-issues.md) | Open decisions, pending yes/no items, fixed data errors, workspace notes. |
| [history/](history/) | The approved redesign plan (2026-09-25). |
| [maintenance/](maintenance/) | Notes on changes to the project instructions. |
| [tools/build_course_index.py](tools/build_course_index.py) | Rebuilds `course-index/` from the official course pages (network). |
| [tools/check_grammar_book.py](tools/check_grammar_book.py) | Checks the grammar book against the lesson snapshots, my notes, the Sentences cards and Wiktionary (`fetch`: network). |

The binding rules for the decks are in `../AGENTS.md`; Claude-specific working
rules are in `../CLAUDE.md`.
