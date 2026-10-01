# Implementation Procedure: Add regression tests for _wrap_validation_errors cross-product bug

## Goal

Add regression tests to `tests/tools/test_check_canonical_source_conflicts.py` that verify `_wrap_validation_errors` does not produce cross-product findings across entries.

## Scope

- Modify only `tests/tools/test_check_canonical_source_conflicts.py`.
- In-Scope: Adding a test class `TestWrapValidationErrorsCrossProduct` with two regression tests; ensuring existing tests still pass after the fix.
- Out-of-Scope: Fixing `_wrap_validation_errors` (REQ-001); updating TOOL_DESCRIPTIONS.md (REQ-003).

## Assumptions

- The `_entry` helper function exists in the test file and can be used to construct `RegistryEntry` objects.
- The `_wrap_validation_errors` function is importable from `tools.check_canonical_source_conflicts`.
- After REQ-001 is implemented, these tests should transition from failing to passing.

## Design decisions

- **Approach**: Add a new test class `TestWrapValidationErrorsCrossProduct` with two tests: one for a single exempt single-path entry (should produce no CANONICAL-006), and one for multiple entries x multiple errors (should produce exactly one finding for the violating entry only).
- **Alternative considered**: Adding tests to an existing test class — rejected because a dedicated class makes the regression purpose clear and avoids polluting unrelated test groups.

## Alternatives considered

- Add tests to an existing test class: rejected — a dedicated class makes the regression purpose clear.
- Test all CANONICAL-002 through CANONICAL-005 branches: rejected — the plan specifies testing CANONICAL-006 as the primary example; other branches follow the same pattern.

## Implementation

### Target file

`tests/tools/test_check_canonical_source_conflicts.py`

### Procedure

1. Add the `TestWrapValidationErrorsCrossProduct` test class with two regression tests.
2. Verify existing tests still pass after the fix.

### Method

Edit `tests/tools/test_check_canonical_source_conflicts.py` in-place using targeted edits.

### Details

**Phase 1: Add regression tests**

Append the following test class to the end of the file:

```python
# -----------------------------------------------------------------------
# Regression tests for _wrap_validation_errors cross-product bug
# -----------------------------------------------------------------------


class TestWrapValidationErrorsCrossProduct:
    """Regression tests for _wrap_validation_errors cross-product bug."""

    def test_single_exempt_entry_no_false_positive(self) -> None:
        """A single exempt single-path entry must not produce CANONICAL-006."""
        entry = _entry(
            decision_target="eventbus.core-behavior",
            claim_type="runtime-behavior",
            source_paths=["scripts/eventbus/"],
        )
        # Simulate the validation error that would be generated for this entry
        # if the validator incorrectly flagged it
        errors = [
            "multiple source_paths (1) for claim_type 'runtime-behavior' "
            "on entry targeting 'eventbus.core-behavior': "
            "only 'runtime-behavior' allows multiple sources"
        ]
        conflicts = _wrap_validation_errors(errors, [entry])
        # After fix: no findings because the error doesn't refer to this entry
        # (the error text says "1 source_path" which doesn't match CANONICAL-006 pattern)
        assert len(conflicts) == 0

    def test_multi_entries_multi_errors_no_cross_product(self) -> None:
        """Multiple entries x multiple errors must not produce cross-product findings."""
        entry_a = _entry(
            decision_target="eventbus.core-behavior",
            claim_type="runtime-behavior",
            source_paths=["scripts/eventbus/"],
        )
        entry_b = _entry(
            decision_target="eventbus.persistence-schema",
            claim_type="database-schema",
            source_paths=["scripts/db/schema_sql.py", "scripts/eventbus/db.py"],
        )
        errors = [
            "multiple source_paths (2) for claim_type 'database-schema' "
            "on entry targeting 'eventbus.persistence-schema': "
            "only 'runtime-behavior' allows multiple sources"
        ]
        conflicts = _wrap_validation_errors(errors, [entry_a, entry_b])
        # After fix: exactly one finding for entry_b only
        assert len(conflicts) == 1
        assert conflicts[0].code == "CANONICAL-006"
        assert conflicts[0].affected_files == ["scripts/db/schema_sql.py", "scripts/eventbus/db.py"]
```

**Phase 2: Verify existing tests still pass**

After REQ-001 is implemented, run:

```bash
uv run pytest tests/tools/test_check_canonical_source_conflicts.py tests/tools/test_check_canonical_source_conflicts_routing.py -v --tb=short
```

Expected outcome: All tests pass, including the new regression tests.

## Compatibility considerations

- The fix reduces the number of false-positive findings reported by the conflict checker. Existing tests that rely on the current (buggy) behavior will need to be updated.
- The new regression tests are designed to fail on the current code and pass after the fix.

## Security considerations

N/A: test-only change; no security-sensitive surface.

## Rollback considerations

Remove the new regression test class.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/tools/test_check_canonical_source_conflicts.py` | Regression: single exempt entry no false positive | `uv run pytest tests/tools/test_check_canonical_source_conflicts.py::TestWrapValidationErrorsCrossProduct::test_single_exempt_entry_no_false_positive -v` | Pass (after REQ-001 fix) |
| `tests/tools/test_check_canonical_source_conflicts.py` | Regression: multi entries x multi errors no cross-product | `uv run pytest tests/tools/test_check_canonical_source_conflicts.py::TestWrapValidationErrorsCrossProduct::test_multi_entries_multi_errors_no_cross_product -v` | Pass (after REQ-001 fix) |
| All tests | Existing tests still pass | `uv run pytest tests/tools/test_check_canonical_source_conflicts.py tests/tools/test_check_canonical_source_conflicts_routing.py -v` | All pass |

## Completion criteria

- New regression tests fail on the current code and pass after the fix.
- Existing tests in `tests/tools/test_check_canonical_source_conflicts.py` and `tests/tools/test_check_canonical_source_conflicts_routing.py` pass.
- The test class name and method names clearly indicate the regression purpose.

## Out of scope

Fixing `_wrap_validation_errors` (REQ-001). Updating TOOL_DESCRIPTIONS.md (REQ-003). Resolving the `eventbus.persistence-schema` violation itself (canon002). Changing severity or blocking classification of CANONICAL codes unless required by the confirmed intent. Refactoring unrelated detection functions.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add regression test class | Pending | — | — | REQ-002 |
| 2 | Verify existing tests still pass | Pending | — | — | REQ-002 |

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
- **Requirement ID**: REQ-002 — fix CANONICAL-006 false positives in check_canonical_source_conflicts.py validation-error wrapping
- **Source issue**: N/A: no standalone requirement document is generated
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-223409_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-225322
- **Related target files**: tests/tools/test_check_canonical_source_conflicts.py
