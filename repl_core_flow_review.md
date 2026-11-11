# Review Scope

- **Reviewed:** Core `agent` REPL action flow — input → dispatch → LLM turn loop → tool execution → state management → persistence/shutdown.
  - `scripts/agent/repl_input_loop.py` (`ReplInputLoop`)
  - `scripts/agent/repl.py` (`AgentREPL`)
  - `scripts/agent/orchestrator.py` (`Orchestrator.handle_turn`)
  - `scripts/agent/llm_turn_runner.py` (`LLMTurnRunner.run`)
  - `scripts/agent/llm_turn_executor.py` (`LlmTurnExecutor`)
  - `scripts/agent/tool_runner.py` (`execute_all_tool_calls`, `execute_one_tool_call`)
  - `scripts/agent/tool_loop_guard.py` (`ToolLoopGuard`)
  - `scripts/agent/tool_round_completion.py` (`complete_round`)
  - `scripts/agent/tool_result_pairing.py`, `scripts/agent/message_schema.py`
  - `scripts/agent/config_dataclasses.py` (`ToolConfig` defaults)
  - `scripts/agent/turn_persistence.py`, `scripts/agent/stdin_reader.py`
  - `scripts/agent/workflow_engine_adapter.py`, `scripts/agent/tool_approval.py`, `scripts/agent/tool_policy.py`
  - `scripts/agent/bg_task_monitor.py`, `scripts/agent/signal_handler.py`
  - `scripts/agent/workflow/workflow_engine.py`
- **Not reviewed:** `workflow/workflow_engine.py` internals beyond its hand-off contract (toolexec001 rows 08/09), `docs/23_agent/` prose (Phase 7 cross-checked only for the two repeat-guard defaults), and generated/vendored code (`__pycache__/`, `.venv/`).
- **Working tree vs reviewed head:** matched. `git status --short` clean; `HEAD = 95b23d1905591315d603cf1925bcd9cf716a6890`.
- **Commands run:**
  - `uv run ruff check` on the 6 core files → `All checks passed!`
  - `uv run mypy --no-namespace-packages` on the 6 core files → `Success: no issues found in 6 source files`
  - `uv run pytest` on the affected module trees → `457 passed` (`test_repl`, `test_repl_error_handling`, `test_stdin_reader`, `test_tool_loop_guard`, `test_llm_turn_runner`, `test_tool_runner`, `test_orchestrator`, `test_turn_persistence`)

### Summary

- **Overall assessment:** The core REPL action flow is correct and safe. Every trust-boundary gate, id-completeness invariant, and shutdown race handled in the reviewed paths holds against adversarial tracing. One Low finding survives Phase 8 (a redundant guard evaluation). No Critical/High/Medium defect was found.
- **Highest-risk area:** None elevated. The shutdown/dispatch race in `ReplInputLoop._repl_loop` and the per-call id-completeness guarantee in `complete_round` were the highest-risk surfaces; both verified clean.
- **Recommended next step:** `proceed`. The single Low finding is optional cleanup; it does not block. See Final Recommendation.

### Findings

#### F-001 — Empty-result-repeat guard is evaluated twice per turn; the turn-start call in `ToolLoopGuard.check_all` is provably inert

- **Severity:** Low
- **Confidence:** High
- **Evidence label:** Explicit in code
- **Evidence:**
  - `tool_loop_guard.py:check_all` runs `check_cycle`, `_check_progress_stagnation`, `check_empty_result_repeat`, `check_dedup`, `check_retry` in order and returns the first hit. The empty-result call sits at the top of each turn.
  - `llm_turn_runner.py:run` calls `self._guard.check_all(...)` at the top of every loop iteration (before tool execution), then again after `execute_all_tool_calls` at the post-execution point where `check_empty_result_repeat(message)` is called a second time (with `check_unavailable_repeat` and `check_error_limit` following).
  - `tool_runner.py:execute_one_tool_call` is the sole writer of `_empty_result_counts` (`guard.record_tool_result(name, text)` on a non-error result); `tool_runner.py:_run_group_calls` and `_run_plan_batches` also break early on `guard.scan_empty_result_repeat()`.
  - `config_dataclasses.py`: `tool_empty_result_max_repeats = 0` (disabled) by default; `docs/23_agent/agent_08_03_configuration-tools-memory.md:40` states both repeat guards default to 0 (disabled).
- **Current behavior:** When the guard is enabled (`> 0`), any per-tool empty-result count that reaches the threshold is caught by the post-execution `check_empty_result_repeat` in the same turn and fails that turn (`TurnResult(action="fail", reason="empty_result_repeat")`). Counts therefore never persist past a threshold crossing, so at the start of the next turn the turn-start `check_all` occurrence reads a count strictly below the threshold and returns `None`. When disabled (default), `scan_empty_result_repeat` returns `None` immediately and neither occurrence fires.
- **Impact:** No correctness, safety, or behavioral impact. The turn-start call performs no useful work in either mode; it is dead code that a maintainer reading `check_all`'s docstring ("Run cycle, stagnation, dedup, retry, and empty result guards in order") may assume is meaningful.
- **Recommended action:** Remove the `check_empty_result_repeat(message)` invocation from `ToolLoopGuard.check_all` and drop "empty result" from its docstring list. Add a one-line note that the empty-result guard is evaluated once per turn, after execution, in `LLMTurnRunner.run`. Keep the post-execution check untouched.

### Open Questions

- **Question:** Is the turn-start empty-result check intended as a defensive re-check for a future code path that could increment counts without reaching the post-execution check?
  - **Why it matters:** If such a path is planned, removing the call would drop the defense.
  - **Required confirmation:** Confirm no in-turn path increments `_empty_result_counts` other than `execute_one_tool_call` (currently true: it is the sole writer). If confirmed, the call is purely redundant.

### Suggested Tests

- **Test target:** `tests/agent/test_tool_loop_guard.py`, `tests/agent/test_llm_turn_runner.py`
- **Behavior to verify:** After removing the turn-start call, an empty-result sequence that crosses the threshold is still detected via the post-execution check and fails the turn with `reason="empty_result_repeat"`; a disabled guard (`0`) still performs no detection.
- **Failure mode:** A regression would show the turn continuing past the threshold (missing detection) or a test asserting the removed call's existence.

### Documentation Notes

- **Target document:** `docs/23_agent/agent_08_03_configuration-tools-memory.md`
- **Required update:** None required. The doc correctly documents the default-off policy for both repeat guards; it does not describe the per-turn evaluation topology that F-001 concerns.
- **Reason:** The default values are intentional and correct (verified against `config_dataclasses.py`); nothing to change.

### Final Recommendation

`proceed`. The reviewed head is clean of Critical/High/Medium defects. ruff, mypy, and the 457 affected tests pass. The single Low finding (F-001) is non-blocking optional cleanup; it does not affect runtime behavior in either the default-disabled or enabled configuration. It is filed as an issue for optional resolution. No check remains unconfirmed in a high-risk area.
