## Goal
Record the new github-mcp input contract in the server catalog doc (docs row 18): generated schemas, `dry_run` on write tools, and the changed call shapes.
## Scope
**Release unit**: N/A: not part of a release unit
- Modifies only `docs/22_mcp/mcp_04_01_web-search-file-read-github.md` (Plan Phase 8 doc hand-off).
## Assumptions
- Lands with Phase 8 (after seq 03-13); docs content policy applies (point at the request models).
## Design decisions
- "Input contract" paragraph: every `inputSchema` is generated from its request model, rejects unknown
  fields, carries bounds/patterns, exposes `dry_run` on write tools, nests `github_push_files` file
  entries under `$defs`.
- Rewrite the `max_per_page` bullet: the model validates `per_page` 1..100 (default 30 for the four
  paginated repository-domain tools); config clamps only below that cap.
## Alternatives considered
- N/A: prose-level edit; the generated tool/port table is owned by `tools/generate_reference_table.py`.
## Implementation
### Target file
`docs/22_mcp/mcp_04_01_web-search-file-read-github.md`
### Procedure
1. Insert the "Input contract" paragraph after the **Configuration:** line of the github-mcp section.
2. Rewrite the `max_per_page` bullet; extend Error mapping: local argument rejection is `is_error:
   true` on `/v1/call_tool` (HTTP 400 on `GitHubValidationError`), distinct from PyGithub mapping.
3. List the changed inputs from REQ-004/REQ-005/REQ-008 as compact bullets: newly rejected argument
   shapes (unknown fields, empty text, out-of-range numbers, oversized payloads, empty or oversized
   lists, no-op PR update) and newly accepted ones (`dry_run`, previously unpublished `per_page`).
## Compatibility considerations
- N/A: docs-only row; it records behavior introduced by seq 03-13, changes no code or config.
## Security considerations
- N/A: documentation of existing guards (seq 03-13).
## Rollback considerations
- N/A: revert the commit.
## Validation plan
- The four docs gates in `rules/tool-gates.md` (`check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp`).
## Completion criteria
- The github-mcp section states the generated-schema contract, `dry_run` publication, the corrected
  `per_page` story, and the changed-input lists, with all docs gates passing on this file.
## Out of Scope
- Config parsing rules (seq 19), generated reference tables, agent-side gate docs.
## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Input contract paragraph, changed-input lists, `max_per_page` rewrite | Completed | 20261124-222851 | 20261124-222851 | REQ-001, REQ-003, REQ-005, REQ-008 REQ-001, REQ-003, REQ-005, REQ-008 Input contract paragraph + newly rejected/accepted bullets added after Configuration; max_per_page bullet rewritten to model-bound-then-config-clamp; Error mapping extended with the local-rejection outcome (is_error true / HTTP 200 on /v1/call_tool, HTTP 400 on the domain routers). |
| 2 | Run the docs gates | Completed | 20261124-222851 | 20261124-222851 | check_docs_quality, check_docs_structure (this file), check_docs_content_policy --strict, check_docs_consistency --domain mcp, check_docs_japanese: all clean. |
### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (single schema source), `REQ-003` (`dry_run` published), `REQ-005` (bounds), `REQ-008` (runtime rejection)
- **Source issue**: issues/20261119-140510_mcpai003_github-pydantic-schema-source.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-173306_mcpai003_github-pydantic-schema-source.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-181931
- **Related target files**: `docs/22_mcp/mcp_04_01_web-search-file-read-github.md`