"""next-steps.md keeps the learner's rule line; the Claude hook refuses edits that remove it."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NEXT_STEPS = ROOT / "next-steps.md"
HOOK = ROOT / ".claude" / "hooks" / "protect-next-steps.py"
# The learner's rule (2026-10-01). Changing it needs the learner, never an agent.
RULE = "Rule (the learner's; no AI may change or delete this rule or this file): extremely short."


def run_hook(payload: dict) -> bool:
    """True when the hook denies the tool call."""
    result = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload), capture_output=True,
                            text=True, check=True)
    return '"deny"' in result.stdout


class NextStepsTest(unittest.TestCase):
    def test_file_keeps_rule_line(self):
        self.assertTrue(NEXT_STEPS.exists(), "next-steps.md was deleted")
        self.assertIn(RULE, NEXT_STEPS.read_text(encoding="utf-8").splitlines())

    def test_hook_uses_same_rule(self):
        self.assertIn(json.dumps(RULE, ensure_ascii=False), HOOK.read_text(encoding="utf-8"))

    def test_hook_blocks_rule_changes_and_deletion(self):
        path = str(NEXT_STEPS)
        self.assertTrue(run_hook({"tool_name": "Edit", "cwd": str(ROOT), "tool_input": {
            "file_path": path, "old_string": "extremely short.", "new_string": "short."}}))
        self.assertTrue(run_hook({"tool_name": "Write", "cwd": str(ROOT), "tool_input": {
            "file_path": path, "content": "# Next steps\n"}}))
        self.assertTrue(run_hook({"tool_name": "Bash", "tool_input": {"command": "rm next-steps.md"}}))

    def test_hook_allows_step_changes(self):
        first_step = next(line for line in NEXT_STEPS.read_text(encoding="utf-8").splitlines()
                          if line.startswith("1."))
        self.assertFalse(run_hook({"tool_name": "Edit", "cwd": str(ROOT), "tool_input": {
            "file_path": str(NEXT_STEPS), "old_string": first_step, "new_string": "1. Next step"}}))
        self.assertFalse(run_hook({"tool_name": "Bash", "tool_input": {"command": "git add next-steps.md"}}))


if __name__ == "__main__":
    unittest.main()
