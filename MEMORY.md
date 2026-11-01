# Project Memory — Non-sensitive

Read on every maintenance pass and update after lasting changes.

- Windows project: D:\Side Projects\badminton_booking_script.
- User wants a keyboard-only menu on existing Desktop Enable Badminton Booking.cmd.
- Booking automation paused since 2026-09-29. Do not resume without explicit ENABLE selection.
- Source-controlled schedule.json holds non-private weekly slots, date exceptions and daily send time. booking.private.json and persistent browser sessions stay local and ignored. The CLI's option 8 shows full student IDs locally and uses visible double-entry to edit them without toggling the scheduler, and the sender rejects stale prepared messages when the private settings change.
- Python + Playwright/Chrome sender; Windows PowerShell 5.1 Task Scheduler controls.
- Safety: PAUSED guard, date-based duplicate prevention, malformed-state fail-closed behavior, send window limit, schedule-change guard. Synthetic sender tests do not open Messenger.
- Git privacy audits inspect **staged** content and reject real-looking numeric identifiers, including in CI without local private settings. Treat this as defense-in-depth, not a guarantee that arbitrary secrets cannot slip through.
- Work sequence: inspect AGENTS/LESSONS/CHANGELOG/MEMORY, implement, verify, privacy audit, inspect staged paths, commit/push, verify PRIVATE remote state.
- 2026-10-15 verified: scheduler enable/edit/restore/disable sequence and read-only Messenger composer check passed. Actual message delivery remains unverified without a live booking send.
