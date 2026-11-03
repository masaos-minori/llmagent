## Goal

Route the compression result in `ConversationStateManager.handle_history_compression`
through the lock-guarded `swap_history` (new) helper instead of the direct assignment, so a
message appended during the `compress` await survives the swap (REQ-002; AC-1, AC-2), prove
it with an interleaving test (REQ-003 (a)), and re-run the background-task audit (REQ-004;
AC-5).

## Scope
**Release unit**: N/A: not part of a release unit

Covers the `scripts/agent/conversation_state_manager.py` row (seq 02) and its companion
test row `tests/agent/test_history_compression_consistency.py` (seq 04,
companion-eligible, no document of its own) of
`plans/20261101-143236_histlock001_history-compression-bypasses-conversation-lock.md`.
Runs after `implementations/20261103-111932_01_scripts_agent_context.py.md` (the helper and
its unit tests exist by then); the interleaving test is written red against the unmodified
manager first.

## Assumptions
- Verified against current source (20261103): `handle_history_compression`
  (`scripts/agent/conversation_state_manager.py:165`) does the direct assignment
  `ctx.conv.history, result = await ctx.services_required.hist_mgr.compress(ctx.conv.history)`
  (175-177), guards persistence on `result.compressed_count > 0` (178) with the boundary
  assert (183-185, pre-existing assert_used), then `boundary.replace_messages(ctx.conv.history)`
  (186) and `ctx.conv.undo_floor = len(ctx.conv.history)` (190); the sole caller is
  `WorkflowEngineAdapter._prepare_turn_input` (`scripts/agent/workflow_engine_adapter.py:368`).
- `swap_history` (new) is declared by the seq 01 sibling document (resolved from sibling;
  signature `swap_history(new_history, base_history, base_len)`).
- The interleaving test can reuse the file's existing fixtures `_compression_ctx` (306) and
  `_TurnBoundaryStub` (291), which already drive `handle_history_compression` against a
  real `ConversationState` and a patched session DB.
- UNK-02 decision (kept per the Plan): the preserved tail sits below the new `undo_floor`
  (`undo_floor = len(history after swap)` — nothing in the compressed snapshot is
  undoable); the interleaving test states this expectation explicitly.
- Plan overlap re-confirmed 20261103: `check_plan_target_overlaps.py` reports no overlap
  naming this Plan; no gating dependency (`plan_dependency_order` result in the progress
  report).

## Design decisions
N/A: the Plan's Design (capture base list + length pre-await, swap via the helper, persist
from post-swap history) is adopted unchanged; no new decision is needed at file level.

## Alternatives considered
N/A: the Plan rejected holding the lock across `compress` and re-running `compress`; the
implementation follows Decision 1/2 from the Plan (seq 01 document implements the helper).

## Implementation
### Target file
`scripts/agent/conversation_state_manager.py`

### Procedure
1. Write the red interleaving companion test (see Companion test files) and confirm it
   fails against the unmodified manager (the appended message disappears).
2. In `handle_history_compression` (conversation_state_manager.py:165):
   - Before the `compress` call (175): capture `base_history = ctx.conv.history` and
     `base_len = len(base_history)`.
   - Change the call to `new_history, result = await
     ctx.services_required.hist_mgr.compress(base_history)`, then
     `await ctx.conv.swap_history(new_history, base_history, base_len)` — no assignment to
     `ctx.conv.history` remains in this method (AC-1).
   - Keep the `compressed_count > 0` guard (178), the boundary assert (183-185) and the
     `replace_messages` / `undo_floor` statements (186, 190) reading `ctx.conv.history`
     after the swap (REQ-002: persisted snapshot and `undo_floor` computed from post-swap
     history).
3. Re-run the REQ-004 audit scan (`rg -n "create_task|ensure_future|asyncio.gather"
   scripts/agent` and `rg -n "append_message|extend_messages|conv\.history"
   scripts/agent`) and record the outcome in this document's Execution Status Notes; if a
   writer that can append during the compression window is found, stop and revisit the
   Plan's Priority before merging (REQ-004; AC-5).

### Method
Capture-then-swap: the pre-await list object and its length are the helper's guards; the
persistence block is untouched except that it now reads the post-swap history.

### Details
- On the no-op path `compress` returns the same list object, so `swap_history` returns
  immediately and behavior is identical (REQ-003 (b) shape); the `compressed_count > 0`
  guard still skips `replace_messages` (AC-4).
- `handle_history_compression` is radon A(4) (verified 20261103); the change adds no
  branching, so it must stay A(4).
- The method docstring (166-171) stays valid; optionally add one sentence that the swap is
  lock-guarded and preserves concurrent appends.

### Companion test files
- `tests/agent/test_history_compression_consistency.py` (companion of the
  `scripts/agent/conversation_state_manager.py` row; Plan `Implementation Target Files`
  seq 04 covered here per the companion rule)
  - Procedure: add `test_append_during_compression_survives_swap` (new) using
    `_compression_ctx` / `_TurnBoundaryStub`: patch `hist_mgr.compress` with a stub that
    awaits an `asyncio.Event` and returns the summary-shaped new list built from pre-await
    slices (mirrors `scripts/agent/history.py` summary path); start
    `mgr.handle_history_compression()` as a task, `await ctx.conv.append_message(...)`
    while the stub is in flight, release the event in a `finally`, await the task; assert
    the appended message is in `ctx.conv.history` exactly once and after the compressed
    messages, is present in the list the stub boundary captured for `replace_messages`, and
    `undo_floor == len(ctx.conv.history)` after the swap (the UNK-02 rule stated as an
    assertion comment) — AC-2.
  - Validation: red against the unmodified manager (message lost at the swap), green after
    Procedure 2; drive ordering with the `asyncio.Event`, never sleeps (Plan Risks).

## Compatibility considerations
- `compress()`'s logic and return contract, the persistence boundary call and the
  `compressed_count` condition are unchanged (REQ-002; AC-4).
- Existing green tests must stay green unchanged: `TestHandleHistoryCompressionPersist`
  (`tests/agent/test_orchestrator.py:2087`), the two integration compression tests in
  `tests/integration/test_orchestrator_integration.py`, and this file's existing cases
  (`test_manager_path_sets_undo_floor_to_snapshot_length` at 340,
  `test_compression_failure_restores_pre_turn_state` at 375).
- No `docs/` change (Plan Documentation Impact N/A).

## Security considerations
N/A: no new input or trust-boundary change; validation of appended messages already
happened in `append_message` (Plan Assumptions).

## Rollback considerations
- Revert the commit (this change and the seq 01 helper land together); no config or schema
  change to unwind.

## Validation plan
1. `uv run pytest tests/agent/test_history_compression_consistency.py
   tests/agent/test_orchestrator.py tests/integration/test_orchestrator_integration.py
   tests/agent/test_history_manager.py` — interleaving test red before Procedure 2 and
   green after; existing compression tests unchanged (AC-2, AC-4).
2. Static: `uv run ruff check scripts/agent/conversation_state_manager.py
   tests/agent/test_history_compression_consistency.py`, `uv run ruff format --check` on
   both, `uv run mypy scripts/agent/conversation_state_manager.py` — no findings.
3. Complexity / security / size: `radon cc scripts/agent/conversation_state_manager.py -s`
   (stays A(4)); `uv run bandit -r scripts/agent -c pyproject.toml` (no new finding; the
   two existing assert_used in this file are the pre-existing justified boundary asserts);
   `uv run python tools/check_module_size.py` (8775 B of 20480 B).
4. REQ-004 audit scan commands (Procedure 3).
5. Full validation sequence per `rules/toolchain.md` (diff-cover baseline recording first,
   then the threshold gate) runs once at the end of the plan's execution across both
   documents; deploy is a hand-off to `skills/deploy/SKILL.md` after commit and push, and
   is the user's decision.

## Completion criteria
- AC-1: `handle_history_compression` contains no direct assignment to `ctx.conv.history`;
  the compression result reaches the history only through `swap_history`.
- AC-2: the interleaving test shows the concurrent append survives the swap exactly once,
  after the compressed messages, in the persisted snapshot.
- AC-4: `compress()` tests, `TestHandleHistoryCompressionPersist`, the two integration
  tests and the consistency tests pass unchanged; `compressed_count == 0` still skips
  `replace_messages`.
- AC-5: the audit re-scan result is recorded here; no new writer found, or the Plan is
  revisited before merging.

## Out of Scope
- The helper itself and its unit tests (seq 01 document).
- Sibling direct assignments in `/compact`, `/undo`, `/clear` (UNK-01).
- `HistoryManager.compress` internals (`scripts/agent/history.py`, read-only), the
  first-turn title-generation background task, `clear_previous_turn_ephemeral_messages()`
  (Plan Out-of-Scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write red interleaving test, confirm it fails against the unmodified manager (Procedure 1; Companion test files) | Completed | 20261103-163700 | 20261103-164151 | `test_append_during_compression_survives_swap` red confirmed: appended row lost (assert 0 == 1) |
| 2 | Capture-then-swap change in `handle_history_compression` (Procedure 2) | Completed | 20261103-163700 | 20261103-164151 | base_history/base_len captured pre-await; `await ctx.conv.swap_history(...)`; no direct assignment remains (AC-1); docstring sentence added |
| 3 | Re-run REQ-004 audit scan and record the result (Procedure 3) | Completed | 20261103-163700 | 20261103-164151 | No new writer found: only background task near history is the first-turn title task (`conversation_state_manager.py:113`, takes `line` only, Plan Out-of-Scope); all append/extend writers (`llm_turn_runner`, `tool_runner:327`, `tool_round_completion:80`, `mode_classification:67`) run in the sequential turn flow, not concurrently with the compress window. Plan Priority not revisited (AC-5) |
| 4 | Run this document's checks (Validation plan 1-2; full sequence at plan end) | Completed | 20261103-163700 | 20261103-164151 | targeted pytest 259 passed (interleaving green, existing compression tests unchanged); ruff check+format clean; mypy clean; radon `handle_history_compression` A(4) unchanged, no C+; bandit: 2 pre-existing justified assert_used only; check_module_size OK (9059 B); reference_table --check: no drift |

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
- **Requirement ID**: REQ-002 (compression result reaches history only via the guarded
  swap; snapshot and `undo_floor` from post-swap history), REQ-003 (interleaving test for a
  concurrent append), REQ-004 (background-task audit re-scan)
- **Source issue**: issues/20261003-180339_histlock001_history-compression-bypasses-conversation-lock.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-143236_histlock001_history-compression-bypasses-conversation-lock.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-111932
- **Related target files**: `scripts/agent/conversation_state_manager.py`, `tests/agent/test_history_compression_consistency.py`