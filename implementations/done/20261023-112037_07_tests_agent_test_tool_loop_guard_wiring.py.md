## Goal

Create `tests/agent/test_tool_loop_guard_wiring.py`, the first module that asserts the
empty-result guard reaches the tool-execution path end to end. It proves mid-batch
visibility for both group shapes, the inert-option case, the turn-level
`reason="empty_result_repeat"` acceptance case, and no leak across turns
(`REQ-007`, `AC-2`, `AC-4`, `AC-5`, `AC-6`).

## Scope

New file `tests/agent/test_tool_loop_guard_wiring.py` (create). No existing file asserts that
the guard reaches `tool_runner`; this Plan's turn-level acceptance criterion needs one home
that is not a mocked entry point. Reference reads only:
- `tests/agent/test_tool_loop_guard.py:360-413` — the option/default assertions to reuse.
- `tests/agent/test_llm_turn_runner.py:397-518` — the mocking pattern that hid the gap.
- `scripts/agent/llm_turn_executor.py:73-102` — the per-turn construction the test drives.
- `scripts/agent/config_dataclasses.py:178` — the `<= 0` default meaning.

## Assumptions

- `tool_empty_result_max_repeats` defaults to `0` (`config_dataclasses.py:178`); `<= 0`
  keeps the feature disabled (`record_tool_result` early-returns at `tool_loop_guard.py:159-160`).
- A stub tool that returns `""` synchronously and fast avoids wall-clock flakiness.
- The guard's `_empty_result_counts` is observable directly for the mid-batch visibility
  assertion.

## Design decisions

- **Drive the real executor and a real `ToolLoopGuard`** (no mocked entry point), so the
  acceptance runs the unmocked path (`AC-6`/`AC-7`). The stub tool observes its own calls via
  a counter the test controls.
- **Assert mid-batch visibility** by checking `guard._empty_result_counts` while a later call
  of the same batch is still pending — this is the exact gap `tool002` needs recorded.
- **One group shape per visibility test**: one sequential-group test and one gathered-group
  test, so both scheduling shapes (`tool_runner.py` `:69-73` and `:74`) are covered.

## Alternatives considered

- Asserting only the final `TurnResult` — insufficient: it proves the guard fired but not
  that the count was visible *during* the batch (`AC-2`).
- Reusing an existing turn test — rejected: every existing turn test replaces the entry point
  with a mock (`test_llm_turn_runner.py:397`, `:436`, `:485`, `:518`, `:583`), so the gap is
  invisible there.

## Implementation

### Target file

`tests/agent/test_tool_loop_guard_wiring.py` (new)

### Procedure

1. A helper that builds a real `ToolLoopGuard` and a stub tool returning `""` N times, with a
   call counter the test can inspect.
2. Sequential-group visibility test: with `max_repeats=2`, three `""` results in one turn,
   assert the turn returns `TurnResult(action="fail", answer=msg, reason="empty_result_repeat")`
   and that `guard._empty_result_counts[tool_name]` was non-zero while a later batch call was
   still executing.
3. Gathered-group visibility test: same as (2) through the gathered path.
4. Inert-option case: `max_repeats=0` (default) never fires; the loop exhausts
   `max_tool_turns` without `empty_result_repeat`.
5. No-leak-across-turns case: counts from one turn do not carry into the next.

### Method

- Reuse the option/default fixture pattern from `test_tool_loop_guard.py:360-413`.
- Construct the turn via `LLMTurnExecutor.handle_llm_turn` (`llm_turn_executor.py:83`), which
  builds one `ToolLoopGuard` per turn and hands it to `LLMTurnRunner`.
- For the stub tool, register a tool whose coroutine returns `ToolCallResult(output="",
  is_error=False, ...)` and increments a test-visible counter on each call.
- Set `tool_empty_result_max_repeats=2` on the turn config; set `max_tool_turns` to the
  minimum that reaches the threshold.

### Details

- The mid-batch visibility assertion reads `guard._empty_result_counts` from within the stub
  tool's observation (the stub sees its own count already incremented by an earlier call in
  the same batch).
- The no-leak case runs two turns with the same guard-less executor and asserts the second
  turn starts from zero counts.
- No time bounds are asserted anywhere.

## Compatibility considerations

### Corrections found while implementing

- New module written with real `ToolLoopGuard`, real `execute_all_tool_calls` and `LLMTurnRunner`; the stub tool observes the guard counts mid-batch for sequential and gathered groups (the gathered stub waits briefly so the earlier calls have finished). Added a call-site check that the runner passes its own guard. Mutation checks (recording removed; `guard=` not passed) fail 3 and 9 tests.


- New module; imported by the normal `tests/agent` collection. Add no import edge that breaks
  `lint-imports`.

## Security considerations

- N/A: tests only.

## Rollback considerations

- N/A: revert the commit; the module is self-contained.

## Validation plan

- `uv run pytest tests/agent/test_tool_loop_guard_wiring.py -q` — all cases green.
- Mutation/removal gates (`AC-7`): removing the recording call makes the visibility cases red;
  removing the `max_repeats=2` setting makes the acceptance case red. Each removal must turn
  the suite red.
- `uv run pytest tests/agent -q` — full suite green (plus this module); 7 permanent skips
  unchanged.

## Completion criteria

The module exists with the four case families; both group shapes show mid-batch visibility;
the inert-option and no-leak cases hold; the turn-level `empty_result_repeat` acceptance
passes; each AC-7 removal turns the suite red; the full `tests/agent` suite passes.

## Out of Scope

- The production threading/recording (`scripts/agent/tool_runner.py`, row 1;
  `scripts/agent/llm_turn_runner.py`, row 2).
- The docstring correction (row 3).
- The existing test call-site migrations (rows 4-6).
- Reference regeneration (row 8).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Build helper: real guard + stub tool returning "" with a call counter | Completed | 20261023-163755 | 20261023-163755 | reuse test_tool_loop_guard.py:360-413 pattern implemented; full suite 9909 passed |
| 2 | Sequential- and gathered-group mid-batch visibility tests | Completed | 20261023-163755 | 20261023-163755 | AC-2; read guard._empty_result_counts inside stub |
| 3 | Inert-option (max_repeats<=0) and no-leak-across-turns cases | Completed | 20261023-163755 | 20261023-163755 | AC-4, AC-5 |
| 4 | Turn-level empty_result_repeat acceptance case | Completed | 20261023-163755 | 20261023-163755 | AC-6; real executor, no mock |
| 5 | Run validation + AC-7 removal gates (`rules/toolchain.md`) | Completed | 20261023-163755 | 20261023-163755 | each removal turns suite red |

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
- **Requirement ID**: `REQ-007`
- **Source issue**: `issues/20261021-093421_tool001_empty-result-loop-guard-is-never-wired.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-092413_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-112037
- **Related target files**: `tests/agent/test_tool_loop_guard_wiring.py`