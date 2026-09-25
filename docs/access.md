# Access to course materials

Checked 2026-09-25.

| Course | What Claude needs | Status |
|---|---|---|
| DW Nicos Weg | Nothing. Lesson pages, exercises, grammar and culture pages, and script PDFs are public; `ANKI/harvest_sources.py` reads them directly. A DW account only stores your progress and the DW vocabulary trainer. | Works |
| VHS-Lernportal | The public PDFs (word lists, film scripts, grammar lists) need nothing. Lesson content inside the portal (scenarios, exercises, phrase trainer) needs a session. | Public part works; portal: see below |
| Easy German | YouTube: nothing. Official transcripts are for members only. | See [easy-german-transcripts.md](easy-german-transcripts.md) |

## VHS portal: how Claude can read lesson content

Claude reads pages through your own Chrome (the Claude in Chrome extension),
read-only. Two ways to open the portal there:

1. **You log in once in Chrome** (tick "stay logged in" if offered). Claude then
   reads the lessons in that session. It never needs your password: its safety
   rules do not allow it to type passwords into login forms, even with your
   permission. That is also why a `.env` file with your password would not help.
2. **Guest access** ("Ohne Registrierung testen" → "Als Gast einloggen"): no
   password, but clicking it means agreeing to the portal's data-processing
   notice, which Claude will only do after you say yes. Guests do not see
   every area, and guest data is deleted after 24 hours.

An API is not needed and the portal does not offer one.

**What happened on 2026-09-25:** the learner logged in, but the portal keeps
its login inside that one tab (a session code in the web address), so a new tab
opened by Claude is logged out. Claude therefore used guest access (with the
learner's yes). Recipe for the trainers:
1. *Mein A1 → Vokabeltrainer* (or *Phrasentrainer*); choose the lesson and **English**; *Los geht's*.
2. Each card shows both sides in `span.courselet_text`. Clicking ✔
   (`input.courselet_vocabulary_trainer_right`) moves to the next card. Cards come in
   both directions and repeat, so collect until the number of unique pairs stops growing.
3. Keep each browser call short (a few cards). Long loops freeze Chrome. The phrase
   trainer froze repeatedly and was stopped after 5 phrases.
4. Save the pairs to `VHS-Lernportal/<level>/Materials/source-snapshot.json`
   as a `vhs-portal-capture` source, noting any normalisation.

If you ever want a script to log in without the browser, keep the password
in the macOS Keychain, not a `.env` (the `Documents` folder may sync to
iCloud). Type this yourself so the password never appears in the chat:

```sh
security add-generic-password -s vhs-lernportal -a "<your username>" -w
```

A script can read it with `security find-generic-password -s vhs-lernportal -w`.
No such script exists yet; the browser route above is simpler.
