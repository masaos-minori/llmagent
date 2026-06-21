# Implementation: Add Fallback Truncation When LLM History Compression Fails

## Goal

Bound context growth when LLM-based history compression fails by applying a deterministic fallback truncation strategy that preserves protected turns and drops low-value messages first. Make fallback usage observable via `/context`.

## Scope

**In-Scope:**
- Add `_fallback_truncate(history)` to `HistoryManager`; drop messages in priority order:
  1. `tool`-role messages (lowest value for future turns)
  2. Older non-tool messages outside the protected tail, sorted by importance ascending
  3. Stop when back under `_char_limit` OR nothing more to drop
- Add `stat_fallback_truncate_count: int = 0` to `HistoryManager`
- Add `is_fallback: bool = False` field to `CompressResult`
- In `compress()`: call `_fallback_truncate()` instead of returning unchanged history when `summary_text is None` and the limit is still exceeded
- Add `fallback_truncate_count: int` to `ContextStateView` + `collect_context_state()`
- Show fallback count in `/context` output (writer already handles `ContextStateView` fields)
- Add `_reset_for_testing()` that resets `stat_fallback_truncate_count`

**Out-of-Scope:**
- Replacing LLM-based compression or `HistoryCompressionError`
- Changing `history_protect_turns` semantics
- Adding a new configuration flag (fallback is always active when LLM fails)

## Assumptions

1. The existing `HistorySelectionPolicy.sort_by_importance()` provides the ordering needed to select truncation candidates — no new selection logic needed.
2. Dropping `tool`-role messages is safe because they are only needed for immediate LLM turn context; older tool messages have no retention value.
3. `_char_limit` is always > 0 when `compress()` is triggered (confirmed by `_is_over_char_limit`).
4. `CompressResult` is a frozen dataclass — add `is_fallback` with default `False` to keep backward compatibility.
5. `ContextStateView` is a plain dataclass — adding `fallback_truncate_count` with default `0` is backward-compatible.

## Unknowns & Gaps

| ID | Unknown | Evidence Missing | Resolution | Blocking |
|---|---|---|---|---|
| UNK-01 | Should fallback truncation also apply when `_token_limit` is exceeded (not just char limit)? | The require says "context size remains bounded"; token limit is secondary to char limit | Apply fallback for both over_char and over_token cases — check count_chars after truncation | False |
| UNK-02 | Should the `/context` command display the fallback count only when > 0? | No policy stated | Show it always ("0") to communicate the stat exists; helps operators distinguish normal from degraded | False |
| UNK-03 | What if fallback truncation drops all messages and still exceeds the limit? | Edge case: single very large message | Log a WARNING "Fallback truncation could not bring context under limit" and return best-effort | False |

## Implementation

### Target files

- `scripts/agent/history.py` — `_fallback_truncate()`, `stat_fallback_truncate_count`, `CompressResult.is_fallback`, `compress()` call site
- `scripts/agent/services/models.py` — `ContextStateView.fallback_truncate_count: int = 0`
- `scripts/agent/services/context_view.py` — pass `fallback_truncate_count` to `ContextStateView`
- `scripts/agent/cli_view.py` or writer — show fallback count in `/context` output
- `tests/test_history_manager.py` (verify existing coverage) or new test file — add fallback tests

### Procedure

#### Step 1: Add `is_fallback` to `CompressResult`

In `history.py`: `CompressResult.is_fallback: bool = False`
No callers break (field is read-only).

#### Step 2: Add `stat_fallback_truncate_count` to `HistoryManager`

Init: `self.stat_fallback_truncate_count: int = 0`

#### Step 3: Implement `_fallback_truncate()`

```python
def _fallback_truncate(
    self, history: list[LLMMessage]
) -> tuple[list[LLMMessage], CompressResult]:
    """Drop low-value messages to bring context under char limit.

    Drop order: tool-role first, then oldest unimportant messages outside protected tail.
    Preserves system messages and the most-recent protect_turns turn pairs.
    """
    protected_tail = self._selection_policy.get_protected_tail(history)
    system_msgs = [m for m in history if m["role"] == "system"]
    remaining = [m for m in history if m not in set(map(id, system_msgs)) and m not in protected_tail]
    # Sort by importance ascending (lowest importance = truncate first)
    candidates = self._selection_policy.sort_by_importance(remaining, ascending=True)
    dropped = 0
    new_history = list(history)
    for msg in candidates:
        if not self._is_over_char_limit(new_history):
            break
        new_history.remove(msg)
        dropped += 1
    self.stat_fallback_truncate_count += 1
    if self._is_over_char_limit(new_history):
        logger.warning(
            "Fallback truncation could not bring context under limit:"
            " chars=%d limit=%d",
            self.count_chars(new_history),
            self._char_limit,
        )
    logger.info("Fallback truncation applied: dropped %d messages", dropped)
    return new_history, CompressResult(
        compressed_count=dropped, protected_count=len(protected_tail),
        summary_added=False, is_fallback=True
    )
```

Note: `HistorySelectionPolicy` may need a `get_protected_tail()` method if not already exposed.

#### Step 4: Update `compress()` call site

Replace:
```python
if summary_text is None:
    return history, _no_op
```
with:
```python
if summary_text is None:
    return self._fallback_truncate(history)
```

#### Step 5: Update `ContextStateView` and `collect_context_state()`

- `models.py`: add `fallback_truncate_count: int = 0`
- `context_view.py`: pass `fallback_truncate_count=ctx.services.hist_mgr.stat_fallback_truncate_count`
- Verify that the `/context` command writer uses this field

#### Step 6: Add tests

- Test: when LLM fails, `compress()` calls `_fallback_truncate()` and returns compressed history
- Test: `stat_fallback_truncate_count` increments on fallback
- Test: `CompressResult.is_fallback == True` on fallback path
- Test: protected turns are preserved after fallback
- Test: tool-role messages are dropped before user/assistant messages

### Method

- New method `_fallback_truncate()` in `HistoryManager` (~30 lines)
- Add `is_fallback` field to frozen `CompressResult` dataclass (backward-compatible default)
- Add `fallback_truncate_count` to `ContextStateView` dataclass (backward-compatible default)
- Replace `_no_op` return path with fallback truncation

### Details

- `HistorySelectionPolicy` may need `get_protected_tail()` or `sort_by_importance(ascending=True)` — check existing API before implementing
- `list.remove()` in `_fallback_truncate` is O(n) per drop — fine for typical history sizes (< 200 msgs)
- Adding `fallback_truncate_count` to `ContextStateView` with default `= 0` prevents positional arg breakage

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `_fallback_truncate()` logic | Unit | `uv run pytest tests/ -k history -v` | all pass |
| `stat_fallback_truncate_count` | Unit — mock LLM fail | `uv run pytest tests/ -k history -v` | count increments |
| `ContextStateView.fallback_truncate_count` | Unit — `collect_context_state` | `uv run pytest tests/ -k context -v` | field present |
| Lint | Static | `uv run ruff check scripts/` | 0 errors |
| Type check | Static | `uv run mypy scripts/` | no new errors |
| Full suite | Regression | `uv run pytest -q` | no new failures |

## Risks

- **Risk:** `HistorySelectionPolicy` has no `get_protected_tail()` or `sort_by_importance(ascending=True)`
  → **Mitigation:** check existing API before implementing; add minimal helpers if needed
- **Risk:** `list.remove()` in `_fallback_truncate` is O(n) per drop — fine for typical history sizes (< 200 msgs)
  → **Mitigation:** no action needed; flag if history ever exceeds 1000 messages
- **Risk:** Adding `fallback_truncate_count` to `ContextStateView` breaks tests that construct it with positional args
  → **Mitigation:** use `= 0` default; grep for `ContextStateView(` to verify no positional construction
