# Implementation: history_selection_policy.py

## Goal

Replace the anonymous `tuple[list, list, list] | None` return type of `select_turns_to_compress()` with a typed `SelectionResult` dataclass so callers can access fields by name rather than by index.

## Scope

- Target: `scripts/agent/history_selection_policy.py`
- Add `SelectionResult` dataclass with `system_msgs`, `to_compress`, `remaining` fields
- Change `select_turns_to_compress()` return type from `tuple[...] | None` to `SelectionResult | None`
- Update caller in `history.py` to use `result.system_msgs`, `result.to_compress`, `result.remaining`

## Assumptions

1. `history.py` is the only caller of `select_turns_to_compress()`; the destructuring `split = ...; system_msgs, to_compress, remaining = split` becomes `result = ...; result.system_msgs` etc.
2. No other callers exist (confirmed by grep).

## Implementation

### Target file

`scripts/agent/history_selection_policy.py`

### Procedure

1. Add at the top of the file:
   ```python
   from dataclasses import dataclass
   from rag.types import LLMMessage

   @dataclass(frozen=True)
   class SelectionResult:
       system_msgs: list[LLMMessage]
       to_compress: list[LLMMessage]
       remaining: list[LLMMessage]
   ```
2. Change `select_turns_to_compress()` return type to `SelectionResult | None`.
3. Replace the `return system_msgs, to_compress, remaining` with `return SelectionResult(system_msgs=..., to_compress=..., remaining=...)`.
4. Update `history.py`:
   - `split = self._selection_policy.select_turns_to_compress(history)` stays the same.
   - `if split is None: return history, _no_op` stays the same.
   - Change `system_msgs, to_compress, remaining = split` to use `split.system_msgs`, `split.to_compress`, `split.remaining`.

### Method

Pure structural change — no logic change. `frozen=True` makes `SelectionResult` immutable, which is appropriate since it represents a snapshot of the selection.

### Details

```python
@dataclass(frozen=True)
class SelectionResult:
    system_msgs: list[LLMMessage]
    to_compress: list[LLMMessage]
    remaining: list[LLMMessage]
```

In `history.py`, the call site changes from:
```python
system_msgs, to_compress, remaining = split
```
to:
```python
system_msgs = split.system_msgs
to_compress = split.to_compress
remaining = split.remaining
```

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/history_selection_policy.py scripts/agent/history.py` | 0 errors |
| Type check | `uv run mypy scripts/` | no new errors |
| Tests | `uv run pytest tests/ -k "history"` | all pass |
