# Project Memory — Non-sensitive

Read on every maintenance pass and update after lasting changes.

- Windows project: D:\Side Projects\badminton_booking_script.
- User wants a keyboard-only menu on existing Desktop Enable Badminton Booking.cmd.
- Automation state is user-controlled and may change between sessions. Inspect the actual Windows task and PAUSED marker before acting; never automatically enable or disable a live installation during maintenance.
- Source-controlled schedule.json holds non-private weekly slots, date exceptions and send time. booking.private.json and persistent browser sessions stay local and ignored. Current CLI: 1 status, 2 schedule submenu, 3 Facebook setup/login, 4 full visible Student IDs with visible double-entry, 5 explicit start, 6 indefinite pause, 0 exit. Status is RUNNING only when Task Scheduler is enabled and PAUSED absent, otherwise PAUSED. Private ID changes must never toggle scheduling, and sender rejects stale settings at submission.
- Python + Playwright/Chrome sender; Windows PowerShell 5.1 Task Scheduler controls.
- Safety: PAUSED guard, date-based duplicate prevention, malformed-state fail-closed behavior, send window limit, schedule-change guard. Synthetic sender tests do not open Messenger.
- Git privacy audits inspect **staged** content and reject real-looking numeric identifiers, including in CI without local private settings. Treat this as defense-in-depth, not a guarantee that arbitrary secrets cannot slip through.
- Work sequence: inspect AGENTS/LESSONS/CHANGELOG/MEMORY, implement, verify, privacy audit, inspect staged paths, commit/push, verify PRIVATE remote state.
- 2026-10-15 verified: scheduler enable/edit/restore/disable sequence and read-only Messenger composer check passed. Actual message delivery remains unverified without a live booking send.
- GitHub onboarding: README includes complete Windows PowerShell first-run path; scripts/initialize_booking.ps1 creates ignored synthetic private settings and PAUSED only for a new installation; task registration remains paused until explicit start. --validate-config verifies own settings and rejects sample recipient/Student IDs without opening Facebook. A fresh non-sending --check-auth is required at every explicit enable because auth.ok can be stale. Windows integration tests mock Task Scheduler; installed Chrome channel does not require a separate Playwright Chromium download.
- Root/Desktop `Enable Badminton Booking.cmd` opens one-click local setup and CLI through `Manage Badminton Booking.cmd` / `scripts/launch_booking.ps1`. It creates/repairs `.venv` and pinned packages if necessary; first-time configuration starts PAUSED, while subsequent launches preserve existing files and booking state. Do not assume live task state from a previous handoff; inspect it fresh.
- CodeGraph 1.6.2 is installed and project-local indexing initialized; `.codegraph/` is excluded via .gitignore. After code changes run `codegraph sync` and verify status; never publish the graph or local sensitive content.
