# Implementation Procedure: Exit-Code Regression Test for check_needs_confirmation_inventory.py

## Goal

Lock the exit-status decision in behavior by adding a regression test asserting the exit code matches the decision: warnings-only run → exit 0, ERROR-finding run → exit non-zero.

## Scope

Add a regression test in `tests/tools/test_check_needs_confirmation_inventory.py` that drives `main()` (or `report_and_exit()`) against synthetic issue sets and asserts the exit code for (a) WARNING-only findings and (b) an ERROR finding. Current 170-line test covers per-function issue counts only and never exercises `main()`'s return value.

## Assumptions

- The owner decision is recorded: warnings → exit 0 (detection mode), only ERROR findings cause failure.
- The existing test file uses tmp_path fixtures and calls functions directly rather than invoking `main()`.
- No additional files require modification beyond this single test file.

## Design decisions

- Use the existing tmp_path fixture pattern to create synthetic docs/ directories with controlled "Needs confirmation" markers.
- Drive `main()` (which returns an int) rather than `report_and_exit()` directly, since `main()` is the public entry point and its return value is what consumers observe.
- Test two scenarios: (a) WARNING-only findings → assert return == 0, (b) ERROR finding → assert return != 0.

## Alternatives considered

- Test `report_and_exit()` directly instead of `main()`: less realistic because consumers invoke `main()` via the console script. However, `report_and_exit()` is the internal function that determines the exit code, so testing it directly would also validate the core logic. The choice depends on whether the goal is to test the public API (`main()`) or the internal contract (`report_and_exit()`). Both are valid; `main()` is preferred for consumer-facing verification.

## Implementation

### Target file

`tests/tools/test_check_needs_confirmation_inventory.py`

### Procedure

1. Add a new test class `TestExitCodeBehavior` near the end of the file.
2. Implement two test methods:
   - `test_warnings_only_returns_zero`: Create a tmp_path with docs containing only WARNING-level findings (untracked inline markers), drive `main()`, assert return == 0.
   - `test_error_finding_returns_nonzero`: Create a tmp_path with docs containing an ERROR-level finding (declared field count mismatch), drive `main()`, assert return != 0.
3. Ensure the test does not depend on the real docs/ directory — use isolated tmp_path fixtures.

### Method

Append a new test class to the existing test file. Follow the existing tmp_path fixture pattern used by `TestUntrackedInlineMarkers` and `TestGovernanceDocMarkerClassification`.

### Details

**Proposed additions to the test file:**

```python
class TestExitCodeBehavior:
    """Verify main()'s exit-code contract: warnings → 0, ERROR → non-zero."""

    def test_warnings_only_returns_zero(self, tmp_path: Path) -> None:
        """A run yielding only WARNING findings must return exit code 0."""
        # Set up a minimal inventory doc with NO open NC items
        # (so check_missing_nc_fields produces no issues)
        # and a domain doc with an untracked inline marker
        # (so check_untracked_inline_markers produces a WARNING).
        docs_dir = tmp_path / "docs"
        _write(
            docs_dir,
            "governance_03_issue-and-uncertainty-management.md",
            "## Part 2:\n#### NC-1\n**Status:** resolved\n**Source File:** `example.md`\n",
        )
        _write(
            docs_dir,
            "05_agent_example.md",
            "Needs confirmation: is this value correct?\n",
        )
        # Replace INVENTORY_DOC_PATH with our temp path
        import tools.check_needs_confirmation_inventory as mod
        orig_path = mod.INVENTORY_DOC_PATH
        try:
            mod.INVENTORY_DOC_PATH = docs_dir / "governance_03_issue-and-uncertainty-management.md"
            result = mod.main()
            assert result == 0, f"Expected exit code 0 for WARNING-only findings, got {result}"
        finally:
            mod.INVENTORY_DOC_PATH = orig_path

    def test_error_finding_returns_nonzero(self, tmp_path: Path) -> None:
        """A run yielding an ERROR finding must return a non-zero exit code."""
        # Set up a minimal inventory doc with NO open NC items
        # and a domain doc declaring 'following eleven fields' with fewer items
        # (so check_declared_field_count produces an ERROR).
        docs_dir = tmp_path / "docs"
        _write(
            docs_dir,
            "governance_03_issue-and-uncertainty-management.md",
            "## Part 2:\n#### NC-1\n**Status:** resolved\n**Source File:** `example.md`\n",
        )
        _write(
            docs_dir,
            "05_agent_example.md",
            "The following eleven fields are required:\n1. Field A\n2. Field B\n",
        )
        import tools.check_needs_confirmation_inventory as mod
        orig_path = mod.INVENTORY_DOC_PATH
        try:
            mod.INVENTORY_DOC_PATH = docs_dir / "governance_03_issue-and-uncertainty-management.md"
            result = mod.main()
            assert result != 0, f"Expected non-zero exit code for ERROR finding, got {result}"
        finally:
            mod.INVENTORY_DOC_PATH = orig_path
```

## Compatibility considerations

- The test uses the same `_write` helper already defined in the file.
- The test temporarily replaces `INVENTORY_DOC_PATH` to avoid depending on the real docs/ directory. This is consistent with the existing tmp_path fixture pattern.
- The test does not modify any production code.

## Security considerations

- No security impact: this is a test addition only.

## Rollback considerations

- Remove the added test class via git checkout if the classification is disputed.
- The rollback restores the original test file without the exit-code assertions.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/tools/test_check_needs_confirmation_inventory.py` | Unit: assert `main()` return codes for WARNING-only and ERROR-finding inputs | `uv run pytest tests/tools/test_check_needs_confirmation_inventory.py::TestExitCodeBehavior` | WARNING-only → 0; ERROR → non-zero |

## Completion criteria

- The new test class `TestExitCodeBehavior` exists with both test methods.
- `uv run pytest tests/tools/test_check_needs_confirmation_inventory.py::TestExitCodeBehavior` passes.
- The test does not depend on the real docs/ directory (uses isolated tmp_path fixtures).

## Out of scope

- Changing the checker's warning messages or severity levels.
- Resolving the actual orphaned markers themselves.
- Changing inventory entry format.
- Altering `report_and_exit()` logic or any other checker function.
- Modifying CI configuration files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add exit-code regression test for WARNING-only scenario | Pending | — | — | REQ-003 |
| 2 | Add exit-code regression test for ERROR-finding scenario | Pending | — | — | REQ-003 |
| 3 | Verify test passes with pytest | Pending | — | — | AC-003 |

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
- **Source issue**: issues/20261002-155701_ncinv002_exit_status_for_untracked_markers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261003-144238_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261003-155827
- **Related target files**: tests/tools/test_check_needs_confirmation_inventory.py
