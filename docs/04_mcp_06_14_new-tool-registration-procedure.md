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

#### Optional fields

- `status`: Tool status (e.g., "available", "degraded")
- `is_write`: Whether the tool performs write operations
- `requires_serial`: Whether the tool requires serialized execution
- `resource_scope`: List of resource scopes the tool can access
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
| 3 | 所有元のMCPサーバー(`mcp_servers/<name>/server.py`)に`dispatch()`ハンドラを実装する | **[必須]** |
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

When updating tool metadata, you must understand that there are two independent update paths:

### Path 1: /v1/tools metadata (runtime availability)

Updating `/v1/tools` response affects:
- What tools are visible to the LLM via `/v1/tools`
- Runtime routing decisions made by `RuntimeToolRegistry`
- LLM visibility (enabled/disabled state)

This path is controlled by the MCP server's `/v1/tools` endpoint implementation.

### Path 2: config/agent.toml metadata (DAG scheduling)

Updating `config/agent.toml` tool definitions affects:
- DAG scheduling metadata (`requires_serial`, `resource_scope`, `is_write`, etc.)
- How tools execute in the DAG context
- Shell-specific serial behavior

This path is controlled by the agent configuration file.

### Important: Independent updates

These two update paths are **independent**. Updating `/v1/tools` metadata alone does not change DAG scheduling behavior. If you need to change both runtime availability AND DAG scheduling metadata, you must update both `/v1/tools` and `config/agent.toml` separately.

See [dispatch-and-routing.md](./04_mcp_03_01_dispatch-and-routing.md#data-source-for-dag-scheduling) for details on the data source distinction.

---


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
