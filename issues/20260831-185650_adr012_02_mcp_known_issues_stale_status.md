# MCP-003/MCP-004/MCP-005 Status and Resolution Notes in MCP Known Issues are stale vs. verified code and tests

## Priority
Medium

## Summary
During the ADR-012 acceptance evaluation (2026-08-31), direct code and test inspection found
that `docs/04_mcp_90_inconsistencies_and_known_issues.md`'s MCP-003, MCP-004, and MCP-005
entries contain Status values and Resolution Notes that no longer match the current
implementation. All three entries need re-verification and correction.

## Background
ADR-012 (Git MCP Server-Side Write Enforcement) was evaluated and accepted based on direct
inspection of `scripts/mcp_servers/git/*.py` and execution of the full
`tests/mcp_servers/git/` suite (164 tests, all passing). That evaluation surfaced several
discrepancies between this Known Issues document's claims and the verified current state.

## Problem
(Evidence: Explicit in code and Verified by test — see each item)

- **MCP-003** (Status: `open`): its own Resolution Notes already narrow the remaining scope to
  `GIT-001`/`GIT-002`, both of which are separately listed in the same document with
  Status `resolved`. The parent MCP-003 entry was never updated to `resolved` even though
  its full described scope (protected-branch/Force-Push guard, option-injection) is
  implemented and tested (`test_check_protected_branch`, `test_is_safe_ref`, and related
  tests in `tests/mcp_servers/git/test_git_security_compliance.py`, all passing).
- **MCP-004** (Status: `resolved`, core issue): its Resolution Notes list "(1) config floor
  check preventing effective risk below HIGH for git tools via ProductionConfigValidator" as
  a remaining open item. This floor check is already implemented:
  `scripts/shared/production_config_validator.py::_check_approval_risk_floor()` explicitly
  checks `git_checkout`/`git_pull`/`git_push` against a HIGH-risk floor. The Resolution Notes
  are stale on this specific point; items (2) (end-to-end test through shipped config) and (3)
  (git-specific approval-screen preview) were not independently re-verified during the
  ADR-012 evaluation and may still be accurate.
- **MCP-005** (Status: `open`, "Resolution Notes: Open, pending confirmation"): direct code
  inspection of `scripts/mcp_servers/git/git_server.py` (lines ~154, ~174) shows the audit
  call already uses `req.args.get("repo_path", "")` (the correct schema key) and passes it as
  `target=repo_path` to `_audit_log()` — not the `"repo"` key this entry describes as the bug.
  A dedicated test, `tests/mcp_servers/git/test_repository_state.py::test_audit_record_includes_repo_identity`,
  passes and directly verifies this. The entry's "pending confirmation" framing is stale; this
  appears fully resolved.

## Reason for Change
Known Issues Status fields and Resolution Notes are relied on elsewhere (e.g., ADR-012 itself
cited MCP-003/MCP-004/MCP-005 in its own Known Deviations before this evaluation) as the
current, canonical state of these gaps. Stale entries cause downstream documents to repeat
outdated claims and can block or misdirect future decisions (e.g., an ADR's Completion Criteria
referencing "MCP-005 must be closed" when it already is).

## Implementation Intent
Re-verify each of the three entries against current source and tests, and update Status,
Resolution Notes, and Severity fields to match. Where an entry's full scope is resolved, mark
it `resolved` with accurate Resolution Notes citing the verifying test(s). Where only part of
an entry's scope is resolved (MCP-004's remaining two items), narrow the entry's stated scope
to what is actually still open rather than leaving stale text describing already-fixed
sub-items.

## Target Files or Areas
- `docs/04_mcp_90_inconsistencies_and_known_issues.md` (MCP-003, MCP-004, MCP-005 entries)

## Required Changes
- MCP-003: update Status to `resolved` (or explicitly cross-reference GIT-001/GIT-002 as the
  entries carrying the actual resolution, if this repository's convention prefers not to
  re-flip a superseded parent entry — decide based on existing convention for similar cases).
- MCP-004: remove the "config floor check" item from the list of remaining open items in
  Resolution Notes, since `_check_approval_risk_floor()` already implements it; re-verify items
  (2) and (3) (end-to-end test, approval-screen preview) before deciding whether they remain
  accurate.
- MCP-005: update Status to `resolved`; update Resolution Notes to cite
  `test_audit_record_includes_repo_identity` and the corrected `repo_path` usage in
  `git_server.py`.

## Constraints
- Do not modify `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md` in this issue — it
  was already updated on 2026-08-31 to reflect the corrected understanding of these three
  issues (its own Known Deviations no longer lists MCP-003/004/005 as ADR-level gaps).
- Re-verify MCP-004 items (2) and (3) against current code/tests before changing their status —
  they were not independently confirmed during the ADR-012 evaluation and should not be assumed
  resolved without evidence.

## Acceptance Criteria
- MCP-003, MCP-004, and MCP-005 Status and Resolution Notes accurately reflect current
  `scripts/mcp_servers/git/` code and `tests/mcp_servers/git/` test results.
- Each corrected claim cites the specific verifying test or code location.
- `uv run python tools/check_docs_quality.py docs/04_mcp_90_inconsistencies_and_known_issues.md` shows no new issues.

## Testing Expectations
Documentation-only change. Re-run `uv run pytest tests/mcp_servers/git/ -q` (164 tests as of
2026-08-31) to reconfirm before finalizing status changes, and check
`scripts/shared/production_config_validator.py`/its tests for MCP-004 items (2)/(3).

## Documentation Impact
This issue is itself the documentation-accuracy fix for the three entries.

## Out of Scope
- Any other MCP-xxx or GIT-xxx entry in this document.
- `CI-002`'s separate stale-reference problem (production/local recovery distinction citing a
  now-merged ADR-011), already tracked in
  `issues/20260831-181721_adr008_02_ci002_stale_reference_reinvestigation.md`.

## Dependencies
Follows the 2026-08-31 ADR-012 acceptance evaluation and update.

## Unresolved Questions
Whether this repository's convention is to flip a "parent" issue like MCP-003 to `resolved`
once its narrowed sub-issues (GIT-001/GIT-002) are both resolved, or to leave the parent as a
historical umbrella entry and rely on the sub-issues for current status — needs a
maintainer/convention decision; default to marking MCP-003 `resolved` with a note pointing to
GIT-001/GIT-002 unless told otherwise.

## AI Implementation Instruction
Re-run `tests/mcp_servers/git/` and re-read `production_config_validator.py` and
`git_server.py` before editing — do not carry forward this issue's own quoted line numbers
without re-confirming them, since they may drift. Do not mark MCP-004 items (2)/(3) as resolved
without independent verification; this issue only confirms item (1) is resolved.
