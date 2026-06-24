# Implementation: Align tool_definitions_strict in Agent Docs

## Goal

Update `05_agent_08` `tool_definitions_strict` entry with canonical behavior from MCP plan 16 and add a cross-reference to `04_mcp_06`.

## Scope

**In:**
- `docs/05_agent_08_configuration_and_settings.md` — update `tool_definitions_strict` description

**Out:** No code changes.

## Assumptions

1. MCP plan 16 established `04_mcp_06` §Startup Validation Behavior as canonical source.
2. `tool_definitions_strict = true` (default): fatal on schema mismatch at startup.
3. `strict_startup_validation = false` downgrades to WARNING.

## Implementation

### Target file

`docs/05_agent_08_configuration_and_settings.md`

### Procedure

1. Read `docs/05_agent_08_configuration_and_settings.md` to find the `tool_definitions_strict` entry.
2. Update the entry with canonical wording and cross-reference.

### Method

Read then Edit tool patch.

### Details

**Updated `tool_definitions_strict` config entry:**

```markdown
#### `tool_definitions_strict`

**Default:** `true`

Controls startup validation of MCP tool definitions.

| Value | Behavior |
|---|---|
| `true` (default) | Schema mismatch → FATAL, agent exits |
| `false` | Schema mismatch → WARNING, agent starts |

To override fatal behavior: set `strict_startup_validation = false` in agent config.

For full startup validation behavior (all 4 cases), see `04_mcp_06` §Startup Validation Behavior.
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Cross-reference added | `grep -n "04_mcp_06\|strict_startup_validation" docs/05_agent_08_configuration_and_settings.md` | found |
| No code changes | `git diff agent/` | empty |
