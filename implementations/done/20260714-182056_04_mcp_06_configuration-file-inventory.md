# Implementation Procedure: Clarify Responsibility Boundary Between Agent and MCP Server Config (Configuration File Inventory)

## Goal

Clarify the configuration file inventory to show the two-layer ownership model and list agent.toml fields separately from server-local config fields.

## Scope

- `docs/04_mcp_06_configuration-file-inventory.md` only
- Text rewrite and reorganization; no new content creation beyond what's needed to replace obsolete descriptions

## Assumptions

1. The requirement `requires/20260714_04_require.md` is the canonical specification for this task.
2. The inventory currently implies a single-file config model that needs correction.
3. No source code changes are required — documentation updates only.

## Implementation

### Target file

`docs/04_mcp_06_configuration-file-inventory.md`

### Procedure

1. **Scan for single-file model implications**: Search for patterns suggesting all config lives in one place.
2. **Reorganize under two-layer model**: Restructure the inventory to clearly separate agent-side and server-local config.
3. **List fields separately**: Document agent.toml fields and server-local config fields as distinct categories.

### Method

- Pattern-based search followed by section restructuring via file edit.
- Preserve surrounding context and formatting.

### Details

- Restructure the inventory into two clear sections:
  1. Agent Process Configuration (`config/agent.toml`)
     - List the five confirmed agent-side fields
  2. MCP Server-Local Application Configuration (`config/*_mcp_server.toml`)
     - List common server-local config types (allowlists, denylists, resource limits, etc.)
     - Note per-server variations (allowed_repos, command_allowlist, allowed_dirs)
- Remove any text implying a single-file config model.

## Validation plan

1. Verify the inventory clearly separates the two config layers.
2. Confirm all five agent-side fields are listed accurately.
3. Verify no implication that MCP servers can read `agent.toml`.
4. Verify no broken cross-references from restructured sections.
5. Run `pre-commit run --all-files` if markdown linting is configured.
