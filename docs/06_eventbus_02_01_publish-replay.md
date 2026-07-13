---
title: "Event Bus: Publish and Replay Endpoints"
category: eventbus
tags:
  - event-bus
  - http-api
  - publish
  - replay
  - sse
  - streaming
  - json-schema
  - pagination
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_02_02_subscribe-ack.md
  - 06_eventbus_02_03_nack-health-dlq.md
source:
  - 06_eventbus_02_01_publish-replay.md
---

# Event Bus: Publish and Replay Endpoints

## POST /publish

イベントを publish する。冪等性あり: 重複する `event_id` は黙って無視される。

**実装の詳細（Explicit in code）**: `event_id` が既存の場合、SQLite への `INSERT OR IGNORE` はスキップされ（`inserted=False`）、その場合は `EventBroker.publish()` による購読者への配信通知も行われない。既存イベントと同じ `seq` を含む 200 レスポンスは返るが、ライブ subscribe 中のコンシューマへは再配信されない。

**リクエストボディ**（`event_envelope.json` JSON Schema に対して検証される）:

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "topic": "topic.name",
  "payload": {},
  "producer": "producer-name",
  "published_at": "2026-06-24T00:00:00Z"
}
```

**リクエストボディの制約:**

| フィールド | 型 | 必須 | 制約 |
|---|---|---|---|
| `event_id` | string (UUID v4) | Yes | `^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$` に一致する必要がある |
| `topic` | string | Yes | minLength 1、maxLength 255 |
| `payload` | object | Yes | オブジェクトである必要がある（文字列不可） |
| `producer` | string | Yes | minLength 1、maxLength 255 |
| `published_at` | string (date-time) | Yes | ISO-8601 date-time 形式 |
| `schema_version` | string | No | デフォルト "1.0" |

**追加制約**: 追加プロパティは許可されない（`additionalProperties: false`）。余分なフィールドがあると 422 の検証エラーになる。

**レスポンス 200:**
```json
{"event_id": "uuid-string", "seq": 42}
```

**レスポンス 422:** JSON Schema の検証エラー。

**JSONL 追記の失敗**: JSONL アーカイブへの書き込みが失敗した場合（例: ディスクフル）でも、イベントは SQLite にはコミットされ、200 が返される。WARNING がログに記録される。

---

## GET /replay

過去のイベントを replay する。`seq > since_seq` を満たすイベントを返す。`format=json` の場合はページネーションに対応する。

**クエリパラメータ:**

| パラメータ | 型 | デフォルト | 制約 | 説明 |
|---|---|---|---|---|
| `since_seq` | int | 0 | >= 0 | 開始シーケンス番号（この値自体は含まない） — 上限値の検証なし |
| `limit` | int | 100 | >= 1、<= 1000 | 1 ページあたりに返すイベントの最大数 |
| `offset` | int | 0 | >= 0 | ページネーションのためにスキップするイベント数 |
| `format` | str | `sse` | `sse` または `json` | レスポンス形式: SSE ストリームまたは JSON のページネーションオブジェクト |

**レスポンス（`format=json`）:** `total`、`limit`、`offset`、`items` フィールドを持つページネーションオブジェクト:
```json
{"total": 100, "limit": 50, "offset": 0, "items": [{seq, event_id, topic, payload, producer, published_at}, ...]}
```

- `total`: 条件に一致するイベントの総数（limit/offset は無視）— 残りページ数の計算に使用
- `limit`: リクエストされた limit の値
- `offset`: リクエストされた offset の値
- `items`: イベントオブジェクトの配列（最大 `limit` 件）。`offset >= total` の場合は空配列

**レスポンス（`format=sse`）:** 各イベントは SSE の data 行として出力される:
```
data: {"seq": 42, "event_id": "...", "topic": "...", "payload": {}, "producer": "...", "published_at": "..."}
```

**SSE のページネーション動作**: SSE 形式は SQL レベルの `LIMIT/OFFSET` を適用するが、ページネーション可能な増分消費には対応**していない**。ストリームは `limit` 件のイベントを出力した後に終了し、クローズする — 更新後の offset で同じストリームを継続する仕組みはない。ページネーションによる消費が必要な場合は `format=json` を使用すること。

**エラーレスポンス:**
- **422**: パラメータ値が不正な場合（limit < 1 または limit > 1000、offset < 0）

## Related Documents

- `06_eventbus_02_02_subscribe-ack.md`
- `06_eventbus_02_03_nack-health-dlq.md`

## Keywords

event-bus
http-api
publish
replay
sse
streaming
json-schema
pagination
