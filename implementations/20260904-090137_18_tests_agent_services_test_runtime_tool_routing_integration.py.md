## Goal
Replace the single `SecurityProfile.LOCAL` construction in this integration
test with `SecurityProfile.PRODUCTION`.

## Scope
- **In-Scope**: the `ctx.cfg.mcp.security_profile = SecurityProfile.LOCAL`
  assignment (verified 2026-09-04, line 334).
- **Out-of-Scope**: the rest of this integration test file — confirmed by
  direct read/grep to contain exactly one `SecurityProfile` reference.

## Assumptions
- None beyond the Plan's own Assumptions section.

## Design decisions
- Change the value to `SecurityProfile.PRODUCTION` rather than removing the
  line — re-read the surrounding test at execution time to confirm the test
  does not specifically depend on Local-profile routing behavior; if the
  test's intent is generic (any valid profile), `PRODUCTION` is the correct
  replacement per row 2's new default.

## Alternatives considered
- Removing the assignment entirely, relying on `MCPConfig`'s new default
  (row 2): rejected — an explicit assignment documents intent for readers of
  this integration test and avoids an implicit dependency on the dataclass
  default's specific value.

## Implementation
### Target file
`tests/agent/services/test_runtime_tool_routing_integration.py`

### Procedure
Replace `ctx.cfg.mcp.security_profile = SecurityProfile.LOCAL` (line 334)
with `ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION`.

### Method
Direct `Edit`.

### Details
Current (verified 2026-09-04):
```python
ctx.cfg.mcp.security_profile = SecurityProfile.LOCAL
```
After:
```python
ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION
```

## Compatibility considerations
None: single-value test-fixture change.

## Security considerations
N/A: test-only file.

## Rollback considerations
Single-line edit under version control; revert via `git revert` if needed.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/agent/services/test_runtime_tool_routing_integration.py` | Integration | `uv run pytest tests/agent/services/test_runtime_tool_routing_integration.py -v` | Test passes; no reference to `SecurityProfile.LOCAL` remains |

## Completion criteria
No reference to `SecurityProfile.LOCAL` remains in this file.

## Out of scope
All other tests/fixtures in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | N/A | — | — | This row's target file is itself the test file |
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
- **Requirement ID**: REQ-001
- **Source issue**: issues/done/20260902-143333_localremoval_remove_local_mode_and_enforce_production_grade_policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-091417_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-090137
- **Related target files**: tests/agent/services/test_runtime_tool_routing_integration.py
