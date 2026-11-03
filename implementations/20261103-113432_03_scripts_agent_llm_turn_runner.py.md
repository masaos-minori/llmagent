## Goal

Make `LLMTurnRunner` free the event loop while its diagnostic writes run: `run()` awaits
`flush_guard_hints` (new) after every guard check it makes (before finalizing, returning a
`TurnResult`, or continuing), and `_handle_llm_error` runs its three diagnostic writes
through `await asyncio.to_thread` in the current order with the existing per-write
containment and warning logs unchanged (REQ-002, REQ-003; AC-2, AC-3).

## Scope
**Release unit**: N/A: not part of a release unit

Covers the `scripts/agent/llm_turn_runner.py` row (seq 03) and its companion test row
`tests/agent/test_llm_turn_runner.py` (seq 07, companion-eligible, no document of its own)
of `plans/20261101-143807_blockio001_sync-sqlite-writes-block-event-loop.md`. Runs after
`implementations/20261103-113432_01_scripts_agent_tool_loop_guard.py.md` (the flush method
it awaits is declared there) and after seq 02 (production deferral wiring); it is the last
code document of the plan before the plan-wide validation.

## Assumptions
- Verified against current source (20261103): `run()` guard sites —
  `self._guard.check_all(...)` followed by `return await self._finalize_after_guard()`
  (`scripts/agent/llm_turn_runner.py:139-146`), `check_empty_result_repeat` (169-172),
  `check_unavailable_repeat` (173-175), `check_error_limit` (177-178); the module has no
  `import asyncio` yet (checked by grep). `run()` is radon C(15).
- `_handle_llm_error` (189-247+): three contained writes — `save` for `llm_transport_error`
  (203-210), `save_partial_completion` (217-223), `save` for `mid_turn_error` (233-247),
  each inside `try/except Exception` with its own warning text;
  `stat_partial_completions` update (229) is outside the writes.
- `check_error_limit` produces no guard hint (`_save_guard_hint` call sites are only the
  six listed in the seq 01 document), so no flush is needed after it; its `TurnResult`
  return path is unchanged.
- Companion tests can reuse the file's patterns: `_make_ctx()` (30, MagicMock ctx),
  `patch.object(runner, "_stream_llm", AsyncMock(...))` (e.g. 243, 443),
  `patch("agent.llm_turn_runner.execute_all_tool_calls", ...)` (468-469), and the existing
  `_handle_llm_error` refusal tests (383, 411) that call `_handle_llm_error` directly with
  MagicMock diagnostics.
- Module size 15064 B (gate 20480 B) — ample headroom for this file.

## Design decisions
- Three explicit `await self._guard.flush_guard_hints()` statements placed immediately
  after the three guard checks, each check rewritten from `if msg := check(...)` to a named
  assignment + unconditional flush + `if msg:` — deviating from Plan D3's "one private
  async helper": the rewrite adds zero decision points (walrus removal and awaits are not
  branches), keeps `run()` at C(15), and a helper method would add indirection and bytes
  without a complexity gain. The radon check (Validation plan 3) enforces the D3 constraint
  that matters.
- Flush after every check (trip or not), satisfying REQ-002 "after every guard check ...
  before it finalizes, returns a `TurnResult`, or continues"; the flush is a no-op without
  a thread hop when nothing is pending (seq 01 contract), so non-trip iterations pay no
  cost.
- `_handle_llm_error` offload: wrap each call in place —
  `await asyncio.to_thread(ctx.diagnostics.save, ...)` /
  `await asyncio.to_thread(ctx.diagnostics.save_partial_completion, ...)` keeping the exact
  positional/keyword arguments, `try/except Exception` blocks and warning texts
  (REQ-003); containment semantics are identical because `asyncio.to_thread` re-raises the
  worker exception in the awaiting coroutine (Plan Risks note).

## Alternatives considered
- Plan D3's private flush helper wrapping check-and-flush: rejected for this file as above
  (indirection with no branch-count benefit); the Plan's binding constraint (no complexity
  increase) is met by the explicit-await form.
- Offloading the guard flush at the executor instead of the runner: rejected — REQ-002
  names the runner's per-check ordering.

## Implementation
### Target file
`scripts/agent/llm_turn_runner.py`

### Procedure
1. Write the red companion tests (see Companion test files) and confirm they fail against
   the current synchronous implementation.
2. Add `import asyncio` to the module imports.
3. In `run()`, rewrite the three guard sites (139, 169, 173) as named assignment +
   `await self._guard.flush_guard_hints()` + `if guard_msg:` return, preserving each
   site's current return (`_finalize_after_guard()` for check_all; the fail `TurnResult`
   with `answer=guard_msg` and the same `reason` for the other two). Do not touch the
   `check_error_limit` site.
4. In `_handle_llm_error`, wrap the three diagnostic calls (203, 217, 233) in
   `await asyncio.to_thread(...)` as described in Design decisions; keep everything else —
   the `ctx.diagnostics is not None` guards, both `except Exception` clauses and their
   `# noqa` comments, warning texts, `stat_partial_completions`, and the returned
   `TurnResult`s — unchanged.

### Method
In-place call-site rewrites; no new methods, no signature changes.

### Details
- UNK-01 (blocking at implementation time, per the Plan): read
  `scripts/shared/config_loader.py`'s load path before finishing this step; `DiagnosticStore.save`
  calls it from the worker thread. If the load path is not safe against concurrent
  loop-thread reads, serialize at this offload site (e.g. a module-level `asyncio.Lock`
  guarding the to_thread calls) without touching `diagnostic_store.py`, and record the
  outcome in this document's Notes.
- `asyncio.to_thread` argument style: keep the exact same positional/keyword arguments the
  direct calls use, moved after the callable.
- The cancelled-turn Risk (worker write outliving a cancelled turn) is accepted by the Plan;
  no code response here.

### Companion test files
- `tests/agent/test_llm_turn_runner.py` (companion of the `scripts/agent/llm_turn_runner.py`
  row; Plan `Implementation Target Files` seq 07 covered here per the companion rule)
  - Procedure: add a partial-path responsiveness test (new): `_make_ctx()` with a
    `threading.Event`-blocking stub for `ctx.diagnostics.save` (blocks only the worker
    thread) and a recording stub for `ctx.diagnostics.save_partial_completion`; run
    `runner._handle_llm_error(...)` as a task with an `LLMTransportError` carrying
    `partial_text`; assert a `loop.call_soon` callback fires while `save` is blocked, that
    `save_partial_completion` has not been called yet, then set the event and assert the
    task returns the same fail `TurnResult` the existing refusal tests assert — each write
    completes before the next and before the return (REQ-006(a), REQ-003; AC-3, AC-6).
  - Procedure: add the mid-turn-path version (new): `LLMTransportError` without
    `partial_text`, same pattern around the single `save` call.
  - Procedure: add the run() flush-order tests (new) following the existing run() patch
    pattern (`_stream_llm` AsyncMock with a tool_calls message,
    `patch("agent.llm_turn_runner.execute_all_tool_calls", AsyncMock(...))`): (i) trip —
    the MagicMock guard's `check_all` returns a message, `flush_guard_hints` (new) is an
    AsyncMock, and a `MagicMock` manager records call order asserting the flush await
    happens before the finalize path returns the `TurnResult` (REQ-006(d); AC-2); (ii)
    non-trip — all three checks return None and the manager order shows
    `check_all → flush → ... → check_empty_result_repeat → flush → check_unavailable_repeat
    → flush` across one loop iteration (REQ-002).
  - Procedure: keep the existing refusal tests (`test_handle_llm_error_does_not_propagate_*`,
    383, 411) unchanged — they prove containment survives the offload (AC-3 third clause).
  - Validation: `uv run pytest tests/agent/test_llm_turn_runner.py -q` — new tests red
    before Procedure 2-4, green after.

## Compatibility considerations
- No signature, `TurnResult` shape, or return-path change; `run()` and `_handle_llm_error`
  callers (`llm_turn_executor.py`, workflow adapter) are untouched.
- Existing tests pass unchanged except the new additions (REQ-007): the refusal tests keep
  proving containment through `to_thread` re-raise.
- No `docs/` change (Plan Documentation Impact N/A).

## Security considerations
- Diagnostic payloads are unchanged; only their execution thread moves (AC-3). No new
  input handling.

## Rollback considerations
- Single-file change plus tests; revert the commit restores synchronous writes.

## Validation plan
1. `uv run pytest tests/agent/test_llm_turn_runner.py tests/agent/test_llm_turn_executor.py -q`
   — red before Procedures 2-4, green after; existing tests unchanged.
2. Static: `uv run ruff check scripts/agent/llm_turn_runner.py tests/agent/test_llm_turn_runner.py`,
   `uv run ruff format --check` on both, `uv run mypy scripts/agent/llm_turn_runner.py`.
3. Complexity: `uv run radon cc scripts/agent/llm_turn_runner.py -s -n C` — `run` stays
   exactly C(15), no new grade C-or-worse function (Plan gate). Size: `uv run python
   tools/check_module_size.py` (15064 B, ample). Bandit: no new finding.
4. UNK-01 config_loader read and outcome recorded in Execution Status Notes (Assumptions).
5. The plan-wide validation sequence (`rules/toolchain.md`, diff-cover) runs once after all
   six documents are executed.

## Completion criteria
- AC-2: on a guard trip and on non-trip iterations, the flush await follows each guard
  check before the return/proceed, pinned by the manager-order tests.
- AC-3: no diagnostic write executes on the loop thread; writes complete sequentially
  before the `TurnResult`; a raising write still degrades to the existing warning and same
  `TurnResult` (existing refusal tests green).
- AC-6: loop callbacks fire while stubbed writes block; the awaiting coroutine finishes
  only after release.

## Out of Scope
- The deferral mode itself (seq 01) and its enablement (seq 02).
- `execute_all_tool_calls` internals and the tool-runner write sites (seq 04/05/08).
- Containment for `_record_transport_failure` / serialization writes (UNK-02, out of plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write red companion tests, confirm they fail (Procedure 1; Companion test files) | Pending | — | — | |
| 2 | Add `import asyncio`, rewrite the three guard sites with flush awaits (Procedure 2-3) | Pending | — | — | |
| 3 | Offload the three `_handle_llm_error` writes via `asyncio.to_thread` (Procedure 4) | Pending | — | — | |
| 4 | UNK-01 config_loader read; run this document's checks (Validation plan 2-4) | Pending | — | — | |

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
- **Requirement ID**: REQ-002 (flush awaited after every guard check before
  finalize/return/continue), REQ-003 (`_handle_llm_error` writes off the loop, sequential,
  containment unchanged), REQ-006 (responsiveness/order tests)
- **Source issue**: issues/20261003-180333_blockio001_sync-sqlite-writes-block-event-loop.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-143807_blockio001_sync-sqlite-writes-block-event-loop.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-113432
- **Related target files**: `scripts/agent/llm_turn_runner.py`, `tests/agent/test_llm_turn_runner.py`
