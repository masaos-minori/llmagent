# Governance Verification Matrix — GV-020 / GV-021 ステータスと Follow-up の矛盾

## Priority
Medium

## Summary
`governance_04_documentation-checks.md` の Governance Verification Matrix で GV-020 が `Partial`、GV-021 が `Existing` とされているが、Follow-up Work Needed セクションにそれぞれ実装タスクが残っている。ステータスと Follow-up の内容が矛盾している。

## Background
- GV-020: "Removed-name reintroduction in current specifications" — Status: Partial、Follow-up: `Implement the context-aware (retained-but-superseded) detection case; promote to default-on once the corpus is compliant`
- GV-021: "Docs content policy violation (implementation detail in docs/*.md)" — Status: Existing、Follow-up: `Promoted to default-on after corpus compliance`

両方とも既にツールが存在する（`check_compat_shims.py --check-removed-names`、`check_docs_content_policy.py`）が、Follow-up に「プロモーション」や「実装」のタスクが残っている。

## Problem
Matrix の Status が `Partial` または `Existing` だが Follow-up に未完了タスクが残っているため、実装範囲が明確でない。また、GV-021 の "Promoted to default-on after corpus compliance" という記述は、現在の状態が不明確。

## Reason for Change
ステータスと Follow-up の矛盾を解消し、実装担当者が正確な実装範囲を理解できるようにするため。

## Implementation Intent
以下のいずれかの対応を行う：
1. Follow-up Work Needed から GV-020 / GV-021 のエントリを削除（既に実装済みなら）
2. Matrix の Status を適切な値に更新（未実装部分があるなら）
3. Follow-up Work Needed の記述を現在の状態に合わせて修正

## Target Files or Areas
- `docs/00_governance/governance_04_documentation-checks.md`
- `tools/check_compat_shims.py`
- `tools/check_docs_content_policy.py`

## Required Changes
- `check_compat_shims.py` の実装範囲を確認
- `check_docs_content_policy.py` の実装範囲を確認
- Matrix と Follow-up のどちらかを正しい状態に合わせる

## Constraints
- 既存のツールの機能を壊さない
- Status の更新は Matrix と Follow-up の両方で一貫させる

## Acceptance Criteria
- Matrix の Status と Follow-up Work Needed の内容が矛盾していない
- 各ルールの実装範囲が文書とコードで一致している

## Testing Expectations
- Not required — ドキュメントのみの変更（ただし実装範囲の確認にはテスト実行が必要）

## Documentation Impact
このドキュメント自体が対象。Governance Verification Matrix と Follow-up Work Needed の一貫性が確保される。

## Out of Scope
- ツールの機能追加・変更（実装範囲の確認のみ）
- 他の Governance ルールのステータス修正

## Dependencies
- N/A: none

## Unresolved Questions
- GV-020 の "context-aware (retained-but-superseded) detection case" の実装状況は？
- GV-021 の "corpus compliance" の定義と達成状況は？

## AI Implementation Instruction
1. `tools/check_compat_shims.py` と `tools/check_docs_content_policy.py` の実装を確認
2. 各ツールの現在のカバレッジを評価
3. `docs/00_governance/governance_04_documentation-checks.md` の Matrix と Follow-up を修正
   - 既に実装済み → Follow-up エントリを削除
   - 部分的に実装済み → Matrix を `Partial` に更新 + Follow-up を修正
4. Follow-up Work Needed の番号付けを確認

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260926-183302
- **Related target files**: docs/00_governance/governance_04_documentation-checks.md
