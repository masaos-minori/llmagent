# Implementation: scripts/agent/commands/registry.py — Remove Duplicate _COMMANDS, Import from command_defs

**Plan source:** `plans/20260702-202746_plan.md` (Phase 2)
**Target file:** `scripts/agent/commands/registry.py`

---

## Goal

Remove the local `_COMMANDS` list from `registry.py` and import it from `command_defs.py`, making `command_defs.py` the single source of truth.

---

## Scope

**In:**
- Extend existing import: `from agent.commands.command_defs import _COMMANDS, CommandDef`
- Delete the local `_COMMANDS: list[CommandDef] = [...]` block (lines 47–213) from `registry.py`
- Confirm `_cmd_help()` and `dispatch()` still reference `_COMMANDS` correctly

**Out:**
- Changes to `command_defs.py` (Phase 1 — separate step)
- Changes to command handler implementations
- Plugin command dispatch

---

## Assumptions

1. `/approve` and `/reject` added to `command_defs.py` in Phase 1 before this step.
2. No external code imports `_COMMANDS` directly from `registry.py` (confirmed: `factory.py` imports from `command_defs`, not `registry`).
3. `CommandRegistry.__init__` fail-fast check (`hasattr(self, _cmd.handler)`) validates no handler is missing.

---

## Implementation

### Target file

`scripts/agent/commands/registry.py`

### Procedure

1. Extend the import line: `from agent.commands.command_defs import _COMMANDS, CommandDef`
2. Delete the local `_COMMANDS: list[CommandDef] = [...]` block (lines ~47–213).
3. Verify both `_cmd_help()` and `dispatch()` use `_COMMANDS` without modification.
4. Run: `grep -Rn "^_COMMANDS" scripts/agent/commands/` — expect only `command_defs.py`.
5. Run full toolchain: ruff, mypy, lint-imports, uv run pytest.

### Method

Edit tool for import line update. Edit tool for block deletion.

### Details

After deletion, `registry.py` no longer defines `_COMMANDS` locally. The variable name is unchanged, so all internal usages continue to work via the imported binding.

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Single definition | `grep -Rn "^_COMMANDS" scripts/agent/commands/` | Only `command_defs.py` |
| Lint | `ruff check scripts/agent/commands/registry.py` | 0 errors |
| Type check | `mypy scripts/agent/commands/registry.py` | No new errors |
| Architecture | `lint-imports` | 0 violations |
| Tests | `uv run pytest` | All pass |
| Manual smoke | `/help` in running agent | `/approve`, `/reject`, `/db`, `/mdq`, `/plugin` listed |
