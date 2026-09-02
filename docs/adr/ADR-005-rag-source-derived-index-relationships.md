---
title: "ADR-005: RAGの正本と派生インデックスの関係"
area: adr
decision_scope:
  - rag
related:
  - ADR-002
supersedes: []
superseded_by: null
---

# ADR-005: RAGの正本と派生インデックスの関係

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

`documents`と`chunks`を文書・チャンク内容の正本とし、`chunks_fts`と`chunks_vec`を再構築可能な派生インデックスとして定義し、整合性確認、削除順序、復旧の基準を一意にする。DESIGN-3の判断をADRへ統合する。

## Context

### Problem

RAGインフラでは`documents`、`chunks`、`chunks_fts`、`chunks_vec`の4つのデータストアが存在し、それぞれが異なる役割を持つ。派生インデックスから正本を更新する誤りや、削除順序の不整合により孤立レコードが発生するリスクがある。また、FTS5とVector Engineを交換しても再構築できるという設計上の保証が必要。

### Constraints

- 単一SQLiteデータベース内で複数のテーブルが共存する
- `chunks_fts`はFTS5仮想テーブルであり、標準的なFK制約をサポートしない
- `chunks_vec`はsqlite-vec拡張であり、標準的なFK制約をサポートしない
- 削除時に`chunks_vec`にFKがないため、明示的な削除が必要
- 整合性チェックは起動時と手動で実行される

### Assumptions

- 対象環境：単一Host、単一SQLite
- 想定規模：同時実行数は限定的
- 信頼境界：SQLite内でのみ権限を付与する
- 外部依存先：なし（SQLiteはローカルファイル）
- 前提が崩れた場合に再評価が必要な事項：複数DB構成、分散実行、外部インデックスストア統合

## Decision

### Decision Details

1. `documents`は文書単位の正本である。URLごとのメタデータを保持し、`url` UNIQUE制約を持つ。
2. `chunks`はチャンク内容の正本である。`content`、`normalized_content`、`chunk_index`、`doc_id` FK（ON DELETE CASCADE）を持つ。
3. `chunks_fts`は`chunks`から生成する全文検索用派生インデックスである。AFTER INSERT/AFTER UPDATE/AFTER DELETEトリガーで同期する。
4. `chunks_vec`は`chunks`から生成するベクトル検索用派生インデックスである。インジェクションパイプライン中に明示的INSERT、削除時に明示的DELETEを行う。
5. 派生インデックスから正本を更新しない。`chunks_fts`への直接INSERT/UPDATEは禁止し、`/session rag-rebuild-fts`のみ許可する。
6. 整合性チェックでは`chunks`を基準に差分を検出する。
7. 文書削除時は対象`chunks_vec`を先に削除し、その後`documents`を削除する（CASCADEで`chunks`も削除され、Triggerで`chunks_fts`が同期）。
8. FTS5の通常同期と手動再構築で同じ生成規則を使う（`COALESCE(normalized_content, content)`）。
9. FTS5またはVector Engineを交換しても、`documents`と`chunks`から再構築できる。
10. 次の運用判断をOperationsへ反映する：
    - `fts_gap > 0`: FTS5を再構築
    - `fts_orphan_count > 0`: FTS5を再構築
    - `orphan_vec_count > 0`: 対象文書を再インジェスト
    - `vec != chunks`: 埋め込みまたは同期失敗として調査
11. Ingestion経路とMCP削除経路が同じ削除ヘルパーまたは同じ不変条件を使用する。

### Scope

- **対象コンポーネント**: `DocumentManager`, `RagMaintenanceService`, `check_rag_consistency()`
- **対象プロセス**: Agentプロセス、ingesterプロセス
- **対象データ**: `documents`テーブル、`chunks`テーブル、`chunks_fts`仮想テーブル、`chunks_vec`仮想テーブル
- **対象Environment Profile**: すべての環境（local/dev/production）
- **対象APIまたは処理経路**: `DocumentManager.delete_existing_document()`, `DocumentManager.delete_document(url)`, `RagMaintenanceService.reconcile_url()`, `RagMaintenanceService.rebuild_fts()`

### Out of Scope

- 個別のインジェクションステップの詳細
- ベクトル埋め込みモデルの選択基準
- FTS5のトークナイザ設定の詳細
- 検索結果のランキングアルゴリズム

## Rationale

### 1. 最重要の採用理由 — Data Integrity

正本と派生の明確な分離により、データの一貫性が確保される。派生インデックスから正本を更新する誤りを物理的に防止する。

### 2. 第2の採用理由 — Operability

削除順序の不変条件を定義することで、孤立レコードの発生を防ぐ。整合性チェックと修復手順が統一されるため、運用担当者が迷わない。

### 3. 第3の採用理由 — Portability

FTS5とVector Engineを交換しても再構築できるため、将来の技術移行が容易になる。

「現行コードがこの方式で実装されているため」だけを採用理由にしない。

## Alternatives Considered

### Alternative A: Derived indexes as authoritative

#### Description

`chunks_fts`と`chunks_vec`を正本とし、`documents`と`chunks`を派生データとする。

#### Advantages

- インデックスからの逆引きが可能
- 検索結果から原文を再生成できる可能性がある

#### Disadvantages

- 検索インデックスが壊れたときに原文が失われる
- 両方のインデックスが壊れると完全なデータ損失
- 整合性チェックが逆の方向になる

#### Reason for Rejection

Data Integrityを優先し、検索インデックスの破損によるデータ損失を防ぐため不採用とした。

#### Reconsideration Conditions

- 検索インデックスが原文よりも正確な情報源となる場合
- 両方のインデックスの冗長化が確立された場合

### Alternative B: No deletion order invariant

#### Description

削除順序を規定せず、各インデックスが独立してクリーンアップする。

#### Advantages

- シンプルな構造
- 依存関係が少ない

#### Disadvantages

- 孤立レコードの発生
- データ損失のリスク
- 整合性チェックの複雑化

#### Reason for Rejection

Data Integrityを優先し、孤立レコードの発生を防ぐため不採用とした。

#### Reconsideration Conditions

- sqlite-vecがFK制約をサポートする場合
- FTS5が標準的なDELETEをサポートする場合

### Alternative C: Manual sync only

#### Description

トリガーによる自動同期を廃止し、すべてを手動で管理する。

#### Advantages

- 明示的な制御が可能
- トリガーのオーバーヘッドがない

#### Disadvantages

- 人間の操作ミスによる不整合
- リアルタイム同期ができない
- 運用負荷の増大

#### Reason for Rejection

Operabilityを優先し、リアルタイム同期と人間の操作ミスを防止するため不採用とした。

#### Reconsideration Conditions

- トリガーのパフォーマンス問題が深刻化した場合
- 手動同期ツールが十分に成熟した場合

## Consequences

### Positive Consequences

- 正本と派生の明確な分離が確保される
- 削除順序の不変条件により孤立レコードが発生しない
- 整合性チェックと修復手順が統一される
- FTS5とVector Engineの交換が容易になる
- Ingestion経路とMCP削除経路が同じ規則へ統一される

### Negative Consequences

- `chunks_vec`にFKがないため、明示的な削除が必要
- 整合性チェックの閾値が厳格（ゼロ許容）
- トリガーのオーバーヘッド
- 再構築時のコスト

### Operational Consequences

- 起動時に整合性チェックが実行される
- 不一致の修復には手動コマンドが必要
- 再構築は`/session rag-rebuild-fts`または`ingester.py --force`で実行

### Security Consequences

- 信頼境界：SQLite内でのみ権限を付与する
- 認証、認可：設定ファイルに基づく権限判定
- Secretの取扱い：最小公開原則に従う
- Fail-Closed：設定ファイル欠落時は起動中止
- Audit Log：設定読み込みイベントの記録

該当しない場合は「対象外」と記載する。

## Invariants

- INV-01: 派生インデックスから正本を更新しない。
- INV-02: 文書削除時は`chunks_vec` → `documents`の順序で削除する。
- INV-03: FTS5の通常同期と手動再構築で同じ生成規則を使う。
- INV-04: 整合性チェックでは`chunks`を基準に差分を検出する。
- INV-05: Ingestion経路とMCP削除経路が同じ削除ヘルパーを使用する。

## Exceptions

なし

## Failure Policy

### Fail-Fast Conditions

- 整合性チェックで`fts_orphan_count > 0`の場合（データ損失リスク）
- 削除時に`write_mode=True`が有効でない場合（FK無効）

### Fail-Open or Degraded Conditions

- ローカル開発環境では、軽微な整合性不一致は警告として記録される

### Retry Policy

- Retry対象：インジェクション失敗
- Retry回数：`retry_policy.max_attempts`（デフォルト3回）
- Backoff：固定間隔（デフォルト1秒）
- RetryしないError：整合性チェックの不一致

### Fallback Policy

- Fallback対象：なし
- Fallback先：なし
- Fallbackを禁止する条件：整合性チェックの不一致
- Fallback理由の記録先：監査ログ

該当しない場合は「対象外」と記載する。

## Data Ownership and Persistence

- **System of Record**: `documents`テーブル、`chunks`テーブル
- **Derived Data**: `chunks_fts`仮想テーブル、`chunks_vec`仮想テーブル
- **Ownership**: RAGチーム（正本の所有）
- **Persistence**: SQLiteファイルシステム
- **Transaction Boundary**: 文書単位
- **Recovery Source**: 正本（`documents` + `chunks`）
- **Deletion Rule**: `chunks_vec` → `documents`（CASCADEで`chunks`、Triggerで`chunks_fts`）

該当しない場合は「対象外」と記載する。

## Verification

### Automated Tests

- **Test**: 削除後に孤立`chunks_vec`が残らないこと
  - **Verifies**: INV-02
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/test_rag_index_integrity.py::test_deletion_order_invariant` (TEST-DESIGN3-04)

- **Test**: `documents`削除で`chunks`がCascade削除されること
  - **Verifies**: INV-02
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/test_rag_index_integrity.py::test_force_reingest_no_orphan_vectors` (TEST-DESIGN3-03)

- **Test**: FTS Triggerと手動再構築の出力が一致すること
  - **Verifies**: INV-03
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/test_rag_index_integrity.py::test_fts_rebuild_uses_cascade` (TEST-DESIGN3-01)

- **Test**: Gap、Orphanを整合性チェックが検出すること
  - **Verifies**: INV-04
  - **Type**: Regression
  - **Blocking**: Yes
  - **Implementation**: `tests/test_rag_index_integrity.py::test_consistency_check_detects_fts_gap` (TEST-DESIGN3-05)

- **Test**: `chunks_fts`は`chunks`から派生していること（直接INSERTされない）
  - **Verifies**: INV-01
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/test_rag_index_integrity.py::test_chunks_fts_is_derived_index` (TEST-DESIGN3-02)

### Startup Validation

- 起動時に`check_rag_consistency()`が実行される
- 不一致がある場合に警告が記録される

### Deployment Validation

- デプロイ前後に整合性チェックの結果を確認
- デプロイ後の整合性チェックがPASSすること

### Runtime Monitoring

- Health Check：整合性チェックの結果
- Metrics：`fts_gap`、`fts_orphan_count`、`orphan_vec_count`
- Logs：整合性チェックイベント、エラーイベント
- Alert条件：`fts_orphan_count > 0`
- Degraded条件：`fts_gap > 0`または`orphan_vec_count > 0`

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

- **Known Issue**: `sqlite-vec` lacks FK constraints — `chunks_vec` has no foreign key pointing to `chunks`. This is a known architectural limitation of `sqlite-vec` virtual tables. Consequence: Orphaned vector records can exist after document deletion if the explicit `chunks_vec` deletion step is missed. Mitigation: All deletion code paths enforce the `chunks_vec` → `documents` ordering invariant.
- **Type**: Architectural Limitation
- **Summary**: `chunks_vec`にFK制約が存在しない
- **Impact**: 明示的な削除ステップが必要
- **Resolution Target**: sqlite-vecがFK制約をサポートするまで緩和不可

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

- `sqlite-vec`がFK制約をサポートする場合
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

- **Approved By**: タスクレベル承認判断(リポジトリ管理者。個別レビュアー名は記録しない)
- **Approval Date**: 記録なし(タスクレベル承認判断のため個別の承認日は記録しない)
- **Approval Reference**: `docs/00_governance_01_documentation-policy.md` ADR Acceptance Evidence Standard

本ADRの`Accepted`ステータスは、上記ガバナンス文書が定めるタスクレベル承認判断を受理証跡とする。個別レビュアー名・承認日による正式なApproval Recordは作成していない。

## Related Documents

### Related ADRs

- ADR-002: プロセス単位の設定所有権とConfig Isolation

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
