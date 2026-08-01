# Add reason for restart_recommended always being False in docs/04_mcp_02_02

## Priority
Medium

## Summary
`docs/04_mcp_02_02_startup-modes-and-health.md` correctly documents that `restart_recommended` always returns `False` (confirmed against code), but does not explain why — whether this is an unimplemented placeholder or an intentional design decision not to offer auto-restart recommendations.

## Reason for Change
An operator could mistakenly rely on this field expecting eventual auto-recovery signaling, or conversely dismiss it as simply broken, without knowing which interpretation is correct — this review flags both possibilities as plausible and unconfirmed.

## Implementation Intent
Confirm with the implementation owner (or via commit history/design notes) whether this is a future-planned feature or an intentional non-feature, and document whichever is confirmed. If unconfirmable, register as an explicit Needs Confirmation item alongside the existing accurate description.

## Target Files or Areas
`docs/04_mcp_02_02_startup-modes-and-health.md`

## Required Changes
- Investigate whether `restart_recommended`'s always-False behavior is a known placeholder for future implementation, or an intentional design choice.
- Add: "`restart_recommended` currently always returns `False` ([confirmed reason once determined] / Needs confirmation: is this a planned-but-unimplemented flag, or an intentional design choice not to provide auto-restart signaling?). Operators should not rely on this field to expect automatic recovery."

## Acceptance Criteria
The reason for the always-False behavior is either documented as confirmed fact, or the file explicitly states it as an open Needs Confirmation item — not left silently unexplained.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/04_mcp_02_02` gains a reason (or explicit open-question note) for this behavior.

## Out of Scope
Do not implement `restart_recommended` logic in this issue — documentation only.

## AI Implementation Instruction
Check commit history and any nearby design comments before concluding the reason is unconfirmable — only fall back to a Needs Confirmation note if a reasonable investigation turns up nothing.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_mcp.md §4 強化候補 (restart_recommended常にFalse固定), §6B (restart_recommended常にFalse固定の理由)
- Generated at: 2026-08-02
