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

    def test_student_id_edit_through_menu_without_scheduler_sync(self):
        private = {"chat_url": "https://www.facebook.com/messages/t/0000000",
                   "student_ids": ["000000", "000001"]}
        with patch("booking_manager.prompt",
                   side_effect=["8", "1", "1", "000002", "000002", "0", "0"]), \
             patch("booking_manager.load_private", return_value=private), \
             patch("booking_manager.save_private") as save, \
             patch("booking_manager.save_and_sync") as sync, \
             patch("booking_manager.load_schedule", return_value=load_schedule()):
            self.assertEqual(main(), 0)
            save.assert_called_once()
            self.assertEqual(save.call_args.args[0]["student_ids"],
                             ["000002", "000001"])
            sync.assert_not_called()

    def test_student_id_remove_last_is_blocked(self):
        private = {"chat_url": "https://www.facebook.com/messages/t/0000000",
                   "student_ids": ["000000"]}
        with patch("booking_manager.prompt",
                   side_effect=["8", "3", "0", "0"]), \
             patch("booking_manager.load_private", return_value=private), \
             patch("booking_manager.save_private") as save, \
             patch("booking_manager.load_schedule", return_value=load_schedule()):
            self.assertEqual(main(), 0)
            save.assert_not_called()

    def test_student_id_add_rejects_duplicate(self):
        private = {"chat_url": "https://www.facebook.com/messages/t/0000000",
                   "student_ids": ["000000"]}
        with patch("booking_manager.prompt", side_effect=["8", "2", "000000", "000000", "0", "0"]), \
             patch("booking_manager.load_private", return_value=private), \
             patch("booking_manager.save_private") as save, \
             patch("booking_manager.load_schedule", return_value=load_schedule()):
            self.assertEqual(main(), 0)
            save.assert_not_called()

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
