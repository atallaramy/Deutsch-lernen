# Card design (rationale and examples)

The binding rules are in `AGENTS.md`; this page explains them with real
cards. Evidence: [research.md](research.md).

## Who owns what

| Knowledge | Deck | Never *asked* in |
|---|---|---|
| A word or fixed phrase (noun without article, infinitive, adjective, pronoun, greeting) | Vocabulary | Articles, Sentences |
| The gender of a singular noun | Articles | Vocabulary (the article may be visible), Sentences |
| Forms, word order, du/Sie, replies, patterns, how names are used | Sentences | Vocabulary, Articles |
| Plurals, principal parts, short forms | Backs only (not tested) | — |

## Contexts

- **German contexts are verbatim source text**, checked against a local
  snapshot on every build. That includes DW scripts, DW exercise, grammar and
  culture pages, and the VHS word lists and film scripts.
- **English cues and scenes** are prompts written to match the source and
  reviewed in the preview.
- **With a context**, you type exactly what fills the blank.
- **A context must earn its place.** Most nouns appear only in glossary lists,
  so their Articles cards show the noun and its gloss.

### Examples from the current decks

| Card | Front | Answer | Why |
|---|---|---|---|
| Vocabulary *Pass* | „Nico, hast du einen ＿＿＿?" — *passport* | `Pass` | DW E1 L4 exercise, verbatim. *Reisepass* stays on the back, because on the front it would give the answer away. |
| Vocabulary *Mama* vs *Mutter* | „Nein, Lisa ist nicht meine ＿＿＿." — *mum/mom (what a child says)*; „Das sind meine Eltern, meine ＿＿＿ und mein Vater." — *mother (the neutral word)* | `Mama` / `Mutter` | Different registers. The two cards are kept apart in the new-card queue. |
| Vocabulary *Guten Tag* | „11:00 Uhr – 18:00 Uhr: ＿＿＿." — *formal hello — during the day* | `Guten Tag` | The DW exercise times tell the three greetings apart. |
| Vocabulary *Information* | *information desk (e.g. at the airport) — short form, singular* | `Information` | Corrects the old wrong meaning (DW: short for *Informationsschalter*). |
| Articles *Pass* | „＿＿＿ Pass ist in Nicos Tasche." | `Der` | A nominative slot; you type the capital because the article starts the sentence. |
| Articles *Name* | *Name — name* | `der` | Every source sentence has *mein/Ihr*, which would give the gender away, so there is no context. The back warns: ends in ‑e but is *der*. |
| Articles *Spaghetti* | — | — | Plural-only (DW: *nur Plural*), so there is no gender card. The Vocabulary back says so. |
| Sentences reply | Scene: someone greets you formally… Prompt: „Guten Tag! Wie geht es Ihnen?" | `Sehr gut, danke. Und Ihnen?` | Verbatim DW script. Covers the entry *Und Ihnen?*. |
| Sentences name (D4) | Scene: your friend Martina is leaving on a trip… | `Tschüss, Martina. Gute Reise!` | A first name goes with the informal farewell. |
| Sentences with your error | Scene: ask a stranger (formal) where they are from | `Woher kommen Sie?` | The back shows "Not: ~~Wo kommen Sie?~~", your own error from the notes. |

## Leakage checks (run by `build_all.py check`)

- **Vocabulary:** the answer (or its stem) must not appear anywhere else in
  the context. A cue that contains the answer is flagged for the preview
  (e.g. a cognate like *hotel → Hotel*).
- **Articles:**
  - the blank must be the gender article directly before the noun
  - no *ein/eine*, possessive, *kein* or *dies-/welch-* word before the noun
  - the noun must appear exactly once
  - no plural on the front
  - pronouns in the context are flagged for a human look
- **Every deck:**
  - no identical source sentence on two fronts
  - no context that contains another card's Sentences answer (reply prompts are the exception and are spaced apart)
  - no two Vocabulary cues sharing a meaning with different answers

## Typed answers

Spelling, capitals, umlauts, ß and punctuation are strict, so the cards teach
correct German writing. The apostrophe is the one you type on the Mac German
keyboard (`'`, Shift+#). On the German layout, ä/ö/ü/ß have their own keys.
