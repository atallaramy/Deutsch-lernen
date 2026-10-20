"""News texts for paper re-reading (docs/tools/fetch_news.py): parsing only, no network."""

import html
import json
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "docs" / "tools"))

import fetch_news  # noqa: E402

TTML = """<tt:tt><tt:body><tt:div>
<tt:p begin="00:00:02.000"><tt:span>* Gong *</tt:span></tt:p>
<tt:p begin="00:00:05.000"><tt:span>Untertitel: Norddeutscher Rundfunk 2026</tt:span></tt:p>
<tt:p begin="00:00:10.000"><tt:span>Willkommen zur tagesschau in Einfacher Sprache.</tt:span></tt:p>
<tt:p begin="00:00:36.000"><tt:span>Und nun zur 1. Nachricht.</tt:span></tt:p>
<tt:p begin="00:00:40.000"><tt:span>In Berlin gab es gerade</tt:span><tt:br/><tt:span>ein großes Treffen.</tt:span></tt:p>
<tt:p begin="00:00:45.000"><tt:span>Jetzt zeigen wir einen Film dazu.</tt:span></tt:p>
<tt:p begin="00:00:50.000"><tt:span>Bei dem Fest sind viele Investoren.</tt:span></tt:p>
<tt:p begin="00:01:00.000"><tt:span>Und nun zur nächsten Nachricht.</tt:span></tt:p>
<tt:p begin="00:01:05.000"><tt:span>Die EU will das ändern.</tt:span></tt:p>
<tt:p begin="00:01:10.000"><tt:span>Und das waren unsere Nachrichten.</tt:span></tt:p>
<tt:p begin="00:01:12.000"><tt:span>Berlin. Treffen.</tt:span></tt:p>
<tt:p begin="00:01:14.000"><tt:span>Und jetzt kommt das Wetter.</tt:span></tt:p>
<tt:p begin="00:01:16.000"><tt:span>Es werden 8 bis 18 Grad.</tt:span></tt:p>
<tt:p begin="00:01:20.000"><tt:span>Das war die tagesschau in Einfacher Sprache.</tt:span></tt:p>
<tt:p begin="00:01:22.000"><tt:span>Tschüss und bis zum nächsten Mal.</tt:span></tt:p>
<tt:p begin="00:01:25.000"><tt:span>Copyright Untertitel: NDR 2026</tt:span></tt:p>
</tt:div></tt:body></tt:tt>"""

DW_PAGE = """<div data-testid="richtext-content-container"><span><h2>Frankreich: Innenminister bietet R&uuml;cktritt an</h2>

<p>Nach den <strong>Protesten</strong> fordert <strong>Premierminister</strong> Lecornu <strong>lokale Ausgangssperren</strong>. <strong>Innenminister </strong>Nu&ntilde;ez sagt etwas.<br>
<br>
<strong>Protest, -e</strong> (m.) – eine Demonstration<br>
&#160;</p>

<h2>Australien: Abgeordnete angefahren</h2>

<p>Die Polizei sagt, dass sie einen Autofahrer <strong>festgenommen </strong>hat.<br>
<br>
<strong>jemanden fest|nehmen</strong> – jemanden verhaften<br>
</p></span></div>"""


def episode(topics):
    return fetch_news.ts_episode("https://www.tagesschau.de/x/tse-1.html", player_page(topics))


def player_page(topics, subtitles=True):
    player = {"mc": {"meta": {"broadcastedOnDateTime": "2026-10-20T17:00:00+0000", "synopsis": ", ".join(topics)}}}
    if subtitles:
        player["mc"]["subtitles"] = [{"kind": "normal", "sources": [{"kind": "ebutt", "url": "https://x/untertitel-1.xml"}]}]
    header = html.escape(json.dumps({"url": "/json/headerapp"}), quote=True)
    return f'<div data-v="{header}"></div><div data-v="{html.escape(json.dumps(player), quote=True)}"></div>'


class TagesschauTest(unittest.TestCase):
    def test_subtitle_lines_drop_credits_and_join_breaks(self):
        lines = fetch_news.ttml_lines(TTML)
        self.assertNotIn("* Gong *", lines)
        self.assertNotIn("Copyright Untertitel: NDR 2026", lines)
        self.assertIn("In Berlin gab es gerade ein großes Treffen.", lines)

    def test_episode_reads_the_first_player_in_berlin_time(self):
        found = episode(["Berlin: Treffen", "EU: Rechte", "Das Wetter"])
        self.assertEqual(f"{found.when:%Y%m%d %H%M}", "20261020 1900")
        self.assertEqual(found.source, "https://x/untertitel-1.xml")
        self.assertEqual(found.topics, ["Berlin: Treffen", "EU: Rechte", "Das Wetter"])

    def test_episode_without_subtitles_has_no_source(self):
        found = fetch_news.ts_episode("https://x", player_page(["A", "Das Wetter"], subtitles=False))
        self.assertEqual(found.source, "")

    def test_markdown_keeps_news_recap_and_weather(self):
        text = fetch_news.ts_markdown(episode(["Berlin: Treffen", "EU: Rechte", "Das Wetter"]),
                                      fetch_news.ttml_lines(TTML))
        self.assertIn("# tagesschau in Einfacher Sprache – 20.10.2026, 19:00 Uhr", text)
        self.assertIn("## 1. Berlin: Treffen\n\nIn Berlin gab es gerade ein großes Treffen. "
                      "Jetzt zeigen wir einen Film dazu.\n\nBei dem Fest sind viele Investoren.", text)
        self.assertIn("## 2. EU: Rechte\n\nDie EU will das ändern.", text)
        self.assertIn("## Und das waren unsere Nachrichten\n\n1. Berlin: Treffen\n2. EU: Rechte\n\n"
                      "## Das Wetter\n\nEs werden 8 bis 18 Grad.", text)
        for dropped in ("Willkommen", "Und nun zur", "Tschüss"):
            self.assertNotIn(dropped, text)

    def test_transition_variants_and_lead_sentences(self):
        lines = ["Und nun zur ersten Nachricht:", "Die Rente steigt.", "Um einen Beschluss von der Regierung",
                 "geht es auch in der nächsten Nachricht.", "Rauchen wird teurer.", "Zur nächsten Nachricht.",
                 "Es regnet in Spanien.", "Und das waren unsere Nachrichten:", "Und jetzt kommt das Wetter:",
                 "Es ist kalt.", "Und das war die tagesschau in Einfacher Sprache.", "Tschüss, bis zum nächsten Mal."]
        news, recap, weather = fetch_news.ts_sections(lines)
        self.assertEqual(news, [["Die Rente steigt."],
                                ["Um einen Beschluss von der Regierung", "geht es auch in der nächsten Nachricht.",
                                 "Rauchen wird teurer."],
                                ["Es regnet in Spanien."]])
        self.assertEqual(recap, [])
        self.assertEqual(weather, ["Es ist kalt."])

    def test_markdown_numbers_items_and_keeps_spoken_recap_when_topics_do_not_match(self):
        text = fetch_news.ts_markdown(episode(["Nur ein Thema"]), fetch_news.ttml_lines(TTML))
        self.assertIn("## Nachricht 1", text)
        self.assertIn("## Nachricht 2", text)
        self.assertIn("## Und das waren unsere Nachrichten\n\nBerlin. Treffen.\n", text)

    def test_topics_without_weather_still_head_the_items(self):
        text = fetch_news.ts_markdown(episode(["Berlin: Treffen", "EU: Hilfe für die Ukraine."]),
                                      fetch_news.ttml_lines(TTML))
        self.assertIn("## 2. EU: Hilfe für die Ukraine\n", text)

    def test_markdown_keeps_everything_without_section_markers(self):
        text = fetch_news.ts_markdown(episode([]), ["Ein Satz.", "Noch ein Satz."])
        self.assertIn("Ein Satz. Noch ein Satz.", text)


class DwTest(unittest.TestCase):
    def test_items_keep_text_and_leave_the_glossary(self):
        self.assertEqual(fetch_news.dw_items(DW_PAGE), [
            ("Frankreich: Innenminister bietet Rücktritt an",
             "Nach den Protesten fordert Premierminister Lecornu lokale Ausgangssperren. Innenminister Nuñez sagt etwas."),
            ("Australien: Abgeordnete angefahren", "Die Polizei sagt, dass sie einen Autofahrer festgenommen hat."),
        ])

    def test_time_comes_from_the_pdf_heading(self):
        self.assertEqual(fetch_news.dw_time("Manuskript\n20. Oktober 2026, 08:30 Uhr\nNachricht 1"),
                         (date(2026, 10, 20), "0830"))
        self.assertEqual(fetch_news.dw_time("1. März 2026, 8:05 Uhr"), (date(2026, 3, 1), "0805"))
        self.assertIsNone(fetch_news.dw_time("no date here"))


if __name__ == "__main__":
    unittest.main()
