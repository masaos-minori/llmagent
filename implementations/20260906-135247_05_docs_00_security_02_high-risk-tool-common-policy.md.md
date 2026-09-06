## Goal
Correct the Git MCP row (currently line 190) of `docs/00_security_02_high-risk-tool-common-policy.md`
to cite live-path evidence for its enforcement claims, alongside the existing
`GitService`-direct citations, matching row 03's ADR-012 correction (REQ-010).

## Scope
- In scope: the single Git MCP bullet at line 190 (`- **Git MCP**: ...`).
- Out of scope: line 80's separate Git MCP bullet (a different claim, about the
  absence of a subcommand allowlist and unvalidated `branch`/`remote` values — not
  flagged as stale by this cycle's investigation; still accurate) and every other
  row in this document.

## Assumptions
- Executes after row 03 (ADR-012) so the live-path test names cited here match
  exactly what row 03 confirms and adds — do not independently re-derive the test
  list; reuse row 03's Method findings.

## Design decisions
- Cite the same live-path test classes row 03 adds to ADR-012
  (`TestLiveCallToolAuthorization`, `TestDryRunAndDetachedHeadLivePath`,
  `TestPostConditionBypassPrevention`) rather than deriving a separate citation set —
  this keeps both documents' evidence for the same underlying claim consistent, per
  this Plan's AC-7 ("consistent terminology and valid cross-links").

## Alternatives considered
- Leave line 190 unedited and rely on its existing cross-reference to
  `00_governance_03_issue-and-uncertainty-management.md`: rejected — the line's own
  text ("are implemented") still rests on the dead-code-path-only test citations
  listed earlier in the same sentence; the cross-reference does not fix the
  sentence's own citation.

## Implementation
### Target file
`docs/00_security_02_high-risk-tool-common-policy.md`

### Procedure
1. In the line currently reading:
   `**Git MCP**: GitConfig.protected_branches and GitService._check_protected_branch()
   (called via _validate_protected()) enforce a protected-branch policy (tests:
   test_git_security_compliance.py::test_check_protected_branch,
   test_git_checkout_protected_branch, test_git_push_protected_branch,
   test_is_safe_ref). The Force-Push block is not applicable because git_push exposes
   no force parameter. Dirty-Worktree/Detached-HEAD guards and postcondition
   verification are implemented (see 00_governance_03_issue-and-uncertainty-management.md).`
   — append, after the existing test-name parenthetical, the live-path test classes:
   `TestLiveCallToolAuthorization` (protected-branch enforcement via
   `POST /v1/call_tool`), and for the Dirty-Worktree/Detached-HEAD/postcondition
   sentence, add `TestDryRunAndDetachedHeadLivePath` and
   `TestPostConditionBypassPrevention` as the live-path proof backing "are
   implemented".
2. Re-verify line 190 is still the correct target line before editing (re-confirm via
   `rg -n "Git MCP" docs/00_security_02_high-risk-tool-common-policy.md` — line numbers
   may have shifted since this document's authoring).

### Method
Reuses row 03 (ADR-012)'s Method findings directly — `TestLiveCallToolAuthorization`,
`TestDryRunAndDetachedHeadLivePath`, and `TestPostConditionBypassPrevention` in
`tests/mcp_servers/git/test_git_security_compliance.py` all use the `client`
(`TestClient`) fixture, confirmed via direct read this cycle (2026-09-06).

### Details
No production code change — documentation-only citation correction, consistent with
row 03's ADR-012 edit.

## Compatibility considerations
N/A: documentation-only.

## Security considerations
N/A: corrects evidence citation only; does not change the underlying protection.

## Rollback considerations
Revert via `git checkout` on this file alone if a check_docs_quality/structure finding
appears.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/00_security_02_high-risk-tool-common-policy.md`
- `uv run python tools/check_docs_structure.py docs/00_security_02_high-risk-tool-common-policy.md`
- `uv run python tools/check_docs_consistency.py --domain mcp` (cross-checks doc claims
  against `scripts/` — confirms the newly-cited test class names actually exist).

## Completion criteria
- Line 190 cites at least one live-path (`TestClient`) test class alongside the
  existing `GitService`-direct citations.
- `check_docs_quality.py`/`check_docs_structure.py`/`check_docs_consistency.py`
  report no new finding.

## Out of scope
- Line 80's separate Git MCP bullet — unrelated claim, not stale.
- ADR-012 itself — tracked in seq 03.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-010
- **Source issue**: issues/20260902-144914_gitcleanup_remove_placeholders_and_align_docs_with_verified_implementation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-192746_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-135247
- **Related target files**: docs/00_security_02_high-risk-tool-common-policy.md
