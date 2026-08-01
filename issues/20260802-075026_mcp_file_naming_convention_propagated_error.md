# Fix bare-name vs prefixed-name file convention error propagated across docs/04_mcp_06_14, 06_15, and 07

## Priority
High

## Summary
`docs/04_mcp_06_14`, `docs/04_mcp_06_15`, and `docs/04_mcp_07_tool_schema_export_policy.md` describe MCP server implementation files using bare names (`server.py`, `tools.py`), but the actual, confirmed convention is `<name>_server.py` / `<name>_tools.py`. The 07 file is internally self-contradictory: lines ~41-43 state the bare-name convention is historical/outdated, yet the rest of the file's body still uses bare names.

## Reason for Change
This is a confirmed factual error (verified against implementation), propagated across 3 files, with one file actively contradicting itself. A developer following this document when adding a new MCP server would create incorrectly-named files.

## Implementation Intent
Rewrite all 3 files to consistently use the `<name>_server.py` / `<name>_tools.py` convention, resolving the self-contradiction in 07 by removing the stale bare-name text entirely rather than leaving both versions present.

## Target Files or Areas
`docs/04_mcp_06_14`, `docs/04_mcp_06_15`, `docs/04_mcp_07_tool_schema_export_policy.md`

## Required Changes
- Replace all bare-name (`server.py`/`tools.py`) references with the prefixed convention (`<name>_server.py`/`<name>_tools.py`) across all 3 files.
- In `04_mcp_07`, remove the outdated bare-name text entirely (not just note that it's historical) so the file no longer contradicts its own lines ~41-43.

## Acceptance Criteria
No file in this set references bare `server.py`/`tools.py` as the current convention; `04_mcp_07` has no remaining self-contradiction between its historical note and its body text.

## Testing Expectations
Not required (documentation-only). Manually verify the current naming convention via `ls scripts/mcp_servers/*/` before finalizing.

## Documentation Impact
All 3 files corrected for consistency.

## Out of Scope
Do not change actual MCP server source file names in this issue — documentation only.

## AI Implementation Instruction
This is a confirmed factual error — apply directly. When editing `04_mcp_07`, read the full file first to ensure every bare-name reference is caught, not just the ones near the already-noted historical caveat.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_mcp.md §1 (全体評価 item 3), §5 例3, §6A (ファイル命名規則)
- Generated at: 2026-08-02
