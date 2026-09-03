---
title: "ADR-008: SQLiteを4DBへ分離する"
area: adr
tags:
  - system
  - sqlite
  - database-separation
decision_scope:
  - system
related:
  - ADR-002
---

# ADR-008: SQLiteを4DBへ分離する

## Status

Accepted

使用可能なStatusは次のとおりとする。

- `Proposed`: 提案中、レビューまたは承認前
- `Accepted`: 採用済みであり、現行設計として有効

Accepted後に現在の判断を変更する場合は、本ADR本文を直接更新する。同じ変更の中で、影響を受けるSpecification、Reference、Operations文書および検証要件を更新する。

## Summary

更新頻度、障害範囲、保持期間、復旧方法が異なるデータを4つのSQLite DBへ分離する判断を正典化する。`rag.sqlite`、`session.sqlite`、`workflow.sqlite`、`eventbus.sqlite`の責務を定義し、DB間Transactionを使用しないことと整合性確保方法を説明する。sqlite-vecの適用範囲を限定し、DBごとのBackup、Recovery、保持方針を整理する。あわせて、物理的破損からの復旧が満たすべき安全境界（障害分類、バックアップ候補の独立検証、Atomicな置換、Dry Runの無変更保証、永続化ドメインごとの復旧方針）を正典化する。

## Context

### Problem

RAGインデックス、セッション状態、ワークフロー状態、イベントバス状態はそれぞれ異なる更新頻度、ロック競合特性、障害範囲、保持期間、復旧方法を持つ。単一DBで管理すると、WAL競合によるパフォーマンス劣化、障害の伝播、バックアップの複雑化が生じる。

また、複数のSQLiteファイルに分離した状態でも、復旧機構自体に明示的な安全契約がなければ危険である。DBが開けない原因（物理的破損か、一時的なロック競合か）を区別できない復旧機構は、実際には壊れていないDBに対しても実行され得るため、復旧機構が存在しない場合より危険になり得る。検証されていないバックアップからの復元や、対象DBを非Atomicに上書きする実装は、単一ファイルの破損インシデントを、破損した原本と正常なバックアップの両方を失うリスクへ変える。

### Constraints

- 単一Host、複数プロセスでの実行を前提とする
- デプロイ環境では起動前に各DBファイルが存在することを確認する必要がある
- sqlite-vec拡張は`rag.sqlite`だけにロードする必要がある
- DB間で物理外部キー、SQL JOIN、分散Transactionを前提としない
- WorkflowまたはEventBusの永続化失敗をログだけで成功扱いにしない
- リカバリは現在、手動かつ運用者起動のCLI操作であり、起動時の自動処理ではない
- マイグレーション機構は存在せず、Schema変更にはDB全体の再作成を要する（本ADRの対象外）

### Assumptions

- 対象環境：単一Host、複数プロセス
- 想定規模：同時実行数は限定的
- 信頼境界：各DB内でのみ権限を付与する
- 外部依存先：なし（SQLiteはローカルファイル）
- バックアップは定期的なファイルコピー（`rotate_all_dbs()`）であり、継続的に検証されたSnapshotではない
- 前提が崩れた場合に再評価が必要な事項：複数Host構成、分散実行、外部イベントストア統合、レプリケーション型ストレージへの移行

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
14. リカバリは、アクションを選択する前にDB状態（healthy / confirmed corruption / lock contention / permission failure / invalid format / unknown）を分類しなければならない。Lock ContentionおよびPermission Failureを物理的破損として分類してはならない。
15. リストア候補のバックアップは、対象DBを置き換える前に、それ自体の整合性を独立して検証しなければならない。
16. リストアは候補を一時的な場所へStageし、検証したうえで、現行設計でサポートされる範囲においてのみ対象DBをAtomicに置換する。対象DBは、候補が検証に合格する前に上書きしてはならない。
17. Unknownまたは分類不能な障害は、対象DBを保持し、自動リストアではなく運用者の介入を要求する。
18. Dry Runは、いかなる分類結果であっても対象DBを移動、置換、Truncate、削除、書き換えしてはならない。
19. 破損したDBは、置換を行う前に診断用として退避コピーを作成する。退避コピーの保持および削除は運用者の手動判断に委ねる。自動削除は行わない。
20. 復旧方針は永続化ドメインごとに明示的に定義する。`rag.sqlite`は正本（`chunks`テーブル等）から再構築可能なため再構築による復旧を許容し、`session.sqlite`はバックアップからの復元を許容する。`workflow.sqlite`と`eventbus.sqlite`は自動リストアを禁止し、復旧は運用者による手動対応のみとする（サイレントな再初期化は行わない）。

### Scope

- **対象コンポーネント**: `DbConfig`, `SQLiteHelper`, `create_schema()`, `db/recovery.py`, `db/maintenance.py`
- **対象プロセス**: Agentプロセス、ingesterプロセス、EventBusプロセス
- **対象データ**: `rag.sqlite`, `session.sqlite`, `workflow.sqlite`, `eventbus.sqlite`
- **対象Environment Profile**: すべての環境（local/dev/production）
- **対象APIまたは処理経路**: `DbConfig.rag_db_path`, `DbConfig.session_db_path`, `DbConfig.workflow_db_path`, `DbConfig.eventbus_db_path`, `recover_corruption()`

### Out of Scope

- 個別のDBスキーマの詳細
- WAL Checkpointの詳細なパラメータ
- Backupツールやスクリプトの実装
- リカバリの自動（無人）起動化（現在は運用者起動のみであり、自動化は別途の判断を要する）
- マイグレーション、Schemaバージョニング戦略
- 継続的なバックアップ検証、レプリケーション設計
- 監視・メトリクス設計（別ADRで扱う）

## Rationale

### 1. 最重要の採用理由 — Operability

各DBが独立して初期化、接続、Checkpoint、Recoveryできるため、障害範囲が局所化される。1DBの破損が他DBの初期化、復旧を要求しない。

### 2. 第2の採用理由 — Performance

更新頻度の異なるデータが同じDBにある場合、WAL競合によりパフォーマンスが劣化する。RAGは高書込・高読込、SessionはAppend-heavy、Workflowは低頻度だがトランザクション重要、EventBusはリアルタイム配信が優先される。これらの特性が異なるため、分離することでロック競合を回避できる。

### 3. 第3の採用理由 — Data Integrity

各DBに独立したBackup、Recovery、WAL Checkpoint、Health Check、保持期間を定義できる。RAGは再構築可能、Sessionは履歴保持、Workflowは再開と監査、EventBusは未処理EventとOffsetを重視するという違いに対応できる。検証されていないバックアップからの復元や非Atomicな上書きは、破損した原本と正常なバックアップの両方を失うリスクに変えるため、候補の独立検証とAtomicな置換を要件とする。

### 4. 第4の採用理由 — Correctness（Recovery Safety）

破損と一時的なロックを区別できない復旧機構は、実際には壊れていないDBに対して実行され得るため、復旧機構が存在しない場合より危険である。`workflow`/`eventbus`ドメインの復旧方針が未定義のままだと、それらのドメインで実際に障害が起きた際に運用者が取るべき行動が存在しないため、本ADRはこの方針を明示的に定める。

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

### Alternative D: Treat every DB-open failure as corruption and always restore from backup

#### Description

DBオープン失敗を常に破損として扱い、常にバックアップから復元する。

#### Advantages

- 単一のコード経路で単純

#### Disadvantages

- 一時的なLock/Permission障害に対しても不要にリストアが実行される
- 実際には一時的な状態だった場合に、直近の書き込みを失うリスクがある

#### Reason for Rejection

分類の不変条件（Lock ContentionとPermission FailureをCorruptionとして扱わない）に違反するため不採用とした。

#### Reconsideration Conditions

- 該当なし

### Alternative E: Leave workflow/eventbus unrecoverable by policy, permanently

#### Description

`workflow.sqlite`/`eventbus.sqlite`を恒久的に復旧不能として扱う。

#### Advantages

- 実装作業が不要

#### Disadvantages

- 未告知の恒久的なギャップとなり、運用者が`rag`/`session`と同様に復旧できると誤解する可能性がある

#### Reason for Rejection

復旧不能とするか運用者による手動復旧手順を用意するかは明示的な決定であるべきであり、本ADRでは後者（運用者による手動復旧）を採用したため不採用とした。

#### Reconsideration Conditions

- 該当なし

## Consequences

### Positive Consequences

- 各DBの独立性が確保される
- 障害範囲が局所化される
- バックアップが容易になる
- 保持期間の個別管理が可能になる
- sqlite-vecの適用範囲が限定される
- リカバリ操作が明文化された安全性契約に対して監査可能になる
- バックアップの破損や部分的リストアが、稼働中（たとえ破損していても）のDBを置き換える前に検出される

### Negative Consequences

- DB間JOINができない
- 複合トランザクションが必要になる
- バックアップのスクリプティングが必要
- 障害対応時に複数のDBを確認する必要がある
- リカバリが、候補の検証・Stage・再検証・Atomic置換という、単純な単一コピー実装より多い手順を要する

### Operational Consequences

- 起動時に各DBの接続が確認される
- 設定変更時は所有DBの再起動が必要
- 障害対応時にDBごとの復旧手順が必要
- `workflow.sqlite`/`eventbus.sqlite`の物理的破損時は自動リストアが行われないため、運用者が手動で復旧対応を行う必要がある
- 退避された破損DBコピーの削除は運用者の手動判断に委ねる（自動削除は行わない）

### Security Consequences

- 信頼境界：各DB内でのみ権限を付与する
- 認証、認可：設定ファイルに基づく権限判定
- Secretの取扱い：最小公開原則に従う
- Fail-Closed：設定ファイル欠落時は起動中止
- リカバリ操作のError MessageおよびAudit Recordは、行レベルのDB内容を含めてはならない（Pathおよび例外テキストのみ）
- Audit Log：設定読み込みイベントの記録

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
- INV-13: リカバリアクションは、DB状態の分類（healthy / corruption / lock contention / permission failure / invalid format / unknown）の後にのみ選択する。Lock ContentionおよびPermission Failureを物理的破損として分類してはならない。
- INV-14: リストア候補のバックアップは、対象DBを置き換える前に独立して検証されなければならない。
- INV-15: 対象DBは、候補が検証に合格する前に上書きしてはならない。置換は、現行設計でサポートされる範囲でAtomicに行う。
- INV-16: Dry Runは、いかなる分類結果であっても対象DBを移動、置換、Truncate、削除、書き換えしてはならない。
- INV-17: Unknownまたは分類不能な障害は、対象DBを保持し、自動リストアではなく運用者の介入を要求する。
- INV-18: `workflow.sqlite`と`eventbus.sqlite`に対する自動リストアは禁止する。復旧は運用者による手動対応のみとし、`rag.sqlite`（再構築）・`session.sqlite`（バックアップ復元）とは異なる方針を明示的に適用する。

## Exceptions

なし

## Failure Policy

### Fail-Fast Conditions

- `rag.sqlite`の接続失敗時（RAG機能停止）
- `session.sqlite`の接続失敗時（セッション機能停止）
- `workflow.sqlite`の接続失敗時（ワークフロー機能停止）
- `eventbus.sqlite`の接続失敗時（イベント配信停止）
- リストア候補のバックアップが独立検証に失敗した場合
- Unknownまたは分類不能な整合性チェック失敗の場合

### Fail-Open or Degraded Conditions

該当なし。破損リカバリはFail-Closedドメインとして設計する。判断に迷う場合は状態を保持し、自動的に動作するのではなく運用者の対応を要求する。

### Retry Policy

- Retry対象：インジェクション失敗
- Retry回数：`retry_policy.max_attempts`（デフォルト3回）
- Backoff：固定間隔（デフォルト1秒）
- RetryしないError：整合性チェックの不一致
- リカバリは運用者起動による単発の試行であり、自動リトライループは存在しない

### Fallback Policy

- Fallback対象：なし
- Fallback先：なし
- Fallbackを禁止する条件：整合性チェックの不一致
- Fallback理由の記録先：監査ログ

## Data Ownership and Persistence

- **System of Record**: 4つのSQLite DB（`rag.sqlite`, `session.sqlite`, `workflow.sqlite`, `eventbus.sqlite`）
- **Derived Data**: 再生成可能な派生データ（FTS5、Vector Index）
- **Ownership**: RAGチーム、Agentチーム、Workflowチーム、EventBusチーム
- **Persistence**: ファイルシステム（`/opt/llm/db/`ディレクトリ）
- **Transaction Boundary**: DB単位
- **Recovery Source**: `rag.sqlite`/`session.sqlite`は運用者供給の検証済みバックアップファイル。`workflow.sqlite`/`eventbus.sqlite`は自動リストア対象外であり、運用者による手動対応。
- **Deletion Rule**: 各DBの削除は独立して実行する。診断用に退避された破損DBコピー（`*_corrupt_<timestamp>.sqlite`）の削除は運用者の手動判断に委ね、自動削除は行わない。

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

- **Test**: Lock Contentionパスが物理的破損として分類されないこと
  - **Verifies**: INV-13
  - **Type**: Regression
  - **Blocking**: Yes

- **Test**: Dry Runが、いかなる分類結果においても対象DBをByte-identicalに保つこと
  - **Verifies**: INV-16
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: `workflow`/`eventbus`を指定した`recover_corruption()`呼び出しが自動リストアを行わないこと
  - **Verifies**: INV-18
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

### Manual Review

- デプロイメント前のDB Schema検証
- `workflow.sqlite`/`eventbus.sqlite`向けの運用者手動復旧手順（具体的な作業手順書）は本ADRでは未整備であり、別途Runbookとして整備する必要がある

Verificationが存在しないInvariantは、未検証事項としてIssue登録する。

## Implementation Notes

現在の実装がDecisionをどのように実現しているかを簡潔に記載する。

- 実装ファイル: `scripts/db/config.py`, `scripts/db/helpers.py`, `scripts/db/maintenance.py`, `scripts/db/recovery.py`
- 主要ClassまたはFunction: `DbConfig.rag_db_path`, `DbConfig.session_db_path`, `DbConfig.workflow_db_path`, `DbConfig.eventbus_db_path`, `create_schema()`, `SQLiteHelper.__init__()`, `recover_corruption()`, `_classify_error()`, `_run_integrity_check()`, `_restore_from_backup()`
- データベーススキーマ: `rag.sqlite`（`documents`, `chunks`, `chunks_fts`, `chunks_vec`）、`session.sqlite`（`sessions`, `messages`, `memories`, `memories_vec`）、`workflow.sqlite`（`tasks`, `attempts`, `artifacts`, `approvals`）、`eventbus.sqlite`（`events`）
- WALモード：すべての接続で`PRAGMA journal_mode=WAL`
- チェックポイントモード：`sqlite_wal_checkpoint_mode` config（デフォルト`TRUNCATE`）
- 対応するテスト: `tests/test_db_*.py`, `tests/db/test_db_maintenance.py`, `tests/integration/test_session_recovery.py`

この章は設計判断の根拠にしない。詳細なAPI、Class、Function一覧はImplementation Referenceへ記載する。

行番号は記載せず、File PathとSymbol名で参照する。

## Known Deviations

ADRと現行実装、設定、テスト、文書に差異がある場合に記載する。

- **Known Issue**: EVENTBUS-008 — Production deployment requires an authentication model. The recommended workaround is keeping `allow_public_bind=false` and binding to loopback only, using SSH tunnels for remote access. Static bearer token validation is planned but not implemented.
  - **Type**: Security Gap
  - **Summary**: EventBusの認証モデルが未実装
  - **Impact**: 外部公開時のセキュリティリスク
  - **Resolution Target**: 認証の実装が必要

- **Resolved Issue**: `recover_corruption()`（`scripts/db/recovery.py`）は、Unknown分類（`DbCondition.UNKNOWN`）をCorruption分類と同一に扱い、`rag`/`session`に対しては自動的にバックアップからのリストアを試みる。これはINV-17（Unknownまたは分類不能な障害は対象DBを保持し運用者の介入を要求する）を現時点では満たしていない。
  - **Type**: Resolved
  - **Summary**: Unknown分類がCorruptionと同一挙動になっていたが、`preserved_operator_intervention_required`アクションでDB保持・運用者介入要求を実装した
  - **Impact**: 分類不能な整合性チェック失敗であっても、`rag`/`session`では自動的にリストアが実行され得る
  - **Resolution**: `implementations/20260902-064946_01_scripts_db_recovery_py.md` で実装済み；ユニットテストおよびインテグレーションテストで検証済み
  - **解決済み**: REQ-001〜REQ-003により、`recover_corruption()`に`DbCondition.UNKNOWN`専用の分岐を追加し、`action="preserved_operator_intervention_required"`を返して対象DBを保持し運用者介入を要求するようになった（`_restore_from_backup()`は呼び出されない）。これによりINV-17を満たす。**影響**: INV-17 → 解消済み。

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
- sqlite-vecがFK制約をサポートする場合
- FTS5が標準的なDELETEをサポートする場合
- 共通設定ファイルの新設が必要となった場合
- 永続化ストレージがファイル以外へ移行された場合
- マイグレーション機構またはレプリケーション型ストレージ基盤が導入された場合
- バックアップ戦略が定期ファイルコピーから別方式へ変更された場合
- 自動（無人）リカバリトリガーが提案された場合
- `workflow.sqlite`/`eventbus.sqlite`の復旧方針を手動対応から自動化された経路へ変更する場合

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
- ADR-005: RAGの正本と派生インデックスの関係
- ADR-006: EventBusのSQLite永続化とSSE配信方式

### Specifications

- [DB Architecture and Schema](90_shared_04_02_db_architecture_and_schema-schema-reference.md) — DBスキーマ参照
- [DB API and Operations — Recovery and Reference](90_shared_05_04_db_api_and_operations-recovery-and-reference.md) — リカバリAPIとOperations参照
- [RAG Persistence](03_rag_04_02_rag-persistence.md) — RAG永続化
- [RAG Recovery](03_rag_04_03_rag-recovery.md) — RAG復旧
- [Agent Session Persistence](05_agent_04_01_agent-session-persistence.md) — セッション永続化
- [EventBus Persistence Schema and Replay](06_eventbus_03_persistence_schema_and_replay.md) — EventBus永続化スキーマ
- [DLQ Offsets and Delivery Semantics](06_eventbus_04_dlq_offsets_and_delivery_semantics.md) — DLQオフセットと配信セマンティクス

### Operations

- [Operations and Observability](05_agent_10_01_operations-and-observability-startup-and-health.md) — 運用と観測
- [Manual Recovery: workflow.sqlite / eventbus.sqlite](05_agent_10_01_operations-and-observability-startup-and-health.md#manual-recovery-workflowsqlite-eventbussqlite) — workflow.sqlite / eventbus.sqliteの手動復旧手順

### Known Issues

- [Issue and Uncertainty Management](00_governance_03_issue-and-uncertainty-management.md) — EventBus既知の問題
- [Issue and Uncertainty Management](00_governance_03_issue-and-uncertainty-management.md) — SHARED-003（workflow/eventbus復旧手続きの実務Runbook未整備）、CI-002（本ADRの現行内容と対応しない旧記述の疑い）

### Implementation References

- `scripts/db/config.py` — `DbConfig` frozen dataclass
- `scripts/db/helpers.py` — `SQLiteHelper.__init__()`, `load_vec()`
- `scripts/db/maintenance.py` — `create_schema()`, `check_rag_consistency()`
- `scripts/db/recovery.py` — `recover_corruption()`, `_classify_error()`, `_run_integrity_check()`, `_restore_from_backup()`
- `rag.sqlite` — `documents`, `chunks`, `chunks_fts`, `chunks_vec`
- `session.sqlite` — `sessions`, `messages`, `memories`, `memories_vec`
- `workflow.sqlite` — `tasks`, `attempts`, `artifacts`, `approvals`
- `eventbus.sqlite` — `events`
- テスト — `tests/test_db_*.py`, `tests/db/test_db_maintenance.py`, `tests/integration/test_session_recovery.py`

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
- [x] 既存ADRとの関係が記載されている
- [x] 関係するSpecificationと矛盾していない
- [x] 現行実装との差異がKnown Issueへ登録されている
- [ ] Ownerと必要なReviewerが定義されている
- [x] Review Triggersが記載されている
- [x] ADR索引と関係領域のDocument Guideへ登録されている
