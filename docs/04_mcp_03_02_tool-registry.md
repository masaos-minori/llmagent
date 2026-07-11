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
  - 04_mcp_03_04_tool-call-tracing-and-watchdog.md
  - 04_mcp_03_05_lifecycle-and-new-server.md
  - 04_mcp_07_tool_schema_export_policy.md
source:
  - 04_mcp_03_routing_lifecycle_and_execution.md
---

# Tool Registry: ドリフト検証、ツール追加、キャッシュと並行数制御

ToolRegistry の責任はツールからサーバーへの所有関係とルーティングのみであり、スキーマレジストリではない。`ToolDefinition.description` / `input_schema` は予約済みで未使用である。LLM に見えるツールのスキーマの正規ソースは各サーバーの `TOOL_LIST` ([04_mcp_07_tool_schema_export_policy.md](04_mcp_07_tool_schema_export_policy.md)) である。

### ドリフト検証

3つの比較関数が設定のドリフトを検出する。

| 関数 | 比較対象 | 呼び出しタイミング |
|---|---|---|
| `validate_routing_against_config()` | config の `tool_names` 対 レジストリ | 起動時（`repl_health.py` の `check_routing_drift()`） |
| `validate_routing_against_live()` | ライブの `/v1/tools` 対 レジストリ | 起動時（`repl_health.py` の `check_routing_drift_vs_live()`） |
| `validate_all_routing()` | 上記両方の組み合わせ | まだ組み込まれていない（将来対応） |

> **起動時検証のセマンティクス** — 上記の `validate_routing_against_live()` および
> `validate_all_routing()` 関数は、ライブの `/v1/tools` を内部ルーティングレジストリと比較する。
> これらは `repl_health.py` のツール定義チェックとは異なる。ツール定義チェックは、
> （`agent.toml` からの）設定済み `tool_definitions` をライブの `/v1/tools` と比較するものである。
> `tool_definitions_strict` の起動失敗時の挙動については、
> [04_mcp_06 §Startup Validation Behavior](04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md#startup-validation-behavior-tool_definitions_strict) を参照。

ドリフト警告はエージェント起動時に表示される。

```
WARNING Routing drift [file_read]: [file_read] tool 'read_multiple_files' in registry but not in config. Update file_read_mcp_server.toml [mcp_servers.file_read] tool_names or the registry to resolve.
```

### 新しいツールの追加

| ステップ | アクション | 必須か |
|---|---|---|
| 1 | `shared/tool_constants.py` の適切な frozenset にツール名を追加する | **[必須]** |
| 2 | レジストリはインポート時にこれらの frozenset から自動構築される — レジストリの手動編集は不要 | （自動） |
| 3 | 所有する MCP サーバー（`mcp/<name>/server.py`）に `dispatch()` ハンドラーを実装する | **[必須]** |
| 4 | `/v1/tools` エンドポイントでツールを公開する（`server_key` フィールドを含むツール定義を返す） | **[推奨]** — `check_routing_drift_vs_live()` による起動時ドリフト検出を可能にする |
| 5 | `config/tools_definitions.toml` に LLM スキーマを追加する（OpenAI function-calling 形式） | **[必須]** — ツールを LLM に見せる場合 |
| 6 | 新ツール用に `config/agent.toml` に `tool_safety_tiers` エントリを追加する | **[必須]** — 全てのツールは安全性ティアを宣言しなければならない |
| 7 | `config/<key>_mcp_server.toml` の `[mcp_servers.<key>]` セクションの `tool_names` にツール名を追加する | **[任意]** — 起動時ドリフト検証のみを可能にする; ルーティングには不要 |

**推奨手順**: ToolRegistry の frozenset に追加する（ステップ1）+ `/v1/tools` エンドポイントで公開する（ステップ4）。config の `tool_names`（ステップ7）はルーティングの入力ではない; あくまでドリフト検証用のメタデータである。未知のツールは即時失敗する — フォールバックは存在しない。`/v1/tools` でツールを公開することで、`check_routing_drift_vs_live()` による起動時ドリフト検出が可能になる; ルーティングには影響しない。

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
_SIDE_EFFECT_TOOLS = WRITE_TOOLS | DELETE_TOOLS | frozenset({"shell_run"})
is_side_effect(tool_name: str) -> bool
```

`execute_all_tool_calls()` が副作用を持つツールを1つでも検出した場合、`serial_tool_calls`
の設定に関わらず、そのラウンドの全ての呼び出し（副作用のないツールを含む）を直列化する。

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_03_01_dispatch-and-routing.md`
- `04_mcp_03_03_transport-and-health.md`
- `04_mcp_03_04_tool-call-tracing-and-watchdog.md`
- `04_mcp_03_05_lifecycle-and-new-server.md`
- `04_mcp_07_tool_schema_export_policy.md`

## Keywords

mcp
routing
ToolRegistry
tool cache
concurrency limits
side effect detection
routing drift
