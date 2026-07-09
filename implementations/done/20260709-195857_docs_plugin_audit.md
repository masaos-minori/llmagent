# Implementation: docs — plugin audit and observability documentation

## Goal

Document plugin vs MCP audit event distinction, plugin observability limitations, and how to interpret plugin audit events.

## Scope

- `docs/05_agent_10_operations-and-observability.md`
- `docs/05_agent_11_extension-points.md`

## Assumptions

1. Both doc files exist with sections on audit and plugins.
2. Phase 2 implementation (source field standardization) is complete.

## Implementation

### Target files

1. `docs/05_agent_10_operations-and-observability.md`
2. `docs/05_agent_11_extension-points.md`

### Procedure

1. In `docs/05_agent_10_operations-and-observability.md`: add section noting that plugin tool audit events have `source="plugin"`, `server_key=""`, `request_id=""`.
2. In `docs/05_agent_11_extension-points.md`: document the observability limitations for plugin tools (no MCP request_id, no server_key).

### Details

- Cross-reference between the two docs for completeness.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Plugin audit documented | `rg "source.*plugin" docs/` | 2+ matches |
