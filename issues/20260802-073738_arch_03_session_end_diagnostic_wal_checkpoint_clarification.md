# Clarify WAL checkpoint failure behavior in docs/01_overview-arch-03-features.md session-end diagnostic section

## Priority
Medium

## Summary
`docs/01_overview-arch-03-features.md` (~lines 62-70) describes session-end diagnostic saving involving a WAL checkpoint, but does not describe what happens if the WAL TRUNCATE checkpoint fails (behavior on next startup, data-loss risk).

## Reason for Change
This bears on recovery/failure understanding — an operator encountering a failed checkpoint needs to know whether the process still exits cleanly and what state the WAL file will be in in the next startup.

## Implementation Intent
Add a sentence describing WAL TRUNCATE checkpoint failure behavior, based on verified source behavior — not asserted without confirmation.

## Target Files or Areas
`docs/01_overview-arch-03-features.md`

## Required Changes
- Investigate the actual behavior when a WAL TRUNCATE checkpoint fails during session-end diagnostic save (does the process still exit? what state is the WAL file left in for next startup? is data loss possible?).
- If confirmable from source, add: "If the WAL TRUNCATE checkpoint fails, the process still exits, but on next startup it resumes with an enlarged WAL file (no data loss is expected, but this should be monitored)." — adjust wording to match actual verified behavior.
- If not confirmable through reasonable source inspection, register this as a Needs Confirmation item in `docs/00_governance_07` instead of asserting unverified behavior.

## Acceptance Criteria
The WAL checkpoint failure behavior is either documented as verified fact, or explicitly tracked as a Needs Confirmation item — not left silently unaddressed nor asserted without verification.

## Testing Expectations
Not required (documentation-only). The underlying investigation is a source-reading exercise, not a test run — though a manual reproduction (forcing a checkpoint failure) would provide the strongest verification if feasible.

## Documentation Impact
`docs/01_overview-arch-03-features.md` gains a verified (or explicitly unconfirmed) checkpoint-failure behavior note.

## Out of Scope
Do not change the WAL checkpoint implementation in this issue — documentation only.

## AI Implementation Instruction
Do not write the suggested sentence verbatim without first verifying it against actual source behavior — the review itself flags this content as "record only after implementation confirmation; if unconfirmed, treat as Needs Confirmation."

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_overview_architecture.md §4 強化候補 (arch-03「セッション終了時の診断保存」)
- Generated at: 2026-08-02
