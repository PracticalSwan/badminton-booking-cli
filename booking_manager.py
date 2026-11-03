"""Text-only booking settings manager; no Messenger messages are sent here."""
from __future__ import annotations

import subprocess
import sys
from datetime import date
from pathlib import Path

from booking_config import (
    DAYS, ROOT, ConfigError, format_time, is_example_private, load_private,
    load_schedule, parse_clock, save_private, save_schedule, validate_private,
    validate_schedule, validate_slot,
)

PAUSED = ROOT / "PAUSED"


def prompt(message: str) -> str:
    return input(message).strip()


def task_state() -> str:
    script = (
        "$t=Get-ScheduledTask -TaskName 'Badminton Court Booking' "
        "-ErrorAction SilentlyContinue; if($null -eq $t){'Not installed'}else{$t.State}"
    )
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", script],
            check=True, capture_output=True, text=True, timeout=15,
        )
        return result.stdout.strip() or "Unknown"
    except (FileNotFoundError, OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return "Unavailable"


def booking_status() -> str:
    """Show only user-facing RUNNING/PAUSED, based on both safety controls."""
    if PAUSED.exists():
        return "PAUSED"
    return "RUNNING" if task_state() in ("Ready", "Running") else "PAUSED"


def show_settings(config: dict) -> None:
    print("\n=== Badminton booking settings ===")
    print(f"Booking status: {booking_status()}")
    print(f"Daily send time: {config['send_time']} (Asia/Bangkok)")
    print("Weekly bookings:")
    for index, day in enumerate(DAYS, start=1):
        slot = config["weekly"][day]
        text = "SKIP" if slot is None else f"{format_time(slot['start'])} - {format_time(slot['end'])}"
        print(f"  {index}. {day.title():9} {text}")
    print("Date-specific overrides:")
    if not config["overrides"]:
        print("  (none)")
    for day, slot in config["overrides"].items():
        text = "SKIP" if slot is None else f"{format_time(slot['start'])} - {format_time(slot['end'])}"
        print(f"  {day}: {text}")
    print("Note: bookings for a date already sent will not be resent.")


def ask_slot() -> dict[str, str] | None:
    print("Enter times in 24-hour HH:MM format (e.g. 16:30).")
    if prompt("Skip the booking? [y/N]: ").lower() == "y":
        return None
    start = prompt("Booking START (HH:MM): ")
    end = prompt("Booking END   (HH:MM): ")
    parse_clock(start)
    parse_clock(end)
    return validate_slot({"start": start, "end": end})


def ask_date() -> str:
    value = prompt("Booking date (YYYY-MM-DD): ")
    try:
        if date.fromisoformat(value).isoformat() != value:
            raise ValueError()
    except ValueError as exc:
        raise ConfigError("Date must be a real YYYY-MM-DD calendar date.") from exc
    return value


def save_and_sync(config: dict) -> None:
    save_schedule(config)
    # If sync fails, pause rather than leave a mismatched enabled scheduler trigger.
    script = ROOT / "sync_schedule.ps1"
    try:
        subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                        "-File", str(script)], check=True, timeout=30)
    except (FileNotFoundError, OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        try:
            run_control("stop_booking.ps1")
        except Exception:
            pass
        raise RuntimeError("Schedule saved but scheduler sync failed; pause attempted. Check Task Scheduler and PAUSED.") from exc
    print("Settings saved. Enabled/disabled status was preserved.")


def run_control(script_name: str) -> None:
    script = ROOT / script_name
    subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-File", str(script)], check=True, timeout=60)


def ask_student_id() -> str:
    """Read and confirm an ID visibly in the user's local console."""
    first = prompt("New Student ID: ")
    second = prompt("Confirm Student ID: ")
    if first != second:
        raise ConfigError("Student ID confirmation did not match.")
    # Delegate content validation to validate_private inside save_private.
    return first


def select_student_id(count: int) -> int:
    selection = prompt(f"Student number (1-{count}): ")
    if not selection.isdecimal() or not 1 <= int(selection) <= count:
        raise ConfigError("Choose a valid Student ID list position.")
    return int(selection) - 1


def manage_student_ids() -> None:
    """Display and edit full IDs locally; never write their values to application logs."""
    while True:
        private = load_private()
        ids = private["student_ids"]
        print("\n=== Student IDs ===")
        for index, student_id in enumerate(ids, start=1):
            print(f"  {index}. {student_id}")
        print("1. Replace an existing Student ID")
        print("2. Add a Student ID")
        print("3. Remove a Student ID")
        print("0. Back to main menu")
        action = prompt("Select option: ")
        if action == "0":
            return
        try:
            updated = list(ids)
            if action == "1":
                position = select_student_id(len(ids))
                updated[position] = ask_student_id()
                if updated == ids:
                    print("No change.")
                    continue
            elif action == "2":
                updated.append(ask_student_id())
            elif action == "3":
                if len(ids) == 1:
                    raise ConfigError("At least one Student ID is required.")
                position = select_student_id(len(ids))
                if prompt("Type REMOVE to confirm deletion: ") != "REMOVE":
                    print("Cancelled.")
                    continue
                del updated[position]
            else:
                print("Unknown menu choice.")
                continue
            save_private(validate_private({"chat_url": private["chat_url"], "student_ids": updated}))
            print("Student IDs updated in local private settings; scheduler state unchanged.")
        except (ConfigError, OSError) as exc:
            print(f"ERROR: {exc}")


def run_auth_action(option: str) -> None:
    """Run a non-sending browser operation using the launcher's Python environment."""
    code = subprocess.run([sys.executable, str(ROOT / "booking.py"), option]).returncode
    if code != 0:
        print("Facebook verification failed. Check your conversation URL or log in again.")
    else:
        print("Messenger access verified. No booking message was sent.")


def manage_facebook() -> None:
    """Configure local Messenger settings without opening or modifying live bookings."""
    while True:
        print("\n=== Facebook account and conversation ===")
        print("1. Set/change conversation URL and Student IDs")
        print("2. Log in to Facebook in Chrome")
        print("3. Check login (no message sent)")
        print("0. Back to main menu")
        choice = prompt("Select option: ")
        if choice == "0":
            return
        if choice == "2":
            run_auth_action("--login")
            continue
        if choice == "3":
            run_auth_action("--check-auth")
            continue
        if choice != "1":
            print("Unknown menu choice.")
            continue

        try:
            current = load_private()
            if is_example_private(current):
                print("First-time setup: replace the example URL and Student ID.")
            else:
                print("Press ENTER at either prompt to keep that existing setting.")
            print("Open your own Facebook Messenger conversation and copy its URL.")
            url = prompt("Messenger conversation URL: ") or current["chat_url"]
            raw_ids = prompt("Student IDs (comma-separated, visible locally): ")
            ids = [item.strip() for item in raw_ids.split(",")] if raw_ids else current["student_ids"]
            updated = validate_private({"chat_url": url, "student_ids": ids})
            if is_example_private(updated):
                raise ConfigError("Replace the example Messenger URL and Student IDs first.")
            if updated != current:
                save_private(updated)
                print("Private settings saved locally; booking status unchanged.")
            else:
                print("Settings unchanged.")
            if prompt("Open Chrome to log in to Facebook now? [Y/n]: ").lower() not in ("n", "no"):
                run_auth_action("--login")
        except (ConfigError, OSError) as exc:
            print(f"ERROR: {exc}")


def manage_schedule() -> None:
    """Keep detailed schedule changes out of the main menu."""
    while True:
        config = load_schedule()
        print("\n=== Booking schedule ===")
        print("1. Change weekly court times or skip a weekday")
        print("2. Add/change a date-specific booking or skip")
        print("3. Remove a date-specific override")
        print("4. Change daily message send time")
        print("0. Back to main menu")
        choice = prompt("Select option: ")
        if choice == "0":
            return
        try:
            if choice == "1":
                selection = prompt("Weekday number (1=Mon ... 7=Sun): ")
                if selection not in map(str, range(1, 8)):
                    raise ConfigError("Choose a weekday from 1 through 7.")
                day = DAYS[int(selection) - 1]
                config["weekly"][day] = ask_slot()
                save_and_sync(config)
            elif choice == "2":
                booking_date = ask_date()
                config["overrides"][booking_date] = ask_slot()
                save_and_sync(config)
            elif choice == "3":
                booking_date = ask_date()
                if booking_date not in config["overrides"]:
                    print("No override for that date; nothing changed.")
                else:
                    del config["overrides"][booking_date]
                    save_and_sync(config)
            elif choice == "4":
                new_time = prompt("New daily SEND time (HH:MM, 00:01 to 23:59): ")
                parse_clock(new_time)
                config["send_time"] = new_time
                validate_schedule(config)
                save_and_sync(config)
            else:
                print("Unknown menu choice.")
        except (ConfigError, RuntimeError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            print(f"ERROR: {exc}")


def main() -> int:
    try:
        while True:
            config = load_schedule()
            print(f"\n=== Badminton Booking | {booking_status()} ===")
            print("1. View booking status and schedule")
            print("2. Edit booking schedule")
            print("3. Facebook setup and login")
            print("4. View/change Student IDs")
            print("5. Start automatic booking")
            print("6. Pause automatic booking indefinitely")
            print("0. Exit")
            choice = prompt("Select option: ")
            try:
                if choice == "0":
                    return 0
                if choice == "1":
                    show_settings(config)
                elif choice == "2":
                    manage_schedule()
                elif choice == "3":
                    manage_facebook()
                elif choice == "4":
                    manage_student_ids()
                elif choice == "5":
                    if prompt("Start automatic Messenger bookings? Type YES to confirm: ") == "YES":
                        run_control("start_booking.ps1")
                    else:
                        print("Cancelled.")
                elif choice == "6":
                    run_control("stop_booking.ps1")
                else:
                    print("Unknown menu choice.")
            except (ConfigError, RuntimeError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
                print(f"ERROR: {exc}")
    except (KeyboardInterrupt, EOFError):
        print("\nExiting; booking status unchanged.")
        return 0
    except ConfigError as exc:
        print(f"Cannot open booking settings: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
