# Implementation Procedure: scripts/agent/commands/cmd_memory.py

## Goal

`cmd_memory.py` の 2 箇所の `.isdigit()` フィルタを `parse_flag_int()` で置き換える。

## Scope

**In:**
- `scripts/agent/commands/cmd_memory.py` — lines 102-104, 215

**Out:** メモリ取得ロジックの再設計

## Implementation

### _memory_list (line 103-104)

```python
# Before:
limit_args = [a for a in args if a.isdigit()]
limit = int(limit_args[0]) if limit_args else 10

# After:
from agent.commands.utils import parse_flag_int
limit_str = next((a for a in args if a not in ("semantic", "episodic")), None)
limit = parse_flag_int(limit_str, default=10)
```

### _memory_prune (line 215)

```python
# Before:
day_args = [a for a in args if a.isdigit()]
days = int(day_args[0]) if day_args else ctx.cfg.memory.memory_retention_days

# After:
from agent.commands.utils import parse_flag_int
day_str = next((a for a in args if a not in ("--dry-run",)), None)
days = parse_flag_int(day_str, default=ctx.cfg.memory.memory_retention_days)
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| isdigit なし | `grep -n "isdigit" scripts/agent/commands/cmd_memory.py` | 0 matches |
| Tests | `uv run pytest tests/ -k "memory" -x -q` | all pass |
