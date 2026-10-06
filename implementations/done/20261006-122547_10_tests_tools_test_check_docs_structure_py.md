## Goal

Add cases to `test_check_docs_structure.py`: body block at `##` and `###` levels reported; heading inside fenced code ignored; `related: []` accepted; invalid `related` format / missing target / self-reference / duplicate reported. (REQ-006 / AC-6)

## Scope

- Add test cases for:
  - Body block at `##` and `###` levels reported
  - Heading inside fenced code ignored
  - `related: []` accepted
  - Invalid `related` format / missing target / self-reference / duplicate reported

## Assumptions

- The existing test classes (schema, basename index, duplicates) provide a pattern to follow
- The strengthened tool behavior is the adopted policy

## Design decisions

- Follow the existing test class pattern in `tests/tools/test_check_docs_structure.py`
- Add test methods for each new case
- Use temporary files with appropriate content to test each case

## Alternatives considered

- Adding tests to an existing test class — rejected because a dedicated test class provides clearer ownership

## Implementation

### Target file

`tests/tools/test_check_docs_structure.py`

### Procedure

1. Add test class/method for body block at `##` and `###` levels
2. Add test for heading inside fenced code ignored
3. Add test for `related: []` accepted
4. Add tests for invalid `related` format / missing target / self-reference / duplicate

### Method

- Create a new test class following the pattern of existing test classes
- Add test methods for each new case
- Use temporary files with appropriate content

### Details

**New test class to add:**
```python
class TestCheckTailSectionsAnyLevel:
    """Tests for any-level body Related Documents detection."""

    def test_body_related_at_h2_level_reported(self) -> None:
        """Body ## Related Documents in non-ADR doc is reported."""
        content = "## Related Documents\n\n- `foo.md`\n"
        issues = check_tail_sections(Path("test.md"), content)
        assert len(issues) == 1
        assert "non-ADR document must not carry a body '## Related Documents' section" in issues[0]

    def test_body_related_at_h3_level_reported(self) -> None:
        """Body ### Related Documents in non-ADR doc is reported."""
        content = "### Related Documents\n\n- `foo.md`\n"
        issues = check_tail_sections(Path("test.md"), content)
        assert len(issues) == 1
        assert "non-ADR document must not carry a body '### Related Documents' section" in issues[0]

    def test_heading_inside_fenced_code_ignored(self) -> None:
        """Heading inside fenced code block is ignored."""
        content = '```\n## Related Documents\n```\n'
        issues = check_tail_sections(Path("test.md"), content)
        assert len(issues) == 0

    def test_adr_related_documents_required(self) -> None:
        """ADR doc requires ## Related Documents section."""
        content = "# Some ADR\n"
        issues = check_tail_sections(Path("docs/10_adr/ADR-001-test.md"), content)
        assert len(issues) == 1
        assert "missing '## Related Documents' section" in issues[0]
```

**New test class for related format validation:**
```python
class TestValidateRelatedFormat:
    """Tests for related: format validation."""

    def test_empty_list_accepted(self) -> None:
        """related: [] is accepted."""
        issues = _validate_related_format([])
        assert len(issues) == 0

    def test_valid_basename_accepted(self) -> None:
        """Valid basename ending in .md is accepted."""
        issues = _validate_related_format(["foo.md"])
        assert len(issues) == 0

    def test_invalid_extension_rejected(self) -> None:
        """Non-.md extension is rejected."""
        issues = _validate_related_format(["foo.txt"])
        assert len(issues) == 1
        assert "must end in '.md'" in issues[0]

    def test_path_in_entry_rejected(self) -> None:
        """Path in entry is rejected."""
        issues = _validate_related_format(["subdir/foo.md"])
        assert len(issues) == 1
        assert "must be a plain basename" in issues[0]

    def test_anchor_in_entry_rejected(self) -> None:
        """Anchor in entry is rejected."""
        issues = _validate_related_format(["foo.md#section"])
        assert len(issues) == 1
        assert "must be a plain basename" in issues[0]
```

## Compatibility considerations

- This is a test file addition — no existing code is modified
- The tests follow the conventions of sibling test files in `tests/tools/`
- No test-discovery convention conflicts expected

## Security considerations

- No security implications — this is a test file addition
- The tests prevent future regressions in the strengthened check behavior

## Rollback considerations

- If the tests fail due to the current tool behavior, they confirm the regression exists
- The tests should be added alongside the fix (SEQ-04), not before it

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/tools/test_check_docs_structure.py` | Unit: any-level detection, fenced-code ignore, format validation, ADR unchanged | `uv run pytest tests/tools/test_check_docs_structure.py -q -p no:cacheprovider -p no:randomly` | New cases pass; existing cases still pass |
| Changed tool files | Static analysis | `uv run ruff`, `uv run mypy`, `uv run bandit` (per `routing.md`) | Clean |
| Full docs-tooling suite | Integration: repo passes its own checks | `uv run python tools/check_docs_quality.py`, `tools/check_docs_structure.py` | All pass |

## Completion criteria

- Test cases for body block at `##` and `###` levels
- Test for heading inside fenced code ignored
- Test for `related: []` accepted
- Tests for invalid `related` format / missing target / self-reference / duplicate
- All tests pass after SEQ-04 is applied
- Static analysis clean

## Out of scope

- Modifying any existing test file beyond adding new test methods
- Changing the `error_type` vocabulary ("transport" | "tool" | "")
- Changing `server_key` handling
- Changing the transport error path
- Changing retry logic or health tracking
- Renaming or re-scoping `from_transport()`; redesigning `ToolCallResult`
- Optional: asserting `ctx.diagnostics.save_transport_failure` is not called for an HTTP tool-level error

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add test cases for any-level detection | Completed | 20261006-232956 | 20261006-232956 | REQ-006 |
| 2 | Add test cases for related format validation | Completed | 20261006-232956 | 20261006-232956 | REQ-006 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261006-232956 | 20261006-232956 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261006-232956 | 20261006-232956 |  |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20261005-143453_rel001_consolidate-related-document-information-into-front-matter-related.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261006-073642_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-122547
- **Related target files**: tests/tools/test_check_docs_structure.py