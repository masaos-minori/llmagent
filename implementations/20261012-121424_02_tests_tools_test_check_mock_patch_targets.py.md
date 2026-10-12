## Goal
- Cover the marker behavior added in procedure 01 (`REQ-003`).

## Scope
- Only `tests/tools/test_check_mock_patch_targets.py`.

## Assumptions
- The existing `_run`, `_write` helpers and the `tmp_path` source-tree pattern in `TestIneffectivePatchTarget` are reused as they are.

## Design decisions
- Add the cases to `TestIneffectivePatchTarget`, built from the same `db.helper.SQLiteHelper` / `agent.diagnostic_store` fixture as `test_origin_patch_flagged_against_module_level_reimport`.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`tests/tools/test_check_mock_patch_targets.py`

### Procedure
1. Add `test_marker_with_reason_suppresses_the_finding`: the `patch(` line ends with `# mock-patch-ok: imports SQLiteHelper inside the function`; expect `[]`.
2. Add `test_marker_without_reason_does_not_suppress`: the line ends with `# mock-patch-ok:`; expect one finding.
3. Add `test_marker_on_a_different_line_does_not_suppress`: the marker sits on the line after `patch(`; expect one finding.

### Method
- Copy the fixture sources of the existing flagged case and change only the `patch(` line, written as a `@patch(...)` decorator line with the trailing comment.

### Details
- Place the new cases after `test_origin_patch_flagged_against_module_level_reimport`; no new helper is needed.

## Compatibility considerations
N/A: test-only change; no runtime or public interface is affected.

## Security considerations
N/A: no input handling, credentials, or I/O boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_check_mock_patch_targets.py -v`; `uv run ruff format --check tests/tools`, `uv run ruff check tests/tools`.

## Completion criteria
- The three new cases pass together with all existing cases; without procedure 01 applied, the first case fails.

## Out of scope
- Changing existing cases or the `_run` helper.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the three marker test cases | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the touched files | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (inline suppression marker with a mandatory reason)
- **Source issue**: issues/20261012-120426_mock001_fix-ineffective-mock-patch-targets-in-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-120856_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-121424
- **Related target files**: tests/tools/test_check_mock_patch_targets.py
