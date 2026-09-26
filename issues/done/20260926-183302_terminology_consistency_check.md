# Terminology Glossary — 用語の一貫性の確認

## Priority
Low

## Summary
`governance_02_documentation-metadata.md` の Terminology Glossary に `Obsolete` / `Dead Code` / `Deprecated` の区別が記載されているが、他の文書でも同じ定義が使われているか確認が必要。特に `governance_04_documentation-checks.md` の Evidence Label Validation で言及されている "Deprecated" が Glossary の "Obsolete" と同じ意味かどうか不明確。

## Background
`governance_02_documentation-metadata.md` の Terminology Glossary には以下の定義がある：
- **Obsolete**: A named entity that still exists in source and remains callable, but is no longer the current production path for its original purpose — superseded by a different mechanism.
- **Dead Code**: A named entity that exists in source with zero current callers anywhere in the codebase — distinct from Obsolete, which may still be reachable via a legacy path.

一方、`governance_04_documentation-checks.md` の Evidence Label Validation では "Deprecated" が evidence label として定義されており、これは "Describes an obsolete feature no longer in use." と説明されている。

## Problem
Evidence Label Validation の "Deprecated" と Terminology Glossary の "Obsolete" が同じ意味かどうか不明確。また、他の文書でも同じ定義が使われているか確認が必要。

## Reason for Change
用語の一貫性を確保することで、実装担当者が正確な用語の意味を理解できるようにするため。

## Implementation Intent
以下のいずれかの対応を行う：
1. Evidence Label Validation の "Deprecated" と Terminology Glossary の "Obsolete" が同じ意味なら、その旨を明記
2. Evidence Label Validation の "Deprecated" と Terminology Glossary の "Obsolete" が異なる意味なら、区別を明確化
3. 他の文書でも同じ定義が使われているか確認

## Target Files or Areas
- `docs/00_governance/governance_02_documentation-metadata.md`
- `docs/00_governance/governance_04_documentation-checks.md`

## Required Changes
- Evidence Label Validation の "Deprecated" と Terminology Glossary の "Obsolete" の関係を明記
- 他の文書でも同じ定義が使われているか確認
- 必要に応じて用語の統一

## Constraints
- 既存の用語の定義を変更しない
- 用語の変更は全ての文書で一貫させる

## Acceptance Criteria
- Evidence Label Validation の "Deprecated" と Terminology Glossary の "Obsolete" の関係が明確になっている
- 他の文書でも同じ定義が使われている

## Testing Expectations
- Not required — ドキュメントのみの変更

## Documentation Impact
このドキュメント自体が対象。用語の一貫性が確保される。

## Out of Scope
- 用語の定義変更
- 他の Governance ルールの修正

## Dependencies
- N/A: none

## Unresolved Questions
- Evidence Label Validation の "Deprecated" と Terminology Glossary の "Obsolete" は同じ意味か？
- 他の文書でも同じ定義が使われているか？

## AI Implementation Instruction
1. `docs/00_governance/governance_04_documentation-checks.md` の Evidence Label Validation を開く
2. `docs/00_governance/governance_02_documentation-metadata.md` の Terminology Glossary を開く
3. Evidence Label Validation の "Deprecated" と Terminology Glossary の "Obsolete" の関係を明記
4. 他の文書でも同じ定義が使われているか確認

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260926-183302
- **Related target files**: docs/00_governance/governance_02_documentation-metadata.md, docs/00_governance/governance_04_documentation-checks.md
