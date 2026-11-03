## Goal

Give `ToolLoopGuard` an opt-in deferral mode: a constructor keyword (default off) that
records guard-hint payloads into a pending list instead of writing synchronously, plus an
async flush that persists them in recorded order off the event loop through the existing
contained save step (REQ-001; AC-1). With the keyword off, `check_*` and `_save_guard_hint`
behave exactly as today (REQ-007; AC-1 default half).

## Scope
**Release unit**: N/A: not part of a release unit

Covers the `scripts/agent/tool_loop_guard.py` row (seq 01) and its companion test row
`tests/agent/test_tool_loop_guard.py` (seq 06, companion-eligible, no document of its own)
of `plans/20261101-143807_blockio001_sync-sqlite-writes-block-event-loop.md`. Execution
order for the whole plan: this document first (the deferral API other documents call),
then seq 08 (red tool-runner tests), seq 05, seq 04, seq 02, seq 03, then the plan-wide
validation.

## Assumptions
- Verified against current source (20261103): `_save_guard_hint` is a `@staticmethod`
  (`scripts/agent/tool_loop_guard.py:138`) that builds the payload (fields + `guard_type` +
  `now_iso_raw()` timestamp), skips when `ctx.diagnostics is None`, and saves inside
  `try/except Exception` with the `kind=guard_hint` warning (152-159). The six call sites
  (207, 260, 322, 369, 394, 425) all call it as `self._save_guard_hint(self._ctx, ...)`
  from `check_empty_result_repeat`, `check_unavailable_repeat`, `check_cycle`,
  `_check_progress_stagnation`, `check_dedup` and `check_retry`. `__init__` is
  `(self, ctx)` at 101.
- `tests/agent/test_tool_loop_guard.py` `TestSaveGuardHintContainment` (659) calls
  `ToolLoopGuard._save_guard_hint(ctx, "dedup", tool="write_file")` statically; the
  additive design below keeps that call working unchanged (REQ-007).
- The existing deferral-off tests (`ctx.diagnostics.save.assert_called_once()` after
  `check_*`) pass through the delegation path unchanged; `tests/agent/test_tool_loop_guard_wiring.py`
  exists and drives guards through the runner.
- `tool_loop_guard.py` is 19032 B (gate 20480 B) — the ~200 B addition fits.
- UNK-01 (ConfigLoader thread safety) belongs to the write sites that call
  `asyncio.to_thread`; it is settled during seq 03/04 execution and does not gate this
  document (the guard flush is one of those sites; the resolution is recorded there).

## Design decisions
- Additive shape (Plan D2 option c, kept): keep the static `_save_guard_hint(ctx, ...)` as
  today; extract its contained persist step into a new static
  `_persist_guard_hint_payload(ctx, payload)` (new) that both `_save_guard_hint` and the
  flush reuse, so the containment/warning text exists exactly once (Plan REQ-001 "reusing
  the existing contained persist step").
- New constructor keyword `defer_hints: bool = False` (keyword-only) and instance state
  `self._pending_guard_hints: list[dict[str, object]]` (new); a new instance method
  `_record_guard_hint(self, guard_type, **fields)` (new) either appends the
  event-time payload (defer on) or delegates to the unchanged static save (defer off); the
  six `check_*` call sites switch from `self._save_guard_hint(self._ctx, ...)` to
  `self._record_guard_hint(...)`.
- New `async def flush_guard_hints(self)` (new): returns without a thread hop when nothing
  is pending; otherwise drains the list in recorded order, each payload through
  `await asyncio.to_thread(self._persist_guard_hint_payload, self._ctx, payload)`.
- Timestamp stays event-time: the payload (including `now_iso_raw()`) is captured at
  record time, per Plan D2's "stores the payload, not a closure".

## Alternatives considered
- Converting `_save_guard_hint` to an instance method: rejected — it breaks the static call
  in `TestSaveGuardHintContainment` (`ToolLoopGuard._save_guard_hint(ctx, ...)`), a change
  REQ-007 does not license.
- Async `check_*` methods / always-on pending queue: rejected by the Plan (Design D2).

## Implementation
### Target file
`scripts/agent/tool_loop_guard.py`

### Procedure
1. Write the red companion tests (see Companion test files) and confirm they fail (the
   keyword/methods do not exist yet).
2. In `__init__` (tool_loop_guard.py:101): add keyword-only `defer_hints: bool = False`,
   store `self._defer_hints`, and initialize `self._pending_guard_hints: list[dict[str,
   object]] = []`; state in the docstring that the mode defers hint writes to
   `flush_guard_hints` (new) and why (blocking SQLite write off the loop).
3. Extract the contained save from `_save_guard_hint` into static
   `_persist_guard_hint_payload(ctx, payload)` (new): `ctx.diagnostics is None` guard, the
   `try/except Exception` block and the existing warning text move there unchanged;
   `_save_guard_hint` builds the payload and delegates to it.
4. Add instance `_record_guard_hint(self, guard_type, **fields)` (new): build the payload
   exactly as `_save_guard_hint` does (timestamp at event time); when `self._defer_hints`,
   append it to `self._pending_guard_hints` and return; otherwise call
   `self._persist_guard_hint_payload(self._ctx, payload)`. Switch the six call sites (207,
   260, 322, 369, 394, 425) to `self._record_guard_hint(guard_type, ...)`.
5. Add `async def flush_guard_hints(self)` (new) per the Design decision; import `asyncio`
   at module top.

### Method
Additive API plus a one-step extraction inside the existing save helper; no `check_*`
branch or threshold logic changes.

### Details
- `_save_guard_hint` keeps its signature and payload building so the static containment
  test (`TestSaveGuardHintContainment`) and any external use stay valid.
- `radon cc`: `_save_guard_hint` B-decomposition splits one branch into the extracted
  helper; no method may rise above its current rank (recheck `radon cc
  scripts/agent/tool_loop_guard.py -s` after the change).
- Deferred hints with `ctx.diagnostics is None`: the `is None` guard lives in the persist
  step; `_record_guard_hint` (new) may still queue a payload — flush then no-ops per payload
  inside the persist step (same behavior as today's synchronous no-op).

### Companion test files
- `tests/agent/test_tool_loop_guard.py` (companion of the `scripts/agent/tool_loop_guard.py`
  row; Plan `Implementation Target Files` seq 06 covered here per the companion rule)
  - Procedure: add a `TestGuardHintDeferral` (new) class next to
    `TestSaveGuardHintContainment`, using the file's existing `_make_ctx` fixture pattern:
    (i) deferral on + a tripped `check_unavailable_repeat` records no
    `ctx.diagnostics.save` call until `await guard.flush_guard_hints()` runs, then save is
    called once per recorded hint in recorded order (REQ-006(c); AC-1); (ii) two hints
    recorded across two checks flush in order with distinct `guard_type` payload fields;
    (iii) the payload `timestamp` is the event-time value (monkeypatch
    `agent.tool_loop_guard.now_iso_raw` before the check and assert it appears in the flush
    save call); (iv) flush contains a `save` `RuntimeError` with the existing
    `kind=guard_hint` warning and still flushes the remaining hint (REQ-006(c)); (v) flush
    with nothing pending completes without a thread hop (monkeypatch a spy over
    `asyncio.to_thread` and assert it is not called).
  - Procedure: add the flush responsiveness test (REQ-006(a); AC-6): stub
    `ctx.diagnostics.save` to block on a `threading.Event` (blocks only the worker
    thread), run `flush_guard_hints` (new) as a task, assert a callback scheduled with
    `loop.call_soon` fires while the write is blocked, then set the event and assert the
    task completes; never sleep on the loop.
  - Procedure: leave every existing test unchanged — deferral-off default behavior is
    proven by the suite passing as-is (REQ-006(b); AC-1).
  - Validation: `uv run pytest tests/agent/test_tool_loop_guard.py -q` — new tests red
    before Procedure 2, green after Procedure 5.

## Compatibility considerations
- `ToolLoopGuard(self._ctx)` construction sites (executor 89, tests) are unaffected: the
  keyword defaults to off (REQ-001, REQ-007).
- No `docs/` change (Plan Documentation Impact N/A). `uv run python
  tools/generate_reference_table.py --check` after implementation: new methods are private
  or class members — regenerate manifests only if the checker reports drift.
- The two public-ish symbols this document adds (`_record_guard_hint` (new),
  `flush_guard_hints` (new)) are underscore-private, so no manifest regeneration is expected
  (dupcallid001 lesson: only public symbols force regeneration).

## Security considerations
- Payloads queued between check and flush live in process memory only until flushed; they
  pass through the same `DiagnosticStore.save` guard as the synchronous path (no new
  trust-boundary bypass).

## Rollback considerations
- Single-file additive change plus tests; revert the commit restores today's behavior. No
  config or schema change.

## Validation plan
1. `uv run pytest tests/agent/test_tool_loop_guard.py tests/agent/test_tool_loop_guard_wiring.py -q`
   — new tests red before Procedure 2, all green after Procedure 5 (Validation plan row 1).
2. Static: `uv run ruff check scripts/agent/tool_loop_guard.py tests/agent/test_tool_loop_guard.py`,
   `uv run ruff format --check` on both, `uv run mypy scripts/agent/tool_loop_guard.py` —
   no findings.
3. `radon cc scripts/agent/tool_loop_guard.py -s` — no method rank increase; `uv run bandit
   -r scripts/agent/tool_loop_guard.py -c pyproject.toml` — no new finding; `uv run python
   tools/check_module_size.py` — stays under the gate (19032 B + ~200 B).
4. The plan-wide validation sequence (`rules/toolchain.md`, diff-cover) runs once after all
   six documents of this plan are executed.

## Completion criteria
- AC-1: with deferral on, no `save` until the flush; then one contained `save` per hint in
  order, off the loop, with the event-time timestamp; with deferral off every existing
  assertion passes unchanged.
- Flush with nothing pending makes no thread hop; a failing save degrades to the existing
  warning without escaping `flush_guard_hints` (new).

## Out of Scope
- Enabling the keyword in production (`scripts/agent/llm_turn_executor.py`, seq 02) and
  awaiting the flush in `run()` (`scripts/agent/llm_turn_runner.py`, seq 03).
- `DiagnosticStore` internals (read-only per REQ-007) and UNK-02 containment for other
  write sites.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write red companion tests, confirm they fail (Procedure 1; Companion test files) | Completed | 20261103-165600 | 20261103-170600 | `TestGuardHintDeferral` 6 cases incl. loop-responsiveness; red confirmed (TypeError: unexpected keyword `defer_hints`) |
| 2 | Implement keyword, pending list, payload extraction, `_record_guard_hint` (new), `flush_guard_hints` (new) (Procedure 2-5) | Completed | 20261103-165600 | 20261103-170600 | `asyncio` imported; `_persist_guard_hint_payload` extracted (warning text once); six call sites switched to `_record_guard_hint`; static `_save_guard_hint` signature kept |
| 3 | Run this document's checks (Validation plan 1-3) | Completed | 20261103-165600 | 20261103-170600 | pytest guard+wiring 58 passed; ruff check+format clean; mypy clean; radon: no rank increase (`_save_guard_hint` B→A(1), new methods A); bandit no new finding; reference_table --check: no drift; NOTE: doc's "~200 B" estimate was low — actual addition ~1370 B, docstrings compressed to fit the gate: 20403 B < 20480 B (was 19032 B) |

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
- **Requirement ID**: REQ-001 (opt-in deferral mode and awaited async flush; default off is
  byte-for-byte today's behavior), REQ-007 (no change to `DiagnosticStore`; existing guard
  tests pass unchanged)
- **Source issue**: issues/20261003-180333_blockio001_sync-sqlite-writes-block-event-loop.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-143807_blockio001_sync-sqlite-writes-block-event-loop.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-113432
- **Related target files**: `scripts/agent/tool_loop_guard.py`, `tests/agent/test_tool_loop_guard.py`