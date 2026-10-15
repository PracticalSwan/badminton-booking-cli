# Badminton Booking CLI

Windows automation for Assumption University Sports Center Messenger badminton requests. The interface is a **text-only command-line menu**, not a GUI.

## Desktop usage

Double-click **Enable Badminton Booking.cmd** on the Desktop. Its new purpose is to open the CLI manager, **not** automatically enable the task. Choose a menu number:

| Menu | Action |
| --- | --- |
| 1 | View weekly slots, date exceptions, send time and current pause/scheduler state |
| 2 | Edit any Monday-Sunday booking time or skip a weekday |
| 3 | Add/change one calendar-date booking, or skip that date |
| 4 | Remove a date exception and restore weekly behavior |
| 5 | Edit the daily Messenger send time |
| 6 | ENABLE automatic sending after explicit YES confirmation |
| 7 | DISABLE automatic sending indefinitely |
| 0 | Exit without altering enabled/disabled state |

**Default:** Send request at 08:00 Asia/Bangkok. Monday-Friday court slot 16:30-18:00, Sunday 15:30-17:00; Saturday skipped. Times use 24-hour HH:MM. Specific-date exceptions take precedence over weekly settings.

The Task Scheduler task is named **Badminton Court Booking**. It launches one minute before the configured send time; the sender waits for the exact send time and rejects sends more than five minutes late. To keep launcher and send on the same calendar date, send time 00:00 is not supported (valid 00:01-23:59). Booking slots must end after start on the same date.

## Safe configuration

- Versioned non-sensitive booking schedule: schedule.json
- Local-only Messenger recipient and student IDs: booking.private.json
- Example private file with dummy IDs: booking.private.example.json
- Local-only session browser profiles: chrome_profile and browser_profile
- Local-only pause marker and sent history: PAUSED and state.json

If moving to a new PC, copy the example to booking.private.json and enter the actual recipient URL and numeric student IDs, then authenticate manually. Never put Facebook passwords in that file. For the existing PC, the original private settings are preserved locally and Git-ignored.

Changing a setting **does not enable** sending. While PAUSED exists, manually started booking.py also exits without opening Messenger. Edits sync the Windows scheduler trigger and preserve its disabled state. If syncing fails, the manager attempts to disable automation, and displays an error. Already-sent dates are not resent just because settings changed. If booking history is corrupted or unreadable, sending is deliberately blocked until history is repaired to avoid a duplicate booking message.

## Files

- booking_manager.py: interactive CLI menu
- booking_config.py: validation, date overrides, serialization, private settings
- booking.py: Messenger sender and pause/duplicate/stale-config guards
- start_booking.ps1 / stop_booking.ps1: explicit task state controls
- enable_booking.ps1 / sync_schedule.ps1: Task Scheduler install and trigger updates
- Manage Badminton Booking.cmd: launcher inside project
- scripts/install_desktop_launcher.ps1: installer for the existing Desktop launcher
- tests: unit, CLI and mocked no-network sender boundary tests
- .github/workflows/verify.yml: Windows/Linux unit and privacy tests, plus PowerShell parser verification
- AGENTS.md / LESSONS.md / CHANGELOG.md / MEMORY.md: required workflow references

## Tests and privacy

From the project root, run:

    .venv\Scripts\python.exe -m unittest discover -s tests -v
    .venv\Scripts\python.exe booking.py --self-test
    .venv\Scripts\python.exe booking.py

The last command must return "Booking automation is paused. Nothing sent." if PAUSED exists. After staging intended files, run:

    .venv\Scripts\python.exe scripts\privacy_check.py
    git status --short
    git ls-files

Do not stage booking.private.json, auth.ok, state.json, PAUSED, session directories or logs, even in a PRIVATE repository. No automated live Messenger sends are permitted during verification.

A non-sending authentication check is available via `.venv\Scripts\python.exe booking.py --check-auth`; it opens the locally authenticated Chrome profile, navigates to Messenger, verifies the composer, and closes the browser. This does not establish that a message was delivered or that a court was booked.

## Maintenance

Read and maintain AGENTS.md, LESSONS.md, CHANGELOG.md and MEMORY.md each maintenance pass. Verify locally and audit staged files before committing or pushing. A separate live send test requires explicit authorization.
