## Goal
Remove the two `production_mode=(ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION)`
computations and their `non_fatal_prefix=`/`view=` companion arguments at
both `retry_once_with_delay()` call sites, matching that function's new
signature.

## Scope
- **In-Scope**: the two `retry_once_with_delay(...)` call sites in
  `scripts/agent/startup_mcp_starter.py` — one inside the subprocess-start
  retry path, one inside `verify_health()`'s post-startup health-check retry
  path.
- **Out-of-Scope**: `_start_http_subprocess_once()`, `_verify_single_health()`
  (the functions passed as `fn` — confirmed by direct read to contain no
  `security_profile`/`production_mode` reference of their own).

## Assumptions
- Must execute together with (or after) row 7 (`retry_helper.py`)'s own
  signature change — if row 7 lands first, this file's calls would raise
  `TypeError` for `production_mode`/`non_fatal_prefix`/`view` being
  unexpected keyword arguments until this row also lands.

## Design decisions
- Remove all three now-obsolete keyword arguments (`production_mode`,
  `non_fatal_prefix`, `view`) at both call sites in the same edit, rather
  than removing them incrementally — partial removal would leave the file in
  a state that does not compile against row 7's new signature.

## Alternatives considered
- N/A: this row's change is a direct, mechanical consequence of row 7's
  signature change; no alternative approach was considered.

## Implementation
### Target file
`scripts/agent/startup_mcp_starter.py`

### Procedure
1. In the subprocess-start retry call (verified 2026-09-04, lines ~96-106),
   remove `production_mode=(ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION)`
   and `non_fatal_prefix=f"MCP subprocess {key!r} failed to start after retry:"`
   and `view=self._view`, keeping `fatal_prefix=...`.
2. In `verify_health()`'s retry call (verified 2026-09-04, lines ~145-154),
   remove the same three arguments, keeping `fatal_prefix=...`.
3. Remove the now-unused `from shared.mcp_config import SecurityProfile`
   import if no other reference to `SecurityProfile` remains in this file
   (re-check via `rg -n "SecurityProfile" scripts/agent/startup_mcp_starter.py`
   at execution time).

### Method
Direct `Edit` at the two call sites.

### Details
Current (verified 2026-09-04), first call site:
```python
result = await retry_once_with_delay(
    lambda: self._start_http_subprocess_once(key, cfg),
    delay=RETRY_DELAY_SEC,
    shutdown_event=self._shutdown_event,
    interrupt_msg=f"shutdown requested during startup retry delay for {key!r}",
    production_mode=(
        ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION
    ),
    fatal_prefix=f"{OutputTag.FATAL} MCP subprocess {key!r} failed to start after retry:",
    non_fatal_prefix=f"MCP subprocess {key!r} failed to start after retry:",
    view=self._view,
)
```
After:
```python
result = await retry_once_with_delay(
    lambda: self._start_http_subprocess_once(key, cfg),
    delay=RETRY_DELAY_SEC,
    shutdown_event=self._shutdown_event,
    interrupt_msg=f"shutdown requested during startup retry delay for {key!r}",
    fatal_prefix=f"{OutputTag.FATAL} MCP subprocess {key!r} failed to start after retry:",
)
```
Apply the identical pattern to the second call site inside `verify_health()`.

## Compatibility considerations
Directly coupled to row 7 — must land in the same overall Plan execution.

## Security considerations
None directly — mechanical consequence of row 7's hardening.

## Rollback considerations
Small, localized edit under version control; revert via `git revert` if
needed, together with row 7.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/startup_mcp_starter.py` | Unit + Integration | `uv run pytest tests/agent/test_startup.py -v` | Both `retry_once_with_delay()` call sites succeed with the new signature; MCP subprocess start/health-check failures always raise `RuntimeError` after retry |

## Completion criteria
Both call sites pass only `fn`, `delay`, `shutdown_event`, `interrupt_msg`,
and `fatal_prefix`; no `production_mode`/`SecurityProfile` reference remains
in this file.

## Out of scope
`_start_http_subprocess_once()`, `_verify_single_health()`'s own bodies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Must land together with row 7 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by row 22's own edit |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Documentation impact owned by `adrprodonly`, sequenced after this Plan lands |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/done/20260902-143333_localremoval_remove_local_mode_and_enforce_production_grade_policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-091417_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-090137
- **Related target files**: scripts/agent/startup_mcp_starter.py
