---
title: "Event Bus: Reference API — Route Handlers"
category: eventbus
tags:
  - event-bus
  - api-reference
  - route-handlers
  - publish-route
  - ack-route
  - dlq-route
  - replay-route
  - subscribe-route
  - health-route
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_06_01_reference-api-core-modules.md
  - 06_eventbus_06_03_reference-api-broker-and-offsets.md
source:
  - 06_eventbus_06_01_reference-api-core-modules.md
---

# Event Bus: Reference API — Route Handlers

## scripts/eventbus/publish_route.py

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `publish` | `(request: Request) -> dict[str, Any]` | POST /publish ハンドラ。JSON Schema を検証し、イベントを DB に挿入し、JSONL アーカイブに追記し、EventBroker に通知する |

### レスポンス

| フィールド | 型 | 説明 |
|---|---|---|
| `event_id` | str | イベント ID |
| `seq` | int | 割り当てられたシーケンス番号 |

### エラーレスポンス

| ステータスコード | 詳細 | 条件 |
|---|---|---|
| 422 | JSON Schema 検証エラーメッセージ | 無効なペイロード |

**注記**: JSONL アーカイブへの追記失敗は HTTP エラーとして表面化しない。`OSError` はキャッチされ、警告としてログに記録され、イベントは SQLite にコミットされたままリクエストは 200 を返す。

---

## scripts/eventbus/ack_route.py

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `ack_event` | `(request: Request, event_id: str, consumer_id: str = Query(default="")) -> dict[str, Any]` | POST /events/{event_id}/ack ハンドラ(正規のパス) |
| `nack` | `(request: Request, event_id: str = Query(default="")) -> dict[str, Any]` | POST /nack ハンドラ。失敗回数をインクリメントし、`>= max_retry` の場合は DLQ に promotion する |

### レスポンス (ack)

| フィールド | 型 | 説明 |
|---|---|---|
| `event_id` | str | イベント ID |
| `acked` | bool | ack が成功した場合は常に True |
| `seq` | int \| None | シーケンス番号(新規に ack された場合のみ。既に ack 済みの場合は含まれない) |
| `already_acked` | bool | イベントが既に ack 済みだった場合のみ存在する |

### レスポンス (nack)

| フィールド | 型 | 説明 |
|---|---|---|
| `event_id` | str | イベント ID |
| `delivery_failure_count` | int | 現在の配信失敗回数 |
| `dlq_promoted` | bool \| None | イベントが DLQ に promotion された場合のみ存在する |

### エラーレスポンス (nack)

| ステータスコード | 詳細 | 条件 |
|---|---|---|
| 404 | "event not found" | イベントが存在しない、または既に ack 済み |
| 400 | "event_id is required" | event_id クエリパラメータが指定されていない |

---

## scripts/eventbus/dlq_route.py

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `dlq_list` | `(request: Request, limit: int = Query(default=100, ge=1, le=1000), offset: int = Query(default=0, ge=0)) -> dict[str, Any]` | GET /dlq ハンドラ。ページネーションされた DLQ イベントリストを返す |
| `dlq_requeue` | `(request: Request, event_id: str) -> dict[str, Any]` | POST /dlq/{event_id}/requeue ハンドラ。DLQ イベントを通常の配信に requeue する |

### レスポンス (dlq_list)

| フィールド | 型 | 説明 |
|---|---|---|
| `total` | int | DLQ イベントの総数 |
| `limit` | int | リクエストされた limit |
| `offset` | int | リクエストされた offset |
| `items` | list[dict] | ページネーションされた DLQ イベント dict のリスト |

### レスポンス (dlq_requeue)

| フィールド | 型 | 説明 |
|---|---|---|
| `event_id` | str | イベント ID |
| `requeued` | bool | requeue が成功した場合は常に True |
| `dlq_imminent` | bool \| None | failure_count >= max_retry の場合のみ存在する(イベントが直ちに再度 DLQ 化される可能性がある) |

### エラーレスポンス (dlq_requeue)

| ステータスコード | 詳細 | 条件 |
|---|---|---|
| 404 | "event not found" | イベントが存在しない |
| 409 | "event is not in DLQ" | イベントは存在するが dlq_at が NULL(既に requeue または ack 済み) |

---

## scripts/eventbus/replay_route.py

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `replay` | `(request: Request, since_seq: int = Query(default=0), fmt: str = Query(default="sse"), limit: int = Query(default=100), offset: int = Query(default=0)) -> StreamingResponse \| dict[str, Any]` | GET /replay ハンドラ。SSE(デフォルト)でイベントをストリーミングするか、`fmt=json` の場合はページネーションされた JSON を返す |

---

## scripts/eventbus/subscribe_route.py

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `subscribe` | `(request: Request, topic: list[str] = Query(default=[]), since_seq: int = Query(default=0), consumer_id: str = Query(default="")) -> StreamingResponse` | GET /subscribe ハンドラ。SSE ストリーミングによる replay+push ハイブリッドモデル。`topic` は複数値を受け付ける |

---

## scripts/eventbus/health_route.py

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `health_check` | `(request: Request) -> JSONResponse` | GET /health ハンドラ。各コンポーネントのヘルス状態を返す |

---

## scripts/eventbus/app.py — HTTP エンドポイント

### 有効なエンドポイント

| エンドポイント | メソッド | 説明 |
|---|---|---|
| `/publish` | POST | イベントを publish する(event_id により冪等) |
| `/replay` | GET | 過去のイベントを replay する(SSE ストリームまたはページネーションされた JSON レスポンス。JSON の場合は limit/offset によるページネーションをサポート) |
| `/subscribe` | GET | replay+push ハイブリッドモデルでイベントをストリーミングする |
| `/health` | GET | コンポーネントのヘルスチェック |
| `/dlq` | GET | DLQ イベントを一覧表示する |
| `/dlq/{event_id}/requeue` | POST | DLQ イベントを通常の配信に requeue する |
| `/events/{event_id}/ack` | POST | イベントを ack する(正規の ack パス) |
| `/nack` | POST | イベントを nack する |

**注記 (2026-07-10):** `POST /ack`(クエリパラメータ方式の互換エイリアス)は削除された。

## Related Documents

- `06_eventbus_06_01_reference-api-core-modules.md`
- `06_eventbus_06_03_reference-api-broker-and-offsets.md`

## Keywords

event-bus
api-reference
route-handlers
publish-route
ack-route
dlq-route
replay-route
subscribe-route
health-route
