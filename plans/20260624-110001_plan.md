# Plan: Enable Dependency-Aware Tool Scheduling by Default

**Requirement:** `requires/20260622_77_require.md`

---

## Goal

Enable `use_tool_dag=True` as the default so mixed rounds (read + write tools) use resource-scoped dependency ordering instead of round-wide serialization. The DAG scheduling code (`tool_scheduler.py`, `_execute_with_dag()`) is already fully implemented and tested — the only gap is that the `config_builders.py` default overrides the dataclass default to `False`.

---

## Scope

**In:**
- `scripts/agent/config_builders.py` — fix `cfg.get("use_tool_dag", False)` → `True` to match the dataclass default
- `config/tools.toml` — add explicit `use_tool_dag = true` comment+value
- `docs/05_agent_08_configuration.md` — update `use_tool_dag` default from `False` to `True`; expand description to document DAG scheduling semantics

**Out:**
- Rewriting `tool_scheduler.py` or `_execute_with_dag()` (already correct)
- Adding new `requires_serial` or `resource_scope` metadata to `tools_definitions.toml`
- Removing `_execute_standard()` (still needed for `serial_tool_calls=True` path)
- Changing how `is_write` is determined (correctly uses `WRITE_TOOLS`/`DELETE_TOOLS` sets)

---

## Assumptions

1. `config_dataclasses.py:224` already has `use_tool_dag: bool = True` — the dataclass default is the intended deployed default.
2. `config_builders.py:189` `cfg.get("use_tool_dag", False)` is the only place that overrides the intent to `False`.
3. `tools.toml` contains `serial_tool_calls = false` but no `use_tool_dag` line — config file was never updated to match the design intent.
4. `_execute_with_dag()` is safe as the default:
   - Tools not in `tool_definitions` → no `ToolSpec` in `tool_meta` → default `is_write=False`, `requires_serial=False`, `resource_scope=""` → placed in the parallel group (conservative safe default)
   - `WRITE_TOOLS` / `DELETE_TOOLS` sets are used for `is_write` detection regardless, so write side-effects are caught even for dynamically loaded MCP tools
5. Existing tests in `test_tool_runner.py` cover `_execute_with_dag()` with explicit `use_tool_dag=True` — no new test logic needed; but a regression test asserting the builder default should be added.
6. No behavior change for rounds with `serial_tool_calls=True` — that path still serializes everything.

---

## Unknowns

| ID | Unknown | Resolution | Blocking |
|---|---|---|---|
| UNK-01 | Does any `config/*.toml` file explicitly set `use_tool_dag = false` that would override the new builder default? | `grep -r "use_tool_dag" config/` returns no results — no file sets it. Safe to change builder default. | False |
| UNK-02 | Do integration tests use `use_tool_dag=False` implicitly (via default config)? | Tests that test `_execute_standard()` explicitly pass `use_tool_dag=False`. Tests using `_cfg()` factory at line 58 already have `use_tool_dag=True`. No implicit dependency. | False |

---

## Affected Areas

| File | Change | Blast radius | Churn | Deploy impact |
|---|---|---|---|---|
| `scripts/agent/config_builders.py` | Change `False` → `True` for `use_tool_dag` default | Low | High | Low (behavior change for mixed rounds) |
| `config/tools.toml` | Add `use_tool_dag = true` | Low | Low | None (makes explicit what was implicit) |
| `docs/05_agent_08_configuration.md` | Update default from `False` to `True`; expand DAG semantics description | Low | Low | None |
| `tests/test_tool_runner.py` | Add test asserting `use_tool_dag` defaults to `True` from builder | Low | Active | None |

---

## Design

### Change 1: `config_builders.py` — fix default

**Before (line 189):**
```python
use_tool_dag=bool(cfg.get("use_tool_dag", False)),
```

**After:**
```python
use_tool_dag=bool(cfg.get("use_tool_dag", True)),
```

This makes the builder default match the dataclass default (`bool = True`) and the DAG scheduling path becomes active for all mixed rounds.

### Change 2: `config/tools.toml` — make explicit

Add after `serial_tool_calls = false`:
```toml
# use_tool_dag: enable dependency-aware scheduling (write-before-read, resource-scoped)
# When true: independent read-only tools run concurrently even in rounds with writes.
# When false: any side-effect tool in the round forces sequential execution (legacy behavior).
use_tool_dag = true
```

### Change 3: `docs/05_agent_08_configuration.md` — update description

Before:
```
| `use_tool_dag` | `False` | Execute WRITE_TOOLS before READ_TOOLS |
```

After:
```
| `use_tool_dag` | `True` | Dependency-aware scheduling: independent reads run concurrently; writes serialized per resource scope. Disable for strict round-wide serialization legacy behavior. |
```

### Change 4: Tests — builder default assertion

In `tests/test_tool_runner.py`, add:
```python
class TestConfigBuilderDefaults:
    def test_use_tool_dag_defaults_to_true(self) -> None:
        """use_tool_dag must default to True in config_builders to enable DAG scheduling."""
        from agent.config_builders import _build_tool_config
        cfg = _build_tool_config({})
        assert cfg.use_tool_dag is True, (
            "DAG scheduling must be enabled by default; "
            "set use_tool_dag=false in tools.toml to revert"
        )
```

---

## Behavioral Change Summary

| Round composition | Before (use_tool_dag=False) | After (use_tool_dag=True) |
|---|---|---|
| All read-only tools | Parallel | Parallel (unchanged) |
| All write tools, same resource_scope | Serial (all) | Serial (scoped) |
| Read + write tools, mixed | Serial (all) | Writes first, then reads in parallel |
| `requires_serial=True` tool | Serial (all) | Sequential barrier (unchanged) |
| `serial_tool_calls=True` | Serial (all) | Serial (all — flag overrides DAG) |

Debug/trace visibility (already implemented — no change needed):
- `ROUND_SERIALIZATION` log lines in `tool_scheduler.py`
- `ROUND_EXEC` log lines in `_execute_with_dag()` 
- `ctx.stats.stat_serialization_events` for session diagnostics

---

## Implementation Steps

1. **Phase 1: `config_builders.py`**
   - [ ] Change `cfg.get("use_tool_dag", False)` → `cfg.get("use_tool_dag", True)`
   - [ ] `uv run pytest tests/test_tool_runner.py -v` — all pass

2. **Phase 2: `tools.toml`**
   - [ ] Add `use_tool_dag = true` with comment

3. **Phase 3: Docs**
   - [ ] Update `use_tool_dag` row in `05_agent_08_configuration.md`

4. **Phase 4: Tests**
   - [ ] Add `TestConfigBuilderDefaults.test_use_tool_dag_defaults_to_true` to `test_tool_runner.py`
   - [ ] `uv run pytest tests/test_tool_runner.py tests/test_tool_scheduler.py -v`
   - [ ] `uv run ruff check scripts/agent/config_builders.py`

---

## Validation Plan

| Check | Tool | Target |
|---|---|---|
| Lint | `ruff check scripts/agent/config_builders.py` | 0 errors |
| Tests | `uv run pytest tests/test_tool_runner.py -v` | all pass |
| Tests | `uv run pytest tests/test_tool_scheduler.py tests/test_tool_scheduler_comprehensive.py -v` | all pass |
| Regression | `uv run pytest tests/test_agent_repl_tool_exec.py -v` | no regression |

---

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Mixed-round serialization change causes unexpected behavior in production | Low | DAG writes-before-reads preserves all safety guarantees; read tools getting unblocked earlier is the intent |
| Config file with explicit `use_tool_dag = false` in production gets overridden | Very low | Config file values take precedence over the builder default; `cfg.get("use_tool_dag", True)` returns the file value if set |
| Tests relying on implicit `use_tool_dag=False` default break | Low | All tests that rely on `False` already pass it explicitly (verified in test_tool_runner.py) |
