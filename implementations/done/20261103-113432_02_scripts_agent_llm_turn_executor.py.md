## Goal

Turn the guard deferral mode on for the production `ToolLoopGuard` by passing the
`defer_hints` (new) keyword at the sole construction site, and pin that wiring with a test
(REQ-002; AC-2 second half, REQ-006(e)).

## Scope
**Release unit**: N/A: not part of a release unit

Covers the `scripts/agent/llm_turn_executor.py` row (seq 02) and its companion test row
`tests/agent/test_llm_turn_executor.py` (seq 09, companion-eligible, no document of its
own) of `plans/20261101-143807_blockio001_sync-sqlite-writes-block-event-loop.md`. Runs
after `implementations/20261103-113432_01_scripts_agent_tool_loop_guard.py.md` — the
keyword it passes is declared there.

## Assumptions
- Verified against current source (20261103): `ToolLoopGuard(self._ctx)` at
  `scripts/agent/llm_turn_executor.py:89` inside `handle_llm_turn` is the only production
  construction site (`rg "ToolLoopGuard\(" scripts` finds only this line).
- `tests/agent/test_llm_turn_executor.py` `_run_turn` (line 23) patches
  `agent.llm_turn_executor.ToolLoopGuard` (line 28) without inspecting constructor
  arguments, so the new assertion is an addition, not a rewrite.
- `defer_hints` (new) is declared by the earlier sibling document (seq 01); this document
  adds no new symbol.
- Module size 4237 B (gate 20480 B) — trivial growth.

## Design decisions
N/A: the Plan fixes this change (enable the seq 01 keyword at the sole site); no file-level
decision remains.

## Alternatives considered
N/A: the Plan rejected other ways to enable the mode; the construction-site keyword is the
chosen mechanism (Plan D2).

## Implementation
### Target file
`scripts/agent/llm_turn_executor.py`

### Procedure
1. Write the red companion test (see Companion test files) and confirm it fails against the
   current construction call.
2. Change line 89 to `ToolLoopGuard(self._ctx, defer_hints=True)`.

### Method
One constructor argument; nothing else in `handle_llm_turn` changes.

### Details
- The keyword is keyword-only (declared by seq 01), so pass it by name.
- Keep the existing comment context; optionally extend the nearby comment to name the
  deferral (the guard's hint writes are flushed by `LLMTurnRunner.run()` — seq 03), per the
  Plan's Risk mitigation that the keyword's docstring names the blocking trade-off.

### Companion test files
- `tests/agent/test_llm_turn_executor.py` (companion of the `scripts/agent/llm_turn_executor.py`
  row; Plan `Implementation Target Files` seq 09 covered here per the companion rule)
  - Procedure: add a test (new) in the file that runs `_run_turn` and asserts the patched
    `ToolLoopGuard` mock was called once with `defer_hints=True` in its keyword arguments —
    capture the mock instance (e.g. `patch(..., autospec=True)` or a `MagicMock` bound in a
    `with` block) instead of discarding it, keeping the existing `_run_turn` patch stack
    otherwise unchanged (REQ-006(e); AC-2).
  - Validation: `uv run pytest tests/agent/test_llm_turn_executor.py -q` — red before
    Procedure 2, green after.

## Compatibility considerations
- Only this site constructs the guard; all test constructions (e.g. `ToolLoopGuard(ctx)` in
  `tests/agent/test_tool_runner.py`) keep the deferral-off default (REQ-007).
- No `docs/` change (Plan Documentation Impact N/A); `uv run python
  tools/generate_reference_table.py --check` at validation confirms no drift.

## Security considerations
N/A: no new input or trust-boundary change.

## Rollback considerations
N/A: one-token change; revert the commit.

## Validation plan
1. `uv run pytest tests/agent/test_llm_turn_executor.py -q` — new test red then green; the
   file's existing tests pass unchanged.
2. Static: `uv run ruff check scripts/agent/llm_turn_executor.py tests/agent/test_llm_turn_executor.py`,
   `uv run ruff format --check` on both, `uv run mypy scripts/agent/llm_turn_executor.py`.
3. The plan-wide validation sequence (`rules/toolchain.md`) runs once after all six
   documents of this plan are executed.

## Completion criteria
- AC-2 (construction half): `handle_llm_turn` builds the guard with `defer_hints=True`, and
  a test pins it; with the seq 01/03 documents complete, hints recorded during a turn are
  flushed before `run()` proceeds.

## Out of Scope
- The deferral implementation itself (seq 01) and the flush awaits in `run()` (seq 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write red executor wiring test, confirm it fails (Procedure 1; Companion test files) | Completed | 20261103-175500 | 20261103-182109 | TestGuardDeferralWiring added (own patch stack, _run_turn untouched); red confirmed: kwargs defer_hints missing. |
| 2 | Pass `defer_hints=True` at the construction site (Procedure 2) | Completed | 20261103-182109 | 20261103-182109 | ToolLoopGuard(self._ctx, defer_hints=True) + 2-line comment naming the deferral and the seq 03 flush. |
| 3 | Run this document's checks (Validation plan 1-2) | Completed | — | 20261103-182109 | 45 passed (executor+runner files); ruff/format clean; mypy clean. Commit lands together with seq 03 (flush await) so no deferral-without-flush state is ever committed. |

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
- **Requirement ID**: REQ-002 (the production guard is built with deferral on), REQ-006
  (the wiring assertion)
- **Source issue**: issues/20261003-180333_blockio001_sync-sqlite-writes-block-event-loop.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-143807_blockio001_sync-sqlite-writes-block-event-loop.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-113432
- **Related target files**: `scripts/agent/llm_turn_executor.py`, `tests/agent/test_llm_turn_executor.py`