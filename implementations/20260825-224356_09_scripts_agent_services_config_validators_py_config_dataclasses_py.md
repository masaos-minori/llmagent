## Goal

Remove the dead validator `validate_tool_cache_max_size` (`_v_tool_cms`) and its wiring after `ToolExecutor` cache deletion eliminates the `tool_cache_max_size` field from `ToolConfig`.

## Scope

**In-Scope**:
- `scripts/agent/services/config_validators.py`: delete `validate_tool_cache_max_size`.
- `scripts/agent/config_dataclasses.py`: delete `_v_tool_cms` import and `__post_init__` call; delete `tool_cache_ttl`/`tool_cache_max_size` fields from `ToolConfig`.

**Out-of-Scope**:
- Other validators in `config_validators.py` (tracked separately as `issues/20260825_config_validators_duplicate_range_checks_issue.md`).

## Assumptions

- All three Requirements depend on the separate `ToolExecutor` cache deletion landing first. Do NOT implement until confirmed.

## Design decisions

- If `tool_cache_ttl` survives for other purposes after cache removal, keep it but remove only `tool_cache_max_size`.
- If both survive for other purposes, remove only the validator and its wiring, keeping the fields.

## Alternatives considered

- Keep the validator and accept type-check errors when `tool_cache_max_size` is removed: rejected because it creates a broken invariant.
- Add try/except around the validator: rejected because it masks the root cause — the validator should not exist after field removal.

## Implementation

### Target files

- `scripts/agent/services/config_validators.py`
- `scripts/agent/config_dataclasses.py`

### Procedure

#### Phase 1: Preparation

```bash
# PREREQUISITE CHECK — MUST PASS BEFORE proceeding:
rg "apply_config\(\*, cache_ttl" scripts/shared/tool_executor.py
# Expected: NO MATCHES

rg "_cache_ttl\|_cache\|stat_cache_hits\|_execute_with_cache" scripts/shared/tool_executor.py
# Expected: NO MATCHES
```

If either check shows remaining cache code, STOP. Wait for the prerequisite change.

#### Phase 2: Core Logic

**Step A: Delete `validate_tool_cache_max_size` from `config_validators.py`**

Current code (lines 139–143):
```python
def validate_tool_cache_max_size(cfg: ToolConfig) -> None:
    """Validate that tool_cache_max_size is non-negative."""
    if cfg.tool_cache_max_size < 0:
        raise ValueError(
            f"tool_cache_max_size must be >= 0, got {cfg.tool_cache_max_size}"
        )
```

After change: delete these 5 lines entirely.

**Step B: Remove `_v_tool_cms` import and `__post_init__` call from `config_dataclasses.py`**

Current code (line 91):
```python
    validate_tool_cache_max_size as _v_tool_cms,
```

After change: delete this line.

Current code (line 235):
```python
        _v_tool_cms(self)
```

After change: delete this line.

**Step C: Remove `tool_cache_ttl` and `tool_cache_max_size` fields from `ToolConfig`**

Current code (approximate location — must verify at runtime):
```python
@dataclass
class ToolConfig:
    """Tool execution, caching, approval policy, and prompt settings."""

    tool_cache_ttl: float = 300.0
    # LRU eviction when exceeded; 0 = unlimited
    tool_cache_max_size: int = 200
    # Forces build_execution_groups() to emit one sequential phase per call (in
    # ... rest unchanged
```

After change:
```python
@dataclass
class ToolConfig:
    """Tool execution, approval policy, and prompt settings."""

    # tool_cache_ttl and tool_cache_max_size removed — TTL cache deleted from ToolExecutor
    # Forces build_execution_groups() to emit one sequential phase per call (in
    # ... rest unchanged
```

Also update `factory.py` (line 302):
```python
        cache_max_size=ctx.cfg.tool.tool_cache_max_size,
```
→ Delete or replace with appropriate value based on whether cache still exists.

Also update `config_builders.py` (lines 278, 309):
```python
    tool_cache_max_size = _get_int_or_default(cfg, "tool_cache_max_size", 200)
    # ...
    tool_cache_max_size=tool_cache_max_size,
```
→ Delete or replace based on whether cache still exists.

#### Phase 3: Deployment & Verification

- Run: `grep -rn "tool_cache_max_size\|_v_tool_cms" scripts/`
- Expected: 0 matches.
- Run: `python -c "from agent.config_dataclasses import ToolConfig; ToolConfig()"`
- Expected: succeeds without error.

### Details

- **REQ-001**: Delete `validate_tool_cache_max_size` from `config_validators.py`.
- **REQ-002**: Delete `_v_tool_cms` import and `__post_init__` call from `config_dataclasses.py`.
- **REQ-003**: Delete `tool_cache_ttl`/`tool_cache_max_size` fields from `ToolConfig` (requires cache deletion prerequisite).

### Prerequisite verification checklist

Before implementing any step:

- [ ] `rg "apply_config\(\*, cache_ttl" scripts/shared/tool_executor.py` returns NO matches
- [ ] `rg "_cache_ttl\|_cache\|stat_cache_hits\|_execute_with_cache" scripts/shared/tool_executor.py` returns NO matches
- [ ] Confirm with reviewer that cache deletion PR has landed

## Compatibility considerations

- No API changes — removal of dead code path.
- `ToolConfig()` construction will no longer have `tool_cache_ttl`/`tool_cache_max_size` defaults.
- Consumers passing these fields to config builders will need updating (separate concern).

## Security considerations

- None — removal of dead code path.

## Rollback considerations

- Revert: restore original files.
- Git ref-safe rollback: `git checkout HEAD -- scripts/agent/services/config_validators.py scripts/agent/config_dataclasses.py`.
- No database migration or config file changes.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| Repository | Static check | `grep -rn "tool_cache_max_size\|_v_tool_cms" scripts/` | 0 matches |
| Repository | Smoke test | `python -c "from agent.config_dataclasses import ToolConfig; ToolConfig()"` | Succeeds without error |

## Completion criteria

- [ ] `validate_tool_cache_max_size` removed from `config_validators.py`.
- [ ] `_v_tool_cms` import removed from `config_dataclasses.py`.
- [ ] `_v_tool_cms(self)` call removed from `ToolConfig.__post_init__`.
- [ ] `tool_cache_ttl`/`tool_cache_max_size` fields removed from `ToolConfig`.
- [ ] No references to `tool_cache_max_size` or `_v_tool_cms` remain in repo.
- [ ] `ToolConfig()` constructs successfully.
- [ ] Prerequisite cache deletion verified before implementation.

## Out of scope

- Changes to `validate_*` function contents (other than this validator).
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
- **Source issue**: issues/20260825_config_validators_dead_cache_validator_issue.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-142646_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-08-25 22:43:56
- **Related target files**: scripts/agent/services/config_validators.py, scripts/agent/config_dataclasses.py
