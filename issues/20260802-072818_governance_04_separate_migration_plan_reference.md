# Confirm and link the identity of "a separate migration plan" referenced in docs/00_governance_04 Migration Notes

## Priority
Low

## Summary
`docs/00_governance_04`'s Migration Notes mention "a separate migration plan" without naming or linking it. `docs/00_governance_08_known-issues-migration-plan.md` is a plausible match, but this is not confirmed in the text.

## Reason for Change
An unnamed reference forces readers to guess which document is meant, risking wasted search time or reliance on a document that may not even be the right one.

## Implementation Intent
Confirm whether `docs/00_governance_08` is the intended referent; if so, name it explicitly with a link/path.

## Target Files or Areas
`docs/00_governance_04_known-issues-template.md`

## Required Changes
- Read `docs/00_governance_08` and compare its scope against what Migration Notes describes.
- If it matches, replace "a separate migration plan" with an explicit reference to `docs/00_governance_08_known-issues-migration-plan.md`.
- If it does not match, either create the missing document or remove the dangling reference (do not leave it unnamed).

## Acceptance Criteria
The Migration Notes reference is either an explicit, correct link, or the dangling reference is removed.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/00_governance_04` updated with a resolved reference.

## Out of Scope
Do not modify `docs/00_governance_08`'s content in this issue (see the related stale-migration-plan-rewrite issue for that).

## AI Implementation Instruction
Verify the match by reading both documents' actual scope, not just by name similarity.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_governance.md §6 Needs confirmation item ("a separate migration plan"の実在確認)
- Generated at: 2026-08-02
