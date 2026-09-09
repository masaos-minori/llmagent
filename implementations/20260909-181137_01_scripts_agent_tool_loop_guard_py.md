# Implementation Procedure: Add Empty Result Repeat Guard to ToolLoopGuard

## Goal

Add a new guard method `check_empty_result_repeat` to `ToolLoopGuard` that detects repeated empty tool results from the same tool within a single turn, preventing infinite loops caused by tools returning empty results repeatedly.

## Scope

- Modify `scripts/agent/tool_loop_guard.py`: add new guard method, state tracking, hint emission, and integration into `check_all()`.
- No other files modified in this document.

## Assumptions

- A "tool result" is considered empty when the tool returns no meaningful output (e.g., `""`, `{}`, `None`).
- The guard should track empty results per-tool independently of arguments — different arguments calling the same tool should count toward the same counter.
- The threshold is configurable via `ToolConfig.tool_empty_result_max_repeats` (default `0` = disabled).
- Existing four guards' behavior/thresholds are unchanged.

## Design decisions

- Track empty results using a dict keyed by tool name (not tool+arguments), resetting at turn boundaries.
- Use `ToolConfig.tool_empty_result_max_repeats` as the threshold; `0` means disabled.
- Emit a HINT-level guard hint when triggered, consistent with existing guard hints.
- Do NOT modify `check_all()` signature — instead, accumulate empty-result data separately and expose it via a new method.

## Alternatives considered

1. **Include arguments in the key**: Would allow distinguishing empty results across different inputs but would miss the core problem — a tool consistently returning empty regardless of input.
2. **Add execution results to `check_all()` parameters**: Would require changing the public API of `ToolLoopGuard.check_all()`, affecting all callers. Less desirable given the existing contract.
3. **Use a separate guard instance**: Would isolate the new logic but adds unnecessary complexity and duplication.

## Implementation

### Target file
`scripts/agent/tool_loop_guard.py`

### Procedure

1. Add `EMPTY_RESULT_REPEAT_HINT` constant near other HINT constants.
2. Add `tool_empty_result_max_repeats` field to `ToolConfig` dataclass.
3. Add `_empty_result_counts: dict[str, int]` attribute to `ToolLoopGuard.__init__`.
4. Reset `_empty_result_counts` in `reset_per_turn_state()`.
5. Implement `record_tool_result(tool_name: str, result: Any) -> None` method.
6. Implement `check_empty_result_repeat(message: str) -> GuardHint | None` method.
7. Call `record_tool_result()` from the caller side after tool execution completes.
8. Call `check_empty_result_repeat(message)` inside `check_all()` alongside existing guards.

### Method

```python
def record_tool_result(self, tool_name: str, result: Any) -> None:
    """Record a tool result for empty-result repeat detection."""
    if self._config.tool_empty_result_max_repeats <= 0:
        return
    if not self._is_empty_result(result):
        # Reset counter on successful result
        self._empty_result_counts[tool_name] = 0
        return
    self._empty_result_counts[tool_name] = self._empty_result_counts.get(tool_name, 0) + 1

def check_empty_result_repeat(self, message: str) -> GuardHint | None:
    """Check if any tool has exceeded the empty result repeat threshold."""
    if self._config.tool_empty_result_max_repeats <= 0:
        return None
    for tool_name, count in self._empty_result_counts.items():
        if count >= self._config.tool_empty_result_max_repeats:
            return GuardHint(
                level=HINT_LEVEL_WARNING,
                code="TOOL_EMPTY_RESULT_REPEAT",
                message=f"Tool '{tool_name}' returned empty result {count} times in a row",
                details={"tool_name": tool_name, "repeat_count": count},
            )
    return None
```

### Details

- `_is_empty_result(result)`: Returns `True` if `result` is `""`, `{}`, `[]`, `None`, or equivalent empty value.
- `_empty_result_counts` resets at turn boundary via `reset_per_turn_state()`.
- When a non-empty result arrives for a tool, its counter resets to `0`.
- When an empty result arrives, increment the counter for that tool.
- `check_empty_result_repeat()` iterates over all tracked tools and returns a hint if any exceeds the threshold.
- Integration into `check_all()`: call `self.check_empty_result_repeat(message)` after existing checks.

## Compatibility considerations

- Adding `tool_empty_result_max_repeats` to `ToolConfig` requires updating any existing `ToolConfig` instantiations to include the new field with default value `0`.
- New HINT codes must not conflict with existing ones.
- The guard hint format must match existing hint structures for downstream consumers.

## Security considerations

- No security impact. This change only affects loop-detection behavior.

## Rollback considerations

- Revert: remove the new method, attribute, and config field. Restore `check_all()` to its original form.
- If `tool_empty_result_max_repeats` is added to `ToolConfig`, ensure backward compatibility by providing a default value during migration.

## Validation plan

1. Unit test: verify `record_tool_result()` increments/decrements counters correctly.
2. Unit test: verify `check_empty_result_repeat()` returns hint when threshold exceeded.
3. Unit test: verify reset behavior at turn boundaries.
4. Integration test: verify end-to-end flow with actual tool execution results.

## Completion criteria

- [ ] `ToolLoopGuard` has `check_empty_result_repeat()` method implemented.
- [ ] `ToolConfig` has `tool_empty_result_max_repeats` field with default `0`.
- [ ] `_empty_result_counts` is initialized and reset properly.
- [ ] `record_tool_result()` is called after tool execution completes.
- [ ] `check_empty_result_repeat()` is called inside `check_all()`.
- [ ] HINT constant `EMPTY_RESULT_REPEAT_HINT` is defined.
- [ ] All validation tests pass.

## Out of scope

- Implementing `_check_progress_stagnation()`.
- Changing existing four guards' behavior or thresholds.
- Handling empty LLM response content.
- Modifying `check_all()` signature to accept execution results.

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
- **Related target files**: scripts/agent/tool_loop_guard.py
