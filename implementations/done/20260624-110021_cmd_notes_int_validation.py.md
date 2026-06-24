# Implementation Procedure: scripts/agent/commands/cmd_notes.py

## Goal

`cmd_notes.py` の 3 箇所の `.isdigit()` チェックを try/except 正整数バリデーションに置き換える。

## Scope

**In:**
- `scripts/agent/commands/cmd_notes.py` — lines 54, 65, 76

**Out:** ノート永続化の変更

## Implementation

### _note_delete, _note_pin, _note_unpin (各メソッド)

```python
# Before:
if not arg.isdigit():
    self._out.write_validation_error("/note delete <id>")
    return
note_id = int(arg)

# After (全3メソッド共通パターン):
try:
    note_id = int(arg)
    if note_id <= 0:
        raise ValueError
except (ValueError, TypeError):
    self._out.write_validation_error("/note delete <id>")  # message varies per method
    return
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| isdigit なし | `grep -n "isdigit" scripts/agent/commands/cmd_notes.py` | 0 matches |
| Tests | `uv run pytest tests/ -k "note" -x -q` | all pass |
