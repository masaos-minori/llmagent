## Goal
- Mark the three effective `db.helper.SQLiteHelper` patches with the suppression marker (`REQ-004`).

## Scope
- The patch lines at 348, 369, and 404 in `TestMemoryPrune`.

## Assumptions
- `memory_prune` in `scripts/agent/commands/memory_data_ops.py` imports `SQLiteHelper` inside the function (lines 196 to 199), so the patch is effective.
- Marker support from procedure 01 is applied first, otherwise the checker still reports these lines.

## Design decisions
- Add `# mock-patch-ok: memory_prune imports SQLiteHelper inside the function` to each of the three `patch(...)` lines.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`tests/agent/commands/test_agent_cmd_memory.py`

### Procedure
1. Add the marker comment after the opening parenthesis of the `patch("db.helper.SQLiteHelper"...)` call line at each of the three sites.

### Method
- Write the marker right after the opening parenthesis, as `patch(  # mock-patch-ok: <reason>` with the arguments on the following lines. A trailing comment after the closing parenthesis does not work: `ruff format` wraps the call and the comment leaves the `patch(` line, where the checker looks.

### Details
- No code change; the comment is the only edit.

## Compatibility considerations
N/A: test-only change; no runtime or public interface is affected.

## Security considerations
N/A: no input handling, credentials, or I/O boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/commands/test_agent_cmd_memory.py -v`; `uv run python tools/check_mock_patch_targets.py` reports no finding for this file.

## Completion criteria
- Three markers are present with a reason, tests pass, and the checker is silent for this file.

## Out of scope
- Changing the patches or the tests' assertions.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the marker with its reason at the three patch lines | Completed | 20261012-130111 | 20261012-130203 | changed: tests/agent/commands/test_agent_cmd_memory.py (3 markers after the patch( open paren); procedure Method corrected: a trailing comment is moved off the patch( line by ruff format |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the touched files | Completed | 20261012-130203 | 20261012-130203 | ruff format/check pass; 18 tests pass; checker silent for this file |

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
- **Related target files**: tests/agent/commands/test_agent_cmd_memory.py