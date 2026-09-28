#!/usr/bin/env python3
"""Snapshot official lesson sources into Materials/ so deck builds can verify contexts offline.

Network step, run manually: `python3 ANKI/harvest_sources.py --lesson <lesson-id>` (or `--all`).
Needs `pdftotext` (poppler) for PDF sources and `pandoc` for a DW lesson's readable `Materials/lesson-pages.md`.
Builders never use the network.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LESSONS = ROOT / "ANKI" / "lesson-vocabulary.json"
USER_AGENT = "Mozilla/5.0 (German-learning source snapshot)"
APOLLO_RE = re.compile(r"window.__APOLLO_STATE__\s*=\s*(\{.*?\});?\s*</script>", re.S)
FIGURE_RE = re.compile(r"<figure\b.*?</figure>", re.S)  # images; their caption is only a photo credit ("null DW")
LESSON_PAGES = "lesson-pages.md"


def fetch(url: str) -> bytes:
    request = urllib.request.Request(urllib.parse.quote(url, safe=":/?=&%#"), headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def clean_text(fragment: str) -> str:
    text = re.sub(r"<br\s*/?>|</p>|</li>", "\n", FIGURE_RE.sub("", fragment))
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    return "\n".join(re.sub(r"[ \t ]+", " ", line).strip() for line in text.splitlines() if line.strip())


def pdf_lines(path: Path) -> list[str]:
    result = subprocess.run(["pdftotext", "-layout", str(path), "-"], check=True, capture_output=True, text=True)
    lines = []
    for raw in result.stdout.splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        if line and not line.startswith("Deutsch zum Mitnehmen") and not re.match(r"^©|^Seite \d+ von \d+$", line):
            lines.append(line)
    return lines


def parse_apollo(page: str, url: str) -> dict:
    match = APOLLO_RE.search(page)
    if not match:
        raise RuntimeError(f"No embedded data at {url}")
    return json.loads(match.group(1))


def apollo(url: str) -> dict:
    return parse_apollo(fetch(url).decode("utf-8", "ignore"), url)


def dw_knowledge_page(url: str) -> dict:
    """Grammar (gr-) and culture (rs-) pages: the page's own Knowledge text, plus its HTML for lesson-pages.md."""
    page_id = url.rsplit("-", 1)[-1]
    state = apollo(url)
    knowledge = state.get(f"Knowledge:{page_id}", {})
    texts = [clean_text(knowledge[field]) for field in ("name", "teaser", "text") if isinstance(knowledge.get(field), str)]
    return {"id": url.rsplit("/", 1)[-1], "url": url, "title": knowledge.get("name") or "", "texts": [t for t in texts if t],
            "html": FIGURE_RE.sub("", knowledge.get("text") or "")}


def dw_vocabulary(state: dict) -> list[dict]:
    """The lesson's vocabulary page (/lv) in page order: German, official English, and forms (plural or principal parts)."""
    lesson = next(value for key, value in state.items() if key.startswith("Lesson:"))
    items = []
    for ref in lesson.get("vocabularies") or []:
        knowledge = state[ref["__ref"]]
        items.append({"id": knowledge["id"], "german": clean_text(knowledge.get("name") or ""),
                      "english": clean_text(knowledge.get("text") or ""), "forms": clean_text(knowledge.get("subTitle") or "")})
    return items


def dw_lesson(lesson_url: str) -> dict:
    """Collect a DW lesson's vocabulary page, correct exercise texts, grammar and culture pages."""
    base = lesson_url.rstrip("/")
    lesson_id = re.search(r"/l-(\d+)", base).group(1)
    page = fetch(base + "/lv").decode("utf-8", "ignore")
    vocabulary = {"url": base + "/lv", "items": dw_vocabulary(parse_apollo(page, base + "/lv"))}
    if not vocabulary["items"]:
        raise RuntimeError(f"No vocabulary items at {vocabulary['url']}; check the lesson URL")
    paths = sorted(set(re.findall(rf'/en/[^"\s]*/l-{lesson_id}/e-\d+', page)))
    knowledge_paths = sorted(set(re.findall(rf'/en/[^"\s]*/l-{lesson_id}/(?:gr|rs)-\d+', page)))
    pages = [dw_knowledge_page("https://learngerman.dw.com" + path) for path in knowledge_paths]
    exercises = []
    for path in paths:
        url = "https://learngerman.dw.com" + path
        state = apollo(url)
        exercise = next(value for key, value in state.items() if key.startswith("Exercise:"))
        texts: list[str] = []
        if exercise.get("inputText"):
            texts.append(clean_text(exercise["inputText"]))
        for key, value in sorted(state.items()):
            if key.startswith("Inquiry:"):
                for field in ("text", "inquiryText"):
                    if value.get(field):
                        texts.append(clean_text(value[field]))
            elif key.startswith("Alternative:") and value.get("isCorrect") and value.get("alternativeText"):
                texts.append(clean_text(value["alternativeText"]))
        tags = sorted(set(re.findall(r'data-title="([^"]+)"', json.dumps(state, ensure_ascii=False))))
        exercises.append({"id": path.rsplit("/", 1)[-1], "url": url, "title": exercise.get("name", ""),
                          "texts": [text for text in texts if text], "vocabularyTags": tags})
        time.sleep(0.3)
    return {"lessonUrl": base, "vocabulary": vocabulary, "exercises": exercises, "pages": pages}


def markdown_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def html_to_markdown(fragment: str) -> str:
    """Pandoc GFM; paragraphs inside table cells are joined with " · " so pandoc can emit a pipe table, not raw HTML."""
    fragment = re.sub(r'<span id="ck_editor_caret_marker"[^>]*></span>', "", fragment)
    fragment = re.sub(r"<td([^>]*)>(.*?)</td>", lambda m: "<td%s>%s</td>" % (m.group(1), " · ".join(
        part.strip() for part in re.split(r"</?p[^>]*>", re.sub(r"<br\s*/?>", " ", m.group(2))) if part.strip())),
        fragment, flags=re.S)
    result = subprocess.run(["pandoc", "-f", "html", "-t", "gfm", "--wrap=none", "--shift-heading-level-by=2"],
                            input=fragment, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def lesson_pages_markdown(label: str, record: dict, harvested_on: str) -> str:
    """Readable copy of a DW lesson's vocabulary, grammar and culture pages (the snapshot holds the same text)."""
    parts = [f"# {label}: vocabulary, grammar and culture pages", "",
             f"Copied from learngerman.dw.com on {harvested_on} by `ANKI/harvest_sources.py`; do not edit, rerun it. "
             "The same text is in `source-snapshot.json`.", "",
             "## Vocabulary", "", f"<{record['vocabulary']['url']}>", "",
             "| German | English | Forms |", "|---|---|---|"]
    parts += [f"| {markdown_cell(item['german'])} | {markdown_cell(item['english'])} | {markdown_cell(item['forms'])} |"
              for item in record["vocabulary"]["items"]]
    for prefix, heading in (("gr-", "Grammar"), ("rs-", "Culture")):
        for page in record["pages"]:
            if page["id"].startswith(prefix):
                parts += ["", f"## {heading}: {page['title'].strip()}", "", f"<{page['url']}>", "", html_to_markdown(page["html"])]
    return "\n".join(parts) + "\n"


def lesson_pages_for(lesson: dict) -> tuple[Path, str] | None:
    """(path, content) of a DW lesson's Materials/lesson-pages.md, rendered from its saved snapshot."""
    target = ROOT / lesson["snapshot"]
    snapshot = json.loads(target.read_text(encoding="utf-8")) if target.exists() else {"sources": []}
    record = next((source for source in snapshot.get("sources", []) if source.get("kind") == "dw-exercises"), None)
    if not record or "vocabulary" not in record:
        return None
    label = f"DW {lesson['level']} E{lesson['unit']} L{lesson['lesson']} · {lesson['title']}"
    return target.parent / LESSON_PAGES, lesson_pages_markdown(label, record, snapshot["harvestedOn"])


def write_lesson_pages(lesson: dict) -> None:
    rendered = lesson_pages_for(lesson)
    if rendered:
        path, content = rendered
        path.write_text(content, encoding="utf-8")
        print(f"readable copy {path.relative_to(ROOT)}")


def snapshot_source(source: dict) -> dict:
    kind = source["kind"]
    record = {key: source[key] for key in ("id", "kind", "url") if key in source}
    if kind in {"dw-script-pdf", "vhs-pdf"}:
        local = ROOT / source["localFile"]
        if not local.exists():
            local.parent.mkdir(parents=True, exist_ok=True)
            payload = fetch(source["url"])
            if not payload.startswith(b"%PDF-"):
                raise RuntimeError(f"{source['url']} did not return a PDF")
            local.write_bytes(payload)
        record["localFile"] = source["localFile"]
        record["sha256"] = hashlib.sha256(local.read_bytes()).hexdigest()
        record["lines"] = pdf_lines(local)
    elif kind == "dw-exercises":
        record.update(dw_lesson(source["url"]))
    else:
        raise RuntimeError(f"Unknown source kind: {kind}")
    return record


GLOSS_SNAPSHOT = ROOT / "ANKI" / "gloss-snapshot.json"
OFFICIAL_GLOSS_ORIGINS = {"dw-glossary", "dw-culture-page", "vhs-vocabulary-trainer"}


def needs_gloss_check(entry: dict) -> bool:
    return not OFFICIAL_GLOSS_ORIGINS & set(entry.get("origin", [])) and entry.get("pos") not in {"name"}


def gloss_terms(entry: dict) -> list[str]:
    if entry.get("glossLookup"):
        return list(entry["glossLookup"])
    return [re.sub(r"[.!?]+$", "", entry["lemma"]).strip()]


def wiktionary(term: str) -> dict:
    url = "https://en.wiktionary.org/api/rest_v1/page/definition/" + urllib.parse.quote(term.replace(" ", "_"))
    request = urllib.request.Request(url, headers={"User-Agent": "GermanStudyNotes/1.0 (personal learning project; low volume)"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = json.loads(response.read())
            break
        except urllib.error.HTTPError as error:
            if error.code == 429 and attempt < 5:
                time.sleep(2 ** attempt * 2)  # Wikimedia rate limit: back off and retry
                continue
            return {"url": url, "status": error.code, "definitions": []}
    definitions = [{"pos": block.get("partOfSpeech", ""), "text": clean_text(item["definition"])}
                   for block in payload.get("de", []) for item in block.get("definitions", []) if item.get("definition")]
    return {"url": f"https://en.wiktionary.org/wiki/{urllib.parse.quote(term.replace(' ', '_'))}#German",
            "status": 200, "definitions": definitions}


def dictcc(term: str) -> dict:
    """Second dictionary for phrases Wiktionary lacks: keep only pairs whose German side is the term itself."""
    url = "https://www.dict.cc/?s=" + urllib.parse.quote_plus(term)
    page = fetch(url).decode("utf-8", "ignore")
    columns = [re.findall(r'"((?:[^"\\]|\\.)*)"', match.group(1)) if match else []
               for match in (re.search(r"var c1Arr = new Array\((.*?)\);", page), re.search(r"var c2Arr = new Array\((.*?)\);", page))]
    key = re.sub(r"[^\w ]", "", term).casefold().strip()
    definitions = [{"pos": "", "text": english.replace("\\'", "'")} for english, german in zip(*columns)
                   if english and re.sub(r"[^\w ]", "", german).casefold().strip() == key]
    return {"url": url, "status": 200 if definitions else 404, "definitions": definitions, "dictionary": "dict.cc"}


def snapshot_glosses(data: dict) -> None:
    """English meanings that no official glossary supplies are checked against en.wiktionary."""
    existing = json.loads(GLOSS_SNAPSHOT.read_text(encoding="utf-8"))["terms"] if GLOSS_SNAPSHOT.exists() else {}
    terms = sorted({term for course in data["courses"] for lesson in course["lessons"]
                    for entry in lesson.get("entries", []) if needs_gloss_check(entry) for term in gloss_terms(entry)})
    for term in terms:
        if term not in existing or existing[term]["status"] not in (200, 404) or \
                (not existing[term]["definitions"] and "dictionary" not in existing[term]):
            record = {**wiktionary(term), "dictionary": "en.wiktionary"}
            if not record["definitions"]:
                time.sleep(1.5)
                record = dictcc(term)
            existing[term] = {**record, "fetchedOn": time.strftime("%Y-%m-%d")}
            time.sleep(1)
            print(f"gloss {term}: {len(existing[term]['definitions'])} German definition(s)")
    GLOSS_SNAPSHOT.write_text(json.dumps({
        "description": "Dictionary definitions (en.wiktionary, else dict.cc) for meanings that no official course glossary "
                       "supplies (captured by ANKI/harvest_sources.py --glosses).",
        "terms": dict(sorted(existing.items())),
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--lesson", action="append", help="lesson id from lesson-vocabulary.json")
    group.add_argument("--all", action="store_true", help="every lesson that declares sources")
    group.add_argument("--glosses", action="store_true", help="check non-official English meanings against en.wiktionary")
    group.add_argument("--pages", action="store_true",
                       help="offline: rewrite each DW lesson's Materials/lesson-pages.md from its saved snapshot")
    args = parser.parse_args()

    data = json.loads(LESSONS.read_text(encoding="utf-8"))
    if args.glosses:
        snapshot_glosses(data)
        return
    if args.pages:
        for course in data["courses"]:
            for lesson in course["lessons"]:
                if course["id"] == "dw-nicos-weg":
                    write_lesson_pages(lesson)
        return
    snapshots: dict[str, list[dict]] = {}
    harvested: list[dict] = []
    lesson_ids = set(args.lesson or [])
    for course in data["courses"]:
        for lesson in course["lessons"]:
            if args.all or lesson["id"] in lesson_ids:
                bucket = snapshots.setdefault(lesson["snapshot"], [])
                bucket.extend(source for source in lesson.get("sources", []) if source not in bucket)
                harvested.append(lesson)
    missing = lesson_ids - {lesson["id"] for course in data["courses"] for lesson in course["lessons"]}
    if missing:
        sys.exit(f"Unknown lesson id(s): {', '.join(sorted(missing))}")

    for snapshot_path, sources in snapshots.items():
        target = ROOT / snapshot_path
        existing = json.loads(target.read_text(encoding="utf-8")) if target.exists() else {"sources": []}
        by_id = {source["id"]: source for source in existing["sources"]}
        for source in sources:
            by_id[source["id"]] = snapshot_source(source)
            print(f"snapshot {snapshot_path} :: {source['id']}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({
            "description": "Official source text captured by ANKI/harvest_sources.py for offline context verification.",
            "harvestedOn": time.strftime("%Y-%m-%d"),
            "sources": [by_id[key] for key in sorted(by_id)],
        }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for lesson in harvested:
        write_lesson_pages(lesson)


if __name__ == "__main__":
    main()
