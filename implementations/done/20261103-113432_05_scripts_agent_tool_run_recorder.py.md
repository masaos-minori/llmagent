## Goal

Split the round serialization-event recording so the `ctx.stats` bookkeeping stays on the
loop thread and each `save_serialization_event` write runs off the loop via
`asyncio.to_thread`, awaited per event in order (REQ-005; AC-5), leaving the caller-side
diff in `tool_runner.py` at a single `await` (that call site is the seq 04 document).

## Scope
**Release unit**: N/A: not part of a release unit

Covers the `scripts/agent/tool_run_recorder.py` row (seq 05) of
`plans/20261101-143807_blockio001_sync-sqlite-writes-block-event-loop.md`. No companion
test row of its own: the Plan assigns its tests to `tests/agent/test_tool_runner.py`
(covered by `implementations/20261103-113432_08_tests_agent_test_tool_runner.py.md`, which
writes the red tests first). Executes in the same commit as
`implementations/20261103-113432_04_scripts_agent_tool_runner.py.md` — between the two
edits the call site would await a non-coroutine, so run tests only after both land.

## Assumptions
- Verified against current source (20261103): `_record_round_serialization_events`
  (`scripts/agent/tool_run_recorder.py:83`) builds one `round_event` dict per
  `SerializationEvent`, appends it to `ctx.stats.stat_serialization_events` and adds
  `stat_serialization_total_overhead_ms`, then — when `ctx.diagnostics is not None` — calls
  `ctx.diagnostics.save_serialization_event` with keyword arguments (108-115). The module
  has no `import asyncio` yet.
- Sole caller is `tool_runner.py` (import at 49, call at 453); no test calls the function
  directly (rg 20261103) — serialization tests drive it through `execute_all_tool_calls`
  (e.g. `test_side_effect_calls_diagnostic_save`, tests/agent/test_tool_runner.py:1663), so
  the coroutine change reaches tests through awaited paths only.
- Module size 5552 B (gate 20480 B) — the ~100 B growth here is where the Plan's size-gate
  mitigation puts the offload glue (Plan Risks, added 20261103); `tool_runner.py` has only
  36 B of headroom.

## Design decisions
- Convert `_record_round_serialization_events` itself to `async def` and place the per-event
  `await asyncio.to_thread(ctx.diagnostics.save_serialization_event, ...)` inside the
  existing loop: stats appends and the `is not None` check stay synchronous (executed on the
  loop thread before each await); event order and payload values are unchanged. This
  satisfies REQ-005/AC-5 semantics transitively awaited from `_execute_with_dag` (seq 04
  awaits this coroutine before `_record_round_exec`) while keeping the `tool_runner.py` diff
  at `await` + 6 B (Plan Risks mitigation; deviation from the row wording's
  "synchronous step the async caller can offload" is deliberate and size-driven).
- `asyncio.to_thread` keyword arguments identical to the direct call (kwargs pass through
  unchanged, keeping `assert_called_once_with`-style existing assertions valid).

## Alternatives considered
- Keeping the function synchronous and returning per-event save arguments for a `to_thread`
  loop in `_execute_with_dag`: rejected — ~90 B pushed onto `tool_runner.py`'s 36 B
  headroom, guaranteeing the size gate fails with no behavioral gain.
- Batching all serialization saves into one worker call: rejected by REQ-005 ("once per
  serialization event and in event order").

## Implementation
### Target file
`scripts/agent/tool_run_recorder.py`

### Procedure
1. Confirm the red serialization responsiveness test from the seq 08 document exists and
   fails.
2. Add `import asyncio` to the module imports.
3. Change `def _record_round_serialization_events(` (tool_run_recorder.py:83) to
   `async def`; inside the per-event loop, keep the stats append and overhead add
   synchronous, and replace the direct `ctx.diagnostics.save_serialization_event(...)`
   (108-115) with `await asyncio.to_thread(ctx.diagnostics.save_serialization_event, ...)`
   carrying the identical keyword arguments under the unchanged
   `if ctx.diagnostics is not None:` guard.

### Method
Keyword change + one call-site wrap inside the existing loop; payload construction, stats
entries and function arguments unchanged.

### Details
- The `ts = now_iso_raw()` timestamp stays loop-side, computed once per round before the
  loop (unchanged).
- No containment added (UNK-02 unchanged: a failing save re-raises in the awaiting
  coroutine).
- radon: one `await` adds no branch; the function's rank must not increase.

### Companion test files
- None of its own. The row's Plan tests (tests/agent/test_tool_runner.py, seq 08 row) are
  owned by the seq 08 document; this document contributes the production half its
  serialization tests verify.

## Compatibility considerations
- `tool_runner.py:453` must gain `await` in the same commit (seq 04 Procedure 4); without
  it the function would never be awaited (RuntimeWarning + behavior break).
- Existing serialization tests (`test_side_effect_calls_diagnostic_save` and neighbors)
  pass unchanged (REQ-007): MagicMock diagnostics are callable through `asyncio.to_thread`.
- No `docs/` change; no public symbols (underscore-private) — no manifest regeneration.

## Security considerations
N/A: unchanged payloads; only the executing thread moves.

## Rollback considerations
N/A: revert the commit (with seq 04); no config or schema change.

## Validation plan
1. `uv run pytest tests/agent/test_tool_runner.py -q` after the seq 04 change lands in the
   same commit — seq 08 serialization tests green, existing serialization tests unchanged.
2. Static: `uv run ruff check scripts/agent/tool_run_recorder.py`, `uv run ruff format
   --check`, `uv run mypy scripts/agent/tool_run_recorder.py`, bandit (no new finding);
   `radon cc scripts/agent/tool_run_recorder.py -s` (no rank increase); `uv run python
   tools/check_module_size.py` (5552 B + ~100 B, ample).
3. The plan-wide validation sequence (`rules/toolchain.md`, diff-cover) runs once after all
   six documents are executed.

## Completion criteria
- AC-5: each `save_serialization_event` runs on a worker thread, once per event in event
  order, and `ctx.stats.stat_serialization_events` /
  `stat_serialization_total_overhead_ms` keep the same entries appended on the loop thread.
- The seq 08 responsiveness test shows a loop callback firing while the write is blocked.

## Out of Scope
- The `_execute_with_dag` call-site `await` (seq 04) and the red tests (seq 08).
- `_record_pending_state` / `_finalize_state` `tool_call_state` writes (UNK-03, out of plan).
- Containment for these writes (UNK-02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm seq 08 red serialization test exists and fails | Completed | 20261103-172500 | 20261103-174428 | Seq 08 serialization red test confirmed failing (see seq 08 doc). |
| 2 | `import asyncio`, `async def`, per-event `to_thread` wrap (Procedure 2-3) | Completed | 20261103-174000 | 20261103-174428 | import asyncio + async def + per-event await asyncio.to_thread wrap landed; stats appends stayed synchronous; kwargs verbatim. |
| 3 | Run this document's checks with seq 04 in the same commit (Validation plan 1-2) | Completed | 20261103-174428 | 20261103-181609 | Validation 1-2 all green (91/91 test_tool_runner incl. seq 08 serialization test; ruff/format/mypy/bandit clean; radon _record_round_serialization_events stays A(3); size 5783 B ample). Commit blocked by the seq 04 tool_runner.py size-gate Blocker (see 04 doc Blocker Log). Commit unblocked by owner's baseline approval (agent/tool_runner.py 21000 B). Recorder 5783 B ample; radon A(3) unchanged; all Validation 1-2 green. |

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
- **Requirement ID**: REQ-005 (stats bookkeeping on the loop thread; per-event diagnostic
  write off the loop in event order), REQ-007 (existing serialization tests unchanged)
- **Source issue**: issues/20261003-180333_blockio001_sync-sqlite-writes-block-event-loop.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-143807_blockio001_sync-sqlite-writes-block-event-loop.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-113432
- **Related target files**: `scripts/agent/tool_run_recorder.py` (its row's tests are
  covered by the seq 08 document; see Companion test files)