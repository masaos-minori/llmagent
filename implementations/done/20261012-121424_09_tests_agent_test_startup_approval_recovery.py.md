## Goal
- Mark the three effective `shared.logger.Logger` patches with the suppression marker (`REQ-004`).

## Scope
- The patch lines at 649, 690, and 817.

## Assumptions
- `recover()` in `scripts/agent/startup_approval_recovery.py` imports `Logger` inside the function (line 28), so the patch is effective; the tests assert exactly one matching warning, which would fail otherwise.
- Marker support from procedure 01 is applied first.

## Design decisions
- Add `# mock-patch-ok: recover() imports Logger inside the function` to each `with patch("shared.logger.Logger") as mock_logger:` line; one comment covers both importers the checker names for that line.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`tests/agent/test_startup_approval_recovery.py`

### Procedure
1. Add the marker comment after the opening parenthesis of the `patch("shared.logger.Logger")` line at each of the three sites.

### Method
- Write the marker right after the opening parenthesis, as `patch(  # mock-patch-ok: <reason>` with the arguments on the following lines. A trailing comment after the closing parenthesis does not work: `ruff format` wraps the call and the comment leaves the `patch(` line, where the checker looks.

### Details
- No code change.

## Compatibility considerations
N/A: test-only change; no runtime or public interface is affected.

## Security considerations
N/A: no input handling, credentials, or I/O boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_startup_approval_recovery.py -v`; `uv run python tools/check_mock_patch_targets.py` reports `No findings.` once procedures 01 to 09 are all applied.

## Completion criteria
- Three markers are present with a reason, tests pass, and the repository-wide checker reports no findings.

## Out of scope
- Changing the patches or assertions.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the marker with its reason at the three patch lines | Completed | 20261012-130217 | 20261012-130238 | procedure Method corrected (marker after open paren) before implementing changed: tests/agent/test_startup_approval_recovery.py (3 markers after the patch( open paren) |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the touched files; confirm the repository-wide checker reports no findings | Completed | 20261012-130238 | 20261012-130238 | ruff format/check pass; 27 tests pass; repository-wide checker reports No findings |

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
- **Requirement ID**: `REQ-004` (mark the effective function-local-import patches)
- **Source issue**: issues/20261012-120426_mock001_fix-ineffective-mock-patch-targets-in-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-120856_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-121424
- **Related target files**: tests/agent/test_startup_approval_recovery.py