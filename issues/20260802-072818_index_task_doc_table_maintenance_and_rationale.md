# Add rationale for the "do not load all docs/*.md" rule and a maintenance note to the タスク別ドキュメント参照 tables in docs/00_index.md

## Priority
Low

## Summary
`docs/00_index.md` instructs readers/agents not to load all `docs/*.md` files, but gives no reason why. Separately, the タスク別ドキュメント参照 tables (~lines 73-149) enumerate specific file paths that must track source-code/doc renames to stay accurate — the line-128 filename typo (tracked separately) shows this has already gone stale once.

## Reason for Change
An unexplained "must not" rule is easy for future readers/agents to misunderstand or dismiss. The table's staleness risk, already manifested once, should be flagged as an explicit operational responsibility rather than left implicit.

## Implementation Intent
Add one sentence explaining the context-budget rationale for selective loading, and one operational note above the tables stating they must be kept in sync with actual file names/structure.

## Target Files or Areas
`docs/00_index.md` (~lines 57-59 and ~73-149)

## Required Changes
- After the "do not load all docs/*.md" instruction (~line 57-59), add: "理由: 全件読み込みはコンテキスト消費が過大になり、タスクに無関係な情報がノイズとして混入するため。"
- Above the タスク別ドキュメント参照 tables, add an operational note such as: "※本表は該当ドキュメントのリネーム・分割に追従して更新する運用注意事項であり、定期的な実在確認が必要。"

## Acceptance Criteria
Both additions are present; existing table content/structure is otherwise unchanged.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/00_index.md` gains two short explanatory notes.

## Out of Scope
Do not restructure the tables themselves or change any file path entries (see the related filename-typo issue for the one confirmed correction).

## AI Implementation Instruction
Keep additions to one sentence each; do not expand into a longer explanation section.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_governance.md §3 要約候補 item 8, §4 強化候補 (タスク別ドキュメント参照導入文), §5 例5
- Generated at: 2026-08-02
