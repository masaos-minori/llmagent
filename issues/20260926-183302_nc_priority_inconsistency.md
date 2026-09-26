# NC-027 / NC-028 / NC-029 / NC-033 / NC-034 / NC-035 の Priority 値と NC-036 の不一致

## Priority
Low

## Summary
`governance_03_issue-and-uncertainty-management.md` の Needs Confirmation Inventory で、NC-027 / NC-028 / NC-029 / NC-033 / NC-034 / NC-035 は全て `Low` だが、NC-036 は `High` となっている。なぜ NC-036 だけが High なのかの区別基準が文書内で明確でない。

## Background
Needs Confirmation Inventory の Priority 値は以下のように定義されている：
- **High** — Must resolve before next release
- **Medium** — Resolve within sprint
- **Low** — Nice-to-have

NC-036 は "Is the parse-error-triggers-fallback behavior an intentional refinement of Decision #9 or an unintended deviation?" という質問で、ADR-010 の Decision #9 と実際の挙動の矛盾を示している。これに対して NC-027 / NC-028 / NC-029 / NC-033 / NC-034 / NC-035 は、定数の根拠や設定値の理由に関する質問である。

## Problem
Priority の違いが意図的なものか、それとも不整合なのかを明確にする必要がある。また、なぜ NC-036 だけが High なのかの区別基準が文書内で明確でない。

## Reason for Change
Priority の違いが意図的ならその理由を明記し、不整合なら修正する必要がある。

## Implementation Intent
以下のいずれかの対応を行う：
1. Priority の違いが意図的なら、その理由を文書内に明記
2. Priority の違いが不整合なら、Priority を統一
3. NC-036 の High の理由を明確化

## Target Files or Areas
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md`

## Required Changes
- Needs Confirmation Inventory の Priority 値の一貫性を確認
- Priority の違いが意図的なら理由を明記
- Priority の違いが不整合なら修正

## Constraints
- 既存の項目の内容を変更しない
- Priority の更新は全ての項目で一貫させる

## Acceptance Criteria
- Needs Confirmation Inventory の Priority 値に一貫性がある
- Priority の違いが意図的な場合はその理由が明記されている

## Testing Expectations
- Not required — ドキュメントのみの変更

## Documentation Impact
このドキュメント自体が対象。Needs Confirmation Inventory の一貫性が確保される。

## Out of Scope
- Needs Confirmation Inventory の構造変更
- 他の Governance ルールの修正

## Dependencies
- N/A: none

## Unresolved Questions
- なぜ NC-036 だけが High なのか？
- 他の NC 項目も High にすべきか？

## AI Implementation Instruction
1. `docs/00_governance/governance_03_issue-and-uncertainty-management.md` の Needs Confirmation Inventory を開く
2. 各項目の Priority 値を確認
3. Priority の違いが意図的なら理由を明記
4. Priority の違いが不整合なら修正

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260926-183302
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md
