# Implementation Procedure: Consolidate MCP Configuration Ownership and Secret-Based Authentication Model (Configuration File Inventory)

## Goal

Update configuration file inventory to add explicit two-layer ownership section, document `tool_definitions` as canonical location, document `security_profile` as agent-wide setting, and list server-local config fields separately.

## Scope

- `docs/04_mcp_06_configuration-file-inventory.md` only
- Text rewrite and reorganization; no new content creation beyond what's needed to replace obsolete descriptions

## Assumptions

1. The requirement `requires/20260714_08_require.md` is the canonical specification for this task.
2. The inventory currently implies a single-file config model that needs correction.
3. No source code changes are required — documentation updates only.

## Implementation

### Target file

`docs/04_mcp_06_configuration-file-inventory.md`

### Procedure

1. **Add two-layer ownership section**: Restructure inventory into clear Layer 1 (agent.toml) and Layer 2 (server-local) sections.
2. **Document `tool_definitions`**: Point to `config/agent.toml::tool_definitions` as canonical.
3. **Document `security_profile`**: Document as agent-wide setting in `agent.toml`.
4. **List server-local config fields**: Separate server-local config fields from agent-side fields.

### Method

- Section-by-section text replacement via file edit.
- Preserve surrounding context and formatting.

### Details

Restructure into two clear sections:
1. Agent Process Configuration (`config/agent.toml`)
   - List the five confirmed agent-side fields
   - Document `tool_definitions` as canonical location
   - Document `security_profile` as agent-wide setting
2. MCP Server-Local Application Configuration (`config/*_mcp_server.toml`)
   - List common server-local config types (allowlists, denylists, resource limits, etc.)
   - Note per-server variations (allowed_repos, command_allowlist, allowed_dirs)
   - Document secret references (`auth_token_env`, `auth_token_file`)

## Validation plan

1. Verify the inventory clearly separates the two config layers.
2. Confirm all five agent-side fields are listed accurately.
3. Verify `tool_definitions` and `security_profile` are properly documented.
4. Verify no implication that MCP servers can read `agent.toml`.
5. Verify no broken cross-references from restructured sections.
6. Run `pre-commit run --all-files` if linting is configured.
