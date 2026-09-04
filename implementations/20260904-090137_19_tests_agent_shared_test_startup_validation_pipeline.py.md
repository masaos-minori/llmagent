## Goal
Update `test_startup_validation_pipeline.py`'s profile fixtures and remove
its implicit dependency on `production_mode` being computed from
`security_profile`, matching rows 5/6/11's unconditional-severity edits.

## Scope
- **In-Scope**: `ctx.cfg.mcp.security_profile = "local"` (verified
  2026-09-04, line 70) and `ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION`
  (line 160), plus any test asserting divergent FATAL/WARNING behavior
  between these two fixture setups.
- **Out-of-Scope**: any test in this file whose assertions are unrelated to
  severity gating (confirm at execution time by reading the full file, not
  yet inspected beyond the 3 grep matches).

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Coordinate with rows 5, 6, 11's own edits; full file read still needed at execution time |
| 2 | Add or update tests per Validation plan | Pending | — | — | This row's target file is itself the test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
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
