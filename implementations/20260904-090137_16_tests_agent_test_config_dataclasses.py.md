## Goal
Update `MCPConfig`'s default-profile test to expect `SecurityProfile.PRODUCTION`
instead of `SecurityProfile.LOCAL`, matching row 2's default-value change.

## Scope
- **In-Scope**: the test asserting `MCPConfig()`'s default `security_profile`
  (verified 2026-09-04, lines 301-307).
- **Out-of-Scope**: `test_string_profile_coerced_to_enum()` (lines 309-313) —
  unaffected, confirmed by direct read (asserts coercion of the still-valid
  `"production"` string, unrelated to the default value).

## Assumptions
- Must execute together with, or after, row 2's default-value change —
  otherwise this test would assert against the pre-edit default.

## Design decisions
- Rename the test from an implied "default is Local" name (verify exact
  current name at execution time via
  `grep -n "def test_" tests/agent/test_config_dataclasses.py | sed -n '/30[0-9]/p'`)
  to reflect "default is Production", keeping the same assertion structure.

## Alternatives considered
- None: this is a direct, 1:1 mirror of row 2's default-value change; no
  alternative approach considered.

## Implementation
### Target file
`tests/agent/test_config_dataclasses.py`

### Procedure
Update the default-profile test (verified 2026-09-04, lines 304-307) to
assert `SecurityProfile.PRODUCTION`.

### Method
Direct `Edit`.

### Details
Current (verified 2026-09-04):
```python
from shared.mcp_config import SecurityProfile

cfg = MCPConfig()
assert cfg.security_profile == SecurityProfile.LOCAL
```
After:
```python
from shared.mcp_config import SecurityProfile

cfg = MCPConfig()
assert cfg.security_profile == SecurityProfile.PRODUCTION
```
Re-confirm the exact enclosing test function name and line numbers via
`grep -n "SecurityProfile" tests/agent/test_config_dataclasses.py` at
execution time before editing.

## Compatibility considerations
Coupled to row 2 — must land together.

## Security considerations
N/A: test-only file.

## Rollback considerations
Single-assertion edit under version control; revert via `git revert` if
needed, together with row 2.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/agent/test_config_dataclasses.py` | Unit | `uv run pytest tests/agent/test_config_dataclasses.py -v` | `MCPConfig()`'s default `security_profile` test passes against `SecurityProfile.PRODUCTION` |

## Completion criteria
No test in this file asserts `SecurityProfile.LOCAL` as `MCPConfig()`'s
default.

## Out of scope
`test_string_profile_coerced_to_enum()` and all other tests in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Coordinate with row 2's own edit |
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
- **Requirement ID**: REQ-002
- **Source issue**: issues/done/20260902-143333_localremoval_remove_local_mode_and_enforce_production_grade_policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-091417_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-090137
- **Related target files**: tests/agent/test_config_dataclasses.py
