# Reduce template-memo-style detail in docs/06_eventbus_90_inconsistencies_and_known_issues.md

## Priority
Medium

## Summary
Apply the design-doc reduction policy from `memo-doc-eventbus-review.md` to `docs/06_eventbus_90_inconsistencies_and_known_issues.md`: keep the operational meaning of each known/deferred issue (including the impact of unimplemented Agent integration and non-monotonic ack offsets); remove the full 17-field template, unverified metadata, and Statement A/B migration memos.

## Reason for Change
This chapter is the canonical source for known issues and deferred items (per `memo-doc-eventbus-review.md` §「章間の正本ルール」: 既知問題・保留事項 = `06_eventbus_90_inconsistencies_and_known_issues`), but a Known Issues section that degrades into a bug-list-with-metadata-fields loses its value as an operational reference, per this memo's explicit prohibition (§「禁止事項」: Known Issues を単なるバグ一覧にすること).

## Implementation Intent
Restructure each entry to explain what the issue means, why it matters, what to watch for operationally, and the criteria for deciding whether/how to address it — not a metadata template or diff memo.

## Target Files or Areas
`docs/06_eventbus_90_inconsistencies_and_known_issues.md`

## Required Changes
- Keep: the meaning of each known issue, why it is a problem, operational cautions, fix-decision criteria, the reasoning behind each deferred item, the operational impact of Agent integration being unimplemented, the operational impact of ack-offset monotonicity not being guaranteed. The note that `promote_to_dlq()` is not on the production path may be kept, but only briefly as an implementation detail (this chapter is the destination for that relocated note from `06_eventbus_02_04_dlq-background-loop`, per that issue).
- Remove or compress: the full 17-field issue template, unverified metadata fields (Owner / First Found / Target / Related), Statement A/B-style migration memos, detailed implementation file/test names, a plain schema-vs-implementation-difference table.
- Before removing any entry, verify against current code per `rules/coding.md` §「Documentation notes — "Current behavior" classification」 whether the discrepancy still applies; do not delete a note without this verification.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」 where applicable to a known-issues chapter.
- No entry uses the full 17-field template or unverified metadata fields; each entry states operational meaning instead.
- Every entry is classified per `rules/coding.md`'s five-way classification (Accepted current specification / Implementation fix required / Documentation fix required / Issue already tracked / Obsolete and removable) before being kept, cross-referenced, or deleted.
- The Agent-integration-unimplemented and ack-offset-non-monotonicity impact statements remain explicit.

## Testing Expectations
Not required for behavior (documentation-only). No dedicated eventbus docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task. Coordinate with `06_eventbus_02_04_dlq-background-loop`'s cleanup issue for the relocated `promote_to_dlq()` note.

## Out of Scope
- Other `docs/06_eventbus_*.md` chapters.
- Fixing the underlying code issues themselves (file separate issues under `issues/` per the "Implementation fix required" classification if discovered during this cleanup — but per AGENTS.md Global Rule 8, do not implement eventbus code fixes even then).
- Any code under `scripts/eventbus/` — per AGENTS.md Global Rule 8, eventbus implementation changes are prohibited; this issue is documentation-only.

## AI Implementation Instruction
Follow `memo-doc-eventbus-review.md` §「06_eventbus_90_inconsistencies_and_known_issues」 and `rules/coding.md`'s "Current behavior" classification table. Do not touch any file under `scripts/eventbus/` — AGENTS.md Global Rule 8 forbids eventbus implementation changes (investigation only); if a new "Implementation fix required" item is discovered, file it as a separate issue rather than implementing a fix. Do not silently delete a discrepancy note without first verifying against current code that it no longer applies. Mark unclear items as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-eventbus-review.md` §「06_eventbus_90_inconsistencies_and_known_issues」
- Generated at: 2026-08-05
