---
title: "Tool Registry: Drift Verification, Adding Tools, Cache and Concurrency"
category: mcp
tags:
  - mcp
  - routing
  - tool-registry
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_03_01_dispatch-and-routing.md
  - 04_mcp_03_03_transport-and-health.md
  - 04_mcp_03_03_transport-and-health.md
  - 04_mcp_03_04_tool-call-tracing-and-watchdog.md
  - 04_mcp_03_05_lifecycle-and-new-server.md
  - 04_mcp_07_tool_schema_export_policy.md
---

# Tool Registry: ドリフト検証、ツール追加、キャッシュと並行数制御

ToolRegistry の責任はツールからサーバーへの所有関係の管理（ドリフト検出用のシードデータ）のみであり、スキーマレジストリではない。実行時のルーティングは `RuntimeToolRegistry` が唯一の権威であり、ToolRegistry はルーティング判断には使われない（詳細は本ドキュメント末尾「`RuntimeToolRegistry` とライブ検出」節を参照）。`ToolDefinition.description` / `input_schema` は予約済みで未使用である。LLM に見えるツールのスキーマの正規ソースは各サーバーの `TOOL_LIST` ([04_mcp_07_tool_schema_export_policy.md](04_mcp_07_tool_schema_export_policy.md)) である。

## ドリフト検証

### Drift validation

3つの比較関数が設定のドリフトを検出する。

| 関数 | 比較対象 | 呼び出しタイミング |
|---|---|---|
| `validate_routing_against_config()` | config の `tool_names` 対 レジストリ | 起動時（`McpToolDiscoveryService` のドリフト検証） |
| `validate_routing_against_live()` | ライブの `/v1/tools` 対 レジストリ | 起動時（`McpToolDiscoveryService` のドリフト検証） |
| `validate_all_routing()` | 上記両方の組み合わせ | まだ組み込まれていない（将来対応） |

> **起動時検証のセマンティクス** — 上記の `validate_routing_against_live()` および
> `validate_all_routing()` 関数は、ライブの `/v1/tools` を内部ルーティングレジストリと比較する。
> これらは `McpToolDiscoveryService` のツール定義チェックとは異なる。ツール定義チェックは、
> （`agent.toml` からの）設定済み `tool_definitions` をライブの `/v1/tools` と比較するものである。
> `tool_definitions_strict` の起動失敗時の挙動については、
> [04_mcp_06 §Startup Validation Behavior](04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md#startup-validation-behavior-tool_definitions_strict) を参照。

ドリフト警告はエージェント起動時に表示される。

``` text
WARNING Routing drift [file_read]: [file_read] tool 'read_multiple_files' in registry but not in config. Update file_read_mcp_server.toml [mcp_servers.file_read] tool_names or the registry to resolve.
```

### 新しいツールの追加
詳細な手順は [Adding a new tool](docs/04_mcp_03_05_lifecycle-and-new-server.md#adding-a-new-tool) を参照してください。なお、 の  はルーティングの入力ではなく、あくまでドリフト検証用のメタデータです.


### 検証

登録完了後:

```bash
uv run pytest tests/test_tool_constants.py tests/test_route_resolver.py -v
```

期待結果: 全てのルーティングテストがパスすること。`tool_definitions_strict = true` の場合、エージェントを再起動し、起動ログに `"Routing: N/N tools mapped"` が表示され、未マッピングの警告がないことを確認する。

### 主要 API

```python
from shared.tool_registry import get_registry, validate_all_routing

registry = get_registry()
server_key = registry.get_server_for_tool("read_text_file")  # → "file_read"
tool_names = registry.get_tool_names("file_read")  # → ["read_text_file", ...]
all_tools = registry.get_all_tool_names()  # → frozenset of all tool names
mismatches = validate_all_routing(server_configs, live_tool_lists)  # → dict[str, list[str]]
```

```python
executor = ToolExecutor(
    http=httpx.AsyncClient(...),
    cache_ttl=300.0,
    server_configs=server_configs,
    cache_max_size=200,
    concurrency_limits={"file_write": 1},
    lifecycle=lifecycle_router,
)
result = await executor.execute("read_text_file", {"path": "/opt/llm/..."})
# result: ToolCallResult(output, is_error, request_id, server_key)
```

### キャッシュの挙動

- `is_error=False` の結果のみキャッシュする
- キャッシュキー: `"tool_name:args_json"`（プレーンな文字列; MD5 ではない）
- エントリは `cache_ttl` 秒後に失効する
- `cache_max_size > 0` の場合は LRU により削除される（`0` = 無制限）
- キャッシュヒット時: `request_id=""`（ライブリクエストは行われない）
- 統計: `stat_cache_hits: int`

### 並行数制限

`concurrency_limits={"server_key": N}` は、サーバーごとの同時呼び出しを N 件に制限する。
遅延生成される `asyncio.Semaphore` として実装されている。未知のキーの場合 → warning ログのみ出力。

### 副作用検出

```python
_SIDE_EFFECT_TOOLS = (
    WRITE_TOOLS | DELETE_TOOLS | frozenset({"shell_run"})
    | GIT_WRITE_TOOLS | GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS
    | CICD_WRITE_TOOLS | RAG_WRITE_TOOLS | MDQ_WRITE_TOOLS
)
is_side_effect(tool_name: str) -> bool
```

`is_side_effect()`/`_SIDE_EFFECT_TOOLS`（`shared/tool_executor_helpers.py`）は現在
`shared/tool_executor.py` の TTL キャッシュのバイパス判定にのみ使われる。バッチ実行の
並列/直列判定は、唯一の実行パスである `agent/tool_runner.py::_execute_with_dag()` が
`agent/tool_scheduler.py::build_execution_groups()` に委譲して行い、
`PreparedToolCall.spec.is_write`（`agent/tool_preparation.py::prepare_tool_calls()`が
承認フェーズより前に`RuntimeToolRegistry`経由で解決済み）を参照する。未登録ツールや
`RuntimeToolRegistry`未接続の呼び出しは準備フェーズでフェイルクローズドに却下され、
スケジューリング・実行のいずれにも到達しない（「保守的に副作用ありとして扱う」フォールバックは
廃止された）。`serial_tool_calls`は別の実行エンジンへの分岐ではなく、`build_execution_groups()`への
`force_serial`入力としてスケジューラに渡され、`True`の場合はフェーズ構築/コンフリクトグラフ構築を
バイパスして呼び出し順に1件ずつの単独シリアルフェーズを強制する。

### 安全性ティア検証

- `check_tool_safety_tiers()`: `tool_safety_tiers` に未宣言のレジストリ登録済みツールを警告する。`agent/repl_health.py` の起動時チェックから呼び出される（Explicit in code）。
- `check_unknown_tool_safety_tiers()`: `tool_safety_tiers` のキーがレジストリ未登録（例: 個別ツール名ではなくサーバーキーを誤って指定）の場合に検出する。`shared/production_config_validator.py` から呼び出される（Explicit in code）。
- 両関数とも `tool_safety_tiers` が空/未設定の場合は空リストを返す（チェックをスキップする）。

### 実装上の補足 (Current behavior): tool_cache.py と ToolSpec

- `shared/tool_cache.py` の `ToolResultCache`（LRU + TTL）は現在 `ToolExecutor` からは使用されていない。`ToolExecutor` は独自の `OrderedDict` ベースのキャッシュ（本ドキュメント「キャッシュの挙動」節）を持ち、stampede protection（inflight future 共有）と密結合しているため、代わりに使われている。`ToolResultCache` は非推奨ではなく、stampede protection を必要としない将来の利用者向けのスタンドアロンユーティリティとして残されている。（Explicit in code: `shared/tool_cache.py` モジュール docstring）
- `shared/tool_spec.py` の `ToolSpec`（frozen dataclass）は、承認済みツール呼び出し1件分の実行メタデータ（`call_id`, `name`, `args`, `resource_scopes`（kind接頭辞付きスコープ文字列のタプル）, `requires_serial`, `is_write`）を保持する。`agent/tool_runner.py::_execute_with_dag()` が呼び出しごとに `RuntimeToolRegistry.tool_spec_for_call(call_id, name, args)`（内部で `shared/resource_scope.py::resolve_resource_scopes()` を呼び出し `resource_scopes` を解決する）経由で構築し、call_id をキーとする `dict[str, ToolSpec]`（`call_specs`）として `agent/tool_scheduler.py::build_execution_groups()` に渡され、単一の `ExecutionPlan`（`batches`/`ScheduledGroup`/`SerializationEvent`）として並列/直列判定に使われる。（Explicit in code）

### `RuntimeToolRegistry` とライブ検出（実装済み）

`shared/runtime_tool.py`（`RuntimeTool`, `build_runtime_tool()`）と `shared/runtime_tool_registry.py`（`RuntimeToolRegistry`）は、本ドキュメントが説明する既存の `shared.tool_registry.ToolRegistry` とは別の、追加的なモジュールである。`agent/services/mcp_tool_discovery.py` の `McpToolDiscoveryService`（`async def discover_all() -> DiscoveryResult`）は、各 HTTP トランスポート MCP サーバーの `/v1/tools` をライブに取得し、レスポンス形状を検証する。`name`/`description`/`inputSchema` に加え、`is_write`/`requires_serial`/`resource_scope_kind`/`resource_scope_keys` の4フィールドはスキーマ2.0契約として**必須**であり（`shared/resource_scope.py::validate_tool_schema_v2()` で型・既知kind・`resource_scope_keys`が`inputSchema.properties`に存在することまで検証）、欠落または検証失敗した個別ツールはレジストリから除外される（サイレントなデフォルト適用はしない）。`status`/`resource_scope`（レガシーの単数形）/`enabled`は存在する場合のみ型検証する。`build_runtime_tool()` 経由で `RuntimeTool` に正規化し、サーバー間でツール名が重複した場合は当該ツールをレジストリから除外した上で、`security_profile`（production/local）や `strict` 設定に関わらず常に `FATAL` の `StartupCheckOutcome` を返す（`_dedupe_and_build()` に明示的に実装された挙動。起動パイプラインは FATAL を `pipeline.add_fatal()` に渡すため起動が中断される）。

**[Explicit in code]** `McpToolDiscoveryService` は `startup.py` から呼び出される。`ToolExecutor.set_runtime_registry(runtime_reg)` により RuntimeToolRegistry が接続される。`ToolRouteResolver.resolve()` は RuntimeToolRegistry のみを参照して解決する。ToolRegistry はルーティング判断には一切使われない — `tool_constants.py` frozenset のドリフト検出用データとしてのみ機能する（本ドキュメント冒頭の説明を参照）。

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_03_01_dispatch-and-routing.md`
- `04_mcp_03_03_transport-and-health.md`
- `04_mcp_03_03_transport-and-health.md`
- `04_mcp_03_04_tool-call-tracing-and-watchdog.md`
- `04_mcp_03_05_lifecycle-and-new-server.md`
- `04_mcp_07_tool_schema_export_policy.md`

## Keywords

mcp
routing
ToolRegistry
tool cache
ToolResultCache
ToolSpec
concurrency limits
side effect detection
routing drift
tool safety tiers
RuntimeToolRegistry
McpToolDiscoveryService
