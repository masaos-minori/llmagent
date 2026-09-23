# P0-002: `common.toml` の参照が残っている — ファイルは削除済み

## Priority
High

## Summary
`docs/03_rag_02_04_ingestion_pipeline-ingester.md` の 2箇所で `common.toml::embedding_dims` を参照しているが、`config/common.toml` は既に存在しない。設定は `config/agent.toml` に統合済みであり、この参照は誤った情報をもたらす。

## Background
プロジェクトの設定ファイルは `config/common.toml` から `config/agent.toml` に統合された。`docs/02_deployment.md:81` でもこの変更は記録されている（"Previous documentation and scripts referred to `config/common.toml`, but this has been corrected to `config/agent.toml`."）。しかし、RAG ingestion pipeline のドキュメントで古い参照が残っている。

## Problem
`docs/03_rag_02_04_ingestion_pipeline-ingester.md:163,237` で `common.toml::embedding_dims` を参照している。このファイルは存在せず、開発者が誤ったパスをたどる可能性がある。

## Reason for Change
設定ファイルの統合後にドキュメントの更新が漏れており、実装とドキュメントの乖離が発生している。これはデプロイメントや設定の理解に直接的な誤解をもたらす。

## Implementation Intent
1. `docs/03_rag_02_04_ingestion_pipeline-ingester.md` の `common.toml` 参照をすべて `agent.toml` 参照に置き換える
2. `embedding_dims` の実際の設定場所を確認し、正しいパスを記載する
3. 必要に応じて `config/agent.toml` の該当セクションを確認し、設定値の整合性を取る

## Target Files or Areas
- `docs/03_rag_02_04_ingestion_pipeline-ingester.md`
- `config/agent.toml`
- `scripts/rag/ingestion/ingester.py`

## Required Changes
- `docs/03_rag_02_04_ingestion_pipeline-ingester.md:163` の `common.toml::embedding_dims` を正しいパスに更新
- `docs/03_rag_02_04_ingestion_pipeline-ingester.md:237` の同様の参照を更新

## Constraints
- `common.toml` の復活を行ってはならない
- 既存の設定値を変更してはならない

## Acceptance Criteria
- [ ] `docs/03_rag_02_04_ingestion_pipeline-ingester.md` に `common.toml` の参照が残っていない
- [ ] 全ての設定参照が `config/agent.toml` または対応するモジュールを指している
- [ ] `grep -rn 'common\.toml' docs/` で RAG ingestion pipeline ドキュメント以外のみがヒットする

## Testing Expectations
- ドキュメントの一貫性チェックツールで警告がないことを確認
- `grep -rn 'common\.toml' docs/` で RAG ingestion pipeline ドキュメント以外のみがヒットすることを確認

## Documentation Impact
- `docs/03_rag_02_04_ingestion_pipeline-ingester.md` の更新が必要
- 他のドキュメントで `common.toml` の参照が残っていないか併せて確認すべき

## Out of Scope
- `common.toml` の復活
- 設定値自体の変更
- ドキュメント外のコード修正

## Dependencies
- N/A: none

## Unresolved Questions
- N/A: none

## AI Implementation Instruction
- `docs/03_rag_02_04_ingestion_pipeline-ingester.md` のみ修正する
- `common.toml` の参照を `agent.toml` または対応するモジュールパスに置き換える
- 設定値の変更は行わない

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260923-100001
- **Related target files**: docs/03_rag_02_04_ingestion_pipeline-ingester.md, config/agent.toml, scripts/rag/ingestion/ingester.py
