# Implementation: scripts/agent/commands/registry.py — Remove duplicate _COMMANDS block from registry.py

**Plan source:** `plans/20260702-202746_plan.md` (Phase 2)
**Target file:** `scripts/agent/commands/registry.py`

---

## Goal

Eliminate the duplicate _COMMANDS list definition in registry.py by extending the existing import from command_defs.py and deleting the local block, making command_defs.py the single source of truth.

---

## Scope

**In:**
- Extend the existing import from agent.commands.command_defs to include both `_COMMANDS` and `CommandDef`
- Delete the local `_COMMANDS: list[CommandDef] = [...]` block (lines 47-213) from registry.py

**Out:**
- Any changes to command_defs.py (handled in Phase 1)
- Changes to command handler logic or routing

---

## Assumptions

1. registry.py already imports from agent.commands.command_defs but only imports a subset; the import line needs extending to add _COMMANDS and CommandDef
2. The local _COMMANDS block in registry.py (lines 47-213) is an exact duplicate of the list in command_defs.py and can be safely removed after the import is in place

---

## Implementation

### Target file

`scripts/agent/commands/registry.py`

### Procedure

1. Read registry.py to confirm the current import line from agent.commands.command_defs and the extent of the local _COMMANDS block
2. Edit the import line to: `from agent.commands.command_defs import _COMMANDS, CommandDef`
3. Delete the local `_COMMANDS: list[CommandDef] = [...]` block (lines 47-213)
4. Run `grep -Rn "^_COMMANDS" scripts/agent/commands/` and confirm only command_defs.py appears
5. Run the full toolchain: ruff check, mypy, lint-imports, uv run pytest

### Method

Edit tool for import extension and block deletion; grep for validation

### Details

- Import change: find the existing `from agent.commands.command_defs import ...` line and add `_COMMANDS, CommandDef` to the imported names
- Block to delete: the entire `_COMMANDS: list[CommandDef] = [` ... `]` literal including all CommandDef(...) entries and the closing bracket in registry.py
- After deletion, registry.py should reference _COMMANDS from the import only

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Single definition check | grep -Rn "^_COMMANDS" scripts/agent/commands/ | Only command_defs.py listed |
| No local block | grep -n "_COMMANDS" scripts/agent/commands/registry.py | Only import and usage lines, no definition |
| Lint | ruff check scripts/agent/commands/ | 0 errors |
| Type check | mypy scripts/agent/commands/ | no new errors |
| Import lint | python -m lint_imports (if configured) | no violations |
| Tests | uv run pytest | all pass |
