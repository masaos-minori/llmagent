## Goal
State the boundary as the code implements it after Phase 3: `allowed_repos` covers reads as well as writes, an empty allowlist denies all access including reads, the canonical-key normalization policy, and the search-qualifier rule (REQ-011; AC-11).
## Scope
**Release unit**: N/A: not part of a release unit (Plan Phase 5 is validated on its own)
## Assumptions
- The file states no normalization policy, so that part is an addition, not a correction; the plan's `155-166` citation is refuted (that range is the Keywords list and the file ends at line 157).
- The fail-closed classification itself is unchanged; only the write-only wording is corrected.
## Design decisions
- Correct the existing statements in place, in the `Repository Control` section, rather than adding a section, so no heading, TOC, front-matter, or `Keywords` change is needed.
## Alternatives considered
- N/A: no alternative location for the same claim; this file is the canonical source for allowlists.
## Implementation
### Target file
`docs/22_mcp/mcp_05_01_access-control-and-allowlists.md`
### Procedure
1. Line 37 (the per-server summary row) and lines 81-83 (`### allowed_repos (github-mcp)`): state reads and writes, and that an empty allowlist denies all repository access including reads, enforced at `_get_repo()` before the first API call.
2. Add the normalization policy: `Owner/Repo` and `owner/repo` are the same key, the canonical form is the lowercase key used by the guard, the API slug, the error text, and the audit record; already-canonical input is unchanged.
3. Add the search-qualifier rule: at the default the query is scoped at construction time, and a `repo:`/`org:`/`user:` qualifier outside the boundary is rejected before the API call.
### Method
- Keep the file's existing bullet style and cross-links; add nothing outside these two sections.
### Details
- `check_docs_consistency.py --domain mcp` resolves the config keys and symbol names written here, so they must match rows 3 and 4 exactly.
## Compatibility considerations
- N/A: documentation only; the shipped defaults keep current behavior.
## Security considerations
- The stated policy and the enforced behavior agree only after Phase 3 lands, so this row is committed with the implementation, not before it.
## Rollback considerations
- N/A: revert the commit.
## Validation plan
| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `docs/22_mcp/mcp_05_01_access-control-and-allowlists.md` | Docs gates + cross-check | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/22_mcp/mcp_05_01_access-control-and-allowlists.md`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`, `uv run python tools/check_docs_consistency.py --domain mcp` | No finding; the keys and symbols named resolve against `config/` and `scripts/` |
## Completion criteria
- The file states the boundary as reads and writes, the empty-allowlist meaning including reads, the normalization policy, and the search-qualifier rule, and the docs gates pass (AC-11).
## Out of Scope
- The settings-to-check mapping rows (row 22) and the github-mcp tool page (row 23).
## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the three text changes per Procedure | Pending | — | — | |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` | Pending | — | — | Documentation-only row: no test step |
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
- **Related target files**: `docs/22_mcp/mcp_05_01_access-control-and-allowlists.md`
