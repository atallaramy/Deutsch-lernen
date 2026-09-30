# Claude instructions — German-learning workspace

@AGENTS.md

`AGENTS.md` (imported above) holds all project rules and is shared with other
agents; change rules there. This file adds only how Claude works here.

## Replies

- At most 5 lines: what is done, what is needed. No card or test counts, file
  paths or check results unless the learner asks or something failed.
- Progress notes: one line, only for news or a blocker.
- Calm and concrete. Ask only real decisions, with concrete examples.
- After a lesson: one line `Import: …` with only the files that `package` lists.
- When the learner changes a rule, make sure the edit is in the rule files. If
  an edit is blocked, say so in the same reply.

## The learner

- A1 now with DW *Nicos Weg*, the VHS-Lernportal course and Easy German; then
  A2 and B1. The system grows gradually with their study; a large build at once
  is discouraging.
- Mac with the German-Standard keyboard; typed answers stay strict about
  spelling, capitals, umlauts and punctuation.
- Their effort goes to studying German. Never hand them checking or review work
  (meanings, spellings, sources, card lists). Verify it yourself: official
  course material, dictionaries (`python3 ANKI/harvest_sources.py --glosses`),
  or a peer consult when online sources fall short. Exception, by their choice:
  the mistake rounds on their own lesson notes are a study exercise.

## Questions about a lesson

- For any question about a lesson or level (grammar, vocabulary, goals, what
  comes next): first read the matching file in `docs/course-index/`
  (`dw-nicos-weg-a1.md`, `…-a2.md`, `…-b1.md`, `vhs-a1.md`, `vhs-a2.md`,
  `vhs-b1.md`) and `docs/links.md`. Then open the official lesson page or PDF
  linked there for detail, and cite the links you used.
- For a grammar question, also read the topic page in the grammar book
  (`Grammatik/README.md` is the index). It holds the verified rule, examples and
  the learner's own mistakes.
- For a lesson the learner has studied, also use its notes, its
  `Materials/lesson-pages.md` and its `Materials/source-snapshot.json`.
- Answering questions never builds cards.
- When you find a new useful source, add it to `docs/links.md` with the date
  you checked it.
- Access: DW is public. For VHS portal pages use the learner's logged-in Chrome
  (Claude in Chrome, read-only); never ask for, store or type passwords. The
  portal's login stays inside the learner's own tab, so use guest access, which
  the learner consented to. See `docs/access.md`. Easy German transcripts:
  `docs/easy-german-transcripts.md`.

## Building decks

- Read `docs/processing-a-lesson.md` in full before capturing or building any
  lesson.
- Never ask the learner to review cards; read the new cards yourself with
  `check --lesson ID`.
- Commands:
  - `python3 ANKI/build_all.py check` — validate, verify sources (`--lesson ID`: list that lesson's cards)
  - `python3 ANKI/build_all.py package` — build packages (refuses while the check has errors; ends with `Import: …`)
  - `python3 -m unittest discover -s ANKI/tests`
  - `python3 ANKI/harvest_sources.py --lesson ID` — network: snapshot official sources and write `Materials/lesson-pages.md`
  - `python3 ANKI/harvest_sources.py --pages` — offline: rewrite the DW `lesson-pages.md` copies from their snapshots
  - `python3 ANKI/harvest_sources.py --glosses` — network: dictionary check of meanings no glossary supplies
  - `python3 docs/tools/build_course_index.py` — network: rebuild the lesson index
  - `python3 docs/tools/check_grammar_book.py` — check the grammar book (`fetch`: network, Wiktionary verb tables)
  - `python3 docs/tools/build_grammar_pdf.py` — rebuild `Grammatik/Grammatik.pdf` after the check (`--check`: is it current?)
