# Manual Checks — 番号付きチェックと番号なしチェックの混在

## Priority
Low

## Summary
`governance_04_documentation-checks.md` の Manual Checks セクションで、9-14 の番号付きチェックと、番号なしのチェックが混在している。番号なしのチェックは "Evidence Label Validation" と "ADR Section Header Compliance" の2つ。

## Background
Manual Checks セクションでは、9-14 の番号付きチェックが存在するが、"Evidence Label Validation" と "ADR Section Header Compliance" は番号なしで記載されている。これは番号付けの不整合であり、実装担当者がどのチェックが実装済みかを判断しにくくなる。

## Problem
番号付きチェックと番号なしチェックが混在しているため、実装担当者がどのチェックが実装済みかを判断しにくくなる。また、番号付けの欠番が生じている可能性もある。

## Reason for Change
Manual Checks の番号付けを一貫させることで、実装担当者がどのチェックが実装済みかを容易に判断できるようにするため。

## Implementation Intent
Manual Checks の番号付けを再確認し、欠番があれば補完するか、番号なしのチェックに番号を付与する。

## Target Files or Areas
- `docs/00_governance/governance_04_documentation-checks.md`

## Required Changes
- Manual Checks の番号付けを再確認
- 欠番があれば補完
- 番号なしのチェックに番号を付与

## Constraints
- 既存のチェックの内容を変更しない
- 番号付けの変更は Manual Checks のみ

## Acceptance Criteria
- Manual Checks の番号付けが一貫している
- 欠番がない

## Testing Expectations
- Not required — ドキュメントのみの変更

## Documentation Impact
このドキュメント自体が対象。Manual Checks の一貫性が確保される。

## Out of Scope
- チェックの内容変更
- Automated Checks の番号付け変更

## Dependencies
- N/A: none

## Unresolved Questions
- 欠番（1-8）の原因は何か？削除された項目の記録は必要か？

## AI Implementation Instruction
1. `docs/00_governance/governance_04_documentation-checks.md` の Manual Checks を開く
2. 番号付きチェックと番号なしチェックを確認
3. 欠番があれば補完
4. 番号なしのチェックに番号を付与

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260926-183302
- **Related target files**: docs/00_governance/governance_04_documentation-checks.md
