# Nicos Weg A1 materials

Every lesson has its own folder. Its `Materials/` subfolder holds the official
DW English script/vocabulary PDF; existing lesson Markdown and lesson decks
stay in that same lesson folder.

`a1-script-vocabulary-manifest.json` records the official URL and local file
for all 76 A1 lessons. Re-run `ANKI/download_nicos_weg_a1_materials.py` to
verify and fill any missing script/vocabulary PDFs without redownloading files
that are already valid.

Each processed lesson's teacher guide (`Teacher guide and exercises
(German).pdf`) is saved in its `Materials/` by `ANKI/harvest_sources.py`, from
the lesson's *Other tools* page. The A1–B1 activity book is in
`../Materials/`.
