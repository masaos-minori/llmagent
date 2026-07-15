# Implementation Procedure: Clarify Responsibility Boundary Between Agent and MCP Server Config (Routing Lifecycle)

## Goal

Rewrite the MCP routing/lifecycle documentation to distinguish agent-side vs server-local configuration and document that lifecycle/transport changes require full agent restart.

## Scope

- `docs/04_mcp_03_routing_lifecycle_and_execution.md` only
- Text rewrite and clarification; no new content creation beyond what's needed to replace obsolete descriptions

## Assumptions

1. The requirement `requires/20260714_04_require.md` is the canonical specification for this task.
2. Agent-side MCP fields in `agent.toml`: `startup_mode`, `transport`, `url`, `healthcheck_mode`, `cmd`.
3. MCP servers read only their own `*_mcp_server.toml` files.
4. Lifecycle/transport changes require full agent restart.
5. No source code changes are required — documentation updates only.

## Implementation

### Target file

`docs/04_mcp_03_routing_lifecycle_and_execution.md`

### Procedure

1. **Locate lifecycle sections**: Find sections describing MCP server startup, shutdown, and lifecycle management.
2. **Distinguish config layers**: Rewrite to clearly separate agent-side lifecycle/transport config from server-local application config.
3. **Document restart requirement**: Explicitly state that lifecycle/transport changes require full agent restart.

### Method

- Section-by-section text replacement via file edit.
- Preserve surrounding context and formatting.

### Details

- Rewrite lifecycle section to specify which config layer controls which aspect:
  - Agent.toml controls: startup_mode, transport, url, healthcheck_mode, cmd
  - *_mcp_server.toml controls: allowlists, denylists, resource limits, audit paths, etc.
- Add explicit statement: "Changes to lifecycle/transport settings in `agent.toml` require a full agent restart. Changes to server-local application config in `*_mcp_server.toml` can be applied via `/reload`."
- Ensure consistency with the two-layer model introduced in other documents.

## Validation plan

1. Verify the rewritten lifecycle section clearly distinguishes the two config layers.
2. Confirm the restart requirement is explicitly documented.
3. Verify no implication that MCP servers can read `agent.toml`.
4. Verify no broken cross-references from removed sections.
5. Run `pre-commit run --all-files` if markdown linting is configured.
