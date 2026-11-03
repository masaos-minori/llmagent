## Goal

Mark each call as dispatched in `_recorded_call` immediately before its transport is
awaited and clear the marker when its result row is collected, threading the round's
`dispatched_ids` (new) set through `_execute_with_dag` → `_run_plan_batches` → `_run_group_calls`
→ `_recorded_call` alongside the existing `collected` threading (REQ-001), and pin the
end-to-end cancellation semantics with a blocking-stub-gateway test (AC-001..AC-005).

## Scope
**Release unit**: N/A: not part of a release unit

Covers the `scripts/agent/tool_runner.py` row (seq 04) and its companion test row
`tests/agent/test_tool_runner.py` (seq 08 of the plan table, companion-eligible, no
document of its own) of
`plans/20261101-144325_inflightcancel001_cancelled-call-reported-unexecuted.md`. Runs after
`implementations/20261103-121149_03_scripts_agent_tool_round_completion.py.md` (consumes
`dispatched_ids` (new) declared there) and is the last code document of the plan; the docs
document (seq 05) then precedes the plan-wide validation. Intra-plan execution order:
01 → 02 → 03 → 04 → 05.

## Assumptions
- Verified against current source (20261103): `_recorded_call` (tool_runner.py:67-105)
  awaits `execute_one_tool_call` (defined at 255) and writes `collected[pc.call_id]` only
  afterwards (100 on the captured-exception path, 103 on success), so an awaiting call is
  absent from `collected`; `except Exception` (92) intentionally lets `CancelledError`
  propagate (its comment names REQ-002/AC-5). `_run_group_calls` (108) drives serial and
  gather paths, `_run_plan_batches` (383), `_execute_with_dag` (417);
  `execute_all_tool_calls` (465) builds `state = RoundState([...])` (495), passes
  `state.collected` at 518, catches `BaseException` (521) → `finish(ROUND_NOT_COMPLETED)`
  (523) → re-raise, and finishes `GUARD_STOP` (527). radon: `_recorded_call` A(2),
  `_run_group_calls` A(5), `_run_plan_batches` B(9), `_execute_with_dag` A(5),
  `execute_all_tool_calls` B(7) — added parameters add no branches.
- Size gate (Plan Risks 20261103): `tool_runner.py` is 20444 B against the 20480 B
  `check_module_size.py` gate (36 B headroom, not baselined), and blockio001's Pending
  procedure `implementations/20261103-113432_04_scripts_agent_tool_runner.py.md` edits the
  same file first, shrinking the headroom further. This document's edits add on the order
  of 200-250 B. If `uv run python tools/check_module_size.py` fails after the edits:
  record a Blocker Log row, stop before committing, and report to the owner — the owner
  decides `--update-baseline` vs a tool_runner split Plan; do not compact unrelated code to
  squeeze under the gate.
- Cross-plan test-file overlap: `tests/agent/test_tool_runner.py` is also extended by
  blockio001's seq 08 (`TestDiagnosticWritesOffEventLoop` (new), lands first); the new test
  class here (`TestCancellationDispatchState` (new)) is disjoint and name-collision-free.
- `dispatched_ids` (new) is declared by the earlier sibling document (seq 03) as a
  defaulted `RoundState` field; this document adds no new `RoundState` construction.
- Companion fixture pattern (verified 20261103): `_make_ctx`/`_cfg`/`_tc`/`_approve_all`
  helpers (118-703), transport stubbed at `ctx.services_required.tools.execute`
  (`AsyncMock`) as in `TestMidRoundGuardStop` (971-1028); assertions via
  `_saved_text`/`_saved_tool_ids` (682-691) which read the persisted batch written through
  `complete_round`.
- Red-first: the cancellation tests fail pre-change (both unanswered ids get the
  not-executed text today), satisfying AC-005.

## Design decisions
- Parameter: add `dispatched: set[str]` to the four-function chain exactly where
  `collected` already appears, and pass `state.dispatched_ids` from `execute_all_tool_calls`
  into `_execute_with_dag` — no new state object, no attribute lookup on `ctx` (Plan D1).
- Mark `dispatched.add(pc.call_id)` in `_recorded_call` immediately before the
  `try`/`await execute_one_tool_call` block, and `dispatched.discard(pc.call_id)` after
  each `collected[pc.call_id] = ...` write (both paths): a call whose result row exists is
  answered and its dispatch state no longer matters; a call cancelled mid-await stays in
  the set (its row is synthesized outcome-unknown). Conservative by design: a cancellation
  in the gap between the add and the transport request still reads as in flight — "verify
  before repeating" is the safe statement there (Plan Assumption).
- `_record_pending_state`/`tool_call_state` rows (toolstate001 mechanism) are untouched:
  the pending-row path and `dispatched_ids` (new) are parallel accounts of the same fact (Plan
  Dependencies note: related, not duplicate).

## Alternatives considered
- Deriving in-flight from `collected` absence alone: rejected by the Plan (approved-but-
  never-started calls would wrongly read as in flight).
- Passing `RoundState` itself down the chain instead of the bare set: rejected — the chain's
  current style passes the containers (`collected`) it uses, keeping signatures minimal.

## Implementation
### Target file
`scripts/agent/tool_runner.py`

### Procedure
1. Write the red companion tests (see Companion test files) and confirm they fail.
2. Add `dispatched: set[str]` (new parameter) to `_recorded_call`, `_run_group_calls`,
   `_run_plan_batches` and `_execute_with_dag` next to each existing `collected` parameter,
   and pass it at every call site in the chain (including the two `_recorded_call` calls in
   the serial and gather paths of `_run_group_calls` and the `_run_group_calls` calls in
   `_run_plan_batches`).
3. In `execute_all_tool_calls`, extend the `_execute_with_dag(...)` call (514-519) with
   `state.dispatched_ids` (keyword `dispatched=state.dispatched_ids`).
4. In `_recorded_call`: `dispatched.add(pc.call_id)` immediately before the `try:` whose
   body awaits `execute_one_tool_call`; `dispatched.discard(pc.call_id)` after the
   `collected[pc.call_id] = error_row` write and after the `collected[pc.call_id] = result`
   write. One-line comment naming the in-flight/never-dispatched contract (REQ-001).
5. Run `uv run python tools/check_module_size.py` immediately after the edits. If
   `tool_runner.py` exceeds 20480 B: record a Blocker Log row in this document, stop before
   committing, and report to the owner (Plan Risks contingency); do not compact unrelated
   code.

### Method
Signature threading of one set parameter plus three statements in `_recorded_call`; no
branching added (radon ranks unchanged: A(2)/A(5)/B(9)/A(5)/B(7) ceilings).

### Details
- Line citations here predate blockio001's Pending `tool_runner.py` edits (its seq 04
  lands first per the memo order): expect line-number drift; anchor on the symbols
  (`_recorded_call`, `_run_group_calls`, `_run_plan_batches`, `_execute_with_dag`,
  `execute_all_tool_calls`) and re-verify before editing.
- The set is per round (`RoundState` instance per `execute_all_tool_calls` call) — no
  module-level or ctx-level state.
- `CancelledError` propagation semantics of `_recorded_call`'s `except Exception` are
  unchanged (its existing comment stays accurate).

### Companion test files
- `tests/agent/test_tool_runner.py` (companion of the `scripts/agent/tool_runner.py` row;
  Plan `Implementation Target Files` seq 08 covered here per the companion rule)
  - Procedure: add class `TestCancellationDispatchState` (new) using the file's existing
    helpers (`_make_ctx(_cfg(serial_tool_calls=True))`, `_tc`, `_approve_all()`,
    `ToolLoopGuard(ctx)`, `_saved_text`, `_saved_tool_ids`) with an `asyncio.Event`-driven
    blocking transport stub installed on `ctx.services_required.tools.execute` (a coroutine
    `side_effect` that sets a `started` event then awaits a never-set `hold` event):
    (i) `test_inflight_call_gets_the_outcome_unknown_row` (new): declare `c0`, `c1`
    (serial group, so `c1` never starts); run `execute_all_tool_calls` as an
    `asyncio.create_task`, `await started.wait()`, `task.cancel()`,
    `with pytest.raises(asyncio.CancelledError): await task`; assert exactly the two
    declared ids are saved, `_saved_text(ctx, "c0")` contains "outcome unknown" and "verify
    before repeating", `_saved_text(ctx, "c1")` contains "the tool round did not complete"
    (REQ-001, REQ-002; AC-001, AC-002, AC-003, AC-005). No sleeps: drive ordering only via
    the events, and release `hold` in a `finally`.
    (ii) `test_completed_call_keeps_its_real_result` (new): `c0` returns `_ok("done")`
    normally, `c1` blocks as above; cancel after `c1` starts; assert `c0`'s saved row is
    its real result (not a synthesized text) and `c1`'s is outcome-unknown (AC-004).
    (iii) `test_cancellation_before_any_dispatch_keeps_not_executed` (new): cancel the
    task after approval completes but before the transport `started` event fires (drive via
    `await asyncio.sleep(0)` ticks, no wall-clock sleeps on the round); assert every saved
    row is the not-executed round text (AC-002).
    (iv) Regression: every existing class (`TestMidRoundGuardStop`,
    `TestBatchFailureTotality`, `TestCompletedResultsSurviveAFailure`,
    `TestExecuteAllToolCalls`, `TestExecuteWithDag` and neighbors) stays byte-identical and
    green — guard-stop texts and completed results unchanged (REQ-003; AC-004).
  - Validation: `uv run pytest tests/agent/test_tool_runner.py -q` — new tests red before
    Procedure 2-4, green after.

## Compatibility considerations
- `tests/agent/test_tool_runner.py` is shared with blockio001's seq 08 document: land
  blockio001 first, then this document's class after it; the two add disjoint classes.
- The `_execute_with_dag` chain has no callers outside `tool_runner.py` and its own test
  file (its extra keyword `force_serial` pattern is preserved).
- Turn-persistence tests (`tests/agent/test_turn_persistence.py`) must stay green — the
  synthesized-row shapes are unchanged (Plan Regression row).
- Size gate is the critical checkpoint (Assumptions + Procedure 5). `tool_runner.py` adds no
  new public symbol (parameter only) — `tools/generate_reference_table.py --check` should
  report no drift.

## Security considerations
N/A: no new input; ids are internal.

## Rollback considerations
- Four signature additions plus three statements plus the new test class; revert the commit
  restores today's chain.

## Validation plan
1. `uv run pytest tests/agent/test_tool_runner.py -q` — new tests red before Procedure 2-4,
   green after (Plan Validation plan row 1).
2. Regression: `uv run pytest tests/agent/ -k "tool or round or pairing or persistence" -q`
   — green (Plan Validation plan row 4).
3. Static: `uv run ruff check scripts/agent/tool_runner.py tests/agent/test_tool_runner.py`,
   `uv run ruff format --check` on both, `uv run mypy --no-namespace-packages
   scripts/agent/tool_runner.py`.
4. Gates: `uv run radon cc scripts/agent/tool_runner.py -s` (ranks unchanged), `uv run
   python tools/check_module_size.py` (see Procedure 5 contingency), `uv run bandit -r
   scripts/agent/tool_runner.py -c pyproject.toml` (no new finding), `uv run lint-imports`.
5. The plan-wide validation sequence (`rules/toolchain.md`, diff-cover) runs once after all
   four code documents of this plan are executed.

## Completion criteria
- AC-001: the in-flight call's persisted row says the outcome is unknown and may have run.
- AC-002: the never-dispatched call keeps the not-executed text.
- AC-003: exactly one row per declared id. AC-004: completed calls keep real results and
  guard-stop texts are unchanged. AC-005: new tests red pre-change, green post-change.

## Out of Scope
- The enum member (seq 01), the text dict (seq 02), `RoundState.dispatched_ids` and the
  partition (seq 03), the docs paragraph (seq 05), the module-size baseline decision (owner
  action on Blocker), `repl_input_loop.py` graceful-shutdown behavior (Reference File).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write red companion cancellation tests, confirm they fail (Procedure 1; Companion test files) | Pending | — | — | Land after blockio001's seq 08 test class in the shared file |
| 2 | Thread `dispatched` through the four-function chain and mark in `_recorded_call` (Procedure 2-4) | Pending | — | — | Expect line drift from blockio001's tool_runner edits; anchor on symbols |
| 3 | Size-gate checkpoint and this document's checks (Procedure 5; Validation plan 2-4) | Pending | — | — | Blocker + stop-and-report if `tool_runner.py` exceeds 20480 B |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Requirement ID**: REQ-001 (dispatch marker before the transport await, cleared on
  collect), REQ-002/REQ-003/REQ-004 (end-to-end cancellation behavior)
- **Source issue**: issues/20261101-073608_inflightcancel001_cancelled-call-reported-unexecuted.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-144325_inflightcancel001_cancelled-call-reported-unexecuted.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-121149
- **Related target files**: `scripts/agent/tool_runner.py`, `tests/agent/test_tool_runner.py`
