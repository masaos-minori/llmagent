# Implementation Procedure: config/agent.toml — add missing file_read tool_definitions and tool_names

Source plan: `plans/20260711-204820_plan.md` — Phase 2 (Core Logic Implementation)

## Goal

Resolve the File Read MCP server's tool-definition mismatch and routing drift by adding the 4 missing `[[tool_definitions]]` blocks (`list_directory_with_sizes`, `read_media_file`, `read_multiple_files`, `get_file_info`) and updating `[mcp_servers.file_read].tool_names` from 5 to all 9 tools in `config/agent.toml`.

## Scope

**In:**
- `config/agent.toml` (~line 509 area): add 4 new `[[tool_definitions]]` blocks for the missing tools.
- `config/agent.toml:338`: update `[mcp_servers.file_read].tool_names` to list all 9 tools.

**Out:**
- No MCP server code or endpoint function changes — `scripts/mcp_servers/file/read_tools.py` already implements all 9 tools; this is purely a config-side gap.
- No enabling of `tool_definitions_strict = true` or `routing_drift_strict = true` — both are long-term improvements, not part of this fix.
- No auto-generation tooling for tool definitions — long-term improvement, out of scope.

## Assumptions

1. The 4 missing tools are confirmed to exist on the running File Read server via `scripts/mcp_servers/file/read_tools.py` (plan Assumption 1) — this is a config-catch-up fix, not new server functionality.
2. `shared/tool_constants.py`'s `READ_TOOLS` frozenset already includes all 9 tools, and `ToolRegistry` auto-populates from this frozenset at import time (plan's Blast Radius note) — the registry side is already correct; only the LLM-facing config side (`[[tool_definitions]]` blocks and `tool_names`) is incomplete. No changes needed to `tool_constants.py`, `tool_routing_validation.py`, or `tool_registry.py`.
3. Existing `[[tool_definitions]]` blocks for the other 5 file_read tools follow a consistent, replicable pattern (plan Assumption 2) — the new blocks should match that same structure (name, description, parameter schema fields) rather than inventing a new format.
4. Japanese descriptions are used consistently across existing tool definitions (plan Assumption 3) — the 4 new definitions' description text should match this existing convention, not switch to English.
5. Per the plan's UNK-02 (non-blocking): the exact parameter schema for each missing tool should be verified against the actual MCP server's `/v1/tools` response before finalizing the new `[[tool_definitions]]` blocks, rather than guessed from the tool's Python signature alone — this is a verification step to perform during implementation, not a blocker for writing this procedure document.
6. Per the plan's UNK-01 (non-blocking, resolved): `/opt/llm/config/agent.toml` and this repository's `config/agent.toml` are separate, non-git-linked files requiring independent application of this same change and independent deploys.

## Implementation

### Target file

`config/agent.toml`

### Procedure

1. Query the running File Read MCP server's `/v1/tools` endpoint (`curl http://127.0.0.1:8005/v1/tools`) to obtain the authoritative parameter schema (types, required fields, descriptions if any) for each of the 4 missing tools — do not guess schemas from source code alone (per Assumption 5/UNK-02).
2. Locate the existing `[[tool_definitions]]` blocks for the other 5 `file_read` tools (around line 509) to confirm the exact structural pattern (field names, TOML array-of-tables syntax, description language) used today.
3. Add 4 new `[[tool_definitions]]` blocks, one each for `list_directory_with_sizes`, `read_media_file`, `read_multiple_files`, `get_file_info`, immediately after the last existing `file_read` tool definition — matching the confirmed pattern from step 2, with parameter schemas from step 1, and Japanese descriptions consistent with the existing 5 blocks (per Assumption 4).
4. Locate `[mcp_servers.file_read].tool_names` (line 338) and update it from its current 5-item list to include all 9 tool names (the existing 5 plus the 4 newly-defined ones), in a consistent order (e.g. matching `READ_TOOLS`'s frozenset members, or alphabetical — match whatever ordering convention the existing list already uses).
5. Do not modify any other `[mcp_servers.*]` section or unrelated `[[tool_definitions]]` blocks for other servers.

### Method

Four additive TOML array-of-tables entries (`[[tool_definitions]]`) plus one list-value update (`tool_names`), both within the same file. No schema/structural change to the TOML format itself — only new instances of an existing pattern.

### Details

- Apply this change identically to both `/opt/llm/config/agent.toml` (production) and this repository's `config/agent.toml` (development/source), per Assumption 6 — two independent edits, two independent deploys via the standard `deploy/deploy.sh` workflow.
- Keep parameter-schema field names and types byte-consistent with what `/v1/tools` actually reports (step 1) — a mismatch here would reintroduce the same class of drift this fix is meant to close, just for different tools.
- Verify the final tool count is exactly 9 for `file_read`, matching `READ_TOOLS`'s frozenset size and this repo's already-passing `tests/test_tool_registry_counts.py` expectations (cross-reference: a sibling, already-processed plan's implementation doc `20260711-165948_tool_registry_get_tool_names_sorted_order.md` establishes `file_read=9` as the confirmed, stable count — this config fix should make `agent.toml`'s `tool_names` list agree with that same count, not introduce a new, different one).

## Validation plan

Filtered from the plan's Validation Plan table to checks relevant to this file:

| Check | Tool | Target |
|---|---|---|
| Config validation | `cd /opt/llm && uv run python scripts/agent/startup.py --validate-config` | No tool definition mismatches |
| Tool count | `curl http://127.0.0.1:8005/v1/tools \| jq '.tools \| length'` | Returns `9` |
| Routing drift | `/mcp status` in agent REPL | No drift warnings for `file_read` |
| Tool discovery | `curl http://127.0.0.1:8005/v1/tools \| jq '.tools[].name'` | All 9 tool names listed, matching the new `tool_names` config value |
