# German Anki system: revised redesign plan (specific to this workspace)

- **Workspace:** `/Users/ramya/Documents/Deutsch lernen`
- **Date:** 2026-09-25
- **Status:** Proposal only. I have not changed, created, deleted, renamed or rebuilt anything in the workspace. I wrote only this file (in Downloads) and temporary text extracts in a session scratch folder.
- **Purpose:** For review by another model or person before anything is implemented.

---

## 0. Summary

The current system works mechanically. Packages validate, contain no audio, and use typed recall. But it has four kinds of problem:

1. **Data errors.** Two DW lesson URLs return 404, and the Tschüss URL in `sentence-sources.json` is also a 404. One card teaches a wrong meaning (`die Information`). One Articles card treats a plural-only noun as a gender item (`die Spaghetti`).
2. **Coverage gaps.** Three lessons have notes with vocabulary but are not in `lesson-vocabulary.json` at all: DW *Das ist Nico*, DW *Woher kommst du?* and VHS *Lektion 2*. Easy German has not been captured either. Several items in the notes are missing from lessons that were processed. The builders also silently drop names and placeholder fragments.
3. **Weak cards.** Some prompts are ambiguous (*Mama/Mutter*). Some cards give the answer away because the English and German words are the same (*hotel → Hotel*). Glosses got garbled when duplicate entries were merged. Some typed answers need punctuation or a typographic apostrophe to match. Some cues use grammar jargon. Some transcript lines were filed as "vocabulary".
4. **Engineering.** The builders are not deterministic: timestamps, sequential IDs and zip dates change on every run. They bootstrap the Anki schema by copying whichever `.apkg` sorts first. Three nearly identical builders exist. There are no checks for leakage, ambiguity, duplicates or coverage, and there are no tests.

The redesign has four parts:

- **Three decks, each with one clearly owned skill.** A single ownership matrix decides which deck tests what (§6.1).
- **Context used only where it earns its place.** A context must be a verified official sentence (DW script or exercise, VHS word list or film script, or Easy German's official transcript). Otherwise the card uses a bare but precise cue.
- **A coverage ledger.** Every captured entry must map to at least one card, so nothing is dropped. One card may cover two entries where separate cards would test the same recall.
- **An automated quality gate.** It checks leakage, ambiguity, duplicates, source verification and determinism, and a human reviews a preview before anything is packaged.

**Rough size after migration** (estimate, ±15%): about 310–330 captured entries, giving about 230–260 Vocabulary cards, 110–130 Articles cards and 70–90 Sentences cards. Today there are 128, 62 and 27.

**Needs your decision:** D1–D8 in §5. These are architectural choices, so I have not picked them silently. Each one has a recommendation.

---

## 1. Confirmed decisions I am applying

| Your decision | How the plan applies it |
|---|---|
| Existing Anki progress need not be preserved; rebuilding from scratch is fine. | Clean rebuild with new versioned note types and a new GUID namespace. Retire/suspend logic is dropped from the first build. |
| Never remove vocabulary captured from your lesson notes. No quotas. Do not skip easy entries, names or entries that are hard to put in context. Improve weak cards instead. | A coverage ledger fails the build if any captured entry has no card. Hard-coded exclusions are removed from the code (`include_entry` currently drops names, "…" fragments, *Brauchst du?* and *Willst du?*). |
| Do not merge Vocabulary, Articles and Sentences. | Each deck owns one skill (§6.1), enforced by cross-deck checks. |
| Keep notes and vocabulary records separate and attributable to course and lesson. | Lesson Markdown stays read-only. The capture record is restructured as course → lesson → entry, with per-entry provenance. Learner spellings are kept as `learnerForm`, next to the verified official form. |
| Research and use online materials for DW, VHS and Easy German, prefer official ones, and record the exact source. | See §7. I confirmed today which official sources exist and can be fetched (§2). |
| Context is preferred but never forced. Use a bare precise prompt when no good verified context exists. | Rule C6 plus a fallback card form in each deck. |
| Leave the pronunciation resource untouched. No audio or TTS. | The builder never scans the tree for `.apkg` files. A tripwire checks that the pronunciation files' SHA-256 hashes are unchanged after every build. The validator bans `[sound:`, `{{tts`, `<audio`, `<video` and `<img`, and requires an empty media map. |
| Inspect the actual workspace first. | Done (§2, §3). |

---

## 2. What I inspected

**Local files (all read in full unless noted):**

- `AGENTS.md`
- `ANKI/anki-card-design-reference.md`, `ANKI/README.md`
- `ANKI/lesson-vocabulary.json`: 6 DW lessons, 156 entries
- `ANKI/sentence-sources.json`: 27 cards
- `ANKI/build_vocabulary_decks.py`, `build_articles_deck.py`, `build_sentences_deck.py`, `anki_package_utils.py`, `download_nicos_weg_a1_materials.py`
- All three scan indexes
- Every `.apkg` in the tree, opened as SQLite (notes, cards, revlog, models, decks, media):
  - cumulative: Articles 62/62, Vocabulary 128/128, Sentences 27/27 (notes/cards), revlog 0 everywhere
  - 6 DW lesson decks
  - 2 legacy packages in `03_Tschüs/`
  - the pronunciation deck, whose media I inspected only as metadata
- Every lesson Markdown file: DW (8 with content, 1 empty), VHS (`Lesson_02/lektion_02.md`; the other folders are empty), Easy German (`01…Greetings&Farewells.md`; files 02–07 are empty)
- Text extracted from the official DW script/vocabulary PDFs for E0 L1–L4, E1 L1–L4, E2 L1–L4 and E3 L1–L4, plus the *Von A bis Z* teacher guide

**Online, checked today:**

- **DW course page** `https://learngerman.dw.com/en/nicos-weg/c-36519789`, which gives the official lesson IDs. DW lesson and exercise pages can be fetched, and their embedded data contains the exercise texts. Exercise sentences are **tagged with the glossary entry they practise**. Example: on `…/people-at-the-airport/l-37251054/e-37255866`, "Das ist Eva Zimmermann (26). Sie **studiert** im 8. Semester." is tagged with the entry "(etwas) studieren", and "Peter Stein (42) ist **Pilot** bei der Lufthansa…" is tagged with "Pilot, -en (m.)". This is an ideal official source of contexts.
- **VHS-Lernportal, public official PDFs:**
  - *Wortschatzlisten A1*: `https://www.vhs-lernportal.de/wws/bin/4007498-4014834-1-dvv_wortschatzlisten_a1.pdf`. Numbered per lesson, with articles and plurals. Lektion 2 is items 48–108.
  - *Filmskripte A1*: `https://www.vhs-lernportal.de/wws/bin/4007498-4014866-1-dvv_filmskripte_a1.pdf`. The *Nasrins Welt* scripts; Lektion 2 is about her family.
  - Teacher guide: `…4007242-4008330-1-vhs_lp_handreichung_deutsch_unterrichten_a1.pdf`. Covers Lektion 1 only.
  - The scenarios, exercises and vocabulary/phrase trainer inside the portal require a (free) login.
- **Easy German:** the episode in your notes is *Greetings & Farewells in Slow German | Super Easy German 274* (YouTube `aRlakaPVrEw`, posted March 2025). Full transcripts are a members' feature. The Markdown in your folder is an auto-generated transcript with recognition errors ("albd Schmidt", "usel", "vit die viert dich"), so it cannot be used as a verbatim source.

---

## 3. Findings (critique of the current rules, data and decks)

### 3.1 Data and sourcing errors

| # | Finding | Evidence |
|---|---|---|
| E1 | The Hallo URL is dead. | `lesson-vocabulary.json` has `…/hallo/l-37251017`, which returns 404. The course page gives `…/hallo/l-37250531`. |
| E2 | The *Nico hat ein Problem* URL is dead. | The JSON has `l-37262889` (404). The official ID is `l-37265543`. |
| E3 | The Tschüss URL in the sentence data is dead. | `sentence-sources.json` has `l-37251040` (404). `lesson-vocabulary.json` has the correct `l-37251033`. |
| E4 | The Tschüss entry has no `vocabularySourceUrl`. | The PDF is `static.dw.com/downloads/52718807/…e0-l3…`, already referenced in `sentence-sources.json`. |
| E5 | Wrong meaning. | The Vocabulary card asks "information → Information". The DW glossary says: *die Information – Kurzform von: der Informationsschalter, hier nur Singular*, i.e. the **information desk**. |
| E6 | A plural-only noun is taught as a gender item. | The Articles card "Spaghetti → die". The DW glossary says *die Spaghetti – nur Plural*. |
| E7 | Principal parts are missing or incomplete. | Your notes have *fliegen: fliegt, flog, ist geflogen*, but the JSON entry has no forms. *kommen* and *arbeiten* have only the Präsens (from your grammar table). The DW E1 L3 glossary gives *kommt, kam, ist gekommen*. |
| E8 | The *Kurzform* notes from the official glossaries are not captured. | Examples: *noch einmal → noch mal*, *Pass → Reisepass*, *Universität → Uni*, *Kaffee (nach Zahl: Kaffee)*, *Pizza alt. Pizzas*, *Uhr: in Uhrzeiten nur Singular*. These are useful corrective feedback for the back of the card. |

### 3.2 Coverage gaps (captured in notes, not in `lesson-vocabulary.json`)

| Lesson | In JSON? | Not yet captured (examples) |
|---|---|---|
| DW E0 L1 *Hallo!* | yes (27) | *danke sehr*; *Wie geht's? / Wie geht's dir?* (official variants and in your notes); **culture notes:** *Servus, Grüß Gott, Grüezi* (written "Grüyi"), *Moin*; *Na ja* (exercise). |
| DW E0 L2 *Kein Problem!* | yes (37) | Nothing from the list. The exercise texts (*Tennis, Fußball, Semester, wohnen*) are candidate contexts, not entries (D3). |
| DW E0 L3 *Tschüss!* | yes (27) | See E4. |
| DW E0 L4 *Von A bis Z* | yes (23) | Forms (E7, E8). Glossed acronyms from exercise 5/10: *LKW, PKW, AGB, USB, USA, DNA, DRK* (D3). |
| DW E1 L1 *Ich heiße Emma* | yes (17) | Grammar terms you wrote with articles: *das Personalpronomen, der Singular, der Plural* (D3). The possessive table is grammar and belongs to Sentences. |
| DW E1 L2 *Das ist Nico* | **no** | *helfen (hilft, half, hat geholfen), Keine Ahnung, der Kurs, die Sprache, der Taxifahrer, die Taxifahrerin, Sie ist Taxifahrerin, der Vorname, woher*. Glossed exercise items: *der Familienname, welche (which), der Sprachkurs*. Official glossary extras: *(das) Deutsch, er, in, lernen, sie, Er ist Taxifahrer*. |
| DW E1 L3 *Woher kommst du?* | **no** | About 25 items: *kommen, lernen, machen, der Sprachkurs, sprechen, der Tourist / die Touristin, was, wie, wir, wo, wohnen, Was machen Sie hier?, Was machst du hier?, Wo wohnen Sie?, Woher kommen Sie?* (your notes say "Wo kommen Sie?"), *Ich wohne in Sevilla*, and the terms *das Verb, die Konjugation, das Präsens*. |
| DW E1 L4 *Nico hat ein Problem* | yes (25) | *Welche Nummer hast du?* (exercise). |
| DW E2 L1 *Zahlen von 1 bis 100* | no | The notes file is **empty (0 bytes)**, so I would not process it until you study it (Q1). |
| VHS A1 *Lektion 2* | **no** | 15 family terms, numbers 0–20, 9 *Familienstand* terms, *Wie viele Kinder haben Sie?, Ich buchstabiere, Buchstabieren Sie das, Vielen Dank, Nachname, Familienname*, and "verstehr" (meaning unclear, Q2). Your number list skips **sechzehn**, which is in the official VHS list and is the irregular one (*sech-zehn*). |
| Easy German SEG 274 | **no** | The notes are a raw transcript with no explicit list (D7). |

Your notes contain typos that **must never reach a card**. The official spelling wins, and your form is kept only for provenance:

| In your notes | Official form |
|---|---|
| Sparchkurz / Sprachkurze | der Sprachkurs, die Sprachkurse |
| Trouristen | Touristen |
| sprecht (3rd person) | spricht |
| Grußeltern | Großeltern |
| Shon | Sohn |
| Getschwester | Geschwister |
| verpartener | verpartnert |
| heiß (past of heißen) | hieß |
| Fruende | Freunde |
| Heir ist | Hier ist |
| Mmas | Mamas |
| Wo kommen Sie? | Woher kommen Sie? |

**Observation:** your notes show y↔z swaps ("Kuryform", "Kreuy", "Grüyi"), which suggests you switch keyboard layouts. Typed Anki comparison is strict, so please check which layout you use while reviewing. Otherwise the cards will mark keyboard slips as knowledge errors.

### 3.3 Card-design problems (real cards from the current packages)

1. **Ambiguous prompts.** "mom; mother → Mama" and "mother → Mutter". Either answer fits the first prompt.
2. **Cognates that give the answer away.** About 15 of the 128 Vocabulary cards test only capitalisation: hotel/Hotel, taxi/Taxi, pizza/Pizza, computer/Computer, restaurant/Restaurant, museum/Museum, okay/okay, super/super, Hi!/Hi!, Hey!/Hey!, spaghetti/Spaghetti.
3. **Garbled merged glosses.** "please; here you go; please; if you please → bitte" and "downtown; city center; centre; center → Zentrum". The merge concatenates the glosses and does not split the separate senses.
4. **Friction in typed answers.** The answer fields contain terminal punctuation ("Guten Abend.", "Guten Morgen.", "Tschüss.") and the typographic apostrophe ("Mach’s gut!"). Typing "Guten Abend" or "Mach's gut" therefore shows as a mismatch.
5. **Jargon cues.** "in the — uncontracted dative form → in dem" and "into the — contraction of in das → ins" test terminology, not usage.
6. **Transcript lines filed as vocabulary.** "You are Emma → Du bist Emma.", "This is Nico → Das ist Nico.", "It is nine o'clock → Es ist neun Uhr." These are patterns, and their skill belongs in Sentences.
7. **Articles cards show no context, and the gender hints miss the most dependable A1 rules.** The existing suffix hints (‑ung, ‑tät, ‑um …) are correct. But there is no hint for:
   - the female-person suffix **‑in → always die** (Pilotin, Studentin, Freundin, Deutschlehrerin, Polizistin, Taxifahrerin, Touristin)
   - **compounds take the gender of their last part** (Fahrradgeschäft, Hausnummer, Supermarkt, Flughafen, Deutschlehrer)
   - **natural gender** (Mann, Frau, Vater, Mutter, Tante, Papa, Mama)
   
   Nor are there warnings for exceptions that trap learners: **der Name, der Buchstabe** end in ‑e but are masculine n-nouns, and **der Kaffee**.
8. **Captured items silently dropped.** For example, the Tschüss lesson deck has 19 cards for 27 entries. Martina, Herbert, *Brauchst du?*, *Wo ist …?* and *Willst du?* are dropped in code. *Mach’s gut*, *Gute Reise* and *Bis bald* are delegated to Sentences, which is fine. The dropped fragments come from real sentences in the script (*Brauchst du Hilfe?*, *Wohin willst du? / Willst du ins Zentrum?*), so they can be covered properly.
9. **Sentences is the strongest deck**, being curated, scene-cued and grammar-focused. Two weaknesses: the dividing line between "fixed expression in Vocabulary" and "fixed expression in Sentences" is fuzzy (*Guten Abend* is in Vocabulary but *Bis bald* is in Sentences), and completion cards have no scene. Keep most of these cards and improve them.

### 3.4 Engineering problems

| # | Problem | Why it matters |
|---|---|---|
| B1 | `time.time()` is used for note `mod`, model and deck IDs on initialisation, the index `updatedAt`, and zip timestamps. | Two runs never produce identical output, contrary to your determinism requirement. |
| B2 | Note IDs are sequential from 1 in **every** package: Articles 1–63, Vocabulary 1–146, Sentences 25–129. | The "Added" date shows 1970, and IDs collide across packages. *Assumption to test:* Anki's importer reassigns IDs on collision. Either way, hash-derived IDs in a realistic range avoid the issue. |
| B3 | The schema is bootstrapped by copying another package. `source_package()` takes the first sorted `.apkg` outside `ANKI/`, and the Articles builder needs `vocabulary.apkg`. | Hidden dependency: it could pick up the legacy or pronunciation package. |
| B4 | Three builders duplicate `package()`, `checksum()`, `initialise()` and the stale-note logic. | Changes drift apart. |
| B5 | `validate_package` checks integrity, orphans, counts and the audio ban only. | There are no checks for duplicates, ambiguity, leakage, coverage, cross-deck overlap or determinism. |
| B6 | Exclusions are hard-coded in code (`{"Brauchst du?", "Willst du?"}`, "(a name)"). | Editorial decisions are hidden in code. |
| B7 | There are no tests. | Changes to behaviour are unverified. |

### 3.5 Workspace housekeeping (report only; nothing will be touched without your approval)

- The notes for DW E1 L2 and E1 L3 are inside `Materials/`, but the rule says Markdown lives beside the lesson deck (Q3).
- The PDFs at the root of E1 L1 and E1 L4 are identical to the copies in their `Materials/` folders (`cmp` confirms).
- There are legacy packages in `03_Tschüs/`:
  - `Tschüs.apkg` (same content as `Tschüs_Vocabulary.apkg`)
  - `tschuess.apkg` (an old German→English recognition deck, 27 notes)
- The design reference says the *Kein Problem* deck is "German front, typed English answer". That is out of date.

---

## 4. Learning principles and the evidence behind them

| Principle | Evidence | Design consequence |
|---|---|---|
| **Recall beats recognition, especially for spelling and production.** | Nakata 2016 (IRAL 54(3)): recall formats beat recognition for productive knowledge of orthography. The Anki multiple-choice FAQ recommends direct questions. | All three decks stay typed-recall. No multiple choice. |
| **Spaced retrieval with feedback.** | Kim & Webb 2022, a meta-analysis of spacing in L2 learning (48 experiments). Karpicke & Roediger 2008. | Keep Anki scheduling (recommend FSRS, desired retention 0.90, per the Anki manual). The back always gives corrective feedback. |
| **A single context sentence adds little to learning meaning. Its value lies in knowing how the word is used.** | Webb 2007 (LTR 11(1)): a single glossed sentence had little effect on vocabulary knowledge compared with word pairs. Context helps with grammatical function and collocation. | Context is not a ritual. A context must teach something (collocation, case frame, register, typical situation); otherwise use a bare precise cue. This supports your decision "never force it". |
| **Similar items interfere when learned together.** | Tinkham 1993 and 1997, and Nation 2000 (TESOL Journal): semantic sets hinder learning. Wozniak's rule 11 ("combat interference"). | Disambiguating cues for near-synonyms and pairs. New cards are ordered so interfering pairs do not arrive on the same day. The contrast appears on the back. |
| **Gender is learned better when the noun comes with its article in larger units.** | Arnon & Ramscar 2012 (*Cognition* 122(3)): learning the noun before the sentence impairs learning of article–noun relations. | The Articles back always shows the full chunk (*die Tasche, die Taschen*). A nominative sentence slot is used where a real one exists. |
| **Explicit gender cues help novices.** | Presson, MacWhinney & Tokowicz 2014 (*Applied Psycholinguistics* 35(4)). Köpcke & Zubin 1984 set out semantic, morphological and phonological principles of gender assignment. | A pattern hint is shown **only** when it is dependable (‑in, ‑ung, ‑heit/‑keit, ‑chen, compound's last part, natural gender), and exceptions carry warnings. |
| **Minimum information, context cues, sources.** | Wozniak's *20 rules*: 4 (minimum information), 16 (context cues simplify wording), 17 (redundancy is compatible with minimum information), 18 (provide sources). | One target per card. Situational cues. Every card shows its source. Redundancy is allowed only when the retrieval is different. |
| **Practise the way you will use the language (transfer-appropriate processing).** | Morris, Bransford & Franks 1977. | Sentences uses micro-dialogue responses and register switches, not translation drills. |
| **One new element per sentence** (practitioner guidance from the sentence-mining community, not a controlled study). | Experienced-learner practice ("i+1"). | A known-word check flags context words you have not captured anywhere, so they can be replaced or glossed. |
| **Anki's own mechanics.** | Anki manual: typed comparison is exact and single-line; sibling burying applies only to cards of the **same note**. | Normalise typed answer fields. Cross-deck spacing has to come from content (distinct sentences) and new-card order, because Anki will not do it. |

---

## 5. Decisions I need from you (architecture)

### D1. Scope of the cumulative decks and their names
- **A (recommended).** One cumulative system for all courses, named "German A1 — Vocabulary / Articles / Sentences". Provenance is kept in tags (`course::dw`, `course::vhs`, `course::easy-german`, `lesson::<id>`), and exact repeats are merged. For example, *die Tante* appears in DW E0 L4 and VHS L2, but you should have one memory, so one card. This requires changing the rule in AGENTS.md that reserves the `DW A1 —` label.
- **B.** Keep the `DW A1 —` decks DW-only, and give VHS and Easy German lesson decks only. Their vocabulary then never gets long-term review.
- **C.** A separate cumulative trio per course. This duplicates cards for shared words (Hallo, Tschüss, Tante, Name, Familie, …), which violates "no two cards test the same recall".

### D2. Data layout
- **A (recommended).** Keep `ANKI/lesson-vocabulary.json` as the single, faithful capture record, restructured as course → lesson → entry with provenance. Add curated card files `ANKI/vocabulary-cards.json` and `ANKI/articles-cards.json` next to `sentence-sources.json`. What was captured stays separate from editorial choices.
- **B.** One capture file per course. This is cleaner, but conflicts with the file named in AGENTS.md and means more files.
- **C.** Contexts stored inline on entries. This is simpler, but mixes editorial choices with the capture record and makes one card covering several entries awkward.

### D3. What counts as "captured vocabulary"
- **A (recommended).** Three kinds of item count:
  1. every item in a vocabulary or *Wortschatz* list in your notes
  2. every item in your notes written with a gloss (e.g., "LKW … (truck)", "Welche (which)")
  3. the official lesson glossary of every lesson you have notes for
  
  Exercise sentences without a gloss are candidate contexts, not entries. In the migration diff, I will list every borderline item (acronyms, grammar terms) for your yes or no.
- **B.** Only items 1 and 3.
- **C.** Only item 1.

### D4. Proper names (Martina, Herbert, …)
- **A (recommended).** A "register-use" card in Sentences: the name is used in its authentic greeting or farewell (first name ↔ *Tschüss / du*; *Herr / Frau* + surname ↔ *Auf Wiedersehen / Sie*). The name itself has no lexical value. The useful knowledge it carries is how you address that person.
- **B.** A Vocabulary "scene recall" card with the name blanked out. This is trivia and transfers poorly, but it is possible.
- **C.** Lesson deck only.

In every case the card is tagged `type::name`, so one search can suspend them all.

### D5. Which deck owns whole-utterance entries
- **A (recommended).** An explicit rule with an override per entry:
  - An **unanalysed formula** (a greeting, farewell, thanks, apology, *Keine Ahnung*, *Kein Problem*) goes to **Vocabulary**, with a situational cue.
  - An utterance whose value is a **productive pattern or a grammatical choice** (du/Sie, verb form, W-question, *Ich komme aus …*, *Wo ist …?*, *Es ist … Uhr*) goes to **Sentences**.
  
  The coverage ledger guarantees nothing is lost.
- **B.** All utterances go to Sentences, and Vocabulary holds single words only.
- **C.** All utterances go to Vocabulary. This risks duplicate recall with Sentences.

### D6. Content behind the VHS login
- **A (recommended).** Use the public official PDFs as the main source. For items in your notes that come from inside the portal (*Schwiegereltern*, the *Familienstand* categories, *Wie viele Kinder haben Sie?*), either you paste or export the exercise text, or you authorise a **read-only** capture from your logged-in browser session (Claude in Chrome) that saves the exact sentences locally with their locator.
- **B.** Public PDFs only. Items from inside the portal keep "learner-notes" provenance and get bare cues until verified.

### D7. Easy German
- **A (recommended).** Verify against Easy German's official transcript if you have member access. If not, use the German subtitle track that Easy German uploaded (never the auto-captions). Extract the greetings and farewells that the episode explicitly teaches, about 25 (*Auf Wiederhören, Schönen Tag noch, Bis die Tage, Man sieht sich, Man hört sich, Moinsen, Habedere, Servus, Grüezi, Na?, GuMo …*). You confirm the list before it enters the JSON.
- **B.** Nothing enters until you mark the vocabulary yourself.

### D8. Reset procedure in Anki
- **A (recommended).** New versioned note types and a new GUID namespace. Before importing, you delete the old decks and note types in Anki. I will give exact steps.
- **B.** Keep the old GUIDs where the target is unchanged, so importing updates notes in place. There is little point without progress to preserve, and stale templates could linger.

---

## 6. Proposed rules

### 6.1 Ownership matrix (which deck tests what)

| Knowledge | Owner | Never *asked* in |
|---|---|---|
| Link between form and meaning for a word or an unanalysed formula (noun without article, infinitive, adjective, adverb, pronoun, particle, greeting) | **Vocabulary** | Articles, Sentences |
| Gender of a singular noun | **Articles** | Vocabulary (the article may be *visible* there but is never the answer), Sentences |
| Inflected verb forms, case forms, word order, register switching, responses, productive patterns, how names are used | **Sentences** | Vocabulary, Articles |
| Plurals, principal parts, *Kurzformen* | Shown on backs only (not tested) | — |

### 6.2 Vocabulary rules

- **V1. Target.** Exactly one lexical item or formula per card. The typed answer is the citation form: the noun without article, the infinitive without placeholders, the base adjective.
- **V2. Front.**
  - Optional **German context**: a verified sentence with the target replaced by `＿＿＿`.
  - A **required cue**: a precise English meaning or situation, plus a disambiguator when needed (register, region, "(woman)", "informal", "not X").
  - The instruction line: "Type the missing German word" or "Type the German".
- **V3. The slot must accept the citation form exactly.** A noun appears in the nominative (or in an unchanged accusative). An n-declension noun (Name, Buchstabe, Student, Pilot, Polizist, Tourist) appears **only** in the nominative. A verb appears only in an infinitive slot (after a modal, or in the wir/sie/Sie form where that equals the infinitive). If the source uses an inflected form, use a bare cue and show the sentence on the back as an example. The inflected form belongs to Sentences.
- **V4. One sense per card.** Polysemous captured items are split into senses with separate contexts: *bitte* ("please" vs "here you go"); *Frau* ("Ms", "woman", and VHS "wife"); *Mann* ("man", VHS "husband"); *das* ("that").
- **V5. Clean glosses.** Duplicated meanings are removed when entries merge. The official DW gloss is preferred.
- **V6. Cognates.** Where the English and German words are identical, cue the situation or function instead (e.g., the hotel in the taxi scene). If no good cue exists, accept an easy card. An easy card is better than a contrived one.
- **V7. Normalised typed answers.**
  - no terminal punctuation
  - ASCII apostrophe (`Mach's gut`)
  - case, umlauts and ß are kept, because they are part of the knowledge
  - never `type:nc`
  
  The back shows the canonical form ("Mach’s gut!") and accepted variants (*Tschüss / Tschüs*, *noch einmal / noch mal*).
- **V8. Back, in order:** canonical form (noun with article and plural; verb with principal parts and complement) → filled sentence plus translation → one useful note (contrast, *Kurzform*, "nur Plural", "hier nur Singular") → source.
- **V9. True synonyms** (*Familienname / Nachname*) get either a first-letter hint or "≠ the other one" on the front. The back names the other synonym.

### 6.3 Articles rules

- **A1. Answer.** Only `der`, `die` or `das`, typed in lowercase.
- **A2. Context slot.** The context may be used only when the blank sits in a **nominative singular slot with a definite article**: a subject, or a predicate nominative after *sein*. The following slots are forbidden:
  - accusative (`den` reveals masculine)
  - dative or genitive
  - contractions (im, am, zum, zur, ins)
  - plural slots
- **A3. No other gender marker for the target may appear on the front:**
  - ein/eine; possessives (mein/meine, sein/seine, Ihr/Ihre …); kein/keine
  - dies-, welch-
  - strong adjective endings
  - a pronoun referring back (er/sie/es, ihn), relative pronouns
  - the plural form
- **A4. Fallback when no leak-free German sentence exists.** Show the noun with an English gloss, optionally an English micro-scene ("Fahrradgeschäft: bicycle shop; Nico's aunt owns one"). There are no German determiners on the front at all.
- **A5. Back:** the full chunk (*die Tasche, die Taschen*) → the filled sentence → a pattern hint **only if dependable**, or an **exception warning** → source.
- **A6. Scope.** One card per singular noun that has an article. No card for:
  - plural-only nouns (*Spaghetti, Eltern, Großeltern, Geschwister, Schwiegereltern*)
  - forms of address (*Frau / Herr* + name)
  - country and language names used without an article (*Deutschland, Spanien, Deutsch*)
  
  These are covered in Vocabulary, and the reason is recorded in the ledger (`articles: plural-only`). Countries that *do* take an article (*die Türkei, der Irak*) do get cards if they are captured.

### 6.4 Sentences rules

- **S1. Card kinds.** All are typed, single line, one target:
  - **production:** English scene → a German utterance
  - **response:** a German line from someone in the scene → your reply
  - **completion:** one slot for a form, with the scene and lemma given
  - **register switch:** du → Sie, or the reverse
- **S2. What belongs here.** Every entry that D5 assigns to Sentences, plus curated extras that practise a **reusable** pattern or form the lesson actually makes useful.
- **S3.** A scene cue is required on every card, including completion cards.
- **S4. Learner errors.** Your own notes feed a "Not: …" line on the back (e.g., "Not: *Wo kommen Sie?* Origin needs *woher*."). A wrong form is never shown on the front.
- **S5. Variants.** Acceptable variants are shown on the back, with the instruction "grade by meaning and grammar; the capital on the first word and punctuation don't count". Typed comparison is only a guide for sentences.
- **S6.** No German→English mirrors, no multiple choice, and no drills of principal parts that the lesson does not use.

### 6.5 Lesson decks

- File: `<Markdown stem>_Vocabulary.apkg`, next to the lesson Markdown.
- Deck name:
  - DW: `DW — <Lesson> Vocabulary (typed)`, as now
  - VHS: `VHS A1 — Lektion 02 Vocabulary (typed)`
  - Easy German: `Easy German — SEG 274 Vocabulary (typed)`
- **Complete coverage** of that lesson's captured entries, using **the same card content** as the cumulative deck. This includes the few Sentences-type cards for utterance entries of that lesson, so the lesson deck is a full typed introduction and nothing is dropped. Articles cards stay in the cumulative deck only.
- See the disagreement about double reviewing in §15, item 4.

### 6.6 Quality gate (every card)

1. The target is covered in the ledger and source-backed, and the German context is verified against a local snapshot of the source.
2. One unambiguous expected answer, given the cue and the context.
3. Active recall, and no leakage (all automated checks in §8 pass, or the card carries a documented and reviewed exception).
4. The smallest natural unit.
5. No other card tests the same retrieval (§9).
6. The back gives concise corrective feedback, canonical form first.
7. The context earns its place (it teaches use, collocation, register or situation). Otherwise use a bare cue.

### 6.7 Per-lesson guidance (not quotas)

- **Vocabulary and Articles:** driven entirely by coverage. There is no cap and no minimum.
- **Sentences:** the cards required by coverage, plus 0–5 curated pattern or grammar extras per lesson, each passing the gate. Adding no extras is fine.
- Pacing is set in Anki's new-cards-per-day setting, not by limiting cards.

---

## 7. Sourcing contexts

### 7.1 Order of preference for sources

| Course | Order of preference (highest first) |
|---|---|
| **DW Nicos Weg** | (1) the script, i.e. the local PDF in `Materials/`; (2) **official exercise texts**, harvested from the lesson's exercise pages, where DW tags each sentence with the glossary entry it practises; (3) grammar pages; (4) teacher guides (*Von A bis Z* has one locally); (5) your notes, used only after checking them against 1–4 |
| **VHS A1** | (1) *Wortschatzlisten A1* (official, per lesson, with articles and plurals); (2) *Filmskripte A1* (*Nasrins Welt*); (3) the teacher guide (Lektion 1 only); (4) portal content behind the login, via D6; (5) your notes |
| **Easy German** | (1) the official transcript or Easy German's uploaded subtitles (D7); (2) your transcript note is only a pointer to the timestamp |

**Contexts may come from another course** when they are official and recorded. Examples:
- The VHS film line "Das sind meine Eltern, meine Mutter und mein Vater." can be the context for *Mutter*, which is also captured from DW.
- The VHS film line "Im Norden Deutschlands begrüßt man sich mit: Moin!" can be the context for *Moin*, which appears in your DW Hallo culture notes and in Easy German.

### 7.2 Selection criteria

- **C1.** Verbatim is preferred.
- **C2. Adaptation is limited to these operations:**
  - trimming
  - replacing a name with a noun or pronoun, or the reverse
  - changing a determiner to create a nominative definite slot (Articles only)
  - changing the person to reach the citation form
  
  Each adaptation is recorded as `adapted`, with the verbatim original, and the original must be found in the source snapshot.
- **C3.** At most about 12 words.
- **C4.** Every other content word has been captured somewhere, or is glossed on the front (the known-word check flags the rest).
- **C5.** The slot satisfies V3 (Vocabulary) or A2 (Articles).
- **C6.** The sentence teaches something: a collocation, case frame, register or typical situation. Otherwise use a bare cue.
- **C7.** Prefer situations you can reuse: airport, taxi, forms, family, phone calls, introductions.
- **C8.** A sentence appears on the **front** of at most one card across all decks (§9).

**English cues are ours; German contexts are the source's.** English situational cues may be written freely, but they must be precise and must never contain the German target, its stem or a compound containing it. German context text must always be official, verbatim or adapted as allowed in C2. This is how the plan avoids "awkward dictionary-example sentences".

### 7.3 Recording and verification

Every context stores:

- `de` and `en`
- `source`: course, lesson, kind (script / exercise / wordlist / film / transcript), URL, and a locator (PDF page, exercise ID, or video timestamp)
- `verbatim` or `adapted` (with the original)
- `verifiedOn`

A separate command, `harvest_sources.py`, is run by hand and uses the network. It saves snapshots into the lesson `Materials/` folders:
- DW: exercise JSON per studied lesson
- VHS: the PDFs, in `VHS-Lernportal/A1/Materials/`
- Easy German: the subtitle or transcript file

The build itself runs **offline**. A `verify-sources` step checks every context string, after normalising it, against these snapshots and fails on any mismatch.

---

## 8. Preventing answer leakage

### 8.1 Automated checks (the build fails unless a card has a reviewed exception with a reason)

| Check | Decks | Rule |
|---|---|---|
| Target echo | All | The answer tokens, their stem (a prefix of 4 or more characters) and any compound containing the target must not appear in the context, cue or instruction. This catches "Die Tasche? Welche ＿＿＿?", and a cue like "passport (short for Reisepass)", which leaks *Pass*. |
| Gender markers | Articles | A regex forbids `(ein|eine|einen|einem|einer|eines|mein…|dein…|sein…|ihr…|Ihr…|unser…|euer…|kein…|dies…|welch…) (+ optional adjective) <Noun>` on the front. The blank must come immediately before the noun. No contraction before the blank. |
| Plural visible | Articles | The plural form must not appear on the front. |
| Pronoun back-reference | Articles | Any er/sie/es/ihn/ihm/ihr in the same context is **flagged** for human confirmation. Coreference cannot be resolved automatically, so this check is honest about its limits. |
| Singular slot | Articles | Rejects contexts where the noun is followed by a plural verb (*sind*, …) or where the plural form is the target. |
| Citation-form slot | Vocabulary | The token in the context, once filled, must equal the answer. An n-noun must not follow `den/dem/des/einen/einem`. |
| Cognate flag | Vocabulary | If the cue word equals the answer, ignoring case and diacritics, the card is flagged, and a situational cue is required unless waived. |
| Cue collisions | Vocabulary | Normalised cues that overlap with different answers (*Mama/Mutter*, *Papa/Vater*, *Frau* ×3, *Hallo/Hi/Hey*, *Tschüss/Ciao*, *danke/danke schön/Vielen Dank*, *wo/woher/wohin*, *sie/Sie*, *Familienname/Nachname*) fail unless each card has a distinct disambiguator. |
| Punctuation and apostrophe | Vocabulary, Sentences | Typed answer fields must not end in `.!?` and must not contain `’`. |

### 8.2 Human preview (the checks cannot judge meaning)

Every build writes `ANKI/review/preview.html`, which renders the front and back of every card with flagged cards at the top. You or the reviewer approve it before packaging. Semantic ambiguity (another captured word also fits this blank and cue) is judged here, helped by a list of "same part of speech plus overlapping gloss" pairs.

---

## 9. Preventing redundancy across the three decks

1. **Ownership matrix (§6.1).** Each skill has one owner.
2. **Registry of front sentences.** The normalised German text on the front of every card is hashed. The same hash on two fronts fails the build, in any deck. The same sentence may be reused **on backs** as an example.
3. **Coverage ledger.** Each captured entry maps to one or more cards. One card may cover two entries where separate cards would require the same retrieval:
   - *Uhr* and *Es ist neun Uhr.* → one Sentences card
   - *Und Ihnen?* and the formal response → one response card
   
   The ledger shows these relationships, so they are auditable, and you can veto any of them.
4. **Target overlap.** The same normalised answer cannot be the target in Vocabulary and in Sentences, unless the Sentences target is a larger utterance that also requires something else (a form, register or pattern).
5. **Articles vs Vocabulary on the same noun.** Both cards exist by design because they test different skills. They must use **different** front sentences (rule 2). The Vocabulary card for a noun is placed earlier in the queue than its Articles card, which is approximate because the decks have separate queues.
6. **Ordering to avoid interference.** In the new-card queue, pairs flagged as interfering are placed at least about 15 positions apart: *Mama/Mutter*, *Freund/Freundin*, *Student/Studentin*, *Wie heißt du?/Wie heißen Sie?*, formal/informal twins. The contrast is taught on the back.

---

## 10. Before and after examples (real material)

Notation: `＿＿＿` marks the blank, → marks the typed answer, and ⟨…⟩ marks the source.

**1. Vocabulary: *Pass***
- **Before:** "passport — noun; type the German noun without its article" → Pass
- **After, front:** „Hat er Papiere? Einen Ausweis oder einen ＿＿＿?" · cue: *passport (travel document)*
- **After, back:** **der Pass, die Pässe** · *Kurzform von: Reisepass* · "Hat er Papiere? Einen Ausweis oder einen Pass?" – Does he have papers? An ID card or a passport? ⟨DW E1 L4 script⟩
- **Why:** a real scene with a useful collocation (*Papiere, Ausweis*). *Reisepass* moves to the back because on the front it would leak the answer.

**2. Vocabulary: *Mama* vs *Mutter* (ambiguity)**
- **Before:** "mom; mother" → Mama, and "mother" → Mutter
- **After (Mama), front:** „Nein, Lisa ist nicht meine ＿＿＿. Sie ist meine Tante." · cue: *mum/mom (informal, what a child says)* ⟨DW E0 L4 script⟩. Back: **die Mama, die Mamas** · neutral word: *die Mutter*.
- **After (Mutter), front:** „Das sind meine Eltern, meine ＿＿＿ und mein Vater." · cue: *mother (neutral word)* ⟨VHS A1 Lektion 2 film script; also DW E1 L4 glossary⟩. Back: **die Mutter, die Mütter** · informal: *die Mama*.
- The interference ordering keeps these two cards apart in the new queue.

**3. Vocabulary: *Information* (wrong meaning corrected; bare fallback)**
- **Before:** "information — noun…" → Information
- **After, front:** cue only: *the information desk (e.g., at the airport); short form, singular*
- **After, back:** **die Information** · *Kurzform von: der Informationsschalter; hier nur Singular* ⟨DW E0 L2 glossary⟩
- **Why:** no verified sentence exists in the script (the airport-symbols exercise only matches pictures to words), so the card uses the precise bare prompt.

**4. Vocabulary: *studieren* (verb; the context form is inflected, so bare cue plus example)**
- **Before:** "to study (at a college or university) — type the German infinitive"
- **After, front:** cue: *to study at a university (≠ lernen, to learn); infinitive*
- **After, back:** **studieren** – studiert, studierte, hat studiert · "Das ist Eva Zimmermann (26). Sie studiert im 8. Semester." ⟨DW E0 L2 exercise *People at the airport*, e-37255866⟩
- **Why:** the source form *studiert* is inflected, which is a Sentences skill, and Sentences already has "Eva ＿＿＿ im achten Semester." (V3 and §9 rule 4).

**5. Vocabulary: *Hotel* (cognate turned into a scene)**
- **Before:** "hotel" → Hotel
- **After, front:** „Ins Restaurant Königshof oder zum ＿＿＿ Königshof?" · cue: *the taxi driver asks where the businessman is going: to eat, or where he is staying?*
- **After, back:** **das Hotel, die Hotels** ⟨DW E0 L2 script⟩
- **Why:** it is still easy, but it is now a memorable scene from the video with a useful frame (*zum …*).

**6. Vocabulary: *bitte*, split into its two captured senses**
- **Before:** "please; here you go; please; if you please" → bitte
- **After, card 1, front:** „Moment ＿＿＿. Ich muss noch kurz tanken." · cue: *please (a polite request)* ⟨DW E1 L1 script⟩
- **After, card 2, front:** Emma hands something to Nico: „＿＿＿!" – Nico: „Danke." · cue: *here you go (handing something over)* ⟨DW E0 L4 script; what exactly she hands over is to be checked against the video before the cue is finalised⟩. Back: *Kurzform von: bitte schön*.

**7. Vocabulary: *Guten Abend* (typed-answer friction removed)**
- **Before:** the answer field "Guten Abend." (the period is required)
- **After, front:** cue: *early evening, it's getting dark: greet your neighbour (neutral/formal)*
- **After, back:** **Guten Abend!** · *Guten Morgen* (morning) / *Guten Tag* (daytime) ⟨DW E0 L1 glossary; Easy German SEG 274, "when it starts to get dark", timestamp to be verified against the official subtitles⟩
- The typed answer is `Guten Abend`.

**8. Vocabulary with an official German context from another course: *Moin*** (newly captured from your Hallo culture notes)
- **Front:** „Im Norden Deutschlands begrüßt man sich mit: ＿＿＿!" · cue: *northern German greeting, any time of day* ⟨VHS A1 Lektion 1 film script⟩
- **Back:** **Moin!** (also *Moin moin*, colloquial *Moinsen*) ⟨also Easy German SEG 274⟩

**9. Articles: *Tasche***
- **Before:** front "Tasche" → die
- **After, front:** „＿＿＿ Tasche ist nicht im Taxi." · (Tasche = bag) ⟨DW E1 L2 script, verbatim⟩
- **After, back:** **die Tasche, die Taschen** · Pattern: nouns in ‑e are *usually* die (see the exception *der Name*)
- **Leakage check:** nominative subject; *im Taxi* reveals Taxi's gender, not the target's. The Vocabulary card for *Tasche* uses a different sentence ("Hier ist die ＿＿＿ nicht.", from the same script). The Sentences card "Seine Tasche ist weg." is a third sentence.

**10. Articles: *Name* (exception, bare fallback)**
- **Before:** front "Name" → der
- **After, front:** "Name · (name, e.g., on a form)". No German sentence, because every source sentence has *mein / dein / Ihr*, which reveal "not feminine".
- **After, back:** **der Name, die Namen** · ⚠ ends in ‑e but is **der**; n-noun: *den Namen, des Namens* ⟨DW E0 L4 glossary; VHS L1 list⟩

**11. Articles: *Fahrradgeschäft* (compound rule, English micro-scene)**
- **Front:** "Fahrradgeschäft · (bicycle shop; Nico's aunt owns one)". The only source sentences use *ein* ("Die Frau hat ein Fahrradgeschäft."), which would reveal masculine or neuter.
- **Back:** **das Fahrradgeschäft, die Fahrradgeschäfte** · Compounds take the gender of the last part: *das Geschäft* ⟨DW E1 L4⟩

**12. Articles: *Schwester* (a real predicate-nominative context)**
- **Front:** „Mina ist ＿＿＿ Schwester von Arian." ⟨VHS A1 Lektion 2 film script, verbatim⟩
- **Back:** **die Schwester, die Schwestern** · natural gender

**13. Articles: *Spaghetti* (removed from Articles; still covered)**
- **Before:** "Spaghetti → die"
- **After:** no Articles card. The Vocabulary back says "*die Spaghetti*: plural only" ⟨DW E0 L2 glossary⟩, and the ledger records `articles: plural-only`.

**14. Sentences: response (covers *Und Ihnen?*)**
- **Front:** Frau Schneider: „Guten Morgen, Herr Müller, wie geht es Ihnen?" · cue: *you're fine: thank her and ask back (formal)*
- **Back:** **Danke, gut! Und Ihnen?** · informal equivalent: *Und dir?* ⟨DW E0 L1 script (audio course), verbatim⟩
- **Result:** the Vocabulary card "How about you? (formal) → Und Ihnen?" is replaced, and the ledger maps the entry to this card.

**15. Sentences: register switch plus your own error**
- **Front:** cue: *ask a stranger (formal) where they are from*
- **Back:** **Woher kommen Sie?** · informal: *Woher kommst du?* · Not: *Wo kommen Sie?* (origin needs *woher*) ⟨DW E1 L3 glossary; the error is from your notes⟩

**16. Names (D4 option A): *Martina*, currently dropped**
- **Front:** cue: *your friend Martina is flying off: say bye informally, using her first name, and wish her a good trip*
- **Back:** **Tschüss, Martina. Gute Reise!** · formal counterpart: *Auf Wiedersehen, Herr Tillmanns. Gute Reise!* ⟨DW E0 L3 script⟩
- **Covers:** *Martina* and *Gute Reise*. This replaces the separate generic "Gute Reise!" card to avoid overlap.

**17. VHS form context: *verwitwet*** (captured in your notes, beyond A1, kept)
- **Front:** cue: *on a German form, "Familienstand": your spouse has died*
- **Back:** **verwitwet** · other options on forms: *ledig, verheiratet, getrennt lebend, geschieden …*
- Tagged `level::beyond-a1`. The source is your notes from the portal, and the exact form wording is to be verified via D6.

---

## 11. Changes to the data model (sketch)

**`ANKI/lesson-vocabulary.json` (schema 3).** The file is restructured and nothing is removed. A migration check proves that every schema-2 entry maps to an entry in schema 3.

```json
{
  "schemaVersion": 3,
  "revision": "2026-10-01T12:00:00Z",
  "courses": [
    {
      "id": "dw-nicos-weg-a1",
      "title": "DW Nicos Weg A1",
      "courseUrl": "https://learngerman.dw.com/en/nicos-weg/c-36519789",
      "lessons": [
        {
          "id": "dw-nw-a1-e0-l1",
          "legacyId": "a1-hallo",
          "title": "Hallo!",
          "unit": 0,
          "lesson": 1,
          "url": "https://learngerman.dw.com/en/hallo/l-37250531/lv",
          "notesFile": "DW Deutsch lernen/A1/01_Intro_zu_A1/01_Hallo/Hallo.md",
          "sources": [
            {
              "kind": "script-vocabulary-pdf",
              "url": "https://static.dw.com/downloads/52718683/…e0-l1…pdf",
              "local": "…/Materials/Script and vocabulary (English).pdf"
            }
          ],
          "entries": [
            {
              "id": "frau-address",
              "german": "Frau",
              "english": "Ms/Mrs (form of address)",
              "pos": "noun-address",
              "origin": ["dw-glossary", "learner-notes"],
              "officialNote": "hier nur Singular, ohne Artikel"
            },
            {
              "id": "moin",
              "german": "Moin!",
              "english": "hello (northern Germany)",
              "origin": ["learner-notes"],
              "learnerForm": "Moin!"
            }
          ]
        }
      ]
    },
    { "id": "vhs-a1", "…": "…" },
    { "id": "easy-german", "…": "…" }
  ]
}
```

**`ANKI/vocabulary-cards.json` and `ANKI/articles-cards.json` (new, curated).** Each card record contains:
- `key` (stable)
- `covers: ["dw-nw-a1-e1-l4:pass"]`
- `cue`
- `context {de, en, source{…}, verbatim|adapted, original}`
- `answer`, `canonical`, `note`, `disambiguator`
- `interferesWith: [...]`
- `leakReview: {check, reason}`, optional and only for documented exceptions

If an entry has no curated record, the builder generates a **bare-cue card** from the cleaned entry, so coverage never depends on curation. A bare card is flagged "context candidate" in the preview.

**`ANKI/sentence-sources.json` (schema 3).** Adds `covers`, `scene`, `accept` (variants), `learnerError`, and course/lesson IDs. The Tschüss URL is fixed.

---

## 12. Files and decks

### Modify (after approval)

| File | Change |
|---|---|
| `AGENTS.md` | New deck rules: the ownership matrix, context and leakage rules, the coverage ledger, D1/D3/D5 outcomes, lesson-deck completeness, and scope across courses. |
| `ANKI/anki-card-design-reference.md` | Context card patterns, leakage rules and the Anki typed-answer notes. Fix the stale line about *Kein Problem*. |
| `ANKI/README.md` | New commands (`build_all.py`, `harvest_sources.py`), preview and validation. |
| `ANKI/lesson-vocabulary.json` | Schema 3: grouped by course, corrected URLs (E1–E4), provenance, forms (E7, E8). Add DW E1 L2 and E1 L3, VHS L2, and Easy German SEG 274 (after D7), plus the missing items in §3.2. |
| `ANKI/sentence-sources.json` | Schema 3. Revised and new cards. Fix the Tschüss URL. |
| `ANKI/build_vocabulary_decks.py`, `build_articles_deck.py`, `build_sentences_deck.py` | Rewritten as thin modules on a shared core. Deterministic. Coverage-driven. Lesson decks for all courses. |
| `ANKI/anki_package_utils.py` | Becomes the shared core: an embedded Anki schema (no copying of other packages), deterministic IDs, fixed zip timestamps, and the full validator. |
| `ANKI/articles-scan-index.json`, `vocabulary-scan-index.json`, `sentences-scan-index.json` | Regenerated with course, lesson, counts, coverage and flags. The wall-clock `updatedAt` is replaced by the data revision plus a content hash. |

### Create

| File | Purpose |
|---|---|
| `ANKI/vocabulary-cards.json`, `ANKI/articles-cards.json` | Curated cues and contexts. |
| `ANKI/build_all.py` | Single entry point: validate data → verify sources → build 3 cumulative decks and all lesson decks → cross-deck checks → preview → indexes → build again and compare hashes. |
| `ANKI/card_quality.py` | Leakage, ambiguity, duplicate, registry, coverage, known-word and interference-order checks. |
| `ANKI/harvest_sources.py` | Network step run by hand: verify URLs; snapshot DW exercises, the VHS PDFs and Easy German subtitles into the lesson `Materials/`. |
| `ANKI/tests/test_card_quality.py`, `ANKI/tests/test_determinism.py` | Standard-library `unittest` tests: leakage fixtures (including every "before" example above), coverage, and identical output from two builds. |
| `ANKI/review/preview.html` | Generated preview for human approval. |
| `VHS-Lernportal/A1/Materials/` | The official *Wortschatzlisten A1* and *Filmskripte A1* PDFs, plus a README with their URLs. |
| `VHS-Lernportal/A1/Lesson_02/lektion_02_Vocabulary.apkg` | The VHS lesson deck. |
| `EasyGerman/Materials/` and `EasyGerman/01LearnBasiGermanGreetings&Farewells_Vocabulary.apkg` | The Easy German source snapshot and lesson deck (after D7). |
| DW lesson decks for E1 L2 and E1 L3 | Their names depend on Q3 (where the notes files live). |
| DW `Materials/dw-exercises.json` snapshots | One per studied lesson. |

### Regenerate (overwrite)

- `ANKI/articles.apkg`, `ANKI/vocabulary.apkg`, `ANKI/sentences.apkg`
- DW lesson decks: `Hallo_Vocabulary`, `Kein_Problem_Vocabulary`, `Tschüs_Vocabulary`, `Von A bis Z_Vocabulary`, `Ich heiße Emma_Vocabulary`, `Nico hat Problem_Vocabulary`

### Untouched

- **The pronunciation resource:** `build_phonetic_alphabet_deck.py`, `phonetic-alphabet.json`, `Von A bis Z_Phonetic Alphabet_Pronunciation.apkg`, `Materials/README.md`. They are protected by a hash tripwire.
- **All lesson Markdown**: read-only; typos are corrected only in the JSON.
- The official PDFs, `_Vorlage - Nicos Weg A1.md`, the DW `README.md` and the manifest, and `download_nicos_weg_a1_materials.py`.

### Only with your explicit approval

- The legacy `Tschüs.apkg` and `tschuess.apkg`
- The duplicate root PDFs in E1 L1 and E1 L4
- Moving the E1 L2 and E1 L3 notes out of `Materials/` (Q3)

---

## 13. Anki identity, determinism and import

- **GUID:** `sha1("german-a1:v3:<deck>:<card key>")`, first 10 characters of the hex digest. Keys are stable slugs, so editing text keeps the GUID and only a change of target changes it.
- **Note and card IDs:** a base in epoch milliseconds plus a hash of the key. The validator fails on any collision across **all** managed packages.
- **`mod` times:** taken from the data `revision`, which is bumped when content changes. The build is deterministic, and it stays newer on re-import so updates are applied. The validator warns if the content hash changes without a revision bump.
- **SQLite:** built fresh from embedded DDL on every run (schema 11, the same as today), with rows inserted in sorted order and a `VACUUM` at the end. Identical output assumes the same SQLite version.
- **Zip:** sorted entries and a fixed `date_time` derived from the revision. Contents are `collection.anki2` and the media map `{}` only.
- **Requirement:** two builds in a row are byte-identical (compared with SHA-256).
- **Import (D8-A).** In Anki, delete the decks "DW A1 — Articles / Vocabulary / Sentences" and the old lesson decks, then delete the now unused note types under Tools → Manage Note Types, then import the new packages. Recommended settings: FSRS on, desired retention 0.90, and new cards per day chosen by you (about 10–15 across the three decks is a sensible start). This is a user action and I will not touch your Anki collection.
- **Retiring cards later:** once real progress exists after this reset, the previous rule returns: an obsolete card with review history is suspended and tagged, never deleted.

---

## 14. Validation and migration plan

| Phase | Work | Exit criterion |
|---|---|---|
| 0 | You decide D1–D8 and Q1–Q5. The reviewer approves the plan. | Written approval. |
| 1 | **Source capture** (network): verify every URL; save DW exercise snapshots for the 8 studied lessons; download the VHS PDFs into `VHS-Lernportal/A1/Materials/`; capture Easy German per D7 and VHS portal content per D6. | Every source in the JSON has a working URL and a local snapshot. |
| 2 | **Data migration** to schema 3: grouping by course, IDs, corrections, additions. Produce a **diff report** listing every entry added or changed, its provenance, and the borderline items from D3. | Every schema-2 entry is mapped (no removals). You approve the borderline list. |
| 3 | **Curation**: write the card files and the revised sentence sources. Run the linter. Generate the preview. | Zero unwaived check failures. Preview approved by you or the reviewer. |
| 4 | **Rewrite the builders** plus tests. | `unittest` passes, including fixtures for leakage, coverage and determinism. |
| 5 | **Build and validate everything.** | All checks in §8 and below pass. Two builds match byte for byte. The pronunciation tripwire is unchanged. |
| 6 | **Documentation**: update AGENTS.md, README and the design reference. | Rules match the builders' behaviour. |
| 7 | **Smoke test on your devices**: import into Anki desktop and phone, check the typing box, umlaut entry, and a few cards per deck. | Your go-ahead. |

**Validation checks run on every package:**

1. SQLite `integrity_check` = ok. No orphan cards. Notes = cards (one card per note). Deck and note-type names as expected.
2. Media map empty, and the zip contains only `collection.anki2` and `media`. No `[sound:`, `{{tts`, `tts-voices`, `<audio`, `<video` or `<img` in templates or fields.
3. Exactly one `{{type:…}}` per template. No empty fronts.
4. GUID and ID uniqueness across all managed packages.
5. Duplicate prompts: identical normalised fronts in any deck fail the build. Near-duplicates (token Jaccard ≥ 0.8) are flagged.
6. Ambiguous prompts: cue collisions (§8) fail unless disambiguated. Semantic pairs are listed for the preview.
7. Answer leakage: every check in §8.1.
8. Coverage ledger complete. Every Articles exemption has a reason code.
9. Every German context is verified against a local snapshot of its source.
10. Front-sentence registry is unique. The rules on overlapping targets (§9) hold.
11. Determinism, and the pronunciation-file tripwire.

---

## 15. Where I disagree or push back

1. **"Articles as a blank in a sentence" is often worse than a bare noun.** German case means most natural sentences put the noun in the accusative or dative, or behind a possessive or *ein*. Every one of these reveals or distorts gender. Only a nominative slot with a definite article works, and forcing one produces stilted "Der X ist …" sentences. So Articles uses a real nominative sentence when one exists, and otherwise a noun with an English micro-scene (no German determiners). The real leverage of this deck is on the **back**: the full chunk, a dependable rule, and exception warnings.
2. **Evidence does not support "context first" for learning meaning** (Webb 2007). Context should earn its place by teaching use. Several of your current internationalisms will stay easy cards. A contrived cue is worse than an easy card.
3. **Mechanical one-card-per-entry would create duplicates.** Where two captured entries require the same retrieval (*Uhr* and *Es ist neun Uhr.*; *Und Ihnen?* and the formal response), one card covers both, visibly, in the ledger. Nothing is removed, and you can veto each case.
4. **Lesson decks double your reviews.** The same knowledge gets scheduled twice when you also study the cumulative decks. I will keep generating them as the rule requires. But I recommend either using them only for the first pass and then deleting them from Anki, or skipping them and creating an Anki filtered deck from the cumulative decks with `tag:lesson::<id>`, which gives one set of notes and no double scheduling. If you prefer the second option, the lesson-deck rule could become optional.
5. **Names have no lexical content.** A card asking you to recall "Martina" is trivia. The useful knowledge in a name is how you address the person, hence D4-A.
6. **Typed comparison is too strict for sentences.** For Sentences it is a guide, and grading should follow meaning and grammar (S5). For single words it stays strict on purpose, because umlauts and capitals matter.
7. **Some captured items are beyond A1** (*eingetragene Lebenspartnerschaft aufgehoben*). They stay, per your decision, cued by the context of a form and tagged `level::beyond-a1` so you can filter them. I would not build extra cards around them.
8. **The Easy German note cannot be used as a text source.** It is an auto-transcript with recognition errors. Only the official transcript or subtitles can supply German contexts.

---

## 16. Open questions

- **Q1.** Should lessons whose notes file is empty or missing be processed? This covers DW E2 L1 *Zahlen* (0 bytes), Easy German 02–07 (empty) and VHS Lektionen 1 and 3–7 (empty folders). I recommend no, not until you study them.
- **Q2.** What did you mean by "verstehr" in the VHS L2 notes? Possibly *verstehen* or *Ich verstehe*.
- **Q3.** May I move `Das ist Nico.md` and `Woher komst du.md` from `Materials/` up into their lesson folders, where the rule says Markdown belongs? And may I correct the filename typo "komst"? The lesson deck names follow from this.
- **Q4.** Should the legacy `Tschüs.apkg` and `tschuess.apkg` and the duplicate root PDFs stay as they are? The default is to keep them.
- **Q5.** Which keyboard layout do you use for typed answers? See §3.2.
- **Q6 (reviewer).** Are the adaptation operations in C2 tight enough? Is the known-word check too strict for contexts from another course?

---

## 17. Sources

**Official course materials**
- DW Nicos Weg course page (lesson IDs): https://learngerman.dw.com/en/nicos-weg/c-36519789
- DW Tschüss vocabulary page (correct ID): https://learngerman.dw.com/en/tsch%C3%BCss/l-37251033/lv
- DW exercise with tagged vocabulary sentences: https://learngerman.dw.com/en/people-at-the-airport/l-37251054/e-37255866
- DW script and vocabulary PDFs: the local copies in each lesson's `Materials/` (URLs in `a1-script-vocabulary-manifest.json`)
- VHS *Wortschatzlisten A1*: https://www.vhs-lernportal.de/wws/bin/4007498-4014834-1-dvv_wortschatzlisten_a1.pdf
- VHS *Filmskripte A1*: https://www.vhs-lernportal.de/wws/bin/4007498-4014866-1-dvv_filmskripte_a1.pdf
- VHS teacher guide A1 (Lektion 1): https://www.vhs-lernportal.de/wws/bin/4007242-4008330-1-vhs_lp_handreichung_deutsch_unterrichten_a1.pdf
- VHS course information sheet: https://www.vhs-lernportal.de/wws/bin/4007242-4008322-1-infoblatt_a1-b1.pdf
- Easy German, *Greetings & Farewells in Slow German | Super Easy German 274*: https://www.youtube.com/watch?v=aRlakaPVrEw

**Anki**
- Anki manual, deck options (FSRS, desired retention, sibling burying): https://docs.ankiweb.net/deck-options.html
- Anki manual, field replacements (typed answers): https://docs.ankiweb.net/templates/fields.html
- Anki FAQ, multiple choice: https://faqs.ankiweb.net/multiple-choice-questions.html
- Wozniak, *Effective learning: Twenty rules of formulating knowledge*: https://super-memory.com/articles/20rules.htm

**Research** (verified to exist in this session unless marked)
- Webb, S. (2007). Learning word pairs and glossed sentences: the effects of a single context on vocabulary knowledge. *Language Teaching Research* 11(1), 63–81. https://journals.sagepub.com/doi/10.1177/1362168806072463
- Nakata, T. (2016). Effects of retrieval formats on second language vocabulary learning. *IRAL* 54(3), 257–289. https://www.degruyterbrill.com/document/doi/10.1515/iral-2015-0022/html
- Kim, S. K. & Webb, S. (2022). The effects of spaced practice on second language learning: A meta-analysis. *Language Learning*. https://onlinelibrary.wiley.com/doi/abs/10.1111/lang.12479
- Arnon, I. & Ramscar, M. (2012). Granularity and the acquisition of grammatical gender. *Cognition* 122(3), 292–305. https://www.sciencedirect.com/science/article/abs/pii/S001002771100254X
- Presson, N., MacWhinney, B. & Tokowicz, N. (2014). Learning grammatical gender: The use of rules by novice learners. *Applied Psycholinguistics* 35(4), 709–737. https://www.cambridge.org/core/journals/applied-psycholinguistics/article/abs/learning-grammatical-gender-the-use-of-rules-by-novice-learners/5C9F7E93A0F74030C1F04280746745EA
- Köpcke, K.-M. & Zubin, D. (1984). Sechs Prinzipien für die Genuszuweisung im Deutschen. *Linguistische Berichte* 93, 26–50. (Later overview: https://ids-pub.bsz-bw.de/files/8944/Koepcke_Zubin_Prinzipien_fuer_die_Genuszuweisung_im_Deutschen_1996.pdf)
- Nation, I. S. P. (2000). Learning vocabulary in lexical sets: Dangers and guidelines. *TESOL Journal* 9, 6–10. https://onlinelibrary.wiley.com/doi/10.1002/j.1949-3533.2000.tb00239.x (also Tinkham 1993, 1997)
- Karpicke, J. D. & Roediger, H. L. (2008). The critical importance of retrieval for learning. *Science* 319. *(Not re-verified this session; a standard reference.)*
- Morris, C. D., Bransford, J. D. & Franks, J. J. (1977). Levels of processing versus transfer appropriate processing. *JVLVB* 16. *(Not re-verified this session; a standard reference.)*
