# Implementation Procedure: Harden Ephemeral Message Lifecycle, History Compression, and Memory Boundaries

Source plan: `plans/20260717-001758_plan.md`
Source requirement: `requires/20260716_15_require.md`

## Goal

Enforce a strict, verified lifecycle boundary for ephemeral system messages (`_ephemeral`, `_skill_ephemeral`, `_memory_injected`) so they never leak into session persistence, memory extraction, or compressed history, and so they reliably reach the LLM for the turn they were created for — fixing the confirmed defect where `_sync_system_prompt()` currently strips them within the same turn, before the LLM call happens.

## Scope

**In scope**
- `scripts/agent/orchestrator.py`: split `_sync_system_prompt()`'s two responsibilities — move ephemeral/memory-injected cleanup to the start of `_process_turn()` (before `_handle_memory_injection()`/`classify_and_inject_mode()`), keep system-prompt-content sync where the user message is appended.
- `scripts/agent/services/undo_service.py`: extend the backward-scan predicate (currently `ctx.conv.history[cut_idx - 1].get("_memory_injected")`) to also match `_ephemeral`.
- `scripts/agent/services/context_view.py`: expose `stat_fallback_truncate_count` alongside the existing `stat_compress_count` display (line 166).
- `scripts/agent/history_selection_policy.py`: add a documentation comment explaining why system-role messages bypass `classify()` entirely (no behavior change).
- New `tests/test_mode_classification.py`; extend `tests/test_orchestrator.py`, `tests/test_regression_undo_artifact.py`, `tests/test_history_manager.py`, `tests/test_history_selection_policy.py`, `tests/test_cmd_skill.py`.

**Out of scope**
- Redesigning `scripts/agent/memory/*` internals — only verifying the extraction/injection boundary already excludes ephemeral content.
- Removing persistent system prompts.
- Changing `scripts/agent/mdq_rag_classifier.py`.
- Changing the session DB schema.
- Any change to `scripts/agent/mode_classification.py`, `scripts/agent/session.py`, or `scripts/agent/commands/cmd_skill.py` beyond regression-test verification — their current logic is correct; the bug is in the consumer (orchestrator), not these producers.

## Assumptions

1. `agent/history_selection.py` (as named in the source requirement) refers to `scripts/agent/history_selection_policy.py` — confirmed via `tests/test_history_selection_policy.py`'s import of `HistorySelectionPolicy`.
2. `/undo` should strip preceding `_ephemeral` messages using the same rule already applied to `_memory_injected`, since both are turn-scoped artifacts that should not outlive the turn they were created in.
3. `_skill_ephemeral` messages are a subset of `_ephemeral` messages (every `_skill_ephemeral: True` message also has `_ephemeral: True`, per `cmd_skill.py:51-53`) and are covered by the same lifecycle fix without special-casing.
4. The fix must preserve the documented behavior that `_ephemeral` messages are "re-evaluated every turn" (`docs/05_agent_03_01_turn-processing-flow-overview.md:112-114`) — the hint must still be recomputed each turn from a clean slate, not cached/reused.
5. **Confirmed still present in current code** (verified by direct read, 2026-07-17): `orchestrator.py:444-446`'s `_process_turn()` calls `_handle_memory_injection(line)` then `classify_and_inject_mode(line, ctx)` then `_append_user_message(line)`; `_append_user_message` (line 526) calls `_sync_system_prompt()` (line 503-514), which unconditionally strips all `_ephemeral`/`_memory_injected` entries from `ctx.conv.history` — before `_handle_llm_turn()` (line 449) ever runs. This confirms the regression this plan targets is still live, not already fixed.
6. `HistorySelectionPolicy.select_turns_to_compress()` (lines 120-152) already excludes all system-role messages (`system_msgs`, line 128) from the compression candidate pool before `classify()` (line 44) is ever applied — confirmed by direct read. This means ephemeral messages, being system-role, are already never summarized; no behavior change is needed in `history_selection_policy.py`, only a documentation comment.
7. `context_view.py:166` already displays `compress_count = ctx.services_required.hist_mgr.stat_compress_count` — confirmed by direct read — but does not display `stat_fallback_truncate_count` (`history.py:89`, incremented at `history.py:311`), which is the gap to close.
8. `undo_service.py:42`'s existing backward-scan loop only checks `_memory_injected`, not `_ephemeral` — confirmed by direct read; this is the gap Implementation Step 2 (below) closes.

## Implementation

### Target file

Primary: `scripts/agent/orchestrator.py`. Secondary: `scripts/agent/services/undo_service.py`, `scripts/agent/services/context_view.py`, `scripts/agent/history_selection_policy.py`, and the test files listed in Scope.

### Procedure

1. **Lock in the regression baseline first**: add a minimal failing test (in `tests/test_orchestrator.py`) asserting the LLM call payload contains the `_ephemeral`/`_memory_injected` content injected during the *same* turn, before changing any production code — this must fail against current code to confirm the regression is real and reproducible.
2. **Core fix — split `_sync_system_prompt()`'s responsibilities** in `scripts/agent/orchestrator.py`:
   - Extract the ephemeral/memory-injected cleanup logic (currently lines 509-514: `ctx.conv.history = [m for m in ctx.conv.history if not m.get("_ephemeral") and not m.get("_memory_injected")]`) into its own step.
   - Call this cleanup at the **start** of `_process_turn()` (before line 444's `_handle_memory_injection(line)` call), so it removes leftover content from the *previous* turn only.
   - Keep the remaining system-prompt-content sync logic (lines 515-522: refreshing `history[0]` or inserting it) in `_sync_system_prompt()`, called from `_append_user_message()` as today, so it still reflects any `ctx.conv.system_prompt_content` changes (e.g. via `/system`) made earlier in the same turn.
   - Before making this change, re-read `_handle_memory_injection()` and `classify_and_inject_mode()` in full to confirm neither depends on stale ephemeral content already being present in `ctx.conv.history` at the point they run (per Risks below) — both should only *append*.
3. **`/undo` fix**: in `scripts/agent/services/undo_service.py`, extend the backward-scan predicate at line 42 from `ctx.conv.history[cut_idx - 1].get("_memory_injected")` to also match `.get("_ephemeral")`, so `/undo` strips both kinds of turn-scoped artifacts preceding the undone user turn.
4. **Diagnostics**: in `scripts/agent/services/context_view.py`, add `stat_fallback_truncate_count` to the existing status output alongside `compress_count` (line 166), following the same display pattern already used for `stat_compress_count`.
5. **Documentation comment**: in `scripts/agent/history_selection_policy.py`, add a short comment near `select_turns_to_compress()`'s `system_msgs` exclusion (line 128) explaining that system-role messages (including ephemeral ones) are removed from the compression pool before `classify()` runs, so a future reader does not "fix" the apparently-dead "system" branch inside `classify()` by wiring it into `select_turns_to_compress()` and accidentally making ephemeral messages compressible.
6. **Test coverage**:
   - New `tests/test_mode_classification.py`: hint injection, no duplication across repeated tool-loop iterations, hint present in the same turn's payload.
   - Extend `tests/test_orchestrator.py`: assert ephemeral/memory-injected content is present in the LLM call payload for its own turn, and absent from the *next* turn's payload; assert `/skill` content survives to the following turn's LLM call.
   - Extend `tests/test_regression_undo_artifact.py`: `/undo` strips a preceding `_ephemeral` message (not just `_memory_injected`).
   - Extend `tests/test_history_manager.py` / `tests/test_history_selection_policy.py`: add any missing fallback-order case; confirm compression success/failure, protected turns, and ephemeral exclusion remain correct after the reorder.
7. **Verification**: run the full validation sequence from `rules/toolchain.md`, scoped first to the changed files, then the full suite.
8. **Deploy impact check**: confirm no `deploy/deploy.sh` change is needed — no new/removed files under `scripts/`, no new config key, no schema change.

### Method

- Direct source edits: reorder two existing calls in `orchestrator.py` (not a rewrite of `_process_turn`); a small predicate extension in `undo_service.py`; an additive display line in `context_view.py`; a comment-only addition in `history_selection_policy.py`.
- Test-first for the core fix (Step 1 before Step 2), consistent with locking in the regression baseline before changing production code.
- `orchestrator.py` has very high churn (50 commits/30d at plan time) — rebase immediately before implementation and re-read the current file state before editing, since cached line numbers from planning may have shifted.

### Details

- Do not rewrite `_process_turn()` beyond reordering the cleanup call — keep the diff minimal given the file's high churn.
- Do not change `mode_classification.py`, `session.py`, or `cmd_skill.py` production logic — verify via regression tests only, per Scope's out-of-scope list.
- Do not wire `HistorySelectionPolicy.classify()`'s "system" branch into `select_turns_to_compress()` — it is correctly unreachable today; Step 5's comment exists specifically to prevent a future accidental "fix" here.
- Confirm at implementation time (not from this document's cached findings) that `_handle_memory_injection()` and `classify_and_inject_mode()` still only append to `ctx.conv.history` and do not read it expecting prior-turn ephemeral content to already be absent — re-verify given the file's high concurrent-edit risk.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `orchestrator.py` (`_process_turn`, `_sync_system_prompt`) | Unit + regression | `uv run pytest tests/test_orchestrator.py -v` | Ephemeral/memory-injected content present in same-turn LLM payload; absent from next-turn payload |
| `mode_classification.py` (regression only, new test file) | Unit | `uv run pytest tests/test_mode_classification.py -v` | Hint injected once per turn; no accumulation across repeated tool-loop iterations |
| `history.py`, `history_selection_policy.py` | Unit + regression | `uv run pytest tests/test_history_manager.py tests/test_history_selection_policy.py -v` | Compression success/failure, protected turns, fallback order, ephemeral exclusion all pass |
| `undo_service.py` | Regression | `uv run pytest tests/test_regression_undo_artifact.py -v` | `/undo` removes preceding `_ephemeral` and `_memory_injected` messages |
| `cmd_skill.py` (regression only) | Regression | `uv run pytest tests/test_cmd_skill.py -v` | `/skill` content still reaches the LLM call for the following turn |
| `context_view.py` | Manual + regression | inspect `/context` output | `stat_fallback_truncate_count` now displayed alongside `compress_count` |
| Full suite | Regression | `uv run pytest -v` | No new failures vs. current baseline in affected files |
| Lint/type/format | Static | `uv run ruff check scripts/ && uv run mypy scripts/` | No new errors |
| Pre-commit | Final gate | `uv run pre-commit run --all-files` | All hooks pass |
