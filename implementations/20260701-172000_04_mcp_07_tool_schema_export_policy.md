# Implementation: Update docs/04_mcp_07_tool_schema_export_policy.md to reflect completed migration

## Goal

Rewrite the document from "migration plan" framing to "current policy" framing now that
all MCP servers have been migrated from `_MCP_TOOLS` to `TOOL_LIST`.

## Scope

- Target file: docs/04_mcp_07_tool_schema_export_policy.md
- Content update only; no new sections are added beyond what the plan specifies.

## Assumptions

- Steps 1-4 (tools.py, server.py, test files, check_no_compat.py) are complete before
  this documentation step.
- The document currently (confirmed by grep) still contains a "migration plan" section
  listing servers that need to migrate (line 15: "The following MCP servers need to migrate").
- After migration, that section should be replaced with a "completed" or "current state"
  statement.
- Wording should be declarative present tense, not future tense.

## Implementation

### Target file: docs/04_mcp_07_tool_schema_export_policy.md

#### Procedure

1. Read the full document to understand its current structure.
2. Identify sections with migration-plan framing:
   - Section starting at line 15: "The following MCP servers need to migrate from `_MCP_TOOLS` to `TOOL_LIST`"
   - Any "TODO", "will be", "needs to", "planned" language.
3. Replace migration-plan wording with current-state wording:
   - Remove the list of "servers that need to migrate".
   - Add a statement confirming all servers now export `TOOL_LIST`.
   - Change "need to migrate" → "must export" (policy enforcement going forward).
4. Update the migration step checklist (lines 26-29) from future instructions to a
   confirmed-complete note or remove entirely.
5. Ensure the document accurately describes the post-migration invariants:
   - All `mcp/<name>/tools.py` export `TOOL_LIST`.
   - `_MCP_TOOLS` is banned by `check_no_compat.py`.
   - `mcp/github/tools.py` was the reference implementation.

#### Method

Read the full document first, then make targeted edits to sections identified above.
Do not restructure the document beyond what is necessary to remove migration-plan framing.

#### Details

Wording changes (examples):
- `"need to migrate from _MCP_TOOLS to TOOL_LIST"` → `"export TOOL_LIST (migration complete as of 2026-07-01)"`
- `"The following MCP servers need to migrate:"` → `"All MCP servers now export TOOL_LIST:"`
- Migration step list (steps 1-4 in doc) → Convert to a "how to add a new server" guide or remove.

Do not delete the rationale section (lines 9-11: why TOOL_LIST over _MCP_TOOLS); it
remains useful as policy documentation.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Doc consistency check | `pre-commit run check-rag-docs` (or equivalent) | Pass |
| Grep for stale wording | `grep -n "need to migrate\|_MCP_TOOLS" docs/04_mcp_07_tool_schema_export_policy.md` | Zero matches |
| Lint | `pre-commit run --files docs/04_mcp_07_tool_schema_export_policy.md` | Pass |
