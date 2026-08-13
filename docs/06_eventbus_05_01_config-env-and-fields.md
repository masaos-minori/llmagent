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

TOMLファイルから読み込まれる（デフォルト: `/opt/llm/config/eventbus.toml`）。

### 環境変数

- `EVENTBUS_CONFIG_PATH` — TOMLファイルパス
- `EVENTBUS_SCHEMA_PATH` — イベントエンベロープJSON Schemaパス

### 設定フィールド

- `port` — HTTPリスンポート（1024～65535外は起動失敗）
- `db_path` — SQLite DBパス
- `storage_dir` — JSONLアーカイブディレクトリ
- `offsets_dir` — コンシューマーオフセットディレクトリ
- `deadletter_dir` — DLQディレクトリ
- `max_retry` — DLQ昇格前再試行閾値（1未満で起動失敗）
- `host` — リスンアドレス（デフォルト: `127.0.0.1`）
- `allow_public_bind` — パブリックバインド許可（デフォルト: false）

`port` / `max_retry` の検証は `EventBusConfig.__post_init__()` で行う。

### 廃止済みキー

`poll_interval_ms` / `offset_checkpoint_interval` が設定ファイルに残っていると起動失敗。

## Related Documents

- `06_eventbus_05_02_bind-address-and-start.md`
- `06_eventbus_05_03_health-endpoint-semantics.md`
