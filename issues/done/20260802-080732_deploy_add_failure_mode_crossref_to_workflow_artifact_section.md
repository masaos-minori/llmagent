# Add cross-reference from Workflow artifact fail-closed design section to failure-mode table

## Priority
Low

## Summary
`docs/02_deployment-part1.md` §2.2's "Workflow artifact responsibilities" section correctly and completely documents the fail-closed design (no disable/fallback/workflow-optional mode exists), confirmed to exactly match `deploy.sh`'s implementation (existence check, validation, checksum verification, exit 1 on failure). It lacks a pointer to where readers can find the corresponding failure-mode/log detail.

## Reason for Change
Readers who want to know the specific exit codes and log strings for these failure conditions have to search separately; a direct cross-reference makes the failure-mode table (in `part2`) easy to find.

## Implementation Intent
Add a one-sentence cross-reference from this section to `docs/02_deployment-part2.md`'s failure-mode table.

## Target Files or Areas
`docs/02_deployment-part1.md` (§2.2)

## Required Changes
- Add: "ワークフロー定義の検証・チェックサム照合に失敗した場合の挙動・ログ文字列は「失敗モードと復旧」(docs/02_deployment-part2.md)を参照。"

## Acceptance Criteria
The section includes a cross-reference to the failure-mode table in `part2`.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/02_deployment-part1.md` gains a one-sentence cross-reference.

## Out of Scope
Do not otherwise modify this section's existing, already-accurate content.

## AI Implementation Instruction
Keep the addition to one sentence — this section is already confirmed accurate and complete; do not rewrite it beyond adding the cross-reference.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_deployment.md §4 強化候補 (§2.2 Workflow artifact responsibilities)
- Generated at: 2026-08-02
