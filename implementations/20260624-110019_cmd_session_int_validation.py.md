# Implementation Procedure: scripts/agent/commands/cmd_session.py

## Goal

`cmd_session.py` の 3 箇所の `.isdigit()` チェックを正確な整数バリデーションに置き換える。

## Scope

**In:**
- `scripts/agent/commands/cmd_session.py` — lines 70, 77 (session ID), 92 (list limit)

**Out:** セッション読み込み/削除動作の変更

## Implementation

### lines 70, 77 — session ID バリデーション

```python
# Before:
if not arg.isdigit():
    self._out.write_validation_error("...")
    return
session_id = int(arg)

# After:
try:
    sid = int(arg)
    if sid <= 0:
        raise ValueError
except (ValueError, TypeError):
    self._out.write_validation_error("Invalid session ID: must be a positive integer")
    return
session_id = sid
```

### line 92 — list limit

```python
# Before:
limit = int(limit_arg) if limit_arg.isdigit() else 20

# After:
from agent.commands.utils import parse_flag_int
limit = parse_flag_int(limit_arg if limit_arg else None, default=20)
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| isdigit なし | `grep -n "isdigit" scripts/agent/commands/cmd_session.py` | 0 matches |
| Tests | `uv run pytest tests/ -k "session" -x -q` | all pass |
