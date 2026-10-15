"""Text-only booking settings manager; no Messenger messages are sent here."""
from __future__ import annotations

import subprocess
import sys
from datetime import date
from pathlib import Path

from booking_config import (
    DAYS, ROOT, ConfigError, format_time, load_schedule,
    parse_clock, save_schedule, validate_schedule, validate_slot,
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


def show_settings(config: dict) -> None:
    print("\n=== Badminton booking settings ===")
    print(f"Automation: {'PAUSED' if PAUSED.exists() else 'Not paused'}")
    print(f"Windows scheduled task: {task_state()}")
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


def main() -> int:
    try:
        while True:
            config = load_schedule()
            print("\n=== Badminton Booking CLI ===")
            print("1. Show booking settings and status")
            print("2. Change weekly booking day/time")
            print("3. Add/change date-specific booking or skip date")
            print("4. Remove date-specific override")
            print("5. Change daily message send time")
            print("6. ENABLE automatic booking")
            print("7. DISABLE automatic booking indefinitely")
            print("0. Exit")
            choice = prompt("Select option: ")
            try:
                if choice == "0":
                    return 0
                if choice == "1":
                    show_settings(config)
                elif choice == "2":
                    selection = prompt("Weekday number (1=Mon ... 7=Sun): ")
                    if selection not in map(str, range(1, 8)):
                        raise ConfigError("Choose a weekday from 1 through 7.")
                    day = DAYS[int(selection) - 1]
                    config["weekly"][day] = ask_slot()
                    save_and_sync(config)
                elif choice == "3":
                    booking_date = ask_date()
                    config["overrides"][booking_date] = ask_slot()
                    save_and_sync(config)
                elif choice == "4":
                    booking_date = ask_date()
                    if booking_date not in config["overrides"]:
                        print("No override for that date; nothing changed.")
                    else:
                        del config["overrides"][booking_date]
                        save_and_sync(config)
                elif choice == "5":
                    new_time = prompt("New daily SEND time (HH:MM, 00:01 to 23:59): ")
                    parse_clock(new_time)
                    config["send_time"] = new_time
                    validate_schedule(config)
                    save_and_sync(config)
                elif choice == "6":
                    if prompt("Enable scheduled Messenger bookings? Type YES to confirm: ") == "YES":
                        run_control("start_booking.ps1")
                    else:
                        print("Cancelled.")
                elif choice == "7":
                    run_control("stop_booking.ps1")
                else:
                    print("Unknown menu choice.")
            except (ConfigError, RuntimeError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
                print(f"ERROR: {exc}")
    except (KeyboardInterrupt, EOFError):
        print("\nExiting; current enabled/disabled status unchanged.")
        return 0
    except ConfigError as exc:
        print(f"Cannot open booking settings: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
