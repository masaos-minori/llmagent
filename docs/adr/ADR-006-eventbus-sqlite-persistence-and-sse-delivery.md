---
title: "ADR-006: EventBusのSQLite永続化とSSE配信方式"
category: adr
status: accepted
date: "2026-08-21"
last_updated: "2026-08-21"
owners:
  - eventbus-team
reviewers:
  - architecture-reviewer
decision_scope:
  - eventbus
related:
  - ADR-002
supersedes: []
superseded_by: null
---

# ADR-006: EventBusのSQLite永続化とSSE配信方式

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

SQLiteをEventの永続的な正本、SSEをLive配信チャネルとする方式を正典化し、再接続、Replay、ACK、NAK、DLQの配信保証を明確にする。At-Least-Once Deliveryを基本とし、重複は許容するが欠落は許容しない。Offset単調性とConsumer ID競合方針を確定する。

## Context

### Problem

EventBusでは複数のデータストア（SQLite、JSONLアーカイブ、オフセットファイル）が存在し、それぞれが異なる役割を持つ。SQLiteがEventの正本であるが、SSE配信は低遅延チャネルとして独立しており、両者の責務を明確にする必要がある。また、Subscriberの再接続時に未処理EventのReplayを保証し、ACK/NAK/DLQの配信保証を明確にする必要がある。

### Constraints

- 単一SQLiteデータベース内でEventを管理する
- SSE配信は接続中のSubscriberのみへリアルタイムに配信する
- JSONLアーカイブは二次的な監査用ログであり、Primary Storeではない
- Consumer IDはクライアント側で指定され、サーバー側で生成されない
- OffsetはACK駆動で進み、自動で進むわけではない
- sqlite-vec拡張を使用するため、標準的なFK制約の一部が制限される

### Assumptions

- 対象環境：単一Host、単一SQLite
- 想定規模：同時実行数は限定的
- 信頼境界：SQLite内でのみ権限を付与する
- 外部依存先：なし（SQLiteはローカルファイル）
- 前提が崩れた場合に再評価が必要な事項：複数DB構成、分散実行、外部イベントストア統合

## Decision

### Decision Details

1. SQLiteをEventの正本とし、SSEを低遅延配信チャネルとする。
2. Publisherは`POST /publish`でEventをSQLiteへ永続化し、接続中SubscriberへSSE配信する。
3. Subscriber不在の場合でもEventを保存すること。
4. Subscriberの再接続時はConsumer IDとACK Offsetを確認し、SQLiteから未処理EventをReplayし、SSE Live配信へ復帰する。
5. SSE配信成功を永続化成功の代替とせず、SQLite書込失敗時は成功応答を返さない。
6. Consumer IDを再起動後も固定し、ACK Offsetを永続化する。
7. ACK済みOffsetの後退を許可しない。
8. Event IDを付与し、Consumer側で冪等処理できるようにする。
9. At-Least-Once Deliveryを基本とし、重複は許容するが欠落は許容しない。
10. NAK、Retry、DLQ、Requeueの状態、回数、履歴を永続化する。
11. 次の未決事項をコードとテストで確認し、ADRで判断を確定する：
    - `new_offset <= current_offset`を拒否するか警告して無視するか → 拒否する（Monotonicity Invariant）
    - 同一Consumer IDの並行使用を禁止するか → 禁止する（Conflict Detection Required）
    - Consumer ID衝突を検出するか → 検出する
    - ACK永続化失敗時の応答と再配信方針 → エラー応答 + 再配信不可（Fail-Closed）
    - DLQ昇格の複数経路をどう統一するか → インライン昇格を優先し、バックグラウンドループは補完のみ
    - ReplayからLiveへ切り替える際の重複処理 → Consumer側でevent_idによる冪等処理を要求
12. Offset単調性に関するKnown IssueとAPI Referenceの矛盾を解消する。
13. 認証を実装しない場合、LoopbackまたはUnix SocketへのBind、Firewall制限、外部公開禁止を技術的に強制する。

### Scope

- **対象コンポーネント**: `EventBroker`, `EventPublisher`, `EventSubscriber`, `OffsetManager`, `DlqService`
- **対象プロセス**: EventBusプロセス
- **対象データ**: `events`テーブル、オフセットファイル、DLQ状態
- **対象Environment Profile**: すべての環境（local/dev/production）
- **対象APIまたは処理経路**: `POST /publish`, `GET /subscribe`, `POST /events/{event_id}/ack`, `POST /nack`, `POST /dlq/{event_id}/requeue`

### Out of Scope

- セキュリティ認証の詳細な実装（別ADRで扱う）
- メトリクス収集の詳細な設定
- ロギングの詳細なフォーマット
- パフォーマンスベンチマークの閾値

## Rationale

### 1. 最重要の採用理由 — Data Integrity

SQLiteをEventの正本とすることで、Eventの欠落を防ぐ。SSE配信の失敗が永続化の失敗と混同されないため、Eventの信頼性が確保される。

### 2. 第2の採用理由 — Operability

At-Least-Once Deliveryを明確にすることで、Consumer側のエラーハンドリングが統一される。重複は許容されるため、Consumerは冪等処理を実装すればよい。

### 3. 第3の採用理由 — Security

Offset単調性の保証により、不正なACKによるオフセット後退を防ぐ。Consumer ID衝突の検出により、意図せぬEventの受信を防ぐ。

「現行コードがこの方式で実装されているため」だけを採用理由にしない。

## Alternatives Considered

### Alternative A: SSE配信を永続化の代替とする

#### Description

SSE配信成功を永続化成功の代替とし、SQLite書込前にSSE配信を試みる。

#### Advantages

- 低遅延配信が優先される
- シンプルな実装

#### Disadvantages

- Eventの欠落リスク
- 配信失敗時の復旧が困難
- 永続化と配信の責任が不明確

#### Reason for Rejection

Data Integrityを優先し、Eventの欠落を防ぐため不採用とした。

#### Reconsideration Conditions

- SSE配信が100%信頼できる場合
- Eventの欠落が許容される場合

### Alternative B: No offset monotonicity guarantee

#### Description

ACK済みOffsetの後退を許可し、Consumerが任意の順序でACKできる。

#### Advantages

- Consumerの実装が柔軟になる
- 並列ACKが可能

#### Disadvantages

- Offsetsの予測不可能な変動
- データ損失のリスク
- 再現性の低下

#### Reason for Rejection

Data Integrityを優先し、オフセットの後退によるデータ損失を防ぐため不採用とした。

#### Reconsideration Conditions

- Consumerが完全に冪等な処理を実装する場合
- 並列ACKが必要となる場合

### Alternative C: No consumer ID conflict detection

#### Description

同一Consumer IDの並行使用を許可し、最後の書き込みが勝つとする。

#### Advantages

- シンプルな実装
- Consumerの追加が容易

#### Disadvantages

- 意図せぬEventの受信
- Offsetの競合
- データ損失のリスク

#### Reason for Rejection

Securityを優先し、意図せぬEventの受信を防ぐため不採用とした。

#### Reconsideration Conditions

- Consumer IDが完全に一意であることが保証される場合
- 意図せぬEventの受信が許容される場合

## Consequences

### Positive Consequences

- Eventの欠落が防止される
- At-Least-Once Deliveryが明確になる
- Consumerの再接続時に未処理Eventが確実にReplayされる
- Offset単調性が保証される
- Consumer ID衝突が検出される
- DLQ昇格経路が統一される

### Negative Consequences

- 重複Eventの処理が必要になる
- Consumer ID衝突の検出コスト
- Offset単調性の検証オーバーヘッド
- 認証の実装が必要になる

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

- INV-01: SQLiteがEventの正本である。
- INV-02: SSE配信成功を永続化成功の代替としない。
- INV-03: Subscriber不在の場合でもEventを保存する。
- INV-04: Consumer IDを再起動後も固定し、ACK Offsetを永続化する。
- INV-05: ACK済みOffsetの後退を許可しない。
- INV-06: Event IDを付与し、Consumer側で冪等処理できるようにする。
- INV-07: At-Least-Once Deliveryを基本とし、重複は許容するが欠落は許容しない。
- INV-08: NAK、Retry、DLQ、Requeueの状態、回数、履歴を永続化する。
- INV-09: `new_offset <= current_offset`を拒否する。
- INV-10: 同一Consumer IDの並行使用を禁止する。
- INV-11: Consumer ID衝突を検出する。
- INV-12: ACK永続化失敗時はエラー応答を返し、再配信しない。
- INV-13: DLQ昇格はインライン昇格を優先し、バックグラウンドループは補完のみ。
- INV-14: ReplayからLiveへ切り替える際はConsumer側でevent_idによる冪等処理を要求する。
- INV-15: 認証を実装しない場合、LoopbackまたはUnix SocketへのBind、Firewall制限、外部公開禁止を技術的に強制する。

## Exceptions

なし

## Failure Policy

### Fail-Fast Conditions

- SQLite書込失敗時（永続化失敗）
- ACK永続化失敗時（冪等性破損リスク）
- `new_offset <= current_offset`違反時（単調性破損）
- Consumer ID衝突検出時（セキュリティリスク）

### Fail-Open or Degraded Conditions

- ローカル開発環境では、軽微な整合性不一致は警告として記録される
- JSONLアーカイブの書込失敗はWARNINGログのみ（SQLiteは正常）

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

- **System of Record**: `events`テーブル（SQLite）
- **Derived Data**: JSONLアーカイブ（二次的な監査用ログ）、オフセットファイル
- **Ownership**: EventBusチーム（正本の所有）
- **Persistence**: SQLiteファイルシステム
- **Transaction Boundary**: Event単位
- **Recovery Source**: SQLite（正本）
- **Deletion Rule**: DLQ昇格後に削除（またはTTLベースのクリーンアップ）

該当しない場合は「対象外」と記載する。

## Verification

### Automated Tests

- **Test**: Subscriber不在時もEventが保存されること
  - **Verifies**: INV-03
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: 再接続時に未ACK EventがReplayされること
  - **Verifies**: INV-04
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: Offsetが後退しないこと
  - **Verifies**: INV-05
  - **Type**: Regression
  - **Blocking**: Yes

- **Test**: ACK永続化失敗時に成功扱いしないこと
  - **Verifies**: INV-12
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: ReplayとLive切替時の重複をConsumerが処理可能であること
  - **Verifies**: INV-14
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: Retry上限後にDLQへ移ること
  - **Verifies**: INV-13
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: Consumer ID衝突が検出されること
  - **Verifies**: INV-11
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: `new_offset <= current_offset`が拒否されること
  - **Verifies**: INV-09
  - **Type**: Regression
  - **Blocking**: Yes

### Startup Validation

- 起動時にDB接続が確認される
- 設定ファイルが有効か（parseable TOML、必須フィールド）

### Deployment Validation

- デプロイ前後にDB Schemaの確認
- デプロイ後の整合性チェックがPASSすること

### Runtime Monitoring

- Health Check：DB接続状態、DLQタスク状態、Brokerキューバックログ、Slow Consumer検出
- Metrics：Event publish count, ACK count, NACK count, DLQ promotion count
- Logs：Event publishイベント、ACKイベント、NACKイベント、DLQイベント
- Alert条件：`db_unavailable`, `dlq_task_stopped`, `broker_queue_backlog_high`, `slow_consumers_detected`
- Degraded条件：依存関係の障害

### Manual Review

- DLQ昇格の調査
- デプロイメント前のDB Schema検証

Verificationが存在しないInvariantは、未検証事項としてIssue登録する。

## Migration and Rollout

既存実装はDecisionに適合しているが、以下のKnown IssueをADRで判断を確定する必要がある。

### Compatibility

- 後方互換性：既存のAPIはそのまま使用可能
- 旧設定、旧Data、旧APIの扱い：`offset_checkpoint_interval`はDeprecated（起動時に失敗）

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

- 実装ファイル: `scripts/eventbus/broker.py`, `scripts/eventbus/publish.py`, `scripts/eventbus/subscribe.py`, `scripts/eventbus/ack.py`, `scripts/eventbus/nack.py`, `scripts/eventbus/dlq.py`, `scripts/eventbus/offsets.py`
- 主要ClassまたはFunction: `EventBroker.publish()`, `EventSubscriber.subscribe()`, `ack_event()`, `nack_event()`, `promote_single()`, `write_offset()`, `read_offset()`
- データベーススキーマ: `events`テーブル（`seq`, `event_id`, `topic`, `payload`, `acked_at`, `delivery_failure_count`, `dlq_requeue_count`, `dlq_at`）
- オフセットファイル: `{offsets_dir}/{sanitized_consumer_id}`
- DLQ昇格経路: インライン昇格（`POST /nack`時）とバックグラウンドループ（60秒ごと）
- 対応するテスト: `tests/test_eventbus_*.py`

この章は設計判断の根拠にしない。詳細なAPI、Class、Function一覧はImplementation Referenceへ記載する。

行番号は記載せず、File PathとSymbol名で参照する。

## Known Deviations

ADRと現行実装、設定、テスト、文書に差異がある場合に記載する。

- **Known Issue**: EVENTBUS-001 — `write_offset()` lacks a `max(current, new)` check. Reconnection can cause duplicate delivery. No server-side fix planned.
- **Type**: Open Issue
- **Summary**: `write_offset()`の単調性チェックが不足している
- **Impact**: 再接続時に重複配信が発生する可能性がある
- **Resolution Target**: Consumer側でevent_idによる冪等処理を要求することで緩和

- **Known Issue**: EVENTBUS-003 — DLQ dual promotion path (inline + background) was incompletely documented.
- **Type**: Documentation Gap
- **Summary**: DLQ昇格経路のドキュメント不備
- **Impact**: 運用担当者の混乱
- **Resolution Target**: ADRでインライン昇格を優先方針として明確化

- **Known Issue**: EVENTBUS-004 — Dead code `promote_to_dlq()` exists in `dlq.py` with zero callers.
- **Type**: Dead Code
- **Summary**: `promote_to_dlq()`は呼び出し元がない
- **Impact**: コードの複雑さ
- **Resolution Target**: リファクタリング時に削除

- **Known Issue**: EVENTBUS-008 — Production deployment requires an authentication model. The recommended workaround is keeping `allow_public_bind=false` and binding to loopback only, using SSH tunnels for remote access. Static bearer token validation is planned but not implemented.
- **Type**: Security Gap
- **Summary**: 認証モデルが未実装
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

- Consumer IDの衝突検出が必要となった場合
- 認証の実装が必要となった場合
- 永続化ストレージがファイル以外へ移行された場合
- At-Least-Once DeliveryからExactly-Once Deliveryへの変更が必要となった場合

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

### Specifications

- [EventBus System Overview](06_eventbus_01_system-overview.md) — EventBusアーキテクチャ概要
- [Publish/Replay Protocol](06_eventbus_02_01_publish-replay.md) — Publish/Replayプロトコル
- [Subscribe/ACK Protocol](06_eventbus_02_02_subscribe-ack.md) — Subscribe/ACKプロトコル
- [NACK/Health/DLQ Handling](06_eventbus_02_03_nack-health-dlq.md) — NACK/ヘルス/DLQハンドリング
- [Persistence Schema and Replay](06_eventbus_03_persistence_schema_and_replay.md) — 永続化スキーマとReplay
- [DLQ Offsets and Delivery Semantics](06_eventbus_04_dlq_offsets_and_delivery_semantics.md) — DLQオフセットと配信セマンティクス
- [Consumer ID Stability](06_eventbus_05_04_consumer-id-stability.md) — Consumer ID安定性
- [Delivery Operations](06_eventbus_05_05_delivery-operations.md) — 配信操作
- [DLQ Operations](06_eventbus_05_06_dlq-operations.md) — DLQ操作
- [Reference API - Broker and Offsets](06_eventbus_06_03_reference-api-broker-and-offsets.md) — レファレンスAPI
- [Reference API - Route Handlers](06_eventbus_06_04_reference-api-route-handlers.md) — ルートハンドラ
- [Reference API - Core Modules](06_eventbus_06_01_reference-api-core-modules.md) — コアモジュール
- [Config Env and Fields](06_eventbus_06_02_config-env-and-fields.md) — 設定環境とフィールド
- [Bind Address and Start](06_eventbus_06_05_bind-address-and-start.md) — バインドアドレスと起動
- [DLQ Background Loop](06_eventbus_05_01_dlq-background-loop.md) — DLQバックグラウンドループ
- [Health Endpoint Semantics](06_eventbus_05_03_health-endpoint-semantics.md) — ヘルスエンドポイントセマンティクス

### Operations

- [EventBus Operations](06_eventbus_05_7-eventbus-operations.md) — EventBus運用手順

### Known Issues

- [EventBus Known Issues](06_eventbus_90_inconsistencies_and_known_issues.md) — EventBus既知の問題

### Implementation References

- `scripts/eventbus/broker.py` — `EventBroker.publish()`, `EventBroker.notify_subscribers()`
- `scripts/eventbus/publish.py` — `publish_event()`
- `scripts/eventbus/subscribe.py` — `subscribe_events()`
- `scripts/eventbus/ack.py` — `ack_event()`
- `scripts/eventbus/nack.py` — `nack_event()`
- `scripts/eventbus/dlq.py` — `promote_single()`
- `scripts/eventbus/offsets.py` — `write_offset()`, `read_offset()`
- `events`テーブル — `seq`, `event_id`, `topic`, `payload`, `acked_at`, `delivery_failure_count`, `dlq_requeue_count`, `dlq_at`
- テスト — `tests/test_eventbus_*.py`

## Change History

- 2026-08-21: Acceptedとして作成。未決事項の判断を確定

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
