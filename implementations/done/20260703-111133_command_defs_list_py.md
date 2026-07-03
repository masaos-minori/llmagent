## Goal

Expand the module docstring of `command_defs_list.py` to declare it as the single source of truth for `_COMMANDS` and instruct future contributors to add built-in commands here only.

## Scope

- In-Scope:
  - Replace the existing 4-line module docstring (lines 1–5) with an expanded version that includes an explicit "single source of truth" ownership declaration and a "future additions" instruction
  - No changes to `_COMMANDS` list, imports, or any other code
- Out-of-Scope:
  - The `_COMMANDS` list definition itself
  - `CommandDef` import
  - Any other file in `scripts/agent/commands/`

## Assumptions

1. The existing docstring on line 1 is `"""command_defs_list.py — Built-in slash command definitions for AgentREPL.` and closes at line 5 before `from __future__ import annotations`.
2. Docstring-only changes have no runtime effect; no tests assert on module docstring content.
3. Adding the phrase "single source of truth" (or equivalent) is sufficient to satisfy the completion criterion.
4. The docstring does NOT need to enumerate every command; it only needs to state ownership and provide guidance.

## Implementation

### Target file

`/home/masaos/llmagent/scripts/agent/commands/command_defs_list.py`

### Procedure

1. Read the current file to confirm the exact text of the existing docstring (lines 1–5).
2. Replace the existing docstring (lines 1–5) with the expanded docstring shown in the Method section.
3. Confirm that the line immediately after the docstring is still `from __future__ import annotations`.
4. Run `python3 -c "import ast; ast.parse(open('scripts/agent/commands/command_defs_list.py').read())"` to confirm no syntax error.

### Method

Use the `Edit` tool with `old_string` equal to the current full docstring and `new_string` equal to the replacement.

Replacement docstring:

```python
"""command_defs_list.py — Built-in slash command definitions for AgentREPL.

This module is the SINGLE SOURCE OF TRUTH for the _COMMANDS list.
All built-in slash commands are defined here and only here.

Owns:
  _COMMANDS: list[CommandDef] — ordered list of all built-in slash commands.
                                Exact-match commands are listed first;
                                prefix commands follow.

Does NOT own:
  CommandDef / SubcommandSpec dataclasses — defined in agent.commands.command_defs.

To add a built-in command:
  1. Append (or insert) a CommandDef(...) entry in _COMMANDS below.
  2. Implement the corresponding _cmd_<name> handler in the appropriate mixin.
  3. Do NOT add CommandDef entries anywhere else.
"""
```

### Details

- Current docstring text (lines 1–5) to replace:
  ```
  """command_defs_list.py — Built-in slash command definitions for AgentREPL.

  This module contains the _COMMANDS list that defines all built-in slash commands.
  For the CommandDef class definition, see agent.commands.command_defs.
  """
  ```
- The key addition is the explicit `SINGLE SOURCE OF TRUTH` declaration, the `Owns:` / `Does NOT own:` blocks, and the step-by-step `To add a built-in command:` note.
- The inline comment `# Single source of truth for all built-in slash commands.` already exists above `_COMMANDS` at line 11 — keep it as-is.

## Validation plan

```bash
# Confirm docstring contains the ownership claim
python3 -c "
import ast
src = open('scripts/agent/commands/command_defs_list.py').read()
t = ast.parse(src)
ds = ast.get_docstring(t)
print(ds)
assert 'single source of truth' in ds.lower() or 'SINGLE SOURCE OF TRUTH' in ds, 'missing ownership claim'
assert '_COMMANDS' in ds, 'missing _COMMANDS reference'
print('OK')
"

# Full test suite
uv run pytest tests/
```

Expected: Python assertion prints `OK`; all tests pass.
