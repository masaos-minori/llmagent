## Goal

Add unit tests for `check_status_value()` covering valid values, invalid values, and missing `status` field scenarios. REQ-007, REQ-008.

## Scope

- Add unit tests for `check_status_value()` with valid values (`stable`, `draft`)
- Add unit tests for `check_status_value()` with invalid values (`deprecated`, `superseded`, `stabel`)
- Add unit tests for `check_status_value()` with missing `status` field
- Add integration test confirming the check runs in `validate_file()` flow

## Assumptions

- The `check_status_value()` function exists in `tools/check_docs_structure.py` (produced by the companion implementation procedure document)
- Tests follow the existing pattern in `tests/tools/test_check_docs_structure.py` using `tmp_path` fixtures and `_write()` helper
- Error message format matches the style used in `TestSchemaComplianceEnums` tests (lines 94-142)

## Design decisions

- Use a new test class `TestCheckStatusValue` following the naming convention of existing classes (`TestSchemaComplianceRequiredFields`, `TestSchemaComplianceEnums`)
- Test each scenario independently: valid values, invalid values, missing field
- Integration test validates the full `validate_file()` path with schema parameter

## Alternatives considered

- Combine all scenarios into a single parametrized test: would reduce boilerplate but makes individual failure messages less clear
- Test against real documents in `docs/`: would be slower and fragile; tmp_path approach is deterministic

## Implementation
### Target file

`tests/tools/test_check_docs_structure.py`

### Procedure

1. Add import for `check_status_value`
2. Add `TestCheckStatusValue` class with unit tests
3. Add integration test class for `validate_file()` flow

### Method

#### Step 1: Add import

Add `check_status_value` to the imports at line 18-27:

Current:
```python
from tools.check_docs_structure import (
    MAX_SIZE,
    _build_basename_index,
    check_links,
    check_related_links,
    check_schema_compliance,
    check_size,
    check_unique_adr_ids,
    validate_file,
)
```

Change to:
```python
from tools.check_docs_structure import (
    MAX_SIZE,
    _build_basename_index,
    check_links,
    check_related_links,
    check_schema_compliance,
    check_size,
    check_status_value,
    check_unique_adr_ids,
    validate_file,
)
```

#### Step 2: Add `TestCheckStatusValue` class

Add after `TestSchemaComplianceEnums` class (after line 142):

```python
class TestCheckStatusValue:
    def test_missing_status_field_passes(self, tmp_path: Path) -> None:
        """REQ-002: Documents without a 'status' field pass validation (defaults to stable)."""
        content = _COMPLIANT_DOC.replace("area: agent\n", "")
        doc = _write(tmp_path / "example.md", content)
        data = yaml.safe_load(content.split("---")[1]) or {}
        assert check_status_value(doc, data) == []

    def test_status_stable_passes(self, tmp_path: Path) -> None:
        """REQ-003: Documents with 'status: stable' pass validation."""
        content = _COMPLIANT_DOC + "\nstatus: stable\n---\n\nBody.\n"
        doc = _write(tmp_path / "example.md", content)
        data = yaml.safe_load(content.split("---")[1]) or {}
        assert check_status_value(doc, data) == []

    def test_status_draft_passes(self, tmp_path: Path) -> None:
        """REQ-003: Documents with 'status: draft' pass validation."""
        content = _COMPLIANT_DOC + "\nstatus: draft\n---\n\nBody.\n"
        doc = _write(tmp_path / "example.md", content)
        data = yaml.safe_load(content.split("---")[1]) or {}
        assert check_status_value(doc, data) == []

    def test_status_invalid_is_flagged(self, tmp_path: Path) -> None:
        """REQ-004: Documents with invalid 'status' values report an error."""
        for invalid_value in ("deprecated", "superseded", "stabel"):
            content = _COMPLIANT_DOC + f"\nstatus: {invalid_value}\n---\n\nBody.\n"
            doc = _write(tmp_path / "example.md", content)
            data = yaml.safe_load(content.split("---")[1]) or {}
            issues = check_status_value(doc, data)
            assert len(issues) == 1
            assert invalid_value in issues[0]
            assert "not one of ['stable', 'draft']" in issues[0]
```

#### Step 3: Add integration test for `validate_file()` flow

Add after `TestValidateFileSchemaOptIn` class (after line 188):

```python
class TestValidateFileStatusIntegration:
    """REQ-008: Integration test confirming the check runs in `validate_file()` flow."""

    def test_validate_file_reports_invalid_status_without_schema_arg(self, tmp_path: Path) -> None:
        """Invalid status value is reported even when --schema is not passed explicitly,
        because check_status_value() is called unconditionally in validate_file()."""
        content = _COMPLIANT_DOC + "\nstatus: obsolete\n---\n\nBody.\n"
        doc = _write(tmp_path / "example.md", content)
        # No schema argument — check_status_value() should still catch it
        issues = validate_file(doc, expected_area=None, basename_index={})
        assert any("obsolete" in i for i in issues)

    def test_validate_file_accepts_valid_status(self, tmp_path: Path) -> None:
        """Valid status values are accepted in validate_file() flow."""
        for status_val in ("stable", "draft"):
            content = _COMPLIANT_DOC + f"\nstatus: {status_val}\n---\n\nBody.\n"
            doc = _write(tmp_path / "example.md", content)
            issues = validate_file(doc, expected_area=None, basename_index={})
            assert not any("status" in i for i in issues), f"Unexpected status issue for '{status_val}': {issues}"
```

## Compatibility considerations

- Tests use the same `_COMPLIANT_DOC` fixture as existing tests, ensuring consistency
- Error message assertions match the format produced by `check_status_value()` (e.g., `"not one of ['stable', 'draft']"`)

## Security considerations

N/A — test-only change.

## Rollback considerations

If tests fail due to mismatched error message format from `check_status_value()`:
- Update the assertion strings to match the actual output format
- Verify the production code's error message format first

## Validation plan

- Run: `uv run pytest tests/tools/test_check_docs_structure.py::TestCheckStatusValue -v`
- Run: `uv run pytest tests/tools/test_check_docs_structure.py::TestValidateFileStatusIntegration -v`
- All tests must pass

## Completion criteria

- `test_missing_status_field_passes` passes (REQ-002)
- `test_status_stable_passes` passes (REQ-003)
- `test_status_draft_passes` passes (REQ-003)
- `test_status_invalid_is_flagged` passes for all three invalid values (REQ-004)
- `test_validate_file_reports_invalid_status_without_schema_arg` passes (REQ-008)
- `test_validate_file_accepts_valid_status` passes (REQ-008)

## Out of scope

- Testing edge cases like empty string status value (covered by `test_status_invalid_is_flagged` since `""` is not in `["stable", "draft"]`)
- Testing cross-document status validation (out of scope per Plan)

## execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-007, REQ-008
- **Source issue**: issues/20260925-220411_gv002_valid_document_status_validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260925-222320_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260925-230040
- **Related target files**: tests/tools/test_check_docs_structure.py
