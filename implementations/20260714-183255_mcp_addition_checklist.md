# Implementation Procedure: Consolidate MCP Configuration Ownership and Secret-Based Authentication Model (MCP Server Addition Checklist)

## Goal

Update new MCP server addition checklist to use secret-based auth, replace stale references, clarify `tool_names` is not a routing input, and replace `routing.md` references.

## Scope

- `docs/04_mcp_06_new-mcp-server-addition-checklist.md` only
- Text updates and clarifications; no new content creation beyond what's needed to replace obsolete descriptions

## Assumptions

1. The requirement `requires/20260714_08_require.md` is the canonical specification for this task.
2. The document currently contains raw `auth_token` examples, stale file references, and incorrect `tool_names` descriptions.
3. No source code changes are required — documentation updates only.

## Implementation

### Target file

`docs/04_mcp_06_new-mcp-server-addition-checklist.md`

### Procedure

1. **Replace raw `auth_token`**: Substitute all raw `auth_token` examples with secret-based patterns.
2. **Replace stale file references**: Replace `config/tools_definitions.toml` → `config/agent.toml::tool_definitions`.
3. **Clarify `tool_names`**: Document `tool_names` only as optional startup drift validation metadata, not a routing input.
4. **Replace `routing.md` references**: Replace with `04_mcp_03_routing_lifecycle_and_execution.md`.

### Method

- Pattern-based search followed by targeted text replacement via file edit.
- Preserve surrounding context and formatting.

### Details

For each update type:
- Raw `auth_token` → `auth_token_env` / `auth_token_file`
- `config/tools_definitions.toml` → `config/agent.toml::tool_definitions`
- `tool_names` as routing input → `tool_names` as optional drift validation metadata
- `routing.md` → `04_mcp_03_routing_lifecycle_and_execution.md`

## Validation plan

1. Verify no raw `auth_token` examples remain.
2. Confirm no references to `config/tools_definitions.toml`.
3. Verify `tool_names` is documented correctly as drift validation metadata only.
4. Confirm no references to `routing.md`.
5. Verify no broken cross-references from updated sections.
6. Run `pre-commit run --all-files` if linting is configured.
