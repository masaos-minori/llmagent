## Goal

Remove the now-meaningless `tool_cache_ttl` diff-apply line from `_apply_tool_params()`
(REQ-002), per `plans/20260825-142436_plan.md`.

## Scope

- In scope: the two-line `tool_cache_ttl` block in `_apply_tool_params()`
  (`config_reload.py:402-403`) only.
- Out of scope: the `_sync_services()` `tools.apply_config(cache_ttl=...)` block —
  **already removed by a separate implementation** (see Assumptions); the other
  three fields `_apply_tool_params()` collects (`serial_tool_calls`,
  `tool_definitions_strict`, `plan_blocked_tools`); `ToolConfig.tool_cache_ttl`
  field itself (separate Plan, `plans/20260827-121312_plan.md` REQ-001).

## Assumptions

- **Partially implemented — existing documents found and confirmed insufficient**:
  two prior implementation-procedure documents already exist for this same Plan/
  target-file pair (`implementations/20260825-224356_07_scripts_agent_services_config_reload_py.md`,
  `implementations/20260826_01_scripts_agent_services_config_reload.py.md`), both
  with `Source plan: plans/20260825-142436_plan.md` and
  `Related target files: scripts/agent/services/config_reload.py`. Both describe
  REQ-001 (remove `_sync_services()`'s `tools.apply_config(cache_ttl=...)` block)
  AND REQ-002 (remove `_apply_tool_params()`'s `tool_cache_ttl` line) together, but
  neither's Execution Status shows completion (both `Blocked`/`Pending`).
  Re-verifying current source (2026-08-27) found REQ-001 is now satisfied
  (`_sync_services()` no longer references `tools` at all — confirmed via `rg -n
  "tools\.apply_config" scripts/agent/services/config_reload.py` returning no
  matches), evidently completed by the same parallel `ToolExecutor` cache-removal
  implementation (`plans/done/20260826-120000_plan.md`) that removed the cache
  itself, not by either of these two documents. REQ-002 remains open. This document
  covers only the REQ-002 remainder — do not re-implement REQ-001 (already done).
- `ToolConfig.tool_cache_ttl` (the field this diff-apply line writes into) still
  exists as of this writing (`config_dataclasses.py:176`) — removing it is
  `plans/20260827-121312_plan.md`'s REQ-001, a separate Plan. This item's removal
  must land **before** that Plan's REQ-001, per `plans/20260825-142436_plan.md`'s
  own Risks section — otherwise `dataclasses.replace(cfg.tool, tool_cache_ttl=v)`
  (line 367) would raise `TypeError` once the field no longer exists while this
  diff-apply line still generates it.

## Design decisions

- Remove only the two lines (402-403); leave `_apply_tool_params()`'s signature,
  docstring, and the three other field-collection blocks unchanged.

## Alternatives considered

- Wrapping the line in a version-gate or feature flag was considered and rejected —
  per this project's no-compat-shim policy and the fact that `tool_cache_ttl` has no
  live effect regardless of the flag's state.

## Implementation
### Target file
`scripts/agent/services/config_reload.py`

### Procedure
1. Re-run `rg -n "tool_cache_ttl\|tools\.apply_config" scripts/agent/services/config_reload.py`
   immediately before editing, to confirm no drift since this Plan was written.
2. Remove lines 402-403 (the `tool_cache_ttl` diff-apply block) from
   `_apply_tool_params()`.
3. Run `uv run pytest tests/agent/services/test_config_reload*.py -v` (will show the
   seq 04 regression test failing/missing until that item in this pass is also
   applied, if implemented in a different order).

### Method
Direct code deletion (Edit tool) — two lines removed from one method body.

### Details
Current code (verified 2026-08-27, lines 398-409):
```python
    def _apply_tool_params(
        self, cfg: AgentConfig, new_cfg: dict[str, Any], changes: dict[str, Any]
    ) -> None:
        """Collect tool execution setting changes."""
        if (v := _get_float(new_cfg, "tool_cache_ttl")) is not None:
            changes["tool_cache_ttl"] = v
        if (vb := _get_bool(new_cfg, "serial_tool_calls")) is not None:
            changes["serial_tool_calls"] = vb
        if (vb := _get_bool(new_cfg, "tool_definitions_strict")) is not None:
            changes["tool_definitions_strict"] = vb
        if (lst := _get_list(new_cfg, "plan_blocked_tools")) is not None:
            changes["plan_blocked_tools"] = list(lst)
```
Remove the `if (v := _get_float(new_cfg, "tool_cache_ttl")) is not None:
changes["tool_cache_ttl"] = v` block (2 lines), leaving:
```python
    def _apply_tool_params(
        self, cfg: AgentConfig, new_cfg: dict[str, Any], changes: dict[str, Any]
    ) -> None:
        """Collect tool execution setting changes."""
        if (vb := _get_bool(new_cfg, "serial_tool_calls")) is not None:
            changes["serial_tool_calls"] = vb
        if (vb := _get_bool(new_cfg, "tool_definitions_strict")) is not None:
            changes["tool_definitions_strict"] = vb
        if (lst := _get_list(new_cfg, "plan_blocked_tools")) is not None:
            changes["plan_blocked_tools"] = list(lst)
```

## Compatibility considerations

- No API change — `_apply_tool_params()`'s signature is unchanged; only its
  internal behavior for one now-inert key (`tool_cache_ttl`) changes from "silently
  writes a value nothing reads" to "silently ignores the key" — no observable
  behavior change for any caller.
- Must land before `plans/20260827-121312_plan.md`'s REQ-001 (see Assumptions) to
  avoid a `TypeError` regression.

## Security considerations

- N/A: no security-relevant behavior; removes a dead configuration pass-through.

## Rollback considerations

- Two-line revert via `git diff`/`git checkout -- scripts/agent/services/config_reload.py`;
  independent of the seq 04 test file (though both should land together per the
  Plan's Implementation steps).

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/config_reload.py` | Unit | `uv run pytest tests/agent/services/test_config_reload*.py -v` | `tool_cache_ttl` no longer appears in `_apply_tool_params()`'s output; seq 04's new regression test passes once applied |

## Completion criteria

- `rg -n "tool_cache_ttl" scripts/agent/services/config_reload.py` returns no
  matches.
- `_apply_tool_params()`'s three other field-collection blocks are unchanged.

## Out of scope

- `_sync_services()`'s `tools.apply_config(...)` block (already removed).
- `ToolConfig.tool_cache_ttl` field itself (separate Plan).
- `scripts/agent/commands/cmd_config_display.py:48`'s `tool_cache_ttl` display line
  (not this Plan's scope — flagged for `plans/20260827-121312_plan.md`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm no drift via `rg` | Pending | — | — | |
| 2 | Remove the `tool_cache_ttl` diff-apply block | Pending | — | — | Must land before `plans/20260827-121312_plan.md` REQ-001 |
| 3 | Run `uv run pytest tests/agent/services/test_config_reload*.py -v` | Pending | — | — | Requires seq 04 applied |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002
- **Source issue**: `issues/done/20260825_cfgreload_toolexecutor_cache_wiring_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-142436_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure; supersedes the REQ-002 portion of `implementations/20260825-224356_07_scripts_agent_services_config_reload_py.md` and `implementations/20260826_01_scripts_agent_services_config_reload.py.md` (both left Pending/Blocked; their REQ-001 portion was independently completed by `plans/done/20260826-120000_plan.md`)
- **Generated at**: 20260827-132826
- **Related target files**: `scripts/agent/services/config_reload.py`
