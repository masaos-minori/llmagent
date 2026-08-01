# Add conflict-resolution trigger-condition detail to docs/03_rag_00_document-guide.md

## Priority
Medium

## Summary
`docs/03_rag_00_document-guide.md`'s "コンフリクト解決" (conflict resolution) section is the sole documented process for handling contradictions between documents, but it does not specify who acts and at what trigger point — it only states that "the responsible document should be corrected at its root cause" without defining the trigger condition.

## Reason for Change
This section is the operational foundation for correcting the numerous confirmed contradictions found across this domain's review; without a clear trigger condition (when/by whom), the correction process itself risks being inconsistently applied.

## Implementation Intent
Add an explicit trigger-condition statement: when a contradiction is detected during review or implementation work, the canonical-source file (per the Canonical Source Rule) should be corrected, and the detection should be logged in the Known Issues document.

## Target Files or Areas
`docs/03_rag_00_document-guide.md`

## Required Changes
- Add: "レビューや実装変更で矛盾を検出した場合、Canonical Source Ruleで定めた正本側のファイルを修正し、`docs/03_rag_90_inconsistencies_and_known_issues.md`に検出日・内容を追記する。"

## Acceptance Criteria
The conflict-resolution section states an explicit trigger condition (when contradictions are detected) and the required logging action.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/03_rag_00_document-guide.md` gains a clarifying addition; establishes the process that the separate Known-Issues-population issue will follow.

## Out of Scope
Do not restructure the entire conflict-resolution section beyond adding the trigger-condition sentence.

## AI Implementation Instruction
Keep the addition concise — one to two sentences establishing the trigger condition and logging requirement, consistent with how the separate `docs/03_rag_90` population issue will use this process.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §4 強化候補 (00_document-guide コンフリクト解決)
- Generated at: 2026-08-02
