---
title: "Shared Runtime and Execution Infrastructure — Caching and Reference"
area: shared
tags:
  - shared
  - caching
  - reference
related:
  - shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md
  - shared_03_03_runtime_and_execution-llm-and-mcp-clients.md
  - shared_00_document-guide.md
  - shared_02_02_types_and_protocols-tool-and-execution-dto.md
  - shared_03_01_runtime_and_execution-config-and-logging.md
---
# Shared Runtime and Execution Infrastructure

- Overview → [shared_00_document-guide.md](shared_00_document-guide.md)

## 17. `McpServerHealthState` / `McpServerHealthRegistry` (`shared/mcp_health.py`)

An enum for MCP server health states: `HEALTHY` (normal operation), `DEGRADED` (failing but not yet unavailable), `UNAVAILABLE` (circuit breaker open), `HALF_OPEN` (experimental probe after cooldown), and `UNKNOWN` (unregistered keys return `HEALTHY` default; `UNKNOWN` is never observed in practice).

Per-server health tracking for `ToolExecutor` dispatch gating, configured by a consecutive-failure threshold (`failure_threshold`) and a cooldown (`half_open_cooldown_sec`). A success resets the state to `HEALTHY` and clears the failure count and unavailable timestamp, which prevents an immediate re-`UNAVAILABLE` from stale counts.

**State Transitions:** `HEALTHY` → `DEGRADED` on first failure; `DEGRADED` → `UNAVAILABLE` on `failure_threshold` consecutive failures;  `UNAVAILABLE` → `HALF_OPEN` after `half_open_cooldown_sec` (experimental probe); `HALF_OPEN` → `UNAVAILABLE` on probe failure (cooldown resets); `HALF_OPEN` → `HEALTHY` on probe success; any state → `HEALTHY` on successful response.

Unregistered keys report `HEALTHY` (`UNKNOWN` is never observed). The registry stores no degraded reason.

---

## 18. `LlmPayloadHandler` (`shared/llm_payload.py`)

`parse_response()` accepts the raw parsed JSON dict (not `httpx.Response`), validates the `choices`/`message` structure, raises `ValueError` on invalid input and delegates usage parsing to `LlmSseHelpers.parse_usage()`, which invokes the optional `on_usage(prompt_tokens, completion_tokens)` callback.

---

## 19. `LlmHotConfigHandler` (`shared/llm_hot_config.py`)

Manages hot-reloadable config fields for `LLMClient`; `apply_config()` is a partial update that applies only non-`None` values. The hot-reloadable field set is defined by `HOT_CONFIG_FIELDS` in `shared/llm_hot_config.py`; see `shared_03_03` (Configuration).

---

## 20. Reference Notes

- `load_all()` reads `agent.toml` only; other process configs are loaded individually by their own processes (see [Process Separation Policy](shared_03_01_runtime_and_execution-config-and-logging.md#2a-process-separation-policy-config-isolation-policy), the ownership reference).
- `ToolExecutor` does not cache tool results; there is no tool-result cache.
- `git_helper.get_repo_info()` returns `RepoInfoResult`; callers must check `.success` and `.failure_reason`.
- Exact token counts come from the tokenizer endpoint with a category-based estimate fallback (see `token_counter` in `shared_03_02`).
- Health gate state transitions are described in the `McpServerHealthState` section above.

## Keywords

- shared
- caching
- reference
