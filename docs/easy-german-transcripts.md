# Easy German transcripts: method and limits

Tested 2026-09-25 on *Greetings & Farewells in Slow German (Super Easy German
274)*, <https://www.youtube.com/watch?v=aRlakaPVrEw>.

## Method that works (YouTube "Show transcript")

1. Open the video in Chrome.
2. Expand the description (“…more”) and click **Show transcript**.
3. The panel lists timestamped lines. The track name is shown at the bottom
   (here: **German (auto-generated)**).
4. Claude copies the lines with a small script in the page. The transcript panel is
   `[target-id="engagement-panel-searchable-transcript"]`; its text alternates
   timestamp and line.

Downloading captions directly (`api/timedtext`) returns empty responses now,
so the browser panel is the reliable route.

## What the transcript is

- SEG 274 has **only one caption track: German, auto-generated**. Easy
  German did not upload their own German subtitles for it. Their subtitles are
  burned into the video picture instead.
- The auto-generated text is YouTube speech recognition. It is the same text as
  `EasyGerman/01LearnBasiGermanGreetings&Farewells.md` and contains recognition
  errors ("albd Schmidt", "usel", "vit die viert dich").
- Reading the burned-in (official) subtitles from video frames was tried. The
  player did not render video in the automated tab, so this failed.

## How the auto transcript can still be used

- **To find items:** which greetings and farewells the episode teaches, and at what
  timestamp.
- **Not as a context source.** An auto-generated line is not verified text, so it
  never goes on a card.
- **Spelling and meaning** of each item are verified elsewhere: the DW culture
  pages, DW/VHS glossaries, the video's own description (written by Easy
  German), and dictionaries (en.wiktionary via
  `ANKI/harvest_sources.py --glosses`).
- Official transcripts (members) or a video that plays in the browser would allow
  real Easy German contexts later.

For SEG 274 the corrected study transcript is
`EasyGerman/Materials/SEG 274 transcript (auto captions, corrected).md`. The
items themselves were verified against DW, en.wiktionary and dict.cc
(`ANKI/gloss-snapshot.json`).

Check each new episode's tracks: if a video has a manually uploaded German
track (not "auto-generated"), that track is Easy German's own text and can be
snapshotted as a source.
