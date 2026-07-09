# Implementation: docs — update 04_mcp_06_configuration_and_operations.md for unified layout

## Goal

Fix any references to split config ownership in `04_mcp_06_configuration_and_operations.md`.

## Scope

- `docs/04_mcp_06_configuration_and_operations.md`

## Assumptions

1. This doc may reference split config files (common.toml, etc.) from before the unification.
2. Phase 1 verification is complete.

## Implementation

### Target file

`docs/04_mcp_06_configuration_and_operations.md`

### Procedure

1. Search for stale references to split config file names (common.toml, llm.toml, tools.toml, memory.toml, etc.).
2. Replace with accurate `agent.toml` references or remove.
3. Clarify per-server MCP config ownership.

### Details

- Use `rg "common\.toml\|llm\.toml\|tools\.toml\|memory\.toml\|otel\.toml\|security\.toml" docs/04_mcp_06_configuration_and_operations.md` to find stale references.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| No stale split-file references | `rg "common\.toml\|llm\.toml\|tools\.toml" docs/04_mcp_06_configuration_and_operations.md` | 0 matches |
