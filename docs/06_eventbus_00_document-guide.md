---
title: "Event Bus: Document Guide"
category: eventbus
tags:
  - event-bus
  - documentation
  - guide
  - routing
  - file-index
related:
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_02_01_publish-replay.md
  - 06_eventbus_02_02_subscribe-ack.md
  - 06_eventbus_02_03_nack-health-dlq.md
  - 06_eventbus_06_01_reference-api-core-modules.md
source:
  - index.md
---

# Event Bus: Document Guide

## 目的

これらのドキュメントは `scripts/eventbus/` の実装について説明する。Event Bus 機能の実装、デバッグ、拡張を行う際に使用すること。

## 読む順序

| ファイル | 読むタイミング |
|---|---|
| `06_eventbus_01_system-overview.md` | 出発点: アーキテクチャ、機能、セキュリティモデル |
| `06_eventbus_02_01_publish-replay.md` | POST /publish、GET /replay エンドポイント |
| `06_eventbus_02_02_subscribe-ack.md` | GET /subscribe、POST /events/{event_id}/ack |
| `06_eventbus_02_03_nack-health-dlq.md` | POST /nack、GET /health、DLQ 管理 |
| `06_eventbus_02_04_dlq-background-loop.md` | DLQ スイープのバックグラウンドループ |
| `06_eventbus_02_05_failure-behavior-summary.md` | 障害動作のまとめ表 |
| `06_eventbus_03_persistence_schema_and_replay.md` | SQLite スキーマ、WAL、JSONL アーカイブ、リプレイのセマンティクス |
| `06_eventbus_04_dlq_offsets_and_delivery_semantics.md` | DLQ への移行、コンシューマオフセット、at-least-once 保証 |
| `06_eventbus_05_01_config-env-and-fields.md` | 環境変数 + Config フィールド |
| `06_eventbus_05_02_bind-address-and-start.md` | バインドアドレスのルール + 起動コマンド |
| `06_eventbus_05_03_health-endpoint-semantics.md` | ヘルスエンドポイントのセマンティクス |
| `06_eventbus_05_04_consumer-id-stability.md` | コンシューマ ID の安定性 |
| `06_eventbus_05_05_delivery-operations.md` | 検証、監視、再接続時のリカバリ |
| `06_eventbus_05_06_dlq-operations.md` | DLQ 運用 |
| `06_eventbus_05_07_validation-status.md` | CI 検証状況 |
| `06_eventbus_06_01_reference-api-core-modules.md` | コアモジュール API（app.py、config.py、db.py、dlq.py） |
| `06_eventbus_06_02_reference-api-route-handlers.md` | ルートハンドラ API |
| `06_eventbus_06_03_reference-api-broker-and-offsets.md` | ブローカーとオフセットの API |
| `06_eventbus_90_inconsistencies_and_known_issues.md` | 既知のスキーマ/実装上のギャップ、未確認事項 |

## AI クエリルーティング表

| 質問 | ファイル |
|---|---|
| Event Bus とは何か、どのように動作するか | `06_eventbus_01` |
| イベントの publish や replay の方法は | `06_eventbus_02` (§Publish-Replay) |
| イベントの subscribe や ack の方法は | `06_eventbus_02` (§Subscribe-Ack) |
| nack、ヘルスチェック、DLQ 管理の方法は | `06_eventbus_02` (§Nack-Health-DLQ) |
| DLQ バックグラウンドループとは | `06_eventbus_02` (§DLQ Background Loop) |
| 把握しておくべき障害動作は何か | `06_eventbus_02` (§Failure Behavior Summary) |
| Config フィールドと環境変数は何か | `06_eventbus_05` (§Config Env and Fields) |
| バインドアドレスのルールはどうなっているか | `06_eventbus_05` (§Bind Address and Start Command) |
| ヘルスエンドポイントはどう動作するか | `06_eventbus_05` (§Health Endpoint Semantics) |
| コンシューマ ID の安定性とは | `06_eventbus_05` (§Consumer ID Stability) |
| 配信の検証やコンシューマの監視方法は | `06_eventbus_05` (§Delivery Operations) |
| DLQ 運用はどのように行うか | `06_eventbus_05` (§DLQ Operations) |
| CI の検証状況はどうなっているか | `06_eventbus_05` (§Validation Status) |
| 永続化レイヤーとは何か | `06_eventbus_03` |
| DLQ、オフセット、配信のセマンティクスとは | `06_eventbus_04` |
| クラス X はどこで定義され、どこから呼ばれているか | `06_eventbus_06` (§Reference API Core Modules / Route Handlers / Broker and Offsets) |
| 既知の問題や仕様の矛盾点は何か | `06_eventbus_90` |

## ファイル索引

| ファイル | 説明 |
|---|---|
| [06_eventbus_00_document-guide.md](06_eventbus_00_document-guide.md) | エントリポイント |
| [06_eventbus_01_system-overview.md](06_eventbus_01_system-overview.md) | アーキテクチャ、機能、セキュリティモデル |
| [06_eventbus_02_01_publish-replay.md](06_eventbus_02_01_publish-replay.md) | POST /publish、GET /replay エンドポイント |
| [06_eventbus_02_02_subscribe-ack.md](06_eventbus_02_02_subscribe-ack.md) | GET /subscribe、POST /events/{event_id}/ack |
| [06_eventbus_02_03_nack-health-dlq.md](06_eventbus_02_03_nack-health-dlq.md) | POST /nack、GET /health、GET /dlq、POST /dlq/{event_id}/requeue |
| [06_eventbus_02_04_dlq-background-loop.md](06_eventbus_02_04_dlq-background-loop.md) | DLQ スイープのバックグラウンドループ |
| [06_eventbus_02_05_failure-behavior-summary.md](06_eventbus_02_05_failure-behavior-summary.md) | 障害動作のまとめ表 |
| [06_eventbus_03_persistence_schema_and_replay.md](06_eventbus_03_persistence_schema_and_replay.md) | SQLite スキーマ、WAL、JSONL アーカイブ、リプレイのセマンティクス |
| [06_eventbus_04_dlq_offsets_and_delivery_semantics.md](06_eventbus_04_dlq_offsets_and_delivery_semantics.md) | DLQ への移行、コンシューマオフセット、at-least-once 保証 |
| [06_eventbus_05_01_config-env-and-fields.md](06_eventbus_05_01_config-env-and-fields.md) | 環境変数 + Config フィールド |
| [06_eventbus_05_02_bind-address-and-start.md](06_eventbus_05_02_bind-address-and-start.md) | バインドアドレス + 起動コマンド + TOML の例 |
| [06_eventbus_05_03_health-endpoint-semantics.md](06_eventbus_05_03_health-endpoint-semantics.md) | ヘルスエンドポイントのセマンティクス |
| [06_eventbus_05_04_consumer-id-stability.md](06_eventbus_05_04_consumer-id-stability.md) | コンシューマ ID の安定性 |
| [06_eventbus_05_05_delivery-operations.md](06_eventbus_05_05_delivery-operations.md) | 検証、監視、再接続、サブスクライバー数 |
| [06_eventbus_05_06_dlq-operations.md](06_eventbus_05_06_dlq-operations.md) | DLQ ファイルの作成、バックグラウンドループ、requeue、監視 |
| [06_eventbus_05_07_validation-status.md](06_eventbus_05_07_validation-status.md) | CI 検証状況 |
| [06_eventbus_06_01_reference-api-core-modules.md](06_eventbus_06_01_reference-api-core-modules.md) | app.py、config.py、db.py、dlq.py のモジュール API |
| [06_eventbus_06_02_reference-api-route-handlers.md](06_eventbus_06_02_reference-api-route-handlers.md) | publish_route.py、ack_route.py、dlq_route.py、replay_route.py、subscribe_route.py、health_route.py |
| [06_eventbus_06_03_reference-api-broker-and-offsets.md](06_eventbus_06_03_reference-api-broker-and-offsets.md) | broker.py、offsets.py のモジュール API |
| [06_eventbus_90_inconsistencies_and_known_issues.md](06_eventbus_90_inconsistencies_and_known_issues.md) | 既知の不具合、仕様の矛盾、未解決事項、保留事項 |

## 正典ソースのルール

動作に関する正典（canonical）のソースは **ソースコード**（`scripts/eventbus/`）であり、これらのドキュメントではない。ドキュメントとコードが矛盾する場合はコードを信頼し、ドキュメントを更新すること。

## Governance

Cross-cutting documentation rules and policies:

- [Documentation Governance](00_governance_01_documentation-governance.md)
- [Canonical Source Rule](00_governance_02_canonical-source-rule.md)
- [Evidence Labels](00_governance_03_evidence-labels.md)
- [Known Issues Template](00_governance_04_known-issues-template.md)
- [Deprecated Items](00_governance_05_deprecated-items.md)
- [AI Reading Metadata](00_governance_06_ai-reading-metadata.md)

## Related Documents

- `06_eventbus_01_system-overview.md`
- `06_eventbus_03_persistence_schema_and_replay.md`
- `06_eventbus_04_dlq_offsets_and_delivery_semantics.md`
- `06_eventbus_05_01_config-env-and-fields.md`
- `06_eventbus_06_01_reference-api-core-modules.md`

## Keywords

event-bus
documentation
guide
routing
file-index
