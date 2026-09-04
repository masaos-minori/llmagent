## Goal
Remove `StartupValidationPipeline.check_services()`'s `production_mode`
computation and its threading into `audit_security_defaults()`/
`check_readiness()`, making their behavior unconditional.

## Scope
- **In-Scope**: `scripts/agent/startup_validation.py`'s
  `production_mode = ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION`
  computation and its two call-site usages.
- **Out-of-Scope**: `audit_security_defaults()`'s own body (row 11 owns
  `security_audit.py`); `check_readiness()`'s own body (row 6 owns
  `mcp_health.py`); the rest of `check_services()`'s pipeline stages (MCP
  tool discovery, routing drift, RAG consistency) — none reference
  `security_profile`/`production_mode`, confirmed by direct read.

## Assumptions
- This row's edit is coupled to rows 6 and 11: `audit_security_defaults()`
  and `check_readiness()` must drop their own `production_mode` parameters
  (or this row's calls must stop passing it) in the same overall Plan
  execution, or the signatures mismatch. Sequence this row after rows 6 and
  11 land, or coordinate the parameter removal across all three in the same
  cycle.

## Design decisions
- Remove the `production_mode` local variable entirely, along with the
  keyword argument at both call sites, rather than hardcoding
  `production_mode=True` — once rows 6 and 11 also drop the parameter from
  their own signatures, passing it here would be a `TypeError`; removing it
  here keeps this row's own diff minimal and consistent with the other REQ-005
  rows' "delete the conditional, not hardcode it" approach.

## Alternatives considered
- Hardcoding `production_mode=True` at this call site while leaving rows 6/11
  unedited: rejected — this Plan's own Requirements (REQ-005) require the
  called functions themselves to become unconditional, not merely always
  invoked with a fixed argument; leaving the parameter in place would be
  inconsistent with rows 6 and 11's own edits landing in the same cycle.

## Implementation
### Target file
`scripts/agent/startup_validation.py`

### Procedure
1. Remove the `production_mode = ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION`
   line (verified 2026-09-04, line 40) and its now-unnecessary
   `from shared.mcp_config import SecurityProfile` import (line 37) if no
   other reference to `SecurityProfile` remains in this file after the edit
   (re-check via `rg -n "SecurityProfile" scripts/agent/startup_validation.py`
   at execution time).
2. Remove the `production_mode=production_mode` keyword argument from the
   `audit_security_defaults(ctx, production_mode=production_mode)` call
   (line 45).
3. Remove the `production_mode=production_mode` keyword argument from the
   `check_readiness(ctx, production_mode=production_mode)` call (line 58).

### Method
Direct `Edit` at the 3-4 sites listed above.

### Details
Current (verified 2026-09-04):
```
from shared.mcp_config import SecurityProfile

ctx = self._ctx
production_mode = ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION
pipeline = StartupValidationResult()

# 1. Security audit
try:
    warnings = audit_security_defaults(ctx, production_mode=production_mode)
    ...
# 2. Service readiness
try:
    result = await check_readiness(ctx, production_mode=production_mode)
    ...
```
After: drop the `production_mode` variable and both keyword arguments,
calling `audit_security_defaults(ctx)` and `await check_readiness(ctx)`
instead — matching rows 11's and 6's own signature changes.

## Compatibility considerations
Coupled to rows 6 (`mcp_health.py`) and 11 (`security_audit.py`) — their
function signatures must drop `production_mode` in the same overall Plan
execution or this file's calls will raise `TypeError` for an unexpected
keyword argument.

## Security considerations
None directly — removes a relaxed-validation code path; net effect is a
security hardening (both called functions always enforce their strict
behavior after this change).

## Rollback considerations
Small, localized edit under version control; revert via `git revert` if
needed. Revert together with rows 6 and 11 if any of the three needs to be
undone, since their signatures are coupled.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/startup_validation.py` | Unit + Integration | `uv run pytest tests/agent/shared/test_startup_validation_pipeline.py -v` | `check_services()` calls `audit_security_defaults()`/`check_readiness()` without `production_mode`; both always enforce FATAL behavior |

## Completion criteria
No `SecurityProfile`/`production_mode` reference remains in
`scripts/agent/startup_validation.py`; `check_services()` calls both
downstream functions with their new, unconditional signatures.

## Out of scope
`audit_security_defaults()`'s own body (row 11); `check_readiness()`'s own
body (row 6); the rest of the validation pipeline's stages.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260904 | 20260904 | Also updated a stale ADR-004 comment referencing `production_mode` (line 68) |
| 2 | Add or update tests per Validation plan | Completed | 20260904 | 20260904 | Covered by row 19's own edit, executed in the same cycle |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260904 | 20260904 | ruff/mypy clean; implemented together with rows 6,7,8,11 (coupled cluster) — `tests/agent/shared/test_startup_validation_pipeline.py` 12 passed |
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
- **Requirement ID**: REQ-005
- **Source issue**: issues/done/20260902-143333_localremoval_remove_local_mode_and_enforce_production_grade_policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-091417_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-090137
- **Related target files**: scripts/agent/startup_validation.py
