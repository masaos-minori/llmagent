# Implementation Procedure: Integrate Empty Result Repeat Guard into Turn Loop

## Goal

Integrate the new `check_empty_result_repeat()` guard into the turn loop so it is checked after each tool execution, following the same pattern as `check_error_limit()`.

## Scope

- Modify `scripts/agent/llm_turn_runner.py`: add call to `check_empty_result_repeat()` after tool execution.
- No other files modified in this document.

## Assumptions

- The guard instance (`self._guard`) is already available in `LLMTurnRunner`.
- `check_empty_result_repeat()` returns `GuardHint | None` like other guard methods.
- The guard hint handling logic is consistent across all guards.

## Design decisions

- Call `check_empty_result_repeat()` after `execute_all_tool_calls()`, similar to how `check_error_limit()` is called.
- Return early with a fail action when the guard triggers, consistent with existing guard behavior.
- Pass the current LLM message to `check_empty_result_repeat()` for context.

## Alternatives considered

1. **Call inside `check_all()`**: Would require changing the `check_all()` signature to accept execution results. Less desirable given the existing contract.
2. **Call before tool execution**: Would prevent the issue from occurring but wouldn't catch the actual problem (empty results from execution).
3. **Use a separate guard check method**: Would isolate the new logic but adds unnecessary complexity.

## Implementation

### Target file
`scripts/agent/llm_turn_runner.py`

### Procedure

1. Add call to `self._guard.check_empty_result_repeat(message)` after `execute_all_tool_calls()`.
2. Handle the guard hint return value similarly to `check_error_limit()`.

### Method

```python
async def run(
    self,
    llm_url: str,
    *,
    workflow_id: str,
    task_id: str,
    stage_id: str,
    attempt_id: str,
) -> TurnResult:
    """Send ctx.conv.history to LLM, execute tool calls, return TurnResult."""
    if not (workflow_id and task_id and stage_id and attempt_id):
        raise RuntimeError(
            "LLMTurnRunner.run() requires non-empty workflow context: "
            f"workflow_id={workflow_id!r}, task_id={task_id!r}, "
            f"stage_id={stage_id!r}, attempt_id={attempt_id!r}"
        )
    ctx = self._ctx
    state = TurnLoopState()

    for turn in range(ctx.cfg.tool.max_tool_turns):
        try:
            response = await self._stream_llm(llm_url, turn)
        except LLMTransportError as e:
            return await self._handle_llm_error(
                e, turn, workflow_id=workflow_id, task_id=task_id
            )

        message, finish_reason = response.message, response.finish_reason

        has_tool_calls = bool(message.get("tool_calls"))
        if (finish_reason != "tool_calls") or not has_tool_calls:
            answer = await self._finalize_answer_text(message)
            return TurnResult(action="continue", answer=answer)

        if msg := self._guard.check_all(
            state.seen_calls,
            state.round_fingerprints,
            state.failed_calls,
            message,
        ):
            return await self._finalize_after_guard()

        await ctx.conv.append_message(message)
        ctx.session.save(
            "assistant",
            message.get("content") or "",
            tool_calls=message.get("tool_calls"),
        )

        errors_before = ctx.stats.stat_tool_errors
        await execute_all_tool_calls(
            ctx,
            message["tool_calls"],
            turn,
            out_failed_keys=state.failed_calls,
        )
        n_errors = ctx.stats.stat_tool_errors - errors_before
        state.consecutive_errors = ToolLoopGuard.update_errors(
            state.consecutive_errors, n_errors, len(message["tool_calls"])
        )
        
        # New: Check empty result repeat guard after tool execution
        if msg := self._guard.check_empty_result_repeat(message):
            return TurnResult(action="fail", answer=msg, reason="empty_result_repeat")
        
        if msg := self._guard.check_error_limit(state.consecutive_errors):
            return TurnResult(action="fail", answer=msg, reason="error_limit")

    logger.warning("Reached max_tool_turns=%s", ctx.cfg.tool.max_tool_turns)
    return TurnResult(
        action="fail",
        answer="Maximum tool turns reached.",
        reason="max_tool_turns",
    )
```

### Details

- Added `if msg := self._guard.check_empty_result_repeat(message):` block after `execute_all_tool_calls()`.
- Returns `TurnResult(action="fail", answer=msg, reason="empty_result_repeat")` when triggered.
- Placed before `check_error_limit()` to prioritize empty-result detection over error-limit detection.
- Uses the same pattern as `check_error_limit()` for consistency.

## Compatibility considerations

- Adding a new guard check does not change the function's return type or side effects.
- The new check follows the same pattern as existing checks, ensuring consistency.
- Error results are excluded from empty-result tracking, which aligns with the existing behavior where errors are handled separately.

## Security considerations

- No security impact. This change only affects loop-detection behavior.

## Rollback considerations

- Revert: remove the `check_empty_result_repeat()` call and its associated logic.
- No migration needed since the default `None` value ensures backward compatibility.

## Validation plan

1. Verify `check_empty_result_repeat()` is called after `execute_all_tool_calls()`.
2. Verify the guard hint is returned correctly when triggered.
3. Verify the turn fails with the correct reason ("empty_result_repeat").
4. Verify the feature works when guard is not present (backward compatibility).

## Completion criteria

- [ ] `check_empty_result_repeat(message)` is called after `execute_all_tool_calls()`.
- [ ] Guard hint is handled consistently with existing guard checks.
- [ ] Turn fails with `reason="empty_result_repeat"` when triggered.
- [ ] Backward compatibility maintained (no crash when guard is absent).

## Out of scope

- Implementing the guard logic itself (covered in `scripts/agent/tool_loop_guard.py`).
- Adding the config field (covered in `scripts/agent/config_dataclasses.py`).
- Wiring tool results into guard state (covered in `scripts/agent/tool_runner.py`).
- Updating documentation or tests (covered in respective documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | |
| 2 | Add or update tests per Validation plan | Completed | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A: no docs/00_index.md task-scope mapping for scripts/agent/llm_turn_runner.py |

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
- **Requirement ID**: REQ-001 (Detect repeated empty tool results within a single turn)
- **Source issue**: issues/done/20260908-194034_toolloop002_detect-empty-tool-result-repetition.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-221112_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260909-181137
- **Related target files**: scripts/agent/llm_turn_runner.py
