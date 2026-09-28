# Every useful link (verified 2026-09-25)

Every link here was opened and checked on 2026-09-25, unless marked otherwise.
For any lesson question, start with the lesson index in
[`course-index/`](course-index/): it has every lesson's title, goal, grammar
topic, lesson page and script PDF for DW A1–B1, and the topics and grammar
of every VHS A1–B1 lesson.

## DW Learn German — Nicos Weg (Deutsche Welle)

| What | Link | Notes |
|---|---|---|
| Nicos Weg A1 (English interface) | <https://learngerman.dw.com/en/nicos-weg/c-36519789> | 76 lessons + final test. Index: [dw-nicos-weg-a1.md](course-index/dw-nicos-weg-a1.md) |
| Nicos Weg A2 (English interface) | <https://learngerman.dw.com/en/nicos-weg/c-36519797> | 76 lessons + final test. Index: [dw-nicos-weg-a2.md](course-index/dw-nicos-weg-a2.md) |
| Nicos Weg B1 (German interface only) | <https://learngerman.dw.com/de/nicos-weg/c-36519718> | There is no English B1 course page; the B1 scripts are German-only. Index: [dw-nicos-weg-b1.md](course-index/dw-nicos-weg-b1.md) |
| Nicos Weg A1/A2 in the German interface | A1 <https://learngerman.dw.com/de/nicos-weg/c-36519687> · A2 <https://learngerman.dw.com/de/nicos-weg/c-36519709> | From the German course sitemap |
| Course sitemaps | <https://learngerman.dw.com/en/course-sitemap.xml> · <https://learngerman.dw.com/de/course-sitemap.xml> | Lists the official course IDs |
| Grammar overview (all levels) | <https://learngerman.dw.com/en/grammar> | |
| Vocabulary overview | <https://learngerman.dw.com/en/vocabulary> | |
| DW vocabulary trainer | <https://learngerman.dw.com/en/user/vocabularyTrainerStart> | Needs a free DW account |
| Placement test | <https://learngerman.dw.com/en/placementDashboard> · <https://learngerman.dw.com/en/placement-test/c-36519788> · German: <https://learngerman.dw.com/de/einstufungstest/c-36519653> | |
| List of all script/vocabulary PDFs (A1, A2 English; B1 German) | <https://gist.githubusercontent.com/eduardvasilache/8d88ae7b549cc34a201bd8fc52520307/raw/50fdaa32e0ae6e6769973d5ae069001eeba4d90d/dw-scripts-nico-a1-a2-b1.txt> | Community list of official `static.dw.com` URLs; each PDF link points to DW itself |
| Example A2 script PDF | <https://learngerman.dw.com/downloads/52723388/nicos-weg-a2-e0-l1-manuskript-und-wortschatz-englisch.pdf> | |
| Example B1 script PDF (German) | <https://learngerman.dw.com/downloads/53486820/nicos-weg-b1-e0-l1-manuskript-und-wortschatz-deutsch.pdf> | |
| Teacher guide + exercises, *Von A bis Z* | <https://static.dw.com/downloads/52719092/nicos-weg-a1-e0-l4-lehrerhandreichung-und-uebungen.pdf> | Saved in that lesson's `Materials/` |

How DW pages are built (useful for tooling): lesson pages end in `/l-<id>`.
Each lesson has a vocabulary page (`/l-<id>/lv`), exercise pages (`/e-<id>`),
grammar pages (`/gr-<id>`) and culture pages (`/rs-<id>`). Their data sits in
`window.__APOLLO_STATE__`. On the vocabulary page, the lesson's `vocabularies`
list points to `Knowledge` records: `name` (German), `text` (official English),
`subTitle` (plural note or principal parts); checked 2026-09-27. Exercise
sentences are tagged with the glossary entry they practise, so the official exercises are
the best context source. Correct answers are marked with `isCorrect`. DW's
server returns HTTP 200 even for wrong lesson IDs, so check the page content,
not the status code.

## Lessons you have studied (DW A1, VHS A1)

### DW Nicos Weg A1 · Hallo! (E0 L1)
- Lesson page: <https://learngerman.dw.com/en/hallo/l-37250531> · notes: `DW Deutsch lernen/A1/01_Intro_zu_A1/01_Hallo/Hallo.md`
- Culture: [Greetings in German](https://learngerman.dw.com/en/greetings-in-german/l-37250531/rs-39370662) (lists Servus, Grüß Gott, Grüezi, Moin)
- Grammar: [Informal and formal (1)](https://learngerman.dw.com/en/informal-and-formal-1/l-37250531/gr-38310488)
- Exercises (12), e.g. [Asking people how they're doing](https://learngerman.dw.com/en/asking-people-how-theyre-doing/l-37250531/e-37252406)
- Script and vocabulary PDF: <https://static.dw.com/downloads/52718683/nicos-weg-a1-e0-l1-manuskript-und-wortschatz-englisch.pdf>

### DW Nicos Weg A1 · Kein Problem! (E0 L2)
- Lesson page: <https://learngerman.dw.com/en/kein-problem/l-37251054> · notes: `DW Deutsch lernen/A1/01_Intro_zu_A1/02_Kein Problem/Kein_Problem.md`
- Culture: [International words in German](https://learngerman.dw.com/en/international-words-in-german/l-37251054/rs-39370824)
- Exercises (12), e.g. [People at the airport](https://learngerman.dw.com/en/people-at-the-airport/l-37251054/e-37255866) (Eva Zimmermann, Peter Stein)
- Script and vocabulary PDF: <https://static.dw.com/downloads/52719054/nicos-weg-a1-e0-l2-manuskript-und-wortschatz-englisch.pdf>

### DW Nicos Weg A1 · Tschüss! (E0 L3)
- Lesson page: <https://learngerman.dw.com/en/tschüss/l-37251033> · notes: `DW Deutsch lernen/A1/01_Intro_zu_A1/03_Tschüs/Tschüs.md`
- Grammar: [Informal and formal (2)](https://learngerman.dw.com/en/informal-and-formal-2/l-37251033/gr-38310645)
- Culture: [Saying goodbye](https://learngerman.dw.com/en/saying-goodbye/l-37251033/rs-39371009)
- Exercises (12), e.g. [And how are you? (1)](https://learngerman.dw.com/en/and-how-are-you-1/l-37251033/e-37255725)
- Script and vocabulary PDF: <https://static.dw.com/downloads/52719087/nicos-weg-a1-e0-l3-manuskript-und-wortschatz-englisch.pdf>

### DW Nicos Weg A1 · Von A bis Z (E0 L4)
- Lesson page: <https://learngerman.dw.com/en/von-a-bis-z/l-37256418> · notes: `DW Deutsch lernen/A1/01_Intro_zu_A1/04_Von A bis Z/Von A bis Z.md`
- Culture: [How's it going?](https://learngerman.dw.com/en/hows-it-going/l-37256418/rs-40965828) · [The phonetic alphabet](https://learngerman.dw.com/en/the-phonetic-alphabet/l-37256418/rs-39371795)
- Exercises (10), e.g. [Here are Nico, Emma, and Lisa](https://learngerman.dw.com/en/here-are-nico-emma-and-lisa/l-37256418/e-37262583)
- Script and vocabulary PDF: <https://static.dw.com/downloads/52719090/nicos-weg-a1-e0-l4-manuskript-und-wortschatz-englisch.pdf>

### DW Nicos Weg A1 · Ich heiße Emma (E1 L1)
- Lesson page: <https://learngerman.dw.com/en/ich-heiße-emma/l-37262882> · notes: `DW Deutsch lernen/A1/02_meeting_people/01_Lesson_01/Ich heiße Emma.md`
- Culture: [Meeting Germans](https://learngerman.dw.com/en/meeting-germans/l-37262882/rs-39370848)
- Grammar: [Personal pronouns: ich, du](https://learngerman.dw.com/en/personal-pronouns-ich-du/l-37262882/gr-38320451) · [Personal pronouns: Sie](https://learngerman.dw.com/en/personal-pronouns-sie/l-37262882/gr-38320692)
- Exercises (9), e.g. [Asking what someone is called](https://learngerman.dw.com/en/asking-what-someone-is-called/l-37262882/e-43702442)
- Script and vocabulary PDF: <https://static.dw.com/downloads/52719106/nicos-weg-a1-e1-l1-manuskript-und-wortschatz-englisch.pdf>

### DW Nicos Weg A1 · Das ist Nico (E1 L2)
- Lesson page: <https://learngerman.dw.com/en/das-ist-nico/l-37262923> · notes: `DW Deutsch lernen/A1/02_meeting_people/02_Lesson_02/Das ist Nico.md`
- Culture: [And what's your name?](https://learngerman.dw.com/en/and-whats-your-name/l-37262923/rs-39371008)
- Exercises (8), e.g. [Here are Nico and Emma](https://learngerman.dw.com/en/here-are-nico-and-emma/l-37262923/e-37264626)
- Script and vocabulary PDF: <https://static.dw.com/downloads/52719126/nicos-weg-a1-e1-l2-manuskript-und-wortschatz-englisch.pdf>

### DW Nicos Weg A1 · Woher kommst du? (E1 L3)
- Lesson page: <https://learngerman.dw.com/en/woher-kommst-du/l-37263828> · notes: `DW Deutsch lernen/A1/02_meeting_people/03_Lesson_03/Woher komst du.md`
- Grammar: [Conjugation: present tense (1)](https://learngerman.dw.com/en/conjugation-present-tense-1/l-37263828/gr-38320838)
- Culture: [My name is Müller](https://learngerman.dw.com/en/my-name-is-müller/l-37263828/rs-39371127) · [Name changes after marriage](https://learngerman.dw.com/en/name-changes-after-marriage/l-37263828/rs-40965959)
- Exercises (12), e.g. [How, where, from where or what?](https://learngerman.dw.com/en/how-where-from-where-or-what/l-37263828/e-37268049)
- Script and vocabulary PDF: <https://static.dw.com/downloads/52719129/nicos-weg-a1-e1-l3-manuskript-und-wortschatz-englisch.pdf>

### DW Nicos Weg A1 · Nico hat ein Problem (E1 L4)
- Lesson page: <https://learngerman.dw.com/en/nico-hat-ein-problem/l-37265543> · notes: `DW Deutsch lernen/A1/02_meeting_people/04_Lesson_04/Nico hat Problem.md`
- Culture: [Communication at offices and agencies](https://learngerman.dw.com/en/communication-at-offices-and-agencies/l-37265543/rs-39371132)
- Grammar: [Conjugation: haben](https://learngerman.dw.com/en/conjugation-haben/l-37265543/gr-38310825) · [Conjugation: present tense (2)](https://learngerman.dw.com/en/conjugation-present-tense-2/l-37265543/gr-38321810) · [Personal pronouns: er, sie](https://learngerman.dw.com/en/personal-pronouns-er-sie/l-37265543/gr-38320906) · [Personal pronouns: plural](https://learngerman.dw.com/en/personal-pronouns-plural/l-37265543/gr-38321282)
- Exercises (11), e.g. [A call for Lisa](https://learngerman.dw.com/en/a-call-for-lisa/l-37265543/e-37266248)
- Script and vocabulary PDF: <https://static.dw.com/downloads/52719209/nicos-weg-a1-e1-l4-manuskript-und-wortschatz-englisch.pdf>

### DW Nicos Weg A1 · Zahlen von 1 bis 100 (E2 L1)
- Lesson page: <https://learngerman.dw.com/en/zahlen-von-1-bis-100/l-37265621> · notes: `DW Deutsch lernen/A1/03_contact_details/01_Lesson_01/Zahlen von 1 bis 100.md`
- Grammar: [Numbers from 11 to 19](https://learngerman.dw.com/en/numbers-from-11-to-19/l-37265621/gr-38307006) · [Numbers from 20 to 100](https://learngerman.dw.com/en/numbers-from-20-to-100/l-37265621/gr-38307981)
- Culture: [Happy Birthday!](https://learngerman.dw.com/en/happy-birthday/l-37265621/rs-39370325) · [Celebrating birthdays in the office](https://learngerman.dw.com/en/celebrating-birthdays-in-the-office/l-37265621/rs-40966362)
- Exercises (14), e.g. [An invitation](https://learngerman.dw.com/en/an-invitation/l-37265621/e-37271074)
- Script and vocabulary PDF: <https://static.dw.com/downloads/52719212/nicos-weg-a1-e2-l1-manuskript-und-wortschatz-englisch.pdf>

### DW Nicos Weg A1 · Wichtige Nummern (E2 L2) · checked 2026-09-27
- Lesson page: <https://learngerman.dw.com/en/wichtige-nummern/l-37269501> · notes: `DW Deutsch lernen/A1/03_contact_details/02_Lesson_02/Wichtige Nummern.md`
- Culture: [Lost and found](https://learngerman.dw.com/en/lost-and-found/l-37269501/rs-39370411)
- Exercises (12), e.g. [Understanding phone numbers (1)](https://learngerman.dw.com/en/understanding-phone-numbers-1/l-37269501/e-37272723)
- Script and vocabulary PDF: <https://static.dw.com/downloads/52719221/nicos-weg-a1-e2-l2-manuskript-und-wortschatz-englisch.pdf>

### VHS A1 · Lektion 2 (Meine Familie und ich)
- Vocabulary trainer with English, inside the portal: *Mein A1 → Vokabeltrainer → Lektion 2 → English* (captured 2026-09-25 into `VHS-Lernportal/A1/Materials/source-snapshot.json`)
- Portal (login): <https://a1.vhs-lernportal.de/> · notes: `VHS-Lernportal/A1/Lesson_02/lektion_02.md`
- Word list (items 48–108): see VHS below · Film script *Nasrins Welt*, Lektion 2 (Familie) · Topics/grammar: [vhs-a1.md](course-index/vhs-a1.md#lektion-2--meine-familie-und-ich)
- Film on YouTube: [Nasrins Welt A1 Lektion 02 Familie](https://www.youtube.com/watch?v=Q9h34NLMiZ0)

Full exercise lists and the text of every snapshot are in each lesson's
`Materials/source-snapshot.json`.

## VHS-Lernportal (Deutscher Volkshochschul-Verband, DVV)

| What | Link |
|---|---|
| Course portals (free login) | A1 <https://a1.vhs-lernportal.de/> · A2 <https://a2.vhs-lernportal.de/> · B1 <https://b1.vhs-lernportal.de/> |
| Topics and grammar per lesson (*Themen und Grammatik*) | A1 <https://www.vhs-lernportal.de/wws/bin/4007530-4015506-1-dvv_grammatiklisten_a1.pdf> · A2 <https://www.vhs-lernportal.de/wws/bin/4007530-4015506-2-dvv_grammatiklisten_a2.pdf> · B1 <https://www.vhs-lernportal.de/wws/bin/4007530-4015506-3-dvv_grammatiklisten_b1.pdf> |
| Word lists per lesson (with articles and plurals) | A1 <https://www.vhs-lernportal.de/wws/bin/4007498-4014834-1-dvv_wortschatzlisten_a1.pdf> · A2 <https://www.vhs-lernportal.de/wws/bin/4007498-4014834-2-dvv_wortschatzlisten_a2.pdf> · B1 <https://www.vhs-lernportal.de/wws/bin/4007498-4014834-3-dvv_wortschatzlisten_b1.pdf> |
| Film scripts (*Nasrins Welt*) | A1 <https://www.vhs-lernportal.de/wws/bin/4007498-4014866-1-dvv_filmskripte_a1.pdf> · A2 <https://www.vhs-lernportal.de/wws/bin/4007498-4014866-2-dvv_filmskripte_a2.pdf> · B1 <https://www.vhs-lernportal.de/wws/bin/4007498-4014866-3-dvv_filmskripte_b1.pdf> |
| Teaching materials page | <https://www.vhs-lernportal.de/wws/unterrichtsmaterial.php> |
| Teacher guides | A1 Lektion 1: <https://www.vhs-lernportal.de/wws/bin/4007242-4008330-1-vhs_lp_handreichung_deutsch_unterrichten_a1.pdf> · Overview: <https://www.vhs-lernportal.de/wws/anleitungen-und-handreichungen.php> · DaZ guide: <https://www.vhs-lernportal.de/wws/bin/4007530-4015202-1-dvv_hr_daz_web.pdf> · "Deutsch unterrichten" (2024): <https://www.vhs-lernportal.de/wws/bin/4007530-4015250-1-2024_05_dvv_handreichung_deutsch_unterrichten.pdf> |
| Course information sheet (A1–B1, 12 lessons each) | <https://www.vhs-lernportal.de/wws/bin/4007242-4008322-1-infoblatt_a1-b1.pdf> |
| About the portal / FAQ | <https://a1.vhs-lernportal.de/wws/553396.php> · <https://a1.vhs-lernportal.de/wws/faq-lernende.php> |

The courses follow the BAMF integration-course curriculum:
<https://www.bamf.de/SharedDocs/Anlagen/DE/Integration/Integrationskurse/Kurstraeger/KonzepteLeitfaeden/rahmencurriculum-integrationskurs.pdf?__blob=publicationFile&v=9>

## Easy German

| What | Link | Notes |
|---|---|---|
| Website | <https://www.easygerman.org/> | |
| Membership (transcripts, vocab helper) | <https://www.easygerman.org/membership> | Transcripts and worksheets are members-only (from the Learner tier) |
| Super Easy German playlist | <https://www.youtube.com/playlist?list=PLk1fjOl39-53GxQIn1Hxdouokf0J0SDpl> | Beginner series |
| Podcast | <https://www.easygerman.org/podcast> | |
| Episode you studied: *Greetings & Farewells in Slow German (Super Easy German 274)* | <https://www.youtube.com/watch?v=aRlakaPVrEw> | March 2025. Your notes file is an auto-generated transcript with recognition errors |

## Exams and levels

| What | Link |
|---|---|
| Goethe-Zertifikat A1 (Start Deutsch 1) word list | <https://www.goethe.de/pro/relaunch/prf/de/A1_SD1_Wortliste_02.pdf> |
| Goethe-Zertifikat A2 word list | <https://www.goethe.de/pro/relaunch/prf/de/Goethe-Zertifikat_A2_Wortliste.pdf> |
| Goethe-Zertifikat B1 word list | <https://www.goethe.de/pro/relaunch/prf/de/Goethe-Zertifikat_B1_Wortliste.pdf> |
| Goethe exam pages | A1 <https://www.goethe.de/ins/de/de/prf/prf/gzsd1.html> · A2 <https://www.goethe.de/ins/de/de/prf/prf/gzsd2.html> · B1 <https://www.goethe.de/ins/de/de/prf/prf/gzb1.html> (B1 details: <https://www.goethe.de/ins/de/de/prf/prf/gzb1/inf.html>) · All exams: <https://www.goethe.de/de/spr/prf.html> |
| CEFR companion volume (Council of Europe) | <https://www.coe.int/en/web/common-european-framework-reference-languages/cefr-companion-volume-and-its-language-versions> |
| CEFR global scale / self-assessment grid | <https://www.coe.int/en/web/common-european-framework-reference-languages/table-1-cefr-3.3-common-reference-levels-global-scale> · <https://www.coe.int/en/web/common-european-framework-reference-languages/table-2-cefr-3.3-common-reference-levels-self-assessment-grid> |

goethe.de and coe.int block scripts but open normally in a browser.

## Dictionaries (gender, plural, spelling, examples)

- Duden: <https://www.duden.de/rechtschreibung/Tasche> (swap the word). Apostrophe rules: <https://www.duden.de/sprachwissen/rechtschreibregeln/apostroph>. *Tschüss* and *tschüs* are both correct: <https://www.duden.de/rechtschreibung/Tschuess> · <https://www.duden.de/rechtschreibung/tschues>
- DWDS (corpus examples): <https://www.dwds.de/wb/Tasche>
- Wiktionary (declension tables): <https://de.wiktionary.org/wiki/Tasche>
- dict.cc (second dictionary for phrases, used by `harvest_sources.py --glosses`): <https://www.dict.cc/?s=Schönen+Tag+noch>
- en.wiktionary definition API (used by `harvest_sources.py --glosses` to check meanings): <https://en.wiktionary.org/api/rest_v1/page/definition/Tochter>. German Wiktionary raw text (German definitions, translation tables): `https://de.wiktionary.org/w/index.php?title=<Wort>&action=raw`
- Wiktionary conjugation tables (checked 2026-09-26; used by `docs/tools/check_grammar_book.py fetch`): <https://de.wiktionary.org/wiki/Flexion:kommen> (swap the verb)
- Register and region labels (checked 2026-09-26): en.wiktionary, e.g. <https://en.wiktionary.org/wiki/pfiat_di> (*chiefly Austria, Bavaria, informal*); DWDS style labels, e.g. <https://www.dwds.de/wb/bis%20die%20Tage> (*salopp*)

## Grammar references (checked 2026-09-26)

Used by the grammar book ([`Grammatik/`](../Grammatik/README.md)). These DW grammar
pages belong to lessons not studied yet. They confirm rules only; examples always
come from studied lessons.

| DW page | Lesson | Confirms |
|---|---|---|
| [Numbers from 11 to 19](https://learngerman.dw.com/en/numbers-from-11-to-19/l-37265621/gr-38307006) · [Numbers from 20 to 100](https://learngerman.dw.com/en/numbers-from-20-to-100/l-37265621/gr-38307981) | A1 E2 L1 | 13–19, *sechzehn/siebzehn*, *-zig*, *einundzwanzig* |
| [W-questions](https://learngerman.dw.com/en/w-questions/l-37269671/gr-38306976) | A1 E2 L3 | question word – verb – subject |
| [Prepositions of place: aus](https://learngerman.dw.com/en/prepositions-of-place-aus/l-37269671/gr-38307071) · [in, an](https://learngerman.dw.com/en/prepositions-of-place-in-an/l-37269671/gr-38309222) | A1 E2 L3 | *kommen aus*, *wohnen in*, countries with an article |
| [Questions and statements](https://learngerman.dw.com/en/questions-and-statements/l-37337877/gr-38306265) | A1 E4 L2 | verb second in statements, verb first in yes/no questions |

## Anki

- Deck options, FSRS, desired retention, sibling burying: <https://docs.ankiweb.net/deck-options.html>
- Typed answers (`{{type:…}}`): <https://docs.ankiweb.net/templates/fields.html#checking-your-answer>
- Importing `.apkg` files (GUIDs, updating notes): <https://docs.ankiweb.net/importing/packaged-decks.html>
- Filtered decks (study one lesson from the cumulative decks): <https://docs.ankiweb.net/filtered-decks.html>
- Leeches: <https://docs.ankiweb.net/leeches.html>
- Getting started / note types / templates: <https://docs.ankiweb.net/getting-started.html> · <https://docs.ankiweb.net/editing.html> · <https://docs.ankiweb.net/templates/intro.html> · <https://docs.ankiweb.net/templates/generation.html>
- FAQ, multiple choice: <https://faqs.ankiweb.net/multiple-choice-questions.html>
- Wozniak, *Twenty rules of formulating knowledge*: <https://super-memory.com/articles/20rules.htm>

## Research behind the card design

See [research.md](research.md) for what each paper means for the cards.

- Webb (2007), a single context sentence vs word pairs: <https://journals.sagepub.com/doi/10.1177/1362168806072463>
- Nakata (2016), recall vs recognition formats: <https://www.degruyterbrill.com/document/doi/10.1515/iral-2015-0022/html>
- Kim & Webb (2022), spacing meta-analysis: <https://onlinelibrary.wiley.com/doi/abs/10.1111/lang.12479>
- Arnon & Ramscar (2012), learning gender with article + noun in larger units: <https://www.sciencedirect.com/science/article/abs/pii/S001002771100254X>
- Presson, MacWhinney & Tokowicz (2014), gender rules for novices: <https://www.cambridge.org/core/journals/applied-psycholinguistics/article/abs/learning-grammatical-gender-the-use-of-rules-by-novice-learners/5C9F7E93A0F74030C1F04280746745EA>
- Köpcke & Zubin, German gender assignment principles: <https://ids-pub.bsz-bw.de/files/8944/Koepcke_Zubin_Prinzipien_fuer_die_Genuszuweisung_im_Deutschen_1996.pdf>
- Nation (2000), interference in lexical sets: <https://onlinelibrary.wiley.com/doi/10.1002/j.1949-3533.2000.tb00239.x>

## Claude Code

- How Claude Code loads `CLAUDE.md` and `AGENTS.md`: <https://code.claude.com/docs/en/memory>
