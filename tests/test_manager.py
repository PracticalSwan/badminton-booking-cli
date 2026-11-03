import unittest
from unittest.mock import patch
from booking_manager import main
from booking_config import load_schedule


class CliTests(unittest.TestCase):
    def setUp(self):
        # All menu tests run without querying or altering the real Windows scheduler.
        scheduler = patch("booking_manager.task_state", return_value="Ready")
        scheduler.start()
        self.addCleanup(scheduler.stop)

    def test_exit_without_modification(self):
        with patch("booking_manager.prompt", return_value="0"), \
             patch("booking_manager.load_schedule", return_value={"version": 1}):
            self.assertEqual(main(), 0)

    def test_invalid_day_does_not_save(self):
        with patch("booking_manager.prompt", side_effect=["2", "1", "9", "0", "0"]), \
             patch("booking_manager.load_schedule", return_value=load_schedule()), \
             patch("booking_manager.save_and_sync") as sync:
            self.assertEqual(main(), 0)
            sync.assert_not_called()

    def test_edit_weekday_saves_and_syncs(self):
        with patch("booking_manager.prompt", side_effect=["2", "1", "1", "n", "17:00", "18:00", "0", "0"]), \
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
                   side_effect=["4", "1", "1", "000002", "000002", "0", "0"]), \
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
                   side_effect=["4", "3", "0", "0"]), \
             patch("booking_manager.load_private", return_value=private), \
             patch("booking_manager.save_private") as save, \
             patch("booking_manager.load_schedule", return_value=load_schedule()):
            self.assertEqual(main(), 0)
            save.assert_not_called()

    def test_student_id_add_rejects_duplicate(self):
        private = {"chat_url": "https://www.facebook.com/messages/t/0000000",
                   "student_ids": ["000000"]}
        with patch("booking_manager.prompt", side_effect=["4", "2", "000000", "000000", "0", "0"]), \
             patch("booking_manager.load_private", return_value=private), \
             patch("booking_manager.save_private") as save, \
             patch("booking_manager.load_schedule", return_value=load_schedule()):
            self.assertEqual(main(), 0)
            save.assert_not_called()

    def test_disable_calls_pause_script(self):
        with patch("booking_manager.prompt", side_effect=["6", "0"]), \
             patch("booking_manager.load_schedule", return_value=load_schedule()), \
             patch("booking_manager.run_control") as control:
            self.assertEqual(main(), 0)
            control.assert_called_once_with("stop_booking.ps1")

    def test_enable_requires_explicit_yes(self):
        with patch("booking_manager.prompt", side_effect=["5", "no", "0"]), \
             patch("booking_manager.load_schedule", return_value=load_schedule()), \
             patch("booking_manager.run_control") as control:
            self.assertEqual(main(), 0)
            control.assert_not_called()

    def test_schedule_submenu_keeps_date_skip_and_send_time(self):
        import booking_manager

        config = load_schedule()
        with patch("booking_manager.prompt",
                   side_effect=["2", "2026-12-01", "y", "4", "09:15", "0"]), \
             patch("booking_manager.load_schedule", return_value=config), \
             patch("booking_manager.save_and_sync") as save:
            booking_manager.manage_schedule()
        self.assertIsNone(config["overrides"]["2026-12-01"])
        self.assertEqual(config["send_time"], "09:15")
        self.assertEqual(save.call_count, 2)

    def test_main_menu_routes_schedule_without_enabling(self):
        import booking_manager

        with patch("booking_manager.prompt", side_effect=["2", "0"]), \
             patch("booking_manager.load_schedule", return_value=load_schedule()), \
             patch("booking_manager.manage_schedule") as schedule, \
             patch("booking_manager.run_control") as controls:
            self.assertEqual(main(), 0)
        schedule.assert_called_once()
        controls.assert_not_called()

    def test_status_only_running_or_paused(self):
        import tempfile
        from pathlib import Path
        import booking_manager

        with tempfile.TemporaryDirectory() as directory:
            pause = Path(directory) / "PAUSED"
            with patch.object(booking_manager, "PAUSED", pause), \
                 patch("booking_manager.task_state", return_value="Ready"):
                self.assertEqual(booking_manager.booking_status(), "RUNNING")
                pause.touch()
                self.assertEqual(booking_manager.booking_status(), "PAUSED")
                pause.unlink()
            for state in ("Disabled", "Not installed", "Unavailable", "Unknown"):
                with self.subTest(state=state), \
                     patch.object(booking_manager, "PAUSED", pause), \
                     patch("booking_manager.task_state", return_value=state):
                    self.assertEqual(booking_manager.booking_status(), "PAUSED")

    def test_facebook_setup_uses_only_synthetic_private_and_never_sends(self):
        import tempfile
        from pathlib import Path
        from booking_config import load_private as read_private, save_private as write_private
        import booking_manager

        sample = {"chat_url": "https://www.facebook.com/messages/t/0000000",
                  "student_ids": ["000000"]}
        with tempfile.TemporaryDirectory() as directory:
            private_path = Path(directory) / "booking.private.json"
            write_private(sample, private_path)
            new_url = "https://www.facebook.com/messages/t/00000000"
            with patch("booking_manager.prompt",
                       side_effect=["1", new_url, "000001, 000002", "n", "0"]), \
                 patch("booking_manager.load_private", side_effect=lambda: read_private(private_path)), \
                 patch("booking_manager.save_private", side_effect=lambda data: write_private(data, private_path)), \
                 patch("booking_manager.run_auth_action") as auth, \
                 patch("booking_manager.run_control") as controls:
                booking_manager.manage_facebook()
            self.assertEqual(read_private(private_path),
                             {"chat_url": new_url, "student_ids": ["000001", "000002"]})
            auth.assert_not_called()
            controls.assert_not_called()

    def test_facebook_setup_invalid_input_preserves_private(self):
        import tempfile
        from pathlib import Path
        from booking_config import load_private as read_private, save_private as write_private
        import booking_manager

        sample = {"chat_url": "https://www.facebook.com/messages/t/0000000",
                  "student_ids": ["000000"]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "booking.private.json"
            write_private(sample, path)
            before = path.read_bytes()
            with patch("booking_manager.prompt",
                       side_effect=["1", "https://example.com/messages/t/111", "000001", "0"]), \
                 patch("booking_manager.load_private", side_effect=lambda: read_private(path)), \
                 patch("booking_manager.save_private", side_effect=lambda data: write_private(data, path)), \
                 patch("booking_manager.run_auth_action") as auth:
                booking_manager.manage_facebook()
            self.assertEqual(path.read_bytes(), before)
            auth.assert_not_called()

    def test_facebook_setup_existing_values_are_preserved_when_blank(self):
        from booking_config import validate_private
        import booking_manager

        current = validate_private({"chat_url": "https://www.facebook.com/messages/t/00000000",
                                    "student_ids": ["000001", "000002"]})
        with patch("booking_manager.prompt", side_effect=["1", "", "", "n", "0"]), \
             patch("booking_manager.load_private", return_value=current), \
             patch("booking_manager.save_private") as save, \
             patch("booking_manager.run_auth_action") as auth:
            booking_manager.manage_facebook()
        save.assert_not_called()
        auth.assert_not_called()

    def test_facebook_setup_can_trigger_manual_login(self):
        import booking_manager

        current = {"chat_url": "https://www.facebook.com/messages/t/00000000",
                   "student_ids": ["000001"]}
        with patch("booking_manager.prompt", side_effect=["1", "", "", "", "0"]), \
             patch("booking_manager.load_private", return_value=current), \
             patch("booking_manager.save_private") as save, \
             patch("booking_manager.run_auth_action") as auth:
            booking_manager.manage_facebook()
        save.assert_not_called()
        auth.assert_called_once_with("--login")

    def test_main_menu_routes_facebook_setup_without_enabling(self):
        import booking_manager
        with patch("booking_manager.prompt", side_effect=["3", "0"]), \
             patch("booking_manager.load_schedule", return_value=load_schedule()), \
             patch("booking_manager.manage_facebook") as setup, \
             patch("booking_manager.run_control") as controls:
            self.assertEqual(main(), 0)
        setup.assert_called_once()
        controls.assert_not_called()

if __name__ == "__main__":
    unittest.main()
