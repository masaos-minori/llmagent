## Goal
Remove `TestSecurityProfile`'s Local-member tests, since `SecurityProfile.LOCAL`
no longer exists once row 1 lands.

## Scope
- **In-Scope**: `TestSecurityProfile`'s `test_local_value()` and
  `test_str_to_enum_local()` (verified 2026-09-04, lines 236-238, 246-248).
- **Out-of-Scope**: `test_production_value()`, `test_invalid_value_raises()`,
  `test_str_to_enum_production()` — all unaffected, confirmed by direct read.

## Assumptions
- Must execute together with, or after, row 1's enum-member removal —
  otherwise these tests still pass against the pre-edit enum and mask the
  fact that row 1 has not yet landed.

## Design decisions
- Delete the two Local-specific tests entirely rather than adapting them —
  once row 1 lands, `SecurityProfile.LOCAL` and `SecurityProfile("local")`
  both raise `AttributeError`/`ValueError` at class-definition/call time, so
  there is no meaningful assertion left to make about a "local" value; the
  removal itself is the correct regression signal (a stray reference would
  now fail collection).
- `test_invalid_value_raises()` (`SecurityProfile("invalid")` raises
  `ValueError`) already covers the post-removal behavior for a supplied
  `"local"` string querying the now-single-member enum — no new test needed;
  optionally extend this test to explicitly include `"local"` in a
  parametrized list alongside `"invalid"`, confirming it too now raises.

## Alternatives considered
- Repurposing `test_local_value()` to assert
  `with pytest.raises(AttributeError): SecurityProfile.LOCAL`: rejected —
  adds test noise for a case already covered by Python's own attribute-access
  semantics; not part of this Plan's public contract to verify.

## Implementation
### Target file
`tests/shared/test_mcp_config.py`

### Procedure
1. Remove `test_local_value()` (verified 2026-09-04, lines 236-238).
2. Remove `test_str_to_enum_local()` (verified 2026-09-04, lines 246-248).
3. Extend `test_invalid_value_raises()` to a parametrized test covering both
   `"invalid"` and `"local"` as inputs that now raise `ValueError`.

### Method
Direct `Edit` at the `TestSecurityProfile` class (lines 236-249).

### Details
Current (verified 2026-09-04):
```python
class TestSecurityProfile:
    def test_local_value(self) -> None:
        assert SecurityProfile.LOCAL == "local"

    def test_production_value(self) -> None:
        assert SecurityProfile.PRODUCTION == "production"

    def test_invalid_value_raises(self) -> None:
        with pytest.raises(ValueError):
            SecurityProfile("invalid")

    def test_str_to_enum_local(self) -> None:
        assert SecurityProfile("local") == SecurityProfile.LOCAL

    def test_str_to_enum_production(self) -> None:
        assert SecurityProfile("production") == SecurityProfile.PRODUCTION
```
After:
```python
class TestSecurityProfile:
    def test_production_value(self) -> None:
        assert SecurityProfile.PRODUCTION == "production"

    @pytest.mark.parametrize("value", ["invalid", "local"])
    def test_invalid_value_raises(self, value: str) -> None:
        with pytest.raises(ValueError):
            SecurityProfile(value)

    def test_str_to_enum_production(self) -> None:
        assert SecurityProfile("production") == SecurityProfile.PRODUCTION
```

## Compatibility considerations
None: test-only file, no production code impact.

## Security considerations
N/A: test-only file.

## Rollback considerations
Test-only edit under version control; revert via `git revert` if needed.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/shared/test_mcp_config.py` | Unit | `uv run pytest tests/shared/test_mcp_config.py -v` | No test references `SecurityProfile.LOCAL`; `SecurityProfile("local")` is confirmed to raise `ValueError` |

## Completion criteria
No test in this file references `SecurityProfile.LOCAL`.

## Out of scope
`test_production_value()`, `test_str_to_enum_production()`, and all other
test classes in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Coordinate with row 1's own edit |
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
- **Requirement ID**: REQ-001, REQ-011
- **Source issue**: issues/done/20260902-143333_localremoval_remove_local_mode_and_enforce_production_grade_policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-091417_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-090137
- **Related target files**: tests/shared/test_mcp_config.py
