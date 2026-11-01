import copy
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from booking_config import (
    ConfigError, booking_for_date, compose_message, format_time,
    load_private, load_schedule, parse_clock, save_schedule, validate_schedule,
)

ROOT = Path(__file__).resolve().parents[1]


class ScheduleTests(unittest.TestCase):
    def setUp(self):
        self.config = load_schedule(ROOT / "tests" / "fixtures" / "schedule.default.json")

    def test_default_weekly_and_saturday(self):
        self.assertEqual(booking_for_date(self.config, date(2026, 10, 19)), {"start": "16:30", "end": "18:00"})
        self.assertEqual(booking_for_date(self.config, date(2026, 10, 18)), {"start": "15:30", "end": "17:00"})
        self.assertIsNone(booking_for_date(self.config, date(2026, 10, 17)))

    def test_date_override_and_skip_priority(self):
        self.config["overrides"]["2026-10-19"] = {"start": "10:30", "end": "11:30"}
        self.config["overrides"]["2026-10-18"] = None
        self.assertEqual(booking_for_date(self.config, date(2026, 10, 19))["start"], "10:30")
        self.assertIsNone(booking_for_date(self.config, date(2026, 10, 18)))

    def test_validation_rejects_bad_times_and_slots(self):
        for value in ("00:60", "24:00", "9:00", "-1:30", "hi", ""):
            with self.subTest(value=value), self.assertRaises(ConfigError):
                parse_clock(value)
        self.config["weekly"]["monday"] = {"start": "18:00", "end": "17:00"}
        with self.assertRaises(ConfigError):
            validate_schedule(self.config)

    def test_midnight_send_rejected_to_keep_trigger_same_day(self):
        self.config["send_time"] = "00:00"
        with self.assertRaises(ConfigError):
            validate_schedule(self.config)

    def test_date_invalid_and_injection_rejected(self):
        self.config["overrides"]["2026-02-30"] = None
        with self.assertRaises(ConfigError):
            validate_schedule(self.config)
        del self.config["overrides"]["2026-02-30"]
        self.config["overrides"]["../../secrets"] = None
        with self.assertRaises(ConfigError):
            validate_schedule(self.config)

    def test_saves_valid_config_atomically(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "schedule.json"
            self.config["send_time"] = "09:12"
            save_schedule(self.config, path)
            self.assertEqual(load_schedule(path), self.config)
            self.assertFalse(any(Path(tmp).glob(".schedule-*.tmp")))

    def test_invalid_schedule_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "schedule.json"
            save_schedule(self.config, path)
            original = path.read_bytes()
            broken = copy.deepcopy(self.config)
            broken["send_time"] = "25:00"
            with self.assertRaises(ConfigError):
                save_schedule(broken, path)
            self.assertEqual(path.read_bytes(), original)

    def test_private_settings_and_message_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "private.json"
            data = {"chat_url": "https://www.facebook.com/messages/t/0000000",
                    "student_ids": ["100001", "100002"]}
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(load_private(path), data)
            self.assertEqual(compose_message({"start": "15:30", "end": "17:00"}, data),
                             "Booking Badminton Court  3:30 PM to 5:00 PM  100001 100002")
            data["chat_url"] = "https://evil.example/messages/t/0000000"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ConfigError):
                load_private(path)

    def test_private_ids_are_unique_numeric_and_nonempty(self):
        from booking_config import validate_private
        baseline = {"chat_url": "https://www.facebook.com/messages/t/0000000",
                    "student_ids": ["000000", "000001"]}
        self.assertEqual(validate_private(baseline), baseline)
        for ids in ([], ["000000", "000000"], ["not-numeric"],
                    ["000000", " "], ["000000", 123], "000000"):
            with self.subTest(ids=ids), self.assertRaises(ConfigError):
                validate_private({**baseline, "student_ids": ids})

    def test_private_settings_saved_atomically_and_without_schedule_change(self):
        from booking_config import save_private
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "booking.private.json"
            original = {"chat_url": "https://www.facebook.com/messages/t/0000000",
                        "student_ids": ["000000", "000001"]}
            save_private(original, path)
            updated = {**original, "student_ids": ["000002", "000001"]}
            save_private(updated, path)
            self.assertEqual(load_private(path), updated)
            self.assertFalse(list(Path(tmp).glob(".booking-private-*")))
            before = path.read_bytes()
            with self.assertRaises(ConfigError):
                save_private({**original, "student_ids": []}, path)
            self.assertEqual(path.read_bytes(), before)

    def test_private_settings_keep_recipient_without_ids_in_error(self):
        from booking_config import save_private
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "booking.private.json"
            original = {"chat_url": "https://www.facebook.com/messages/t/0000000",
                        "student_ids": ["000000"]}
            save_private(original, path)
            self.assertEqual(load_private(path)["chat_url"], original["chat_url"])

    def test_format_time(self):
        self.assertEqual(format_time("16:30"), "4:30 PM")
        self.assertEqual(format_time("08:00"), "8:00 AM")


if __name__ == "__main__":
    unittest.main()
