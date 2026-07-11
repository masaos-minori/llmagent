---
title: "HttpTransport, McpServerHealthRegistry, and Tracing Correlation Keys"
category: mcp
tags:
  - mcp
  - transport
  - health-registry
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_03_01_dispatch-and-routing.md
  - 04_mcp_03_02_tool-registry.md
  - 04_mcp_03_04_tool-call-tracing-and-watchdog.md
  - 04_mcp_03_05_lifecycle-and-new-server.md
source:
  - 04_mcp_03_routing_lifecycle_and_execution.md
---

# HttpTransport、McpServerHealthRegistry、追跡の相関キー

## HttpTransport (`shared/tool_executor.py`)

```python
HttpTransport(http, base_url, server_key, cfg=McpServerConfig)
result = await transport.call("tool_name", {"arg": "val"})
```

- `cfg.auth_token` が空でない場合、`Authorization: Bearer <token>` を追加する
- 全てのトランスポートレベルの障害（タイムアウト、HTTP 非 2xx、不正な形式のレスポンス、リトライ消尽）で `TransportError` を発生させる; `is_error=True` を直接返すことはない
- トランスポートエラーハンドラーが `TransportError` を捕捉し、`ToolCallResult(error_type="transport")` に変換する
- `set_session_id(session_id)` はリクエストごとに `X-Session-Id` ヘッダーを注入する
- **リトライ:** HTTP 429/502/503/504 でリトライを行う。最大3回の試行で、遅延時間は減少していく: 試行0回目は4秒待機、試行1回目は2秒待機、試行2回目は1秒待機した後、最終的な消尽エラーとなる。計算式: 2^(RETRY_MAX - attempt - 1)。これは指数バックオフではない（試行ごとに遅延が減少する）。HealthRegistry に記録されるのは最終結果のみ（成功、または全リトライ消尽後の TransportError）。
- **リトライ不可のエラー:** HTTP タイムアウト（`httpx.TimeoutException`）と、429/502/503/504 以外のステータスコードによる HTTPStatusError は、リトライなしで即時に伝播する。

---

## McpServerHealthRegistry (`shared/mcp_config.py`)

`_build_tool_executor()`（factory.py）内で作成され、`ToolExecutor`（`set_health_registry()` 経由）と
`AppServices.health_registry` の間で共有される、サーバーごとの失敗トラッカー。
両者は同一のオブジェクトを保持するため、`ToolExecutor` によって記録されたヘルス状態は
`AppServices.health_registry` を通じて即座に可視化される。

**状態遷移:**

```
HEALTHY ──(failure × threshold)──→ UNAVAILABLE
   ↑                                    │
   │                            (cooldown 30s elapsed)
   │                                    ↓
   └──(record_success)────────── HALF_OPEN (trial probe)
                                        │
                              (failure)─┘ → UNAVAILABLE (cooldown reset)
```

| 状態 | 条件 |
|---|---|
| `HEALTHY` | 失敗なし、または呼び出し成功後 |
| `DEGRADED` | 失敗回数 < しきい値（デフォルト3） |
| `UNAVAILABLE` | 失敗回数 ≥ しきい値; ディスパッチはブロックされる |
| `HALF_OPEN` | 30秒のクールダウン経過後; 1回の試行ディスパッチが許可される |

| メソッド | 説明 |
|---|---|
| `record_failure(server_key)` | 失敗回数をインクリメント; `HALF_OPEN → UNAVAILABLE`（クールダウンリセット); しきい値到達時 → `UNAVAILABLE` |
| `record_degraded(server_key, reason)` | オプションの理由文字列とともに、状態を `DEGRADED` に設定する; 到達可能だが再起動不可なサーバーに対してウォッチドッグから呼び出される。現在の状態が `UNAVAILABLE` または `HALF_OPEN` の場合は no-op（debug ログのみ記録し、状態・理由は変更しない）— circuit breaker のディスパッチゲーティングとシングルトライアル窓を維持するためのガード |
| `get_degraded_reason(server_key)` | 最後に記録された degraded の理由文字列を返す。設定されていない場合は `None` |
| `record_success(server_key)` | 失敗回数、unavailable タイムスタンプ、degraded の理由をリセット; `HALF_OPEN → HEALTHY` |
| `get_state(server_key)` | 現在の状態; 未知のキーの場合は `HEALTHY` を返す |
| `is_unavailable(server_key)` | `UNAVAILABLE` であり、かつクールダウンがまだ経過していない場合 `True`; 副作用として、クールダウン経過時に `HALF_OPEN` へ遷移する |

**コンストラクタ:** `McpServerHealthRegistry(failure_threshold=3, half_open_cooldown_sec=30.0)`
- `half_open_cooldown_sec`: `UNAVAILABLE` に入ってから試行ディスパッチが許可されるまでの秒数（デフォルト30秒、固定値 — 指数バックオフではない）

---

## エンドツーエンドのツール呼び出し追跡

### 相関キー

| キー | 生成元 | 出現箇所 |
|---|---|---|
| `X-Session-Id` | エージェント（`ctx.session.session_id`） | HTTP リクエストヘッダー; MCP サーバーアクセスログ; エージェント audit ログ |
| `X-Request-Id` | MCP サーバー（リクエストごとの UUID） | HTTP レスポンスヘッダー; MCP サーバーアクセスログ; エージェント audit ログ（`x_request_id`） |
| `server_key` | `McpServerConfig.key` | エージェントルーティングログ; `ToolCallResult.server_key`; health registry; トランスポートエラーカウンター |
| `tool_name` | LLM のツール呼び出し | エージェント audit ログ; MCP サーバーリクエストログ; ツールエラーカウンター |

1つのツール呼び出しを追跡するには、`X-Request-Id`（呼び出しごとに一意）と `X-Session-Id`（セッション全体に及ぶ）を結合する。

---

### 成功パスの例

```
1. Agent: LLM emits tool_use for "read_text_file"
   → tool_runner.execute_one_tool_call(ctx, name="read_text_file", ...)
   → ToolRouteResolver.resolve("read_text_file") → server_key="file_read"

2. Agent → Server (HTTP):
   POST /v1/call_tool
   X-Session-Id: 42
   body: {"name": "read_text_file", "args": {...}}

3. MCP server (file-read-mcp):
   Server log: INFO [42] read_text_file args=... → OK
   Response: X-Request-Id: abc-123, is_error=false, result="..."

4. Agent receives:
   ToolCallResult(output="...", is_error=False, request_id="abc-123", server_key="file_read")

5. Agent audit_tool_exec():
    audit log entry (JSON-lines): {"event":"tool_exec","task_id":"...","tool":"read_text_file","mcp_request_id":"abc-123","is_error":false,"error_type":"","ts":...}

6. Health registry:
   HealthRegistry.record_success("file_read") → state remains HEALTHY
```

---

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_03_01_dispatch-and-routing.md`
- `04_mcp_03_02_tool-registry.md`
- `04_mcp_03_04_tool-call-tracing-and-watchdog.md`
- `04_mcp_03_05_lifecycle-and-new-server.md`

## Keywords

mcp
HttpTransport
McpServerHealthRegistry
health state
retry
correlation keys
tool call tracing
