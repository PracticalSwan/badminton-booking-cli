import unittest
from unittest.mock import patch
from booking_manager import main
from booking_config import load_schedule


class CliTests(unittest.TestCase):
    def test_exit_without_modification(self):
        with patch("booking_manager.prompt", return_value="0"), \
             patch("booking_manager.load_schedule", return_value={"version": 1}):
            self.assertEqual(main(), 0)

    def test_invalid_day_does_not_save(self):
        with patch("booking_manager.prompt", side_effect=["2", "9", "0"]), \
             patch("booking_manager.load_schedule", return_value=load_schedule()), \
             patch("booking_manager.save_and_sync") as sync:
            self.assertEqual(main(), 0)
            sync.assert_not_called()

    def test_edit_weekday_saves_and_syncs(self):
        with patch("booking_manager.prompt", side_effect=["2", "1", "n", "17:00", "18:00", "0"]), \
             patch("booking_manager.load_schedule", return_value=load_schedule()), \
             patch("booking_manager.save_and_sync") as sync:
            self.assertEqual(main(), 0)
            sync.assert_called_once()
            config = sync.call_args.args[0]
            self.assertEqual(config["weekly"]["monday"], {"start": "17:00", "end": "18:00"})

    def test_disable_calls_pause_script(self):
        with patch("booking_manager.prompt", side_effect=["7", "0"]), \
             patch("booking_manager.load_schedule", return_value=load_schedule()), \
             patch("booking_manager.run_control") as control:
            self.assertEqual(main(), 0)
            control.assert_called_once_with("stop_booking.ps1")

    def test_enable_requires_explicit_yes(self):
        with patch("booking_manager.prompt", side_effect=["6", "no", "0"]), \
             patch("booking_manager.load_schedule", return_value=load_schedule()), \
             patch("booking_manager.run_control") as control:
            self.assertEqual(main(), 0)
            control.assert_not_called()


if __name__ == "__main__":
    unittest.main()
