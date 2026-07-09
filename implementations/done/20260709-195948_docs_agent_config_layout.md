# Implementation: docs — update 05_agent_08_configuration.md for unified layout

## Goal

Rewrite the "Configuration Loading" section in `05_agent_08_configuration.md` to describe the unified `agent.toml` layout and clarify config ownership.

## Scope

- `docs/05_agent_08_configuration.md`

## Assumptions

1. Phase 1 verification is complete.
2. `load_all()` only reads `agent.toml`.
3. Per-server MCP transport configs are loaded separately by each MCP server.

## Implementation

### Target file

`docs/05_agent_08_configuration.md`

### Procedure

1. Replace the "Files loaded by load_all()" table with a single-file `agent.toml` description.
2. Clarify that `load_all()` only reads `agent.toml` (not common.toml, llm.toml, etc.).
3. Document that per-server MCP transport configs are loaded separately by each MCP server.
4. Remove or update references to split config files.
5. Note that split file support was removed and `agent.toml` is now the canonical base config.

### Details

- Keep the existing structure; only update the loading section.
- Add a note for historical context if needed.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| No split-file references | `rg "common\.toml\|llm\.toml\|tools\.toml" docs/05_agent_08_configuration.md` | 0 matches |
