# Implementation: Extract HistorySelectionPolicy from HistoryManager

## Goal

Extract `_classify`, `_classify_importance`, `_partition_by_class`, `_sort_by_importance`,
and `_select_turns_to_compress` from `HistoryManager` into `HistorySelectionPolicy`
in `agent/history_selection_policy.py`.

## Scope

**In:**
- `scripts/agent/history_selection_policy.py`: new module with `HistorySelectionPolicy` class
- `scripts/agent/history.py`: `HistoryManager` instantiates `HistorySelectionPolicy` and
  delegates the five extracted methods to it; existing `@staticmethod` wrappers kept as
  backward-compatible aliases so `HistoryManager._classify_importance` still works

**Out:**
- Changing `compress()` / `force_compress()` public API
- Changing `_call_compress_llm()` or `_build_summary_msg()`

## Assumptions

- `test_history_manager.py` uses `_classify_importance = HistoryManager._classify_importance`;
  keeping the staticmethod wrapper means no test changes required
- `HistorySelectionPolicy` takes `compress_turns` and `protect_turns` in `__init__`

## Implementation

### `scripts/agent/history_selection_policy.py`

```python
"""agent/history_selection_policy.py
HistorySelectionPolicy — importance-based compression candidate selection.
"""
from __future__ import annotations
import re
from rag.types import LLMMessage

_POLICY_KEYWORDS = re.compile(...)  # same regex as history.py

class HistorySelectionPolicy:
    def __init__(self, compress_turns: int, protect_turns: int) -> None: ...
    @staticmethod
    def classify(msg: LLMMessage) -> str: ...
    @staticmethod
    def classify_importance(msg: LLMMessage) -> float: ...
    @staticmethod
    def partition_by_class(turn_msgs: list[LLMMessage]) -> tuple: ...
    @staticmethod
    def sort_by_importance(msgs: list[LLMMessage]) -> list[LLMMessage]: ...
    def select_turns_to_compress(self, history: list[LLMMessage]) -> ...: ...
```

### `scripts/agent/history.py`

- Remove `_POLICY_KEYWORDS` (moved to `history_selection_policy.py`)
- Add `self._selection_policy = HistorySelectionPolicy(compress_turns, protect_turns)`
- Keep `@staticmethod _classify_importance` as alias:
  `_classify_importance = HistorySelectionPolicy.classify_importance`
- Replace `self._partition_by_class(...)` → `self._selection_policy.partition_by_class(...)`
- Replace `self._sort_by_importance(...)` → `self._selection_policy.sort_by_importance(...)`
- Replace `self._select_turns_to_compress(...)` → `self._selection_policy.select_turns_to_compress(...)`

## Validation plan

```bash
uv run ruff check scripts/agent/history.py scripts/agent/history_selection_policy.py
uv run mypy scripts/
PYTHONPATH=scripts uv run lint-imports
uv run pytest tests/test_history_manager.py -v
```
