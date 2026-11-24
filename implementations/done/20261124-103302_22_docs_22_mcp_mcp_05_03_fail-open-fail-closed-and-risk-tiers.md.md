## Goal
Correct the `allowed_repos` (github-mcp) row to cover reads and writes, and add the settings-to-check rows for the two new checks and the published GitHub checks that name no guard today (REQ-009, REQ-011; AC-7, AC-9, AC-11).
## Scope
**Release unit**: N/A: not part of a release unit (Plan Phase 5 is validated on its own)
## Assumptions
- The fail-closed classification itself is unchanged; only its scope and the missing check-to-guard rows are added.
- `path_denylist` stays the registered ADR-004 fail-open exception; its row is not changed.
## Design decisions
- Extend the existing "Startup Security Validation" mapping table rather than adding a section, so the check ids stay in one place with the other servers' rows.
## Alternatives considered
- N/A: no alternative location for the check-to-guard mapping; the docs gate resolves the ids against `scripts/shared/security/posture_contract.py`.
## Implementation
### Target file
`docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`
### Procedure
1. Line 26: change "All writes denied" to reads and writes, and state that an empty allowlist denies all repository access including reads, enforced at `_get_repo()` before the first API call.
2. Add mapping rows for `allow_global_search` → `server.global_search` (`warning` when global search is opted in, `ok` when the boundary is enforced) and `max_file_read_size_kb` → `server.max_file_read_size` (`ok` when positive, `not_applicable` at `0`), naming the guard in `scripts/mcp_servers/github/github_service_security.py`.
3. Add the mapping rows for `server.repo_allowlist`, `server.force_push_policy`, `server.pr_review_required`, `server.audit_log_writable`, `server.per_page_bounds`, each naming the guard function that enforces it.
4. Line 93 (Notes for AI Systems): change "`allowed_repos` (GitHub writes)" to reads and writes.
### Method
- Keep the table's existing column wording and the `(Explicit in code — path)` citation style the existing rows use.
### Details
- `check_docs_consistency.py --domain mcp` resolves the check ids written here against `scripts/shared/security/posture_contract.py`, so they must be the ids row 24 adds, spelled the same way.
## Compatibility considerations
- N/A: documentation only; no behavior change.
## Security considerations
- The mapping is where a reader learns which published check corresponds to which enforcement; an unmapped check is the gap this row closes.
## Rollback considerations
- N/A: revert the commit.
## Validation plan
| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` | Docs gates + cross-check | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`, `uv run python tools/check_docs_consistency.py --domain mcp` | No finding; every check id named resolves against `scripts/shared/security/posture_contract.py` |
## Completion criteria
- The `allowed_repos` row covers reads and writes, every published GitHub check has a settings-to-check row naming its guard, and the docs gates pass (AC-7, AC-9, AC-11).
## Out of Scope
- The allowlist normalization and search-qualifier wording (row 21) and the github-mcp tool page (row 23).
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
- **Requirement ID**: REQ-009 (the posture reports the settings it enforces), REQ-011 (documentation states the boundary the code implements)
- **Source issue**: issues/done/20261119-140509_mcpai002_github-read-security-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095007_mcpai002_github-read-security-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-103302
- **Related target files**: `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`