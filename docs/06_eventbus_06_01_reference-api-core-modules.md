---
title: "Event Bus: Reference API — Core Modules"
category: eventbus
tags:
  - event-bus
  - api-reference
  - core-modules
  - app-py
  - config-py
  - db-py
  - dlq-py
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_06_02_reference-api-route-handlers.md
  - 06_eventbus_06_03_reference-api-broker-and-offsets.md
source:
  - 06_eventbus_06_01_reference-api-core-modules.md
---

# Event Bus: Reference API — Core Modules

## scripts/eventbus/app.py

モジュールレベル変数（`db`、`broker`、`config`、`envelope_schema`）は、FastAPI の `lifespan` コンテキストマネージャ内で `app.state` に設定される。`app.py` 自体には、CLI エントリポイント（private）以外のルートロジックやヘルパー関数は定義されていない。ルートハンドラは専用の `*_route.py` モジュールに存在する（`06_eventbus_06_02_reference-api-route-handlers.md` を参照）。JSONL アーカイブへの追記（publish 時）とその `OSError` ハンドリングは、`app.py` ではなく `publish_route.py::publish()` にインラインで実装されている。

---

## scripts/eventbus/config.py

```python
class EventBusConfig:
    port: int
    db_path: str
    storage_dir: str
    offsets_dir: str
    deadletter_dir: str
    max_retry: int
    host: str = "127.0.0.1"  # HTTP listen address; validated at startup
    allow_public_bind: bool = False  # Override: allow binding to public/wildcard addresses
```

**注記 (2026-07-10)**: `poll_interval_ms` と `offset_checkpoint_interval` は削除された。TOML ファイルにいずれかのキーが存在する場合、`load_config()` は `ValueError` を発生させる。

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `get_config_path` | `() -> str` | `EVENTBUS_CONFIG_PATH` 環境変数、またはデフォルト値を返す |
| `get_schema_path` | `() -> str` | `EVENTBUS_SCHEMA_PATH` 環境変数、またはデフォルト値を返す |
| `load_config` | `(path: Path \| str \| None) -> EventBusConfig` | TOML 設定を読み込む。path が None の場合は `get_config_path()` を使用する |

### 内部関数

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `_is_public_host` | `(host: str) -> bool` | host がワイルドカード(`0.0.0.0`、`::`)である場合、または IP アドレスとして解析できない(ホスト名の)場合に True を返す。例外は発生させない |

---

### scripts/eventbus/db.py

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `open_db` | `(db_path: str) -> sqlite3.Connection` | WAL、外部キー、スキーマ初期化を有効にして SQLite を開く。エラー時はログを出力して再送出する |

### DB スキーマ

DDL は `scripts/eventbus/schema.sql` で定義されている。`events` テーブルには以下のカラムがある。

| カラム | 型 | 制約 | 説明 |
|---|---|---|---|
| `seq` | INTEGER | PRIMARY KEY AUTOINCREMENT | 自動増分シーケンス番号 |
| `event_id` | TEXT | NOT NULL UNIQUE | クライアントが指定する UUID。重複を防止する |
| `topic` | TEXT | NOT NULL | イベントトピック文字列(1〜255文字) |
| `payload` | TEXT | NOT NULL | イベントペイロードをシリアライズした JSON 文字列 |
| `producer` | TEXT | NOT NULL | プロデューサ識別子文字列(1〜255文字) |
| `published_at` | TEXT | NOT NULL | イベント publish 時の ISO-8601 タイムスタンプ |
| `acked_at` | TEXT | — | ack 時に設定される(冪等) |
| `delivery_failure_count` | INTEGER | NOT NULL DEFAULT 0 | nack 時にインクリメントされる。`>= max_retry` で DLQ への promotion が発生する |
| `dlq_requeue_count` | INTEGER | NOT NULL DEFAULT 0 | DLQ requeue 時にインクリメントされる |
| `dlq_at` | TEXT | — | イベントが DLQ に promotion された時に設定される |

インデックス: `idx_events_topic` (topic)、`idx_events_seq` (seq)、`idx_events_dlq_at` (dlq_at)、`idx_events_dlq_seq` (dlq_at, seq)

---

## scripts/eventbus/dlq.py

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `sweep_orphans` | `(db, deadletter_dir, max_retry) -> int` | `max_retry` に達したがインラインで promotion されなかったイベントに対する、バックグラウンドの sweep ループ(`app.py` から呼び出される)。promotion した件数を返す(通常運用では 0) |
| `promote_single` | `(db, deadletter_dir, event_id) -> bool` | nack しきい値に達した際に1件のイベントを即座に promotion する(インラインパス、`ack_route.py` から呼び出される)。DB 行を更新する前に DLQ の JSON ファイルを書き込むため、書き込み失敗時はイベントが live のまま残る。すでに DLQ 内にある場合、または見つからない場合は `False` を返す |

**注記**: このモジュールには `promote_to_dlq()` も存在し、`sweep_orphans()` とほぼ同一のロジックを持つが、`scripts/eventbus/` 内のどこからも呼び出されていない。デッドコードと見られる。

---

## scripts/eventbus/route_helpers.py

ルートハンドラの共通ヘルパー関数をまとめたモジュール。各ルートの重複コードを排除するために導入された。

#### HTTP リクエストヘルパー

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `get_db` | `(request: Request) -> Any` | `request.app.state.db` を取得。None の場合は RuntimeError |
| `get_config` | `(request: Request) -> Any` | `request.app.state.config` を取得。None の場合は RuntimeError |
| `get_broker` | `(request: Request) -> "EventBroker"` | `request.app.state.broker` を取得。None の場合は RuntimeError |

#### アプリケーションステートヘルパー（Request なし）

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `app_get_db` | `(app: Any) -> Any` | `app.state.db` を取得。None の場合は RuntimeError |
| `app_get_config` | `(app: Any) -> Any` | `app.state.config` を取得。None の場合は RuntimeError |
| `app_get_broker` | `(app: Any) -> "EventBroker"` | `app.state.broker` を取得。None の場合は RuntimeError |

#### DB ロック実行ヘルパー

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `run_with_db_lock` | `(func: Any) -> Any` | `asyncio.to_thread` で `get_db_lock()` コンテキスト内で関数を実行 |

#### イベント行ヘルパー

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `_row_to_dict` | `(row: Any) -> dict[str, Any]` | SQLite Row を辞書に変換。`orjson.loads(row["payload"])` でペイロードをデコード |

#### エラーメッセージ定数

| 定数 | 値 |
|---|---|
| `ERR_EVENT_NOT_FOUND` | `"event not found"` |
| `ERR_EVENT_ID_REQUIRED` | `"event_id is required"` |
| `ERR_EVENT_NOT_IN_DLQ` | `"event is not in DLQ"` |

### Related Documents

- `06_eventbus_06_02_reference-api-route-handlers.md`
- `06_eventbus_06_03_reference-api-broker-and-offsets.md`

### Keywords

event-bus
api-reference
core-modules
app-py
config-py
db-py
dlq-py
route-helpers
