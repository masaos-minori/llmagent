# Implementation Procedure: Consolidate MCP Configuration Ownership and Secret-Based Authentication Model (Pre-Production Fail-Open Checklist)

## Goal

Update pre-production fail-open checklist to validate resolved secrets instead of plain config values, replace stale references, and replace `routing.md` references.

## Scope

- `docs/04_mcp_06_pre-production-fail-open-checklist.md` only
- Text updates and clarifications; no new content creation beyond what's needed to replace obsolete descriptions

## Assumptions

1. The requirement `requires/20260714_08_require.md` is the canonical specification for this task.
2. The document currently validates plain config values rather than resolved secrets.
3. No source code changes are required — documentation updates only.

## Implementation

### Target file

`docs/04_mcp_06_pre-production-fail-open-checklist.md`

### Procedure

1. **Update validation steps**: Change to validate resolved secrets instead of plain config values.
2. **Replace stale file references**: Replace `config/tools_definitions.toml` → `config/agent.toml::tool_definitions`.
3. **Replace `routing.md` references**: Replace with `04_mcp_03_routing_lifecycle_and_execution.md`.

### Method

- Pattern-based search followed by targeted text replacement via file edit.
- Preserve surrounding context and formatting.

### Details

For each update type:
- Plain config value validation → Resolved secret validation
- `config/tools_definitions.toml` → `config/agent.toml::tool_definitions`
- `routing.md` → `04_mcp_03_routing_lifecycle_and_execution.md`

## Validation plan

1. Verify validation steps check resolved secrets, not plain config values.
2. Confirm no references to `config/tools_definitions.toml`.
3. Confirm no references to `routing.md`.
4. Verify no broken cross-references from updated sections.
5. Run `pre-commit run --all-files` if linting is configured.
