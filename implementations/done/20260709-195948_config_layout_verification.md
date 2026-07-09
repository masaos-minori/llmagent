# Implementation: config docs — config layout verification

## Goal

Confirm the current config layout: verify `agent.toml` contents (whether it has `[mcp_servers.*]` sections), and trace how per-server MCP configs are loaded relative to `load_all()`.

## Scope

- `scripts/shared/config_loader.py` — read-only verification
- `config/agent.toml` — read-only verification
- `scripts/agent/config_builders.py` — read-only verification

## Assumptions

1. `load_all()` only loads `agent.toml` (confirmed by prior knowledge).
2. Per-server configs are loaded separately by each MCP server's `load()` method.

## Implementation

### Target files

1. `scripts/shared/config_loader.py`
2. `config/agent.toml`
3. `scripts/agent/config_builders.py`

### Procedure

1. Read `config_loader.py` to confirm `_BASE_CONFIG_FILES = ("agent.toml",)` and no other split files are loaded.
2. Read `agent.toml` to check for `[mcp_servers.*]` sections.
3. Trace how per-server MCP configs are loaded (e.g., `github_mcp_server.toml`).
4. Document findings for use in Phase 2 doc updates.

### Details

- Read-only; no source modifications.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Verification complete | Manual review | Findings documented |
