## Goal
Update `_cfg()`'s default `security_profile` value and confirm
`TestSecurityProfileInvalidValue`'s existing invalid-value tests continue to
pass unmodified against row 3's fallback-string change.

## Scope
- **In-Scope**: `_cfg()`'s `defaults` dict's `"security_profile": "local"`
  entry (verified 2026-09-04, line 50).
- **Out-of-Scope**: `TestSecurityProfileInvalidValue`'s three tests (lines
  62-75) — confirmed by direct read to test `"INVALID_PROFILE"`, `""`, and
  `"123"`, none of which are `"local"`; these continue to raise `ValueError`
  unchanged by this Plan.

## Assumptions
- Must execute after row 3's fallback-string change lands — `_cfg()`'s
  `defaults` dict is passed through `build_agent_config()`, which (post-row-3)
  parses `security_profile` via `SecurityProfile(cfg.get("security_profile", "production"))`;
  an explicit `"local"` value in this dict would still resolve to a
  `ValueError` post-row-1 (since `"local"` is no longer a valid member),
  which would make every test using `_cfg()`'s defaults without an override
  fail at construction, not just the tests specifically about
  `security_profile`.

## Design decisions
- Change `_cfg()`'s default from `"local"` to `"production"` — this
  dictionary is the shared baseline every test in this file builds from via
  `{**defaults, **overrides}`, so it must resolve to a valid profile for any
  test not itself overriding `security_profile`.

## Alternatives considered
- Removing the `"security_profile"` key from `defaults` entirely, relying on
  row 3's own fallback default: rejected — `build_agent_config()`'s fallback
  only applies when the key is absent from the *raw* config dict passed to
  it; since `_cfg()`'s `defaults` dict does supply the key explicitly today,
  removing it changes what `build_agent_config()` receives (an absent key)
  versus what today's tests exercise (a present, valid key) — keeping the
  key present but valid is the minimal, behavior-preserving fix.

## Implementation
### Target file
`tests/agent/test_agent_negative_paths.py`

### Procedure
Replace `"security_profile": "local"` (line 50) with
`"security_profile": "production"`.

### Method
Direct `Edit`.

### Details
Current (verified 2026-09-04):
```python
"allowed_root": "",
"security_profile": "local",
"security_lockdown_enabled": False,
```
After:
```python
"allowed_root": "",
"security_profile": "production",
"security_lockdown_enabled": False,
```
`TestSecurityProfileInvalidValue`'s three tests (lines 62-75) require no
change — re-confirm at execution time via
`uv run pytest tests/agent/test_agent_negative_paths.py::TestSecurityProfileInvalidValue -v`
that they still pass unmodified after row 3 lands.

## Compatibility considerations
Coupled to row 3 — must land after it.

## Security considerations
None directly — test-only file.

## Rollback considerations
Single-line edit under version control; revert via `git revert` if needed.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/agent/test_agent_negative_paths.py` | Unit | `uv run pytest tests/agent/test_agent_negative_paths.py -v` | Every test in this file passes, including all tests relying on `_cfg()`'s defaults without a `security_profile` override |

## Completion criteria
No reference to the string `"local"` as a `security_profile` default value
remains in this file.

## Out of scope
`TestSecurityProfileInvalidValue` and every other test class in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Coordinate with row 3's own edit |
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
- **Requirement ID**: REQ-003
- **Source issue**: issues/done/20260902-143333_localremoval_remove_local_mode_and_enforce_production_grade_policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-091417_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-090137
- **Related target files**: tests/agent/test_agent_negative_paths.py
