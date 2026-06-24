# Implementation Procedure: scripts/agent/commands/registry.py

## Goal

`dispatch()` の先頭に型チェックと空文字列ガードを追加する。

## Scope

**In:**
- `scripts/agent/commands/registry.py` — `dispatch()` メソッド先頭

**Out:** コマンドルーティングロジックの再設計

## Implementation

### dispatch() 先頭にガード追加

```python
async def dispatch(self, line: str) -> bool:
    if not isinstance(line, str):
        raise TypeError(f"dispatch() requires str, got {type(line).__name__}")
    if not line:
        return False
    # ... 既存ループ ...
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/commands/registry.py` | 0 errors |
| 型チェック | `uv run mypy scripts/agent/commands/registry.py` | no new errors |
| Tests | `uv run pytest tests/ -k "registry" -x -q` | all pass |
