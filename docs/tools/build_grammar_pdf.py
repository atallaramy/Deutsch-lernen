#!/usr/bin/env python3
"""Build Grammatik/Grammatik.pdf: the whole grammar book as one printable, clickable PDF.

  python3 docs/tools/build_grammar_pdf.py           rebuild (after the grammar check passes)
  python3 docs/tools/build_grammar_pdf.py --check   exit 1 if the PDF is missing or older than its pages

The Markdown pages stay the source. Page order is the order of the "<level>: studied" tables in
Grammatik/README.md, so a page added there joins the PDF on the next build. Every build runs twice
and must give identical bytes. Needs pandoc and Google Chrome; no network.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_grammar_book  # noqa: E402
from check_grammar_book import BOOK, ROOT, link_targets, plain, tables  # noqa: E402

PDF = BOOK / "Grammatik.pdf"
MANIFEST = BOOK / "Materials" / "pdf-build.json"
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
TITLE = "Grammatik — my German grammar book"
STUDIED_RE = re.compile(r"^(A1|A2|B1): studied$")
CHECKED_RE = re.compile(r"checked (\d{4}-\d{2}-\d{2})")
# Chrome stamps the build time into the PDF; it is replaced by the newest "checked" date of the pages.
PDF_DATE_RE = re.compile(rb"\(D:(\d{14})([^)]*)\)")

CSS = """
@page { size: A4; margin: 16mm 16mm 18mm;
  @bottom-center { content: counter(page); font: 9pt -apple-system, Helvetica, Arial, sans-serif; color: #888; } }
@page :first { @bottom-center { content: none; } }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; font-size: 10.5pt; line-height: 1.45;
  color: #1f2328; margin: 0; }
.cover { text-align: center; padding-top: 55mm; }
.cover h1 { font-size: 34pt; margin: 0; color: #1f3a5f; }
.cover .sub { font-size: 14pt; color: #555; margin: 4pt 0 30mm; }
.cover .meta { font-size: 9.5pt; color: #777; }
.contents { break-before: page; }
.contents h1 { font-size: 20pt; color: #1f3a5f; margin: 0 0 10pt; }
.contents h2 { font-size: 13pt; color: #1f3a5f; margin: 12pt 0 4pt; border-bottom: 1px solid #ddd; }
.contents ol { margin: 0; padding-left: 18pt; }
.contents li { margin: 4pt 0; }
.contents .from { color: #777; font-size: 9pt; }
.topic { break-before: page; }
.level { font-size: 8.5pt; letter-spacing: .12em; color: #8a6d1f; }
.topic h1 { font-size: 19pt; line-height: 1.2; margin: 2pt 0 4pt; color: #1f3a5f; }
.topic h1 + p { font-size: 9pt; color: #555; margin-top: 0; }
.topic h2 { font-size: 13pt; margin: 14pt 0 5pt; color: #1f3a5f; border-bottom: 1px solid #ddd; break-after: avoid; }
p, li { orphans: 2; widows: 2; }
table { border-collapse: collapse; width: 100%; font-size: 9.5pt; margin: 6pt 0 10pt; }
th, td { border: 1px solid #c9ced6; padding: 3pt 5pt; vertical-align: top; text-align: left; }
th { background: #eef2f7; }
tr { break-inside: avoid; }
a { color: #1f5fa8; text-decoration: none; }
code { font-size: 9pt; background: #f2f2f2; padding: 0 2pt; border-radius: 2pt; }
h2[id$="sentences-cards"] + ul { font-size: 8.5pt; color: #666; }
.write-here { height: 30mm; border: 1px dashed #9aa3ad; border-radius: 3pt; break-inside: avoid;
  background: repeating-linear-gradient(transparent 0 7.4mm, #dde1e6 7.4mm 7.5mm); }
"""


@dataclass
class Page:
    level: str
    topic: str
    path: Path
    source: str

    @property
    def slug(self) -> str:
        return f"{self.level}-{self.path.stem}"  # unique across levels (A1/Zahlen vs a later A2/Zahlen)


def book_pages(book: Path = BOOK) -> list[Page]:
    """Studied pages in index order."""
    pages = []
    for table in tables((book / "README.md").read_text(encoding="utf-8")):
        match = STUDIED_RE.match(table.section)
        if not match:
            continue
        for row in table.rows:
            links = link_targets(row[1])
            if links:
                pages.append(Page(match.group(1), plain(row[0]), (book / urllib.parse.unquote(links[0][1])).resolve(),
                                  plain(row[2]) if len(row) > 2 else ""))
    return pages


def inputs_digest(pages: list[Page], book: Path = BOOK) -> str:
    digest = hashlib.sha256(Path(__file__).read_bytes())
    digest.update((book / "README.md").read_bytes())
    for page in pages:
        digest.update(str(page.path.relative_to(book)).encode("utf-8") + b"\0" + page.path.read_bytes())
    return digest.hexdigest()


def rewrite_links(fragment: str, page: Page, slugs: dict[Path, str]) -> str:
    """Web links stay; links to book pages jump inside the PDF; links to local files (notes) become plain text."""
    def replace(match: re.Match) -> str:
        href, rest, text = html.unescape(match.group(1)), match.group(2), match.group(3)
        if href.startswith(("http://", "https://", "mailto:")):
            return match.group(0)
        if href.startswith("#"):
            return f'<a href="#{page.slug}-{html.escape(href[1:])}"{rest}>{text}</a>'
        target = (page.path.parent / urllib.parse.unquote(href.split("#")[0])).resolve()
        if target in slugs:
            return f'<a href="#{slugs[target]}"{rest}>{text}</a>'
        return f'<span class="local">{text}</span>'
    return re.sub(r'<a href="([^"]*)"([^>]*)>(.*?)</a>', replace, fragment, flags=re.S)


def page_html(page: Page, slugs: dict[Path, str]) -> str:
    result = subprocess.run(["pandoc", "-f", "gfm", "-t", "html5", "--wrap=none", f"--id-prefix={page.slug}-"],
                            input=page.path.read_text(encoding="utf-8"), capture_output=True, text=True, check=True)
    fragment = rewrite_links(result.stdout, page, slugs)
    # An unwritten "My rule in my own words" (the "…" placeholder) prints as a box to write in by hand.
    fragment = re.sub(r'(<h2 id="[^"]*my-rule-in-my-own-words">.*?</h2>\s*)<blockquote>\s*<p>…</p>\s*</blockquote>',
                      r'\1<div class="write-here"></div>', fragment, flags=re.S)
    return f'<section class="topic" id="{page.slug}"><div class="level">{page.level}</div>{fragment}</section>'


def updated_on(pages: list[Page]) -> str:
    dates = [date for page in pages for date in CHECKED_RE.findall(page.path.read_text(encoding="utf-8"))]
    return max(dates) if dates else "2026-01-01"


def book_html(pages: list[Page]) -> str:
    slugs = {page.path: page.slug for page in pages}
    levels = list(dict.fromkeys(page.level for page in pages))
    contents = []
    for level in levels:
        items = "".join(f'<li><a href="#{page.slug}">{html.escape(page.topic)}</a> '
                        f'<span class="from">· {html.escape(page.source)}</span></li>'
                        for page in pages if page.level == level)
        contents.append(f"<h2>{level}</h2><ol>{items}</ol>")
    cover = (f'<div class="cover"><h1>Grammatik</h1><div class="sub">my German grammar book</div>'
             f'<div class="meta">{" · ".join(levels)} · {len(pages)} topics · updated {updated_on(pages)}<br>'
             f"Built from the pages in Grammatik/ after every lesson.</div></div>")
    body = "".join(page_html(page, slugs) for page in pages)
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{TITLE}</title>'
            f"<style>{CSS}</style></head><body>{cover}<div class=\"contents\"><h1>Contents</h1>{''.join(contents)}</div>"
            f"{body}</body></html>")


def print_pdf(document: str, output: Path, date: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "grammatik.html"
        source.write_text(document, encoding="utf-8")
        # A separate profile keeps the learner's open Chrome untouched.
        command = [str(CHROME), "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
                   "--disable-extensions", f"--user-data-dir={Path(tmp) / 'profile'}", "--no-pdf-header-footer",
                   "--generate-pdf-document-outline", f"--print-to-pdf={output}", source.as_uri()]
        # Headless Chrome on macOS can stay alive after printing; stop it once it reports the file as written.
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        written, log = False, []
        deadline = time.monotonic() + 120
        try:
            for line in process.stderr:
                log.append(line)
                if "bytes written to file" in line:
                    written = True
                    break
                if time.monotonic() > deadline:
                    break
        finally:
            process.kill()
            process.wait()
        if not written or not output.exists():
            raise RuntimeError("Chrome did not write the PDF:\n" + "".join(log[-20:]))
    stamp = date.replace("-", "").encode() + b"000000"
    data = output.read_bytes()
    output.write_bytes(PDF_DATE_RE.sub(lambda m: b"(D:" + stamp + m.group(2) + b")", data))


def tool_versions() -> dict[str, str]:
    pandoc = subprocess.run(["pandoc", "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
    chrome = subprocess.run([str(CHROME), "--version"], capture_output=True, text=True, check=True).stdout.strip()
    return {"pandoc": pandoc, "chrome": chrome}


def stale_reason(book: Path = BOOK) -> str | None:
    pdf, manifest = book / PDF.name, book / "Materials" / MANIFEST.name
    if not pdf.exists() or not manifest.exists():
        return "Grammatik.pdf has not been built yet"
    recorded = json.loads(manifest.read_text(encoding="utf-8"))
    if recorded.get("inputs") != inputs_digest(book_pages(book), book):
        return "a grammar page, the index or the PDF layout changed after the last build"
    if recorded.get("pdf") != hashlib.sha256(pdf.read_bytes()).hexdigest():
        return "Grammatik.pdf differs from the recorded build"
    return None


def build() -> int:
    missing = [name for name, found in (("pandoc", shutil.which("pandoc")), ("Google Chrome", CHROME.exists())) if not found]
    if missing:
        print(f"Not built: {' and '.join(missing)} not found.")
        return 1
    report = check_grammar_book.check()
    if report.errors:
        for error in report.errors:
            print("ERROR", error)
        print("Not built: fix the grammar book first (python3 docs/tools/check_grammar_book.py).")
        return 1
    pages = book_pages()
    document = book_html(pages)
    with tempfile.TemporaryDirectory() as tmp:
        first, second = Path(tmp) / "a.pdf", Path(tmp) / "b.pdf"
        print_pdf(document, first, updated_on(pages))
        print_pdf(document, second, updated_on(pages))
        if first.read_bytes() != second.read_bytes():
            print("ERROR the PDF build is not deterministic; nothing written")
            return 1
        PDF.write_bytes(first.read_bytes())
    MANIFEST.write_text(json.dumps({
        "description": "Written by docs/tools/build_grammar_pdf.py. 'inputs' fingerprints the builder, README.md and "
                       "every page; the unit tests fail when it no longer matches, so the PDF never lags the pages.",
        "inputs": inputs_digest(pages), "pdf": hashlib.sha256(PDF.read_bytes()).hexdigest(),
        "pages": [str(page.path.relative_to(BOOK)) for page in pages], "tools": tool_versions(),
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{PDF.relative_to(ROOT)}: {len(pages)} topics")
    return 0


def main() -> int:
    if sys.argv[1:] == ["--check"]:
        reason = stale_reason()
        print(f"Out of date: {reason}. Run python3 docs/tools/build_grammar_pdf.py" if reason else "Grammatik.pdf is up to date")
        return 1 if reason else 0
    return build()


if __name__ == "__main__":
    sys.exit(main())
