## Goal
Cover directive matching, one-time consumption, and the ambiguous-match rejection at the preparation boundary.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The module already tests `_logical_call_id` (line 455), so the new tests sit in the same file's preparation
  fixtures and use the existing `_prepare_one` call shape.

## Design decisions
- Tests assert the prepared call's `ToolExecutionContext.call_id` equals the directive's original id, which is
  the observable contract; no test reaches into the helper's internals.

## Alternatives considered
N/A: test-only change.

## Implementation
### Target file
`tests/agent/test_tool_preparation.py`

### Procedure
Add three tests for the directive path.

### Method
- Match: build a `ReplayDirective` (resolved from sibling procedure seq 06) on the turn state with a tool name
  and hash, prepare a call with identical tool and arguments, assert the context carries the original id.
- One-time consumption: prepare two identical calls against one directive; the first gets the original id, the
  second gets a fresh id.
- Ambiguity: two directives for the same tool and hash; assert the call is rejected with the structured error
  kind `ambiguity` and appears in `failures`, not in `prepared`.

### Details
- Build directives through the same helper the production code uses, so the consumed flag semantics are the
  production ones.
- Add a hash-equality assertion for a byte-identical reissue, per the Plan's Risk on edited arguments.

## Compatibility considerations
N/A: test-only change.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_tool_preparation.py` (AC-002).
- `uv run python tools/check_mock_patch_targets.py` if any `patch("module.Symbol")` is added.

## Completion criteria
The three tests fail against the pre-change preparation path and pass after sibling procedure seq 06 lands.

## Out of Scope
No change to the approval-gate tests already in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the matching, consumption, and ambiguity tests | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (one-time consumption), `REQ-002` (matching), `REQ-003` (fail closed on ambiguity)
- **Source issue**: `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261125-105505_mcpai004_logical-idempotency-key-replay.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-112546
- **Related target files**: `tests/agent/test_tool_preparation.py`
