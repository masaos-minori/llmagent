---
title: "Event Bus: Bind Address and Start Command"
category: eventbus
tags:
  - event-bus
  - bind-address
  - startup
  - security
  - public-bind
  - loopback
  - wildcard
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_05_01_config-env-and-fields.md
  - 06_eventbus_05_07_validation-status.md
source:
  - 06_eventbus_05_01_config-env-and-fields.md
---

# Event Bus: Bind Address and Start Command

## バインドアドレス

EventBus サーバは本番環境では `0.0.0.0` ではなく `127.0.0.1`（ループバック）に
バインドすべきである。`0.0.0.0` にバインドすると EventBus API がローカルネットワークに
公開されてしまい、セキュリティリスクとなる（EventBus の HTTP エンドポイントには
認証レイヤーが存在しないため）。

### アドレスの分類

起動時のガード処理は、設定ロード時にバインドアドレスを検証する。

| カテゴリ | アドレス | オーバーライドなしで許可されるか |
|---|---|---|
| ループバック | `127.0.0.1`, `::1` | Yes |
| プライベート IP | `192.168.x.x`, `10.x.x.x`, `172.16.x.x–172.31.x.x` | Yes |
| ワイルドカード IPv4 | `0.0.0.0` | No — `ValueError` を発生させる |
| ワイルドカード IPv6 | `::` | No — `ValueError` を発生させる |
| ホスト名（非 IP） | 任意のホスト名（例: `example.com`） | No — public として扱われる。`ipaddress.ip_address()` は非 IP 文字列に対して ValueError を発生させ、これが捕捉されて public として扱われる |

#### パブリックバインドのオーバーライド

TOML 設定で `allow_public_bind: true` を設定すると、この検証を回避できる。
リバースプロキシなどによる認証手段がない限り、この設定は**推奨されない**。
拒否された場合のエラーメッセージは以下の通り。

``` text
Event Bus bound to public address {host} without allow_public_bind=true.
The API has no authentication — this is a security risk.
```

リモートアクセスが必要な場合は、認証機能を持つリバースプロキシを使用すること。

### 起動コマンド

```bash
EVENTBUS_CONFIG_PATH=/opt/llm/config/eventbus.toml python -m eventbus.app
```

アプリケーションは、設定内の `host` と `port` の値を使って uvicorn を
プログラム的に起動する。
別の方法として: `uvicorn eventbus.app:app --host 127.0.0.1 --port 8010`（CLI での上書き）。

### TOML の例

```toml
port = 8015
db_path = "/opt/llm/data/eventbus.sqlite"
storage_dir = "/opt/llm/data/eventbus-storage"
offsets_dir = "/opt/llm/data/eventbus-offsets"
deadletter_dir = "/opt/llm/data/eventbus-deadletter"
max_retry = 3
host = "127.0.0.1"
allow_public_bind = false
```

**実装上の補足:** 実際の `config/eventbus.toml` は `host`/`allow_public_bind` を省略しており(デフォルトの`127.0.0.1`/`false`が適用される)、パスも `/opt/llm/db/eventbus.sqlite`・`/opt/llm/storage`・`/opt/llm/offsets`・`/opt/llm/deadletter` を使用している。上記は設定可能なキーを網羅するための例示であり、実配置とは異なる(Explicit in code)。

## Related Documents

- `06_eventbus_05_01_config-env-and-fields.md`
- `06_eventbus_05_07_validation-status.md`

## Keywords

event-bus
bind-address
startup
security
public-bind
loopback
wildcard
