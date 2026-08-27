# Shared Types and Protocols - Reference

- Overview → [90_shared_01_overview.md](90_shared_01_overview.md)

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
```

- Validated in `__post_init__`: parent directory must exist, `timeout` must be $\ge$ 1.
- Constructed by `build_db_config()`, which reads `agent.toml` via `ConfigLoader().load("agent.toml")`.
- Used by `SQLiteHelper`, `maintenance.py`, and session factories.

---

## 10. Tool Constants (`shared/tool_constants.py`)

All constants are `frozenset[str]`. They serve as seed data for `ToolRegistry` and are used for side-effect classification in `ToolExecutor`. Defined per category: `READ`/`WRITE`/`DELETE`/`RAG`/`CICD`/`MDQ`/`GIT`/`SHELL`/`WEB_SEARCH`, and referenced by both `shared/tool_executor.py` and `agent/tool_runner.py`. (Explicit in code: `scripts/shared/tool_constants.py`)

---

## 11. `CallToolRequest` / `CallToolResponse` Reference

Defined in `mcp_servers/models.py` (NOT in `shared/`; the `mcp_servers` package was renamed from `mcp` to avoid collision with the PyPI Model Context Protocol SDK `mcp`). These are Pydantic models used only within MCP servers; code in the `shared/` layer should NOT import from `mcp_servers/`. Do not confuse them with the `ToolCallResult` dataclass in `shared/tool_executor.py`. (Explicit in code: `scripts/mcp_servers/models.py`)

---

## 12. Differences between `Protocol`, `TypedDict`, `dataclass`, and DTOs

| Kind | Examples | Mutability | `isinstance()` | Usage |
|---|---|---|---|---|
| `TypedDict` | `LLMMessage`, `ArtifactEvent` | Mutable dict | No (unless `@runtime_checkable`) | Data transport; duck-typed |
| `Protocol` | `RagConfig` | Depends on impl | Yes (if `@runtime_checkable`) | Structural contract; any object satisfying fields works |
| frozen `dataclass` | `LLMUsage`, `LLMResponse`, `ActionResult` | Immutable | Yes | Value objects; hashable |
| `dataclass` | `ShellPolicy`, `DbConfig` | Mutable | Yes | Configuration objects |
| Pydantic model | `CallToolRequest`, `CallToolResponse` | Mutable | Yes | MCP HTTP request/response validation |

**AI Guidance:** If a function accepts `RagConfig`, it should accept any object that satisfies the protocol (including `SimpleNamespace`), provided it has the required fields. Do not assume it must be an `AgentConfig`.
