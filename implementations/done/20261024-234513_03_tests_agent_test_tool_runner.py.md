# Implementation Procedure: tests/agent/test_tool_runner.py

## Goal

Add the one full-round integration case that exercises the fixed contract through the real
`execute_all_tool_calls()` harness (`T-1`; `REQ-007` regression coverage; `AC-1`, `AC-5`, `AC-6`), and
keep the four existing ordering/attribution tests unmodified as the characterization anchors.

## Scope

- Add one test to `TestExecuteAllToolCalls` (`tests/agent/test_tool_runner.py:1044`).
- Modify nothing else in the file: the anchors `test_results_sorted_to_original_call_order` (`:400`),
  `test_tool_meta_is_keyed_by_call_id_not_tool_name` (`:430`),
  `test_denied_tool_call_is_returned_as_tool_message` (`:1145`) and
  `test_results_restored_to_original_order_despite_concurrent_grouping` (`:1566`) stay byte-identical
  (`AC-6`).

## Assumptions

- Today the case fails: the raw batch reaches `complete_round()` and `KeyError: 'id'` escapes
  `execute_all_tool_calls()` (probe CASE A at HEAD `9331b337a`); the test is written before the
  production change (Plan Phase 2 order).
- The preparation phase answers the id-less entry with a `_PrepFailure` tuple whose `llm_text` is
  exactly `"tool call is missing an id"` and whose `tool_call_id` is `""`
  (`tool_preparation.py:82-84`, `_reject()` return), so no new fixture is needed.

## Design decisions

- Reuse this file's existing harness (`_cfg()` / `_make_ctx()` / `_tc()`, `AsyncMock` for
  `ctx.services_required.tools.execute`, `ToolLoopGuard(ctx)` guard) — the same shape as
  `test_denied_tool_call_is_returned_as_tool_message`; no new helpers, no patches needed since a
  read-only tool passes the approval gate.

## Alternatives considered

N/A: the Plan fixes this row as the single integration case for `AC-1`/`AC-6`.

## Implementation

### Target file

`tests/agent/test_tool_runner.py`

### Procedure

Add `test_call_without_id_is_answered_in_batch_position` (new) to `TestExecuteAllToolCalls` (after
`test_denied_tool_call_is_returned_as_tool_message`), `@pytest.mark.asyncio`.

### Method

1. Build the batch: `no_id_call = {"function": {"name": "read_text_file", "arguments": "{}"}}` (the
   `"id"` key removed from the `_tc()` shape) and `valid_call` (new) `= _tc("call_b", "read_text_file")`.
2. Mock `ctx.services_required.tools.execute` as `AsyncMock(return_value=ToolCallResult(output="ok",
   is_error=False, request_id="req-1", server_key=""))`; `await
   execute_all_tool_calls(ctx, [no_id_call, valid_call], 0, guard=ToolLoopGuard(ctx))` with no
   `pytest.raises` wrapper — completion is the assertion.
3. Assert:
   - `ctx.services_required.tools.execute.assert_awaited_once()` and the awaited call is
     `("read_text_file", {"...": ...})`-style for `valid_call` (new) only — the id-less call was never
     executed (`AC-5`).
   - `len(ctx.conv.history) == 2`; `history[0] == {"role": "tool", "tool_call_id": "", "content":
     "tool call is missing an id"}` and `history[1]["tool_call_id"] == "call_b"` — one row per
     declared entry, in declared batch position (`AC-1`, `AC-5`); no synthetic id appears.

### Details

- The test name must not collide with the existing `TestExecuteAllToolCalls` test names; no
  class-level fixtures beyond the module's existing helpers.
- The four anchor tests record `T-5` (their pass before and after the production change is the
  characterization proof of `REQ-005`); record the pre-change 87-pass snapshot in the Execution
  Status notes when running step 1.

## Compatibility considerations

N/A: test-only change; the anchors and the other 86 tests are untouched and must pass before
(pre-change characterization) and after (regression) the production change.

## Security considerations

N/A: test-only, runs under the `tests/conftest.py` `/opt/llm` isolation guard like the rest of the
file.

## Rollback considerations

N/A: revert the single added test (single-commit revert).

## Validation plan

- `uv run pytest tests/agent/test_tool_runner.py -q` before the production change → the new test
  fails with `KeyError: 'id'`, all other tests pass (expected failing state).
- After `20261024-234513_01` and `20261024-234513_02` land: `uv run pytest tests/agent/test_tool_runner.py tests/agent/test_tool_round_completion.py tests/agent/test_tool_preparation.py tests/agent/test_tool_result_pairing.py -q` → all pass, no `KeyError`.
- `uv run pytest tests/agent -q` then `uv run pytest -v` → no new failure (`AC-10`).

## Completion criteria

- The new test fails pre-change and passes post-change; the four anchors pass unmodified; no test
  writes under `/opt/llm`; `AC-1`, `AC-5` and `AC-6` are each witnessed by an assertion in the new
  test or an untouched anchor.

## Out of Scope

- Helper-level cases `T-1`..`T-6` (procedure doc `20261024-234513_02`).
- Production code (procedure doc `20261024-234513_01`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Record the pre-change 87-pass anchor snapshot, then add the new integration test (must fail with `KeyError`) | Completed | 20261025-0100 | 20261025-0100 | TDD gate for this row. Test uses `_tc("read_text_file")` (id `call_read_text_file`) and patches `run_approval_checks`; the procedure's `_tc("call_b", ...)` did not match the helper signature |
| 2 | Re-run after `20261024-234513_01` lands; anchors + new test pass | Completed | 20261025-0100 | 20261025-0100 | |
| 3 | `uv run pytest tests/agent -q` and full-suite regression | Completed | 20261025-0100 | 20261025-0100 | |

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
- **Requirement ID**: `REQ-007` (regression coverage through the round harness), `REQ-001` (no strict
  `tc["id"]` crash), `REQ-005` (anchors as characterization)
- **Source issue**: `issues/20261021-093421_tool004-missing-tool-call-id-raises-keyerror.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-023815_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-234513
- **Related target files**: `tests/agent/test_tool_runner.py`
