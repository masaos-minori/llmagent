# Implementation Procedure: Remove Obsolete web_search_url from Agent Configuration (config/agent.toml)

## Goal

Remove `web_search_url` from `config/agent.toml` and establish `mcp_servers.web_search.url` as the authoritative web search endpoint.

## Scope

- `config/agent.toml` only
- Single-line removal; no new content creation

## Assumptions

1. The requirement `requires/20260714_06_require.md` is the canonical specification for this task.
2. `web_search_url` exists in `config/agent.toml` as an obsolete key.
3. Option A (reject as forbidden key) is preferred over Option B (migration warning).
4. No source code changes are required — config update only.

## Implementation

### Target file

`config/agent.toml`

### Procedure

1. **Scan all code for `web_search_url` references**: Run grep across project for `web_search_url` to identify all references before making changes.
2. **Remove `web_search_url` from `config/agent.toml`**: Locate and delete the `web_search_url` line.

### Method

- Pattern-based search followed by targeted text deletion via file edit.

### Details

- Search for `web_search_url` pattern in `config/agent.toml`
- Delete the entire line containing `web_search_url`
- Preserve surrounding context and formatting

## Validation plan

1. Verify `web_search_url` no longer appears in `config/agent.toml`.
2. Confirm no other config files contain `web_search_url`.
3. Verify no broken cross-references from removed section.
4. Run `pre-commit run --all-files` if linting is configured.
