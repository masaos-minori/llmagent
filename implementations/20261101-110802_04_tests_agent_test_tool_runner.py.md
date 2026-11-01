## Goal

Add producer tests to `tests/agent/test_tool_runner.py` covering the new
`tool_call_state` recording in `_recorded_call` / `execute_one_tool_call`: pending-before-
dispatch, completed/failed finalize, non-fatal recorder errors, BaseException leaving rows
pending, and the unwired-recorder no-op. Implements the test criteria for REQ-001, REQ-002,
REQ-003, REQ-004, REQ-006, REQ-007, REQ-008 (rows 1 and 4 of the plan's Target Files table).

## Scope

- New test class(es) in `tests/agent/test_tool_runner.py`; no existing test modified.
- A small `FakeRecorder` fixture class inside this test file (records call tuples) — no
  production test helper module.

## Assumptions

- Existing fixtures build `AgentContext` with a stub `ToolExecutor` (file already exercises
  `execute_all_tool_calls`/`execute_one_tool_call` directly); new tests reuse that pattern
  and additionally set `ctx.workflow.current_task_id = "task-1"` and
  `ctx.workflow.tool_call_recorder = FakeRecorder()`.
- `ctx.session.session_id` is set in the fixture so the key is deterministic; expected key is
  recomputed in the test via `derive_idempotency_key("call_tool", name, args, str(session_id))`
  — the test asserts the exact key string, not just "some key".

## Design decisions

- Tests assert against the `FakeRecorder` call log (method, task_id, key, tool, retry_class,
  state), not against a real SQLite DB: the producer/consumer DB integration is covered by
  `tests/agent/workflow/test_workflow_state_store.py` (already exists) and the e2e test;
  keeping this file DB-free matches the file's existing no-DB style and the plan's
  unit-test-level scope for row 04.
- Ordering assertion (pending recorded BEFORE the executor ran) is verified by the recorder
  appending a sentinel the fake executor also observes (shared list of event strings),
  mirroring the file's existing event-list fixture style.

## Alternatives considered

- Real-SQLite assertions per test: rejected — DB behavior of the helpers is already covered
  by `tests/agent/workflow/test_workflow_state_store.py`; duplicating it here slows the
  fast unit layer without adding producer-specific signal.
- Testing via `execute_all_tool_calls` end-to-end instead of asserting the recorder call
  log directly: rejected — the DAG path adds scheduler nondeterminism; the recorder call
  log pins the producer contract deterministically.

## Implementation
### Target file

`tests/agent/test_tool_runner.py`

### Procedure

1. Add `FakeRecorder` capturing `(call, task_id, key, tool, retry_class, state)` tuples plus
   a shared event log; add a `failing_recorder` variant whose methods raise.
2. `test_pending_recorded_before_dispatch`: one prepared call; assert event order
   `record_tool_call` before executor invocation, with state `pending`, tool name, and the
   exact derived key.
3. `test_completed_finalize_after_success` and `test_failed_finalize_after_executor_error`:
   assert the finalize tuple state is `completed` / `failed` respectively.
4. `test_recorder_failure_is_non_fatal`: failing recorder (record and finalize both raise);
   assert the tool result row is still produced normally (`is_error` reflects the executor,
   not the recorder) and no exception escapes (REQ-007).
5. `test_baseexception_leaves_pending`: executor raises `asyncio.CancelledError`; assert
   `record_tool_call` happened, no finalize happened, and the exception propagates.
6. `test_unwired_recorder_is_noop`: `tool_call_recorder=None` (the default for all existing
   tests); assert normal execution and zero state writes — proves the 27 pre-existing tests
   in this file stay green without rewiring.
7. `test_retry_class_from_owner`: assert the recorded `retry_class` equals
   `mcp_dedup.retry_class(name)` for a tool listed in `config/mcp_dedup.toml` (e.g.
   `write_file` → `retryable`) and for an unlisted name (`non_retryable` default).
8. `test_key_matches_transport_derivation`: assert recorded key ==
   `derive_idempotency_key("call_tool", name, args, str(session_id))` (REQ-003 acceptance
   criterion, plan Constraint 2).

### Method

Append new test classes after the existing classes; import
`shared.http_transport.derive_idempotency_key` and `shared.mcp_dedup.retry_class` in the
test file.

### Details

- Keep tests deterministic: fixed `session_id`, fixed args strings, no wall-clock
  dependency (timeout behavior belongs to `classify_stale_pending` tests, already covered in
  `tests/agent/workflow/test_workflow_state_store.py`).
- Do not add `pytest.ini` marks: the file is in the `agent` marker set already
  (`-m "not slow and not e2e"` unaffected).

## Compatibility considerations

- Existing 27 tests in this file must pass unmodified — the unwired-recorder default is what
  guarantees that (test 6 pins it).
- `tests/agent/test_tool_approval_preflight.py` also calls `execute_one_tool_call` directly;
  it stays unwired and must remain green (part of the 321-agent-test gate).

## Security considerations

- N/A: test-only changes; fake fixtures use harmless literal args.

## Rollback considerations

- Deleting the added test classes reverts to the file's pre-change state; no production
  dependency.

## Validation plan

- `uv run pytest tests/agent/test_tool_runner.py -x -q` then `uv run pytest tests/agent -x -q`
  (321 baseline + new).
- Full sequence per `rules/toolchain.md`: ruff/mypy on tests config (`type_checks_for_tests`
  is enabled), bandit/vulture/radon, diff-cover ≥90%.
- Mutation spot-check: temporarily disable the finalize call locally and confirm tests 3/5
  fail (the tests must actually bind the behavior, per `rules/testing.md`).

## Completion criteria

- All eight new tests pass; all pre-existing tests in the file pass unmodified.
- REQ-001..REQ-004, REQ-006, REQ-007, REQ-008 acceptance criteria from the plan are each covered by at least one test.

## Out of Scope

- Real-DB or e2e producer-consumer tests (toolexec001 Phase 6 e2e, tracked as plan Risk 3).
- Adapter wiring tests (row 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-006, REQ-007, REQ-008
- **Source issue**: issues/done/20261031-175803_toolstate001_tool-call-state-producer.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-105136_toolstate001_tool-call-state-producer.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-110802
- **Related target files**: tests/agent/test_tool_runner.py
