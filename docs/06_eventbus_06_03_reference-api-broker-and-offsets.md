---
title: "Event Bus: Reference API — Broker and Offsets"
category: eventbus
tags:
  - event-bus
  - api-reference
  - broker
  - offsets
  - eventbroker
  - subscriber
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_06_01_reference-api-core-modules.md
  - 06_eventbus_06_02_reference-api-route-handlers.md
source:
  - 06_eventbus_06_01_reference-api-core-modules.md
---

# Event Bus: Reference API — Broker and Offsets

## scripts/eventbus/broker.py

| クラス | 説明 |
|---|---|
| `_Subscriber` | 内部データクラス: `queue: asyncio.Queue[dict \| None]`、`topics: list[str]`(空リストは全トピックを意味する) |
| `EventBroker` | トピックを意識したファンアウトを行う、インメモリの pub/sub ブローカー |

### EventBroker のメソッド

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `subscribe` | `(topics: list[str]) -> _Subscriber` | 新規サブスクライバを登録する。topics=[] は全トピックを意味する |
| `unsubscribe` | `(sub: _Subscriber) -> None` | サブスクライバをレジストリから削除する。冪等 |
| `publish` | `(event: dict[str, Any]) -> int` | イベントを該当するサブスクライバにファンアウトする。配信件数を返す |
| `shutdown` | `() -> None` | 全サブスクライバに None センチネルを送信し、各自の queue.get() 呼び出しのブロックを解除する |
| `subscriber_count` | `() -> int` | アクティブなサブスクライバ数を返す |
| `max_queue_depth` | `() -> int` | 全サブスクライバ中の最大キュー深度を返す |
| `slow_consumer_count` | `() -> int` | キュー深度が 100 以上のサブスクライバ数を返す |

---

## scripts/eventbus/offsets.py

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `read_offset` | `(offsets_dir, consumer_id) -> int` | 保存されたオフセットを読み込む。見つからない場合は 0 を返す |
| `write_offset` | `(offsets_dir, consumer_id, seq) -> None` | オフセットをファイルに書き込む。必要であればディレクトリを作成する |

## Related Documents

- `06_eventbus_06_01_reference-api-core-modules.md`
- `06_eventbus_06_02_reference-api-route-handlers.md`

## Keywords

event-bus
api-reference
broker
offsets
eventbroker
subscriber
