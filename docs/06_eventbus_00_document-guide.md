---
title: "Event Bus: Document Guide"
category: eventbus
tags:
  - event-bus
  - documentation
  - guide
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

| カテゴリ | ファイル |
|---|---|
| 全体像・アーキテクチャ | `06_eventbus_01_system-overview.md` |
| 主要操作（publish/replay/subscribe/ack/nack/DLQ） | `06_eventbus_02_*` |
| 永続化・スキーマ | `06_eventbus_03_persistence_schema_and_replay.md` |
| delivery semantics・consumer 責務 | `06_eventbus_04_dlq_offsets_and_delivery_semantics.md` |
| 設定・セキュリティ制約・運用 | `06_eventbus_05_*` |
| Reference API（詳細確認用） | `06_eventbus_06_*` |
| 既知問題・保留事項 | `06_eventbus_90_inconsistencies_and_known_issues.md` |

## AI クエリルーティング

| 質問 | ルール |
|---|---|
| Event Bus の設計意図・アーキテクチャ | `06_eventbus_01` |
| イベントの publish / replay / subscribe / ack / nack / DLQ | `06_eventbus_02` |
| 永続化レイヤー・正本データ | `06_eventbus_03` |
| delivery semantics・consumer 責務 | `06_eventbus_04` |
| 設定・bind address・ヘルスチェック・運用 | `06_eventbus_05` |
| API詳細・型・スキーマ | `06_eventbus_06` |
| 既知の問題・仕様の矛盾 | `06_eventbus_90` |

## 正典ソースのルール

動作に関する正典（canonical）のソースは **ソースコード**（`scripts/eventbus/`）であり、これらのドキュメントではない。ドキュメントとコードが矛盾する場合はコードを信頼し、ドキュメントを更新すること。

## Known Issues / Deferred Items

既知の制限・仕様ギャップ・保留事項は `06_eventbus_90_inconsistencies_and_known_issues.md` に一元管理している。個別の章に重複して記載しない。

## Reference API

`06_eventbus_06_*` は詳細なAPI仕様（型定義、スキーマ、エンドポイント仕様）をまとめたReference APIである。設計判断を確認した後は必要に応じて参照するが、設計本文とは分離されている。

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
