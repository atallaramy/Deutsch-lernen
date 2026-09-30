#!/usr/bin/env python3
"""Render ANKI/review/preview.html: every card's front and back for human review before approval."""

from __future__ import annotations

import html
from collections import OrderedDict, defaultdict
from pathlib import Path

from deck_data import Card, Data

STYLE = """
:root { --bg:#fbfaf7; --panel:#ffffff; --ink:#1f2328; --muted:#6b7280; --line:#e5e1d8; --accent:#8a6d1f;
  --gap:#b45309; --bad:#b91c1c; --warn:#a16207; --ok:#15803d; --chip:#f3efe6; }
@media (prefers-color-scheme: dark) { :root { --bg:#1b1c1f; --panel:#24262a; --ink:#e5e7eb; --muted:#9ca3af;
  --line:#34373d; --accent:#e0b45a; --gap:#f59e0b; --bad:#f87171; --warn:#fbbf24; --ok:#4ade80; --chip:#2e3035; } }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--ink); font:15px/1.5 -apple-system,"Segoe UI",Roboto,Arial,sans-serif; }
main { max-width: 1100px; margin: 0 auto; padding: 24px 16px 80px; }
h1 { font-size: 26px; margin: 0 0 4px; } h2 { font-size: 20px; margin: 32px 0 10px; border-bottom:1px solid var(--line); padding-bottom:6px; }
h3 { font-size: 16px; margin: 22px 0 8px; color: var(--accent); }
.muted { color: var(--muted); } .bad { color: var(--bad); } .ok { color: var(--ok); } .warnc { color: var(--warn); }
.summary { display:flex; flex-wrap:wrap; gap:10px; margin:14px 0; }
.stat { background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:10px 14px; min-width:120px; }
.stat b { display:block; font-size:22px; }
.controls { position:sticky; top:0; background:var(--bg); padding:10px 0; z-index:2; display:flex; flex-wrap:wrap; gap:8px; }
.controls button { font:inherit; border:1px solid var(--line); background:var(--panel); color:var(--ink); border-radius:999px;
  padding:5px 12px; cursor:pointer; } .controls button[aria-pressed=true] { background:var(--accent); color:var(--bg); }
.card { background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:12px 14px; margin:10px 0; }
.card header { display:flex; flex-wrap:wrap; gap:6px; align-items:center; font-size:12px; color:var(--muted); }
.chip { background:var(--chip); border-radius:999px; padding:1px 8px; }
.chip.new { color:var(--warn); } .chip.approved { color:var(--ok); }
.sides { display:grid; grid-template-columns: 1fr 1fr; gap:14px; margin-top:8px; }
@media (max-width: 720px) { .sides { grid-template-columns: 1fr; } }
.side { border-left:3px solid var(--line); padding-left:10px; min-width:0; overflow-wrap:anywhere; }
.side .label { font-size:11px; text-transform:uppercase; letter-spacing:.1em; color:var(--muted); }
.instr { font-size:12px; color:var(--muted); } .context { font-size:18px; font-weight:600; margin:4px 0; }
.gap { color:var(--gap); } .cue { margin:4px 0; } .answer { font-family: ui-monospace, Menlo, monospace; background:var(--chip);
  padding:1px 6px; border-radius:6px; } .display { font-size:18px; font-weight:700; } .details { font-size:13px; color:var(--muted); }
.source { font-size:11px; color:var(--muted); margin-top:6px; } .noun { font-size:20px; font-weight:700; }
.flags { margin:8px 0 0; padding-left:18px; font-size:13px; color:var(--warn); }
ul.errors li { color:var(--bad); } table { border-collapse: collapse; width:100%; font-size:13px; }
td, th { border-bottom:1px solid var(--line); padding:4px 6px; text-align:left; vertical-align:top; }
code { font-family: ui-monospace, Menlo, monospace; font-size: 13px; }
"""

SCRIPT = """
const state = {deck: 'all', only: 'all'};
function apply() {
  document.querySelectorAll('.card').forEach(c => {
    const deckOk = state.deck === 'all' || c.dataset.deck === state.deck;
    const onlyOk = state.only === 'all' || (state.only === 'flagged' && c.dataset.flagged === '1')
                 || (state.only === 'unapproved' && c.dataset.approved === '0');
    c.hidden = !(deckOk && onlyOk);
  });
  document.querySelectorAll('[data-set]').forEach(b => {
    const [k, v] = b.dataset.set.split(':'); b.setAttribute('aria-pressed', state[k] === v);
  });
}
document.querySelectorAll('[data-set]').forEach(b => b.addEventListener('click', () => {
  const [k, v] = b.dataset.set.split(':'); state[k] = v; apply(); }));
apply();
"""


def front(card: Card) -> str:
    f = card.fields
    parts = [f"<div class=instr>{f['Instruction']}</div>"]
    if card.deck == "vocabulary":
        if f["Context"]:
            parts.append(f"<div class=context>{f['Context']}</div>")
        parts.append(f"<div class=cue>{f['Cue']}</div>")
    elif card.deck == "articles":
        parts.append(f"<div class=context>{f['Context']}</div>" if f["Context"] else f"<div class=noun>{f['Noun']}</div>")
        parts.append(f"<div class=cue>{f['Gloss']}</div>")
    else:
        parts.append(f"<div class=cue>{f['Scene']}</div>")
        if f["Prompt"]:
            parts.append(f"<div class=context>{f['Prompt']}</div>")
    parts.append(f"<div>typed answer: <span class=answer>{f['Answer']}</span></div>")
    return "".join(parts)


def back(card: Card) -> str:
    f = card.fields
    parts = [f"<div class=display>{f['Display']}</div>"]
    if f.get("Filled"):
        parts.append(f"<div>{f['Filled']}</div>")
    if f.get("Details"):
        parts.append(f"<div class=details>{f['Details']}</div>")
    parts.append(f"<div class=source>{f['Source']}</div>")
    return "".join(parts)


def write(path: Path, data: Data, cards: list[Card], errors: list[str], warnings: dict[str, list[str]],
          hashes: dict[str, str], approved: dict[str, str]) -> None:
    decks = OrderedDict((deck, [card for card in cards if card.deck == deck]) for deck in ("vocabulary", "articles", "sentences"))
    approved_count = sum(hashes[card.key] in approved for card in cards)
    flagged = {card.key for card in cards if warnings.get(card.key)}
    out = ["<!doctype html><html lang=en><head><meta charset=utf-8>",
           "<meta name=viewport content='width=device-width, initial-scale=1'><title>Deck Review</title>",
           f"<style>{STYLE}</style></head><body><main>",
           "<h1>Deck review</h1>",
           f"<p class=muted>Data revision {html.escape(data.revision)} · {len(data.entries)} captured entries in "
           f"{sum(bool(l.record.get('entries')) for l in data.lessons)} studied lessons. Nothing is packaged until every "
           f"card below is approved and all checks pass.</p>",
           "<div class=summary>"]
    for deck, items in decks.items():
        out.append(f"<div class=stat><b>{len(items)}</b>{deck}</div>")
    out.append(f"<div class=stat><b class={'bad' if errors else 'ok'}>{len(errors)}</b>errors</div>")
    out.append(f"<div class=stat><b class=warnc>{len(flagged)}</b>cards with info notes</div>")
    out.append(f"<div class=stat><b>{approved_count}/{len(cards)}</b>approved</div></div>")
    out.append("<p>Every German context has been checked against the official sources, and every English meaning against "
               "the course glossary or a dictionary. The notes under some cards are information, not homework. "
               "When you are happy, tell Claude “approve” (or run <code>python3 ANKI/build_all.py approve --all</code>).</p>")
    if errors:
        out.append("<h2>Errors (must be fixed before approval)</h2><ul class=errors>")
        out += [f"<li>{html.escape(error)}</li>" for error in errors]
        out.append("</ul>")
    if data.pending:
        out.append("<h2>Waiting for your yes/no</h2><p class=muted>These items are in your notes but are borderline under "
                   "decision D3. They are not built until you decide.</p><table><tr><th>Lesson</th><th>Item</th><th>Why</th></tr>")
        out += [f"<tr><td>{html.escape(lesson.label)}</td><td>{html.escape(item['german'])}</td>"
                f"<td>{html.escape(item['reason'])}</td></tr>" for lesson, item in data.pending]
        out.append("</table>")
    merged = [card for card in decks["vocabulary"] if len(card.covers) > 1]
    if merged:
        out.append("<h2>Merged records (identical lemma + sense)</h2><table><tr><th>Card</th><th>Captured in</th></tr>")
        out += [f"<tr><td>{html.escape(card.key)}</td><td>{html.escape(', '.join(card.covers))}</td></tr>" for card in merged]
        out.append("</table>")
    senses = defaultdict(list)
    for card in decks["vocabulary"]:
        senses[card.key.split("|")[0]].append(card.key.split("|")[1])
    separate = {lemma: items for lemma, items in senses.items() if len(items) > 1}
    if separate:
        out.append("<h2>Same word, distinct meanings (kept as separate cards)</h2><table><tr><th>Word</th><th>Senses</th></tr>")
        out += [f"<tr><td>{html.escape(lemma.replace('vocab:', ''))}</td><td>{html.escape(', '.join(items))}</td></tr>"
                for lemma, items in separate.items()]
        out.append("</table>")
    out.append("<h2>Cards</h2><div class=controls>")
    for value in ["all", *decks]:
        out.append(f"<button data-set='deck:{value}'>{value}</button>")
    out.append("<span class=muted>|</span><button data-set='only:all'>every card</button>"
               "<button data-set='only:flagged'>only cards with notes</button>"
               "<button data-set='only:unapproved'>only unapproved</button></div>")
    for deck, items in decks.items():
        out.append(f"<h2>{deck.title()}</h2>")
        by_lesson = OrderedDict()
        for card in sorted(items, key=lambda card: card.order):
            by_lesson.setdefault(card.lessons[0], []).append(card)
        for lesson_id, lesson_cards in by_lesson.items():
            out.append(f"<h3>{html.escape(data.lesson(lesson_id).label)}</h3>")
            for card in lesson_cards:
                is_approved = hashes[card.key] in approved
                notes = warnings.get(card.key, [])
                out.append(f"<article class=card data-deck={deck} data-flagged={'1' if notes else '0'} "
                           f"data-approved={'1' if is_approved else '0'}><header><span class=chip>{html.escape(card.key)}</span>"
                           f"<span class='chip {'approved' if is_approved else 'new'}'>{'approved' if is_approved else 'not approved'}</span>"
                           f"<span class=chip>{html.escape(' '.join(t for t in card.tags if t.startswith(('course::', 'context::'))))}</span>"
                           f"</header><div class=sides><div class=side><div class=label>Front</div>{front(card)}</div>"
                           f"<div class=side><div class=label>Back</div>{back(card)}</div></div>")
                if notes:
                    out.append("<ul class=flags>" + "".join(f"<li>{html.escape(note)}</li>" for note in dict.fromkeys(notes)) + "</ul>")
                out.append("</article>")
    out.append(f"</main><script>{SCRIPT}</script></body></html>")
    path.write_text("\n".join(out), encoding="utf-8")
