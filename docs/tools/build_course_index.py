#!/usr/bin/env python3
"""Build docs/course-index/: lesson-by-lesson titles, goals, grammar topics and official links.

Network step, run manually when a course changes: `python3 docs/tools/build_course_index.py`.
Needs `pdftotext` (poppler) for the VHS grammar lists. Output is reference material only;
it is never used by the deck builders.
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "course-index"
USER_AGENT = "Mozilla/5.0 (course index for personal study)"
DW_SCRIPT_LIST = ("https://gist.githubusercontent.com/eduardvasilache/8d88ae7b549cc34a201bd8fc52520307/raw/"
                  "50fdaa32e0ae6e6769973d5ae069001eeba4d90d/dw-scripts-nico-a1-a2-b1.txt")
DW_COURSES = [
    ("dw-nicos-weg-a1", "A1", "https://learngerman.dw.com/en/nicos-weg/c-36519789", "englisch"),
    ("dw-nicos-weg-a2", "A2", "https://learngerman.dw.com/en/nicos-weg/c-36519797", "englisch"),
    ("dw-nicos-weg-b1", "B1", "https://learngerman.dw.com/de/nicos-weg/c-36519718", "deutsch"),
]
VHS_LEVELS = {
    "A1": {"grammar": "https://www.vhs-lernportal.de/wws/bin/4007530-4015506-1-dvv_grammatiklisten_a1.pdf",
           "words": "https://www.vhs-lernportal.de/wws/bin/4007498-4014834-1-dvv_wortschatzlisten_a1.pdf",
           "films": "https://www.vhs-lernportal.de/wws/bin/4007498-4014866-1-dvv_filmskripte_a1.pdf",
           "portal": "https://a1.vhs-lernportal.de/"},
    "A2": {"grammar": "https://www.vhs-lernportal.de/wws/bin/4007530-4015506-2-dvv_grammatiklisten_a2.pdf",
           "words": "https://www.vhs-lernportal.de/wws/bin/4007498-4014834-2-dvv_wortschatzlisten_a2.pdf",
           "films": "https://www.vhs-lernportal.de/wws/bin/4007498-4014866-2-dvv_filmskripte_a2.pdf",
           "portal": "https://a2.vhs-lernportal.de/"},
    "B1": {"grammar": "https://www.vhs-lernportal.de/wws/bin/4007530-4015506-3-dvv_grammatiklisten_b1.pdf",
           "words": "https://www.vhs-lernportal.de/wws/bin/4007498-4014834-3-dvv_wortschatzlisten_b1.pdf",
           "films": "https://www.vhs-lernportal.de/wws/bin/4007498-4014866-3-dvv_filmskripte_b1.pdf",
           "portal": "https://b1.vhs-lernportal.de/"},
}


def fetch(url: str) -> bytes:
    request = urllib.request.Request(urllib.parse.quote(url, safe=":/?=&%#"), headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def apollo(url: str) -> dict:
    page = fetch(url).decode("utf-8", "ignore")
    return json.loads(re.search(r"window.__APOLLO_STATE__\s*=\s*(\{.*?\});?\s*</script>", page, re.S).group(1))


def dw_script_urls() -> dict[tuple[str, int, int, str], str]:
    pattern = re.compile(r"https://(?:learngerman|static)\.dw\.com/downloads/\d+/nicos-weg-(a1|a2|b1)-e(\d+)-l(\d+)-"
                         r"manuskript-und-wortschatz-(englisch|deutsch)\.pdf")
    return {(m.group(1).upper(), int(m.group(2)), int(m.group(3)), m.group(4)): m.group(0)
            for m in pattern.finditer(fetch(DW_SCRIPT_LIST).decode("utf-8"))}


def dw_course(course_id: str, level: str, url: str, language: str, scripts: dict) -> dict:
    state = apollo(url)
    course = next(value for key, value in state.items() if key.startswith("Course:"))
    lessons, unit, lesson_number, previous_group = [], -1, 0, None
    for link in course['contentLinks({"targetTypes":"LESSON"})']:
        content = state[link["__ref"]]
        lesson = state[content["target"]["__ref"]]
        group = content.get("groupName") or ""
        if content.get("additionalInformation") == "final_test":
            numbering = None
        else:
            if group != previous_group:
                unit, lesson_number, previous_group = unit + 1, 0, group
            lesson_number += 1
            numbering = (unit, lesson_number)
        script = scripts.get((level, *numbering, language)) if numbering else None
        lessons.append({
            "unit": numbering[0] if numbering else None, "lesson": numbering[1] if numbering else None,
            "unitTitle": group, "title": lesson.get("shortTitle"), "goal": lesson.get("learningTargetHeadline"),
            "grammar": lesson.get("grammarDescription"), "url": "https://learngerman.dw.com" + lesson["namedUrl"],
            "script": script,
        })
    return {"id": course_id, "title": f"DW Nicos Weg {level}", "level": level, "courseUrl": url, "lessons": lessons}


def vhs_grammar(level: str, info: dict) -> dict:
    """Split the two-column *Themen und Grammatik* table by the column positions of its header row."""
    with tempfile.TemporaryDirectory() as temp:
        pdf = Path(temp) / "grammar.pdf"
        pdf.write_bytes(fetch(info["grammar"]))
        layout = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], check=True, capture_output=True, text=True).stdout
    lessons: list[dict] = []
    topic_col = grammar_col = None
    in_header = False

    def add(bucket: list[str], text: str) -> None:
        text = re.sub(r"\s+", " ", text).strip()
        if text.startswith("••"):
            bucket.append(text[2:].strip())
        elif text == "Wiederholung":
            bucket.append("Wiederholung (review):")
        elif bucket and not bucket[-1].endswith(":"):
            joiner = "" if bucket[-1].endswith("\u00ad") else " "
            bucket[-1] = re.sub(r"\s+", " ", bucket[-1].rstrip("\u00ad") + joiner + text).strip()
        elif text:
            bucket.append(text)

    for line in layout.splitlines():
        if "Themen und Grammatik" in line:
            in_header = True
            continue
        if "Themen der Lektion" in line and "Grammatik" in line:
            topic_col, grammar_col = line.index("Themen der Lektion"), line.index("Grammatik")
            in_header = False
            continue
        if in_header or topic_col is None or not line.strip() or line.lstrip().startswith("©"):
            continue
        number = re.match(r"^(\d{1,2})\s", line)
        if number:
            lessons.append({"lesson": int(number.group(1)), "title": [], "topics": [], "grammar": []})
        if not lessons:
            continue
        left = line[:topic_col].strip()
        if number:
            left = left[len(number.group(1)):].strip()
        middle, right = line[topic_col:grammar_col].strip(), line[grammar_col:].strip()
        if left:
            lessons[-1]["title"].append(left)
        add(lessons[-1]["topics"], middle)
        add(lessons[-1]["grammar"], right)
    for lesson in lessons:
        title = " ".join(lesson["title"]).replace("\u00ad ", "").replace("\u00ad", "")
        lesson["title"] = re.sub(r"(\w)- ([a-zäöü])", r"\1\2", title)
        lesson["topics"] = [item.strip() for item in lesson["topics"]]
        lesson["grammar"] = [item.strip() for item in lesson["grammar"]]
    return {"id": f"vhs-{level.lower()}", "title": f"VHS-Lernportal Deutschkurs {level}", "level": level, **info, "lessons": lessons}


def dw_markdown(course: dict) -> str:
    lines = [f"# {course['title']} — lesson index", "",
             f"Official course page: <{course['courseUrl']}>. Generated by `docs/tools/build_course_index.py` from DW's own "
             "course data (lesson title, communicative goal, grammar topic) and the script-PDF list.", "",
             "| Unit · Lesson | Title | Goal | Grammar | Links |", "|---|---|---|---|---|"]
    for lesson in course["lessons"]:
        number = f"E{lesson['unit']} L{lesson['lesson']}" if lesson["unit"] is not None else "—"
        links = f"[lesson]({lesson['url']})" + (f" · [script PDF]({lesson['script']})" if lesson["script"] else "")
        lines.append(f"| {number} · {lesson['unitTitle']} | {lesson['title']} | {lesson['goal'] or ''} | "
                     f"{lesson['grammar'] or ''} | {links} |")
    return "\n".join(lines) + "\n"


def vhs_markdown(course: dict) -> str:
    lines = [f"# {course['title']} — topics and grammar per lesson", "",
             f"- Portal (free login): <{course['portal']}>",
             f"- Official *Themen und Grammatik* list: <{course['grammar']}>",
             f"- Official *Wortschatzlisten* (per lesson, with articles and plurals): <{course['words']}>",
             f"- Official *Filmskripte* (Nasrins Welt): <{course['films']}>", "",
             "Copied from the official grammar list by column position (lesson title | topics | grammar). "
             "Open the PDF if a line looks split oddly.", ""]
    for lesson in course["lessons"]:
        lines.append(f"## Lektion {lesson['lesson']}" + (f" — {lesson['title']}" if lesson["title"] else ""))
        lines.append("**Topics:** " + "; ".join(lesson["topics"]))
        lines.append("")
        lines.append("**Grammar:**")
        lines += [f"- {item}" for item in lesson["grammar"]]
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    scripts = dw_script_urls()
    courses = []
    for course_id, level, url, language in DW_COURSES:
        course = dw_course(course_id, level, url, language, scripts)
        courses.append(course)
        (OUT / f"{course_id}.md").write_text(dw_markdown(course), encoding="utf-8")
        time.sleep(0.5)
    for level, info in VHS_LEVELS.items():
        course = vhs_grammar(level, info)
        courses.append(course)
        (OUT / f"{course['id']}.md").write_text(vhs_markdown(course), encoding="utf-8")
    (OUT / "course-index.json").write_text(json.dumps({"generatedOn": time.strftime("%Y-%m-%d"), "courses": courses},
                                                      ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for course in courses:
        print(f"{course['id']}: {len(course['lessons'])} lessons")


if __name__ == "__main__":
    main()
