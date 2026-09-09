# Implementation Procedure: Wire Tool Results into Guard State

## Goal

Wire tool execution results into `ToolLoopGuard`'s per-turn state so that `check_empty_result_repeat()` receives data about empty results from executed tools.

## Scope

- Modify `scripts/agent/tool_runner.py`: add calls to `guard.record_tool_result()` after tool execution completes.
- No other files modified in this document.

## Assumptions

- `AgentContext` has a reference to the guard instance (e.g., `ctx.guard`).
- The guard is available at the point where tool results are collected.
- Empty result detection should happen on the full result text, not just the truncated version.

## Design decisions

- Call `guard.record_tool_result(name, text)` in `_collect_tool_result_msgs()` after processing each tool result.
- Use the full result text (`text`), not the truncated `llm_text`, for empty detection.
- Skip recording for denied tool calls (they don't produce real results).
- Handle both successful and error results — an error result is not considered "empty".

## Alternatives considered

1. **Record in `execute_one_tool_call()`**: Would capture results earlier but would require passing the guard through multiple layers. Less clean separation.
2. **Record in `execute_all_tool_calls()`**: Would allow batching but loses individual result granularity needed for per-tool counting.
3. **Use event hooks**: Would decouple the recording from the caller but adds unnecessary complexity for a simple use case.

## Implementation

### Target file
`scripts/agent/tool_runner.py`

### Procedure

1. Add import for `ToolLoopGuard` type checking (if not already imported).
2. In `_collect_tool_result_msgs()`, after processing each tool result, call `guard.record_tool_result(name, text)`.
3. Ensure the guard is accessed safely (check for None before calling).

### Method

```python
async def _collect_tool_result_msgs(
    ctx: AgentContext,
    results: list[tuple[str, str, dict, str, bool, str]],
    turn: int,
    out_failed_keys: set[str] | None,
) -> list[tuple[str, str | None, list[dict] | None, str | None]]:
    """Log, display, persist, and append tool results to history.

    Returns tool_msgs for session.save_many(). Applies per-turn char limit.
    Raises sqlite3.Error when tool result persistence fails.
    """
    tool_msgs: list[tuple[str, str | None, list[dict] | None, str | None]] = []
    turn_chars = 0
    
    # Get guard reference for empty-result repeat detection
    guard = getattr(ctx, "guard", None)
    
    for tc_id, name, args, text, is_error, llm_text in results:
        _update_stats_for_result(ctx, name, args, is_error, out_failed_keys)
        masked = mask_args(args, ctx.cfg.tool.masked_fields)
        _log_and_emit_tool_call(turn + 1, name, masked)
        _emit_tool_result(text, name)
        
        # Wire tool result into guard for empty-result repeat detection
        if guard is not None and not is_error:
            guard.record_tool_result(name, text)
        
        llm_text = _apply_turn_char_limit(
            llm_text,
            turn_chars,
            limit=ctx.cfg.tool.tool_results_turn_max_chars,
        )
        turn_chars += len(llm_text)
        await ctx.conv.append_message(
            {"role": "tool", "tool_call_id": tc_id, "content": llm_text}
        )
        tool_msgs.append(("tool", llm_text, None, tc_id))
    return tool_msgs
```

### Details

- Added `guard = getattr(ctx, "guard", None)` at the start of the function.
- Added conditional call `guard.record_tool_result(name, text)` inside the loop, after `_emit_tool_result()`.
- Only record non-error results — errors are not "empty" results.
- Use `text` (full result) rather than `llm_text` (truncated) for accurate empty detection.
- Check `guard is not None` before calling to handle cases where guard may not be initialized.

## Compatibility considerations

- Adding `getattr(ctx, "guard", None)` is backward-compatible — existing code without a guard will simply skip the recording.
- The new call does not change the function's return value or side effects.
- Error results are excluded from empty-result tracking, which aligns with the existing behavior where errors are handled separately.

## Security considerations

- No security impact. This change only affects loop-detection behavior.

## Rollback considerations

- Revert: remove the `guard` variable and the `record_tool_result()` call.
- No migration needed since the default `None` value ensures backward compatibility.

## Validation plan

1. Verify `record_tool_result()` is called with correct arguments for each tool result.
2. Verify empty results trigger counter increments correctly.
3. Verify non-empty results reset counters correctly.
4. Verify error results do not affect empty-result counting.
5. Verify the feature works when guard is not present (backward compatibility).

## Completion criteria

- [ ] `guard` variable is obtained from `ctx` using `getattr(ctx, "guard", None)`.
- [ ] `guard.record_tool_result(name, text)` is called after `_emit_tool_result()`.
- [ ] Only non-error results are recorded.
- [ ] Full result text (`text`) is used, not truncated version (`llm_text`).
- [ ] Backward compatibility maintained (no crash when guard is absent).

## Out of scope

- Implementing the guard logic itself (covered in `scripts/agent/tool_loop_guard.py`).
- Adding the config field (covered in `scripts/agent/config_dataclasses.py`).
- Updating documentation or tests (covered in respective documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Related target files**: scripts/agent/tool_runner.py
