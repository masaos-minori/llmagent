## Goal
Remove the Local-profile test path (`test_local_enum_produces_warning`) and
add regression coverage confirming every violation is now an unconditional
error, matching row 4's edit to `ProductionConfigValidator`.

## Scope
- **In-Scope**: **Corrected 2026-09-04** (`code-implementation` Step 3
  adversarial verification): this row's scope was under-identified at
  plan-to-implementation-procedure time — the original scope named only
  `TestProductionConfigValidatorSecurityProfileEnum`'s
  `test_local_enum_produces_warning`/`test_production_enum_produces_error`,
  but 6 additional tests across 4 other classes also asserted the
  now-removed `security_profile="local"` → warning behavior:
  `TestProductionConfigValidatorStrictKeys.test_strict_key_false_produces_warning_in_local`,
  `.test_all_strict_keys_absent_produces_warnings_in_local`,
  `TestProductionConfigValidatorSafetyTiers.test_missing_safety_tier_produces_warning_in_local`,
  `.test_unknown_safety_tier_key_produces_warning_in_local`,
  `TestProductionConfigValidatorAllowedTools.test_allowed_tools_empty_produces_warning_in_local`,
  `TestProductionConfigValidatorApprovalRiskFloor.test_one_git_tool_medium_produces_warning_in_local`.
  All 8 (2 original + 6 newly found) are in scope.
- **Out-of-Scope**: every other test in this file (confirmed by direct read
  to assert `security_profile="production"` outcomes or unrelated
  behavior, unaffected by row 4's edit).

## Assumptions
- Must execute together with, or after, row 4's edit to
  `ProductionConfigValidator` lands — otherwise these tests would test
  against the pre-edit (still-conditional) behavior.

## Design decisions
- Delete `test_local_enum_produces_warning()` entirely rather than
  repurposing it — once row 4 lands, `security_profile=SecurityProfile.LOCAL`
  is no longer a constructible value (row 1 removes the enum member), so
  this test cannot be adapted, only removed.
- Extend `test_production_enum_produces_error()` to confirm the
  *unconditional* nature explicitly (assert `result.warnings == []` for the
  same violation).
- For the 6 newly-found `_in_local` tests (all pass the still-constructible
  string `security_profile="local"`, not the removed enum member): rename
  each to an `_error_even_with_local_profile` variant and flip its
  assertion from `result.warnings` to `result.errors`, plus an added
  `assert result.warnings == []` — these remain meaningful regression tests
  proving the string `"local"` no longer downgrades severity, rather than
  becoming redundant duplicates of their `_in_production` siblings, since
  they specifically guard against reintroducing profile-conditional
  behavior via the string path (which row 4 does not remove — only its
  effect is removed, see row 4's own Assumptions on `security_profile`
  remaining an inert parameter).

## Alternatives considered
- Keeping `test_local_enum_produces_warning()` but changing its assertion to
  expect a `ValueError` at construction time: rejected — that would test
  row 1's enum-removal behavior, which belongs to
  `tests/shared/test_mcp_config.py` (row 15), not this file's
  `ProductionConfigValidator`-focused test class.

## Implementation
### Target file
`tests/shared/test_production_config_validator.py`

### Procedure
1. Remove `test_local_enum_produces_warning()` (verified 2026-09-04, lines
   217-222).
2. Extend `test_production_enum_produces_error()` (lines 210-215) to also
   assert `result.warnings == []` for the same violation, confirming no
   downgrade path remains.
3. Add a new regression test constructing a config with multiple violation
   categories at once (strict-mode key false, unknown tool-safety-tier key,
   `allowed_tools=[]`) and asserting all become errors with zero warnings —
   covering row 4's full `_record()` simplification, not just the single
   `tool_definitions_strict` case the existing tests exercise.

### Method
Direct `Edit`/test addition, anchored on the existing
`TestProductionConfigValidatorSecurityProfile`-equivalent class (re-confirm
exact class name at execution time via `grep -n "^class " tests/shared/test_production_config_validator.py`).

### Details
Current (verified 2026-09-04):
```python
def test_production_enum_produces_error(self) -> None:
    config = {"tool_definitions_strict": False}
    result = ProductionConfigValidator().validate(
        config, security_profile=SecurityProfile.PRODUCTION
    )
    assert any("tool_definitions_strict" in err for err in result.errors)

def test_local_enum_produces_warning(self) -> None:
    config = {"tool_definitions_strict": False}
    result = ProductionConfigValidator().validate(
        config, security_profile=SecurityProfile.LOCAL
    )
    assert any("tool_definitions_strict" in warn for warn in result.warnings)
```
Remove the second test; add `assert result.warnings == []` to the first.

## Compatibility considerations
N/A: test-only file, no production code impact.

## Security considerations
N/A: test-only file.

## Rollback considerations
Test-only edit under version control; revert via `git revert` if needed.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/shared/test_production_config_validator.py` | Unit | `uv run pytest tests/shared/test_production_config_validator.py -v` | All tests pass against row 4's unconditional-error behavior; no test references `SecurityProfile.LOCAL` |

## Completion criteria
No test in this file references `SecurityProfile.LOCAL`; a new test confirms
multiple violation categories all become errors with zero warnings.

## Out of scope
`TestProductionConfigValidatorApprovalRiskFloor` and other unrelated test
classes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260904 | 20260904 | Adversarial verification found 6 additional `_in_local` tests beyond the 2 originally scoped — Scope/Design decisions corrected accordingly |
| 2 | Add or update tests per Validation plan | Completed | 20260904 | 20260904 | This row's target file is itself the test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260904 | 20260904 | ruff clean; 33 passed (up from 33 pre-existing minus 2 removed/renamed plus corrections). Full-suite diff deferred to end of batch |
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
- **Requirement ID**: REQ-011
- **Source issue**: issues/done/20260902-143333_localremoval_remove_local_mode_and_enforce_production_grade_policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-091417_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-090137
- **Related target files**: tests/shared/test_production_config_validator.py
