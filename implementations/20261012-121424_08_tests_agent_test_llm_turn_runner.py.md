## Goal
- Mark the effective `agent.message_schema.validate_message` patch with the suppression marker (`REQ-004`).

## Scope
- The patch line at 147 in `test_fails_when_validation_fails`.

## Assumptions
- `_finalize_after_guard` in `scripts/agent/llm_turn_runner.py` imports `validate_message` inside the function (line 254), so the patch is effective.
- Marker support from procedure 01 is applied first.

## Design decisions
- Append `# mock-patch-ok: _finalize_after_guard imports validate_message inside the function` to that line.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`tests/agent/test_llm_turn_runner.py`

### Procedure
1. Append the marker comment to the `with patch("agent.message_schema.validate_message", ...)` line.

### Method
- The `with` line is already near 88 characters; the trailing comment may exceed it, which is allowed (E501 is ignored in `pyproject.toml`).

### Details
- No code change; the comment is the only edit.

## Compatibility considerations
N/A: test-only change; no runtime or public interface is affected.

## Security considerations
N/A: no input handling, credentials, or I/O boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_llm_turn_runner.py -v`; `uv run ruff format --check tests/agent/test_llm_turn_runner.py`; the checker is silent for this file.

## Completion criteria
- The marker is present with a reason, the file passes, and the checker is silent for it.

## Out of scope
- Changing the patch or the test.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the marker with its reason at the patch line | Pending | — | — | |
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
- **Requirement ID**: `REQ-004` (mark the effective function-local-import patches)
- **Source issue**: issues/20261012-120426_mock001_fix-ineffective-mock-patch-targets-in-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-120856_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-121424
- **Related target files**: tests/agent/test_llm_turn_runner.py
