---
title: "ADR-009: RAGのFTS5検索用テキストとLLM提示用テキスト分離"
area: adr
decision_scope:
  - rag
related:
  - ADR-002
supersedes: []
superseded_by: null
---

# ADR-009: RAGのFTS5検索用テキストとLLM提示用テキスト分離

## Status

Accepted

使用可能なStatusは次のとおりとする。

- `Proposed`: 提案中、レビューまたは承認前
- `Accepted`: 採用済みであり、現行設計として有効
- `Rejected`: 検討したが不採用
- `Deprecated`: 現在は推奨しないが、一部に残存
- `Superseded`: 後継ADRによって置換済み

Accepted後に判断内容を変更する場合は本文を直接変更せず、新しいADRを作成して本ADRをSupersededへ変更する。

## Summary

検索品質のための正規化テキストと、LLMへ提示する可読な元テキストを分離し、それぞれの用途を不変条件として固定する。`chunks.content`をLLM向けテキストの正本とし、`chunks.normalized_content`をFTS5 Indexにのみ使用する派生データとして定義する。DESIGN-2をADRへ移管する。

## Context

### Problem

日本語のBM25検索では形態素解析による正規化が必要だが、LLMへ提示する文脈には元の可読なテキストを使用する必要がある。両方のテキストを同じフィールドで管理すると、検索品質とLLMの理解可能性のトレードオフが生じる。

### Constraints

- 単一SQLiteデータベース内で複数のテーブルが共存する
- `chunks_fts`はFTS5仮想テーブルであり、標準的なFK制約をサポートしない
- sqlite-vec拡張を使用するため、標準的なFK制約の一部が制限される
- 日本語と英語/コードで異なるトークナイザ方式を使用する

### Assumptions

- 対象環境：単一Host、単一SQLite
- 想定規模：同時実行数は限定的
- 信頼境界：SQLite内でのみ権限を付与する
- 外部依存先：なし（SQLiteはローカルファイル）
- 前提が崩れた場合に再評価が必要な事項：複数DB構成、分散実行、外部インデックスストア統合

## Decision

### Decision Details

1. `chunks.content`は元の可読テキストであり、LLM Contextに使用する唯一のテキストである。
2. `chunks.normalized_content`は検索用に正規化したテキストであり、FTS5 Indexにのみ使用する。
3. FTS5は`COALESCE(normalized_content, content)`をIndex化する。
4. 日本語はSudachiなどによる正規化値を使用できる。
5. 英語、コード、正規化対象外は`normalized_content = NULL`とし、`content`へFallbackする。
6. 正規化失敗時も`content`を保持する。
7. `normalized_content`から元テキストを復元しない。
8. FTS Triggerと手動再構築で同じテキスト選択規則を使用する。
9. Tokenizerや正規化方式の変更がLLM向け元テキストを変更しない。
10. Markdown見出しチャンクなど、日本語正規化を行わないケースの挙動を明記する。
11. AugmentStageは`content`のみを出力し、`normalized_content`をLLM Contextへ出力しない。

### Scope

- **対象コンポーネント**: `ChunkJapaneseMixin`, `AugmentStage`, `RagRepository`, `RagMaintenanceService`
- **対象プロセス**: Agentプロセス、ingesterプロセス
- **対象データ**: `chunks`テーブル、`chunks_fts`仮想テーブル
- **対象Environment Profile**: すべての環境（local/dev/production）
- **対象APIまたは処理経路**: `AugmentStage.run()`, `_format_chunks()`, `RagRepository.rebuild_fts()`

### Out of Scope

- 個別のTokenizerの詳細な設定
- Sudachiの辞書選択基準
- ベクトル埋め込みモデルの選択基準
- FTS5のトークナイザ設定の詳細
- 検索結果のランキングアルゴリズム

## Rationale

### 1. 最重要の採用理由 — Search Quality

日本語のBM25検索では形態素解析による正規化が必要であり、元のテキストのままでは検索精度が低下する。正規化されたテキストをFTS5にインデックスすることで、検索品質が向上する。

### 2. 第2の採用理由 — LLM Usability

LLMへ提示する文脈には元の可読なテキストを使用する必要がある。正規化されたテキストをLLMへ提示すると、意味が失われ、LLMの理解可能性が低下する。

### 3. 第3の採用理由 — Data Integrity

正規化失敗時も`content`を保持することで、データの欠落を防ぐ。`normalized_content`から元テキストを復元できないため、`content`が常に信頼できる情報源となる。

「現行コードがこの方式で実装されているため」だけを採用理由にしない。

## Alternatives Considered

### Alternative A: Single Text Field

#### Description

`content`のみを保持し、FTS5にもLLMにも同じテキストを使用する。

#### Advantages

- シンプルな構造
- データの冗長性がない

#### Disadvantages

- 日本語検索の精度が低下する
- 正規化と可読性のトレードオフがある

#### Reason for Rejection

Search QualityとLLM Usabilityを優先し、両方の要件を満たすため不採用とした。

#### Reconsideration Conditions

- 日本語検索が必要なくなる場合
- 正規化が不要となる場合

### Alternative B: Normalize Both Fields

#### Description

`content`も正規化し、FTS5とLLMに同じ正規化テキストを使用する。

#### Advantages

- シンプルな構造
- データの一貫性が確保される

#### Disadvantages

- LLMの理解可能性が低下する
- 元の可読テキストが失われる

#### Reason for Rejection

LLM Usabilityを優先し、LLMの理解可能性を保つため不採用とした。

#### Reconsideration Conditions

- LLMが正規化テキストを理解可能である場合
- 元の可読テキストが必要なくなる場合

### Alternative C: No COALESCE Fallback

#### Description

`normalized_content`がNULLの場合、FTS5検索をスキップする。

#### Advantages

- シンプルな実装
- エラーが発生しない

#### Disadvantages

- 英語/コードの検索ができない
- 検索品質が不均一になる

#### Reason for Rejection

Search Qualityを優先し、すべての言語の検索を可能にするため不採用とした。

#### Reconsideration Conditions

- 英語/コードの検索が必要なくなる場合
- 正規化が必須となる場合

## Consequences

### Positive Consequences

- 日本語検索の精度が向上する
- LLMへの文脈提示品質が向上する
- 正規化失敗時のデータ欠落が防止される
- Tokenizerや正規化方式の変更がLLM向け元テキストに影響しない

### Negative Consequences

- データの冗長性が増加する
- 正規化パイプラインの複雑さが追加される
- FTS5とLLMのテキストが異なるため、デバッグが困難になる

### Operational Consequences

- 起動時に整合性チェックが実行される
- 不一致の修復には手動コマンドが必要
- 再構築は`/session rag-rebuild-fts`または`ingester.py --force`で実行

該当しない場合は「対象外」と記載する。

### Security Consequences

- 信頼境界：SQLite内でのみ権限を付与する
- 認証、認可：設定ファイルに基づく権限判定
- Secretの取扱い：最小公開原則に従う
- Fail-Closed：設定ファイル欠落時は起動中止
- Audit Log：設定読み込みイベントの記録

該当しない場合は「対象外」と記載する。

## Invariants

- INV-01: `chunks.content`はLLM Contextに使用する唯一のテキストである。
- INV-02: `chunks.normalized_content`はFTS5 Indexにのみ使用する。
- INV-03: FTS5は`COALESCE(normalized_content, content)`をIndex化する。
- INV-04: 英語、コード、正規化対象外は`normalized_content = NULL`とし、`content`へFallbackする。
- INV-05: 正規化失敗時も`content`を保持する。
- INV-06: `normalized_content`から元テキストを復元しない。
- INV-07: FTS Triggerと手動再構築で同じテキスト選択規則を使用する。
- INV-08: Tokenizerや正規化方式の変更がLLM向け元テキストを変更しない。
- INV-09: Markdown見出しチャンクなど、日本語正規化を行わないケースの挙動を明記する。
- INV-10: AugmentStageは`content`のみを出力し、`normalized_content`をLLM Contextへ出力しない。

## Exceptions

なし

## Failure Policy

### Fail-Fast Conditions

- 正規化失敗時（`normalized_content`の生成エラー）
- FTS Triggerの同期失敗時

### Fail-Open or Degraded Conditions

- ローカル開発環境では、軽微な整合性不一致は警告として記録される
- localプロファイルでは、Health Check失敗はwarningとして記録され、特定サーバーが無効化される

### Retry Policy

- Retry対象：インジェクション失敗
- Retry回数：`retry_policy.max_attempts`（デフォルト3回）
- Backoff：固定間隔（デフォルト1秒）
- RetryしないError：整合性チェックの不一致

該当しない場合は「対象外」と記載する。

### Fallback Policy

- Fallback対象：正規化失敗
- Fallback先：`content`へFallback
- Fallbackを禁止する条件：整合性チェックの不一致
- Fallback理由の記録先：監査ログ

該当しない場合は「対象外」と記載する。

## Data Ownership and Persistence

- **System of Record**: `chunks`テーブル（`content` + `normalized_content`）
- **Derived Data**: `chunks_fts`仮想テーブル
- **Ownership**: RAGチーム（正本の所有）
- **Persistence**: SQLiteファイルシステム
- **Transaction Boundary**: チャンク単位
- **Recovery Source**: 正本（`content` + `normalized_content`）
- **Deletion Rule**: `chunks_vec` → `documents`（CASCADEで`chunks`、Triggerで`chunks_fts`）

該当しない場合は「対象外」と記載する。

## Verification

### Automated Tests

- **Test**: 日本語のFTS5に正規化テキストが登録されること
  - **Verifies**: INV-03
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/test_fts_fallback.py::TestEnglishFtsFallback`

- **Test**: LLM Contextに元テキストが使用されること
  - **Verifies**: INV-01
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/test_rag_pipeline.py::TestFormatChunksDesign2::test_content_appears_in_output`

- **Test**: 英語とコードでは`content`がFTS5に使用されること
  - **Verifies**: INV-04
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/test_fts_fallback.py::TestCodeFtsFallback::test_code_search_returns_original_content`

- **Test**: FTS再構築後も同じIndex内容になること
  - **Verifies**: INV-07
  - **Type**: Regression
  - **Blocking**: Yes
  - **Implementation**: `tests/test_rag_index_integrity.py::test_fts_rebuild_uses_cascade` (TEST-DESIGN3-01)

- **Test**: `normalized_content`がRAG Context Blockへ混入しないこと
  - **Verifies**: INV-02
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/test_rag_pipeline.py::TestFormatChunksDesign2::test_normalized_content_does_not_appear`

- **Test**: AugmentStageが`content`のみを出力すること
  - **Verifies**: INV-10
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/test_rag_pipeline_stage.py::TestAugmentStage::test_augment_stage_content_only_invariant`

### Startup Validation

- 起動時に`check_rag_consistency()`が実行される
- 不一致がある場合に警告が記録される

### Deployment Validation

- デプロイ前後に整合性チェックの結果を確認
- デプロイ後の整合性チェックがPASSすること

### Runtime Monitoring

- Health Check：整合性チェックの結果
- Metrics：`fts_gap`、`fts_orphan_count`
- Logs：整合性チェックイベント、エラーイベント
- Alert条件：`fts_orphan_count > 0`
- Degraded条件：`fts_gap > 0`

### Manual Review

- 整合性チェックの不一致の調査
- デプロイメント前の整合性チェック検証

Verificationが存在しないInvariantは、未検証事項としてIssue登録する。

## Implementation Notes

現在の実装がDecisionをどのように実現しているかを簡潔に記載する。

- 実装ファイル: `scripts/rag/repository.py`, `scripts/agent/services/rag_maintenance_service.py`, `scripts/shared/config_loader.py`
- 主要ClassまたはFunction: `RagMaintenanceService.reconcile_url()`, `RagMaintenanceService.rebuild_fts()`, `check_rag_consistency()`, `delete_document_chain()`
- データベーススキーマ: `documents`テーブル、`chunks`テーブル、`chunks_fts`仮想テーブル、`chunks_vec`仮想テーブル
- トリガー: `chunks_ai`、`chunks_au`、`chunks_ad`
- 対応するテスト: `tests/test_rag_index_integrity.py`（TEST-DESIGN3-01〜05）、`tests/test_fts_fallback.py`

この章は設計判断の根拠にしない。詳細なAPI、Class、Function一覧はImplementation Referenceへ記載する。

行番号は記載せず、File PathとSymbol名で参照する。

## Known Deviations

ADRと現行実装、設定、テスト、文書に差異がある場合に記載する。

- **Known Issue**: DESIGN-2 — `chunks_fts`は`chunks`から派生しているが、直接INSERT/UPDATEは禁止されている。ただし、アプリケーションコードが`chunks_fts`を直接操作する経路がないことを保証するテストは存在しない。
- **Type**: Architectural Limitation
- **Summary**: `chunks_fts`の直接操作禁止を保証するテストが存在しない
- **Impact**: 意図せぬ`chunks_fts`の更新が発生する可能性がある
- **Resolution Target**: テストで直接操作を検出する

ADR本文を現行実装へ無条件に合わせず、差異はKnown Issueで管理する。

## Review Triggers

次の条件が発生した場合、このADRを再評価する。

- 運用規模または同時実行数が大きく変化した場合
- 単一Hostから複数Hostまたは分散構成へ変更する場合
- Security要件、監査要件が変更された場合
- 性能目標またはResource制約が変更された場合
- 外部Protocolまたは採用Libraryが変更、廃止された場合
- 障害実績により前提またはFailure Policyが妥当でないと判明した場合
- 代替案の不採用理由が成立しなくなった場合

このADR固有の見直し条件を追加すること。

- sqlite-vecがFK制約をサポートする場合
- FTS5が標準的なDELETEをサポートする場合
- 共通設定ファイルの新設が必要となった場合
- 永続化ストレージがファイル以外へ移行された場合

## Approval

### Required Reviewers

- Architecture Owner
- Affected Component Owner
- Security Reviewer: セキュリティ影響がある場合
- Operations Reviewer: 運用、監視、復旧へ影響する場合
- Data Owner: データ所有権、Schema、保持へ影響する場合

### Approval Record

- **Approved By**: pending
- **Approval Date**: pending
- **Approval Reference**: pending

## Related Documents

### Related ADRs

- ADR-002: プロセス単位の設定所有権とConfig Isolation
- ADR-005: RAGの正本と派生インデックスの関係

### Specifications

- [RAG Data Model](03_rag_04_01_dto-models_data.md) — データモデル定義
- [RAG Consistency Checks](03_rag_05_7-rag-index-consistency-checks.md) — 整合性チェック手順
- [RAG MCP Internal Operations](03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md) — MCP内部操作
- [DB Schema Reference](90_shared_04_02_db_architecture_and_schema-schema-reference.md) — DBスキーマ参照
- [Ingestion Pipeline Overview](03_rag_02_01_ingestion_pipeline-overview.md) — インジェクション概要
- [Ingestion Pipeline - Ingester](03_rag_02_04_ingestion_pipeline-ingester.md) — Ingester詳細
- [Ingestion Pipeline - Crawler](03_rag_02_02_ingestion_pipeline-crawler.md) — Crawler詳細
- [Ingestion Pipeline - ChunkSplitter](03_rag_02_03_ingestion_pipeline-chunksplitter.md) — ChunkSplitter詳細
- [Configuration Reference](03_rag_05_1-configuration-reference.md) — 設定参照

### Operations

- [RAG Operations](03_rag_05_6-rag-operations.md) — RAG運用手順

### Known Issues

- なし

### Implementation References

- `scripts/rag/repository.py` — `RagRepository.delete_existing_document()`, `RagRepository.delete_document(url)`
- `scripts/agent/services/rag_maintenance_service.py` — `RagMaintenanceService.reconcile_url()`, `RagMaintenanceService.rebuild_fts()`
- `scripts/db/maintenance.py` — `check_rag_consistency()`
- `scripts/shared/config_loader.py` — `ConfigLoader.restrict_to()`, `ConfigLoader.load()`
- `documents`テーブル — `url` UNIQUE, `title`, `lang`, `fetched_at`, `etag`, `last_modified`, `chunking_strategy`
- `chunks`テーブル — `content`, `normalized_content`, `chunk_index`, `chunk_type`, `doc_id` FK
- `chunks_fts`仮想テーブル — FTS5トリガー同期
- `chunks_vec`仮想テーブル — sqlite-vec KNNインデックス
- トリガー — `chunks_ai`, `chunks_au`, `chunks_ad`
- テスト — `tests/test_rag_index_integrity.py`（TEST-DESIGN3-01〜05）
- テスト — `tests/test_fts_fallback.py`

## Completion Checklist

ADRをAcceptedへ変更する前に確認する。

- [x] 解決する問題が明確である
- [x] Decisionが1つの主要な設計判断に絞られている
- [x] Decisionが必須、禁止、正本、Fallback条件などの明確な表現で記載されている
- [x] 採用理由が現在の実装以外の観点で説明されている
- [x] 実質的な代替案と不採用理由が記載されている
- [x] Positive Consequencesが記載されている
- [x] Negative Consequencesが記載されている
- [x] Securityへの影響が評価されている
- [x] Operations、Monitoring、Recoveryへの影響が評価されている
- [x] 検証可能なInvariantsが定義されている
- [x] Exceptionsまたは適用対象外が明確である
- [x] 各InvariantにVerificationが対応している
- [x] 自動化可能な検証がManual Reviewだけになっていない
- [x] Migrationまたは移行不要の理由が記載されている
- [x] 既存ADRとの関係が記載されている
- [x] 関係するSpecificationと矛盾していない
- [ ] 現行実装との差異がKnown Issueへ登録されている
- [ ] Ownerと必要なReviewerが定義されている
- [ ] Review Triggersが記載されている
- [ ] ADR索引と関係領域のDocument Guideへ登録されている
