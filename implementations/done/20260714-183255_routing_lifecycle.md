# Implementation Procedure: Consolidate MCP Configuration Ownership and Secret-Based Authentication Model (Routing/Lifecycle Documentation)

## Goal

Rewrite the MCP routing/lifecycle documentation to distinguish agent-side vs server-local configuration and replace stale references.

## Scope

- `docs/04_mcp_03_routing_lifecycle_and_execution.md` only
- Text rewrite and clarification; no new content creation beyond what's needed to replace obsolete descriptions

## Assumptions

1. The requirement `requires/20260714_08_require.md` is the canonical specification for this task.
2. The document currently conflates agent-side and server-local config without clear separation.
3. No source code changes are required — documentation updates only.

## Implementation

### Target file

`docs/04_mcp_03_routing_lifecycle_and_execution.md`

### Procedure

1. **Locate lifecycle sections**: Find sections describing MCP server startup, shutdown, and lifecycle management.
2. **Distinguish config layers**: Rewrite to clearly separate agent-side lifecycle/transport config from server-local application config.
3. **Replace stale references**: Replace `routing.md` references with `04_mcp_03_routing_lifecycle_and_execution.md`.

### Method

- Section-by-section text replacement via file edit.
- Preserve surrounding context and formatting.

### Details

- Rewrite lifecycle section to specify which config layer controls which aspect:
  - Agent.toml controls: startup_mode, transport, url, healthcheck_mode, cmd
  - *_mcp_server.toml controls: allowlists, denylists, resource limits, audit paths, etc.
- Replace any `routing.md` references with `04_mcp_03_routing_lifecycle_and_execution.md`
- Ensure consistency with the two-layer model introduced in other documents.

## Validation plan

1. Verify the rewritten lifecycle section clearly distinguishes the two config layers.
2. Confirm no references to `routing.md` remain.
3. Verify no implication that MCP servers can read `agent.toml`.
4. Verify no broken cross-references from removed sections.
5. Run `pre-commit run --all-files` if markdown linting is configured.
