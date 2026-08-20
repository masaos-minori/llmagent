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

全イベントの主ストア。WALモード有効で並行読み取り可能。DB操作は `asyncio.to_thread()` + `threading.Lock` で直列化される。

## スキーマ

主なカラム: `seq`(PK), `event_id`(UNIQUE), `topic`, `payload`(JSON文字列), `producer`, `published_at`, `acked_at`(冪等), `delivery_failure_count`, `dlq_requeue_count`, `dlq_at`(DLQ昇格時)。

`retry_count` カラムは削除済み。既存DBのマイグレーションは冪等に行われる。

### インデックス

- `idx_events_topic` — トピックフィルタ用
- `idx_events_seq` — replayカーソル用
- `idx_events_dlq_at` — DLQクエリ用
- `idx_events_dlq_seq` — DLQイベントのseq順ソート用

## JSONLアーカイブ

`{storage_dir}/events.jsonl` に追記されるが補助的なもの。SQLiteが主ストア。JSONLへの追記失敗でも200を返す。主データはJSONLから読まずにSQLiteクエリを使用すること。

## コンシューマーIDの安定性

コンシューマーIDはクライアントが指定し、サーバー側で自動生成されない。再起動後も安定したIDを使用すること。同一IDの複数コンシューマは最後の書き込みが優先される。

## Replayの挙動

`GET /replay?since_seq=N` は `seq > N` のイベントを `seq` 昇順で返す。SSE形式は逐次ストリーミング、JSON形式は `{total, limit, offset, items}` ページネーションオブジェクト。`total` はJSON形式のみ。

## SQLite/JSONL 整合性チェックとリカバリ手順

### 検出方法
SQLiteの最大 `seq` と JSONLアーカイブの最終行の `seq` を比較し、差異があれば JSONL への追記失敗が発生していたことを示します。

```bash
# SQLite の最大 seq 取得
sqlite3 /path/to/eventbus.db "SELECT MAX(seq) FROM events;"

# JSONL の最終行 seq 取得
tail -1 /path/to/events.jsonl | jq '.seq'
```

両者が一致しない場合、JSONL に欠損があります。

### 既存の検知シグナル
`publish_route.py` (line 59) にて、JSONL 追記失敗時に以下の WARNING ログが出力されます：
```
logger.warning("eventbus: JSONL append failed (event still committed): %s", exc)
```
これは SQLite コミット成功後の JSONL 追記失敗時にのみ出力され、HTTP レスポンスは 200 を返します。この WARNING パスにはメトリクスやアラートが付いていません。

### 推奨される追加対応（本フェーズではドキュメントのみ）

1. **カウンターメトリクス**: 上記 WARNING パスにカウンターメトリクスを追加し、JSONL 追記失敗の発生回数を可視化
2. **オペレータランブック**: SQLite が正（正しいデータを持つ）前提で、欠損した JSONL 行を SQLite から再導出してバックフィルする手順をランブックに記載
   - SQLite は正（`docs/06_eventbus_02_05_failure-behavior-summary.md` より）
   - 欠損 `seq` 範囲を特定し、SQLite から該当行を SELECT して JSONL 形式で追記

- `06_eventbus_00_document-guide.md`
- `06_eventbus_01_system-overview.md`
- `06_eventbus_02_01_publish-replay.md`
- `06_eventbus_04_dlq_offsets_and_delivery_semantics.md`
