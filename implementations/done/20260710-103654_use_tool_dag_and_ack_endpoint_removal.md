# Implementation: Remove `use_tool_dag=false` legacy execution path and the `POST /ack` compatibility endpoint (Phase 3)

## Goal

Remove two breaking-but-approved backward-compatibility surfaces: the `use_tool_dag=false` legacy (non-DAG, write-before-read) tool execution mode, and the `POST /ack` query-parameter compatibility alias for the canonical `POST /events/{event_id}/ack` Event Bus endpoint.

## Scope

**In:**
- `scripts/agent/config_dataclasses.py`: delete the `use_tool_dag: bool = True` field
- `scripts/agent/config_builders.py`: delete the `use_tool_dag=bool(cfg.get("use_tool_dag", True))` line
- `scripts/agent/tool_runner.py`: simplify `execute_all_tool_calls()`'s branch from `if ctx.cfg.tool.use_tool_dag and not ctx.cfg.tool.serial_tool_calls:` to `if not ctx.cfg.tool.serial_tool_calls:` (DAG scheduling becomes unconditional; `_execute_standard()` remains, used only for `serial_tool_calls=True`)
- `scripts/agent/repl_health.py`: delete `use_tool_dag`-related startup banner/log entries and the production-validator call argument
- `scripts/shared/production_config_validator.py`: delete the `use_tool_dag` production/local warning-and-error validation logic
- `config/agent.toml`: delete the `use_tool_dag = true` line
- `scripts/eventbus/app.py`: delete the `@app.post("/ack")` route handler (keep `@app.post("/events/{event_id}/ack")`)
- `scripts/eventbus/ack_route.py`: check whether the legacy `ack()` handler function becomes unused after the route is removed; delete it if so, keep `ack_event()` (the canonical handler)
- Update tests: `tests/test_agent_repl_tool_exec.py`, `tests/test_tool_runner.py`, `tests/test_config_builders.py`, `tests/test_production_config_validator.py`, `tests/test_repl_health.py`, `tests/test_plugin_ci_strict.py`, `tests/test_eventbus_ack_endpoint.py`, `tests/test_eventbus_crash_ack.py`, `tests/test_eventbus_concurrent.py`
- Update docs: `docs/05_agent_08_configuration.md`, `docs/04_mcp_06_configuration_and_operations.md`, `docs/05_agent_06_tool-execution-and-approval.md`, `docs/90_shared_02_types_and_protocols.md`, `docs/90_shared_03_runtime_and_execution.md`, `docs/06_eventbus_02_http_api_and_runtime.md`, `docs/06_eventbus_06_reference_api.md`
- Add a CHANGELOG / release-notes entry documenting removal of `use_tool_dag=false` and `POST /ack` as breaking changes

**Out:**
- `serial_tool_calls` config flag and its behavior — unchanged, still a valid supported mode
- `POST /events/{event_id}/ack` and `POST /nack` — unchanged, canonical endpoints stay as-is
- `_execute_with_dag()` and `_execute_standard()` function bodies — no internal logic changes beyond the branch condition in `execute_all_tool_calls()`

## Assumptions

1. No production config file in this repository sets `use_tool_dag = false` — confirmed `config/agent.toml` currently sets it to `true` explicitly; the field can be deleted from the TOML without changing runtime behavior.
2. The config loader tolerates unknown/removed TOML keys without raising (no strict "reject unknown key" validation was found in `scripts/shared/config_loader.py`); if this assumption is wrong, any external deployment still passing `use_tool_dag = false` (or `= true`) in its TOML will fail to start until the key is removed from that TOML — this is treated as an accepted risk per the approved plan.
3. No external client outside this repository depends on `POST /ack` — the user has explicitly approved deleting it in this cycle (per `plans/20260710-102535_plan.md`, Q4).
3a. If assumption 3 is wrong, the mitigation is the CHANGELOG entry plus the ability to roll back to the previous release tag.
4. `_execute_standard()` in `scripts/agent/tool_runner.py` is still required after this change because it also serves `serial_tool_calls=True` — it must not be deleted, only its selection condition changes.

## Implementation

### Target file

1. `scripts/agent/config_dataclasses.py`
2. `scripts/agent/config_builders.py`
3. `scripts/agent/tool_runner.py`
4. `scripts/agent/repl_health.py`
5. `scripts/shared/production_config_validator.py`
6. `config/agent.toml`
7. `scripts/eventbus/app.py`
8. `scripts/eventbus/ack_route.py`
9. The 9 test files and 7 doc files listed in Scope

### Procedure

1. Delete the `use_tool_dag` field from `scripts/agent/config_dataclasses.py`.
2. Delete the corresponding build line in `scripts/agent/config_builders.py`.
3. In `scripts/agent/tool_runner.py`, change the `execute_all_tool_calls()` condition to only check `ctx.cfg.tool.serial_tool_calls`.
4. In `scripts/agent/repl_health.py`, delete the `"use_tool_dag": getattr(tool_cfg, "use_tool_dag", True)` banner/log entry and the corresponding production-validator call argument.
5. In `scripts/shared/production_config_validator.py`, delete the `use_tool_dag` fail-in-production / warn-in-local validation branch.
6. Delete the `use_tool_dag = true` line from `config/agent.toml`.
7. In `scripts/eventbus/app.py`, delete the `@app.post("/ack") async def ack(...)` route function.
8. In `scripts/eventbus/ack_route.py`, run `grep -rn "\back\b" scripts/eventbus tests --include="*.py"` to confirm whether the legacy `ack()` handler is still referenced anywhere else; delete it only if the route deletion in step 7 makes it fully unused.
9. Update each listed test file: remove test cases that assert on the legacy `use_tool_dag=False` write-before-read behavior or on `POST /ack`; where a test's intent was to verify current (DAG-always-on) behavior, keep it but drop the now-meaningless `use_tool_dag` parametrization.
10. Update each listed doc file: remove `use_tool_dag` as a configurable field (state that DAG scheduling is now unconditional); remove the "Deprecated endpoints" section describing `POST /ack`.
11. Add a CHANGELOG / release-notes entry noting both removals as breaking changes.
12. Run `uv run ruff check scripts/ tests/`, `uv run mypy scripts/`, `PYTHONPATH=scripts uv run lint-imports`.
13. Run `grep -rn "use_tool_dag" scripts tests config docs` and `grep -rn "\"/ack\"\|'/ack'" scripts tests docs` — expect 0 remaining references (aside from the CHANGELOG entry describing the removal).

### Method

Config-flag removal + route deletion. No new abstractions; the DAG scheduling path becomes the sole non-serial execution path instead of one of two alternatives.

### Details

- Removing `use_tool_dag` collapses the four historical execution-mode combinations (`use_tool_dag` × `serial_tool_calls`) down to two: DAG-scheduled parallel (default) or fully serial (`serial_tool_calls=True`).
- `tests/test_agent_repl_tool_exec.py` currently has 6 test functions parametrized by `use_tool_dag` (both `True` and `False`); the `False`-parametrized ones that assert legacy write-before-read ordering must be deleted, not merely updated, since that behavior no longer exists.
- `tests/test_production_config_validator.py` has dedicated `TestUseToolDagValidation`-style test cases (4 tests) that assert on error/warning strings mentioning `use_tool_dag` in production vs. local mode; these must be deleted since the validator code path they test is being removed.
- The `/ack` deletion is a pure route removal — `ack_event()` (the canonical `POST /events/{event_id}/ack` handler) is untouched and continues to serve all ack traffic.

## Validation plan

```bash
uv run ruff format scripts/ tests/
uv run ruff check scripts/ tests/
uv run mypy scripts/
PYTHONPATH=scripts uv run lint-imports
uv run pytest tests/test_agent_repl_tool_exec.py tests/test_tool_runner.py tests/test_config_builders.py \
  tests/test_production_config_validator.py tests/test_repl_health.py tests/test_plugin_ci_strict.py \
  tests/test_eventbus_ack_endpoint.py tests/test_eventbus_crash_ack.py tests/test_eventbus_concurrent.py -v
grep -rn "use_tool_dag" scripts tests config docs   # expect no output (except CHANGELOG)
grep -rn "\"/ack\"\|'/ack'" scripts tests docs       # expect no output (except CHANGELOG)
uv run check-mcp-docs
```

Expected outcome: all listed tests pass, no lint/type/import-layer regressions, no remaining runtime references to `use_tool_dag` or the `/ack` route outside the CHANGELOG entry.
