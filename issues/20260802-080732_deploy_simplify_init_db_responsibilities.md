# Simplify init_db.sh responsibilities bullet list in docs/02_deployment-part2.md

## Priority
Medium

## Summary
`docs/02_deployment-part2.md` §3.1 (~lines 36-40)'s "init_db.shの責務" bullet list is close to a verbatim transcription of the script's own comments, though it does contain genuine design-judgment content: idempotency, checking all 5 required tables, and recording schema version.

## Reason for Change
Full removal would lose real design judgment (what is checked and what causes an abort), but the current level of detail (e.g. exact `sqlite3 .tables` output examples) duplicates what the script itself already documents.

## Implementation Intent
Keep only the judgment-level content — what is checked, and what missing condition causes an abort (fail-closed) — deferring exact verification-command detail to the operations runbook.

## Target Files or Areas
`docs/02_deployment-part2.md` (§3.1, ~lines 36-40)

## Required Changes
- Replace the detailed bullet list with: "init_db.sh は冪等に実行可能で、各DBの必須テーブルとスキーマバージョンを確認したうえで、欠落があれば処理を中止する(fail-closed)。確認対象テーブルの詳細はRunbook参照。"
- Move the exact verification-command detail (e.g. `sqlite3 .tables` output examples) to the operations runbook.

## Acceptance Criteria
The section states idempotency, the tables/schema-version check, and the fail-closed abort condition in a compact form; exact verification-command detail is deferred to the runbook.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/02_deployment-part2.md` shortened; operations runbook gains the detailed verification-command content.

## Out of Scope
Do not change `init_db.sh`'s actual verification logic in this issue — documentation only.

## AI Implementation Instruction
Preserve the idempotency/5-table-check/schema-version-recording judgment content exactly — this is the part of the section explicitly identified as valuable, not to be removed along with the mechanical detail.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_deployment.md §3 要約候補 item 3
- Generated at: 2026-08-02
