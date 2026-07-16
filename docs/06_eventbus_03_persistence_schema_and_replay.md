---
title: "Event Bus: Persistence, Schema, and Replay"
category: eventbus
tags:
  - event-bus
  - sqlite
  - schema
  - wal
  - jsonl-archive
  - replay
  - consumer-offset
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_02_01_publish-replay.md
  - 06_eventbus_04_dlq_offsets_and_delivery_semantics.md
source:
  - index.md
---

# Event Bus: Persistence, Schema, and Replay

## SQLiteデータベース

全イベントの主ストアである。起動時に共有コネクションとして一度だけオープンされる（`check_same_thread=False`）。WALモードが有効化されており、書き込み中でも並行読み取りが可能である。

**`check_same_thread=False` が安全な理由**: DB操作は `asyncio.to_thread()` を介してスレッドプール上で実行され、モジュールレベルの `threading.Lock` により直列化される。さらにWALモードにより、SQLiteレベルでも同時書き込みが直列化される。

## スキーマ

```sql
CREATE TABLE IF NOT EXISTS events (
    seq                    INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id               TEXT    NOT NULL UNIQUE,
    topic                  TEXT    NOT NULL,
    payload                TEXT    NOT NULL,   -- JSON string
    producer               TEXT    NOT NULL,
    published_at           TEXT    NOT NULL,
    acked_at               TEXT,               -- set during ack (idempotent)
    delivery_failure_count INTEGER NOT NULL DEFAULT 0,
    dlq_requeue_count      INTEGER NOT NULL DEFAULT 0,
    dlq_at                 TEXT                -- set when event is promoted to DLQ
);
```

### フィールドの意味

| フィールド | 説明 |
|---|---|
| `seq` | 自動増分整数。replayとsubscribeのカーソルとして使用される |
| `event_id` | クライアント指定のUUID。UNIQUE制約により重複を防止 |
| `topic` | イベントのトピック文字列（1～255文字） |
| `payload` | イベントペイロードのシリアライズ済みJSON文字列 |
| `producer` | プロデューサー識別子文字列（1～255文字） |
| `published_at` | イベントがpublishされた時刻のISO-8601タイムスタンプ |
| `acked_at` | ack時に設定される（冪等— 既存の値を上書きしない） |
| `delivery_failure_count` | nack時にインクリメントされる。`>= max_retry` でDLQ昇格をトリガーする |
| `dlq_requeue_count` | DLQ requeue時にインクリメントされる。`delivery_failure_count` はリセットしない |
| `dlq_at` | DLQに昇格した時刻のISO-8601タイムスタンプ。有効なイベントではNULL |

**注記（2026-07-10）:** `retry_count` は削除された（どのコードパスからも更新されておらず、スキーマ上の残存物にすぎなかった）。`scripts/eventbus/db.py` のマイグレーション処理は、既存のデータベースに対して `ALTER TABLE events DROP COLUMN retry_count` によりこのカラムを冪等に削除する。このフィールドには意味のあるデータが入っていなかったため、データ移行は不要である。

### 初期化とマイグレーションの経路

`open_db()` は起動時に `_init_schema()` を呼び出す。このとき2つの経路に分岐する（`scripts/eventbus/db.py`）。

- **新規DB**: `events` テーブルが存在しない場合、`schema.sql` をそのまま `executescript()` する。上記のスキーマ定義とインデックス4種が一度に作成される。
- **既存DB**: `events` テーブルが存在する場合、`schema.sql` は実行されず、代わりにマイグレーション処理が加算的マイグレーションを行う。具体的には `delivery_failure_count` / `dlq_requeue_count` カラムをALTER TABLEで追加（`duplicate column name` エラーは無視して冪等化）、`retry_count` カラムをDROP COLUMN（`no such column` エラーは無視）、`idx_events_dlq_at` / `idx_events_dlq_seq` インデックスを `CREATE INDEX IF NOT EXISTS` で追加する。

根拠分類: Explicit in code（`scripts/eventbus/db.py` のスキーマ初期化処理 / マイグレーション処理）。

### インデックス

- `topic` に対する `idx_events_topic` — トピックでフィルタするsubscribeクエリを高速化
- `seq` に対する `idx_events_seq` — カーソルベースのreplayを高速化
- `dlq_at` に対する `idx_events_dlq_at` — DLQクエリを高速化（WHERE dlq_at IS NOT NULL）
- `(dlq_at, seq)` に対する `idx_events_dlq_seq` — DLQイベントをseqで並べ替えるための複合インデックス

## JSONLアーカイブ

publishされた各イベントは `{storage_dir}/events.jsonl` にも追記される（1行に1つのJSONオブジェクト、`seq` が付加される）。JSONLファイルは補助的なものであり、SQLiteが正のストアである。JSONLへの追記に失敗した場合でも、イベントはSQLiteに残り200が返される。

**主データをJSONLから読み取ってはならない** — 常にSQLiteクエリを使用すること。

## コンシューマーIDの安定性

コンシューマーIDは常に `consumer_id` クエリパラメータでクライアントが指定するものであり、サーバー側で自動生成されることはない。

再起動後にオフセットの再開を機能させるには、コンシューマーは再起動をまたいで永続する安定した consumer_id を使用する必要がある。

2つのコンシューマーが同じconsumer_idを使用した場合、オフセットファイルは最後の書き込みが優先される（衝突検知は行われない）。

## Replayの挙動

`GET /replay?since_seq=N` は `seq > N` を満たすイベントを `seq` 昇順で返す。SSE形式（デフォルト、`format=sse`）では、イベントごとに1つの `data: {...}\n\n` フレームがストリーミングされる。JSON形式（`format=json`）では `{"total": ..., "limit": ..., "offset": ..., "items": [...]}` の形で返される。

**ページネーション**: `limit`（デフォルト100、1～1000）と `offset`（デフォルト0）クエリパラメータで結果を分割取得する。1回のレスポンスで返るのは最大 `limit` 件までであり、「`seq > N` を満たす全イベント」が無条件に一括で返るわけではない。全件を取得するには `offset` をずらして繰り返し呼び出す必要がある。`total` はJSON形式の場合のみ `seq > N` の総件数として返される（根拠分類: Explicit in code — `scripts/eventbus/replay_route.py`）。

Replayは、JSONLではなくSQLiteから読み取る。

## Related Documents

- `06_eventbus_00_document-guide.md`
- `06_eventbus_01_system-overview.md`
- `06_eventbus_02_01_publish-replay.md`
- `06_eventbus_04_dlq_offsets_and_delivery_semantics.md`

## Keywords

event-bus
sqlite
schema
wal
jsonl-archive
replay
consumer-offset
