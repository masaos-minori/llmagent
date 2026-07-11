---
title: "Shared Runtime and Execution - LLM and MCP Clients (Part 1)"
category: shared
tags:
  - shared
  - runtime
  - llm-client
  - mcp-server-config
  - execution-flow
related:
  - 90_shared_00_document-guide.md
  - 90_shared_03_01_runtime_and_execution-config-and-logging.md
  - 90_shared_03_02_runtime_and_execution-plugin-and-tool-runtime.md
  - 90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md
source:
  - 90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md
---

# Shared Runtime and Execution Infrastructure

- Overview → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)

## 9. `ToolExecutor` and Surrounding Concepts (`shared/tool_executor.py`)

**責務:** ツールディスパッチのコアエンジン — ツール→サーバの解決、キャッシュ、同時実行数制限、ヘルスゲーティング、トランスポート通信を担う。

**`ToolCallResult` データクラス(結果の契約):**
```python
@dataclass
class ToolCallResult:
    output: str          # Tool output string (truncated if > MCP_MAX_RESPONSE_BYTES)
    is_error: bool       # True if the tool call failed
    request_id: str      # X-Request-Id from the MCP server response
    server_key: str      # Server key used for routing (e.g. "file_read", "shell")
```

**実行フロー:**
```
ToolExecutor.execute(tool_name, args) -> ToolCallResult
  1. plugin_registry.get_tool(tool_name) → プラグインが優先される
  2. ToolRouteResolver.resolve(tool_name) → server_key
  3. McpServerHealthRegistry.is_unavailable(server_key) → UNAVAILABLEならブロック
  4. TTL + LRU キャッシュチェック(is_error=Falseの結果のみ)
  5. ツール呼び出しの実行(tool_name, args)
       → セマフォ取得(server_key に concurrency_limits が設定されている場合)
       → HttpTransport.call()
  6. キャッシュ保存(is_error=Falseのみ;TTLは設定から取得)
  7. ToolCallResult を返す
```

**キャッシュの挙動:**
- `is_error=False` の結果のみキャッシュされる
- TTL + LRU退避(`tool_cache_ttl_sec`、`tool_cache_maxsize` で設定可能)
- キャッシュキー: `(tool_name, serialized_args)`
- 副作用のあるツールはキャッシュを完全にバイパスする

**ヘルスゲート:**
- `McpServerHealthRegistry.is_unavailable(server_key)` はUNAVAILABLE時にディスパッチをブロックする
- 連続したトランスポート失敗 → DEGRADED → UNAVAILABLE の状態遷移
- 成功レスポンス → HEALTHYにリセット

**同時実行の挙動:**
- `concurrency_limits` 辞書は server_key → 最大同時呼び出し数 をマッピングする
- ツール実行層でのセマフォベースのスロットリング
- `execute_all_tool_calls()` が副作用のあるツールを検出すると、そのラウンドの全呼び出しが直列化される

**副作用の検出:**
```python
_SIDE_EFFECT_TOOLS = WRITE_TOOLS | DELETE_TOOLS | frozenset({"shell_run"})
is_side_effect(tool_name: str) -> bool
```

`execute_all_tool_calls()` が副作用のあるツールを検出すると、`serial_tool_calls` の設定に関わらず
そのラウンドの全呼び出しが直列化される。

**ルーティング:** 2段カスケード — (1) `/v1/tools` によるライブ検出、(2) `tool_constants.py` の `ToolRegistry`。未知のツールは即座に `ValueError` で失敗する。ルーティングの詳細は [04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md) を参照。

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_03_01_runtime_and_execution-config-and-logging.md`
- `90_shared_03_02_runtime_and_execution-plugin-and-tool-runtime.md`
- `90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md`
- `90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part2.md`

## Keywords

LLMClient
McpServerConfig
McpServerHealthRegistry
execution flow summary
import boundaries
