# Anki card design reference

Use this reference only when building or changing Anki cards and templates.
It is intentionally separate from `AGENTS.md`: the project remains a German
learning system driven by the learner's chosen resources, rather than an Anki
project. The workspace rules in `AGENTS.md` override this reference.

## Current workspace decision

The cumulative Articles, Vocabulary, and Sentences decks and the lesson
Vocabulary decks do **not** use recorded audio, synthetic audio, TTS, sound
fields, or audio-only cards. This is a learner-confirmed rule, not a judgment
that audio is universally ineffective. A separately requested pronunciation
resource is outside this rule. The affected builders must package empty media
and reject audio/TTS markers during validation (`ANKI/anki_package_utils.py`
also rejects images and requires an empty media map).

The deck design also follows these evidence-backed defaults:

- Prefer effortful recall with corrective feedback over recognition. Anki's
  own multiple-choice FAQ recommends converting ordinary multiple-choice facts
  to direct questions because distractors can make them guessable.
- Keep one small, precise target per card. Piotr Wozniak's formulation rules
  describe the minimum-information principle: simpler items are easier to
  schedule, recall, and diagnose when forgotten.
- Use spaced retrieval, not repeated restudy. Language-learning research finds
  that spacing plus retrieval practice and feedback improves L2 vocabulary
  retention.
- Do not multiply cards merely because several templates are possible. A
  second card must demand a materially different and useful retrieval.

## How Anki is structured

- A **note** is the stored learning item and contains fields such as `German`,
  `English`, `Audio`, `Example`, and `Hint`.
- A **card type** is a front/back template. One note can generate several card
  types, and each generated card has independent review scheduling.
- A template inserts a field with `{{FieldName}}`. On the back, `{{FrontSide}}`
  repeats the rendered question; `<hr id=answer>` marks where the answer begins.
- Note types are shared across the collection, not confined to one deck. Do
  not casually change a note type used by another deck; clone or deliberately
  name a distinct type when the structure differs.
- `Tags`, `Type`, `Deck`, `Card`, and `FrontSide` are reserved special field
  names and must not be used for normal fields.

## Question formats

Choose the format for the retrieval skill being trained, not merely because a
format is available. A card should normally test one small, unambiguous thing.

### Direct question and answer

The ordinary card format is a prompt on the front and the answer on the back.
The learner retrieves the answer mentally, aloud, or in writing; reveals the
back; then chooses the review rating honestly. It is the most flexible form
when more than one wording can be correct.

Useful forms include:

- **Recognition/comprehension:** German word, sentence, or audio → English
  meaning. Good for early reading/listening vocabulary.
- **Production:** a precise English meaning or context → German word/form.
  Use it when the learner needs to produce German, not only understand it.
- **Grammar/form recall:** a lemma plus a precise cue (person, tense, case,
  article, comparative, etc.) → one requested German form.
- **Sentence production:** a tightly constrained meaning and target structure
  → a German sentence. Because several good sentences may exist, use manual
  self-grading rather than a single rigid answer checker.
- **Discrimination/minimal pair:** present close forms, meanings, or sounds →
  select or state the distinguishing feature. Explain that distinction on the
  back.

### Forward, reverse, and optional reverse

A note may generate a forward and a reverse card, e.g. German → English and
English → German. Use a reverse only when the reverse prompt has a reasonably
clear expected answer. A broad English gloss often maps to several valid German
words, so forcing a typed reverse can teach an arbitrary answer.

The built-in *Basic (and reversed card)* creates both directions. *Basic
(optional reversed card)* generates the second direction only when a dedicated
marker field (usually `Add Reverse`) is non-empty. The marker is not displayed.
This is a good pattern when only some entries deserve production practice.

### Cloze deletion

Cloze cards hide a word or a short chunk within a meaningful sentence:

```text
Ich {{c1::gehe}} heute nach Hause.
```

Each different cloze number creates a separate card. Reuse the same number to
hide several pieces on one card. A hint follows a second `::`, for example
`{{c1::gehe::verb}}`. Use cloze to retrieve a precise form in context, not to
make a learner reconstruct a long paragraph. Cloze notes are special Anki note
types and cannot be made by converting a regular note type.

### Image occlusion

Native Image Occlusion hides labelled areas of an image, map, chart, table, or
diagram. It supports rectangle, ellipse, and polygon masks. Use it where the
spatial or visual relationship is what must be remembered—not merely to make a
text fact look more interesting.

### Audio and media questions (general Anki capability; disabled here)

- **Listening comprehension:** German audio → meaning, word identification, or
  the next dialogue response.
- **Dictation/spelling:** audio or a concise cue → typed German word/form.
- **Visual prompt:** an image → German label, meaning, or a description.

Put image/sound references in a note field, such as `[sound:word.mp3]` or
`<img src="image.jpg">`. Do not construct a media filename from a template
field, such as `[sound:{{Word}}.mp3]`; Anki does not reliably track that media.
MP3 audio and MP4 video offer the broadest client compatibility.

### Multiple choice

Multiple choice can be made with custom HTML/JavaScript or add-ons, but it is
rarely the best default for flashcards. The official Anki FAQ recommends
turning ordinary multiple-choice facts into direct recall prompts: distractors
can be guessed and test recognition rather than retrieval. Use choices only
when choosing among realistic alternatives is itself the skill being learned.
Always show why the correct choice is correct after revealing the answer; do
not treat a clicked option as a substitute for Anki's normal self-rating.

## Answer methods

### Manual self-grading

The learner answers mentally, orally, or on paper, then compares with the back
and rates recall. This is best for synonyms, flexible word order, open-ended
sentences, and answers that need judgment. The card must make the expected
level of precision clear so self-grading is honest and consistent.

### Typed answer comparison

Put `{{type:AnswerField}}` on the front and include the same answer field on
the back (often by retaining `{{FrontSide}}`). Anki displays one input box and
highlights character differences when the answer is revealed.

Important limits:

- One typed comparison is supported per card.
- It is a single-line comparison, so it is unsuitable for paragraphs or
  several independent answers.
- A typing box does not appear in Anki's template preview or in AnkiWeb.
- `{{type:nc:AnswerField}}` ignores diacritic/combining-character differences.
  Use that only when spelling/diacritics are not the learning target. For
  German spelling practice, do not silently accept a meaningful distinction.

In this workspace every deck uses typed production: an English cue (plus a
verified German context with a blank where one exists) → typed German. Typed
answers are strict about spelling, capitals and punctuation; the apostrophe is
the German Mac keyboard's `'`. With a context, the typed answer is exactly the
blanked text. See `docs/card-design.md`.

### Typed cloze

On a Cloze note, `{{type:cloze:Text}}` tests the hidden content. If multiple
sections are hidden on the same card, their answers are separated with commas.

### Accepted variants

Native typed checking compares against one canonical field, not a list of
synonyms or alternate word orders. For legitimate alternatives, use manual
self-grading and show common variants on the back. Introduce custom answer
checking only when automatic acceptance is essential and it has been verified
on every intended client.

### Hints and text-to-speech

- `{{hint:HintField}}` displays a clickable textual hint only when requested.
  Hints make retrieval easier, so keep them optional and do not use them to
  compensate for a vague prompt. Audio cannot be deferred by a standard hint.
- `{{tts de_DE:German}}` can ask a compatible client to speak a field. Voices
  and quality vary by device, so it is a convenience rather than a replacement
  for deliberate recorded audio.

## German-focused design patterns

| Goal | Front / question | Back / answer |
| --- | --- | --- |
| Vocabulary comprehension | German word or brief German context | English meaning and concise example |
| Vocabulary production | Specific English meaning plus usage cue | German word/form; manual grade if variants fit |
| Noun gender | Noun without article, optionally context | `der` / `die` / `das`, noun, plural, example |
| Listening | Disabled by the current workspace rule | — |
| Inflection | Lemma plus exact grammatical cue | Requested form, rule reminder, natural example |
| Contextual usage | Sentence with one target blank | Missing word/form, translation, concise note |
| Visual terminology | Image occlusion or labelled picture | German label and a short context note |

Where source material supplies it, keep noun article, singular, plural, and
example distinct. For verbs, retain infinitive, required preposition/case,
principal forms when useful, and an example. A translation prompt must be
narrow enough that a production answer can fairly be assessed.

## Template safeguards and quality checks

- `{{#Field}}...{{/Field}}` displays content only when a field is non-empty;
  `{{^Field}}...{{/Field}}` displays it only when empty. Wrap the *whole*
  front in conditionals if controlling whether a card is generated.
- A generated regular card needs a non-empty normal field on its front. Fixed
  template text and special fields do not count. Check changed templates for
  blank cards and inspect **Tools → Empty Cards** before cleaning them up.
- An optional card type should depend on a marker field on its front, avoiding
  accidental blank or irrelevant cards.
- Put the answer first on the back, followed only by material that supports
  future recall: a short example, form note, source note, audio, image, or
  mnemonic.
- Avoid compound prompts and near-duplicate cards. Multiple cards are useful
  only when they require materially different retrieval.
- Test custom templates in preview and on intended desktop/mobile clients.
  Be cautious with client-specific JavaScript in syncable decks.
- Run **Check Media** after packaging or materially changing a media-heavy
  deck, and ensure actual media is included in exports.

## Official sources

- [Getting Started: notes, card types, typed answers, cloze, image occlusion](https://docs.ankiweb.net/getting-started.html)
- [Field replacements: typed answers, hints, TTS, special fields, media](https://docs.ankiweb.net/templates/fields.html)
- [Card generation: reverse, optional, conditional, and cloze cards](https://docs.ankiweb.net/templates/generation.html)
- [Adding and editing: cloze deletion and image occlusion](https://docs.ankiweb.net/editing.html)
- [Media documentation](https://docs.ankiweb.net/media.html)
- [Multiple-choice questions FAQ](https://faqs.ankiweb.net/multiple-choice-questions.html)
- [SuperMemo: 20 rules of formulating knowledge](https://super-memory.com/articles/20rules.htm)
- [Karatas et al.: spacing, retrieval practice, and feedback in L2 vocabulary](https://doi.org/10.1177/13621688211053525)
