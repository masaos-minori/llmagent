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
| `port` | int | — | HTTPリスンポート |
| `db_path` | str | — | SQLiteデータベースファイルのパス |
| `storage_dir` | str | — | JSONLイベントアーカイブのディレクトリ |
| `offsets_dir` | str | — | コンシューマーオフセットファイルのディレクトリ |
| `deadletter_dir` | str | — | デッドレターキューJSONLのディレクトリ |
| `max_retry` | int | — | DLQ昇格前の再試行閾値 |
| `host` | str | `127.0.0.1` | HTTPリスンアドレス（下記のBind Addressセクションを参照） |
| `allow_public_bind` | bool | `false` | オーバーライド: パブリック/ワイルドカードアドレスへのバインドを許可する（セキュリティリスクあり、認証なし） |

## Related Documents

- `06_eventbus_05_02_bind-address-and-start.md`
- `06_eventbus_05_03_health-endpoint-semantics.md`

## Keywords

event-bus
configuration
environment-variables
config-fields
toml
