# Decision log

Confirmed decisions, newest first. The binding rules they produce live in
`AGENTS.md`; this file records why and when.

## 2026-09-27 — vocabulary and grammar pages

| Topic | Decision |
|---|---|
| Goal | The learner: "the idea is to record anything new in those pages [the lesson's grammar page and vocabulary page on the web] and add them to the proper Exercises. this is the goal of your help." Interpretation, applied: "the proper Exercises" means the right deck (Vocabulary, Articles, Sentences) through the usual capture, and the grammar book for a grammar rule. |
| Vocabulary page | Every item on a studied DW lesson's vocabulary page (`/lv`) is recorded in that lesson (entry, pending or declined). `build_all.py check` reports any item that is not. `vocabularyPageForm` links an entry the page writes differently. |
| Grammar pages | Every DW grammar page of a studied lesson is covered by a grammar-book topic page and linked from it; `check_grammar_book.py` reports any that is not. New words and phrases on grammar pages are captured like script items (`origin`: `dw-grammar-page`). |
| Saved copies | The learner: "it is a good idea to save what you see in grammar page and vocabulary page if you think this is useful (in the materials folder)". Applied: the snapshot now holds the vocabulary page, and each DW lesson's `Materials/lesson-pages.md` is a readable copy of its vocabulary, grammar and culture pages (tables and bold endings kept, no audio). |
| Studied lessons | All 10 studied DW lessons were checked: every vocabulary-page item and every grammar page was already recorded, so no cards changed. One item is written differently on the page (`Es ist 09:00 Uhr.`; the PDF and the entry: `Es ist neun Uhr.`) and got `vocabularyPageForm`. |
| Snapshots | Re-harvested; exercise, grammar and culture texts are unchanged apart from dropped photo credits (`null DW`). |
| VHS | Unchanged: the word list, the vocabulary trainer and the grammar list are the VHS equivalents; content inside the portal stays under D6. |

## 2026-09-27 — DW A1 E2 L2 Wichtige Nummern

| Topic | Decision |
|---|---|
| Notes | Moved up from `Materials/` with the learner's yes ("yes move the notes up"). |
| Mistake rounds | Two rounds, saved in the lesson's `Materials/mistakes.md`; three items still open after round 2. |
| Grammar terms | No to *der Indikativ, der Konjunktiv, der Imperativ*: the learner looked them up "preparing for future courses". Recorded as `declinedEntries`. |
| Mistake feedback | The learner will test the "In your notes: …" line on the card backs before deciding whether to keep it. No change yet. |
| Build | The learner approved all 43 new and changed cards; decks built (427 Vocabulary, 149 Articles, 65 Sentences, 12 lesson decks). |

## 2026-09-27 — capture from official materials

| Topic | Decision |
|---|---|
| Capture scope | Changes D3. The learner: "the official materials are also a good source of the decks". Words and fixed phrases worth learning at the lesson's level in a studied lesson's official script and exercises become entries, next to the notes and the glossary. Their meanings go through the dictionary check. Unclear items go to `pendingEntries`. |
| Contexts | Unchanged: script and exercise sentences are the verbatim contexts on the cards. |
| Backfill | The learner: update the cumulative decks for the lessons already studied; "maybe the individual lessons deck do not need that update". New entries there carry `inLessonDeck: false`. Interpretation, applied: each new word is recorded once, in the first lesson where it appears. Words already captured are not recorded again, so approved cards stay as they are. |
| Backfill build | The learner approved all 176 new and changed cards ("approve all"): 134 entries from the scripts and exercises of 10 studied lessons; decks built (404 Vocabulary, 141 Articles, 59 Sentences); lesson decks keep their cards. |

## 2026-09-26 — lesson folder layout

| Topic | Decision |
|---|---|
| `Materials/` | Kept (flat lesson folders were considered). Official materials, `source-snapshot.json` and `mistakes.md` go there. |
| Notes | The learner's notes sit directly in the lesson folder. `Das ist Nico.md`, `Woher komst du.md` and `Zahlen von 1 bis 100.md` were moved up with the learner's yes (resolves Q3); every link to them was updated. |

## 2026-09-26 — printable grammar book

| Topic | Decision |
|---|---|
| Grammar PDF | The learner asked for one browsable, printable file, updated after every lesson, keeping the Markdown pages. `Grammatik/Grammatik.pdf`: cover, clickable contents, one topic per page in index order, PDF bookmarks, page numbers, a lined box for *My rule in my own words*. |
| No fluctuations | The same pages always give byte-identical output; a new page joins by being listed in the index; the build refuses while the grammar check fails; the tests fail while the PDF lags the pages. |
| Tools | pandoc and Google Chrome, both already installed; no network. Links to local notes print as plain text, web links stay clickable. |
| Scope | One PDF for all levels (A2 and B1 will be added as parts), rather than the `Grammatik-A1.pdf` first mentioned. |

## 2026-09-26 — mistake rounds

| Topic | Decision |
|---|---|
| Mistake rounds | The learner's proposal, confirmed: the default first step for every finished lesson. Claude checks the notes against the official sources and dictionaries. Round 1 lists the wrong words exactly as written (with line numbers), no comments; the learner fixes them. Round 2 lists what is still wrong as *wrong → correct*; the learner fixes those. Only then does lesson processing start. |
| Session override | The learner's instruction in a session wins for that session, e.g. "I finished the lesson, correct spelling and start finalizing": Claude saves the mistakes, corrects the notes and continues. |
| Record | Each round is saved in the lesson's `Materials/mistakes.md` before the notes change. Cards (`learnerForm`) and the grammar book quote that file. |
| Checking work | The mistake rounds are the learner's own study exercise; they do not conflict with "the learner does no checking work". |
| What counts | Interpretation, applied: spelling, capitals, umlauts, missing or wrong words, word forms, articles, and punctuation that changes the sentence. Audio lines with no official transcript are listed as uncheckable instead of guessed. |
| First use | DW A1 E2 L1 *Zahlen von 1 bis 100*, before its cards are approved. |
| DW A1 E2 L1 build | The learner approved all 49 new and changed cards after two mistake rounds; the decks were built (270 Vocabulary, 102 Articles, 59 Sentences, 11 lesson decks). |

## 2026-09-26 — grammar book

| Topic | Decision |
|---|---|
| Grammar book | Yes, as proposed: `Grammatik/README.md` index by level and topic, one short Markdown page per studied topic in `Grammatik/A1/`, Markdown only. A check script verifies examples, quoted mistakes, card keys and verb tables whenever the book is updated. It is reference material; the Sentences deck stays the home of grammar practice. |
| Cheatsheets | Changed from the proposal: no Claude-made A1 cheatsheet. `Spickzettel/` is the learner's own folder. In the learner's words: a cheatsheet is "the keys to the knowledge in my head"; built to the learner's taste and understanding; minimal; "when it is too much, it is no longer cheatsheet." Claude may suggest a cheatsheet but asks first. |
| Printing | The learner may ask at any time for lessons or pages collected in a printable format, "to stay away from the computer". Made on request only. |
| After-lesson routine | "Update the grammar book" is step 8 of `docs/processing-a-lesson.md` (step 7 in `AGENTS.md`). |
| Cases | Not an A1-now topic; listed as coming (DW A1 E9+, VHS A1 Lektion 4 for the accusative). The learner's case table and possessive table were checked against Wiktionary and are correct. |
| Sources | Interpretation, applied: DW grammar pages from lessons not yet studied may confirm a rule. Examples come only from studied lessons' snapshots. The in-progress DW E2 L1 notes are not used until the learner says the lesson is studied. |

## 2026-09-25 — build and version control

| Topic | Decision |
|---|---|
| Grammar terms | Yes to *das Personalpronomen, der Singular, der Plural, das Verb, die Konjugation, das Präsens*, "if they are not wrong". Gender, plural and meaning were checked in de.wiktionary and en.wiktionary; all match the notes. |
| USA, DNA, GuMo | No. Recorded as `declinedEntries`, never built. |
| Build | The learner approved all cards; the v3 decks were built (255 Vocabulary, 97 Articles, 52 Sentences, 10 lesson decks). |
| Git | The workspace is a git repository (`main`). One commit before the first build and one after. From now on the learner asks for a commit after every new lesson. |

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
| D3 | What counts as captured | **A** — vocabulary lists in the notes, items written with a meaning, and the official glossary of studied lessons. Borderline items wait for a yes/no. Widened 2026-09-27 to the official script and exercises (see *capture from official materials*). |
| D4 | Proper names | **A** — Sentences cards that practise how the name is used (first name ↔ du/Tschüss; Herr/Frau + surname ↔ Sie). |
| D5 | Home of whole utterances | **A** — fixed formulas in Vocabulary; patterns and grammatical choices in Sentences. |
| D6 | VHS content behind the login | *Open.* Default until decided: public PDFs only. Items from inside the portal keep "your notes" provenance and have bare cues. |
| D7 | Easy German capture | *Open.* SEG 274 is not captured yet. It needs the official transcript or Easy German's uploaded subtitles, and your confirmation of the item list. |
| D8 | Anki reset | Applied default **A**: new versioned note types and GUIDs; delete the old decks in Anki before importing ([anki-import.md](anki-import.md)). |
| Q1 | Lessons with empty notes | Do not build now; build each lesson when you say you studied it. |
| Q2 | "verstehr" | Captured as *verstehen* (to understand); you confirmed "mostly yes". |
| Q3 | Moving `Das ist Nico.md` / `Woher komst du.md` out of `Materials/` | Ask first. Not moved; their lesson decks go in the lesson folder under the current filenames. Resolved 2026-09-26: moved up (see *lesson folder layout*). |
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
