# Reduce implementation-derived detail in docs/06_eventbus_05_07_validation-status.md

## Priority
Low

## Summary
Apply the design-doc reduction policy from `memo-doc-eventbus-review.md` to `docs/06_eventbus_05_07_validation-status.md`: keep which quality gates must be maintained and why health/DLQ regression testing matters; remove exact run commands, test counts, and last-verified dates.

## Reason for Change
This chapter currently records point-in-time CI output (test counts, last-verified date, FAIL/ERROR counts) that goes stale immediately and duplicates what running the test suite already shows.

## Implementation Intent
Keep this chapter focused on the existence of CI validation, which quality gates matter (lint, type check, tests), and why health/DLQ-area regression tests are particularly important given past DLQ-loop issues.

## Target Files or Areas
`docs/06_eventbus_05_07_validation-status.md`

## Required Changes
- Keep: that CI validation exists, which quality gates should be maintained (lint, type check, tests), that there was a past DLQ-loop defect and that health/DLQ-area regression tests are therefore important.
- Remove or compress: exact run commands, test counts, last-verified dates, detailed FAIL/ERROR counts, fine implementation-level fix-history memos.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」.
- No test count, last-verified date, or exact run command remains.
- The rationale for prioritizing health/DLQ regression coverage remains explicit.

## Testing Expectations
Not required for behavior (documentation-only). No dedicated eventbus docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task.

## Out of Scope
- Other `docs/06_eventbus_*.md` chapters.
- `tests/test_eventbus*.py` itself (code, not documentation).
- Any code under `scripts/eventbus/` — per AGENTS.md Global Rule 8, eventbus implementation changes are prohibited; this issue is documentation-only.

## AI Implementation Instruction
Follow `memo-doc-eventbus-review.md` §「06_eventbus_05_07_validation-status」. Do not touch any file under `scripts/eventbus/` or `tests/test_eventbus*.py` — AGENTS.md Global Rule 8 forbids eventbus implementation changes (investigation only). Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-eventbus-review.md` §「06_eventbus_05_07_validation-status」
- Generated at: 2026-08-05
