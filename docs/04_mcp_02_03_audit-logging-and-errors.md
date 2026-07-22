---
title: "MCP Audit Log Format and Common Error Handling"
category: mcp
tags:
  - mcp
  - audit
  - logging
  - errors
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_02_01_endpoints-and-transport.md
  - 04_mcp_02_02_startup-modes-and-health.md
---

# MCP プロトコルとトランスポート: Audit ログとエラー形式

## Audit ログ形式

`POST /v1/call_tool` の各呼び出しは、1件の JSON-lines audit レコードを出力する。

```json
{"event":"mcp_tool_exec","source":"mcp_server","ts":1719500000.0,"session_id":"sess-abc","request_id":"req-uuid","tool":"read_text_file","target":"/workspace/file.txt","outcome":"ok","server_key":"file_read","error_type":""}
```

| フィールド | ソース | 常に存在するか | 欠落/空の場合の値 |
|---|---|---|---|
| `session_id` | `X-Session-Id` リクエストヘッダー | Yes | `"-"` |
| `request_id` | `X-Request-Id`（ミドルウェアが注入する UUID） | Yes | `"-"` |
| `tool` | `req.name`（ツール名） | Yes | — |
| `target` | サーバー固有: リポジトリ slug / コマンド先頭80文字 / クエリ先頭80文字 | Yes | — |
| `outcome` | `"ok"` または `"error"` | Yes | — |
| `detail` | 任意の補足情報 | No | 省略 |
| `server_key` | サーバー識別子（例: `"file_read"`, `"cicd"`, `"mdq"`, `"shell"`, `"github"`） | Yes | `""` |
| `error_type` | トランスポート障害のエラー分類 | Yes | `""` |

**注記:** github-mcp、shell-mcp は共有と両方の audit ログに書き込む。file-delete-mcp のみ専用 audit ログを使用する。ファイル読み込み・書き込み MCP サーバーは audit ログを書かない。github-mcp、shell-mcp の専用 audit ログは ISO8601 タイムスタンプ + op=<operation> + path/repo/command を使用する。これらは X-Session-Id や X-Request-Id の相関フィールドを持たない。ログ間の相関はエージェント側の audit ログを基準として使用する必要がある。

各サーバーのディスパッチハンドラーから呼び出される audit ログ関数によって実装されている。

---

## 共通エラー形式

| エラー種別 | HTTP ステータス | `is_error` |
|---|---|---|
| ツールが見つからない | 200 | `true` |
| ツールのバリデーションエラー | 200 | `true` |
| 認証失敗 | 401 | N/A（トランスポートエラー） |
| サーバーエラー | 500 | N/A（トランスポートエラー） |
| レスポンスの切り詰め | 200 | `false`（コンテンツは提供される） |

HTTP トランスポートエラー（4xx/5xx）は `HttpTransport.call()` によって捕捉され、
`TransportError` 例外が発生する。トランスポートエラーハンドラーはこれを
`ToolCallResult(output=str(e), is_error=True, error_type="transport")` に変換する。

> **注記:** `HttpTransport.call()` はトランスポート障害に対して `is_error=True` を直接返すことはない。
> 代わりに `TransportError` を発生させる。トランスポートエラーハンドラーがこれを捕捉し、
> `ToolCallResult(error_type="transport")` を返す。[04_mcp_03 §HttpTransport](04_mcp_03_03_transport-and-health-part1.md#httptransport) を参照。

### HealthRegistry の更新

- **トランスポート障害**（全リトライ消尽後）: `HealthRegistry.record_failure(server_key)` — 失敗回数をインクリメントし、サーバーを DEGRADED/UNAVAILABLE に遷移させる可能性がある。
- **トランスポート成功**（サーバーからのツールレベルのエラーがある場合も含む）: `HealthRegistry.record_success(server_key)` — 失敗回数を 0 にリセットする。ツールレベルのエラーは `stat_tool_errors` で別途追跡される。
- **キャッシュヒット**: HealthRegistry の更新なし — ライブ呼び出しが行われていないため。
- **プリフライトヘルスチェックによる拒否**: `record_failure()` は呼び出されない — 試行自体が行われていないため。
- **リトライの挙動**: HealthRegistry に記録されるのは最終結果のみ（成功、または全リトライ消尽後の TransportError）。中間のリトライ試行はカウントされない。

### エラー分類表

| エラー種別 | HTTP ステータス | HealthRegistry のアクション | request_id | is_retryable |
|---|---|---|---|---|
| HTTP 4xx（リトライ不可: 401/403/404） | 4xx | `record_failure()` | `""` | No |
| HTTP 5xx（サーバーエラー） | 5xx | `record_failure()` | `""` | Yes（バックオフあり） |
| タイムアウト | N/A | `record_failure()` | `""` | Yes（バックオフあり） |
| 接続拒否 | N/A | `record_failure()` | `""` | No |
| DNS/ネットワークエラー | N/A | `record_failure()` | `""` | No |
| 不正な形式のレスポンス（dict でない、'result' がない） | 200 | `record_failure()` | `""` | No |

全てのトランスポート障害では、リクエストが正常に完了していないため `request_id=""` が設定される。ツールレベルのエラー（HTTP 200 かつ `is_error=True`）はサーバーレスポンスの実際の request_id を使用し、`record_success()` を呼び出す。

---

## dispatch_tool ヘルパー（`mcp_servers/dispatch.py`）

```python
from mcp_servers.dispatch import ToolArgs, dispatch_tool

result = await dispatch_tool(dispatch_table, name, args)
# DispatchResult(output, is_error) を返す
```

- 空文字/空白のみの `name` → `("Tool name must be a non-empty string", True)`
- 未知の `name` → `("Unknown tool: <name>", True)`
- ハンドラーからの `ValueError` → `("Validation error: <e>", True)`
- その他の例外は呼び出し元に伝播する

**Disabled call handling:** When a tool is disabled, the MCP server returns a response with `is_error=True` and includes the concrete reason in the result field. This follows the standard error response format but specifically indicates the tool is disabled rather than encountering a runtime error.

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_02_01_endpoints-and-transport.md`
- `04_mcp_02_02_startup-modes-and-health.md`

## Keywords

mcp
protocol
transport
audit
error
HealthRegistry
TransportError
dispatch_tool
