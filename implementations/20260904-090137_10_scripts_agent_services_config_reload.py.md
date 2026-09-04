## Goal
Remove `security_profile`'s runtime-reload capability in
`ConfigReloadService`, since there is no longer a second value to reload
into once `SecurityProfile.LOCAL` is removed.

## Scope
- **In-Scope**: `scripts/agent/services/config_reload.py`'s
  `_reload_security_profile()` method, its call site, and the
  `FIELD_SECURITY_PROFILE` constant.
- **Out-of-Scope**: `_reload_security_profile()`'s handling of
  `FIELD_SECURITY_LOCKDOWN_ENABLED`/`security_lockdown_enabled` (a distinct,
  unrelated field currently reloaded by the same method) — must be preserved,
  relocated to wherever this method's caller now lives if the method itself
  is removed.

## Assumptions
- None beyond the Plan's own Assumptions section.

## Design decisions
- `_reload_security_profile()` currently reloads two distinct fields:
  `security_profile` (this Requirement's target) and
  `security_lockdown_enabled` (unrelated, out of scope). Rather than deleting
  the whole method, rename/repurpose it to reload only
  `security_lockdown_enabled`, removing just the `security_profile` block —
  preserves the unrelated field's reload capability without requiring a
  larger restructure of the caller (`_apply_field_changes()`'s call at line
  185).

## Alternatives considered
- Deleting `_reload_security_profile()` entirely and moving
  `security_lockdown_enabled`'s reload into a different existing method:
  rejected — larger, unrequested restructure; the security_profile-specific
  block can simply be removed from the existing method, leaving the
  lockdown-enabled logic and the method's (renamed) call site intact.

## Implementation
### Target file
`scripts/agent/services/config_reload.py`

### Procedure
1. Remove the `if (vs := _get_str(new_cfg, FIELD_SECURITY_PROFILE)) is not None: ...`
   block from `_reload_security_profile()` (verified 2026-09-04, lines
   670-681), keeping the `security_lockdown_enabled` block that follows it.
2. Rename the method to `_reload_security_lockdown()` (or similar, reflecting
   its now-narrower scope) and update its call site (line 185) and docstring
   accordingly.
3. Remove the now-unused `FIELD_SECURITY_PROFILE = "security_profile"`
   constant (line 90) if no other reference to it remains in this file
   (re-check via `rg -n "FIELD_SECURITY_PROFILE" scripts/agent/services/config_reload.py`
   at execution time).

### Method
Direct `Edit` at the 3 sites listed above.

### Details
Current (verified 2026-09-04):
```python
def _reload_security_profile(
    self,
    ctx: AgentContext,
    new_cfg: dict[str, Any],
) -> None:
    """Reload security profile fields from new_cfg if present."""
    if (vs := _get_str(new_cfg, FIELD_SECURITY_PROFILE)) is not None:
        try:
            from shared.mcp_config import SecurityProfile

            ctx.cfg.mcp.security_profile = SecurityProfile(vs)
        except ValueError:
            pass  # invalid enum value — leave current
    if (vb := _get_bool(new_cfg, FIELD_SECURITY_LOCKDOWN_ENABLED)) is not None:
        ctx.cfg.mcp.security_lockdown_enabled = vb
```
After:
```python
def _reload_security_lockdown(
    self,
    ctx: AgentContext,
    new_cfg: dict[str, Any],
) -> None:
    """Reload the security-lockdown-enabled field from new_cfg if present."""
    if (vb := _get_bool(new_cfg, FIELD_SECURITY_LOCKDOWN_ENABLED)) is not None:
        ctx.cfg.mcp.security_lockdown_enabled = vb
```
Update the call site (`self._reload_security_profile(ctx, new_cfg)` at line
185) to `self._reload_security_lockdown(ctx, new_cfg)`.

## Compatibility considerations
A `/reload` operation whose new config still sets `security_profile` will
now silently ignore that key (it is no longer read by this reload path) —
consistent with REQ-009's separate, unconditional-rejection handling at
startup config-load time; this row only removes the *runtime-reload*
capability, not startup-time validation (row 12 owns that).

## Security considerations
None directly — removes a runtime-mutable path for a field that no longer
has more than one valid value.

## Rollback considerations
Small, localized method edit under version control; revert via `git revert`
if needed.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/config_reload.py` | Unit | `uv run pytest tests/shared/test_config_hot_reload.py -v` | `/reload` no longer changes `security_profile` at runtime; `security_lockdown_enabled` reload still works |

## Completion criteria
No method in this file reloads `security_profile`; `security_lockdown_enabled`'s
reload capability is preserved under its renamed method.

## Out of scope
`security_lockdown_enabled`'s own semantics (only its reload mechanism is
relocated, not changed).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260904 | 20260904 | Verified exact match; removed `FIELD_SECURITY_PROFILE` constant |
| 2 | Add or update tests per Validation plan | Completed | 20260904 | 20260904 | Covered by row 14's own edit |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260904 | 20260904 | ruff/mypy clean; `test_config_hot_reload.py` 2 passed; `tests/agent/services/test_config_reload.py` 33/42 passed — 9 pre-existing unrelated failures confirmed via `git stash` (e.g. `_sync_services()` arg-count mismatch), left as-is |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | N/A: confirmed via `docs/00_index.md`'s Document References by Task table during code-implementation Step 5 — the only `mcp_config.py`-matching row covers `TransportType`/`StartupMode`/`HealthcheckMode`, not `SecurityProfile`; no changed file in this cycle has a matching task-scope row |

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/done/20260902-143333_localremoval_remove_local_mode_and_enforce_production_grade_policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-091417_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-090137
- **Related target files**: scripts/agent/services/config_reload.py
