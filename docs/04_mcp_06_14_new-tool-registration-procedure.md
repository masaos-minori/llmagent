---
title: "New Tool Registration Procedure"
category: mcp
tags:
  - mcp
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_02_configuration-file-inventory.md
source:
  - 04_mcp_06_02_configuration-file-inventory.md
---

# New Tool Registration Procedure

## 新規ツール登録手順

### /v1/tools Requirements

Before registering a new tool, ensure your MCP server responds to `/v1/tools` requests with the correct format. See [endpoints-and-transport.md](./04_mcp_02_01_endpoints-and-transport.md) for the complete field specification.

#### Required fields

- `name`: Unique tool identifier
- `description`: Human-readable description of the tool
- `inputSchema`: JSON Schema defining the tool's input parameters
- `is_write`: Whether the tool performs write operations (schema-2.0 contract)
- `requires_serial`: Whether the tool requires serialized execution (schema-2.0 contract)
- `resource_scope_kind`: Scope-kind prefix used for conflict detection, e.g. `"filesystem"`, `"git_repo"`, or `""` for unscoped (schema-2.0 contract)
- `resource_scope_keys`: Argument-dict keys whose values are resolved into the call's actual scope strings (schema-2.0 contract; each key must exist in `inputSchema.properties`)

These four schema-2.0 fields are validated by `shared/resource_scope.py::validate_tool_schema_v2()`
and enforced by `agent/services/mcp_tool_discovery.py::McpToolDiscoveryService`. A tool entry
missing any of them, or failing validation, is rejected and excluded from the built
`RuntimeToolRegistry` — it is never silently defaulted.

#### Optional fields

- `status`: Tool status (e.g., "available", "degraded")
- `resource_scope`: legacy singular scope field; type-checked only if present, not required
- `enabled`: Whether the tool is enabled for LLM use
- `capabilities`: Tool capabilities object
- `server_key`: Identifier for the MCP server providing the tool
- `config_dependent`: Whether the tool depends on configuration
- `disabled_reason`: Reason why the tool is disabled (if applicable)

#### Deferred fields

The following fields are deferred and may not be supported yet:

- `disabled_code`: Structured error code for disabled tools (deferred)

**既存**のMCPサーバーに新しいツールを追加する場合:

| 手順 | 操作 | 必須か |
|---|---|---|
| 1 | `shared/tool_constants.py`内の該当するfrozensetにツール名を追加する(例: `READ_TOOLS`、`WRITE_TOOLS`、または新しい`<SERVER>_TOOLS` frozensetを作成して`get_all_mcp_tool_names()`に追加) | **[必須]** |
| 2 | レジストリはインポート時にこれらのfrozensetから自動的に構築される — レジストリの手動編集は不要 | (自動) |
| 3 | 所有元のMCPサーバー(`scripts/mcp_servers/<name>/server.py`)に`dispatch()`ハンドラを実装する | **[必須]** |
| 4 | `/v1/tools`エンドポイントでツールを公開する(`server_key`フィールドを含むツール定義を返す) | **[推奨]** — 起動時のドリフト検証を有効化するが、ルーティングには影響しない |
| 5 | `config/agent.toml`の`[[tool_definitions]]`にLLMスキーマを追加する(OpenAIのfunction-calling形式) | **[必須]** — LLMにツールを見せる場合 |
| 6 | 新しいツールについて`config/agent.toml`に`tool_safety_tiers`のエントリを追加する | **[必須]** — すべてのツールは安全性ティアを宣言する必要がある |
| 7 | `config/<key>_mcp_server.toml`の`[mcp_servers.<key>]`セクションの`tool_names`にツール名を追加する | **[任意]** — 起動時のドリフト検証のみを有効化する;ルーティングには不要 |

**注記**: すべてのツールはToolRegistryに明示的に登録する必要がある。プレフィックスベースのルーティングは存在しない。

### 検証

登録完了後:

```bash
uv run pytest tests/test_tool_constants.py tests/test_route_resolver.py -v
```

期待される結果: すべてのルーティングテストがパスする。`tool_definitions_strict = true`の場合、エージェントを再起動し、起動ログに未マッピングの警告なしで`"Routing: N/N tools mapped"`が表示されることを確認する。

---

## Metadata update paths

`/v1/tools` is now the single source of tool metadata for both runtime availability and DAG
scheduling:

- **LLM visibility / routing**: `RuntimeToolRegistry` (built by `McpToolDiscoveryService` from
  live `/v1/tools` discovery) is the sole routing authority.
- **DAG scheduling**: `agent/tool_runner.py::_execute_with_dag()` builds a per-call `ToolSpec`
  via `RuntimeToolRegistry.tool_spec_for_call()`, which reads the same tool's `is_write`,
  `requires_serial`, `resource_scope_kind`, and `resource_scope_keys` declared in `/v1/tools`.

Updating a tool's `/v1/tools` declaration (its `TOOL_LIST` entry in the owning MCP server)
therefore changes both what the LLM sees/routes to and how the tool is scheduled in the DAG —
there is no separate `config/agent.toml`-driven scheduling metadata path. `config/agent.toml`'s
`[[tool_definitions]]` only supplies the LLM-facing function-calling schema (name, description,
parameters) and carries no scheduling metadata.

See [dispatch-and-routing.md](./04_mcp_03_01_dispatch-and-routing.md#data-source-for-dag-scheduling) for details.

---


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
