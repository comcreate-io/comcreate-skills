from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = str(Path(__file__).resolve().parent.parent)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from comcreate_skills.cli import main, parse


class CliTests(unittest.TestCase):
    def test_parse_inventory_flags(self) -> None:
        command, options = parse(
            [
                "inventory",
                "--no-usage",
                "--no-defaults",
                "--since-days",
                "30",
                "--root",
                "codex=/tmp/skills",
            ]
        )
        self.assertEqual(command, "inventory")
        self.assertFalse(options["usage"])
        self.assertFalse(options["defaults"])
        self.assertEqual(options["sinceDays"], 30)
        self.assertEqual(
            options["roots"], [{"runtime": "codex", "path": "/tmp/skills"}]
        )

    def test_parse_rejects_unknown_root_runtime(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "codex or claude-code"):
            parse(["inventory", "--root", "other=/tmp/skills"])

    def test_unknown_command_exits_one(self) -> None:
        stderr = io.StringIO()
        with patch.object(sys, "stderr", stderr):
            self.assertEqual(main(["nosuch"]), 1)
        self.assertIn("unknown command: nosuch", stderr.getvalue())

    def test_validate_succeeds(self) -> None:
        stdout = io.StringIO()
        with patch.object(sys, "stdout", stdout):
            self.assertEqual(main(["validate"]), 0)
        self.assertIn("Repository is valid.", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
