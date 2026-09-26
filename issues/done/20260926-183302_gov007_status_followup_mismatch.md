# Governance Verification Matrix — GV-007 ステータスと Follow-up リストの矛盾

## Priority
Medium

## Summary
`governance_04_documentation-checks.md` の Governance Verification Matrix で GV-007 が `Existing` とされているが、Follow-up Work Needed セクションにまだ実装タスクとして残っている。既に `check_docs_structure.py` に duplicate link detection が実装済みなので、Follow-up リストから削除する必要がある。

## Background
GV-007 は "Duplicate Related Link prohibition" を指す。Matrix では Tool/Review に `check_docs_structure.py` が記載され、Status は `Existing` となっている。これは既に実装済みであることを示している。しかし Follow-up Work Needed セクションの項目 4 に `GV-007: Implement Duplicate Related Link prohibition check` が残っており、矛盾が生じている。

## Problem
Governance Verification Matrix と Follow-up Work Needed の間で GV-007 のステータスが矛盾しており、実装担当者が混乱する可能性がある。

## Reason for Change
既に実装済みのタスクが Follow-up リストに残っていると、実装不要な作業として認識されるべきものが未完了として扱われるリスクがある。

## Implementation Intent
`governance_04_documentation-checks.md` の Follow-up Work Needed セクションから GV-007 のエントリを削除し、Matrix の Status を `Existing` のまま維持する。

## Target Files or Areas
- `docs/00_governance/governance_04_documentation-checks.md`

## Required Changes
- Follow-up Work Needed セクションから `GV-007: Implement Duplicate Related Link prohibition check` のエントリを削除
- Follow-up Work Needed の番号付けを再確認（欠番があれば修正）

## Constraints
- Matrix の Status カラムは変更しない（既に `Existing`）
- `check_docs_structure.py` の既存機能を変更しない

## Acceptance Criteria
- Follow-up Work Needed に GV-007 のエントリが存在しない
- Matrix の GV-007 の Status が `Existing` のまま維持されている
- Follow-up Work Needed の番号付けが連続している

## Testing Expectations
- Not required — ドキュメントのみの変更

## Documentation Impact
このドキュメント自体が対象。Governance Verification Matrix と Follow-up Work Needed の一貫性が確保される。

## Out of Scope
- Matrix の他のルールとのステータス矛盾の修正
- `check_docs_structure.py` の機能追加・変更

## Dependencies
- N/A: none

## Unresolved Questions
- Follow-up Work Needed の欠番（1-3）の原因は何か？削除された項目の記録は必要か？

## AI Implementation Instruction
1. `docs/00_governance/governance_04_documentation-checks.md` の Follow-up Work Needed セクションを開く
2. `GV-007: Implement Duplicate Related Link prohibition check` のエントリを削除
3. Follow-up Work Needed の番号付けを確認し、欠番があれば修正
4. Matrix の GV-007 の Status が `Existing` のままになっていることを確認

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260926-183302
- **Related target files**: docs/00_governance/governance_04_documentation-checks.md
