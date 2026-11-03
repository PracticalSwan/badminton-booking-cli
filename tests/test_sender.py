"""No-network sender tests with synthetic settings and a fake Messenger composer."""
import unittest
from contextlib import ExitStack
from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import booking
from booking_config import load_schedule

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "schedule.default.json"
FAKE_PRIVATE = {"chat_url": "https://www.facebook.com/messages/t/00000000", "student_ids": ["0000000"]}


class SenderTests(unittest.TestCase):
    def setUp(self):
        self.config = load_schedule(FIXTURE)
        self.now = datetime(2026, 10, 19, 8, 0, tzinfo=ZoneInfo("Asia/Bangkok"))

    def invoke(self, *, paused=(False, False), sent=(False, False), schedules=None, privates=None, now=None):
        actual = now or self.now

        class FakeClock(datetime):
            @classmethod
            def now(cls, tz=None):
                return actual

        with ExitStack() as stack:
            stack.enter_context(patch.object(booking, "datetime", FakeClock))
            stack.enter_context(patch.object(booking, "log"))
            stack.enter_context(patch.object(booking, "is_paused", side_effect=paused))
            stack.enter_context(patch.object(booking, "sent_today", side_effect=sent))
            stack.enter_context(patch.object(booking, "load_schedule", side_effect=schedules or (self.config, self.config)))
            stack.enter_context(patch.object(booking, "load_private", side_effect=privates or (FAKE_PRIVATE, FAKE_PRIVATE)))
            marker = stack.enter_context(patch.object(booking, "AUTH_MARKER"))
            marker.exists.return_value = True
            browser = stack.enter_context(patch.object(booking, "sync_playwright"))
            context = stack.enter_context(patch.object(booking, "open_context"))
            page = stack.enter_context(patch.object(booking, "get_page"))
            composer = stack.enter_context(patch.object(booking, "find_composer"))
            composer.return_value.text_content.return_value = ""
            mark = stack.enter_context(patch.object(booking, "mark_sent"))
            code = booking.run_booking()
            return code, composer, mark, browser, context

    def test_untouched_example_blocks_send_before_browser(self):
        example = {"chat_url": "https://www.facebook.com/messages/t/0000000",
                   "student_ids": ["000000"]}
        code, composer, mark, browser, _ = self.invoke(privates=(example,))
        self.assertEqual(code, 5)
        browser.assert_not_called()
        composer.return_value.press.assert_not_called()
        mark.assert_not_called()

    def test_nominal_composes_once_and_marks_sent(self):
        code, composer, mark, browser, context = self.invoke()
        self.assertEqual(code, 0)
        composer.return_value.fill.assert_called_once()
        self.assertIn("4:30 PM to 6:00 PM", composer.return_value.fill.call_args.args[0])
        composer.return_value.press.assert_called_once_with("Enter")
        mark.assert_called_once_with(date(2026, 10, 19))
        context.return_value.close.assert_called_once()

    def test_paused_on_entry_never_opens_browser(self):
        code, composer, mark, browser, _ = self.invoke(paused=(True,))
        self.assertEqual(code, 0)
        browser.assert_not_called()
        composer.return_value.press.assert_not_called()
        mark.assert_not_called()

    def test_paused_just_before_enter_blocks_send(self):
        code, composer, mark, _, _ = self.invoke(paused=(False, True))
        self.assertEqual(code, 0)
        composer.return_value.press.assert_not_called()
        mark.assert_not_called()

    def test_duplicate_on_entry_blocks_send(self):
        code, composer, mark, browser, _ = self.invoke(sent=(True,))
        self.assertEqual(code, 0)
        browser.assert_not_called()
        composer.return_value.press.assert_not_called()
        mark.assert_not_called()

    def test_duplicate_while_waiting_blocks_send(self):
        code, composer, mark, _, _ = self.invoke(sent=(False, True))
        self.assertEqual(code, 0)
        composer.return_value.press.assert_not_called()
        mark.assert_not_called()

    def test_edit_while_preparing_blocks_stale_send(self):
        changed = load_schedule(FIXTURE)
        changed["send_time"] = "08:05"
        code, composer, mark, _, _ = self.invoke(schedules=(self.config, changed))
        self.assertEqual(code, 0)
        composer.return_value.press.assert_not_called()
        mark.assert_not_called()

    def test_student_ids_changed_while_preparing_blocks_send(self):
        changed = {**FAKE_PRIVATE, "student_ids": ["000001"]}
        code, composer, mark, _, _ = self.invoke(privates=(FAKE_PRIVATE, changed))
        self.assertEqual(code, 0)
        composer.return_value.press.assert_not_called()
        mark.assert_not_called()

    def test_expired_window_never_opens_browser(self):
        late = self.now.replace(hour=8, minute=6)
        code, composer, mark, browser, _ = self.invoke(now=late)
        self.assertEqual(code, 3)
        browser.assert_not_called()
        composer.return_value.press.assert_not_called()
        mark.assert_not_called()

    def test_skip_day_never_opens_browser(self):
        now = self.now.replace(day=17)
        code, composer, mark, browser, _ = self.invoke(now=now)
        self.assertEqual(code, 0)
        browser.assert_not_called()
        composer.return_value.press.assert_not_called()
        mark.assert_not_called()


if __name__ == "__main__":
    unittest.main()
