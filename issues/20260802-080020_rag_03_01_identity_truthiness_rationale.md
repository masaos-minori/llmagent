# Add design rationale to docs/03_rag_03_01 identity-vs-truthiness note

## Priority
Low

## Summary
`docs/03_rag_03_01_query_pipeline-overview.md`'s "identity vs truthiness" note accurately describes that `is not None` checks (not truthiness checks) are used, distinguishing an empty string `""` from `None`, but does not explain why this distinction matters.

## Reason for Change
This is flagged as one of the most easily-misunderstood behaviors for implementers; adding the "why" (distinguishing "searched but got zero results" from "not yet searched") makes the correct-but-unexplained rule much less likely to be "simplified away" by a future editor who doesn't understand its purpose.

## Implementation Intent
Add one sentence explaining the design reasoning behind the identity check.

## Target Files or Areas
`docs/03_rag_03_01_query_pipeline-overview.md`

## Required Changes
- Add: "`""`は有効な(空の)結果として扱われ、`None`は未実行を表す。これにより「検索したが0件だった」と「まだ検索していない」を区別できる。"

## Acceptance Criteria
The identity-vs-truthiness note includes the design rationale (distinguishing zero-results-found from not-yet-searched).

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/03_rag_03_01` gains a one-sentence rationale addition.

## Out of Scope
Do not change the actual identity-check implementation in this issue — documentation only.

## AI Implementation Instruction
Keep the addition to one sentence — this is a small clarifying rationale, not a rewrite of the existing accurate description.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §4 強化候補 (03_01 identity vs truthiness)
- Generated at: 2026-08-02
