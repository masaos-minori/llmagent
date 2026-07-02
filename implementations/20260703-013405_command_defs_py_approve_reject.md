# Implementation: scripts/agent/commands/command_defs.py — Add /approve and /reject, Fix /db is_async

**Plan source:** `plans/20260702-202746_plan.md` (Phase 1)
**Target file:** `scripts/agent/commands/command_defs.py`

---

## Goal

Make `command_defs.py` the single source of truth for all built-in slash commands by adding missing `/approve` and `/reject` entries and fixing the `/db` `is_async` flag.

---

## Scope

**In:**
- Fix `/db` `is_async` flag: change `False` to `True` on the `/db` `CommandDef` entry
- Add `/approve` entry after `/audit`: `CommandDef("/approve", True, False, "_cmd_approve", "[reason]  Approve the pending workflow task")`
- Add `/reject` entry after `/approve`: `CommandDef("/reject", True, False, "_cmd_reject", "[reason]  Reject the pending workflow task")`
- Verify all 24 commands are present in correct order

**Out:**
- Changes to `registry.py` (Phase 2 — separate step)
- Changes to `_cmd_approve` or `_cmd_reject` handler implementations

---

## Assumptions

1. `command_defs.py` is already imported in `registry.py`; only `_COMMANDS` needs to be added to the import (Phase 2).
2. The `_cmd_db` handler is `async def`; therefore `/db` must have `is_async=True`.
3. `/approve` and `/reject` handlers are defined in `cmd_workflow.py` (`_WorkflowMixin`).

---

## Implementation

### Target file

`scripts/agent/commands/command_defs.py`

### Procedure

1. Locate `/db` `CommandDef` entry (line ~136 area); change `is_async=False` to `is_async=True`.
2. After the `/audit` entry, add `/approve` `CommandDef`.
3. After `/approve`, add `/reject` `CommandDef`.
4. Verify all 24 commands present in correct order.
5. Run `ruff check scripts/agent/commands/command_defs.py`.

### Method

Edit tool for each insertion/modification.

### Details

New entries:
```python
CommandDef("/approve", True, False, "_cmd_approve", "[reason]  Approve the pending workflow task"),
CommandDef("/reject",  True, False, "_cmd_reject",  "[reason]  Reject the pending workflow task"),
```

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Single definition | `grep -Rn "^_COMMANDS" scripts/agent/commands/` | Only `command_defs.py` (after Phase 2 completes) |
| Lint | `ruff check scripts/agent/commands/command_defs.py` | 0 errors |
| Type check | `mypy scripts/agent/commands/` | No new errors |
| Tests | `uv run pytest` | All pass |
