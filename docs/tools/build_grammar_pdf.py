#!/usr/bin/env python3
"""Build Grammatik/Grammatik.pdf (the whole grammar book), Spickzettel/Grammatikbegriffe.pdf and every other
Spickzettel/*.md cheatsheet as a one-page PDF of the same name.

  python3 docs/tools/build_grammar_pdf.py           rebuild both (after the grammar check passes)
  python3 docs/tools/build_grammar_pdf.py --check   exit 1 if a PDF is missing or older than its pages

The Markdown pages stay the source. Page order is the order of the "<level>: studied" tables in
Grammatik/README.md, so a page added there joins the PDF on the next build; Grammatikbegriffe.md
closes the book, right after Meine-Fehler.md. Every cheatsheet must fit on one page. Every build runs twice and must give
identical bytes. Needs pandoc and Google Chrome; no network.
"""

from __future__ import annotations

import hashlib
import html
import json
import os
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
from check_grammar_book import (BOOK, CHEATSHEET, COLOUR_RULES, COLOURS, GLOSSARY, MISTAKES, ROOT,  # noqa: E402
                                link_targets, plain, tables)

PDF = BOOK / "Grammatik.pdf"
PNG_DIR = CHEATSHEET.parent / "PNG"  # a phone copy of every cheatsheet
PNG_DPI = "150"
CHEATSHEET_PDF = CHEATSHEET.with_suffix(".pdf")
MANIFEST = BOOK / "Materials" / "pdf-build.json"
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
TITLE = "Grammatik — my German grammar book"
STUDIED_RE = re.compile(r"^(A1|A2|B1): studied$")
CHECKED_RE = re.compile(r"checked (\d{4}-\d{2}-\d{2})")
# Chrome stamps the build time into the PDF; it is replaced by the newest "checked" date of the pages.
PDF_DATE_RE = re.compile(rb"\(D:(\d{14})([^)]*)\)")
PDF_PAGE_RE = re.compile(rb"/Type\s*/Page\b")

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
.case { margin: 0 0 12pt; break-inside: avoid; }
.case h2 { margin: 0; padding: 4pt 8pt; border-radius: 5pt 5pt 0 0; color: #fff; border: 0; background: #4a5560; }
.write-here { height: 30mm; border: 1px dashed #9aa3ad; border-radius: 3pt; break-inside: avoid;
  background: repeating-linear-gradient(transparent 0 7.4mm, #dde1e6 7.4mm 7.5mm); }
"""

CHEATSHEET_CSS = """
@page { size: A4; margin: 11mm 14mm; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; font-size: 9.5pt; line-height: 1.3;
  color: #1f2328; margin: 0; }
h1 { font-size: 18pt; color: #1f3a5f; margin: 0 0 4pt; }
h2 { font-size: 8.5pt; letter-spacing: .12em; text-transform: uppercase; color: #8a6d1f; margin: 7pt 0 2pt; }
table { border-collapse: collapse; width: 100%; table-layout: fixed; }
table:not(:first-of-type) thead { display: none; }
th { font-size: 8pt; color: #777; font-weight: normal; text-align: left; padding: 0 5pt 2pt; }
td { border-top: 1px solid #dde1e6; padding: 2pt 5pt; vertical-align: top; }
th:nth-child(1), td:nth-child(1) { width: 40%; font-weight: 600; color: #1f3a5f; }
th:nth-child(2), td:nth-child(2) { width: 27%; }
td:nth-child(3) { font-style: italic; }
"""

# The learner's own sheet style: a coloured band per case, endings in their colour tag, **word** in bold.
SHEET_CSS = """
@page { size: A4; margin: 10mm 13mm; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; font-size: 10pt; line-height: 1.25;
  color: #222; margin: 0; }
h1 { font-size: 26pt; margin: 0 0 2pt; }
h1 + p { font-size: 11pt; color: #666; margin: 0 0 9pt; }
.case { margin: 0 0 9pt; break-inside: avoid; }
.case h2 { display: flex; justify-content: space-between; align-items: baseline; margin: 0; padding: 4pt 10pt;
  border-radius: 6pt 6pt 0 0; color: #fff; font-size: 14.5pt; background: #4a5560; }
.case h2 small { font-size: 10pt; font-weight: normal; }
table { border-collapse: collapse; width: 100%; border-bottom: 1.5px solid #bbb; }
th { background: #eee; text-align: left; padding: 3.5pt 7pt; font-size: 9.5pt; }
td { padding: 3pt 7pt; vertical-align: top; }
tbody tr:nth-child(even) { background: #f6f6f6; }
td:first-child { color: #666; }
th:not(:last-child), td:not(:last-child) { white-space: nowrap; }
th:last-child, td:last-child { border-left: 1.5px solid #ccc; }
td em { color: #888; font-size: 9pt; }
strong, b { font-weight: 700; color: #222; }
.foot { color: #666; font-size: 9.5pt; }
.foot p { margin: 3pt 0; }
"""


@dataclass
class Page:
    level: str
    topic: str
    path: Path
    source: str

    @property
    def slug(self) -> str:
        return f"{self.level or 'book'}-{self.path.stem}"  # unique across levels (A1/Zahlen vs a later A2/Zahlen)


# Each colour tag (<akk>en</akk>) and band (<div class="case akk">) comes from the one fixed list.
COLOUR_CSS = "".join(f"{tag} {{ color: {hex_}; font-weight: 700; }}\n.case.{tag} h2 {{ background: {hex_}; }}\n"
                     for tag, (_, hex_) in COLOURS.items())


def book_pages(book: Path = BOOK) -> list[Page]:
    """The colour rules, then the studied pages in index order, then my mistakes and the grammar words."""
    pages = [Page("", "Colours", COLOUR_RULES.resolve(), "")] if COLOUR_RULES.exists() else []
    for table in tables((book / "README.md").read_text(encoding="utf-8")):
        match = STUDIED_RE.match(table.section)
        if not match:
            continue
        for row in table.rows:
            links = link_targets(row[1])
            if links:
                pages.append(Page(match.group(1), plain(row[0]), (book / urllib.parse.unquote(links[0][1])).resolve(),
                                  plain(row[2]) if len(row) > 2 else ""))
    if (book / MISTAKES).exists():
        pages.append(Page("", "My recurring mistakes", (book / MISTAKES).resolve(), ""))
    if (book / GLOSSARY).exists():
        pages.append(Page("", "Grammar words", (book / GLOSSARY).resolve(), ""))
    return pages


def sheets(cheatsheet: Path = CHEATSHEET) -> list[Path]:
    """The learner's other cheatsheets: every Spickzettel/*.md beside Grammatikbegriffe.md."""
    return sorted(path for path in cheatsheet.parent.glob("*.md") if path.name != cheatsheet.name)


def inputs_digest(pages: list[Page], book: Path = BOOK, cheatsheet: Path = CHEATSHEET) -> str:
    digest = hashlib.sha256(Path(__file__).read_bytes())
    digest.update((book / "README.md").read_bytes())
    for page in pages:
        digest.update(os.path.relpath(page.path, book).encode("utf-8") + b"\0" + page.path.read_bytes())
    if cheatsheet.exists():
        digest.update(b"cheatsheet\0" + cheatsheet.read_bytes())
    for sheet in sheets(cheatsheet):
        digest.update(b"sheet\0" + sheet.name.encode("utf-8") + b"\0" + sheet.read_bytes())
    return digest.hexdigest()


def page_count(pdf: bytes) -> int:
    return len(PDF_PAGE_RE.findall(pdf))


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
    return f'<section class="topic" id="{page.slug}"><div class="level">{page.level or "All levels"}</div>{fragment}</section>'


def updated_on(pages: list[Page]) -> str:
    dates = [date for page in pages for date in CHECKED_RE.findall(page.path.read_text(encoding="utf-8"))]
    return max(dates) if dates else "2026-01-01"


def book_html(pages: list[Page]) -> str:
    slugs = {page.path: page.slug for page in pages}
    topics = [page for page in pages if page.level]
    levels = list(dict.fromkeys(page.level for page in topics))
    contents = []
    for level in levels:
        items = "".join(f'<li><a href="#{page.slug}">{html.escape(page.topic)}</a> '
                        f'<span class="from">· {html.escape(page.source)}</span></li>'
                        for page in topics if page.level == level)
        contents.append(f"<h2>{level}</h2><ol>{items}</ol>")
    first = next((i for i, page in enumerate(pages) if page.level), len(pages))
    links = [f'<h2><a href="#{page.slug}">{html.escape(page.topic)}</a></h2>' for page in pages]
    contents = [link for i, link in enumerate(links[:first])] + contents
    contents += [link for i, link in enumerate(links) if i >= first and not pages[i].level]
    cover = (f'<div class="cover"><h1>Grammatik</h1><div class="sub">my German grammar book</div>'
             f'<div class="meta">{" · ".join(levels)} · {len(topics)} topics · updated {updated_on(pages)}<br>'
             f"Built from the pages in Grammatik/ after every lesson.</div></div>")
    body = "".join(page_html(page, slugs) for page in pages)
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{TITLE}</title>'
            f"<style>{CSS}{COLOUR_CSS}</style></head><body>{cover}<div class=\"contents\"><h1>Contents</h1>{''.join(contents)}</div>"
            f"{body}</body></html>")


def cheatsheet_html(cheatsheet: Path = CHEATSHEET) -> str:
    result = subprocess.run(["pandoc", "-f", "gfm", "-t", "html5", "--wrap=none"],
                            input=cheatsheet.read_text(encoding="utf-8"), capture_output=True, text=True, check=True)
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{cheatsheet.stem}</title>'
            f"<style>{CHEATSHEET_CSS}{COLOUR_CSS}</style></head><body>{result.stdout}</body></html>")


def sheet_html(sheet: Path) -> str:
    result = subprocess.run(["pandoc", "-f", "gfm", "-t", "html5", "--wrap=none"],
                            input=sheet.read_text(encoding="utf-8"), capture_output=True, text=True, check=True)
    return (f'<!doctype html><html lang="de"><head><meta charset="utf-8"><title>{sheet.stem}</title>'
            f"<style>{SHEET_CSS}{COLOUR_CSS}</style></head><body>{result.stdout}</body></html>")


def sheet_date(sheet: Path) -> str:
    """The sheet's own "checked" date, so a sheet's PDF changes only when the sheet does."""
    dates = CHECKED_RE.findall(sheet.read_text(encoding="utf-8"))
    return max(dates) if dates else "2026-01-01"


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


def png_of(pdf: Path, output: Path) -> None:
    """A phone copy of a one-page PDF."""
    subprocess.run(["pdftoppm", "-png", "-r", PNG_DPI, "-singlefile", str(pdf), str(output.with_suffix(""))],
                   check=True, capture_output=True)


def tool_versions() -> dict[str, str]:
    pandoc = subprocess.run(["pandoc", "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
    chrome = subprocess.run([str(CHROME), "--version"], capture_output=True, text=True, check=True).stdout.strip()
    poppler = subprocess.run(["pdftoppm", "-v"], capture_output=True, text=True).stderr.splitlines()[0]
    return {"pandoc": pandoc, "chrome": chrome, "pdftoppm": poppler}


def stale_reason(book: Path = BOOK, cheatsheet: Path = CHEATSHEET) -> str | None:
    pdf, manifest, cheatsheet_pdf = book / PDF.name, book / "Materials" / MANIFEST.name, cheatsheet.with_suffix(".pdf")
    if not pdf.exists() or not manifest.exists():
        return "Grammatik.pdf has not been built yet"
    if not cheatsheet_pdf.exists():
        return f"{cheatsheet_pdf.name} has not been built yet"
    recorded = json.loads(manifest.read_text(encoding="utf-8"))
    if recorded.get("inputs") != inputs_digest(book_pages(book), book, cheatsheet):
        return "a grammar page, the index, the cheatsheet or the PDF layout changed after the last build"
    if recorded.get("pdf") != hashlib.sha256(pdf.read_bytes()).hexdigest():
        return "Grammatik.pdf differs from the recorded build"
    if recorded.get("cheatsheet") != hashlib.sha256(cheatsheet_pdf.read_bytes()).hexdigest():
        return f"{cheatsheet_pdf.name} differs from the recorded build"
    for sheet in sheets(cheatsheet):
        sheet_pdf = sheet.with_suffix(".pdf")
        if not sheet_pdf.exists():
            return f"{sheet_pdf.name} has not been built yet"
        if recorded.get("sheets", {}).get(sheet.name) != hashlib.sha256(sheet_pdf.read_bytes()).hexdigest():
            return f"{sheet_pdf.name} differs from the recorded build"
    for sheet in [cheatsheet] + sheets(cheatsheet):
        png = cheatsheet.parent / PNG_DIR.name / f"{sheet.stem}.png"
        if not png.exists() or recorded.get("png", {}).get(png.name) != hashlib.sha256(png.read_bytes()).hexdigest():
            return f"PNG/{png.name} is missing or differs from the recorded build"
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
    jobs = [(PDF, book_html(pages), updated_on(pages)), (CHEATSHEET_PDF, cheatsheet_html(), updated_on(pages))]
    jobs += [(sheet.with_suffix(".pdf"), sheet_html(sheet), sheet_date(sheet)) for sheet in sheets()]
    built = {}
    with tempfile.TemporaryDirectory() as tmp:
        for target, document, date in jobs:
            first, second = Path(tmp) / f"{target.stem}-a.pdf", Path(tmp) / f"{target.stem}-b.pdf"
            print_pdf(document, first, date)
            print_pdf(document, second, date)
            if first.read_bytes() != second.read_bytes():
                print(f"ERROR the {target.name} build is not deterministic; nothing written")
                return 1
            built[target] = first.read_bytes()
    one_page = [CHEATSHEET_PDF] + [sheet.with_suffix(".pdf") for sheet in sheets()]
    for target in one_page:
        pages_needed = page_count(built[target])
        if pages_needed != 1:
            print(f"ERROR {target.with_suffix('.md').relative_to(ROOT)} needs {pages_needed} pages; a cheatsheet fits "
                  "on one. Ask the learner what to shorten or split. Nothing written.")
            return 1
    pngs = {}
    with tempfile.TemporaryDirectory() as tmp:
        for target in one_page:
            pdf, first, second = Path(tmp) / target.name, Path(tmp) / "a.png", Path(tmp) / "b.png"
            pdf.write_bytes(built[target])
            png_of(pdf, first)
            png_of(pdf, second)
            if first.read_bytes() != second.read_bytes():
                print(f"ERROR the PNG of {target.name} is not deterministic; nothing written")
                return 1
            pngs[PNG_DIR / f"{target.stem}.png"] = first.read_bytes()
    for target, data in built.items():
        target.write_bytes(data)
    PNG_DIR.mkdir(exist_ok=True)
    for target, data in pngs.items():
        target.write_bytes(data)
    MANIFEST.write_text(json.dumps({
        "description": "Written by docs/tools/build_grammar_pdf.py. 'inputs' fingerprints the builder, README.md, "
                       "every page and the cheatsheet; the unit tests fail when it no longer matches, so the PDFs "
                       "never lag the pages.",
        "inputs": inputs_digest(pages), "pdf": hashlib.sha256(PDF.read_bytes()).hexdigest(),
        "cheatsheet": hashlib.sha256(CHEATSHEET_PDF.read_bytes()).hexdigest(),
        "sheets": {sheet.name: hashlib.sha256(sheet.with_suffix(".pdf").read_bytes()).hexdigest() for sheet in sheets()},
        "png": {path.name: hashlib.sha256(data).hexdigest() for path, data in sorted(pngs.items())},
        "pages": [os.path.relpath(page.path, BOOK) for page in pages], "tools": tool_versions(),
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{PDF.relative_to(ROOT)}: {len(pages)} pages; {CHEATSHEET_PDF.relative_to(ROOT)}: 1 page"
          + "".join(f"; {sheet.with_suffix('.pdf').relative_to(ROOT)}: 1 page" for sheet in sheets())
          + f"; {len(pngs)} PNG copies in {PNG_DIR.relative_to(ROOT)}")
    return 0


def main() -> int:
    if sys.argv[1:] == ["--check"]:
        reason = stale_reason()
        print(f"Out of date: {reason}. Run python3 docs/tools/build_grammar_pdf.py" if reason else "All PDFs are up to date")
        return 1 if reason else 0
    return build()


if __name__ == "__main__":
    sys.exit(main())
