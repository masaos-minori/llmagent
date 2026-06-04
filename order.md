# Refactor Instructions

## Goal

Remove only the remaining **high-priority backward-compatibility layers**.
Do not add new features.
Do not expand scope beyond compatibility removal.
Migrate all callers first, then delete legacy paths completely.

## Target Files

* `agent/context.py`: remove flat-access backward compatibility.
* `agent/config.py`: remove flat-field backward compatibility.
* `agent/orchestrator.py`: remove backward-compat delegate methods.
* `agent/http_lifecycle.py`: remove backward-compat `procs` property.

## Rules

* Replace all legacy access paths with the new structured APIs before deletion.
* Do not leave old and new paths coexisting.
* Update tests and call sites together.

## File-Specific Instructions

### `agent/context.py`

* Remove `__getattr__` / `__setattr__` flat-access compatibility.
* Migrate all old `ctx.xxx` access to the new structured state/services layout.

### `agent/config.py`

* Remove flat-field compatibility access.
* Migrate all old `cfg.xxx` usage to nested config access such as:
  * `cfg.llm.llm_url`
  * `cfg.mcp.mcp_servers`
  * `cfg.obs.audit_log_file`

### `agent/orchestrator.py`

* Remove legacy delegate methods kept only for old tests/callers.
* Delete:
  * `_run_turn()`
  * `_record_llm_latency()`
  * `_update_consecutive_errors()`
  * `_check_consecutive_error_limit()`
  * `_check_all_tool_guards()`
* Move tests to `LLMTurnRunner` and `ToolLoopGuard`.

### `agent/http_lifecycle.py`

* Remove the backward-compat `procs` property.
* Replace all usages with explicit lifecycle APIs such as `verify_running()`.

## Work Order

1. Find all remaining legacy usages.
2. Migrate all callers to the new APIs.
3. Delete all compatibility code.
4. Update tests so no legacy path remains.

## Done Criteria

* `AgentContext` no longer supports flat compatibility access.
* `AgentConfig` no longer supports flat compatibility access.
* `Orchestrator` no longer exposes legacy delegate methods.
* `HttpServerLifecycleManager` no longer exposes `procs`.
* All tests and runtime paths use only the new APIs.
