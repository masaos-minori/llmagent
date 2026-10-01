# Implementation Procedure: Fix _wrap_validation_errors error-to-entry mapping

## Goal

Fix `_wrap_validation_errors()` in `tools/check_canonical_source_conflicts.py` so that each finding is reported only for the Registry entry that caused the validation error, eliminating cross-product duplication of findings across entries.

## Scope

- Modify only `tools/check_canonical_source_conflicts.py`.
- In-Scope: Adding Decision Target matching logic to `_wrap_validation_errors` to skip errors that don't refer to the current entry; documenting the behavior of non-validation detection functions when validation errors exist; documenting the exit status behavior.
- Out-of-Scope: Adding regression tests (REQ-002); updating TOOL_DESCRIPTIONS.md (REQ-003).

## Assumptions

- Each validation error string contains the Decision Target of the entry that caused it (e.g., `"multiple source_paths (2) for claim_type 'database-schema' on entry targeting 'eventbus.persistence-schema'"`).
- The CANONICAL-006 detection function (`detect_multiple_source_paths_violation`) already correctly filters per-entry; the bug is isolated to `_wrap_validation_errors`.
- The decision on running other detection functions alongside validation errors should be documented rather than changed without evidence.
- The checker exits 0 even though the registry validator exits 1 for the same Registry — this is intended because CANONICAL-006 is NON_BLOCKING.

## Design decisions

- **Approach**: Match each validation error to the entry it refers to by extracting the Decision Target from the error message and comparing it against each entry's `decision_target`. Only emit a finding if the error refers to that specific entry.
- **Alternative considered**: Validating per entry before calling `_wrap_validation_errors` — rejected because the validation errors are already aggregated at call time; the fix belongs in the wrapper.
- **Decision on detection functions with validation errors**: Document as intended behavior (return early on validation errors) until evidence shows otherwise. This avoids scope creep while preserving the current behavior.
- **Decision on exit status**: Document as intended behavior (CANONICAL-006 is NON_BLOCKING, so exit 0) until evidence shows otherwise.

## Alternatives considered

- Map each validation error to the entry it refers to (by matching the Decision Target carried in the error): adopted.
- Preserve existing CANONICAL codes, severities, and messages for true positives: adopted.
- Clarify, and either fix or document as intended, whether detection functions should also run when validation errors exist: documented as intended behavior.

## Implementation

### Target file

`tools/check_canonical_source_conflicts.py`

### Procedure

1. Add Decision Target matching logic to `_wrap_validation_errors` to skip errors that don't refer to the current entry.
2. Document the behavior of non-validation detection functions when validation errors exist.
3. Document the exit status behavior.

### Method

Edit `tools/check_canonical_source_conflicts.py` in-place using targeted edits.

### Details

**Phase 1: Write failing regression tests first** (see REQ-002)

```python
class TestWrapValidationErrorsCrossProduct:
    """Regression tests for _wrap_validation_errors cross-product bug."""

    def test_single_exempt_entry_no_false_positive(self) -> None:
        """A single exempt single-path entry must not produce CANONICAL-006."""
        entry = _entry(
            decision_target="eventbus.core-behavior",
            claim_type="runtime-behavior",
            source_paths=["scripts/eventbus/"],
        )
        errors = [
            "multiple source_paths (1) for claim_type 'runtime-behavior' "
            "on entry targeting 'eventbus.core-behavior': "
            "only 'runtime-behavior' allows multiple sources"
        ]
        conflicts = _wrap_validation_errors(errors, [entry])
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
        assert len(conflicts) == 1
        assert conflicts[0].code == "CANONICAL-006"
        assert conflicts[0].affected_files == ["scripts/db/schema_sql.py", "scripts/eventbus/db.py"]
```

**Phase 2: Fix `_wrap_validation_errors`**

Before:
```python
def _wrap_validation_errors(
    errors: list[str], entries: Sequence[RegistryEntry]
) -> list[CanonicalConflict]:
    """Convert M-01-04 validation errors into findings with CANONICAL-XXX codes."""
    conflicts: list[CanonicalConflict] = []
    for entry in entries:
        for err in errors:
            if "empty decision_target" in err:
                # ... create finding for this entry
            elif "empty claim_type" in err:
                # ... create finding for this entry
            # etc.
```

After:
```python
def _wrap_validation_errors(
    errors: list[str], entries: Sequence[RegistryEntry]
) -> list[CanonicalConflict]:
    """Convert M-01-04 validation errors into findings with CANONICAL-XXX codes."""
    conflicts: list[CanonicalConflict] = []
    for entry in entries:
        for err in errors:
            # Skip errors that don't refer to this entry
            if entry.decision_target and entry.decision_target not in err:
                continue
            if "empty decision_target" in err:
                # ... create finding for this entry
            elif "empty claim_type" in err:
                # ... create finding for this entry
            # etc.
```

Key change: Add `if entry.decision_target and entry.decision_target not in err: continue` before processing each error. This ensures each finding is only emitted for the entry that actually caused the error.

**Phase 3: Document behavior decisions**

Add docstring notes or inline comments to clarify:
1. When validation errors exist, `_run_detection_functions()` is NOT called (return early).
2. CANONICAL-006 is NON_BLOCKING, so the checker exits 0 even when the registry validator exits 1.

## Compatibility considerations

- The fix reduces the number of false-positive findings reported by the conflict checker. Existing tests that rely on the current (buggy) behavior will need to be updated.
- The decision to document (rather than change) the behavior of non-validation detection functions when validation errors exists preserves the current behavior until evidence shows otherwise.

## Security considerations

N/A: tooling-only change; no security-sensitive surface.

## Rollback considerations

Revert the `_wrap_validation_errors` change and remove the new regression tests.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tools/check_canonical_source_conflicts.py` | Format + lint | `uv run ruff format tools/check_canonical_source_conflicts.py` then `uv run ruff check tools/check_canonical_source_conflicts.py` | Clean (no diffs, no errors) |
| `tools/check_canonical_source_conflicts.py` | Type check | `uv run mypy tools/check_canonical_source_conflicts.py` | Pass |
| `tools/check_canonical_source_conflicts.py` | Security lint | `uv run bandit tools/check_canonical_source_conflicts.py` | No new findings |
| `tests/tools/test_check_canonical_source_conflicts.py` | Regression tests | `uv run pytest tests/tools/test_check_canonical_source_conflicts.py tests/tools/test_check_canonical_source_conflicts_routing.py -v` | All pass |
| Smoke run | Real Registry check | `uv run python tools/check_canonical_source_conflicts.py` | Reports CANONICAL-006 only for `eventbus.persistence-schema`, not for `eventbus.core-behavior` |

## Completion criteria

- Running the checker against the current Registry reports CANONICAL-006 only for `eventbus.persistence-schema`, not for `eventbus.core-behavior`.
- New regression tests fail on the current code and pass after the fix.
- Existing tests in `tests/tools/test_check_canonical_source_conflicts.py` and `tests/tools/test_check_canonical_source_conflicts_routing.py` pass.
- The decision on running other detection functions alongside validation errors is reflected in code and tests.

## Out of scope

Adding regression tests (REQ-002). Updating TOOL_DESCRIPTIONS.md (REQ-003). Resolving the `eventbus.persistence-schema` violation itself (canon002). Changing severity or blocking classification of CANONICAL codes unless required by the confirmed intent. Refactoring unrelated detection functions.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Write failing regression tests first | Pending | — | — | REQ-002 |
| 2 | Phase 2: Fix `_wrap_validation_errors` | Pending | — | — | REQ-001 |
| 3 | Phase 3: Validate | Pending | — | — | REQ-001 through REQ-003 |

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
- **Requirement ID**: REQ-001 — fix CANONICAL-006 false positives in check_canonical_source_conflicts.py validation-error wrapping
- **Source issue**: N/A: no standalone requirement document is generated
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-223409_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-225322
- **Related target files**: tools/check_canonical_source_conflicts.py
