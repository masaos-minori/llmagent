# Area Canonical Maps — Status 値の不統一

## Priority
Low

## Summary
`governance_01_documentation-policy.md` の Area Canonical Maps で、Overview/Deployment/RAG/MCP/Agent/EventBus/Shared/DB の Primary は `(Needs Confirmation — path does not exist in repository)` だが、Governance の Primary は `Active` となっている。同じ "Primary" なのに Status が異なる理由の説明がない。

## Background
Area Canonical Maps は各領域の文書と権威の関係を定義している。Overview/Deployment/RAG/MCP/Agent/EventBus/Shared/DB の Primary は全て `(Needs Confirmation — path does not exist in repository)` となっており、これらのパスがリポジトリに存在しないことを示している。しかし Governance の Primary は `Active` となっており、Status の値が異なる。

## Problem
同じ "Primary" なのに Status が異なる理由の説明がないため、実装担当者が混乱する可能性がある。また、なぜ他の領域の Primary が Needs Confirmation なのか、その理由も不明確。

## Reason for Change
Status の違いが意図的なものか、それとも不整合なのかを明確にする必要がある。

## Implementation Intent
以下のいずれかの対応を行う：
1. Status の違いが意図的なら、その理由を文書内に明記
2. Status の違いが不整合なら、Status を統一
3. Needs Confirmation の理由を明確化

## Target Files or Areas
- `docs/00_governance/governance_01_documentation-policy.md`

## Required Changes
- Area Canonical Maps の Status 値の一貫性を確認
- Status の違いが意図的なら理由を明記
- Status の違いが不整合なら修正

## Constraints
- 既存の文書の構造を壊さない
- Status の更新は全ての領域で一貫させる

## Acceptance Criteria
- Area Canonical Maps の Status 値に一貫性がある
- Status の違いが意図的な場合はその理由が明記されている

## Testing Expectations
- Not required — ドキュメントのみの変更

## Documentation Impact
このドキュメント自体が対象。Area Canonical Maps の一貫性が確保される。

## Out of Scope
- Area Canonical Maps の構造変更
- 他の Governance ルールの修正

## Dependencies
- N/A: none

## Unresolved Questions
- なぜ Overview/Deployment/RAG/MCP/Agent/EventBus/Shared/DB の Primary が Needs Confirmation なのか？
- Governance の Primary が Active である理由は何か？

## AI Implementation Instruction
1. `docs/00_governance/governance_01_documentation-policy.md` の Area Canonical Maps を開く
2. 各領域の Status 値を確認
3. Status の違いが意図的なら理由を明記
4. Status の違いが不整合なら修正

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260926-183302
- **Related target files**: docs/00_governance/governance_01_documentation-policy.md
