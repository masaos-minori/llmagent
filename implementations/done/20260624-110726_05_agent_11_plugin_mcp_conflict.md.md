# Implementation: Document Strict Plugin MCP-Conflict Rejection

## Goal

Document the behavior when a plugin registers a tool that conflicts with a built-in MCP tool. Add conflict rejection section to `05_agent_11` and SPEC entry to `05_agent_90`.

## Scope

**In:**
- `docs/05_agent_11_plugin_and_extension_system.md` — add conflict rejection section
- `docs/05_agent_90_specifications_and_design_contracts.md` — add SPEC-PLUGIN-01

**Out:** No code changes.

## Assumptions

1. Plugin tool name conflict with built-in MCP tool → startup error (fatal if `tool_definitions_strict = true`).
2. Error message includes both the conflicting plugin name and the MCP tool name.
3. `strict_startup_validation = false` downgrades to WARNING, built-in MCP tool takes precedence.

## Implementation

### Target file

`docs/05_agent_11_plugin_and_extension_system.md`, `docs/05_agent_90_specifications_and_design_contracts.md`

### Procedure

1. Grep plugin registry for conflict handling:
   ```bash
   grep -rn "conflict\|duplicate.*tool\|tool.*already.*registered" agent/ --include="*.py" | head -10
   ```
2. Read `docs/05_agent_11_plugin_and_extension_system.md` plugin registration section.
3. Add conflict rejection section.
4. Read `docs/05_agent_90_specifications_and_design_contracts.md` and add SPEC entry.

### Method

Bash grep → Read docs → Edit patches.

### Details

**Conflict rejection section for `05_agent_11`:**

```markdown
## Plugin/MCP Tool Conflict Rejection

If a plugin attempts to register a tool name already registered by a built-in MCP server:

**With `tool_definitions_strict = true` (default):**
```
PluginConflictError: Plugin '{plugin_name}' tool '{tool_name}' conflicts with built-in MCP tool.
Agent startup failed.
```

**With `strict_startup_validation = false`:**
```
WARNING: Plugin '{plugin_name}' tool '{tool_name}' skipped — conflicts with built-in MCP tool.
```
Built-in MCP tool takes precedence. Plugin tool registration is silently skipped.

> **Best practice:** Use unique namespaced tool names for plugins (e.g., `my_plugin__search` instead of `search`).
```

**SPEC-PLUGIN-01 for `05_agent_90`:**

```markdown
### SPEC-PLUGIN-01: Plugin/MCP Tool Name Conflict Policy
**Status:** Implemented
Plugin tool names that conflict with built-in MCP tools are rejected at startup.
With `tool_definitions_strict = true` (default): fatal error.
With `strict_startup_validation = false`: WARNING, built-in tool takes precedence.
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Conflict rejection section | `grep -n "Conflict Rejection\|PluginConflictError" docs/05_agent_11_plugin_and_extension_system.md` | found |
| SPEC entry | `grep -n "SPEC-PLUGIN-01" docs/05_agent_90_specifications_and_design_contracts.md` | found |
| No code changes | `git diff agent/` | empty |
