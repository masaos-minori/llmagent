---
title: "Shared Types and Protocols - Reference"
area: shared
tags:
  - shared
  - types
  - reference
related:
  - shared_02_01_types_and_protocols-core-types.md
  - shared_02_02_types_and_protocols-tool-and-execution-dto.md
  - shared_00_document-guide.md
---
# Shared Types and Protocols - Reference

- Overview → [shared_00_document-guide.md](shared_00_document-guide.md)

## 9a. `DbConfig` (`db/config.py`)

`DbConfig` is a frozen dataclass holding the four platform database paths, the `sqlite-vec` extension path (empty means the vec extension is not required) and the SQLite timeouts.

- `__post_init__` rejects empty DB paths, non-existent parent directories and `sqlite_timeout < 1`.
- `build_db_config()` constructs it from `agent.toml` via `ConfigLoader().load("agent.toml")`.
- It is consumed by `SQLiteHelper`, `maintenance.py` and session factories. Field defaults: `db/config.py`.

---

## 10. Tool Constants (`shared/tool_constants.py`)

The per-category tool-name frozensets serve as seed data for `ToolRegistry` and for side-effect classification in `ToolExecutor`; they are shared by `shared/` and `agent/`.

---

## 11. `CallToolRequest` / `CallToolResponse` Reference

Defined in `mcp_servers/models.py` (NOT in `shared/`; the package is named `mcp_servers`, not `mcp`, to avoid collision with the PyPI Model Context Protocol SDK `mcp`). These are Pydantic models used only within MCP servers; code in the `shared/` layer should NOT import from `mcp_servers/`. Do not confuse them with the `ToolCallResult` dataclass in `shared/transport_dto.py`.

---

## 12. Choosing a Type Kind

`TypedDict` is used for mutable data transport (`LLMMessage`, `ArtifactEvent`), `Protocol` for structural contracts, frozen `dataclass` for immutable value objects, and Pydantic models for MCP HTTP request/response validation.

**AI Guidance:** If a function accepts `RagConfig`, it should accept any object that satisfies the protocol (including `SimpleNamespace`), provided it has the required fields. Do not assume it must be an `AgentConfig`.

## Keywords

- shared
- types
- reference
