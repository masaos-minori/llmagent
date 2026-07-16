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

**`ToolCallResult` データクラス(結果の契約、`shared/transport_dto.py`、frozen dataclass):**
```python
@dataclass(frozen=True)
class ToolCallResult:
    output: str          # Tool output string (truncated if > MCP_MAX_RESPONSE_BYTES)
    is_error: bool       # True if the tool call failed
    request_id: str      # X-Request-Id from the MCP server response; "" for plugin/cache
    server_key: str      # Server key used for routing (e.g. "file_read", "shell"); "" for plugin tools
    source: str = ""      # "mcp" | "plugin" | "" (cache/error paths)
    error_type: str = ""  # "transport" | "tool" | "plugin_contract" | "" (empty on success)
```

**訂正 (Explicit in code):** 旧記述は `source` / `error_type` フィールドを欠いていた。`error_type` はエラーの分類(トランスポート層/ツール層/プラグイン契約違反)を示し、ヘルスゲートやエラーカウンタ集計(`get_error_counters()`)で参照される。

**実行フロー:**
```
ToolExecutor.execute(tool_name, args) -> ToolCallResult
  1. PluginToolInvoker.try_execute(tool_name, args) → プラグイン該当時はここで確定し、以降(キャッシュ/ルーティング)はバイパス
  2. TTL + LRU キャッシュチェック(is_error=Falseの結果のみ;キャッシュミス時のみ以降へ進む)
  3. stampede protection(_inflight）→ 同一キーの同時実行はFutureを共有
  4. ToolRouteResolver.resolve(tool_name) → server_key
  5. startup_mode=none ゲート → 無効化されたサーバは即エラー
  6. McpServerHealthRegistry.is_unavailable(server_key) → UNAVAILABLEならブロック(HALF_OPENは1回だけ許可)
  7. lifecycle.ensure_ready(server_key)(設定されている場合)
  8. ツール呼び出しの実行(tool_name, args)
       → セマフォ取得(server_key に concurrency_limits が設定されている場合)
       → HttpTransport.call()
  9. キャッシュ保存(is_error=Falseのみ;TTLは設定から取得)
  10. ToolCallResult を返す
```

**訂正 (Explicit in code):** 旧記述はルーティング解決(2)をキャッシュチェック(4)より前に置いていたが、実装では `execute()` → `_execute_with_cache()` でキャッシュキー(`tool_name` と引数のみ)を先に判定し、キャッシュミス時のみ `_execute_with_stampede_protection()` 経由で `_raw_execute()` に入り、その内部でルーティング・startup_modeゲート・ヘルスチェック・lifecycle待機を行う。また `_raw_execute()` が例外を送出した場合、待機中の全同時呼び出しにも同じ例外が伝播する(stampede保護のフェイルセーフ)。

**キャッシュの挙動:**
- `is_error=False` の結果のみキャッシュされる
- TTL + LRU退避(`tool_cache_ttl_sec`、`tool_cache_maxsize` で設定可能)
- キャッシュキー: `(tool_name, serialized_args)`
- 副作用のあるツールはキャッシュを完全にバイパスする

**ヘルスゲート:**
- `McpServerHealthRegistry.is_unavailable(server_key)` はUNAVAILABLE時にディスパッチをブロックする
- 連続したトランスポート失敗 → DEGRADED → UNAVAILABLE の状態遷移(`failure_threshold` 到達でUNAVAILABLE)
- 成功レスポンス → HEALTHYにリセット(失敗カウント・degraded理由もクリア)

**訂正・追記 (Explicit in code, `shared/mcp_health.py`):** `McpServerHealthState` には `HEALTHY` / `DEGRADED` / `UNAVAILABLE` に加えて `HALF_OPEN` と `UNKNOWN` が存在する。`is_unavailable()` は単純なgetterではなく、UNAVAILABLE状態が `half_open_cooldown_sec` を超えて継続すると副作用としてHALF_OPENへ遷移し、その呼び出し限りで1回だけ試行ディスパッチを許可する(サーキットブレーカー的挙動)。HALF_OPEN中に失敗すると即座にUNAVAILABLEへ戻る(`record_failure()` 内で `was_half_open` を判定)。`record_degraded()` はUNAVAILABLE/HALF_OPEN状態を上書きしない(ガード付き)。

**同時実行の挙動:**
- `concurrency_limits` 辞書は server_key → 最大同時呼び出し数 をマッピングする
- ツール実行層でのセマフォベースのスロットリング（`ToolTransportInvoker` のセマフォ初期化処理）
- `execute_all_tool_calls()`(`agent/tool_runner.py`)が副作用のあるツールを検出すると、`serial_tool_calls` の設定に関わらずそのラウンドの全呼び出しが直列化される

**副作用の検出:**
```python
_SIDE_EFFECT_TOOLS = WRITE_TOOLS | DELETE_TOOLS | frozenset({"shell_run"}) | GIT_WRITE_TOOLS | GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS
is_side_effect(tool_name: str) -> bool
```

> **訂正 (Explicit in code):** `_SIDE_EFFECT_TOOLS` / `is_side_effect()` は `shared/tool_executor.py` ではなく `shared/tool_executor_helpers.py` に定義されている。また `execute_all_tool_calls()` と `serial_tool_calls` による直列化判定は `ToolExecutor` 自身のメソッドではなく `agent/tool_runner.py`(agentレイヤー)が呼び出し元であり、`is_side_effect()` の判定結果を用いてラウンド単位で並列/直列を切り替える。`ToolExecutor.execute()` は単一のツール呼び出し単位のAPIであり、ラウンド全体の直列化制御は行わない。集合には旧記述にない `GIT_WRITE_TOOLS` / `GITHUB_WRITE_TOOLS` / `GITHUB_DANGEROUS_TOOLS` も含まれる。

**ルーティング (Explicit in code):** `shared/tool_registry.py` の `ToolRegistry` が唯一のルーティング権威(sole routing authority)。`ToolRouteResolver.resolve()`(`shared/route_resolver.py`)は `ToolRegistry.get_server_for_tool()` のみを参照し、未知のツールは即座に `ValueError` で失敗する。設定ファイルの `tool_names` および `/v1/tools` によるライブ検出は、起動時のドリフト検証(`shared/tool_routing_validation.py`)専用のメタデータであり、実行時のルーティング判断には使われない。旧「2段カスケード」方式(ライブ検出→レジストリの順で解決)は現行コードには存在しない。ルーティングの詳細は [04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md) を参照。

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
ToolRegistry
ToolRouteResolver
HALF_OPEN
tool_executor_helpers
stampede protection
