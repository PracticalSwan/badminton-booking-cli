"""Fresh-install safety checks: no live task, browser, or Messenger access."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import booking
from booking_config import ConfigError, validate_private

ROOT = Path(__file__).resolve().parents[1]


class FirstRunTests(unittest.TestCase):
    def test_synthetic_example_is_schema_valid_but_not_operational(self):
        example = json.loads((ROOT / "booking.private.example.json").read_text(encoding="utf-8"))
        self.assertEqual(validate_private(example), example)
        with patch.object(booking, "load_private", return_value=example):
            with self.assertRaisesRegex(ConfigError, "example Messenger URL"):
                booking.load_operational_private()

    def test_login_rejects_example_without_opening_facebook(self):
        example = json.loads((ROOT / "booking.private.example.json").read_text(encoding="utf-8"))
        with patch.object(booking, "load_private", return_value=example), \
             patch.object(booking, "sync_playwright") as browser:
            with self.assertRaises(ConfigError):
                booking.authenticate()
            browser.assert_not_called()

    def test_realistic_synthetic_values_pass_operational_guard(self):
        configured = {"chat_url": "https://www.facebook.com/messages/t/00000000",
                      "student_ids": ["000001"]}
        with patch.object(booking, "load_private", return_value=configured):
            self.assertEqual(booking.load_operational_private(), configured)

    def test_placeholder_student_id_blocks_operational_guard(self):
        configured = {"chat_url": "https://www.facebook.com/messages/t/00000000",
                      "student_ids": ["000001", "000000"]}
        with patch.object(booking, "load_private", return_value=configured):
            with self.assertRaises(ConfigError):
                booking.load_operational_private()

    def test_install_registration_writes_pause_before_task_register(self):
        content = (ROOT / "enable_booking.ps1").read_text(encoding="utf-8")
        self.assertLess(content.index("Set-Content -LiteralPath $PauseFile"),
                        content.index("Register-ScheduledTask -TaskName"))
        self.assertIn("Disable-ScheduledTask -TaskName $TaskName", content)

    def test_explicit_start_checks_auth_and_config_before_enabling(self):
        content = (ROOT / "start_booking.ps1").read_text(encoding="utf-8")
        self.assertLess(content.index("Test-Path -LiteralPath $AuthMarker"),
                        content.index("Enable-ScheduledTask -TaskName"))
        self.assertLess(content.index("--validate-config"),
                        content.index("Enable-ScheduledTask -TaskName"))

    @unittest.skipUnless(sys.platform == "win32", "PowerShell 5.1 integration requires Windows")
    def test_initializer_is_paused_and_idempotent_in_isolated_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "scripts").mkdir()
            source = ROOT / "scripts" / "initialize_booking.ps1"
            script = root / "scripts" / source.name
            script.write_bytes(source.read_bytes())
            (root / "booking.private.example.json").write_bytes(
                (ROOT / "booking.private.example.json").read_bytes())
            command = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                       "-File", str(script)]
            first = subprocess.run(command, capture_output=True, text=True, timeout=20)
            self.assertEqual(first.returncode, 0, first.stderr)
            private = root / "booking.private.json"
            pause = root / "PAUSED"
            self.assertTrue(pause.is_file())
            self.assertEqual(validate_private(json.loads(private.read_text(encoding="utf-8"))),
                             json.loads(private.read_text(encoding="utf-8")))
            # Repeat after local customization; neither personal data nor pause state changes.
            private.write_text(json.dumps({"chat_url":
                "https://www.facebook.com/messages/t/00000000",
                "student_ids": ["000001"]}), encoding="utf-8")
            pause_before = pause.read_bytes()
            private_before = private.read_bytes()
            second = subprocess.run(command, capture_output=True, text=True, timeout=20)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(private.read_bytes(), private_before)
            self.assertEqual(pause.read_bytes(), pause_before)


if __name__ == "__main__":
    unittest.main()
