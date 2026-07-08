# Implementation: H-8 — Remove /tool CommandDef entry

## Goal

Remove the `/tool` slash-command registration from `_COMMANDS`, so it no longer appears in
`/help`, tab completion, or dispatch.

## Scope

**Target**: `scripts/agent/commands/command_defs_list.py`

**Depends on**: land together with `implementations/20260708-164900_cmd_tooling_h8.py.md`
(removing the `CommandDef` entry without removing `_cmd_tool` would leave dead code; removing
`_cmd_tool` without removing the `CommandDef` entry would cause `CommandRegistry.__init__()`'s
fail-fast validator to raise `AttributeError` since the handler name would no longer resolve).

**Out of scope**: every other `CommandDef` entry in this file (e.g. `/db`, `/set`) — unchanged.

## Assumptions

1. The `CommandDef("/tool", ...)` block is a single, self-contained 6-line entry with no shared
   state or ordering dependency on adjacent entries (confirmed by reading the surrounding
   `/db` and `/set` entries — each `CommandDef(...)` call is independent).
2. `_COMMANDS`' fail-fast validator in `CommandRegistry.__init__()` checks that every listed
   handler name (e.g. `"_cmd_tool"`) exists as a method — removing the entry is necessary and
   sufficient; it does not separately require the handler method to exist for entries NOT in the
   list (per the plan's U-3 analysis: "fail-fast only checks that listed handlers exist, not the
   reverse").

## Implementation

### Target file

`scripts/agent/commands/command_defs_list.py`

### Procedure

#### Step 1: Confirm the exact block boundaries

```bash
grep -n "\"/tool\"" -B1 -A6 scripts/agent/commands/command_defs_list.py
```

#### Step 2: Remove the block

Current (a `CommandDef(...)` entry between the `/db` and `/set` entries):

```python
    CommandDef(
        "/tool",
        True,
        False,
        "_cmd_tool",
        "list | show <idx>  Inspect stored tool results",
    ),
```

Remove this entire block. The preceding `/db` entry's closing `),` and the following `/set`
entry's opening `CommandDef(` become adjacent (with normal list-item spacing), exactly as if the
`/tool` entry had never existed between them.

### Method

- Single list-item deletion; no reordering of surrounding entries, no change to the `CommandDef`
  dataclass/namedtuple definition itself.

### Details

- The four positional/keyword values in the removed `CommandDef` (`"/tool"`, `True`, `False`,
  `"_cmd_tool"`, `"list | show <idx>  Inspect stored tool results"`) have no meaning outside this
  one entry — removing the whole tuple/call is a complete, self-contained deletion.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `ruff check scripts/agent/commands/command_defs_list.py` | 0 errors |
| Type check | `mypy scripts/` | no new errors |
| Grep (entry removed) | `grep -n "\"/tool\"\|_cmd_tool" scripts/agent/commands/command_defs_list.py` | no matches |
| Registry fail-fast | `PYTHONPATH=scripts .venv/bin/python -c "from agent.commands.registry import CommandRegistry"` (or equivalent instantiation smoke test) | no `AttributeError` at import/construction time |
| Manual check | run `/help` | no `/tool` line printed |
| Manual check | run `/tool list` | `dispatch()` returns `False` (command falls through as unrecognized, not handled) |
| Tests (full) | `uv run pytest -v` | no new failures once all H-8 docs are applied together |
| Pre-commit | `pre-commit run --all-files` | pass |
