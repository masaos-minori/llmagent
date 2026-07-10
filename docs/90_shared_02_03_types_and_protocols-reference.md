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

# Shared Types and Protocols

- Overview → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)

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

- Validated in `__post_init__`: parent directories must exist; timeout/embedding_dims >= 1
- Built by `build_db_config()` which reads `agent.toml` via `ConfigLoader().load("agent.toml")`
- Used by `SQLiteHelper`, `maintenance.py`, and session factory code

---

## 10. Tool Constants (`shared/tool_constants.py`)

All constants are `frozenset[str]`. Used by `ToolRegistry` for seed data and by `ToolExecutor` for side-effect classification.

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

Referenced also by `shared/tool_executor.py` and `agent/tool_runner.py`.

---

## 11. `CallToolRequest` / `CallToolResponse` Reference

Defined in `mcp/models.py` (NOT in `shared/`):

```python
class CallToolRequest(BaseModel):
    name: str
    args: dict = {}

class CallToolResponse(BaseModel):
    result: str
    is_error: bool
```

These are Pydantic models used only within MCP servers. `shared/` layer code does not
import from `mcp/`. Do not confuse with `ToolCallResult` dataclass in `shared/tool_executor.py`.

---

## 12. How `Protocol`, `TypedDict`, `dataclass`, and DTO Differ

| Kind | Examples | Mutability | `isinstance()` | Usage |
|---|---|---|---|---|
| `TypedDict` | `LLMMessage`, `ArtifactEvent` | Mutable dict | No (unless `@runtime_checkable`) | Data transport; duck-typed |
| `Protocol` | `RagConfig` | Depends on impl | Yes (if `@runtime_checkable`) | Structural contract; any object satisfying fields works |
| frozen `dataclass` | `LLMUsage`, `LLMResponse`, `ActionResult` | Immutable | Yes | Value objects; hashable |
| `dataclass` | `ShellPolicy`, `DbConfig` | Mutable | Yes | Configuration objects |
| Pydantic model | `CallToolRequest`, `CallToolResponse` | Mutable | Yes | MCP HTTP request/response validation |

**AI guidance:** When a function accepts `RagConfig`, any object with the required fields
(including `SimpleNamespace`) satisfies the protocol. Do not assume it must be `AgentConfig`.

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
