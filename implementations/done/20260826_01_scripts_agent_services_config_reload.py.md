# Implementation Procedure Output Template (Canonical)

## Goal
Remove wiring for `cache_ttl` in `ConfigReloadService` once `ToolExecutor` TTL cache is removed.

## Scope
- In-Scope: `scripts/agent/services/config_reload.py` — remove `tools.apply_config(cache_ttl=...)` block in `_sync_services()` and `_apply_float(..., "tool_cache_ttl", ...)` line in `_apply_tool_params()`.

## Assumptions
- Prerequisite: `ToolExecutor` TTL cache removal must be completed and verified.

## Design decisions
- If `ToolExecutor.apply_config` is kept for other parameters, keep the `"tools"` call but remove only the `cache_ttl` argument.

## Alternatives considered
- N/A

## Implementation
### Target file
`scripts/agent/services/config_reload.py`
### Procedure
1. **Verify prerequisite**: Check that `ToolExecutor` cache removal is complete using `rg "apply_config\(\*, cache_ttl" scripts/shared/tool_executor.py`.
2. **Modify `_sync_services()`**: Remove the `tools.apply_config(cache_ttl=...)` block. Ensure `result.applied.append("tools")` remains if other parameters are being applied via `apply_config`.
3. **Modify `_apply_tool_params()`**: Remove the `_apply_float(new_cfg, "tool_cache_ttl", ...)` line.
4. **Add regression test**: Add a test case to ensure `/reload` works correctly after the cache removal.
### Method
Code modification and testing.
### Details
- REQ-001: Modify `_sync_services()` in `scripts/agent/services/config_reload.py`.
- REQ-002: Modify `_apply_tool_params()` in `scripts/agent/services/config_reload.py`.
- REQ-003: Add regression tests for `/reload`.

## Compatibility considerations
- None.

## Security considerations
- None.

## Rollback considerations
- Revert changes to `scripts/agent/services/config_reload.py` via git.

## Validation plan
- Run `uv run pytest tests/agent/services/test_config_reload*.py -v` to confirm `/reload` works without error post-cache-removal.

## Completion criteria
- `scripts/agent/services/config_reload.py` no longer references `tool_cache_ttl`.
- `/reload` operation succeeds successfully in tests.

## Out of scope
- Removing `ToolExecutor` cache implementation itself.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-08-27 | 2026-08-27 | Adversarial verification confirmed: `rg cache_ttl scripts/agent/services/config_reload.py` returns no matches; `rg tools\.apply_config scripts/agent/services/config_reload.py` returns no matches. REQ-001 and REQ-002 were independently completed by `plans/done/20260826-120000_plan.md` (ToolExecutor cache removal). No code changes needed. |
| 2 | Add or update tests per Validation plan | Completed | 2026-08-27 | 2026-08-27 | No new tests required — existing tests pass without cache_ttl wiring. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-08-27 | 2026-08-27 | Validated below. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-08-27 | 2026-08-27 | N/A: no docs/00_index.md task-scope mapping for config_reload.py. |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: `issues/20260825_cfgreload_toolexutor_cache_wiring_issue.md`
- **Source requirement**: N/A
- **Source plan**: `plans/20260825-142436_plan.md`
- **Source implementation procedure**: N/A
- **Generated at**: 2026-08-26T12:00:00Z
- **Related target files**: `scripts/agent/services/config_reload.py`
