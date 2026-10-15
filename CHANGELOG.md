# Changelog

## 2026-10-15 — Verification and safety maintenance

- Reproduced and fixed corrupted booking-history fail-open, preventing duplicate sends when state.json cannot be parsed.
- Reproduced and fixed privacy checker staged-versus-worktree mismatch; added numeric identifier detection for CI without private settings.
- Added synthetic no-network sender boundary tests (pause, duplicate, stale settings, skip day, expired time and nominal submission).
- Expanded CI to install pinned runtime dependencies and test on Linux and Windows, including Windows PowerShell script parsing.
- Verified a real enabled-state CLI toggle and live Task Scheduler send-time update, then restored the default schedule and indefinite pause.
- Verified saved Messenger login with the read-only --check-auth path; composer was available, with no booking sent.
- Updated official GitHub Actions to immutable current Node 24 release commits and pinned Ubuntu 24.04 to avoid scheduled ubuntu-latest migration; adjusted numeric-ID privacy detection to exclude hex SHA substrings.

## 2026-10-15 — Configurable CLI and private repository preparation

- Added a text-only booking menu for weekly slots, calendar-date overrides/skips, send time, and enable/disable actions.
- Moved recipient/student IDs into local Git-ignored configuration; source configuration contains only booking schedule.
- Updated sender for configurable timing/slots and added a final stale-config guard.
- Added scheduler trigger synchronization, Desktop launcher installer, tests, CI and privacy checks.
- Updated project instructions and created lessons and durable project memory.
- Verified CLI send-time scheduling adjustment/restoration in a disabled Windows task without sending any Messenger message.

## 2026-09-29 — Indefinite manual pause

- Added start/stop scripts and PAUSED marker; confirmed the Windows task disabled and no message on paused run.
