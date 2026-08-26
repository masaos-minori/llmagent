## Goal

Remove the `config_reload.py` wiring to `ToolExecutor`'s TTL cache (`tool_cache_ttl` diff-apply + `_sync_services()` `tools.apply_config(cache_ttl=...)` call) so that `/reload` does not raise `AttributeError` after the cache is deleted.

## Scope

**In-Scope**:
- `scripts/agent/services/config_reload.py`: remove `_sync_services()` block calling `ctx.services_required.tools.apply_config(cache_ttl=ctx.cfg.tool.tool_cache_ttl)` and its `result.applied.append("tools")`. Remove `_apply_tool_params()` line for `tool_cache_ttl`.

**Out-of-Scope**:
- `ToolExecutor` cache implementation itself (prerequisite tracked separately).
- Other fields in `_sync_services()` / `_apply_tool_params()`.

## Assumptions

- All three Requirements depend on the separate `ToolExecutor` cache deletion landing first. Do NOT implement until confirmed.

## Design decisions

- If `ToolExecutor.apply_config` survives for other parameters after cache removal, keep it but remove only the `cache_ttl` argument.
- If `ToolExecutor.apply_config` is fully removed, remove the entire `_sync_services()` tools block.

## Alternatives considered

- Keep the wiring and accept intermittent `AttributeError`: rejected because it breaks `/reload` reliability.
- Add try/except around the call: rejected because it masks the root cause — the wiring should not exist after cache removal.

## Implementation

### Target file

`scripts/agent/services/config_reload.py`

### Procedure

#### Phase 1: Preparation

```bash
# PREREQUISITE CHECK — MUST PASS BEFORE proceeding:
rg "apply_config\(\*, cache_ttl" scripts/shared/tool_executor.py
# Expected: NO MATCHES (cache_ttl parameter must be removed from ToolExecutor)

rg "_cache_ttl\|_cache\|stat_cache_hits\|_execute_with_cache" scripts/shared/tool_executor.py
# Expected: NO MATCHES (all cache-related code must be removed)
```

If either check shows remaining cache code, STOP. Wait for the prerequisite change.

#### Phase 2: Core Logic

**Step A: Remove `tool_cache_ttl` from `_apply_tool_params()`**

Current code (lines 240–259):
```python
def _apply_tool_params(self, cfg: AgentConfig, new_cfg: dict[str, Any]) -> None:
    """Apply tool execution settings."""
    _apply_float(
        new_cfg, "tool_cache_ttl", lambda v: setattr(cfg.tool, "tool_cache_ttl", v)
    )
    _apply_bool(
        new_cfg,
        "serial_tool_calls",
        lambda v: setattr(cfg.tool, "serial_tool_calls", v),
    )
    # ... rest unchanged
```

After change:
```python
def _apply_tool_params(self, cfg: AgentConfig, new_cfg: dict[str, Any]) -> None:
    """Apply tool execution settings."""
    # tool_cache_ttl removed — TTL cache deleted from ToolExecutor
    _apply_bool(
        new_cfg,
        "serial_tool_calls",
        lambda v: setattr(cfg.tool, "serial_tool_calls", v),
    )
    # ... rest unchanged
```

**Step B: Remove or modify `_sync_services()` tools block**

Current code (approximate location — must verify at runtime):
```python
if ctx.services_required.tools:
    ctx.services_required.tools.apply_config(cache_ttl=ctx.cfg.tool.tool_cache_ttl)
    result.applied.append("tools")
```

Option 1 — if `ToolExecutor.apply_config` is fully removed:
```python
# Removed — ToolExecutor no longer accepts config updates via apply_config
```

Option 2 — if `ToolExecutor.apply_config` survives for other params:
```python
if ctx.services_required.tools:
    ctx.services_required.tools.apply_config()
    result.applied.append("tools")
```

#### Phase 3: Deployment & Verification

- Run: `uv run pytest tests/agent/services/test_config_reload*.py -v`
- Verify: no `AttributeError` on `/reload` with `tool_cache_ttl` field present.
- Verify: `"tools"` appears in `result.applied` (or is absent if Option 1 applied).

### Details

- **REQ-001**: Remove `tools.apply_config(cache_ttl=...)` block from `_sync_services()`. If `apply_config` survives for other params, remove only `cache_ttl` argument.
- **REQ-002**: Remove `tool_cache_ttl` diff-apply line from `_apply_tool_params()`.
- **REQ-003**: Regression test verifying `/reload` completes without error after cache deletion.

### Prerequisite verification checklist

Before implementing any step:

- [ ] `rg "apply_config\(\*, cache_ttl" scripts/shared/tool_executor.py` returns NO matches
- [ ] `rg "_cache_ttl\|_cache\|stat_cache_hits\|_execute_with_cache" scripts/shared/tool_executor.py` returns NO matches
- [ ] Confirm with reviewer that cache deletion PR has landed

## Compatibility considerations

- No API changes — removal of dead wiring.
- No config schema changes required.
- `AgentConfig.tool_cache_ttl` field may also need removal (separate concern — verify before removing from dataclass).

## Security considerations

- None — removal of dead code path.

## Rollback considerations

- Revert: restore original files.
- Git ref-safe rollback: `git checkout HEAD -- scripts/agent/services/config_reload.py`.
- No database migration or config file changes.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/config_reload.py` | Unit | `uv run pytest tests/agent/services/test_config_reload*.py -v` | `/reload` works without error after cache deletion |

## Completion criteria

- [ ] `tool_cache_ttl` reference removed from `_apply_tool_params()`.
- [ ] `tools.apply_config(cache_ttl=...)` removed from `_sync_services()`.
- [ ] No `AttributeError` on `/reload` when `tool_cache_ttl` field is present in payload.
- [ ] `"tools"` correctly reported in reload outcome (either as applied or absent).
- [ ] Prerequisite cache deletion verified before implementation.

## Out of scope

- Changes to `validate_*` function contents.
- Applying validation re-execution to `ApprovalConfig`, `MemoryConfig`, `MCPConfig` etc.
- Adding new validation rules.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Preparation / Refactoring | Blocked | — | — | Prerequisite: ToolExecutor cache deletion unimplemented (UNK-01) |
| 2 | Core Logic Implementation | Blocked | — | — | Awaiting prerequisite |
| 3 | Deployment & Verification | Blocked | — | — | Awaiting prerequisite |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| Phase 1 | No issue/plan exists proposing ToolExecutor cache deletion itself | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: issues/20260825_cfgreload_toolexecutor_cache_wiring_issue.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-142436_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-08-25 22:43:56
- **Related target files**: scripts/agent/services/config_reload.py
