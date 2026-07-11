---
title: "Shared Types and Protocols - Reference"
category: shared
tags:
  - shared
  - types
  - tool-constants
  - call-tool
  - protocol-vs-dataclass
related:
  - 90_shared_00_document-guide.md
  - 90_shared_02_01_types_and_protocols-core-types.md
  - 90_shared_02_02_types_and_protocols-tool-and-execution-dto.md
source:
  - 90_shared_02_01_types_and_protocols-core-types.md
---

# 共有の型とプロトコル

- 概要 → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)

## 9a. `DbConfig` (`db/config.py`)

```python
@dataclass
class DbConfig:
    rag_db_path: str
    session_db_path: str
    workflow_db_path: str = "/opt/llm/db/workflow.sqlite"
    sqlite_vec_so: str = ""       # empty = vec extension not required
    sqlite_timeout: int = 30
    sqlite_busy_timeout_ms: int = 30000
    embedding_dims: int = 384
```

- `__post_init__` で検証される: 親ディレクトリが存在すること、timeout/embedding_dims が 1 以上であること
- `ConfigLoader().load("agent.toml")` 経由で `agent.toml` を読み込む `build_db_config()` によって構築される
- `SQLiteHelper`、`maintenance.py`、およびセッションファクトリのコードで使用される

---

## 10. ツール定数 (`shared/tool_constants.py`)

すべての定数は `frozenset[str]` である。`ToolRegistry` のシードデータとして、また `ToolExecutor` の副作用分類に使用される。

| Constant | Tool names |
|---|---|
| `READ_TOOLS` | `list_directory`, `list_directory_with_sizes`, `directory_tree`, `read_text_file`, `read_media_file`, `read_multiple_files`, `search_files`, `grep_files`, `get_file_info` (9 tools) |
| `WRITE_TOOLS` | `write_file`, `edit_file`, `create_directory`, `move_file` (4 tools) |
| `DELETE_TOOLS` | `delete_file`, `delete_directory` (2 tools) |
| `RAG_TOOLS` | `rag_run_pipeline`, `rag_debug_pipeline` |
| `CICD_TOOLS` | `trigger_workflow`, `get_workflow_runs`, `get_workflow_status`, `get_workflow_logs` |
| `MDQ_TOOLS` | `search_docs`, `get_chunk`, `outline`, `index_paths`, `refresh_index`, `stats`, `grep_docs`, `fts_consistency_check`, `fts_rebuild` (9 tools) |
| `GIT_TOOLS` | `git_status`, `git_log`, `git_diff`, `git_branch`, `git_show`, `git_add`, `git_commit`, `git_checkout`, `git_pull`, `git_push` |
| `SHELL_TOOLS` | `shell_run` |
| `WEB_SEARCH_TOOLS` | `search_web` |

`shared/tool_executor.py` および `agent/tool_runner.py` からも参照される。

---

## 11. `CallToolRequest` / `CallToolResponse` リファレンス

`mcp/models.py` で定義されている (`shared/` ではない):

```python
class CallToolRequest(BaseModel):
    name: str
    args: dict = {}

class CallToolResponse(BaseModel):
    result: str
    is_error: bool
```

これらは MCP サーバー内でのみ使用される Pydantic モデルである。`shared/` レイヤーのコードは
`mcp/` からインポートしない。`shared/tool_executor.py` の `ToolCallResult` dataclass と混同しないこと。

---

## 12. `Protocol`、`TypedDict`、`dataclass`、DTO の違い

| Kind | Examples | Mutability | `isinstance()` | Usage |
|---|---|---|---|---|
| `TypedDict` | `LLMMessage`, `ArtifactEvent` | Mutable dict | No (unless `@runtime_checkable`) | Data transport; duck-typed |
| `Protocol` | `RagConfig` | Depends on impl | Yes (if `@runtime_checkable`) | Structural contract; any object satisfying fields works |
| frozen `dataclass` | `LLMUsage`, `LLMResponse`, `ActionResult` | Immutable | Yes | Value objects; hashable |
| `dataclass` | `ShellPolicy`, `DbConfig` | Mutable | Yes | Configuration objects |
| Pydantic model | `CallToolRequest`, `CallToolResponse` | Mutable | Yes | MCP HTTP request/response validation |

**AI ガイダンス:** 関数が `RagConfig` を受け取る場合、必要なフィールドを持つオブジェクトであれば
(`SimpleNamespace` を含め) プロトコルを満たす。`AgentConfig` でなければならないと仮定しないこと。

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_02_01_types_and_protocols-core-types.md`
- `90_shared_02_02_types_and_protocols-tool-and-execution-dto.md`

## Keywords

tool constants
CallToolRequest
CallToolResponse
Protocol
TypedDict
dataclass
DTO
