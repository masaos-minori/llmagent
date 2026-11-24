## Goal
Make the github-mcp section state what the code enforces after Phase 3: read-path enforcement, the normalization policy, the read-size limit, the strict-UTF-8 policy, and the search boundary at query-construction time (REQ-011; AC-11).
## Scope
**Release unit**: N/A: not part of a release unit (Plan Phase 5 is validated on its own)
## Assumptions
- Only write-operation enforcement and `max_file_size_kb` are stated today (lines 85-91); the read-path controls are additions, not corrections. The tool list is owned by `docs/22_mcp/mcp_01_tool_ownership_matrix.md` and is not changed here.
## Design decisions
- State the added claims inside the existing "Security controls" list and "Guard coverage" subsections rather than adding a section, so the guard layering the file already describes stays intact.
## Alternatives considered
- N/A: this is the canonical github-mcp page; the allowlist policy wording stays in `mcp_05_01` (row 21) and is referenced here, not restated.
## Implementation
### Target file
`docs/22_mcp/mcp_04_01_web-search-file-read-github.md`
### Procedure
1. Line 87: state that `allowed_repos` covers reads as well as writes, enforced at `_get_repo()` before the first API call for any operation naming a repository.
2. Add the two new controls with their documented defaults: `allow_global_search = false` (searches scoped at query-construction time; a `repo:`/`org:`/`user:` qualifier outside the boundary is rejected before the call) and `max_file_read_size_kb = 0` (checked against the content metadata size before decoding).
3. State the normalization policy (the lowercase key is the single identity used by the guard, the API slug, the error text, and the audit record) and the decoding policy: content that does not decode as strict UTF-8 is rejected with `GitHubValidationError`; no U+FFFD substitution occurs.
4. In "Guard coverage" (lines 97-99), replace the write-only phrasing with the read-and-write layering: the common guard covers reads through `_get_repo()`, and the read path applies the path denylist, the read-size check, and strict decoding.
### Method
- Keep the file's existing bullet style and cite the guard module once, as the existing text does.
### Details
- The file is 116 lines at baseline; `check_docs_structure.py` bounds file size, so the added bullets must stay inside the limit.
- The config keys and symbol names written here must match rows 3 and 4 exactly, because the docs cross-check resolves them against `config/github_mcp_server.toml` and `scripts/`.
## Compatibility considerations
- N/A: documentation only; the shipped defaults keep current behavior.
## Security considerations
- This is the page a reader uses to decide whether a github-mcp read is bounded; before this row it claims enforcement the code does not perform.
## Rollback considerations
- N/A: revert the commit.
## Validation plan
| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `docs/22_mcp/mcp_04_01_web-search-file-read-github.md` | Docs gates + cross-check | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/22_mcp/mcp_04_01_web-search-file-read-github.md`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`, `uv run python tools/check_docs_consistency.py --domain mcp` | No finding; the keys and symbols named resolve against `config/` and `scripts/` |
## Completion criteria
- The section states read-path enforcement, the normalization policy, the read-size limit, the strict-decoding policy, and the query-construction boundary, and the docs gates pass (AC-11).
## Out of Scope
- The allowlist policy page (row 21) and the settings-to-check mapping (row 22).
## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the four changes per Procedure | Completed | 20261124-152854 | 20261124-152854 |  |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` | Completed | 20261124-152854 | 20261124-152854 | Documentation-only row: no test step |
### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |
### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |
## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-011 (documentation states the boundary the code implements)
- **Source issue**: issues/done/20261119-140509_mcpai002_github-read-security-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095007_mcpai002_github-read-security-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-103302
- **Related target files**: `docs/22_mcp/mcp_04_01_web-search-file-read-github.md`