## Goal

Cover the `merge-related` decision (one-time aid vs any-level) and any behavior change in `test_manage_frontmatter.py`. (REQ-006 / AC-6)

## Scope

- Add test cases for the `merge-related` decision (one-time aid vs any-level)
- Cover any behavior change in the `merge-related` subcommand

## Assumptions

- The existing test classes (`TestMergeRelatedDefaults`, `TestMergeRelatedInputForms`) provide a pattern to follow
- The one-time-aid recommendation is the adopted policy (UNK-04)
- The `merge-related` subcommand's existing functionality is preserved

## Design decisions

- Follow the existing test class pattern in `tests/tools/test_manage_frontmatter.py`
- Add test methods for the one-time-aid behavior
- Use temporary files with appropriate content to test each case

## Alternatives considered

- Adding tests to an existing test class — rejected because a dedicated test class provides clearer ownership

## Implementation

### Target file

`tests/tools/test_manage_frontmatter.py`

### Procedure

1. Add test class/method for one-time-aid behavior
2. Add test for second-level heading detection only
3. Add test for manual migration note for deep `### ` blocks

### Method

- Create a new test class following the pattern of existing test classes
- Add test methods for each new case
- Use temporary files with appropriate content

### Details

**New test class to add:**
```python
class TestMergeRelatedOneTimeAid:
    """Tests for merge-related one-time-aid behavior."""

    def test_merge_related_detects_h2_only(self) -> None:
        """merge-related detects ## Related Documents (second-level only)."""
        # Create a temp file with ## Related Documents
        content = "## Related Documents\n\n- `foo.md`\n"
        # ... test that merge-related can migrate this
        # The exact test depends on the merge-related API

    def test_merge_related_does_not_detect_h3(self) -> None:
        """merge-related does NOT detect ### Related Documents (third-level)."""
        # Create a temp file with ### Related Documents
        content = "### Related Documents\n\n- `foo.md`\n"
        # ... test that merge-related does NOT migrate this
        # The exact test depends on the merge-related API

    def test_merge_related_dry_run_default(self) -> None:
        """merge-related defaults to --dry-run."""
        # ... test that dry-run mode is the default
        # The exact test depends on the merge-related API
```

## Compatibility considerations

- This is a test file addition — no existing code is modified
- The tests follow the conventions of sibling test files in `tests/tools/`
- No test-discovery convention conflicts expected

## Security considerations

- No security implications — this is a test file addition
- The tests prevent future regressions in the `merge-related` behavior

## Rollback considerations

- If the tests fail due to the current tool behavior, they confirm the regression exists
- The tests should be added alongside the fix (SEQ-05), not before it

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/tools/test_manage_frontmatter.py` | Unit: `merge-related` one-time-aid behavior | `uv run pytest tests/tools/test_manage_frontmatter.py -q -p no:cacheprovider -p no:randomly` | Passes |
| Changed tool files | Static analysis | `uv run ruff`, `uv run mypy`, `uv run bandit` (per `routing.md`) | Clean |
| Full docs-tooling suite | Integration: repo passes its own checks | `uv run python tools/check_docs_quality.py`, `tools/check_docs_structure.py` | All pass |

## Completion criteria

- Test cases for one-time-aid behavior
- Test for second-level heading detection only
- Test for manual migration note for deep `### ` blocks
- All tests pass after SEQ-05 is applied
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
| 1 | Add test cases for merge-related one-time-aid behavior | Completed | 20261006-233019 | 20261006-233019 | REQ-006 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261006-233019 | 20261006-233019 |  |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261006-233019 | 20261006-233019 |  |

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
- **Related target files**: tests/tools/test_manage_frontmatter.py