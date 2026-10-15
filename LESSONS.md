# Lessons Learned

Read at the start of every maintenance task. Add only evidence-backed findings.

## 2026-10-15

- The Desktop launcher previously ran task installation directly, bypassing pause/resume semantics. The new launcher must open the menu rather than implicitly enabling the task.
- The send time was previously duplicated in Python (08:00) and Task Scheduler (07:59). Editing the send time requires synchronizing the trigger and preserving its Disabled state.
- Private repository visibility alone is insufficient: Facebook profile data, recipient/student identifiers and logs must remain untracked.
- The safety test for a paused sender must exit without launching a browser or sending a message.
- Real Task Scheduler integration confirmed the send-time edit moved the trigger from 07:59 to 08:04 (send 08:05), then restored 07:59 (send 08:00); PAUSED and Disabled remained unchanged.
- Default-time assertions in self-tests would break after users customize their slots; test current config validity and keep fixed sample expectations in a dedicated test fixture.
