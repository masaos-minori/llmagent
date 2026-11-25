## Goal
Prove across a process boundary that a directive reconstructed from the persisted row reconnects a reissued call
to the original logical call id.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The test uses only `tmp_path` stores and loopback, so nothing reaches a path under `/opt/llm`, matching the
  convention of the sibling cross-process tests.
- `tests/integration/conftest.py` provides the shared call store and the child-process runner; no new fixture is
  added.

## Design decisions
- The assertions cross a process boundary rather than reusing the in-process fakes of
  `tests/agent/test_mcp_call_recovery.py`, because the persistence assumption is what this test covers.

## Alternatives considered
- An in-process test with a re-opened store — rejected: it would not exercise the restart the Issue's Testing
  Expectations require.

## Implementation
### Target file
`tests/integration/test_replay_directive_across_restart.py` (new)

### Procedure
Write the interrupted-to-reissued-to-completed flow across a restart.

### Method
- Plant an `interrupted` replayable row with a canonical hash through the shared store.
- Run the child process, exit, then reopen the store in the parent and reconstruct the directive from the
  persisted row.
- Reissue the call with identical tool name and arguments and assert the prepared call carries the original id,
  then finalize the row and assert the consumed row is not listed again.

### Details
- `pytestmark = pytest.mark.integration`, matching the sibling files.
- Assert the ambiguous case once: two `interrupted` rows with the same tool and hash produce the structured
  ambiguity error rather than an arbitrary pick.
- Include the run-5x flakiness note in the module docstring, as the sibling integration tests do.

## Compatibility considerations
Depends on sibling procedures seq 01, 02, 06, and 08; the test cannot pass before the write path and the matching
path land.

## Security considerations
N/A.

## Rollback considerations
N/A: delete the file with the revert.

## Validation plan
- `uv run pytest tests/integration/test_replay_directive_across_restart.py -m integration` (AC-005).

## Completion criteria
The test fails if the reissued call gets a fresh id, if a consumed row is re-listed, or if an ambiguous match is
resolved by choice instead of rejection.

## Out of Scope
No dispatcher-side dedup assertions (mcpai001 boundary).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the cross-restart integration test | Pending | — | — | |
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
- **Requirement ID**: `REQ-002` (reissue reuses the original id), `REQ-006` (directive survives restart)
- **Source issue**: `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261125-105505_mcpai004_logical-idempotency-key-replay.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-112546
- **Related target files**: `tests/integration/test_replay_directive_across_restart.py`
