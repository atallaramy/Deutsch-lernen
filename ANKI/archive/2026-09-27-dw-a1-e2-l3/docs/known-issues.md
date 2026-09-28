# Known issues and open items (2026-09-25)

## Waiting for your decision

- **VHS portal (D6): partly done.** The Lektion 2 vocabulary trainer (61 words
  with official English) is captured. The phrase trainer froze Chrome after 5
  phrases; it can be retried in a later session ([access.md](access.md)). The
  *Familienstand* terms from your notes are dictionary-checked. Their exact
  wording in the portal exercises has not been captured yet.
- **Easy German (D7): done.** 31 items captured and verified. Pending (no
  dictionary confirms them): *Man hört sich.*, *Wir hören wieder voneinander.*, *GuMo*.
- **DW A1 E2 L3 (2026-09-28):** the grammar page's country list (*aus dem Irak … aus den
  Vereinigten Arabischen Emiraten*), marked "Reference only" in your notes: cards or no cards?
  Also five words beyond A1 from the script and exercises (*passieren, aufschreiben, der Aufnäher,
  die Polizeistelle, die Radiomoderatorin*): add them tagged, or leave them out?
- **Pending until a source confirms them:** *Man hört sich.* and *Wir hören
  wieder voneinander.* (Easy German). Declined: USA, DNA, GuMo.
- **Old lesson-deck files** (`Hallo_Vocabulary.apkg`, `Kein_Problem_Vocabulary.apkg`, …)
  are the previous design. They are kept (no deletion without your go-ahead), but do
  not import them; the new ones are named `DW A1 E… - Vocabulary.apkg`.

## Found and fixed in the v3 data

- Dead DW links: Hallo (`l-37251017` → `l-37250531`), Nico hat ein Problem
  (`l-37262889` → `l-37265543`), Tschüss in the sentence data
  (`l-37251040` → `l-37251033`). The Tschüss PDF link `52718807` is dead; the
  right one is `52719087`, which matches your local PDF's hash.
- Wrong meaning: *die Information* is the information desk (DW: short for
  *Informationsschalter*), not "information".
- *die Spaghetti* is plural-only, so it has no Articles card.
- Missing forms added from the glossaries: *fliegen*, *kommen*, the *Kurzform*
  notes (*noch mal*, *Reisepass*, *Uni*).
- Lessons you had studied but that were never captured (DW E1 L2, E1 L3, VHS
  Lektion 2) are now captured.

## Workspace notes (nothing changed; your call)

- `DW Deutsch lernen/A1/a1-script-vocabulary-manifest.json` still points to the
  old folder names (`A1/02/…`, `A1/03/…`). **Do not rerun**
  `ANKI/download_nicos_weg_a1_materials.py` as it is. It would create a second
  set of `02/`, `03/`… folders. It needs a folder-name mapping first; ask Claude.
- Clear duplicates (identical bytes):
  - `02_meeting_people/01_Lesson_01/Script and vocabulary (English).pdf` = its `Materials/` copy
  - `02_meeting_people/04_Lesson_04/Script and vocabulary (English).pdf` = its `Materials/` copy
  
  Kept; delete only on your explicit go-ahead.
- Legacy packages in `01_Intro_zu_A1/03_Tschüs/`: `Tschüs.apkg` (same cards as
  the old `Tschüs_Vocabulary.apkg`) and `tschuess.apkg` (old German→English
  deck). Kept.
- `04_Von A bis Z/Materials/README.md` mentions a `Phonetic alphabet audio/`
  folder that is not in the workspace. It belongs to the pronunciation resource,
  which is deliberately untouched.
- Empty notes: `EasyGerman/02.md`–`07.md`, and the VHS Lektion 1 and 3–7 folders. They will be
  processed when you study them.
- The phonetic-alphabet builder copies its Anki schema from
  `Von A bis Z_Vocabulary.apkg` when its own package is missing. The v3 lesson
  deck keeps the same schema, so this still works.
- Your notes show y↔z swaps ("Kuryform", "Grüyi", "Kreuy"). This fits the German
  keyboard layout, where Y and Z are swapped compared with English.
