# Lessons Learned

Read at the start of every maintenance task. Add only evidence-backed findings.

## 2026-11-03

- Live state can change between handoffs. Never assume the Windows task or PAUSED marker still matches an old report, and never alter an existing task to test first-run setup; use an isolated directory and read-only inspection.
- Registering a new task without first creating PAUSED could enable sending by default. The installer must write PAUSED before registration and verify that the task remains Disabled; explicit start is the only activation path.
- A structurally valid numeric-only synthetic private example simplifies setup, but it must be rejected as operational configuration until both the URL and IDs are replaced. A separate --validate-config command is non-sending and safe for onboarding.
- Playwright's channel="chrome" uses installed Google Chrome; a separate Playwright Chromium browser download is unnecessary. Unit tests do not establish a live Facebook delivery or reservation.
- Initializer must leave any existing booking.private.json and pause state untouched; it is tested with a temporary directory and no Task Scheduler changes.
- `auth.ok` only proves a previous Messenger login; it does not establish that the current Facebook session is usable. A fresh, non-sending `--check-auth` before enabling prevents a stale marker from activating an unusable task. Isolated Windows PowerShell tests mock task cmdlets to verify both the rejected-auth and successful-enable paths, and that newly registered tasks are disabled with PAUSED present.
- An actual clean private GitHub clone created a new Windows Python 3.10 venv, installed pinned dependencies, initialized PAUSED, rejected synthetic placeholders and validated safely replaced synthetic values. Live `--check-auth` independently found a Messenger composer without sending a message; actual message delivery remains untested.

## 2026-11-01

- Follow-up usability correction: the user must see the full existing Student IDs to select the right ID for editing. Showing them in the local interactive CLI is intentional; this does **not** authorize copying them into source, GitHub, logs, or remote diagnostic output. The previous masking recommendation is superseded for the local CLI.
- Ordinary `input()` makes typed IDs visible during replacement, unlike `getpass()`; retain confirmation and all existing validation and local-only persistence.

- Historical note (superseded 2026-11-01): Student IDs belong only in ignored local private JSON, not in source, versioned schedules, logs, or the Git remote. Current CLI deliberately uses full-ID display and visible double-entry.
- Tests against isolated temporary private files verified replace/add/remove, duplicate and nonnumeric rejection, confirmation mismatch, cancellation, and preservation of the recipient URL without changing Task Scheduler.
- A prepared Messenger request must compare the private configuration again before Enter; mocked sender regression confirmed that an ID change prevents stale submission.
- The user's schedule.json has pre-existing local changes, so feature commits must stage explicit paths and leave those unrelated choices untouched.
- Historical note (superseded 2026-11-01): an older read-only Desktop check used masking; the current CLI instead displays full IDs locally without changing scheduler state.

## 2026-10-15

- The Desktop launcher previously ran task installation directly, bypassing pause/resume semantics. The new launcher must open the menu rather than implicitly enabling the task.
- The send time was previously duplicated in Python (08:00) and Task Scheduler (07:59). Editing the send time requires synchronizing the trigger and preserving its Disabled state.
- Private repository visibility alone is insufficient: Facebook profile data, recipient/student identifiers and logs must remain untracked.
- The safety test for a paused sender must exit without launching a browser or sending a message.
- Real Task Scheduler integration confirmed the send-time edit moved the trigger from 07:59 to 08:04 (send 08:05), then restored 07:59 (send 08:00); PAUSED and Disabled remained unchanged.
- Default-time assertions in self-tests would break after users customize their slots; test current config validity and keep fixed sample expectations in a dedicated test fixture.
- Reproduced: invalid JSON in local state.json was interpreted as an empty state, allowing another booking attempt. Fail closed when existing history is unreadable/invalid.
- Reproduced: the initial Git privacy script inspected working files instead of staged blobs, allowing a staged identifier leak to pass when the worktree was cleaned. Scan the Git index and test index/worktree divergence.
- GitHub CI needs pinned Playwright installed because synthetic sender tests import booking.py; Windows should also parse PowerShell scripts in CI.
- Real Windows enabled-state roundtrip: setting send to 08:07 produced Task Scheduler 08:06 without disabling it; 08:00/07:59 and Disabled + PAUSED were restored. For PowerShell empty objects, inspect property counts using @($obj.PSObject.Properties).Count rather than relying on ambiguous property enumeration.
- Read-only Messenger --check-auth verified the composer was available; this is **not** evidence that actual Enter submission or court reservation succeeded.
- Security regexes need regression tests for false positives: embedded numeric substrings of immutable hexadecimal GitHub Action commit SHAs are not student identifiers. CI actions can use SHA pinning to avoid mutable release tags.
