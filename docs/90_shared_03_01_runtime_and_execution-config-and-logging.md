---
title: "Shared Runtime and Execution - Config and Logging"
area: shared
tags:
  - shared
  - runtime
  - config-loader
  - config-isolation
  - logger
related:
  - 90_shared_00_document-guide.md
  - 90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md
  - 90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md
  - 90_shared_03_04_runtime_and_execution-caching-and-reference.md
source:
  - 90_shared_03_01_runtime_and_execution-config-and-logging.md
---

# Shared Runtime and Execution

- Overview → [90_shared_01_overview.md](90_shared_01_overview.md)

## 1. Purpose

Documents the runtime infrastructure and utilities within `shared/`: configuration loading, logging, token counting, OTel tracing, git helpers, formatters, `ToolExecutor`, and `McpServerConfig`.

---

## 2. `ConfigLoader` (`shared/config_loader.py`)

`ConfigLoader` reads TOML/JSON files sequentially and performs a shallow merge using `dict.update`. Keys prefixed with `_` are excluded. `ConfigMissingError`, `ConfigParseError`, and `ConfigReadError` are all subclasses of `ValueError`. If `restrict_to()` is called, any attempt to access files outside the permitted set raises a `ConfigPermissionError`. `load_all()` targets only `agent.toml` and raises an error if mandatory files are missing when `strict=True`.

---

## 2a. Process Separation Policy (Config Isolation Policy)

**Each process reads only its own configuration file.**

The agent, each MCP server, crawler, ingester, and chunk_splitter operate as independent processes. Each process reads exactly one corresponding configuration file via `ConfigLoader().load("xxx.toml")` at startup. Configuration files for other processes are not read. Values required by multiple processes (e.g., DB paths, external service URLs) should not be placed in a shared file but instead specified individually in each process's respective configuration file. Calling `ConfigLoader.restrict_to(own_config_file)` immediately after process startup enforces this rule at runtime. MCP servers call `restrict_to()` via `MCPServer.run_http()`. Crawler/ingester/chunk_splitter call it within `if __name__ == "__main__":`. The eventbus uses its own loader.

---

## 2b. `RagConfigValidator` / `ProductionConfigValidator` (`shared/config_validator.py`, `shared/production_config_validator.py`)

Both validators return a `ConfigValidationResult(errors, warnings)` (with an `ok` property). The RAG validator checks cross-file consistency in the `rag` section (e.g., mismatch between `embedding_dim`/`vec_dim`, `use_rrf=False`, cache thresholds). The Production validator treats violations as errors regardless of environment. Validation items include: checking if `_REQUIRED_STRICT_KEYS` is `False`, bidirectional differences between `tool_safety_tiers` and the registry, whether `allowed_tools == []`, and an approval-risk floor check for git write tools (`git_checkout`/`git_pull`/`git_push`) that flags any of the three whose effective risk resolves below `HIGH` — via an invalid `approval_risk_rules` override, an explicit non-HIGH override, or an implicit `tool_safety_tiers` fallback — even when `approval_risk_rules` is absent from config entirely. If `known_tools` is omitted, it attempts dynamic retrieval from the registry.

**Note:** `config_validator.py` and `production_config_validator.py` define separate `ConfigValidationResult` dataclasses and do not share a common type. They have different responsibilities (RAG configuration consistency vs. production operational strictness) and should not be confused.

---

## 3. `Logger` (`shared/logger.py`)

```python
class Logger:
    def __init__(self, name: str, log_file: str, *, structured_log: bool = False)
    def info(self, msg: str, *args, **kwargs) -> None
    def warning(self, msg: str, *args, **kwargs) -> None
    def error(self, msg: str, *args, **kwargs) -> None
    def set_context(self, **kwargs) -> None
    def clear_context(self) -> None
```

- The second argument to the constructor is named `log_file` (implementation name; the previous `filepath` was incorrect).
- Both `name` and `log_file` must be non-empty strings; otherwise, a `ValueError` is raised (via string validation function).
- Automatically configures `FileHandler` + `StreamHandler` (prevents duplication by setting `propagate=False`).
- If a handler is already set for a logger with the same `name`, the initialization returns immediately without doing anything (prevents duplicate registration; safe even if multiple `Logger` instances with the same name are created).
- `structured_log=True` $\rightarrow$ Logs are written in JSON Lines format (`_JsonFormatter`; fields include `ts`/`level`/`func`/`msg`, plus `turn_id`/`session_id`/`rag_query_id`/`workflow_id`/`task_id`/`exc` if they contain values).
- Context injection: Using `set_context(turn_id="T001", session_id=42)`, subsequent log lines will include these fields. Because `_ContextFilter` uses `contextvars.ContextVar`, context does not leak between concurrent asyncio tasks sharing the same logger.
- File write errors (`OSError`) $\rightarrow$ A WARNING is logged via the `shared.logger.fallback` logger (displayed on stderr), and execution falls back to `StreamHandler` only; no exception is raised.
- **Log messages must be in English only** (Japanese is not allowed) — per `rules/coding.md` convention.

---
