## Goal
- Add spy-based tests that pin the order and count of close_resources relative to the input loop on the success, startup-failure, and loop-exception paths (`REQ-004`).

## Scope
- Only `tests/agent/test_repl.py`: one new test class appended at the end of the file.

## Assumptions
- The existing helper `_make_bare_repl` returns a REPL whose shutdown coordinator and input loop can be replaced by attribute assignment.
- Existing run tests patch the startup orchestrator in `agent.repl` the same way, so the same patching works here.

## Design decisions
- Plain recording coroutines, not AsyncMock, so the call order and count are observable.
- Apply this procedure before procedure 01 so the order test can be seen failing against the unmodified run method.

## Alternatives considered
N/A: the spy approach is fixed by the Issue and the Plan.

## Implementation
### Target file
`tests/agent/test_repl.py`

### Procedure
1. Append a test class named TestRunResourceCleanup at the end of the file.
2. Add test_cleanup_runs_after_input_loop_on_success: startup patched to succeed; record calls into one list; assert the list equals input loop run then close_resources.
3. Add test_cleanup_runs_once_when_startup_fails: startup patched to raise RuntimeError; assert close_resources was recorded exactly once, the fatal message was written on the view, and the RuntimeError propagates.
4. Add test_cleanup_runs_once_when_input_loop_raises: startup succeeds, the input loop spy raises RuntimeError; assert close_resources was recorded exactly once after the loop and the RuntimeError propagates.
5. Run the order test against the unmodified run method and confirm it fails; keep the output as the mutation evidence.

### Method
- Build each REPL with `_make_bare_repl`; patch `agent.repl.StartupOrchestrator` and set its run to an AsyncMock returning a three-tuple (commands, orchestrator, empty list) or raising.
- Replace the shutdown coordinator and the input loop with simple objects whose async methods append a label to a shared list.

### Details
- Mark each test with the pytest asyncio marker used by the neighbouring async tests.
- Use pytest.raises with a match string for the propagated error.
- Do not touch existing tests or helpers.

## Compatibility considerations
N/A: test-only change.

## Security considerations
N/A: no input handling, credentials, or trust boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_repl.py -v`; before procedure 01 the order test fails, after it all three pass.
- `uv run ruff format --check tests/agent/test_repl.py`, `uv run ruff check tests/agent/test_repl.py`.

## Completion criteria
- Three new tests exist; the success-path order test fails on the old run method and passes after procedure 01; existing tests are unchanged and pass.

## Out of scope
- Modifying existing tests, `_make_bare_repl`, or any production file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the three spy-based tests and confirm the order test fails on the unmodified run method | Completed | 20261012-141517 | 20261012-141538 | stale_detector clean; applied before procedure 01 (mutation precondition) changed: tests/agent/test_repl.py (+TestRunResourceCleanup, 3 tests); mutation precondition met: 2 of 3 fail on the unmodified run() |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the touched file | Completed | 20261012-141636 | 20261012-141636 | ruff format/check pass; 3 new tests pass after procedure 01 (2 failed before); 82 targeted tests pass |

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
- **Requirement ID**: `REQ-004` (spy-based ordering and count tests)
- **Source issue**: issues/20261012-124806_start001_startup-failure-cleanup-handler-closes-shared-http-client-before-the-repl-session-begins.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-140942_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-141133
- **Related target files**: tests/agent/test_repl.py