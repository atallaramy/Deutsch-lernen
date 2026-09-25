# Decision log

Confirmed decisions, newest first. The binding rules they produce live in
`AGENTS.md`; this file records why and when.

## 2026-09-25 — follow-up

| Topic | Decision |
|---|---|
| Checking work | The learner does not do checking or review work. Claude verifies meanings, spellings and sources itself (official material, dictionaries, or a peer consult when online sources fall short). |
| English meanings | Every meaning that no official glossary supplies is checked against en.wiktionary (`ANKI/gloss-snapshot.json`). The build rejects unconfirmed ones. All current meanings pass. Four form terms took the dictionary's wording (e.g. *aufgehoben* → "annulled"). |
| Access | DW needs no login. For the VHS portal, Claude uses the learner's logged-in Chrome read-only; guest access needs the learner's yes to the data notice. No passwords in files or chat ([access.md](access.md)). |
| Easy German | The YouTube transcript panel works but SEG 274 only has auto-generated German captions. They are used to find items, never as card contexts ([easy-german-transcripts.md](easy-german-transcripts.md)). |
| Lesson deck names | Approved ("go ahead"): title-based names under one `Lessons::` deck in Anki. Old files are kept. |
| VHS portal | Learner logged in and consented to the data notice. The login stays inside the learner's own tab (session code in the web address), so Claude used guest access. The Lektion 2 vocabulary trainer (61 words, official English) was captured; it replaced dictionary meanings and corrected two guesses (*der Mann/die Frau* = man/woman; *mein Mann/meine Frau* from the notes stay as husband/wife). |
| Easy German SEG 274 | Captured 31 items. Auto captions are used only to find items, and every spelling and meaning is checked by DW, en.wiktionary or dict.cc. Three unconfirmed items are pending. A corrected transcript is kept as a study aid (not a card source). |

## 2026-09-25 — v3 redesign

Background: the redesign plan (kept in
[history/2026-09-25-redesign-plan.md](history/2026-09-25-redesign-plan.md)) was
reviewed and approved with these choices.

| # | Decision | Choice |
|---|---|---|
| — | Existing Anki progress | Not preserved; decks rebuilt from scratch. |
| — | Captured vocabulary | Never removed; no quotas; easy, proper-name and hard-to-contextualise items stay and are improved instead. |
| — | Deck separation | Vocabulary, Articles and Sentences stay separate, each with its own skill. |
| — | Records | Lesson notes and vocabulary records stay separate and attributable to course and lesson. |
| — | Sources | Use the official online materials of every course (DW, VHS, Easy German) and record the exact source. |
| — | Contexts | Preferred but never forced; a bare precise prompt when no good verified context exists. |
| — | Merging | Merge only identical lemma + sense across courses; keep distinct meanings separate. |
| — | Files | Do not move, rename or delete existing folders, Markdown, legacy packages or PDFs; new verified materials may be added inside `Materials/`. |
| — | Shipping | No pending, authored or merely assumed context may ship; source verification and the learner's preview must pass first. |
| — | Pronunciation deck | Left untouched; no audio/TTS in these decks. |
| — | Growth | Plan for A1, A2 and B1. Build gradually: a lesson is processed when the learner says it has been studied. |
| — | Reference | Keep every useful link in `docs/`, so the learner can ask about any lesson. |
| D1 | Cumulative scope | **A** — one cumulative system for all courses (`German A1 — …`), provenance in tags. |
| D2 | Data layout | **A** — one capture file (`lesson-vocabulary.json`) grouped by course → lesson, plus curated card files. |
| D3 | What counts as captured | **A** — vocabulary lists in the notes, items written with a meaning, and the official glossary of studied lessons. Borderline items wait for a yes/no. |
| D4 | Proper names | **A** — Sentences cards that practise how the name is used (first name ↔ du/Tschüss; Herr/Frau + surname ↔ Sie). |
| D5 | Home of whole utterances | **A** — fixed formulas in Vocabulary; patterns and grammatical choices in Sentences. |
| D6 | VHS content behind the login | *Open.* Default until decided: public PDFs only. Items from inside the portal keep "your notes" provenance and have bare cues. |
| D7 | Easy German capture | *Open.* SEG 274 is not captured yet. It needs the official transcript or Easy German's uploaded subtitles, and your confirmation of the item list. |
| D8 | Anki reset | Applied default **A**: new versioned note types and GUIDs; delete the old decks in Anki before importing ([anki-import.md](anki-import.md)). |
| Q1 | Lessons with empty notes | Do not build now; build each lesson when you say you studied it. |
| Q2 | "verstehr" | Captured as *verstehen* (to understand); you confirmed "mostly yes". |
| Q3 | Moving `Das ist Nico.md` / `Woher komst du.md` out of `Materials/` | Ask first. Not moved; their lesson decks go in the lesson folder under the current filenames. |
| Q4 | Legacy packages and duplicate PDFs | Keep. Removing clear duplicates needs your explicit go-ahead for each file ([known-issues.md](known-issues.md)). |
| Q5 | Keyboard | Mac German-Standard layout. Punctuation and capitalisation stay strict; typed answers use the keyboard apostrophe `'`. |

Interpretations recorded for your review:
- "Context" means German context sentences. English cues and scenes are
  prompts written to match the source and are reviewed in the preview.
- An Articles card keys on lemma + gender, because gender belongs to the noun
  form. *der Mann* has one Articles card, and separate Vocabulary cards for
  "man" and "husband".
- With a context, the typed answer is exactly the words in the blank (the
  sentence supplies the punctuation). Without a context, you type the full
  expression with its punctuation (`Guten Abend.`).
