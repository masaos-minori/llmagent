## Goal
Make the recorder fake satisfy the changed Protocol and prove that a replayed call records the original id and
the hash in the state row.

## Scope
**Release unit**: persisted directive store

## Assumptions
- The fake at line 2305 carries a `snapshot_id` parameter that the Protocol does not declare; it stays as-is
  unless the run shows it is dead, and the new `args_hash` parameter is added in the Protocol order.

## Design decisions
- The test asserts the recorded tuple, which is the observable contract of the recorder seam.

## Alternatives considered
N/A: test-only change.

## Implementation
### Target file
`tests/agent/test_tool_runner.py`

### Procedure
Update the recorder fake and add one replay recording test.

### Method
- Add `args_hash: str` to `FakeRecorder.record_tool_call` and include it in the recorded tuple.
- Add a test that prepares a call, attaches a `ReplayDirective` (resolved from sibling procedure seq 06) to the
  turn state, executes the call, and asserts the recorded key is the directive's original id and the recorded
  hash equals `_canonical_args_hash(args)`.

### Details
- `_state_ctx()` already wires the recorder path; the new test reuses it and the existing `_make_ctx()` fixtures.
- Update `records()` tuple length expectations in the assertions that read it.

## Compatibility considerations
Assertions that compare the recorded tuple shape must be updated together with the fake, or the existing tests
fail on tuple length.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_tool_runner.py` (AC-001).
- `uv run python tools/check_mock_patch_targets.py` if any patch target moves.

## Completion criteria
The fake implements the Protocol as declared in `scripts/agent/context.py`, and the replay test shows the state
row keyed by the original id with the canonical hash.

## Out of Scope
No change to the DAG scheduling tests in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the recorder fake and add the replay recording test | Completed | — | 20261125-130922 | fake now mirrors the Protocol exactly: the dead snapshot_id parameter was removed and args_hash added in Protocol order; one new test asserts the recorded key is the directive id and the recorded hash is the canonical hash |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261125-130922 | 112 passed; ruff format/check pass; mypy clean; check_mock_patch_targets no findings; no tuple-length assertions existed to update |

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
- **Requirement ID**: `REQ-002` (replayed call reuses the original id), `REQ-006` (the row carries the hash)
- **Source issue**: `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261125-105505_mcpai004_logical-idempotency-key-replay.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-112546
- **Related target files**: `tests/agent/test_tool_runner.py`