# Project Memory — Non-sensitive

Read on every maintenance pass and update after lasting changes.

- Windows project: D:\Side Projects\badminton_booking_script.
- User wants a keyboard-only menu on existing Desktop Enable Badminton Booking.cmd.
- Booking automation paused since 2026-09-29. Do not resume without explicit ENABLE selection.
- Source-controlled schedule.json holds non-private weekly slots, date exceptions and daily send time. booking.private.json and persistent browser sessions stay local and ignored.
- Python + Playwright/Chrome sender; Windows PowerShell 5.1 Task Scheduler controls.
- Safety: PAUSED guard, date-based duplicate prevention, send window limit, schedule-change guard. No live Messenger sends during automated tests.
- Work sequence: inspect AGENTS/LESSONS/CHANGELOG/MEMORY, implement, verify, privacy audit, inspect staged paths, commit/push, verify PRIVATE remote state.
