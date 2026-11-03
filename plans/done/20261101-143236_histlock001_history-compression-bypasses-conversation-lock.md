## Goal
- Make `ConversationStateManager.handle_history_compression` (`scripts/agent/conversation_state_manager.py`) replace `ctx.conv.history` with the compressed list only through a new lock-guarded method on `ConversationState` (`scripts/agent/context.py`) that keeps any message appended to the old list while `HistoryManager.compress` was awaiting, so a concurrent `append_message()` / `extend_messages()` can no longer be silently dropped by the swap.

## Priority
Low

## Scope
- **In-Scope**:
  - A new async method on `ConversationState` (working name `swap_history`, distinct from `replace_history` and `restore_messages`) that takes `self._ensure_lock`, performs a raw swap of the history list without per-message validation or sanitizing, and preserves messages appended to the pre-await list after the snapshot.
  - Switching `handle_history_compression` to that method, so the manager no longer assigns `ctx.conv.history` directly for the compression result.
  - Regression tests: unit tests of the new method and an interleaving test that appends during an in-flight `compress` call driven through `handle_history_compression`.
  - Recording the background-task audit result (done at planning time, see Design) and re-running the same scan at implementation time.
- **Out-of-Scope**:
  - `HistoryManager.compress()` selection and summarization logic and its return contract (`scripts/agent/history.py` is read-only here).
  - The first-turn title-generation background task.
  - `ConversationStateManager.clear_previous_turn_ephemeral_messages()` (synchronous, no await between read and write, cannot interleave).
  - Sibling direct assignments of `ctx.conv.history` outside the issue's target files (the `/compact` command, `/undo`, `/clear`); see UNK-01.
  - Changing `replace_history()` or `restore_messages()` behavior, introducing a new lock, or any `docs/` change.
- **Dependencies**: N/A: the Issue lists none (its `histsel001` mention is historical; no file for it exists, see UNK-03). Overlap with `plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` on `scripts/agent/context.py` is judged compatible (different class), so no fix order is required (see Assumptions).

## Background
Found during an adversarial code review of the REPL session-state subsystem. `ConversationState` documents that history access is synchronized with an `asyncio.Lock`; `append_message`, `extend_messages`, `replace_history`, `snapshot_messages` and `restore_messages` all take it. `handle_history_compression` is the one history writer in the turn path that does not: it passes `ctx.conv.history` to `HistoryManager.compress`, which awaits `_check_limits` (token count) and `_get_summary_text` (LLM round trip), then builds the new list from slices computed before the await and the caller assigns the result back. The turn path calls it once per turn from `WorkflowEngineAdapter._prepare_turn_input`, after `append_user_message`.

## Problem
Between the pre-await snapshot and the assignment, any `append_message()` / `extend_messages()` call mutates the old list in place; that message is not in the new list and is lost at the swap, with no lock and no log. The assignment is also not exclusive with the other lock holders. No writer that can run in that window exists today (see the audit in Design), so this is a latent trap, not a demonstrated bug (checked in Step 2 and Step 3).

## Reason for Change
The code contradicts the documented locking contract of `ConversationState`, and the next background writer added to the turn path (for example an async memory or workflow side effect) would turn the trap into silent message loss that no test would catch. Fixing it now is cheap because the swap has a single caller.

## Implementation Intent
Add a trusted, lock-guarded swap on `ConversationState` and call it from `handle_history_compression`. The caller captures the list object and its length before awaiting `compress`; the swap, under the lock, appends the messages added to that same list after the snapshot to the compressed list (skipping any already present, and doing nothing when `compress` returned the same list object). `compress()`, `replace_history()` and the persistence call (`boundary.replace_messages`) keep their contracts.

## Requirements
- `REQ-001`: `ConversationState` gains an async lock-guarded raw-swap method whose name differs from `replace_history`; it uses the existing `self._ensure_lock` (no new lock), assigns the compressed list as given (no validation, no marker stripping), and preserves messages appended to the pre-await list after the caller's snapshot, without duplicating a message already present in the new list and without effect when the new list is the same object as the pre-await list.
- `REQ-002`: `handle_history_compression` assigns the compression result to `ctx.conv.history` only through that method; the persisted snapshot passed to `boundary.replace_messages` and the new `undo_floor` are computed from the post-swap history; `compress()`'s logic and return contract and the `compressed_count > 0` persistence condition are unchanged.
- `REQ-003`: Regression tests prove (a) a message appended through `append_message()` while an awaited `compress` is in flight survives the swap and is part of the persisted snapshot, (b) the helper neither duplicates nor drops messages for the no-op (same-object), fallback-truncate (new list built from the live list) and summary (new list built from the pre-await slices) result shapes, and (c) the helper keeps ephemeral and summary markers that `replace_history` would strip. Existing compression tests stay green.
- `REQ-004`: The background-task audit result is recorded (in this Plan's Design) and the same scan is re-run at implementation time; if it finds a writer that can append during the compression window, the Priority and the implementation notes are revisited before merging.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/context.py | Add the lock-guarded raw-swap method to `ConversationState` next to `replace_history` / `restore_messages`, with a docstring that states its trusted-input contract and how it differs from `replace_history` | The class has no way to swap the whole list under the lock while keeping concurrent appends; `replace_history` re-validates every row as untrusted and strips ephemeral and summary markers, and `restore_messages` is lock-guarded and raw but drops anything appended since its snapshot | REQ-001, REQ-004; AC-1, AC-3 | `ConversationState` docstring says history access is synchronized via `asyncio.Lock`; `append_message`, `extend_messages`, `replace_history`, `snapshot_messages`, `restore_messages` use `self._ensure_lock`; `replace_history` passes `_UNTRUSTED_RESTORE_SOURCE`; `restore_messages` does `self.history.clear()` then `extend(snapshot)` (checked in Step 2 and Step 3) | `tests/agent/test_context_append_message.py` | Verified |
| scripts/agent/conversation_state_manager.py | In `handle_history_compression`, capture the pre-await list and length, await `hist_mgr.compress`, then call the new method instead of assigning `ctx.conv.history`; compute `replace_messages` input and `undo_floor` from the post-swap history | The compression result is assigned without the lock from a list built before the await | REQ-002, REQ-004; AC-1, AC-2, AC-4 | `handle_history_compression` does `ctx.conv.history, result = await ...hist_mgr.compress(ctx.conv.history)` and later `boundary.replace_messages(ctx.conv.history)` and `ctx.conv.undo_floor = len(ctx.conv.history)`; sole caller is `WorkflowEngineAdapter._prepare_turn_input` (checked in Step 2 and Step 3) | `tests/agent/test_history_compression_consistency.py`, `tests/agent/test_orchestrator.py` (`TestHandleHistoryCompressionPersist`), `tests/integration/test_orchestrator_integration.py` | Verified |
| tests/agent/test_context_append_message.py | Add `TestSwapHistory` (or equivalent) next to `TestReplaceHistory`: swap under lock, marker preservation vs `replace_history`, appended-message preservation, same-object no-op, no duplication when the new list already contains the appended message | The file is the existing home of the unit tests for `append_message`, `extend_messages` and `replace_history`; no test covers a whole-list swap | REQ-003, REQ-001; AC-3 | `TestAppendMessage`, `TestExtendMessages`, `TestReplaceHistory` exist and use a real `ConversationState` (checked in Step 3) | `uv run pytest tests/agent/test_context_append_message.py` | Verified |
| tests/agent/test_history_compression_consistency.py | Add an interleaving test: a `compress` stub that awaits an `asyncio.Event`, a concurrent `append_message()` while it is in flight, then assert the message is in `ctx.conv.history`, in the snapshot given to `replace_messages`, and below the final `undo_floor` expectation chosen in the implementation | The file already drives `handle_history_compression` against a real `ConversationState` and a real patched session DB via `_compression_ctx` and `_TurnBoundaryStub`; the Issue's named `tests/agent/test_conversation_state_manager.py` does not exist (checked in Step 3) | REQ-003, REQ-002; AC-2, AC-4 | `test_manager_path_sets_undo_floor_to_snapshot_length` and `test_compression_failure_restores_pre_turn_state` call `mgr.handle_history_compression()` with `ConversationState()` (checked in Step 3) | `uv run pytest tests/agent/test_history_compression_consistency.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/history.py | `HistoryManager.compress` awaits `_check_limits` and `_get_summary_text`, returns the same list object on the no-op path, builds the summary result from pre-await slices, and its fallback path builds from the live list; `force_compress` doc says callers replace `ctx.conv.history` | REQ-001, REQ-002, REQ-003 |
| scripts/agent/history_selection_policy.py | `select_turns_to_compress` returns new lists (`system_msgs`, `to_compress`, `remaining`) computed before the await, confirming the snapshot semantics | REQ-001 |
| scripts/agent/workflow_engine_adapter.py | Sole caller (`_prepare_turn_input`): shows the compression runs after `append_user_message` inside the turn and before the engine runs | REQ-002, REQ-004 |
| scripts/agent/turn_persistence.py | `TurnPersistence.replace_messages`, `snapshot`/`restore_messages` use; compensation restores history element-wise from the turn-start snapshot | REQ-002 |
| scripts/agent/commands/cmd_rag_export.py | Sibling compression site (`/compact`, `force_compress` then direct assignment); confirms it is outside this Plan (UNK-01) | UNK-01 |
| scripts/agent/repl_input_loop.py | The REPL dispatches one line at a time and awaits the dispatch before reading the next input; basis of the audit | REQ-004 |
| scripts/agent/tool_runner.py | Tool-result appends (`ctx.conv.append_message`) and `asyncio.gather` over tool groups happen inside the execute stage, after compression | REQ-004 |
| scripts/agent/llm_turn_runner.py | Assistant and ephemeral appends happen inside the turn's LLM loop | REQ-004 |
| scripts/agent/mode_classification.py | Mode-hint append runs in `_prepare_turn_input` before compression, awaited sequentially | REQ-004 |
| tests/agent/test_orchestrator.py | `TestHandleHistoryCompressionPersist` uses a real `ConversationState` through `_make_ctx`; must stay green | REQ-002, REQ-003 |
| tests/integration/test_orchestrator_integration.py | Two compression persistence tests use a real `ConversationState`; must stay green | REQ-002, REQ-003 |
| tests/agent/test_context.py | Covers `AgentContext`; run as regression only | REQ-001 |
| docs/23_agent/agent_04_02_state-and-persistence-history-compression.md | "Compression Persistence Model" states what is persisted and the undo boundary; no statement about the lock or the swap | REQ-002 (Documentation Impact) |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-002): In `scripts/agent/`, the compression result reaches `ctx.conv.history` only through the new `ConversationState` method; `handle_history_compression` contains no direct assignment to `ctx.conv.history`.
- AC-2 (REQ-002, REQ-003): A message appended with `append_message()` while `compress` is awaiting is present in `ctx.conv.history` after `handle_history_compression` returns, exactly once, after the compressed messages, and in the list passed to `boundary.replace_messages`.
- AC-3 (REQ-001, REQ-003): Unit tests show the method holds `self._ensure_lock` for the swap, leaves ephemeral and summary markers intact (unlike `replace_history`), preserves appended messages, does nothing when the new list is the pre-await list object, and does not duplicate a message the new list already contains.
- AC-4 (REQ-002, REQ-003): `compress()`'s own tests, `TestHandleHistoryCompressionPersist`, the two integration compression tests and the consistency tests pass unchanged; `compressed_count == 0` still skips `replace_messages`.
- AC-5 (REQ-004): The audit result is recorded in this Plan and the implementation-time re-scan finds no writer, or the Plan is revisited.

## Tests
- Unit (`tests/agent/test_context_append_message.py`): new-method cases for REQ-001 and REQ-003 (b), (c): empty tail, tail after the snapshot, same-object result, fallback-shaped result that already contains the tail, marker preservation compared with `replace_history`.
- Interleaving (`tests/agent/test_history_compression_consistency.py`): `compress` stub awaiting an `asyncio.Event`; start `handle_history_compression()` as a task, `await ctx.conv.append_message(...)`, release the event, await the task, assert AC-2 (REQ-003 (a)). Also confirm the test fails against the unmodified manager (the appended message disappears).
- Regression: the commands in the Validation plan; no full-suite run is required beyond `rules/toolchain.md`.

## Documentation Impact
N/A: no `docs/*.md` describes the compression swap or the history lock (the "Compression Persistence Model" section of `docs/23_agent/agent_04_02_state-and-persistence-history-compression.md` covers persistence and the undo boundary only, and `ConversationState`'s docstring already states the locking contract), so no doc is driven by REQ-001 to REQ-004. `docs/23_agent/agent_13_reference-api-generated.md` lists classes, not methods; `uv run python tools/generate_reference_table.py --check` is still run at implementation because `scripts/agent/` changes (checked in Step 2).

## Assumptions
- The REPL awaits each dispatched line before reading the next, and the turn path (prepare, engine, tool rounds) is a single awaited chain, so today no other coroutine can append during the compression await (falsifiable: the implementation-time `rg` scan of `create_task`/`ensure_future` and history writers finds a new writer).
- Keeping the swap as a reassignment of `ctx.conv.history` (not in-place `clear` + `extend`) preserves current behavior: `compress` returns a new list on the summary and fallback paths, and the only local references to the list (`llm_turn_runner`, including `_stream_llm_final_answer`) are taken per call (falsifiable: a test shows a held reference expected to see the swap).
- Messages appended during the window were already validated by `append_message()` / `extend_messages()`, so the swap copies them raw and does not re-validate.
- The `restore_messages` method (raw, lock-guarded, in-place) is not reused because it has a different purpose (turn-start rollback) and cannot keep appended messages; the Issue names only `replace_history` as the method not to reuse, so this extra distinction is a derived judgment.
- Step 8b overlap judgment (`tools/check_plan_target_overlaps.py`): the only finding naming this Plan is `scripts/agent/context.py` shared with `plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md`. Judged compatible: that Plan adds a per-attempt side-effect flag to `TurnState` (its REQ-006) and never mentions `ConversationState`, history or `conversation_state_manager.py`, while this Plan adds one method to `ConversationState`; the two edits are in different classes and either order works. The other active workflow-engine Plans (wfrecovery001, wflease001, wftaskapi001) do not list `scripts/agent/context.py` or `scripts/agent/conversation_state_manager.py` (searched in Step 8b), and `plans/20261101-141314_assertaudit001_audit-assert-risks-post-execution-crash.md` cites `context.py` only as a read-only reference, not as a target. No ordering dependency is added to Scope.
- The Issue's `Testing Expectations` name `tests/agent/test_conversation_state_manager.py`; that file does not exist, and `tests/agent/test_context.py` covers `AgentContext`, so the new tests go into the two existing files listed above (checked in Step 3).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Other call sites assign `ctx.conv.history` directly after an awaited compression: `CmdRagExportMixin._cmd_compact` in `scripts/agent/commands/cmd_rag_export.py` (`force_compress` then assignment), plus the `/undo` and `/clear` services. They run as slash commands inside the same serial dispatch, so they share the latent trap but are outside the Issue's Target Files | No decision whether to route them through the new method too | After this Plan is implemented, the owner decides whether to file a follow-up Issue (for example `/compact` only, as it awaits the same LLM round trip); this Plan does not change them | False |
| UNK-02 | Whether a message preserved from the compression window should sit below or above the new `undo_floor`. The current code sets `undo_floor = len(history)` after the swap, so a preserved message would not be undoable | No document states the intended `/undo` semantics for a message appended during compression; no such message exists today | Keep `undo_floor = len(history after swap)` (the documented rule: nothing in the compressed snapshot is undoable) and state it in the interleaving test; revisit only if a real writer is added | False |
| UNK-03 | The Issue's `Dependencies` mentions a closed `histsel001` issue. No file for `histsel001` exists under `issues/`, `issues/done/`, `plans/` or `plans/done/` (searched by name), so the closure cannot be confirmed from the repository | Not found; the code does show `HistorySelectionPolicy.select_turns_to_compress` in `scripts/agent/history_selection_policy.py` as the current selection logic | Treat as Needs confirmation; non-blocking because the swap contract does not depend on the selection policy (verified: the policy only returns the new sub-lists) | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/context.py | Modify | Medium: additive method on `ConversationState`, which `AgentContext` and about 30 modules import; no existing signature changes. Module size 16219 B of the 20480 B gate (re-measured 20261103; 15851 B at planning time) | 13 commits | Effectively 1 (about 95% of commits are one person under spelling variants of the name; `git-fame` is not installed, derived from `git log` author counts) | not applicable (rsynced) |
| scripts/agent/conversation_state_manager.py | Modify | Low: one runtime caller (`WorkflowEngineAdapter._prepare_turn_input`); change confined to `handle_history_compression` | 4 commits | Effectively 1 (all commits by one person under two spellings) | not applicable (rsynced) |
| tests/agent/test_context_append_message.py | Modify | Low: test-only | 1 commit | Effectively 1 | not applicable (rsynced) |
| tests/agent/test_history_compression_consistency.py | Modify | Low: test-only | 6 commits | Effectively 1 | not applicable (rsynced) |

## Design
Task classification: Path B. Four `Implementation Target Files` rows (more than 3) and a new public method on `ConversationState`, a class shared through `AgentContext` (checked in Step 3). `workflow-path-b.md` analyses: `lint-imports` reports 6 contracts kept; `agent.context` is imported by about 30 modules, `agent.conversation_state_manager` only by `orchestrator.py` (dependency graph, checked in Step 3); 30-day churn from `git log`; `git-fame` and the operational-dependency commands (`ss`, `pip-audit`) are not applicable (no port, database or dependency change).

Verified current behavior (corrections to the Issue, none contradicting it): `handle_history_compression` awaits `compress`, whose summary path builds the result from `select_turns_to_compress` sub-lists taken before `_get_summary_text`; its no-op path returns the very same list object; its fallback path (`_fallback_truncate`) is built after the await from the live list. `clear_previous_turn_ephemeral_messages` is synchronous and out of scope. `replace_history` is async, clears, and validates each row as untrusted (`_UNTRUSTED_RESTORE_SOURCE`), stripping ephemeral and summary markers. One more related method exists that the Issue does not mention: `restore_messages` (raw, lock-guarded, in-place `clear` + `extend`, used by the turn-persistence rollback); it cannot preserve appends, so it is not a substitute.

Decision 1 (name and shape): a new method, working name `swap_history`, taking the compressed list plus the pre-await list object and its length (final signature fixed in the implementation procedure). Under `self._ensure_lock`: if the new list is the pre-await list, return (nothing was compressed, appends are already in it); otherwise extra = messages of the pre-await list at index `base_len` and later (only while `self.history` is still that same list object), keep those that are not already in the new list by identity, set `self.history = [*new, *extra]`. Alternatives considered: (a) hold the lock across the whole `compress` call, rejected because every `append_message` would block for an LLM round trip and the turn path would depend on lock-ordering; (b) reuse `replace_history`, rejected by the Issue (changes the result by re-validating and stripping markers); (c) reuse `restore_messages`, rejected (drops appends, in-place); (d) re-run `compress` when the history changed, rejected (second LLM call, unbounded). Compatibility: the swap keeps reassignment semantics, `compress` and persistence contracts are unchanged, and the existing tests build a real `ConversationState` so none needs a mock update.

Decision 2 (traps the helper must handle): the no-op path (same object) and the fallback path (live list already holds the appended messages) would both duplicate the tail under a naive "append `history[base_len:]`" rule, hence the identity checks above; and if `self.history` is a different object from the pre-await list (another writer reassigned it), the helper preserves nothing and the case stays a plain swap (no writer does this in the turn path today).

Background-task audit result (REQ-004, Issue "Unresolved Questions"), checked in Step 2 and Step 3 with `rg` over `scripts/` for `create_task`, `ensure_future`, `TaskGroup`, `asyncio.gather`, `run_in_executor`, `to_thread`, `threading.Thread` and for every `append_message` / `extend_messages` / `conv.history` writer:
- The only `asyncio.create_task` in the turn path is the first-turn title task in `append_user_message` (writes the session title, no history).
- `ReplInputLoop` creates `ensure_future` tasks for input, shutdown watching and one dispatch task per line, awaited before the next input is read; `is_processing` is set but never read.
- `tool_runner` uses `asyncio.gather` over tool groups, but only inside the execute stage after `_prepare_turn_input` returns; tool-result appends are awaited sequentially there. `llm_turn_runner` and `mode_classification` appends are also awaited inside the same chain; `scripts/agent/workflow/` has no reference to `conv`.
- `cli_view` spinner, `wal_checkpoint_manager` (`to_thread`, database only), `startup_*` and shutdown coordinators, `bg_task_monitor` and `session_persister` touch no history writer (`session_persister` only reads it).
- Conclusion: no background task can append during the compression await window today; the Issue stays a latent trap (Low).

Validation quality baseline (Step 5): `radon cc` ranks for the targets are A or B (`_sanitize_message` B (6); `handle_history_compression` A (4)); `vulture scripts/ --min-confidence 80` reports only unrelated findings in `scripts/rag/` and `scripts/shared/runtime_paths.py`; `bandit` on the two source files reports two `assert_used` findings in `conversation_state_manager.py` (the persistence-boundary asserts, pre-existing and justified inline). The diff-cover baseline number is not recorded because running the full test suite is outside this planning session; it is recorded at implementation time.

## Implementation steps
1. **Phase 1: Helper and audit re-check**
   - [ ] Re-run the audit scan (`rg` for `create_task`, `ensure_future` and history writers) and note the result in the Execution Status row; stop and revisit Priority if a writer can append during the window (REQ-004; scripts/agent/conversation_state_manager.py).
   - [ ] Add the lock-guarded raw-swap method to `ConversationState` with its docstring (REQ-001; scripts/agent/context.py).
   - [ ] Add the unit tests for the method (REQ-001, REQ-003; tests/agent/test_context_append_message.py).
2. **Phase 2: Use it in the manager**
   - [ ] Change `handle_history_compression` to capture the pre-await list and length, await `compress`, call the new method, and compute the persisted snapshot and `undo_floor` from the post-swap history (REQ-002; scripts/agent/conversation_state_manager.py).
   - [ ] Add the interleaving test and confirm it fails against the unmodified manager (REQ-002, REQ-003; tests/agent/test_history_compression_consistency.py).
3. **Phase 3: Verification and deployment hand-off**
   - [ ] Run the Validation plan commands and the diff-cover sequence of `rules/toolchain.md` section 7 (baseline first, then at the Completion-checklist threshold) (REQ-001, REQ-002, REQ-003; scripts/agent/context.py, scripts/agent/conversation_state_manager.py, tests/agent/test_context_append_message.py, tests/agent/test_history_compression_consistency.py).
   - [ ] Deploy is a hand-off to `skills/deploy/SKILL.md`: the change must be committed and pushed first, and deploying is the user's decision (approval gate); both source files ship through the normal rsync with no new file, config key or service change (REQ-002; scripts/agent/context.py, scripts/agent/conversation_state_manager.py).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/context.py, tests/agent/test_context_append_message.py | Unit | `uv run pytest tests/agent/test_context_append_message.py tests/agent/test_context.py` | New and existing tests pass (AC-3) |
| scripts/agent/conversation_state_manager.py, tests/agent/test_history_compression_consistency.py | Unit / integration | `uv run pytest tests/agent/test_history_compression_consistency.py tests/agent/test_orchestrator.py tests/integration/test_orchestrator_integration.py tests/agent/test_history_manager.py` | Interleaving test passes and fails on the old code; existing compression tests unchanged (AC-2, AC-4) |
| Both source files and tests | Static | `uv run ruff check` and `uv run ruff format --check` on the four files; `uv run mypy scripts/agent/context.py scripts/agent/conversation_state_manager.py` | No findings |
| Both source files | Complexity / security | `radon cc scripts/agent/context.py scripts/agent/conversation_state_manager.py -s`; `uv run bandit -r scripts/agent -c pyproject.toml` | No rank above B; no new bandit finding (the two existing `assert_used` are unrelated) |
| scripts/agent/context.py | Size gate and reference table | `uv run python tools/check_module_size.py`; `uv run python tools/generate_reference_table.py --check` | `context.py` stays under 20480 B (currently 16219 B, re-measured 20261103); no table drift |
| scripts/agent/context.py, scripts/agent/conversation_state_manager.py | Coverage | `rules/toolchain.md` section 7 diff-cover sequence | Changed lines meet the Completion checklist threshold |
| scripts/agent/ | Audit (REQ-004) | `rg -n "create_task|ensure_future|asyncio.gather" scripts/agent` and `rg -n "append_message|extend_messages|conv\.history" scripts/agent` | No new writer reachable during the compression await |

## Risks
- **Risk**: A naive "append everything after the snapshot index" rule duplicates messages on the no-op (same list object) and fallback-truncate results, which are built from or are the live list → **Mitigation**: the helper returns early for the same object and de-duplicates by identity; REQ-003 (b) tests each result shape.
- **Risk**: The preserved tail placement relative to `undo_floor` and the persisted snapshot may surprise a future writer (UNK-02) → **Mitigation**: keep the documented rule (`undo_floor = len(history)` after the swap), test it explicitly, and revisit when a real concurrent writer exists.
- **Risk**: The new method is mistaken for a general replacement of `replace_history` and used on untrusted input, bypassing the marker stripping → **Mitigation**: the docstring states the trusted-input contract and points to `replace_history` / `restore_messages` for the other cases; the test compares marker handling with `replace_history`.
- **Risk**: `scripts/agent/context.py` has high churn (13 commits in 30 days) and active Plans touch it, so a merge conflict is likely → **Mitigation**: the change is one additive method in a different region from the `TurnState` / `WorkflowState` edits; see the Step 8b judgment in Assumptions for ordering.
- **Risk**: The interleaving test is timing-sensitive → **Mitigation**: drive ordering with `asyncio.Event` in the `compress` stub instead of sleeps, and release the event in a `finally`.
- **Risk**: The sibling direct assignments (UNK-01) keep the same latent trap → **Mitigation**: non-blocking and out of scope; recorded for the owner's decision on a follow-up Issue.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Audit re-check, lock-guarded swap method and its unit tests (scripts/agent/context.py, scripts/agent/conversation_state_manager.py, tests/agent/test_context_append_message.py) | In Progress | — | — |  |
| 2 | Use the method in `handle_history_compression` and add the interleaving test (scripts/agent/conversation_state_manager.py, tests/agent/test_history_compression_consistency.py) | In Progress | — | — |  |
| 3 | Validation commands, diff-cover and deploy hand-off | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261103-111932_01_scripts_agent_context.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261103-111932_02_scripts_agent_conversation_state_manager.py.md | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261003-180339_histlock001_history-compression-bypasses-conversation-lock.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261101-143236
- **Related target files**: scripts/agent/context.py, scripts/agent/conversation_state_manager.py, tests/agent/test_context_append_message.py, tests/agent/test_history_compression_consistency.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes 1, Implementation Intent, Constraints; `ConversationState` locking methods and `replace_history` / `restore_messages` behavior | scripts/agent/context.py | Step 1 | AC-1, AC-3 | `uv run pytest tests/agent/test_context_append_message.py` | Confirmed by repository evidence |
| REQ-001 | Issue Testing Expectations; `TestReplaceHistory` pattern | tests/agent/test_context_append_message.py | Step 1 | AC-3 | `uv run pytest tests/agent/test_context_append_message.py` | Derived from confirmed evidence |
| REQ-002 | Issue Required Changes 2, Acceptance Criteria 1; `handle_history_compression` direct assignment | scripts/agent/conversation_state_manager.py | Step 2 | AC-1, AC-2, AC-4 | `uv run pytest tests/agent/test_history_compression_consistency.py tests/agent/test_orchestrator.py` | Confirmed by repository evidence |
| REQ-002 | Issue Acceptance Criteria 2, Testing Expectations; existing real-`ConversationState` compression tests | tests/agent/test_history_compression_consistency.py | Step 2 | AC-2, AC-4 | `uv run pytest tests/agent/test_history_compression_consistency.py` | Confirmed by repository evidence |
| REQ-003 | Issue Acceptance Criteria 2, Testing Expectations; `compress` result shapes (no-op, summary, fallback) in `scripts/agent/history.py` | tests/agent/test_context_append_message.py | Step 1 | AC-3 | `uv run pytest tests/agent/test_context_append_message.py` | Derived from confirmed evidence |
| REQ-003 | Issue Testing Expectations (interleaved append during in-flight compression) | tests/agent/test_history_compression_consistency.py | Step 2 | AC-2, AC-4 | `uv run pytest tests/agent/test_history_compression_consistency.py` | Explicit in issue |
| REQ-004 | Issue Required Changes 3 and 4, Unresolved Questions (background-task audit) | scripts/agent/conversation_state_manager.py | Step 1 | AC-5 | `rg` scan in the Validation plan | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261103-111932 -->