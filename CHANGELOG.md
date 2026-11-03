# Changelog

## 2026-11-03 — Follow-up activation safety and clean-clone verification

- Rechecked the published repository via a clean Windows clone, fresh virtual environment, pinned dependencies, and non-sending synthetic configuration workflow.
- Require a fresh non-sending Messenger authentication check before explicitly enabling the Windows task; a stale auth.ok marker alone is insufficient.
- Added Windows PowerShell integration tests that mock Task Scheduler to verify registration remains paused and failed authentication cannot enable a task; tested the successful explicit enable path with synthetic inputs.

## 2026-11-03 — Safe first-time onboarding for other authorized users

- Expanded the GitHub README with Windows prerequisites, venv installation, private local configuration, Messenger login and non-sending authentication checks, schedule/Student ID editing, paused task registration, and troubleshooting.
- Added idempotent, non-sending scripts/initialize_booking.ps1; it creates a local-only sample and PAUSED on new installations without modifying existing private configurations.
- Made example Student IDs syntactically valid yet intentionally synthetic, and introduced --validate-config and operational placeholder rejection.
- Changed task registration to create PAUSED before registration and verify Disabled state; explicit enabling also validates local settings and requires an authentication marker.
- Added isolated first-run regression checks and Windows CI PowerShell syntax coverage. The existing local task and custom schedule were not altered.

## 2026-11-01 — Visible Student ID editing correction

- Updated Student ID menu to display full current IDs with their list positions, rather than asterisks.
- Replaced hidden password-style input with visible double-entry, preserving validation, local-only storage, and all automation safety controls.
- Updated regression tests and CLI instructions. No Student ID values are committed.

## 2026-11-01 — Local Student ID management

- Added CLI option 8 to replace, add, and remove Student IDs using hidden double-entry and masked listings.
- Added validated, atomic writes to local Git-ignored private settings, preserving the Messenger conversation URL, other IDs, schedule, and pause status.
- Sender rechecks private settings just before message submission to avoid stale student lists.
- Added isolated private-file and CLI tests for valid edits, duplicate/invalid IDs, cancellation, minimum one ID, privacy masking, and stale-data send guard.
- Preserved pre-existing user edits to schedule.json without staging them.

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
