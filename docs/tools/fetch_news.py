#!/usr/bin/env python3
"""Save daily news texts to Nachrichten/ (Markdown/ and PDF/) for the learner's paper re-reading.

Network step, run when the learner asks: `python3 docs/tools/fetch_news.py` (newest episode of each show)
or `--days N` (every episode of the last N days). Existing files are never overwritten.
tagesschau in Einfacher Sprache: text from the official NDR subtitles, plus a printable PDF of it (tagesschau
publishes none); an episode without subtitles is skipped, never filled from auto-captions. DW Kurz und leicht:
text from the episode page, plus its official PDF (with glossary). Needs `pdftotext` (poppler),
pandoc and Google Chrome. Nothing here builds cards.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_grammar_pdf import print_pdf  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Nachrichten"
MARKDOWN = OUT / "Markdown"
PDF = OUT / "PDF"
USER_AGENT = "Mozilla/5.0 (news texts for personal study)"
BERLIN = ZoneInfo("Europe/Berlin")
TS_SERIES = "https://www.tagesschau.de/multimedia/sendung/tagesschau_in_einfacher_sprache"
TS_BASE = "https://www.tagesschau.de"
DW_SERIES = "https://learngerman.dw.com/de/kurz-und-leicht/s-69137519"
DW_BASE = "https://learngerman.dw.com"
MONTHS = {name: number for number, name in enumerate(
    ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November",
     "Dezember"], start=1)}

TS_CREDIT = re.compile(r"^(\* .* \*|(Copyright )?Untertitel:.*)$")
TS_NEWS_START = re.compile(r"^(?:(?:Und )?[Nn]un )?[Zz]ur (?:ersten|nächsten|\d+\.) Nachricht[.:]$")
TS_NEWS_LEAD = re.compile(r"\bin der nächsten Nachricht[.:]$")  # "Um … geht es auch in der nächsten Nachricht."
TS_NEWS_END = re.compile(r"^Und das waren unsere Nachrichten[.:]$")
TS_WEATHER = re.compile(r"^Und jetzt kommt das Wetter[.:]$")
TS_OUTRO = re.compile(r"^(?:Und )?(?:Das war die tagesschau|Tschüss)", re.I)
TS_FILM = re.compile(r"\bFilm\b.*[.!?]$")  # "Jetzt zeigen wir einen Film dazu." ends the studio part

NEWS_CSS = """
@page { size: A4; margin: 16mm 18mm; }
body { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; font-size: 12pt; line-height: 1.6;
  color: #1f2328; margin: 0; }
h1 { font-size: 17pt; margin: 0 0 2pt; color: #1f3a5f; }
h1 + p { font-size: 8.5pt; color: #777; margin: 0 0 8pt; }
h2 { font-size: 13pt; margin: 14pt 0 4pt; color: #1f3a5f; break-after: avoid; }
p { margin: 0 0 7pt; orphans: 2; widows: 2; }
a { color: #1f5fa8; text-decoration: none; }
"""


@dataclass
class Episode:
    when: datetime
    url: str
    source: str  # subtitle XML (tagesschau) or PDF (DW)
    topics: list[str]


def fetch(url: str) -> bytes:
    request = urllib.request.Request(urllib.parse.quote(url, safe=":/?=&%#"), headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def clean(fragment: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", re.sub(r"<br\s*/?>", " ", fragment))).split())


# tagesschau in Einfacher Sprache

def ts_player(page: str) -> dict | None:
    """The page's own episode is its first player with metadata."""
    for match in re.finditer(r'data-v="(.*?)"', page):
        try:
            data = json.loads(html.unescape(match.group(1)))
        except json.JSONDecodeError:
            continue
        player = data.get("mc") if isinstance(data, dict) else None
        if isinstance(player, dict) and "meta" in player:
            return player
    return None


def ts_episode(url: str, page: str) -> Episode | None:
    player = ts_player(page)
    if not player:
        return None
    meta = player["meta"]
    when = datetime.strptime(meta["broadcastedOnDateTime"], "%Y-%m-%dT%H:%M:%S%z").astimezone(BERLIN)
    subtitles = [source["url"] for track in player.get("subtitles", []) for source in track.get("sources", [])
                 if source.get("kind") == "ebutt"]
    topics = [topic.strip() for topic in (meta.get("synopsis") or "").split(",") if topic.strip()]
    return Episode(when, url, subtitles[0] if subtitles else "", topics)


def ts_episodes() -> list[Episode]:
    series = fetch(TS_SERIES).decode("utf-8", "ignore")
    links = sorted(set(re.findall(r'href="(/tagesschau_in_einfacher_sprache/tse-\d+\.html)"', series)))
    episodes = []
    for link in links:
        url = TS_BASE + link
        episode = ts_episode(url, fetch(url).decode("utf-8", "ignore"))
        if episode:
            episodes.append(episode)
        time.sleep(0.5)
    return episodes


def ttml_lines(xml: str) -> list[str]:
    lines = []
    for paragraph in re.findall(r"<tt:p\b[^>]*>(.*?)</tt:p>", xml, re.S):
        text = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<tt:br\s*/>", " ", paragraph))).split())
        if text and not TS_CREDIT.match(text):
            lines.append(text)
    return lines


def ts_paragraphs(lines: list[str]) -> list[str]:
    for index, line in enumerate(lines):
        if TS_FILM.search(line) and index + 1 < len(lines):
            return [" ".join(lines[:index + 1]), " ".join(lines[index + 1:])]
    return [" ".join(lines)]


def ts_sections(lines: list[str]) -> tuple[list[list[str]], list[str], list[str]]:
    """News items, the closing headline recap and the weather; the greeting and transitions are dropped."""
    news, recap, weather, current, part = [], [], [], None, "intro"
    for line in lines:
        if TS_NEWS_START.match(line):
            current, part = [], "news"
            news.append(current)
        elif part == "news" and TS_NEWS_LEAD.search(line):
            start = len(current)  # the lead sentence may begin on earlier subtitle lines
            while start and not re.search(r"[.!?:]$", current[start - 1]):
                start -= 1
            lead = current[start:] + [line]
            del current[start:]
            current = lead
            news.append(current)
        elif TS_NEWS_END.match(line):
            part = "recap"
        elif TS_WEATHER.match(line):
            part = "weather"
        elif TS_OUTRO.match(line):
            part = "outro"
        elif part == "news":
            current.append(line)
        elif part == "recap":
            recap.append(line)
        elif part == "weather":
            weather.append(line)
    return news, recap, weather


def ts_markdown(episode: Episode, lines: list[str]) -> str:
    out = [f"# tagesschau in Einfacher Sprache – {episode.when:%d.%m.%Y, %H:%M} Uhr", "",
           f"Video: <{episode.url}> · Text: Untertitel des NDR", ""]
    news, recap, weather = ts_sections(lines)
    if not news:
        return "\n".join(out + [" ".join(lines), ""])
    topics = [topic.rstrip(".") for topic in episode.topics if topic != "Das Wetter"]
    headings = topics if len(topics) == len(news) else []
    for number, item in enumerate(news, start=1):
        out += [f"## {number}. {headings[number - 1]}" if headings else f"## Nachricht {number}", ""]
        for paragraph in ts_paragraphs(item):
            out += [paragraph, ""]
    # The spoken recap is often missing from the subtitles; the episode's official titles stand in for it.
    titles = [f"{number}. {title}" for number, title in enumerate(headings, start=1)]
    if not titles and recap:
        titles = [" ".join(recap)]
    if titles:
        out += ["## Und das waren unsere Nachrichten", "", *titles, ""]
    if weather:
        out += ["## Das Wetter", "", " ".join(weather), ""]
    return "\n".join(out)


def news_pdf(markdown: str, output: Path, day: date) -> None:
    body = subprocess.run(["pandoc", "-f", "gfm", "-t", "html5", "--wrap=none"], input=markdown,
                          capture_output=True, text=True, check=True).stdout
    document = (f'<!doctype html><html lang="de"><head><meta charset="utf-8"><title>{html.escape(output.stem)}'
                f"</title><style>{NEWS_CSS}</style></head><body>{body}</body></html>")
    print_pdf(document, output, f"{day:%Y-%m-%d}")


# DW Kurz und leicht

def dw_items(page: str) -> list[tuple[str, str]]:
    """(headline, text) per news item; the glossary after the blank line is left to the PDF."""
    items = []
    for headline, body in re.findall(r"<h2>(.*?)</h2>\s*<p>(.*?)</p>", page, re.S):
        text = re.split(r"<br\s*/?>\s*<br\s*/?>", body, maxsplit=1)[0]
        items.append((clean(headline), clean(text)))
    return items


def dw_time(pdf_text: str) -> tuple[date, str] | None:
    match = re.search(r"(\d{1,2})\. (\w+) (\d{4}), (\d{1,2}):(\d{2}) Uhr", pdf_text)
    if not match or match.group(2) not in MONTHS:
        return None
    day = date(int(match.group(3)), MONTHS[match.group(2)], int(match.group(1)))
    return day, f"{int(match.group(4)):02d}{match.group(5)}"


def dw_episode_links() -> list[tuple[date, str]]:
    series = fetch(DW_SERIES).decode("utf-8", "ignore")
    links = set(re.findall(r'href="(/de/(\d{8})-kurz-und-leicht-video-nachrichten-zum-deutschlernen/a-\d+)"', series))
    return sorted((datetime.strptime(stamp, "%d%m%Y").date(), DW_BASE + link) for link, stamp in links)


def dw_markdown(day: date, clock: str, url: str, pdf_name: str, items: list[tuple[str, str]]) -> str:
    out = [f"# DW Kurz und leicht – {day:%d.%m.%Y}, {clock[:2]}:{clock[2:]} Uhr", "",
           f"Video: <{url}> · PDF mit Glossar: [{pdf_name}](../PDF/{urllib.parse.quote(pdf_name)})", ""]
    for headline, text in items:
        out += [f"## {headline}", "", text, ""]
    return "\n".join(out)


def pdf_text(data: bytes) -> str:
    with tempfile.NamedTemporaryFile(suffix=".pdf") as handle:
        handle.write(data)
        handle.flush()
        return subprocess.run(["pdftotext", "-l", "1", handle.name, "-"], check=True, capture_output=True,
                              text=True).stdout


# Run

def save_tagesschau(since: date | None) -> list[str]:
    episodes = sorted(ts_episodes(), key=lambda episode: episode.when)
    chosen = [e for e in episodes if e.when.date() >= since] if since else episodes[-1:]
    report = []
    for episode in chosen:
        path = MARKDOWN / f"{episode.when:%Y%m%d %H%M} tagesschau.md"
        if not path.exists():
            if not episode.source:
                report.append(f"skipped {episode.when:%d.%m.%Y} tagesschau: no official subtitles")
                continue
            lines = ttml_lines(fetch(episode.source).decode("utf-8", "ignore"))
            path.write_text(ts_markdown(episode, lines), encoding="utf-8")
            report.append(f"added {path.name}")
        pdf = PDF / f"{path.stem}.pdf"
        if not pdf.exists():
            news_pdf(path.read_text(encoding="utf-8"), pdf, episode.when.date())
            report.append(f"added {pdf.name}")
    return report


def save_dw(since: date | None) -> list[str]:
    links = dw_episode_links()
    chosen = [link for link in links if link[0] >= since] if since else links[-1:]
    report = []
    for day, url in chosen:
        if list(MARKDOWN.glob(f"{day:%Y%m%d} * DWKL.md")):
            continue
        page = fetch(url).decode("utf-8", "ignore")
        pdf_url = re.search(r"https://static\.dw\.com/downloads/\d+/[^\"']+\.pdf", page)
        items = dw_items(page)
        if not pdf_url or not items:
            report.append(f"skipped {day:%d.%m.%Y} DWKL: page layout not recognised")
            continue
        pdf = fetch(pdf_url.group(0))
        stamp = dw_time(pdf_text(pdf))
        if not stamp or stamp[0] != day:
            report.append(f"skipped {day:%d.%m.%Y} DWKL: no date and time in the PDF")
            continue
        name = f"{day:%Y%m%d} {stamp[1]} DWKL"
        (PDF / f"{name}.pdf").write_bytes(pdf)
        (MARKDOWN / f"{name}.md").write_text(dw_markdown(day, stamp[1], url, f"{name}.pdf", items), encoding="utf-8")
        report.append(f"added {name}.md")
        time.sleep(0.5)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--days", type=int, help="every episode of the last N days (default: newest only)")
    args = parser.parse_args()
    since = date.today() - timedelta(days=args.days - 1) if args.days else None
    for folder in (MARKDOWN, PDF):
        folder.mkdir(parents=True, exist_ok=True)
    report = save_tagesschau(since) + save_dw(since)
    print("\n".join(report) if report else "nothing new")


if __name__ == "__main__":
    main()
