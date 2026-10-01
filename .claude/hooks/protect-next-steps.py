#!/usr/bin/env python3
"""PreToolUse hook: agents may edit next-steps.md's steps, never its rule line or the file itself."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NAME = "next-steps.md"
NEXT_STEPS = ROOT / NAME
# Keep identical to the line in next-steps.md; ANKI/tests/test_next_steps.py checks both.
RULE = "Rule (the learner's; no AI may change or delete this rule or this file): extremely short."
BASH_WRITE = re.compile(
    r"\b(rm|mv|cp|unlink|truncate|tee|dd|install|rsync|ln)\b|>\s*['\"]?[^\s;|&]*" + re.escape(NAME)
    + r"|\b(sed|perl)\b[^|;&]*\s-i"
    r"|\bgit\s+(rm|mv|checkout|restore|reset|stash|clean)\b|write_text|write_bytes|open\(|\.unlink\(|os\.remove|shutil"
)


def deny(reason: str) -> None:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))
    sys.exit(0)


def is_next_steps(path: str, cwd: str) -> bool:
    if not path:
        return False
    return Path(os.path.realpath(os.path.join(cwd, os.path.expanduser(path)))) == Path(os.path.realpath(NEXT_STEPS))


def after_edits(current: str, edits: list[dict]) -> str:
    for edit in edits:
        old, new = edit.get("old_string", ""), edit.get("new_string", "")
        current = current.replace(old, new) if edit.get("replace_all") else current.replace(old, new, 1)
    return current


def main() -> None:
    data = json.load(sys.stdin)
    tool, args, cwd = data.get("tool_name", ""), data.get("tool_input", {}) or {}, data.get("cwd") or os.getcwd()
    reason = f"{NAME} belongs to the learner: agents may update its steps but never its rule line or the file itself."
    if tool in ("Write", "Edit", "MultiEdit") and is_next_steps(args.get("file_path", ""), cwd):
        if tool == "Write":
            result = args.get("content", "")
        else:
            current = NEXT_STEPS.read_text(encoding="utf-8") if NEXT_STEPS.exists() else ""
            result = after_edits(current, args.get("edits") if tool == "MultiEdit" else [args])
        if RULE not in result.splitlines():
            deny(reason)
    elif tool == "Bash":
        command = args.get("command", "")
        if NAME in command and BASH_WRITE.search(command):
            deny(reason + " Use the Edit tool to change steps.")


if __name__ == "__main__":
    main()
