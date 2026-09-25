# German Anki decks

`articles.apkg` is the main Anki deck for practising `der`, `die`, and `das`.
Its front shows only the noun and requires a typed article. The back shows the
complete noun, its source plural, and only dependable suffix-based gender hints.
It contains no multiple-choice interaction and no audio.

`articles-scan-index.json` records the durable lesson-vocabulary sources used.
After lesson vocabulary changes, rerun:

```sh
python3 ANKI/build_articles_deck.py
```

The builder updates still-valid nouns in place, adds new nouns, and removes
obsolete unreviewed notes. If an obsolete card has review history, it is
suspended instead of deleted.

`vocabulary.apkg` is the cumulative DW Nico’s Weg A1 lexical-production deck.
Its cards use a precise English/context cue and require one typed German item.
For nouns, the learner types the noun without its article; the Articles deck
owns gender recall. Exact repeats across lessons are merged, proper names are
not made into vocabulary cards, and productive sentence-pattern targets are
delegated to Sentences. Lesson vocabulary captured from DW remains in
`lesson-vocabulary.json`; each lesson deck is created beside its lesson
Markdown file. Rebuild them with:

```sh
python3 ANKI/build_vocabulary_decks.py
python3 ANKI/build_articles_deck.py
```

`sentences.apkg` is the cumulative, manually curated sentence/grammar deck. It
keeps its source-based prompts and explicit selection in
`sentence-sources.json`. Cards use tightly cued German production or one short
contextual completion. There are no recognition mirrors, multiple-choice
variants, audio cards, or TTS. This is the home for grammar and contextual verb
forms; extend it only with distinct, reusable language from the learner's
chosen resources, then run:

```sh
python3 ANKI/build_sentences_deck.py
```

Every builder validates SQLite integrity, note/card links, card count, empty
media, and the absence of audio/TTS before reporting success.
