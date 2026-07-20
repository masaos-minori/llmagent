---
title: "HttpTransport, McpServerHealthRegistry, and Tracing Correlation Keys (Part 2)"
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
  - 04_mcp_03_03_transport-and-health-part1.md
---

# HttpTransport、McpServerHealthRegistry、追跡の相関キー(Part 2)

## エンドツーエンドのツール呼び出し追跡

### End-to-end tool call tracing

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

``` text
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
- `04_mcp_03_03_transport-and-health-part1.md`
- `04_mcp_03_04_tool-call-tracing-and-watchdog.md`
- `04_mcp_03_05_lifecycle-and-new-server.md`

## Keywords

mcp
correlation keys
tool call tracing
end-to-end tracing
