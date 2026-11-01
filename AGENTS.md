# Agent Instructions — Badminton Booking CLI

## Mandatory start of every task

1. Identify the workspace, Git root and status. Read AGENTS.md, LESSONS.md, CHANGELOG.md and MEMORY.md **every time**.
2. Inspect the relevant scripts, tests, Desktop launcher, Windows scheduled task and PAUSED state. Never expose private configuration values.
3. Preserve unrelated work and the local booking state. Define verification and privacy boundaries before changes.
4. At the end, update CHANGELOG.md and document verified lessons in LESSONS.md; update MEMORY.md and these instructions for durable changes. Do not fabricate lessons.

## Architecture and contracts

- Windows PowerShell 5.1 and the task named Badminton Court Booking.
- Desktop Enable Badminton Booking.cmd must launch the text-only menu, not enable booking directly.
- booking_manager.py is the CLI, including a Student ID sub-menu. booking_config.py validates schedule.json and validates/atomically saves the ignored local booking.private.json. Keep the actual chat URL unchanged when editing IDs.
- schedule.json version 1: send_time as HH:MM, weekly with all seven lowercase weekdays as slot/start/end or null, overrides with YYYY-MM-DD keys pointing to slot or null.
- Date overrides win; 00:00 send time and overnight court intervals are not supported.
- Scheduler starts one minute before send; five-minute send cutoff, Asia/Bangkok timezone, duplicate-date prevention.
- Sender checks PAUSED at startup and immediately before Enter; abort if schedule **or private Student IDs** change while preparing. Invalid or unreadable booking history **must block sending** to avoid an accidental duplicate.
- Editing settings must not unpause. stop_booking.ps1 creates PAUSED and disables; start_booking.ps1 explicitly enables and removes PAUSED. sync_schedule.ps1 updates the trigger while preserving disabled state.

## Protected and forbidden data

Never commit, publish or print browser profiles, cookies, sessions, booking.private.json, auth.ok, PAUSED, state.json, logs, credentials, real student IDs or real recipient URL. Within the local CLI, show only masked student IDs and use hidden double-entry for new IDs; never log private values. Even though GitHub is PRIVATE, source must be sanitized. Inspect .gitignore, use explicit Git staging and run scripts/privacy_check.py on tracked/staged files before every push. No Codex CLI; use the user-selected CodexPro connector.

## Verification and publication

- Parse and test Python and PowerShell; test valid/invalid times, date overrides, skipped dates, CLI edits, masked Student ID replace/add/remove/cancel, private-file atomicity/validation, and explicit enable guard. Test private files in isolated temporary directories only.
- Verify Desktop launcher and preserved task state. Do not send actual Facebook messages in automated tests. Live UI/send behavior is not proven by local tests.
- Inspect intended changes and staging, privacy audit, then commit/push when authorized (this maintenance pass includes authorization). The privacy audit must inspect **staged Git blobs**, not just working-tree files, and reject real-looking numeric identifiers even when no private config exists (such as on CI).
- Verify the remote is PRIVATE and the remote HEAD matches. No force-push or history rewriting.
- Report concrete verification limits and unfinished work. Do not claim remote success unless verified.
