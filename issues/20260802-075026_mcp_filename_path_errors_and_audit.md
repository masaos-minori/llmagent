# Fix known filename/import-path errors and audit remaining MCP docs for the same pattern

## Priority
Medium

## Summary
Several MCP documentation files contain confirmed-incorrect filenames or import paths: `docs/04_mcp_04_01` references `models.py` (actual: `github_models.py`); `docs/04_mcp_04_04`/`04_05` reference `mdq/server.py:308` (actual: `mdq_server.py:368`); `docs/04_mcp_05_02` references `mcp_servers.shell.models` and similar (actual: `shell_models.py`-style prefixed paths). These are individually confirmed, but it is unknown whether the same pattern exists elsewhere across all 45 `docs/04_mcp_*.md` files.

## Reason for Change
These are confirmed factual errors that would send a developer searching for the wrong file/line. Given the naming-drift pattern already found in multiple other places in this domain (see the naming-convention and Ownership Matrix issues), it is plausible similar errors exist elsewhere and haven't yet been found.

## Implementation Intent
Fix the 3 known errors directly, then perform a mechanical existence check for every file-path-like string across all 45 `docs/04_mcp_*.md` files to find any additional instances.

## Target Files or Areas
`docs/04_mcp_04_01`, `docs/04_mcp_04_04`/`04_05`, `docs/04_mcp_05_02`, and (for the audit) all `docs/04_mcp_*.md` files

## Required Changes
- Fix `04_mcp_04_01`: `models.py` → `github_models.py`.
- Fix `04_mcp_04_04`/`04_05`: `mdq/server.py:308` → `mdq_server.py:368` (re-verify the line number at fix time, since source may have changed further).
- Fix `04_mcp_05_02`: `mcp_servers.shell.models` and similar bare-name import paths → the actual prefixed module paths (e.g. `shell_models.py`-style).
- Extract every file-path-like string from all 45 `docs/04_mcp_*.md` files and check each against actual repository structure; report any additional mismatches found as follow-up fixes.

## Acceptance Criteria
The 3 known errors are corrected with re-verified line numbers; a completeness report exists stating either "no further path errors found" or listing additional confirmed mismatches for follow-up.

## Testing Expectations
Not required (documentation-only); the audit itself is a mechanical `ls`/`grep` verification, not a test run.

## Documentation Impact
3 files corrected directly; potentially more files flagged via the audit for follow-up fixes.

## Out of Scope
Do not fix any additional mismatches found during the audit directly in this issue — file them as separate, scoped follow-up issues instead.

## AI Implementation Instruction
Re-verify line numbers (e.g. `mdq_server.py:368`) against current source at fix time, since the line may have shifted since this review was written. For the audit, report findings per file rather than silently fixing anything beyond the 3 already-confirmed errors.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_mcp.md §1 (全体評価 item 11), §6A (ファイル名・importパスの個別誤り)
- Generated at: 2026-08-02
