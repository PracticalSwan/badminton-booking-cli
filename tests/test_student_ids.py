"""CLI Student ID edits against isolated private files, never real identifiers."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import booking_manager
from booking_config import load_private, load_schedule, save_private

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "schedule.default.json"
SAMPLE_URL = "https://www.facebook.com/messages/t/0000000"


class PrivateManagerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "booking.private.json"
        save_private(
            {"chat_url": SAMPLE_URL, "student_ids": ["000001", "000002"]},
            self.path,
        )

    def run_menu(self, selections, secrets=()):
        output = io.StringIO()
        with (
            patch("booking_manager.prompt", side_effect=selections),
            patch("booking_manager.getpass.getpass", side_effect=secrets),
            patch("booking_manager.load_schedule", return_value=load_schedule(FIXTURE)),
            patch("booking_manager.load_private", side_effect=lambda: load_private(self.path)),
            patch("booking_manager.save_private", side_effect=lambda x: save_private(x, self.path)),
            patch("booking_manager.save_and_sync") as scheduler,
            patch("booking_manager.run_control") as controls,
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(booking_manager.main(), 0)
            scheduler.assert_not_called()
            controls.assert_not_called()
        return output.getvalue()

    def test_replace_one_id_keeps_others_and_recipient(self):
        output = self.run_menu(["8", "1", "2", "0", "0"], ["000003", "000003"])
        updated = load_private(self.path)
        self.assertEqual(updated["student_ids"], ["000001", "000003"])
        self.assertEqual(updated["chat_url"], SAMPLE_URL)
        self.assertNotIn("000001", output)
        self.assertNotIn("000003", output)
        self.assertIn("******", output)

    def test_add_id_preserves_order(self):
        self.run_menu(["8", "2", "0", "0"], ["000003", "000003"])
        self.assertEqual(load_private(self.path)["student_ids"], ["000001", "000002", "000003"])

    def test_remove_id_requires_confirmation(self):
        output = self.run_menu(["8", "3", "1", "REMOVE", "0", "0"])
        self.assertEqual(load_private(self.path)["student_ids"], ["000002"])
        self.assertNotIn("000002", output)

    def test_cancel_remove_has_no_effect(self):
        before = self.path.read_bytes()
        self.run_menu(["8", "3", "1", "no", "0", "0"])
        self.assertEqual(self.path.read_bytes(), before)

    def test_bad_confirmation_has_no_effect(self):
        before = self.path.read_bytes()
        output = self.run_menu(["8", "1", "1", "0", "0"], ["000003", "000004"])
        self.assertEqual(self.path.read_bytes(), before)
        self.assertIn("confirmation did not match", output)
        self.assertNotIn("000003", output)

    def test_invalid_ids_and_duplicate_rejected(self):
        for item in ("", "abcd", "000001", "１２３４５６"):
            with self.subTest(value_type=item):
                before = self.path.read_bytes()
                self.run_menu(["8", "2", "0", "0"], [item, item])
                self.assertEqual(self.path.read_bytes(), before)

    def test_invalid_index_does_not_modify_file(self):
        before = self.path.read_bytes()
        self.run_menu(["8", "1", "19", "0", "0"])
        self.assertEqual(self.path.read_bytes(), before)

    def test_current_one_id_cannot_be_removed(self):
        save_private({"chat_url": SAMPLE_URL, "student_ids": ["000001"]}, self.path)
        before = self.path.read_bytes()
        self.run_menu(["8", "3", "0", "0"])
        self.assertEqual(self.path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
