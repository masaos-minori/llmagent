# Implementation: Command Summary Maintenance Guidance

## Goal

Add guidance in `05_agent_01` and `05_agent_07` explaining how to keep command summary tables up to date when adding new commands.

## Scope

**In:**
- `docs/05_agent_01_introduction.md` — add "Maintaining the Command List" note
- `docs/05_agent_07_command_system.md` — add maintenance procedure at end of command registration section

**Out:** No code changes.

## Assumptions

1. Commands are registered in `agent/commands/registry.py` or equivalent.
2. Summary tables in docs are maintained manually.
3. The procedure should be a simple ordered checklist.

## Implementation

### Target file

`docs/05_agent_01_introduction.md`, `docs/05_agent_07_command_system.md`

### Procedure

1. Confirm command registry location:
   ```bash
   grep -rn "register_command\|CommandRegistry\|command_registry" agent/ --include="*.py" | head -10
   ```
2. Read `docs/05_agent_07_command_system.md` command registration section.
3. Add maintenance procedure.
4. Read `docs/05_agent_01_introduction.md` and add brief maintenance note.

### Method

Bash grep → Read docs → Edit patches.

### Details

**Maintenance procedure for `05_agent_07`:**

```markdown
## Maintaining the Command List

When adding a new slash command:

1. Add to `agent/commands/registry.py` (or the relevant `cmd_*.py` module)
2. Write a unit test: `tests/test_cmd_{name}.py`
3. Update the command summary table in this doc (§Command Reference)
4. Update the quick-start command list in `05_agent_01` §Quick Start
5. If the command is operator-facing (e.g., `/stats`, `/reload`): update `05_agent_10` §Operator Commands

> The command summary tables in docs are maintained manually. There is no auto-generation.
> Omitting step 3/4 causes the docs to drift — treat it as part of the definition-of-done.
```

**Brief note for `05_agent_01`:**

```markdown
> **Keeping this list current:** When a new command is added, update §Quick Start here AND the full reference in `05_agent_07`. See `05_agent_07` §Maintaining the Command List for the complete procedure.
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Maintenance procedure in 05_agent_07 | `grep -n "Maintaining the Command\|definition-of-done" docs/05_agent_07_command_system.md` | found |
| Note in 05_agent_01 | `grep -n "05_agent_07.*command\|Keeping this list" docs/05_agent_01_introduction.md` | found |
| No code changes | `git diff agent/` | empty |
