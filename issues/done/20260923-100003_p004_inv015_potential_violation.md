# P0-004: INV-015 (ADR-010) の潜在的な違反 — RAG 4xx エラー時のフォールバック

## Priority
High

## Summary
`adr-index.md:85` で ADR-010 の invariant INV-015 が「Potentially violated」としてマークされている。`http_augment.py` が 4xx/parse エラー時にローカルフォールバックを実行しており、ADR-010 が規定する「RAG の外部実行失敗時のインプロセスフォールバック」の範囲を超えている可能性がある。

## Background
ADR-010（RAGの外部実行失敗時のインプロセスフォールバック）は、RAG の外部実行が失敗した場合のフォールバック動作を規定している。INV-015 は「No local fallback on RAG 401/403」を不変条件としており、401/403 エラー時はフォールバックすべきでない。しかし、現在のコードでは 4xx 全般と parse エラー時にフォールバックが発生している。

## Problem
INV-015 の不変条件が潜在的に違反している。401/403 エラー時にフォールバックが発生する場合、認証エラーを隠蔽し、セキュリティ上の問題を引き起こす可能性がある。また、4xx エラーと parse エラーの区別が明確でない場合、本来エラーとするべきケースでフォールバックしてしまう。

## Reason for Change
セキュリティ関連の不変条件の違反は、認証・認可の誤った処理を招き、本番環境での重大な影響をもたらす可能性がある。まず現状のコードを検証し、違反が確認されれば是正する必要がある。

## Implementation Intent
1. `scripts/rag/http_augment.py` の 4xx エラー処理を確認し、401/403 エラー時にフォールバックが発生するか検証する
2. 違反が確認されれば、401/403 エラー時はフォールバックせず、エラーを伝播するように修正する
3. 該当する不変条件（INV-015）の検証ステータスを更新する
4. 関連するテストを追加し、将来の回帰を防ぐ

## Target Files or Areas
- `scripts/rag/http_augment.py`
- `adr-index.md`
- `adr/ADR-010-rag-fallback.md`
- `tests/` （関連テスト）

## Required Changes
- `scripts/rag/http_augment.py` の 4xx エラー処理の検証
- 必要に応じて 401/403 エラー時のフォールバック抑制
- INV-015 の検証ステータスの更新
- テストカバレッジの追加

## Constraints
- 401/403 エラー時のフォールバックを許可してはならない
- 既存の RAG フォールバック動作（4xx 以外）を変更してはならない

## Acceptance Criteria
- [ ] `scripts/rag/http_augment.py` の 401/403 エラー処理が ADR-010 の規定に合致している
- [ ] 401/403 エラー時にフォールバックが発生しないことを確認
- [ ] INV-015 の検証ステータスが更新されている
- [ ] 関連テストが存在し、401/403 エラー時の挙動がカバーされている

## Testing Expectations
- 401/403 エラー時のフォールバック発生を防止するユニットテスト
- 既存の RAG フォールバックテストとの整合性確認
- `uv run pytest` 全テストのパス確認

## Documentation Impact
- `adr-index.md` の INV-015 セクションの更新が必要
- ADR-010 の Completion Checklist の更新が必要

## Out of Scope
- 4xx 以外のエラー処理の変更
- 他の ADR invariant の是正
- RAG フォールバック全体の再設計

## Dependencies
- ADR-010 の要件定義

## Unresolved Questions
- 401/403 エラー時にフォールバックが発生する場合、その意図的な設計かどうか（設定による切り替えの可能性）

## AI Implementation Instruction
- まず `scripts/rag/http_augment.py` の 401/403 エラー処理を検証する
- 違反が確認されれば、401/403 エラー時はフォールバックせずエラーを伝播するように修正する
- 401/403 エラー時のフォールバックが意図的な設計である場合は、ADR-010 の要件定義自体の見直しが必要
- テストを追加し、将来の回帰を防ぐ

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260923-100003
- **Related target files**: scripts/rag/http_augment.py, adr-index.md, adr/ADR-010-rag-fallback.md
