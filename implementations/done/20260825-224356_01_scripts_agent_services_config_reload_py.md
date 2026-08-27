## Goal

Split `_reload_approval_settings()` in `scripts/agent/services/config_reload.py` into four independent helpers aligned with their actual responsibilities: `_reload_tool_allowlist()`, `_reload_memory_runtime()`, `_reload_security_profile()`, and keep `_reload_approval_config()` unchanged. Replace the single call site in `apply_config_dict()` with four explicit calls. Pure refactoring — no behavioral change.

## Scope

**In-Scope**:
- `scripts/agent/services/config_reload.py`: extract three new helpers (`_reload_tool_allowlist`, `_reload_memory_runtime`, `_reload_security_profile`), remove `_reload_approval_settings`, update `apply_config_dict()` call site.

**Out-of-Scope**:
- Any change to which fields are hot-reloadable.
- Changes to field update logic itself (only function boundaries/names).
- Adding `gitops_push_blocked` (tracked separately as `issues/20260825_cfgreload_gitops_push_blocked_not_reloadable_issue`).

## Assumptions

- No implicit ordering dependency between `apply_config_dict()` steps; each helper reads/writes fields isolated from others.
- The call site in `apply_config_dict()` is the only caller of `_reload_approval_settings` (confirmed via grep).

## Design decisions

- Each new helper follows the same signature pattern as `_reload_approval_config(self, ctx: AgentContext, new_cfg: dict[str, Any]) -> None`.
- Field update logic (`_get_bool` / `_get_list` / `_get_int` / `_get_str` diff-apply) is ported verbatim.
- Call order in `apply_config_dict()` preserves the pre-split execution order: approval → tool → memory → security.

## Alternatives considered

- Keep `_reload_approval_settings` as a thin wrapper delegating to four helpers: rejected because the call site is unique (`apply_config_dict()`) and a wrapper adds indirection without benefit.
- Inline all four groups directly inside `apply_config_dict()`: rejected because it would increase cyclomatic complexity of `apply_config_dict()` and reduce testability of individual reload paths.

## Implementation

### Target file

`scripts/agent/services/config_reload.py`

### Procedure

1. Add `_reload_tool_allowlist(self, ctx, new_cfg)` — handles `allowed_tools` field.
2. Add `_reload_memory_runtime(self, ctx, new_cfg)` — handles `memory_retention_days` and `memory_local_only` fields.
3. Add `_reload_security_profile(self, ctx, new_cfg)` — handles `security_profile` and `security_lockdown_enabled` fields.
4. In `apply_config_dict()` (line ~122), replace `self._reload_approval_settings(ctx, new_cfg)` with four explicit calls in order: `_reload_approval_config`, `_reload_tool_allowlist`, `_reload_memory_runtime`, `_reload_security_profile`.
5. Delete `_reload_approval_settings` method entirely.

### Method

```python
# --- Phase 2: Core Logic Implementation ---

# 1. _reload_tool_allowlist (REQ-001)
def _reload_tool_allowlist(
    self,
    ctx: AgentContext,
    new_cfg: dict[str, Any],
) -> None:
    """Reload allowed_tools from new_cfg if present."""
    if (lst := _get_list(new_cfg, "allowed_tools")) is not None:
        ctx.cfg.tool.allowed_tools = list(lst)

# 2. _reload_memory_runtime (REQ-001)
def _reload_memory_runtime(
    self,
    ctx: AgentContext,
    new_cfg: dict[str, Any],
) -> None:
    """Reload memory runtime fields from new_cfg if present."""
    if (v := _get_int(new_cfg, "memory_retention_days")) is not None:
        ctx.cfg.memory.memory_retention_days = v
    if (vb := _get_bool(new_cfg, "memory_local_only")) is not None:
        ctx.cfg.memory.memory_local_only = vb

# 3. _reload_security_profile (REQ-001)
def _reload_security_profile(
    self,
    ctx: AgentContext,
    new_cfg: dict[str, Any],
) -> None:
    """Reload security profile fields from new_cfg if present."""
    if (vs := _get_str(new_cfg, "security_profile")) is not None:
        try:
            from shared.mcp_config import SecurityProfile
            ctx.cfg.mcp.security_profile = SecurityProfile(vs)
        except ValueError:
            pass  # invalid enum value — leave current
    if (vb := _get_bool(new_cfg, "security_lockdown_enabled")) is not None:
        ctx.cfg.mcp.security_lockdown_enabled = vb

# 4. Update apply_config_dict() call site (REQ-002)
# Line ~122: replace
#   self._reload_approval_settings(ctx, new_cfg)
# with
#   self._reload_approval_config(ctx, new_cfg)
#   self._reload_tool_allowlist(ctx, new_cfg)
#   self._reload_memory_runtime(ctx, new_cfg)
#   self._reload_security_profile(ctx, new_cfg)

# 5. Delete _reload_approval_settings method (REQ-003)
# Remove lines 447-469 entirely.
```

### Details

- `_reload_tool_allowlist`: ports lines 454-455 from `_reload_approval_settings`. Uses `_get_list` for typed list extraction.
- `_reload_memory_runtime`: ports lines 456-459. Two fields handled by two separate `_get_*` calls.
- `_reload_security_profile`: ports lines 461-469. Includes `from shared.mcp_config import SecurityProfile` inline import inside the method body (same as original).
- Call order in `apply_config_dict()`: `_reload_approval_config` → `_reload_tool_allowlist` → `_reload_memory_runtime` → `_reload_security_profile`. This matches the pre-split execution order.
- After removal, verify no references to `_reload_approval_settings` remain in `scripts/` or `tests/` (confirmed zero callers before this step).

## Compatibility considerations

- Public API (`ConfigReloadRequest`, `ConfigReloadOutcome`, `apply_config`, `apply_config_dict`) is unchanged.
- Internal method signatures match the existing `_reload_approval_config` pattern.
- No config schema changes; only internal routing of reload logic.

## Security considerations

- No new secrets, credentials, or auth paths introduced.
- `SecurityProfile` import remains guarded inside the method body (same as original).
- Invalid enum values still silently ignored (unchanged behavior).

## Rollback considerations

- Revert: restore `_reload_approval_settings` method body and revert `apply_config_dict()` call to single invocation.
- Git ref-safe rollback via `git checkout HEAD -- scripts/agent/services/config_reload.py`.
- No database migration or config file changes required.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/config_reload.py` | Unit | `uv run pytest tests/agent/services/test_config_reload*.py -v` | All existing tests green |
| Repository | Full suite | `uv run pytest` | No new failures |
| Repository | Type check | `uv run mypy scripts/` | No new errors |

## Completion criteria

- [ ] Three new helpers exist with correct signatures and field assignments matching original logic.
- [ ] `apply_config_dict()` calls all four helpers explicitly in the documented order.
- [ ] `_reload_approval_settings` does not appear anywhere in `scripts/` or `tests/`.
- [ ] Existing `config_reload` test suite passes without modification.
- [ ] `mypy scripts/` reports no new type errors.

## Out of scope

- Adding `gitops_push_blocked` field handling.
- Changing which fields are hot-reloadable.
- Modifying field update logic semantics.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Source issue**: issues/20260825_cfgreload_approval_settings_mixed_concerns_issue.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-141157_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-08-25 22:43:56
- **Related target files**: scripts/agent/services/config_reload.py
