#!/usr/bin/env python3
"""Download and verify DW's English script/vocabulary PDFs for every A1 lesson.

DW publishes these documents lesson by lesson. This downloader creates the
lesson-folder structure first, keeps files idempotent, and records the exact
official static.dw.com URL and local location in a manifest for later browsing.
"""

from __future__ import annotations

import json
import re
import tempfile
import time
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
A1 = ROOT / "DW Deutsch lernen" / "A1"
MANIFEST = A1 / "a1-script-vocabulary-manifest.json"
URL_LIST = (
    "https://gist.githubusercontent.com/eduardvasilache/"
    "8d88ae7b549cc34a201bd8fc52520307/raw/"
    "50fdaa32e0ae6e6769973d5ae069001eeba4d90d/"
    "dw-scripts-nico-a1-a2-b1.txt"
)
PATTERN = re.compile(
    r"https://(?:learngerman|static)\.dw\.com/downloads/(\d+)/"
    r"nicos-weg-a1-e(\d+)-l(\d+)-manuskript-und-wortschatz-englisch\.pdf"
)
EXPECTED_LESSONS = 76
E0_FOLDERS = {
    1: "01_Hallo",
    2: "02_Kein Problem",
    3: "03_Tschüs",
    4: "04_Von A bis Z",
}


def fetch(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 (lesson-material downloader)"})
    with urlopen(request, timeout=60) as response:
        return response.read()


def source_urls() -> list[tuple[int, int, str]]:
    entries = {(int(unit), int(lesson), f"https://static.dw.com/downloads/{asset}/nicos-weg-a1-e{int(unit)}-l{int(lesson)}-manuskript-und-wortschatz-englisch.pdf")
               for asset, unit, lesson in PATTERN.findall(fetch(URL_LIST).decode("utf-8"))}
    expected = {(unit, lesson) for unit in range(19) for lesson in range(1, 5)}
    found = {(unit, lesson) for unit, lesson, _ in entries}
    if found != expected:
        missing = sorted(expected - found)
        unexpected = sorted(found - expected)
        raise RuntimeError(f"A1 manifest is incomplete; missing={missing}, unexpected={unexpected}")
    if len(entries) != EXPECTED_LESSONS:
        raise RuntimeError(f"Expected {EXPECTED_LESSONS} A1 lessons, found {len(entries)}.")
    return sorted(entries)


def lesson_folder(unit: int, lesson: int) -> Path:
    unit_folder = A1 / ("01_Intro_zu_A1" if unit == 0 else f"{unit + 1:02d}")
    lesson_name = E0_FOLDERS[lesson] if unit == 0 else f"{lesson:02d}_Lesson_{lesson:02d}"
    return unit_folder / lesson_name


def valid_pdf(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 1024 and path.read_bytes()[:5] == b"%PDF-"


def download(url: str, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if valid_pdf(destination):
        return "existing"
    payload = fetch(url)
    if not payload.startswith(b"%PDF-"):
        raise RuntimeError(f"DW did not return a PDF for {url}")
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as temporary:
        temporary.write(payload)
        temporary_path = Path(temporary.name)
    temporary_path.replace(destination)
    if not valid_pdf(destination):
        raise RuntimeError(f"Downloaded file failed PDF validation: {destination}")
    return "downloaded"


def main() -> None:
    entries = source_urls()
    downloaded = 0
    existing = 0
    records = []
    for unit, lesson, url in entries:
        folder = lesson_folder(unit, lesson)
        filename = folder / "Materials" / "Script and vocabulary (English).pdf"
        status = download(url, filename)
        downloaded += status == "downloaded"
        existing += status == "existing"
        records.append({
            "unit": unit,
            "lesson": lesson,
            "url": url,
            "file": str(filename.relative_to(ROOT)),
        })
    MANIFEST.write_text(json.dumps({
        "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "description": "Official DW Nicos Weg A1 English script/vocabulary PDFs.",
        "sourceList": URL_LIST,
        "lessons": records,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"A1 scripts/vocabulary: {downloaded} downloaded, {existing} already present, {len(records)} total.")


if __name__ == "__main__":
    main()
