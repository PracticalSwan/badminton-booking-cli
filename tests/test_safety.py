"""Regression checks for sensitive failure paths; never launch Facebook."""
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import booking
from booking_config import ConfigError

ROOT = Path(__file__).resolve().parents[1]


class SafetyTests(unittest.TestCase):
    def test_corrupt_state_does_not_allow_resend(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "state.json"
            state.write_text("{broken json", encoding="utf-8")
            with patch.object(booking, "STATE_FILE", state):
                with self.assertRaises(ConfigError):
                    booking.sent_today(date(2026, 10, 15))

    def test_privacy_check_scans_staged_content_not_clean_worktree(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "scripts").mkdir()
            source = (ROOT / "scripts" / "privacy_check.py").read_text(encoding="utf-8")
            (repo / "scripts" / "privacy_check.py").write_text(source, encoding="utf-8")
            (repo / "booking.private.json").write_text(
                json.dumps({"chat_url": "https://www.facebook.com/messages/t/0000000",
                            "student_ids": ["999999"]}), encoding="utf-8"
            )
            (repo / "tracked.txt").write_text("secret student 999999", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "add", "tracked.txt", "scripts/privacy_check.py"],
                           cwd=repo, check=True, capture_output=True)
            # Discrepancy: staging contains identity; working tree no longer does.
            (repo / "tracked.txt").write_text("clean file", encoding="utf-8")
            result = subprocess.run([sys.executable, str(repo / "scripts" / "privacy_check.py")],
                                    cwd=repo, text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0, "Staged identity leak must be blocked")

    def test_privacy_check_without_private_config_rejects_numeric_id(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "scripts").mkdir()
            source = (ROOT / "scripts" / "privacy_check.py").read_text(encoding="utf-8")
            (repo / "scripts" / "privacy_check.py").write_text(source, encoding="utf-8")
            # Deliberately built in pieces so test source contains no real-looking ID.
            synthetic_id = "456" + "7890"
            (repo / "tracked.txt").write_text("student ID " + synthetic_id, encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "add", "tracked.txt", "scripts/privacy_check.py"],
                           cwd=repo, check=True, capture_output=True)
            result = subprocess.run([sys.executable, str(repo / "scripts" / "privacy_check.py")],
                                    cwd=repo, text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0, "CI must block numeric identifiers without private file")


if __name__ == "__main__":
    unittest.main()
