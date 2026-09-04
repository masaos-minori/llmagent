## Goal
Update `test_startup_validation_pipeline.py`'s profile fixtures and remove
its implicit dependency on `production_mode` being computed from
`security_profile`, matching rows 5/6/11's unconditional-severity edits.

## Scope
- **In-Scope**: `ctx.cfg.mcp.security_profile = "local"` (verified
  2026-09-04, line 70) and `ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION`
  (line 160). **Corrected 2026-09-04** (`code-implementation` Step 3
  adversarial verification, full file read): the actual blocking issue was
  `MODULE = "agent.startup"` (line 20) — stale from before the unrelated
  upstream refactor moved `audit_security_defaults`/`check_readiness`/
  `McpToolDiscoveryService`/`check_routing_drift`/`check_routing_safety_tiers`/
  `RagMaintenanceService` out of `agent.startup` and into
  `agent.startup_validation`. `test_skipped_live_routing_no_raise` and
  `test_validation_pipeline_reports_fatal_when_config_missing` both patch
  `f"{MODULE}.<symbol>"` and raised `AttributeError: <module 'agent.startup'>
  does not have the attribute 'audit_security_defaults'` at collection/
  patch time — unrelated to `security_profile` at all. Both tests also
  constructed a bare `StartupOrchestrator.__new__(...)` without setting
  `_validation_pipeline`/`_reporter`, pre-dating the `StartupValidationPipeline`
  extraction.
- **Out-of-Scope**: `test_validation_result_*` (lines 26-61, pure
  `StartupValidationResult` unit tests, no `agent.startup`/module-path
  dependency); `test_build_agent_config_requires_agent_toml()`,
  `test_check_routing_safety_tiers_context()` (unrelated to this row).

## Assumptions
- Must execute after rows 5, 6, and 11 land — this file tests
  `StartupValidationPipeline.check_services()` (row 5's target), which after
  row 5 no longer computes `production_mode` from `security_profile` at all;
  any test here asserting a WARNING-only outcome for the `"local"`-profile
  fixture (line 70) will fail once rows 6/11 make the underlying checks
  unconditionally FATAL.

## Design decisions
- Replace `ctx.cfg.mcp.security_profile = "local"` (line 70) with
  `ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION` — since
  `SecurityProfile.LOCAL` no longer exists (row 1) and there is only one
  valid profile, both fixtures at lines 70 and 160 become identical; if the
  surrounding tests exist specifically to compare Local-vs-Production
  outcomes, merge them into a single test per the now-single-profile reality
  (re-read full context at execution time to confirm which tests these lines
  belong to and their exact assertions).

## Alternatives considered
- Leaving line 70 as the raw string `"local"`: rejected — even though
  `MCPConfig.security_profile`'s type coercion (row 2/3) might still accept
  the string form in some code path, `"local"` should not appear anywhere in
  this Plan's post-landing test suite as a fixture value, since it no longer
  maps to any valid `SecurityProfile` member.

## Implementation
### Target file
`tests/agent/shared/test_startup_validation_pipeline.py`

### Procedure
1. Replace `ctx.cfg.mcp.security_profile = "local"` (line 70) with
   `ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION`.
2. Re-read the full test function containing line 70 and the full test
   function containing line 160 at execution time
   (`sed -n '1,220p' tests/agent/shared/test_startup_validation_pipeline.py`).
   If either test's purpose was to assert a Local-vs-Production behavioral
   difference (e.g. WARNING vs FATAL), merge the two tests into one
   reflecting the new unconditional-FATAL behavior, removing the now-
   redundant duplicate.
3. Confirm no other test in this file references `production_mode` as a
   keyword argument to `audit_security_defaults()`/`check_readiness()` (both
   signatures change in rows 6/11); update any such call site to drop the
   keyword argument.

### Method
Direct `Edit`, informed by a full read of the file at execution time (only
partial grep evidence gathered as of this document's creation).

### Details
Current (verified 2026-09-04, grep evidence only):
```python
# line 18
from shared.mcp_config import SecurityProfile
# line 70
ctx.cfg.mcp.security_profile = "local"
# line 160
ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION
```
Full surrounding context for lines 70 and 160 was not yet read as of this
document's creation — re-verify at execution time before editing, per Method
above.

## Compatibility considerations
Coupled to rows 5, 6, and 11 — must land after all three.

## Security considerations
None directly — test-only file.

## Rollback considerations
Multi-site edit within a single file, under version control; revert via
`git revert` if needed, together with rows 5/6/11.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/agent/shared/test_startup_validation_pipeline.py` | Unit | `uv run pytest tests/agent/shared/test_startup_validation_pipeline.py -v` | All tests pass against rows 5/6/11's unconditional-FATAL behavior; no test references `SecurityProfile.LOCAL` or a `"local"` string profile value |

## Completion criteria
No reference to `SecurityProfile.LOCAL` or the string `"local"` as a profile
value remains in this file; no call site passes `production_mode=` to
`audit_security_defaults()`/`check_readiness()`.

## Out of scope
Any test unrelated to `security_profile`/`production_mode`, confirmed at
execution time.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260904 | 20260904 | Root cause was `MODULE = "agent.startup"` (stale pre-refactor path), not `security_profile` alone — corrected to `"agent.startup_validation"`; wired a real `StartupValidationPipeline` into the two integration tests that previously used a bare `__new__()` orchestrator |
| 2 | Add or update tests per Validation plan | Completed | 20260904 | 20260904 | This row's target file is itself the test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260904 | 20260904 | ruff clean; 12 passed. Full-suite diff deferred to end of batch |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | N/A: test-only file |

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
- **Related target files**: tests/agent/shared/test_startup_validation_pipeline.py
