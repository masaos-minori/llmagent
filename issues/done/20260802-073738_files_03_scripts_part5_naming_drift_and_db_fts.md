# Fix service-name-prefix drift in docs/01_overview-files-03-scripts-part5.md and resolve db_fts.py's fate

## Priority
High

## Summary
`docs/01_overview-files-03-scripts-part5.md` (~lines 27-82) documents shell/rag_pipeline/cicd/mdq/git MCP servers using generic filenames (`server.py`/`service.py`/`tools.py`/`models.py`), but actual files carry a service-name prefix (`shell_server.py`, `cicd_server.py`, `mdq_server.py`, `git_server.py`, `rag_pipeline_server.py`, etc.). Additionally, `db_fts.py` is documented but does not exist in current source (only a `.pyc` remnant remains in `__pycache__`).

## Reason for Change
The naming pattern itself has drifted from documented convention to actual convention across 5 server subdirectories — a confirmed, high-impact mismatch. `db_fts.py`'s absence without a documented successor leaves a functional gap in understanding (FTS functionality's current location is unknown to readers).

## Implementation Intent
Remove the manually-maintained directory tree; replace with a design-intent summary of the naming convention (service-prefixed files) and a pointer to the implementation tree. Separately, determine where FTS functionality now lives (or confirm it was removed) and document that instead of the nonexistent file.

## Target Files or Areas
`docs/01_overview-files-03-scripts-part5.md`

## Required Changes
- Remove the directory tree enumeration (~lines 27-82) for shell/rag_pipeline/cicd/mdq/git.
- Replace with prose describing the service-prefixed naming convention and a pointer to `scripts/mcp_servers/{shell,rag_pipeline,cicd,mdq,git}/` for the current file list.
- Investigate whether `db_fts.py`'s functionality was merged into `db_grep.py`, `db_schema.py`, or removed entirely; document the actual current location/status instead of the nonexistent file.
- Note that MCP server port-to-name mapping should be consolidated into `docs/01_overview-files-05-config.md` (tracked in a separate issue) rather than repeated here.

## Acceptance Criteria
The file no longer documents a generic naming pattern that contradicts actual service-prefixed filenames; `db_fts.py` is either correctly attributed to its successor or explicitly noted as removed with no successor.

## Testing Expectations
Not required (documentation-only). Manually verify via `ls scripts/mcp_servers/{shell,rag_pipeline,cicd,mdq,git}/` and `grep -r "db_fts\|db_grep\|db_schema" scripts/mcp_servers/mdq/` before finalizing.

## Documentation Impact
`docs/01_overview-files-03-scripts-part5.md` rewritten.

## Out of Scope
Do not implement or move any FTS-related code in this issue — documentation only. Do not consolidate port information into files-05-config.md in this issue (tracked separately).

## AI Implementation Instruction
Resolve the `db_fts.py` question via actual source/git investigation before writing the replacement text — do not guess at a successor file.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_overview_architecture.md §2 削除候補 item 3, §6A (files-03-scripts-part5.md db_fts.py)
- Generated at: 2026-08-02
