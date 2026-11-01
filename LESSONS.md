# Lessons Learned

Read at the start of every maintenance task. Add only evidence-backed findings.

## 2026-11-01

- Student IDs belong only in the ignored local private JSON, not in source, versioned schedules, logs, or the Git remote. Use masked CLI display and hidden double-entry when editing.
- Tests against isolated temporary private files verified replace/add/remove, duplicate and nonnumeric rejection, confirmation mismatch, cancellation, and preservation of the recipient URL without changing Task Scheduler.
- A prepared Messenger request must compare the private configuration again before Enter; mocked sender regression confirmed that an ID change prevents stale submission.
- The user's schedule.json has pre-existing local changes, so feature commits must stage explicit paths and leave those unrelated choices untouched.
- A read-only invocation through the actual Desktop CMD launcher confirmed that the Student ID sub-menu opens and masks current IDs without altering the pause state.

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
