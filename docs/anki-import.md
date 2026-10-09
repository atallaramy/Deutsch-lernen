# Importing the decks into Anki

Only import packages built by `python3 ANKI/build_all.py package`, which runs
after every check passes.

## First import of the v3 decks (one time)

The v3 decks use new note types and new card identities (decision D8), so
remove the old ones first. Otherwise you would review both.

1. In Anki desktop, delete these decks if you have them: `DW A1 — Vocabulary`,
   `DW A1 — Articles`, `DW A1 — Sentences`, and the old lesson decks
   `DW — … Vocabulary (typed)` and `German A1 — Tschüss!`. Leave
   `DW German — Von A bis Z Phonetic Alphabet (pronunciation)` alone.
2. Tools → Manage Note Types: delete the old, now empty types (`German
   Vocabulary — precise production`, `German Articles — typed answers`,
   `German Sentences — …`, `DW … — Precise production`).
3. File → Import: `ANKI/A1/vocabulary.apkg`, `ANKI/A1/articles.apkg`,
   `ANKI/A1/sentences.apkg`.
4. Lesson decks (optional, for a first typed pass through a lesson): import
   `ANKI/A1/Lessons.apkg`, which holds every lesson deck and grows with each
   lesson. Each lesson's own `… - Vocabulary.apkg` next to its notes holds the
   same cards. In Anki they appear under one `Lessons` deck. Do not import the
   old `…_Vocabulary.apkg` files. Lesson decks repeat cards from the cumulative
   decks; once you have gone through a lesson, suspend its cards (Browse →
   select them → Cards → Toggle Suspend) rather than delete the deck, because
   the next import of `Lessons.apkg` would bring a deleted deck back as new cards. Or skip them and use a filtered deck: *Tools → Create
   Filtered Deck*, search `tag:lesson::dw-a1-e1-l3 is:new`.

## Later updates

Re-importing an updated package updates the existing notes (same GUIDs) and
keeps your review history. Import settings: allow updating notes, keep
scheduling.

## Recommended settings

- FSRS on; desired retention 0.90 (Deck options → FSRS).
- New cards per day: about 10–15 across the three decks. Raise it only if
  reviews stay comfortable.
- Leech action: tag only. Tell Claude about leeches, since they usually point to a card
  that needs a better cue.

## Typing on the Mac German keyboard

- ä ö ü ß have their own keys.
- The apostrophe is Shift+#; typed answers expect this `'`.
- Capitals and punctuation count: `Guten Abend.` is not `guten abend`.
- AnkiWeb does not show the typing box; use Anki desktop or the mobile app.
