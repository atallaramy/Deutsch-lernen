# Decision log

One line per confirmed decision, newest first. The rules they produce live in
`AGENTS.md`; git holds the full history.

| Date | Decision |
|---|---|
| 2026-10-01 | `next-steps.md` (first named `roadmap.md`): the learner's next steps, extremely short; its rule line and the file are protected from every AI (Claude hook + test). |
| 2026-10-01 | Git: commits made after the last push are merged into one commit ("I want no git history noise"). |
| 2026-10-01 | Exam practice is marked and explained the way Goethe examiners judge, with Goethe sources, not the course lessons ("This is all done for them"). |
| 2026-10-01 | Exam practice: speaking sent as dictation is marked only on what can be heard, not capitals or punctuation ("I did not type this"). |
| 2026-10-01 | "Exam practice" routine, on request only: Goethe A1 practice limited to the parts whose topics are studied, marked and logged ([exam-practice.md](exam-practice.md)). The exam date is a possibility, not a goal. |
| 2026-09-30 | No card preview or approval step: the learner does not review cards ("remove the preview completely"); `package` needs only a clean check; Claude reads new cards itself (`check --lesson`). Replaces the v3 preview rule and the unrecorded 2026-09-28 request. |
| 2026-09-30 | Accents in non-German names are fixed by Claude in the notes and noted in `mistakes.md` ("I am not here to fix Spanish names"). |
| 2026-09-30 | Words above A1 from official sources are added without asking, tagged Beyond A1 (after "Yes, all 5": *hoffentlich, informiert, die Suche, Setzen Sie sich doch bitte., rausfinden*). |
| 2026-09-30 | Claude commits when a lesson is done, without asking, and before changing builders, the data format or rule files. |
| 2026-09-30 | Kept as they are: lesson decks ("the most valuable"), every DW vocabulary-page item, the grammar book, the mistake rounds. |
| 2026-09-30 | Backups: git only. The `ANKI/archive/` copies were deleted (still in git history); the v2 record moved to `ANKI/legacy-v2-lesson-vocabulary.json`. |
| 2026-09-30 | Replies: at most 5 lines, no counts, paths or check results unless asked or failed; after a lesson one `Import: …` line (`package` lists the files whose cards changed). |
| 2026-09-30 | Rule files: each rule in one place (`AGENTS.md` rules, `processing-a-lesson.md` steps, `CLAUDE.md` Claude only); this log one line per decision. |
| 2026-09-30 | Warnings only for real problems (a cue that gives the answer away, unknown words in an example); "no example sentence", "Beyond A1" and "your own sentence" no longer warn. Errors unchanged. |
| 2026-09-30 | E2 L4 merges: *einhundert, warum, Nachname, Onkel, Tochter, Postleitzahl, Wohnort* join existing cards; *Passnummer* / *Reisepassnummer* stay two cards (short / full form, like *hundert* / *einhundert*); *PLZ* has its own card. |
| 2026-09-28 | Top priority: make studying German easier and save the learner's time, "the only bible"; everything easy and short. |
| 2026-09-28 | `beyond-A1` follows the Goethe-Zertifikat A1 word list. |
| 2026-09-28 | E2 L3 words above A1 kept ("I like those 5 words even if they are above A1"): *passieren, aufschreiben, der Aufnäher, die Polizeistelle, die Radiomoderatorin*. |
| 2026-09-28 | Country list (*aus dem / aus der* + country): not now ("not important right now"), declined. |
| 2026-09-28 | E2 L3 merges: *Entschuldigung* joins *excuse me / sorry*; *Noch einmal, bitte* and *Nochmal, bitte* one card; *Mir geht's gut.* its own Sentences card; *Viel Glück!* / *Viel Erfolg!* cues tell them apart. |
| 2026-09-28 | *die Ergänzungsfrage* takes dict.cc's "completive question"; its cue names it the other word for a W-question. |
| 2026-09-28 | The harvester also saves exercise read-aloud lines and tips (E2 L3 re-harvested). |
| 2026-09-27 | Goal: record everything new on a lesson's vocabulary and grammar pages in the right deck, and a grammar rule in the grammar book. |
| 2026-09-27 | Every item on a studied DW lesson's vocabulary page is recorded in that lesson; `check` reports missing ones; `vocabularyPageForm` for different wording. |
| 2026-09-27 | Every DW grammar page of a studied lesson is covered and linked by a grammar-book page; its new words are captured (`dw-grammar-page`). |
| 2026-09-27 | The snapshot keeps the vocabulary page; each DW lesson gets `Materials/lesson-pages.md`, a readable copy of its vocabulary, grammar and culture pages. |
| 2026-09-27 | Capture widened (changes D3): words and fixed phrases worth learning from a studied lesson's official script and exercises ("the official materials are also a good source"). |
| 2026-09-27 | Backfill of already-studied lessons goes into the cumulative decks only (`inLessonDeck: false`); each word recorded once, in its first lesson. |
| 2026-09-27 | E2 L2 notes moved up from `Materials/` ("yes move the notes up"). |
| 2026-09-27 | No to *der Indikativ, der Konjunktiv, der Imperativ* (looked up for future courses); declined. |
| 2026-09-27 | Open: the learner tests the "In your notes: …" line on card backs before deciding whether to keep it. |
| 2026-09-26 | Mistake rounds are the first step of every finished lesson: round 1 the wrong words as written, no comments; round 2 *wrong → correct*; saved in `Materials/mistakes.md` before the notes change. They are the learner's own study exercise. The learner's instruction in a session replaces them for that session. |
| 2026-09-26 | A mistake is spelling, capitals, umlauts, missing or wrong words, word forms, articles, or punctuation that changes the sentence; audio lines without a transcript are listed as uncheckable. |
| 2026-09-26 | `Materials/` kept for official materials, snapshots and mistakes; notes sit directly in the lesson folder (three notes files moved up; resolves Q3). |
| 2026-09-26 | Grammar book `Grammatik/`: one Markdown page per studied topic, checked by a script; reference only, the Sentences deck stays the home of grammar practice. |
| 2026-09-26 | `Grammatik/Grammatik.pdf`: one printable, clickable file for all levels, rebuilt after every lesson, byte-identical for the same pages (pandoc + Chrome, offline). |
| 2026-09-26 | `Spickzettel/` is the learner's: "the keys to the knowledge in my head", minimal; Claude may suggest a cheatsheet but asks first. |
| 2026-09-26 | Printable collections of lessons or pages only on request ("to stay away from the computer"). |
| 2026-09-26 | Cases are not an A1-now topic (listed as coming); the learner's case and possessive tables were checked and are correct. |
| 2026-09-26 | DW grammar pages from later lessons may confirm a rule; examples come only from studied lessons. |
| 2026-09-25 | The learner does no checking or review work; Claude verifies meanings, spellings and sources (official material, dictionaries, or a peer consult when online sources fall short). |
| 2026-09-25 | Meanings no official glossary supplies are checked against en.wiktionary (else dict.cc); the build rejects unconfirmed ones. |
| 2026-09-25 | Access: DW needs no login; the VHS portal through the learner's Chrome, read-only, guest access (consented); no passwords in files or chat. |
| 2026-09-25 | Easy German auto captions only locate items, never card text; SEG 274 captured (31 items, three pending). |
| 2026-09-25 | VHS L2 vocabulary trainer captured with official English (*der Mann / die Frau* = man / woman; *mein Mann / meine Frau* = husband / wife). |
| 2026-09-25 | Lesson decks named after the lesson title under one `Lessons::` deck ("go ahead"); old files kept. |
| 2026-09-25 | Yes to *das Personalpronomen, der Singular, der Plural, das Verb, die Konjugation, das Präsens*; no to USA, DNA, GuMo (declined). |
| 2026-09-25 | The workspace is a git repository (`main`). |
| 2026-09-25 | v3 redesign ([history/2026-09-25-redesign-plan.md](history/2026-09-25-redesign-plan.md)): old Anki progress not kept; decks rebuilt from scratch. |
| 2026-09-25 | v3: captured vocabulary is never removed; no quotas. |
| 2026-09-25 | v3: Vocabulary, Articles and Sentences are separate decks, each with its own skill. |
| 2026-09-25 | v3: lesson records stay separate and attributable to course and lesson. |
| 2026-09-25 | v3: use every course's official online materials and record the exact source. |
| 2026-09-25 | v3: contexts are preferred but never forced; otherwise a bare, precise prompt. |
| 2026-09-25 | v3: merge only identical lemma + sense. |
| 2026-09-25 | v3: do not move, rename or delete existing folders, Markdown, legacy packages or PDFs. |
| 2026-09-25 | v3: no pending, authored or assumed context may ship. |
| 2026-09-25 | v3: the pronunciation deck stays untouched; no audio or TTS in the decks. |
| 2026-09-25 | v3: plan for A1, A2 and B1; build gradually, a lesson when the learner has studied it. |
| 2026-09-25 | v3: keep every useful link in `docs/`. |
| 2026-09-25 | D1: one cumulative system for all courses (`German A1 — …`), provenance in tags. |
| 2026-09-25 | D2: one capture file (`lesson-vocabulary.json`) grouped by course → lesson, plus curated card files. |
| 2026-09-25 | D3: captured = vocabulary lists in the notes, items written with a meaning, the official glossary; borderline items wait for a yes/no (widened 2026-09-27 and 2026-09-30). |
| 2026-09-25 | D4: proper names get Sentences cards on how the name is used (first name ↔ du/Tschüss; Herr/Frau + surname ↔ Sie). |
| 2026-09-25 | D5: fixed formulas in Vocabulary; patterns and grammatical choices in Sentences. |
| 2026-09-25 | D6 (open): VHS content behind the login; until decided, public PDFs only, portal items keep "your notes" provenance and bare cues. |
| 2026-09-25 | D7 (open): Easy German capture needs the official transcript or uploaded subtitles. |
| 2026-09-25 | D8: new versioned note types and GUIDs; delete the old decks in Anki before importing ([anki-import.md](anki-import.md)). |
| 2026-09-25 | Q1: lessons with empty notes are built when the learner studies them. |
| 2026-09-25 | Q2: "verstehr" captured as *verstehen* ("mostly yes"). |
| 2026-09-25 | Q4: legacy packages and duplicate PDFs are kept; deleting a clear duplicate needs the learner's go-ahead per file. |
| 2026-09-25 | Q5: Mac German-Standard keyboard; strict punctuation and capitals; typed answers use the keyboard apostrophe `'`. |
| 2026-09-25 | "Context" means a German context sentence; English cues and scenes are prompts written to match the source. |
| 2026-09-25 | An Articles card keys on lemma + gender (*der Mann*: one Articles card, separate Vocabulary cards for "man" and "husband"). |
| 2026-09-25 | With a context, the typed answer is exactly the blank; without one, the full expression with its punctuation (`Guten Abend.`). |
