---
title: "ADR-008: SQLiteを4DBへ分離する"
area: adr
decision_scope:
  - system
related:
  - ADR-002
supersedes: []
superseded_by: null
---

# ADR-008: SQLiteを4DBへ分離する

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

更新頻度、障害範囲、保持期間、復旧方法が異なるデータを4つのSQLite DBへ分離する判断を正典化する。`rag.sqlite`、`session.sqlite`、`workflow.sqlite`、`eventbus.sqlite`の責務を定義し、DB間Transactionを使用しないことと整合性確保方法を説明する。sqlite-vecの適用範囲を限定し、DBごとのBackup、Recovery、保持方針を整理する。

## Context

### Problem

RAGインデックス、セッション状態、ワークフロー状態、イベントバス状態はそれぞれ異なる更新頻度、ロック競合特性、障害範囲、保持期間、復旧方法を持つ。単一DBで管理すると、WAL競合によるパフォーマンス劣化、障害の伝播、バックアップの複雑化が生じる。

### Constraints

- 単一Host、複数プロセスでの実行を前提とする
- デプロイ環境では起動前に各DBファイルが存在することを確認する必要がある
- sqlite-vec拡張は`rag.sqlite`だけにロードする必要がある
- DB間で物理外部キー、SQL JOIN、分散Transactionを前提としない
- WorkflowまたはEventBusの永続化失敗をログだけで成功扱いにしない

### Assumptions

- 対象環境：単一Host、複数プロセス
- 想定規模：同時実行数は限定的
- 信頼境界：各DB内でのみ権限を付与する
- 外部依存先：なし（SQLiteはローカルファイル）
- 前提が崩れた場合に再評価が必要な事項：複数Host構成、分散実行、外部イベントストア統合

## Decision

### Decision Details

1. `rag.sqlite`: documents、chunks、FTS5、Vector Indexの正本。RAGチームが所有。
2. `session.sqlite`: Agent Session、Message、会話状態の正本。Agentチームが所有。
3. `workflow.sqlite`: Task、Attempt、Approval、Artifact、処理済みEventの正本。Workflowチームが所有。
4. `eventbus.sqlite`: Event、Offset、Delivery、DLQの正本。EventBusチームが所有。
5. DB分離理由として、書込特性、ロック競合、障害分離、保持期間、復旧方法、拡張ロード範囲の違いを記載する。
6. DB間で物理外部キー、SQL JOIN、分散Transactionを前提としない。
7. DB間関連付けにはSession ID、Workflow ID、Event IDなどの論理IDを使用する。
8. DB間整合性はEvent、冪等処理、状態照合で保証する。
9. sqlite-vecは`rag.sqlite`だけにロードする。
10. 各DBに独立したBackup、Recovery、WAL Checkpoint、Health Check、保持期間を定義する。
11. RAGは再構築可能、Sessionは履歴保持、Workflowは再開と監査、EventBusは未処理EventとOffsetを重視する。
12. WorkflowまたはEventBusの永続化失敗をログだけで成功扱いにしない。
13. DB横断Transactionが困難になるトレードオフより、ロック競合回避、障害分離、復旧単純化を優先する理由を記載する。

### Scope

- **対象コンポーネント**: `DbConfig`, `SQLiteHelper`, `create_schema()`
- **対象プロセス**: Agentプロセス、ingesterプロセス、EventBusプロセス
- **対象データ**: `rag.sqlite`, `session.sqlite`, `workflow.sqlite`, `eventbus.sqlite`
- **対象Environment Profile**: すべての環境（local/dev/production）
- **対象APIまたは処理経路**: `DbConfig.rag_db_path`, `DbConfig.session_db_path`, `DbConfig.workflow_db_path`, `DbConfig.eventbus_db_path`

### Out of Scope

- 個別のDBスキーマの詳細
- WAL Checkpointの詳細なパラメータ
- Backupツールやスクリプトの実装
- 監視・メトリクス設計（別ADRで扱う）

## Rationale

### 1. 最重要の採用理由 — Operability

各DBが独立して初期化、接続、Checkpoint、Recoveryできるため、障害範囲が局所化される。1DBの破損が他DBの初期化、復旧を要求しない。

### 2. 第2の採用理由 — Performance

更新頻度の異なるデータが同じDBにある場合、WAL競合によりパフォーマンスが劣化する。RAGは高書込・高読込、SessionはAppend-heavy、Workflowは低頻度だがトランザクション重要、EventBusはリアルタイム配信が優先される。これらの特性が異なるため、分離することでロック競合を回避できる。

### 3. 第3の採用理由 — Data Integrity

各DBに独立したBackup、Recovery、WAL Checkpoint、Health Check、保持期間を定義できる。RAGは再構築可能、Sessionは履歴保持、Workflowは再開と監査、EventBusは未処理EventとOffsetを重視するという違いに対応できる。

「現行コードがこの方式で実装されているため」だけを採用理由にしない。

## Alternatives Considered

### Alternative A: Single SQLite Database

#### Description

すべてのデータを単一SQLite DBで管理する。

#### Advantages

- シンプルな構造
- DB間JOINが可能
- トランザクションが容易

#### Disadvantages

- WAL競合によるパフォーマンス劣化
- 障害の伝播
- バックアップの複雑化
- 保持期間の統一が必要

#### Reason for Rejection

OperabilityとPerformanceを優先し、ロック競合と障害の伝播を防ぐため不採用とした。

#### Reconsideration Conditions

- 同時実行数が非常に少ない場合
- DB間JOINが必要となる場合

### Alternative B: No sqlite-vec extension

#### Description

ベクトル検索にsqlite-vecを使用しない。

#### Advantages

- sqlite-vecの依存関係がない
- 標準的なSQLiteのみで管理できる

#### Disadvantages

- ベクトル検索のパフォーマンスが劣る
- KNN検索が実現できない
- 埋め込み検索の精度が低下

#### Reason for Rejection

Performanceを優先し、高精度なKNN検索を実現するため不採用とした。

#### Reconsideration Conditions

- sqlite-vecが標準的なSQLite拡張としてサポートされる場合
- ベクトル検索が必要なくなる場合

### Alternative C: Cross-database Transactions

#### Description

DB間のトランザクションを可能にする。

#### Advantages

- 一貫性が確保される
- 複合クエリが可能

#### Disadvantages

- 実装が複雑になる
- パフォーマンスが劣化する
- 障害範囲が拡大する

#### Reason for Rejection

Operabilityを優先し、障害範囲の局所化のため不採用とした。

#### Reconsideration Conditions

- DB間の一貫性が必須となる場合
- 複合トランザクションが必要となる場合

## Consequences

### Positive Consequences

- 各DBの独立性が確保される
- 障害範囲が局所化される
- バックアップが容易になる
- 保持期間の個別管理が可能になる
- sqlite-vecの適用範囲が限定される

### Negative Consequences

- DB間JOINができない
- 複合トランザクションが必要になる
- バックアップのスクリプティングが必要
- 障害対応時に複数のDBを確認する必要がある

### Operational Consequences

- 起動時に各DBの接続が確認される
- 設定変更時は所有DBの再起動が必要
- 障害対応時にDBごとの復旧手順が必要

該当しない場合は「対象外」と記載する。

### Security Consequences

- 信頼境界：各DB内でのみ権限を付与する
- 認証、認可：設定ファイルに基づく権限判定
- Secretの取扱い：最小公開原則に従う
- Fail-Closed：設定ファイル欠落時は起動中止
- Audit Log：設定読み込みイベントの記録

該当しない場合は「対象外」と記載する。

## Invariants

- INV-01: `rag.sqlite`はdocuments、chunks、FTS5、Vector Indexの正本である。
- INV-02: `session.sqlite`はAgent Session、Message、会話状態の正本である。
- INV-03: `workflow.sqlite`はTask、Attempt、Approval、Artifact、処理済みEventの正本である。
- INV-04: `eventbus.sqlite`はEvent、Offset、Delivery、DLQの正本である。
- INV-05: DB間で物理外部キー、SQL JOIN、分散Transactionを前提としない。
- INV-06: DB間関連付けにはSession ID、Workflow ID、Event IDなどの論理IDを使用する。
- INV-07: DB間整合性はEvent、冪等処理、状態照合で保証する。
- INV-08: sqlite-vecは`rag.sqlite`だけにロードする。
- INV-09: 各DBに独立したBackup、Recovery、WAL Checkpoint、Health Check、保持期間を定義する。
- INV-10: WorkflowまたはEventBusの永続化失敗をログだけで成功扱いにしない。
- INV-11: 1DBの破損が他DBの初期化、復旧を要求しない。
- INV-12: DB間処理が冪等に再実行できる。

## Exceptions

なし

## Failure Policy

### Fail-Fast Conditions

- `rag.sqlite`の接続失敗時（RAG機能停止）
- `session.sqlite`の接続失敗時（セッション機能停止）
- `workflow.sqlite`の接続失敗時（ワークフロー機能停止）
- `eventbus.sqlite`の接続失敗時（イベント配信停止）

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

- Fallback対象：なし
- Fallback先：なし
- Fallbackを禁止する条件：整合性チェックの不一致
- Fallback理由の記録先：監査ログ

該当しない場合は「対象外」と記載する。

## Data Ownership and Persistence

- **System of Record**: 4つのSQLite DB（`rag.sqlite`, `session.sqlite`, `workflow.sqlite`, `eventbus.sqlite`）
- **Derived Data**: 再生成可能な派生データ（FTS5、Vector Index）
- **Ownership**: RAGチーム、Agentチーム、Workflowチーム、EventBusチーム
- **Persistence**: ファイルシステム（`/opt/llm/db/`ディレクトリ）
- **Transaction Boundary**: DB単位
- **Recovery Source**: 各DBの手動復旧
- **Deletion Rule**: 各DBの削除は独立して実行する

該当しない場合は「対象外」と記載する。

## Verification

### Automated Tests

- **Test**: 各DBが独立して初期化、接続、Checkpoint、Recoveryできること
  - **Verifies**: INV-01, INV-02, INV-03, INV-04
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: sqlite-vecが`rag.sqlite`以外へロードされないこと
  - **Verifies**: INV-08
  - **Type**: Regression
  - **Blocking**: Yes

- **Test**: 1DBの破損が他DBの初期化、復旧を要求しないこと
  - **Verifies**: INV-11
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: DB間処理が冪等に再実行できること
  - **Verifies**: INV-12
  - **Type**: Integration
  - **Blocking**: Yes

### Startup Validation

- 起動時に各DBの接続が確認される
- 設定ファイルが有効か（parseable TOML、必須フィールド）

### Deployment Validation

- デプロイ前後に各DB Schemaの確認
- デプロイ後の整合性チェックがPASSすること

### Runtime Monitoring

- Health Check：各DBの接続状態
- Metrics：各DBの接続数、WALモード、チェックポイント回数
- Logs：DB接続イベント、エラーイベント
- Alert条件：`db_unavailable`
- Degraded条件：依存関係の障害

該当しない場合は「対象外」と記載する。

### Manual Review

- デプロイメント前のDB Schema検証

Verificationが存在しないInvariantは、未検証事項としてIssue登録する。

## Migration and Rollout

既存実装はDecisionに適合している。4DB構成は既に確立されており、移行作業は不要。

### Compatibility

- 後方互換性：既存の設定ファイルはそのまま使用可能
- 旧設定、旧Data、旧APIの扱い：なし

### Rollback

- Rollback可能な条件：ADRの判断が誤りであった場合
- Rollback手順：新しいADRを作成して本ADRをSupersededへ変更
- Rollbackできない変更：Eventの削除（ロールバック不可）
- Data復旧方法：SQLiteの手動復旧

該当しない場合は「対象外」と記載する。

### Completion Criteria

- 移行完了と判断する条件：既存実装がDecisionに適合していることを確認
- 旧経路を削除する条件：既存実装がDecisionに適合していることを確認

移行が不要な場合は「既存実装はDecisionに適合しており、移行作業は不要」と記載する。

## Implementation Notes

現在の実装がDecisionをどのように実現しているかを簡潔に記載する。

- 実装ファイル: `scripts/db/config.py`, `scripts/db/helpers.py`, `scripts/db/maintenance.py`
- 主要ClassまたはFunction: `DbConfig.rag_db_path`, `DbConfig.session_db_path`, `DbConfig.workflow_db_path`, `DbConfig.eventbus_db_path`, `create_schema()`, `SQLiteHelper.__init__()`
- データベーススキーマ: `rag.sqlite`（`documents`, `chunks`, `chunks_fts`, `chunks_vec`）、`session.sqlite`（`sessions`, `messages`, `memories`, `memories_vec`）、`workflow.sqlite`（`tasks`, `attempts`, `artifacts`, `approvals`）、`eventbus.sqlite`（`events`）
- WALモード：すべての接続で`PRAGMA journal_mode=WAL`
- チェックポイントモード：`sqlite_wal_checkpoint_mode` config（デフォルト`TRUNCATE`）
- 対応するテスト: `tests/test_db_*.py`

この章は設計判断の根拠にしない。詳細なAPI、Class、Function一覧はImplementation Referenceへ記載する。

行番号は記載せず、File PathとSymbol名で参照する。

## Known Deviations

ADRと現行実装、設定、テスト、文書に差異がある場合に記載する。

- **Known Issue**: EVENTBUS-008 — Production deployment requires an authentication model. The recommended workaround is keeping `allow_public_bind=false` and binding to loopback only, using SSH tunnels for remote access. Static bearer token validation is planned but not implemented.
- **Type**: Security Gap
- **Summary**: EventBusの認証モデルが未実装
- **Impact**: 外部公開時のセキュリティリスク
- **Resolution Target**: 認証の実装が必要

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
- ADR-006: EventBusのSQLite永続化とSSE配信方式

### Specifications

- [DB Architecture and Schema](90_shared_04_02_db_architecture_and_schema-schema-reference.md) — DBスキーマ参照
- [RAG Persistence](03_rag_04_02_rag-persistence.md) — RAG永続化
- [RAG Recovery](03_rag_04_03_rag-recovery.md) — RAG復旧
- [Agent Session Persistence](05_agent_04_01_agent-session-persistence.md) — セッション永続化
- [EventBus Persistence Schema and Replay](06_eventbus_03_persistence_schema_and_replay.md) — EventBus永続化スキーマ
- [DLQ Offsets and Delivery Semantics](06_eventbus_04_dlq_offsets_and_delivery_semantics.md) — DLQオフセットと配信セマンティクス

### Operations

- [Operations and Observability](05_agent_10_01_operations-and-observability-startup-and-health.md) — 運用と観測
- [Backup and Recovery](05_agent_10_02_backup-and-recovery.md) — バックアップと復旧
- [Deployment](05_agent_10_03_deployment.md) — デプロイ

### Known Issues

- [EventBus Known Issues](06_eventbus_90_inconsistencies_and_known_issues.md) — EventBus既知の問題

### Implementation References

- `scripts/db/config.py` — `DbConfig` frozen dataclass
- `scripts/db/helpers.py` — `SQLiteHelper.__init__()`, `load_vec()`
- `scripts/db/maintenance.py` — `create_schema()`, `check_rag_consistency()`
- `rag.sqlite` — `documents`, `chunks`, `chunks_fts`, `chunks_vec`
- `session.sqlite` — `sessions`, `messages`, `memories`, `memories_vec`
- `workflow.sqlite` — `tasks`, `attempts`, `artifacts`, `approvals`
- `eventbus.sqlite` — `events`
- テスト — `tests/test_db_*.py`

## Change History

- 2026-08-21: Acceptedとして作成。4DB分離の判断を確定

Accepted後は、Decisionの意味を変更しない軽微な修正だけを記録する。

- YYYY-MM-DD: Acceptedへ変更
- YYYY-MM-DD: Linkまたは表現を修正。Decisionの変更なし

判断内容を変更する場合は、新しいADRを作成して本ADRをSupersededへ変更する。

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
