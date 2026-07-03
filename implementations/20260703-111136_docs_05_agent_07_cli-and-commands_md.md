## Goal

Expand the `CommandRegistry` section of `docs/05_agent_07_cli-and-commands.md` by adding a "Module Ownership" sub-section with a three-module ownership table and a "future command additions" note.

## Scope

- In-Scope:
  - Insert a new sub-section `### Module Ownership` immediately after the existing content of the `## CommandRegistry` section (currently ending at line 64 with the `Boundary:` sentence)
  - The sub-section contains: a Markdown table listing the three modules with what each owns and does not own, and a note on where to add future commands
  - A horizontal rule `---` follows the existing `CommandRegistry` section at line 66; the insertion goes before this rule
- Out-of-Scope:
  - Any other section of the document
  - The `## Slash Command Reference` section or any command-level tables
  - Other documentation files

## Assumptions

1. The `## CommandRegistry` section body currently ends with line 64: `Boundary: \`line == name\` (exact) or \`line.startswith(name + " ")\` (prefix).`
2. Line 65 is blank and line 66 is `---` (the horizontal rule separating sections), confirmed by reading the file.
3. The new `### Module Ownership` sub-section should be inserted between the `Boundary:` sentence and the `---` rule, maintaining one blank line before and after the new content.
4. The three modules are: `command_defs.py`, `command_defs_list.py`, and `registry.py` — as specified in the plan.

## Implementation

### Target file

`/home/masaos/llmagent/docs/05_agent_07_cli-and-commands.md`

### Procedure

1. Read lines 56–70 of the file to confirm the exact current text of the `## CommandRegistry` section boundary.
2. Use `Edit` tool to replace the `Boundary:` line plus the trailing blank line plus `---` with the same text extended by the new sub-section before the `---`.
3. Verify that the `## Slash Command Reference` section header immediately after the `---` is still present and unmodified.

### Method

`old_string`:
```
Boundary: `line == name` (exact) or `line.startswith(name + " ")` (prefix).

---

## Slash Command Reference
```

`new_string`:
```
Boundary: `line == name` (exact) or `line.startswith(name + " ")` (prefix).

### Module Ownership

| Module | Owns | Does NOT Own |
|--------|------|--------------|
| `command_defs.py` | `CommandDef`, `SubcommandSpec` dataclasses | `_COMMANDS` list |
| `command_defs_list.py` | `_COMMANDS` — single source of truth for built-in commands | Dispatch logic |
| `registry.py` | Dispatch behavior; imports `_COMMANDS` from `command_defs_list` | `_COMMANDS` definition |

> **Future command additions:** add a new `CommandDef(...)` entry to `command_defs_list.py` only.
> Implement the corresponding `_cmd_<name>` handler in the appropriate mixin file.

---

## Slash Command Reference
```

### Details

- The `old_string` must match the exact characters around the `---` separator and the `## Slash Command Reference` header, because these are the stable anchors. Read lines 63–70 to confirm the exact wording before constructing `old_string`.
- The table uses standard GitHub-flavored Markdown pipe syntax consistent with existing tables in the file (e.g., the CLIView callbacks table at line 31).
- The blockquote `>` style for the note matches the style used elsewhere in this file (e.g., the workflow section note at line 154).
- `registry.py` entry in the table must state it *imports* `_COMMANDS` (not defines it), consistent with the actual `from agent.commands.command_defs_list import _COMMANDS` at line 42 of `registry.py`.

## Validation plan

```bash
# Confirm command_defs_list.py appears in the commands documentation
grep "command_defs_list" docs/05_agent_07_cli-and-commands.md
# Expected: at least one match (the table row)

# Confirm the ownership table heading exists
grep "Module Ownership" docs/05_agent_07_cli-and-commands.md
# Expected: one match

# Confirm the future additions note exists
grep "Future command additions" docs/05_agent_07_cli-and-commands.md
# Expected: one match

# Full test suite (no runtime breakage)
uv run pytest tests/
```

Expected: all three `grep` commands have exactly one match each; all tests pass.
