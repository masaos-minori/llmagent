# Implementation Procedure: Consolidate MCP Configuration Ownership and Secret-Based Authentication Model (Startup Validation Behavior)

## Goal

Update startup validation behavior documentation to validate resolved secrets at startup and replace stale references.

## Scope

- `docs/04_mcp_06_startup-validation-behavior-tool_definitions_strict.md` only
- Text updates and clarifications; no new content creation beyond what's needed to replace obsolete descriptions

## Assumptions

1. The requirement `requires/20260714_08_require.md` is the canonical specification for this task.
2. The document currently validates plain config values rather than resolved secrets.
3. No source code changes are required — documentation updates only.

## Implementation

### Target file

`docs/04_mcp_06_startup-validation-behavior-tool_definitions_strict.md`

### Procedure

1. **Update validation description**: Change to describe validating resolved secrets at startup.
2. **Replace stale file references**: Replace `config/tools_definitions.toml` → `config/agent.toml::tool_definitions`.

### Method

- Pattern-based search followed by targeted text replacement via file edit.
- Preserve surrounding context and formatting.

### Details

For each update type:
- Plain config value validation → Resolved secret validation
- `config/tools_definitions.toml` → `config/agent.toml::tool_definitions`

## Validation plan

1. Verify validation steps check resolved secrets, not plain config values.
2. Confirm no references to `config/tools_definitions.toml`.
3. Verify no broken cross-references from updated sections.
4. Run `pre-commit run --all-files` if linting is configured.
