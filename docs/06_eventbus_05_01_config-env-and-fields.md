---
title: "Event Bus: Configuration Fields and Environment Variables"
category: eventbus
tags:
  - event-bus
  - configuration
  - environment-variables
  - config-fields
  - toml
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_05_02_bind-address-and-start.md
  - 06_eventbus_05_03_health-endpoint-semantics.md
source:
  - 06_eventbus_05_01_config-env-and-fields.md
---

# Event Bus: Configuration Fields and Environment Variables

## 設定

Event Busの設定はTOMLファイルから読み込まれる（デフォルト: `/opt/llm/config/eventbus.toml`）。

### 環境変数によるオーバーライド

| 変数 | デフォルト | 用途 |
|---|---|---|
| `EVENTBUS_CONFIG_PATH` | `/opt/llm/config/eventbus.toml` | TOML設定ファイルのパス |
| `EVENTBUS_SCHEMA_PATH` | `/opt/llm/schemas/event_envelope.json` | イベントエンベロープ用のJSON Schema |

### 設定フィールド

#### 有効な設定フィールド

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| `port` | int | — | HTTPリスンポート（1024～65535の範囲外は起動時に `ValueError`） |
| `db_path` | str | — | SQLiteデータベースファイルのパス |
| `storage_dir` | str | — | JSONLイベントアーカイブのディレクトリ |
| `offsets_dir` | str | — | コンシューマーオフセットファイルのディレクトリ |
| `deadletter_dir` | str | — | デッドレターキューJSONLのディレクトリ |
| `max_retry` | int | — | DLQ昇格前の再試行閾値（1未満は起動時に `ValueError`） |
| `host` | str | `127.0.0.1` | HTTPリスンアドレス（下記のBind Addressセクションを参照） |
| `allow_public_bind` | bool | `false` | オーバーライド: パブリック/ワイルドカードアドレスへのバインドを許可する（セキュリティリスクあり、認証なし） |

`port` と `max_retry` の検証は `EventBusConfig.__post_init__()` で行われる（根拠分類: Explicit in code — `scripts/eventbus/config.py`）。

### 廃止済み設定キー

`load_config()` は、設定ファイルに廃止済みキーが残っている場合、起動前にエラーとする。

| キー | 状態 |
|---|---|
| `poll_interval_ms` | 削除済み。設定ファイルに存在すると起動時エラー |
| `offset_checkpoint_interval` | 削除済み（no-opフィールドだった）。設定ファイルに存在すると起動時エラー |

これらのキーが `eventbus.toml` に残っている場合、`load_config()` は `ValueError` を送出し、Event Busは起動しない。エラーメッセージには対象キー名と設定ファイルパスが含まれる（根拠分類: Explicit in code — `scripts/eventbus/config.py` の `_REMOVED_CONFIG_KEYS`）。

## Related Documents

- `06_eventbus_05_02_bind-address-and-start.md`
- `06_eventbus_05_03_health-endpoint-semantics.md`

## Keywords

event-bus
configuration
environment-variables
config-fields
toml
