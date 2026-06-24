# Implementation Procedure: scripts/agent/commands/cmd_db.py

## Goal

`cmd_db.py:253` の `.isdigit()` ベース limit 解析を `parse_flag_int()` で置き換える。

## Scope

**In:**
- `scripts/agent/commands/cmd_db.py` line 253

**Out:** `/db` コマンド動作の再設計

## Implementation

### cmd_db.py:253

```python
# Before:
limit = int(limit_raw) if limit_raw and str(limit_raw).isdigit() else 20

# After:
from agent.commands.utils import parse_flag_int
limit = parse_flag_int(limit_raw, default=20)
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| isdigit なし | `grep -n "isdigit" scripts/agent/commands/cmd_db.py` | 0 matches |
| Lint | `uv run ruff check scripts/agent/commands/cmd_db.py` | 0 errors |
