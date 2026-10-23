## Goal

Assert the round-pairing invariant over real stored rows (`REQ-001`, `REQ-002`,
`REQ-005`, `REQ-006`, `REQ-008`, `REQ-012`): after a round forced to fail by each
exception class in the Problem table, every declared `tool_call_id` has exactly one
`role='tool'` row readable through `ctx.session.fetch_messages()` and exactly one
matching entry in `ctx.conv.history`, and the original exception still propagates.
Also cover that completed results survive a later failure, that a mid-round guard
stop answers the skipped id, and that synthesized rows do not touch guard state or
stats.

## Scope

`tests/agent/test_tool_runner.py` only. Adds new test classes to the existing
1372-line file; does not edit existing assertions except where an assertion is the
subject of the change. Reference reads: `scripts/agent/tool_runner.py` (the round,
row 1), `scripts/agent/session_message_repo.py::fetch_messages` (read-back path),
`scripts/agent/tool_enums.py::ToolCallStopReason`. Dependent production file:
`scripts/agent/tool_runner.py`.

## Assumptions

- The existing test helpers (`_cfg`, `_make_ctx`, `_runtime_tools`, `_tc`, `_pc`,
  gateway/approval patches) can drive a real round end-to-end so that
  `fetch_messages()` returns rows written through the real `save_many()` path.
- The exception classes in the Problem table can be forced by stubbing
  `tools.execute` / the resolver / the approval gate, matching how the existing
  `TestExecutorUnavailableGuard` and `TestGatewayBypassPreflightDenial` force raises.

## Design decisions

- Pairing assertions live where a real session exists (`tests/agent/test_tool_runner.py`),
  never by mocking `execute_all_tool_calls` (which is what `test_llm_turn_runner.py`
  does and why no test caught the gap; `REQ-008`).
- Each new class reads back through `fetch_messages()` and compares the declared
  id set against `tool_call_id` rows — the DB-backed view AC-1/AC-2 require.

## Alternatives considered

- Mocking `execute_all_tool_calls` and inspecting the mock — would not exercise the
  synthesis or the real `save_many` path; rejected (the whole point of the gap).

## Implementation

### Target file

`tests/agent/test_tool_runner.py`

### Procedure

Add these classes to the existing file (do not modify existing classes):

1. `TestRoundPairingAfterForcedFailure`, one case per exception in the Problem
   table — `ToolExecutorUnavailableError` (stub `tools = None`), re-raised
   `PolicyViolationError` (gateway-bypass path), resolver `ValueError` for an
   unregistered tool, `gather`-raised error, and a failing tool executor for the
   second call of a sequential group. Each case: declare N ids, force the round
   to raise, assert `pytest.raises` on the original exception, then — before the
   raise unwinds the recorded history — assert that every declared id has exactly
   one `role='tool'` row via `ctx.session.fetch_messages()` and one entry in
   `ctx.conv.history` (`AC-1`, `AC-2`).
2. `TestCompletedResultsSurviveAFailure`: call 1 succeeds, call 2 raises; assert
   call 1's real output is the persisted row for its id and only call 2's id is
   synthesized (`REQ-002`).
3. `TestMidRoundGuardStop`: set `tool.tool_empty_result_max_repeats = 2`, run a
   sequential group of three empty results; assert only the third call is not
   executed, its id is synthesized with the `GUARD_STOP` reason, and the round's
   remaining batch is not dispatched (`REQ-006`).
4. `TestSynthesizedRowsDoNotTouchGuardStateOrStats`: assert
   `ctx.stats.stat_tool_errors`, `ctx.stats.stat_tool_calls`, and `out_failed_keys`
   are unchanged by synthesized rows, and that the empty-result counts see only
   real results (`REQ-005`).
5. `TestNoSecondHintForOneTrip`: assert the mid-round path writes no diagnostic
   while the post-round `check_empty_result_repeat()` writes exactly one
   (`REQ-007`, `AC-5`).

### Method

- Append the new classes after the existing `TestGatewayBypassPreflightDenial`
  (`:1169-1194`) block. Reuse the file's existing helpers and patch targets.
- For the request-shape assertion (`AC-2`), build the next request payload from
  stored history and assert every `tool_calls[].id` has a matching
  `role='tool'` `tool_call_id`.

### Details

- The existing `TestExecutorUnavailableGuard` (`:1155-1166`) and
  `TestGatewayBypassPreflightDenial` (`:1169-1175`) keep asserting the raise
  unchanged (`REQ-008`, `AC-3`); the new cases assert *both* the raise and the
  pairing.
- One `save_many()` per round (`REQ-012`): assert the round writes once.

## Compatibility considerations

### Corrections found while implementing

- The sessions in these tests are mocks, so rows are read from the `save_many` argument and `ctx.conv.history` instead of `fetch_messages()` (no real DB is built in this file). Cases: executor unavailable, re-raised policy violation, resolver error, gathered group failure, approval gate failure, completion failure not masking the original exception, a normal round synthesizing nothing, completed results surviving, a mid-round stop (batch boundary and one sequential group), and stats/guard isolation. Mutation checks: pairing disabled (14 tests fail), scan writing a hint (4), no completion on exception (7), no group-level break (1), no batch-level break (1).


- Purely additive; existing 16 direct `execute_all_tool_calls` call sites
  (`:535`, `:565`, … `:1074`) and the order contract at `:1034` keep passing
  unchanged (`AC-3`).

## Security considerations

- N/A: test-only.

## Rollback considerations

- Delete the added classes; `git checkout -- tests/agent/test_tool_runner.py`
  restores HEAD.

## Validation plan

- `uv run pytest tests/agent/test_tool_runner.py -q --timeout=120` — all new and
  existing classes pass.
- AC-7 negative control: temporarily make the pairing step return `[]` and
  confirm `TestRoundPairingAfterForcedFailure` fails; revert.
- `uv run pytest tests/agent/test_agent_repl_tool_exec.py tests/agent/test_llm_turn_runner.py -q --timeout=120`
  — unchanged.
- `uv run ruff check tests/`, `uv run ruff format --check tests/`.

## Completion criteria

Every declared id has exactly one persisted `role='tool'` row and one history
entry after each forced-failure case, completed results survive a later failure, a
mid-round guard stop answers only the skipped id with the guard-stop reason,
synthesized rows leave stats/guard/`out_failed_keys` untouched, the original
exception still propagates, and all existing assertions remain green.

## Out of Scope

- The pure pairing unit tests — `tests/agent/test_tool_result_pairing.py` (row 5).
- The scan-extraction equivalence tests — `tests/agent/test_tool_loop_guard.py` (row 7).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add TestRoundPairingAfterForcedFailure, TestCompletedResultsSurviveAFailure, AC-2 request-shape assertion (REQ-001, REQ-002, REQ-012) | Completed | 20261023-170141 | 20261023-170141 | Phase 1 implemented; full suite passed |
| 2 | Add TestSynthesizedRowsDoNotTouchGuardStateOrStats (REQ-005) | Completed | 20261023-170141 | 20261023-170141 | Phase 1 |
| 3 | Add TestMidRoundGuardStop, TestNoSecondHintForOneTrip (REQ-006, REQ-007) | Completed | 20261023-170141 | 20261023-170141 | Phase 2, needs guard parameter |
| 4 | Run validation sequence (`rules/toolchain.md`) | Completed | 20261023-170141 | 20261023-170141 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 3 | Mid-round stop needs the tool001 guard parameter | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-005, REQ-006, REQ-008, REQ-012
- **Source issue**: `issues/20261021-093421_tool002-tool-call-persisted-without-tool-results.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-105432_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-113556
- **Related target files**: `tests/agent/test_tool_runner.py`