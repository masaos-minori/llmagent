# Fix web_search/github file-naming drift in docs/01_overview-files-03-scripts-part4.md (confirmed nonexistent filenames)

## Priority
High

## Summary
`docs/01_overview-files-03-scripts-part4.md` (~lines 36-42 for web_search, ~lines 63-93 for github) documents generic filenames (`server.py`, `tools.py`, `models.py`) that do not exist in current source — the actual files are service-prefixed (`web_search_server.py`, `web_search_tools.py`, `web_search_models.py`, `web_search_service.py`), and `web_search_service.py`, `health.py`, `metrics.py` are entirely missing from the document. The github section has an analogous unreflected rename (`server.py` → `github_server.py`, etc., across 3 files).

## Reason for Change
This is a confirmed rename that was never reflected in the documentation, not speculative staleness. It misleads anyone searching by the documented filenames.

## Implementation Intent
Remove the manually-maintained file listing for both web_search and github, replacing it with a design-intent summary of the shared foundation (`models.py`, `dispatch.py`, `tool_validators.py`) that each service builds on, and a pointer to the implementation tree for the current, complete file list.

## Target Files or Areas
`docs/01_overview-files-03-scripts-part4.md`

## Required Changes
- Remove the web_search file listing (~lines 36-42) and the github file listing (~lines 63-93).
- Replace with prose describing the shared-foundation pattern: each MCP server subdirectory builds service-prefixed implementation files (e.g. `web_search_server.py`) on top of common `models.py`/`dispatch.py`/`tool_validators.py`.
- Point readers to `scripts/mcp_servers/web_search/` and `scripts/mcp_servers/github/` for the current, authoritative file list.

## Acceptance Criteria
The file no longer lists specific filenames that don't match current source for either web_search or github; the shared-foundation design intent is preserved.

## Testing Expectations
Not required (documentation-only). Manually verify via `ls scripts/mcp_servers/web_search/` and `ls scripts/mcp_servers/github/` that the rewritten text contains no further false claims.

## Documentation Impact
`docs/01_overview-files-03-scripts-part4.md` rewritten for both the web_search and github sections.

## Out of Scope
Do not investigate other MCP server subdirectories (shell/rag_pipeline/cicd/mdq/git are tracked in a separate issue; other unreviewed directories like `file/` are tracked in the cross-directory audit issue).

## AI Implementation Instruction
Verify the current file list for both subdirectories via `ls`/`grep` before writing replacement text.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_overview_architecture.md §2 削除候補 item 2, §5 例4, §6A (files-03-scripts-part4.md)
- Generated at: 2026-08-02
