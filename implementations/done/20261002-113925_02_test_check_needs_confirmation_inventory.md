# Implementation Procedure: Add regression tests for governance doc marker classification

## Goal

Add regression tests to verify that the fix for detecting orphaned Needs Confirmation markers in governance docs does not produce false positives on definitional mentions. Specifically, test that a governance doc fixture with a definitional mention is not reported, while a status-cell marker is reported.

## Scope

- Add a new test class to `tests/tools/test_check_needs_confirmation_inventory.py` covering the governance doc marker classification scenario.

## Assumptions

- The `_entry` helper and `discover_md_files` infrastructure already exist in the test file and can be reused.
- The classification rule defined in the companion implementation procedure (for `tools/check_needs_confirmation_inventory.py`) will be available by the time these tests are written.

## Design decisions

- Create a dedicated test class `TestGovernanceDocMarkerClassification` following the existing naming convention (`TestGovernanceMetaDocsCurrency`, `TestUntrackedInlineMarkers`, `TestMissingNcFields`).
- Use `tmp_path` fixtures to isolate test data from the real repository.
- Test both positive (marker reported) and negative (definitional not reported) cases.

## Alternatives considered

- Extend the existing `TestUntrackedInlineMarkers` class — rejected because the governance-specific classification logic warrants a separate class with a clear name reflecting its purpose.
- Use parametrized tests — acceptable alternative but separate methods provide clearer error messages when individual assertions fail.

## Implementation

### Target file

`tests/tools/test_check_needs_confirmation_inventory.py`

### Procedure

1. Add a new test class `TestGovernanceDocMarkerClassification` to the test file.
2. Write two test methods:
   - `test_definitional_mention_not_reported`: A governance doc with a definitional mention of "Needs confirmation" should NOT be flagged as an untracked marker.
   - `test_status_cell_marker_reported`: A governance doc with a status-cell marker (e.g., "Needs Confirmation" in a table cell) SHOULD be flagged as an untracked marker.
3. Ensure existing tests continue to pass.

### Method

Following the existing test patterns in the file (using `tmp_path` fixtures and the `_write` helper), add the new test class after the existing classes. The test methods will:

1. Create a temporary directory under `tmp_path`.
2. Write a governance doc fixture with the appropriate content.
3. Call `check_untracked_inline_markers()` directly.
4. Assert the expected result (zero issues for definitional, one issue for marker).

### Details

```python
class TestGovernanceDocMarkerClassification:
    """Verify that the governance doc exemption distinguishes definitional
    mentions from unresolved-item markers."""

    def test_definitional_mention_not_reported(self, tmp_path: Path) -> None:
        """A governance doc discussing the 'Needs confirmation' label itself
        must not be flagged as having an untracked marker."""
        docs_dir = tmp_path / "docs"
        _write(
            docs_dir,
            "governance_01_documentation-policy.md",
            "The Needs confirmation label indicates an item requiring review.\n"
            "See the Needs confirmation Inventory for details.\n",
        )
        files = discover_md_files(docs_dir, prefix="")
        issues = check_untracked_inline_markers(docs_dir, files, entries=[])
        assert issues == []

    def test_status_cell_marker_reported(self, tmp_path: Path) -> None:
        """A governance doc with a status-cell marker (Needs Confirmation in
        a table cell) must be flagged as an untracked marker."""
        docs_dir = tmp_path / "docs"
        _write(
            docs_dir,
            "governance_01_documentation-policy.md",
            "| Field | Value |\n"
            "| --- | --- |\n"
            "| Status | Needs Confirmation |\n",
        )
        files = discover_md_files(docs_dir, prefix="")
        issues = check_untracked_inline_markers(docs_dir, files, entries=[])
        assert len(issues) == 1
        assert issues[0].severity == "WARNING"
        assert "untracked" in issues[0].message.lower()
```

## Compatibility considerations

- This is a test-only change. No production code is modified.
- The test class follows the existing naming convention and uses the same `_write` helper and `tmp_path` fixture pattern as other test classes in the file.
- Imports (`_GOVERNANCE_META_DOCS`, `INVENTORY_DOC_PATH`, `NcEntry`, `check_missing_nc_fields`, `check_untracked_inline_markers`, `discover_md_files`) are already present in the file's import block.

## Security considerations

- No security impact. This is a test-only change.

## Rollback considerations

- Remove the `TestGovernanceDocMarkerClassification` class from the test file.
- No production code changes to revert.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/tools/test_check_needs_confirmation_inventory.py` | Regression tests | `uv run pytest tests/tools/test_check_needs_confirmation_inventory.py::TestGovernanceDocMarkerClassification -v --tb=short` | All pass |
| Full test suite | Existing tests still pass | `uv run pytest tests/tools/test_check_needs_confirmation_inventory.py -v --tb=short` | All pass |

## Completion criteria

- New regression tests fail before and pass after the change.
- Existing tests continue to pass.
- Tests cover both positive (marker reported) and negative (definitional not reported) cases.

## Out of scope

- Adding tests for edge cases beyond the two core scenarios (definitional mention, status-cell marker).
- Modifying the production checker tool (handled by the companion implementation procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add TestGovernanceDocMarkerClassification class | Completed | 20261002-155928 | 20261002-155928 | REQ-003 |
| 2 | Validate: run tests | Completed | 20261002-155928 | 20261002-155928 | REQ-003 |

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
- **Source issue**: issues/20261001-103602_ncinv001_detect-orphaned-needs-confirmation-markers-in-governance-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261002-070708_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261002-113925
- **Related target files**: tests/tools/test_check_needs_confirmation_inventory.py