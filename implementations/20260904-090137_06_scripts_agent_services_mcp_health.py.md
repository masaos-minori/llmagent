## Goal
Remove `check_readiness()`'s `production_mode` parameter and its gating of
the `RuntimeError` raise, making the raise unconditional on
`result.has_issues`.

## Scope
- **In-Scope**: `scripts/agent/services/mcp_health.py`'s `check_readiness()`
  function signature and body only.
- **Out-of-Scope**: `check_service_health()` (the function `check_readiness()`
  calls internally — confirmed by direct read to contain no
  `security_profile`/`production_mode` reference of its own).

## Assumptions
- Coupled to row 5 (`startup_validation.py`), the sole caller of
  `check_readiness()` (confirmed via `rg -rn "check_readiness" scripts/` —
  re-verify at execution time in case another caller was added since).

## Design decisions
- Remove the `production_mode` parameter entirely (default and all) rather
  than hardcoding it to `True` internally — keeps the function signature
  honest about what it now always does, consistent with this Plan's other
  REQ-005 rows.

## Alternatives considered
- Keeping `production_mode: bool = True` as a parameter with a changed
  default: rejected — a parameter that no caller may legitimately set to
  `False` anymore (per this Plan's Implementation intent) should not exist;
  keeping it invites a future regression where some caller re-introduces the
  relaxed path.

## Implementation
### Target file
`scripts/agent/services/mcp_health.py`

### Procedure
1. Remove the `*, production_mode: bool = False` parameter from
   `check_readiness()`'s signature.
2. Change `if production_mode and result.has_issues:` to
   `if result.has_issues:`.
3. Update the docstring to remove the "In development mode, behaves like
   check_service_health(): warnings only" sentence, since that mode no
   longer exists.

### Method
Direct `Edit`, anchored on the exact function body (verified 2026-09-04,
lines 95-112).

### Details
Current:
```python
async def check_readiness(
    ctx: AgentContext, *, production_mode: bool = False
) -> HealthCheckResult:
    """Probe required services at startup; raise in production mode on failure.

    In production mode, any failed health check raises RuntimeError listing
    which services are unavailable.
    In development mode, behaves like check_service_health(): warnings only.
    """
    result = await check_service_health(ctx)
    if production_mode and result.has_issues:
        error_msgs = [f"{w.label}: {w.message}" for w in result.warnings]
        msg = (
            "Startup readiness check failed (required services unavailable): "
            + "; ".join(error_msgs)
        )
        logger.error(msg)
        raise RuntimeError(msg)
    return result
```
After:
```python
async def check_readiness(ctx: AgentContext) -> HealthCheckResult:
    """Probe required services at startup; raise RuntimeError on failure."""
    result = await check_service_health(ctx)
    if result.has_issues:
        error_msgs = [f"{w.label}: {w.message}" for w in result.warnings]
        msg = (
            "Startup readiness check failed (required services unavailable): "
            + "; ".join(error_msgs)
        )
        logger.error(msg)
        raise RuntimeError(msg)
    return result
```

## Compatibility considerations
Coupled to row 5, `check_readiness()`'s sole caller — that row's call site
must drop the `production_mode=production_mode` keyword argument in the same
overall Plan execution.

## Security considerations
None directly — removes a relaxed-validation path; net effect is a security
hardening (any required-service failure now always aborts startup).

## Rollback considerations
Small, localized function edit under version control; revert via `git
revert` if needed, together with row 5.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/mcp_health.py` | Unit + Integration | `uv run pytest tests/agent/test_startup.py -v` | `check_readiness()` always raises `RuntimeError` when `result.has_issues` is true, regardless of any argument |

## Completion criteria
`check_readiness()` has no `production_mode` parameter; its `RuntimeError`
raise is unconditional on `result.has_issues`.

## Out of scope
`check_service_health()`'s own body.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Coordinate with row 5's call-site edit |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by row 22 (`tests/agent/test_startup.py`)'s own edit |
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
- **Related target files**: scripts/agent/services/mcp_health.py
