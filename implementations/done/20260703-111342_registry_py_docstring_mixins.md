## Goal

Replace the misaligned, incomplete `Mixins:` block in the module docstring of `registry.py` with a consistently column-aligned table that lists all 13 active mixins in MRO order — matching the `CommandRegistry` base-class list exactly.

## Scope

- In-Scope:
  - Replace lines 9–19 of the module docstring (the current `Mixins:` block)
  - Add the three missing mixins (`_AuditMixin`, `_WorkflowMixin`, `_PluginsMixin`)
  - Align all three columns (filename, class name with colon, command description) consistently
  - Add an inline note: "keep in sync with CommandRegistry base class list"
- Out-of-Scope:
  - Command behavior changes
  - Registry class or MRO refactoring
  - Changes to any file other than `registry.py`
  - Changes to command definitions

## Assumptions

1. The canonical source of truth for active mixins is the `CommandRegistry` inheritance list (lines 49–63 of `registry.py`), not the docstring.
2. No runtime test validates docstring content; the change has zero runtime impact.
3. Import order in the file is a secondary ordering guide; MRO order (lines 49–62) governs the final sequence in the docstring.
4. Column widths are anchored to the longest entries: `cmd_rag_export.py` (17 chars) for filenames and `_RagExportMixin:` (16 chars) for class names, giving a uniform column-2 width of 17 (class name + colon + trailing space to match `_RagExportMixin: `).

## Implementation

### Target file

`/home/masaos/llmagent/scripts/agent/commands/registry.py`

### Procedure

1. **Read the current file** to confirm the exact old_string for the Edit tool call (lines 9–19 of the docstring, the 10-line block starting with `Mixins:`).
2. **Apply the Edit tool** with the exact old_string and new_string shown in Details below. No other lines are touched.
3. **Verify parse-clean**: run `python -c "import ast; ast.parse(open('scripts/agent/commands/registry.py').read()); print('OK')"` — must print `OK`.
4. **Count rows**: confirm the docstring lists exactly 13 mixin rows; cross-check against the 13 base-class names in `CommandRegistry(...)` at lines 49–62.
5. **Diff check**: run `git diff scripts/agent/commands/registry.py` and confirm changes are confined to the docstring block only.
6. **Linter/type-checker**: run `uv run ruff check scripts/agent/commands/registry.py` and `uv run mypy scripts/agent/commands/registry.py` — both must exit 0.
7. **Full test suite**: run `uv run pytest` — all existing tests must remain green.

### Method

Use the `Edit` tool with `old_string` set to the exact current 10-line `Mixins:` block (verbatim, including 2-space indent per line). This is a pure text substitution — no AST manipulation needed.

Column alignment rule (spaces, no tabs):
- Column 1 (filename): left-aligned, padded to 17 chars, then ` — `
- Column 2 (class name + colon): left-aligned, padded to 17 chars, then the command description
- Every mixin line is indented with exactly 2 spaces inside the module docstring

The three newly added mixins and their sources (confirmed from import list, lines 28–40 of `registry.py`):
- `_AuditMixin` ← `agent.commands.cmd_audit` — handles `/audit`
- `_WorkflowMixin` ← `agent.commands.cmd_workflow` — handles `/approve`, `/reject`
- `_PluginsMixin` ← `agent.commands.cmd_plugins` — handles `/plugin`

### Details

**Exact old_string** (the current Mixins block in the file, lines 9–19, 2-space indent preserved):

```
Mixins:
  cmd_session.py  — _SessionMixin:  /session commands
  cmd_mcp.py      — _McpMixin:      /mcp commands
  cmd_config.py   — _ConfigMixin:   /config, /stats, /set, /reload
  cmd_context.py  — _ContextMixin:  /context, /clear, /undo, /history, /system
  cmd_db.py       — _DbMixin:       /db
  cmd_tooling.py  — _ToolingMixin:  /tool, /plan
  cmd_debug.py      — _DebugMixin:      /debug
  cmd_rag_export.py — _RagExportMixin:  /export, /compact, /rag
  cmd_memory.py   — _MemoryMixin:   /memory
  cmd_mdq.py      — _MdqMixin:      /mdq commands
```

**Exact new_string** (13 rows, consistently aligned, with keep-in-sync note):

```
Mixins (keep in sync with CommandRegistry base class list):
  cmd_session.py    — _SessionMixin:    /session commands
  cmd_mcp.py        — _McpMixin:        /mcp commands
  cmd_config.py     — _ConfigMixin:     /config, /stats, /set, /reload
  cmd_context.py    — _ContextMixin:    /context, /clear, /undo, /history, /system
  cmd_db.py         — _DbMixin:         /db
  cmd_tooling.py    — _ToolingMixin:    /tool, /plan
  cmd_debug.py      — _DebugMixin:      /debug
  cmd_audit.py      — _AuditMixin:      /audit
  cmd_rag_export.py — _RagExportMixin:  /export, /compact, /rag
  cmd_memory.py     — _MemoryMixin:     /memory
  cmd_workflow.py   — _WorkflowMixin:   /approve, /reject
  cmd_plugins.py    — _PluginsMixin:    /plugin
  cmd_mdq.py        — _MdqMixin:        /mdq commands
```

Failure path: if `old_string` does not match exactly (e.g., due to a prior whitespace-only commit), read the file first, extract the current Mixins block verbatim, and use that as `old_string`.

## Validation plan

| Check | Command | Expected outcome |
|---|---|---|
| Syntax valid | `python -c "import ast; ast.parse(open('scripts/agent/commands/registry.py').read()); print('OK')"` | Prints `OK` |
| Diff scope | `git diff scripts/agent/commands/registry.py` | Changes confined to docstring lines only |
| Row count | Manual count in docstring vs. class base list | 13 == 13 |
| Column alignment | Visual inspection of diff output | All `—` separators on the same column |
| Ruff passes | `uv run ruff check scripts/agent/commands/registry.py` | Exit 0, no errors |
| Mypy passes | `uv run mypy scripts/agent/commands/registry.py` | Exit 0, no errors |
| Tests pass | `uv run pytest` | All existing tests green |
