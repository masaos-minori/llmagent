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

**冪等性の理由**: 同じ `event_id` で再 publish しても、SQLite の UNIQUE 制約により既存行が更新されないため、コンシューマは同じイベントを二度受信しない。これは設計上の意図でありバグではない。

**リクエストボディ**: `event_envelope.json` JSON Schema に対して検証される。必須フィールドは `event_id`(UUID v4)、`topic`(1〜255文字)、`payload`(オブジェクト)、`producer`(1〜255文字)、`published_at`(ISO-8601)。`schema_version` は省略可能でデフォルト "1.0"。追加プロパティは許可されない。

**レスポンス**: 成功時は `{event_id, seq}`。422 は JSON Schema 検証エラー。

**JSONL 追記の失敗**: JSONL アーカイブへの書き込みが失敗しても、イベントは SQLite にコミットされ 200 が返される。WARNING がログに記録される。

---

## GET /replay

過去のイベントを replay する。`seq > since_seq` を満たすイベントを返す。`format=json` の場合はページネーションに対応する。

**クエリパラメータ:** `since_seq`(>=0)、`limit`(1-1000, デフォルト100)、`offset`(>=0)、`format`(sse/json, デフォルト sse)。

**レスポンス（`format=json`）:** `{total, limit, offset, items}` のページネーションオブジェクト。`total` は limit/offset を無視した総数。

**レスポンス（`format=sse`）:** 各イベントは `data: {...}` 行として出力される。SSE 形式はページネーション可能な増分消費には対応していない。ストリームは `limit` 件出力後に終了する。

**エラーレスポンス:** 422 — パラメータ値が不正な場合。

## Related Documents

- `06_eventbus_02_02_subscribe-ack.md`
- `06_eventbus_02_03_nack-health-dlq.md`
