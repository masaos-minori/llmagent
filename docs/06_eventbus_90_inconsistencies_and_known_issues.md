---
title: "Event Bus: Known Inconsistencies and Issues"
category: eventbus
tags:
  - event-bus
  - known-issues
  - inconsistencies
  - spec-conflicts
  - deferred-items
  - ack-offset
  - monotonicity
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_02_02_subscribe-ack.md
  - 06_eventbus_02_04_dlq-background-loop.md
  - 06_eventbus_04_dlq_offsets_and_delivery_semantics.md
source:
  - index.md
---

# Event Bus: Known Inconsistencies and Issues

## 対応が必要な項目

これらの項目は、実装変更を要する未解決の問題、またはユーザーに実際の影響を与えている問題を示す。

### Ack オフセットの単調性が保証されていない

| 項目 | 安全な解釈 | 推奨される対応 |
|---|---|---|
| `offsets.py` の `write_offset()` は、オフセットの単調な前進を保証しない(max(current, new) のチェックがない) | 古いイベント seq を ack すると、コンシューマのオフセットが後退する可能性がある。再接続時にコンシューマが重複イベントを受信することがある | コンシューマ側でオフセットの後退が起こり得ることを考慮した実装が必要。サーバー側での修正は予定していない |

## ドキュメントのみで対応する項目

これらの項目は、実装変更を伴わないドキュメント上の改善事項である。

### /replay?format=json はページネーションされたオブジェクトを返す

| 項目 | 安全な解釈 |
|---|---|
| `GET /replay?format=json` は生の配列ではなく `{total, limit, offset, items}` を返す | クライアントは limit/offset パラメータを使って replay 結果をページネーションできる |

### DLQ への promotion は nack 時のインライン処理と安全網としての sweep の組み合わせである

| 項目 | 安全な解釈 |
|---|---|
| 主たる DLQ への promotion は、`delivery_failure_count >= max_retry` となった際に `/nack` でインラインに実行される。バックグラウンドループは、取り残されたイベントに対する安全網としての sweep である | バックグラウンドの DLQ ループは、しきい値に達したがインラインで promotion されなかったイベントを捕捉する。sweep の結果が 0 以外である場合、インライン promotion に問題がある可能性を示す |

## 保留中の項目

Event Bus と Agent ランタイムとの統合は、現時点では意図的に実装されていない。

| 項目 | 状態 | 補足 |
|---|---|---|
| Agent によるイベント publish | 保留 | Agent 側のイベントプロデューサーは実装されていない。Event Bus の HTTP API はどの HTTP クライアントからの publish もサポートしている。Agent 専用のプロデューサーは今後のリリースで追加予定である |
| Agent による SSE subscription | 保留 | `/subscribe` の SSE 経由でイベントを消費する Agent 側のサブスクライバーは存在しない。Agent 側のコンシューマーは今後のリリースで追加予定である |
| Agent 用のイベントトピック | 保留 | 現時点で Agent が定義するトピックは存在しない。Agent のライフサイクルイベント用のトピック規約は、Agent 統合が実装される際に定義される |

## スキーマと実装の差異

| フィールド | スキーマ定義 | 実行時の挙動 | 状態 |
|---|---|---|---|
| `acked_at` | TEXT | ack 時に設定される(冪等 — 既存の値を上書きしない) | 使用中 — `db.py::ack_event()` を参照 |
| `delivery_failure_count` | INTEGER NOT NULL DEFAULT 0 | nack 時にインクリメントされる。`>= max_retry` で DLQ への promotion が発生する | 使用中 — `db.py::nack_event()` を参照 |
| `dlq_requeue_count` | INTEGER NOT NULL DEFAULT 0 | DLQ requeue 時にインクリメントされる。`delivery_failure_count` はリセットされない | 使用中 — `db.py::requeue_event()` を参照 |
| `dlq_at` | TEXT | イベントが DLQ に promotion された時に設定される(インラインまたはバックグラウンド sweep) | 使用中 — DLQ promotion 時に設定される |

## Related Documents

- `06_eventbus_00_document-guide.md`
- `06_eventbus_01_system-overview.md`
- `06_eventbus_02_02_subscribe-ack.md`
- `06_eventbus_02_04_dlq-background-loop.md`
- `06_eventbus_04_dlq_offsets_and_delivery_semantics.md`

## Keywords

event-bus
known-issues
inconsistencies
spec-conflicts
deferred-items
ack-offset
monotonicity
