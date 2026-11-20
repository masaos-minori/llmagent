# Remove the tool catalog and per-server tool name lists from `agent.toml`

## Priority
Medium

## Summary
Make live MCP discovery the source of tool schema, description, capabilities, and server ownership, and move the static ownership and required-capability checks out of `agent.toml` into a machine-readable registry.

## Background
Source: consolidated `agent.toml` reduction backlog (`memo-issue.md`, Issue 2).

Evidence (`Explicit in code`, by reading and `rg`): `scripts/agent/tool_preparation.py` states that it has no `ctx.cfg.tool.tool_definitions` fallback; `scripts/agent/services/tool_validation.py` (lines 106-186) compares `tool_definitions` with live server tool lists, and its warning text names `tools_definitions.toml`, a file that does not exist (the field is read from `agent.toml`); `McpServerConfig.tool_names` is defined and validated in `scripts/shared/mcp_config.py` (lines 70 and 171-179); `config/agent.toml` holds 63 `[[tool_definitions]]` blocks and 10 `tool_names` lines. The claims of a double `/v1/tools` fetch during discovery and of the required-server check using `tool_names` are from the backlog and `Needs confirmation`.

Priority note: the backlog rated this High; by `workflow.md` Phase 7 the evidence supports maintainability and drift risk (Medium). It blocks `issues/20261120-114211_agentcfg003_runtime-tool-metadata.md`, which is ordered by Dependencies, not Priority.

## Problem
Tool names, descriptions, input schemas, and server ownership are kept in several places: the MCP servers, the static registries, `[[tool_definitions]]`, `tool_names`, the RuntimeToolRegistry, and test fixtures. The duplication produces schema and ownership drift and is the main reason `agent.toml` is large.

## Reason for Change
Drift between copies can hide a missing or reassigned tool, and the wrong file name in the warning misleads an operator. It also blocks the metadata consolidation of `issues/20261120-114211_agentcfg003_runtime-tool-metadata.md`.

## Implementation Intent
The RuntimeTool built from live `/v1/tools` is the runtime source of description, schema, capabilities, and server key. Static ownership and required-capability expectations move to a machine-readable registry that the drift check reads. The static checks stay fail-closed: duplicate tool names and routing drift remain fatal.

## Target Files or Areas
- `config/agent.toml`
- `scripts/agent/services/tool_validation.py`, `scripts/agent/services/mcp_tool_discovery.py`, `scripts/agent/services/mcp_tool_discovery_fetch.py`, `scripts/agent/services/mcp_tool_discovery_registry.py`
- `scripts/agent/config_dataclasses.py`, `scripts/agent/config_section_builders.py`, `scripts/agent/services/config_field_registry.py`
- `scripts/shared/mcp_config.py`, `scripts/shared/tool_registry.py`, `scripts/shared/tool_routing_validation.py`, `scripts/shared/runtime_tool_registry.py`
- Tests that build tool definitions from TOML fixtures (`Unknown` until located), `tests/agent/test_config_builders.py`

## Required Changes
- Treat live schema, description, capabilities, and server key as the RuntimeTool source.
- Replace the `tool_definitions` comparison with a drift check against the static registry and routing registry.
- Fetch `/v1/tools` once per server during discovery, if the double fetch is confirmed.
- Express a required server's requirement as a required capability or a registry manifest entry instead of a full tool name list.
- Delete `McpServerConfig.tool_names` and `ToolConfig.tool_definitions`, their builders, reload registry entries, and production valid-key entries, and every `[[tool_definitions]]` and `tool_names` entry in `agent.toml`.
- Move test fixtures to a factory independent of TOML.
- Make a static-versus-live server ownership mismatch fatal.
- Remove the `tools_definitions.toml` wording.

## Constraints
- A change to an ADR decision or invariant needs a maintainer approval record in the same change; do not write or simulate that approval.
- Follow the Current-Specification-Only policy: no compatibility reader for the removed fields; a removed key is rejected with a specific message.
- The `アサインees` typo in an `agent.toml` tool description disappears with the tool definitions; do not fix it separately.

## Acceptance Criteria
- [ ] `agent.toml` holds no tool schema, description, or tool inventory.
- [ ] The schema passed to the LLM comes from the RuntimeToolRegistry.
- [ ] A missing required capability is detected at startup.
- [ ] Duplicate tool names and routing drift stay fatal.
- [ ] Discovery contacts each server once.

## Testing Expectations
- Required capability present and missing; static versus live ownership match and mismatch; duplicate tool name; malformed schema version and input schema; production startup without `tool_definitions` and `tool_names`.
- Run ruff, mypy, import-linter, and the affected tests.

## Documentation Impact
Yes. The source of tool metadata, the required-capability model, and the removed configuration keys.

## Out of Scope
- Safety, approval, preview, and resource metadata (`issues/20261120-114211_agentcfg003_runtime-tool-metadata.md`); the exposure policy (`issues/20261120-114209_agentcfg001_tool-policy-mode.md`).

## Dependencies
- Depends on `issues/20261120-114209_agentcfg001_tool-policy-mode.md`. Blocks `issues/20261120-114211_agentcfg003_runtime-tool-metadata.md`.
- Related: `issues/20261119-145306_cliplc008_mcp-health-capability.md` defines required capability semantics and RuntimeTool diagnostics fields; the required-capability model here must use the same schema. `issues/20261119-145311_cliplc013_api-field-cleanup.md` decides the fate of other `McpServerConfig` fields.

## Unresolved Questions
- `不明`: where the machine-readable ownership and capability registry lives and who owns it.
- `不明`: whether `role`, timeouts, rotation, stagger, and `required` of `McpServerConfig` stay in a launch or connection manifest (the MCP lifecycle components decide this).

## AI Implementation Instruction
Confirm the double fetch and the required-server use of `tool_names` before changing them. Keep duplicate-name and drift failures fatal. Stop and report if a consumer of `tool_definitions` outside the Target Files is found.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261120-114210
- **Related target files**: `config/agent.toml`, `scripts/agent/services/tool_validation.py`, `scripts/agent/services/mcp_tool_discovery.py`, `scripts/agent/services/mcp_tool_discovery_fetch.py`, `scripts/agent/services/mcp_tool_discovery_registry.py`, `scripts/agent/config_dataclasses.py`, `scripts/agent/config_section_builders.py`, `scripts/agent/services/config_field_registry.py`, `scripts/shared/mcp_config.py`, `scripts/shared/tool_registry.py`, `scripts/shared/tool_routing_validation.py`, `scripts/shared/runtime_tool_registry.py`, `tests/agent/test_config_builders.py`
