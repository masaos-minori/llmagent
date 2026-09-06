## Goal
Correct ADR-012's `## Verification` section (currently lines 182-196) to cite tests
that actually exercise the live `POST /v1/call_tool` path, and correct its
`## Known Deviations` section (currently lines 208-212) to state the real post-Phase-0
deviation status, instead of the current dead-code-path-only citations and the false
"no deviations, all resolved" claim (REQ-005, REQ-006, REQ-008).

## Scope
- In scope: rewrite the `### Automated Tests` bullets under `## Verification`
  (currently lines 184-191) to add live-path test citations alongside (not
  necessarily replacing) the existing `GitService`-direct citations; rewrite
  `## Known Deviations` (currently lines 209-212) to reflect the real current state.
- Out of scope: any other ADR-012 section (Decision, Rationale, Invariants,
  Traceability, Approval, etc.) — none were flagged as stale by this cycle's
  investigation.

## Assumptions
- Line numbers above reflect this cycle's read (2026-09-06); re-confirm immediately
  before editing.
- This document's edit executes after row 1/2 (repository_state.py + its test file
  cleanup) have landed, per the Plan's own Phase ordering (Phase 2 after Phase 1) —
  the dead-method removal must land first so this row's "post-cleanup deviation
  status" claim is accurate at the time it is written, not aspirational.

## Design decisions
- Add live-path citations alongside the existing `GitService`-direct ones rather than
  deleting the latter: the `GitService`-direct tests still provide valid unit-level
  coverage of the same logic; the gap this Plan closes is the *absence* of live-path
  proof, not the presence of unit tests.
- For `## Known Deviations`, state findings in English per this ADR's established
  English convention for `## Verification`/`## Implementation Notes`, even though the
  current `## Known Deviations` text is in Japanese — this Plan does not standardize
  the file's language choice per-section; follow whichever the section already uses
  unless correcting stale content requires touching it.

## Alternatives considered
- Replace the `GitService`-direct citations entirely with only live-path ones:
  rejected — Design decisions above; both remain valid evidence for their respective
  claims (unit-level logic vs. end-to-end reachability).

## Implementation
### Target file
`docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md`

### Procedure
1. Under `## Verification` → `### Automated Tests`, append a live-path citation to
   each existing bullet whose invariant now has direct `POST /v1/call_tool`
   `TestClient` coverage (confirmed this cycle in
   `tests/mcp_servers/git/test_git_security_compliance.py`):
   - INV-03 (protected-branch bullet, line 187): add
     `TestLiveCallToolAuthorization` (`test_checkout_protected_branch_denied`,
     `test_pull_protected_branch_denied`, `test_push_protected_branch_denied`,
     `test_checkout_non_protected_branch_allowed`,
     `test_pull_non_protected_branch_allowed`,
     `test_push_non_protected_branch_allowed`, `test_checkout_implicit_target_denied`,
     `test_pull_implicit_target_denied`, `test_push_implicit_target_denied`) as
     live-path evidence.
   - Decision Details #5 / Dirty-Worktree-Detached-HEAD bullet (line 188): add
     `TestDryRunAndDetachedHeadLivePath`
     (`test_dry_run_checkout_skips_dirty_and_detached_precondition`,
     `test_dry_run_checkout_protected_branch_still_denied`,
     `test_non_dry_run_detached_head_denied_then_allowed`,
     `test_dry_run_pull_and_push_skip_dirty_precondition`) as live-path evidence for
     both the guard itself and `gitdryrun`'s new `dry_run`/`allow_detached_head`
     parameters.
   - Decision Details #6 / Postcondition bullet (line 189): add
     `TestPostConditionBypassPrevention`
     (`test_checkout_postcondition_cannot_be_bypassed`,
     `test_pull_postcondition_cannot_be_bypassed`,
     `test_push_postcondition_cannot_be_bypassed`) — this is the concrete proof that
     postcondition verification runs on the live path and cannot be bypassed, closing
     the exact gap `gitauth`'s Plan identified (the previous citations only exercised
     `GitService` directly).
   - Decision Details #9 / stage-ordering bullet: no existing bullet cites this
     directly — add a new bullet: **Test**: all 9 pipeline stages execute in the
     documented order for `git_checkout`/`git_pull`/`git_push`
     (`TestCompletePipelineCoverage`:
     `test_all_stages_execute_in_order_for_checkout/_pull/_push`) — **Verifies**:
     Decision Details #9 — **Type**: Integration — **Blocking**: Yes.
2. Re-verify each of the pre-existing `GitService`-direct test names in lines 185-191
   still exist under those exact names before leaving them in place (do not assume
   from this Plan's authoring-time snapshot); replace any renamed/removed test name
   with its current equivalent.
3. Rewrite `## Known Deviations` (lines 209-212): remove the false "no deviations,
   all resolved" claim; state that `docs/00_governance_03_issue-and-uncertainty-management.md`'s
   MCP-001 (`verify_postcondition()` unconditional-success placeholder) and MCP-002
   (`PipelineResult` missing `post_state`) are both registered and marked `resolved`
   (confirmed this cycle), and reference row 4 (this Plan's
   `docs/00_governance_03...` document) for whether any further deviation remains
   open after Phase 1's dead-method removal lands.

### Method
Confirmed this cycle (2026-09-06) via direct read of
`tests/mcp_servers/git/test_git_security_compliance.py`: `TestLiveCallToolAuthorization`
(line 925), `TestDryRunAndDetachedHeadLivePath` (line 1512),
`TestPostConditionBypassPrevention` (line 670), and `TestCompletePipelineCoverage`
(line 787) all use the `client` fixture (a `TestClient` against the live FastAPI app,
not a direct `GitService` instantiation) — confirmed via each class's own fixture
usage pattern in this file. Confirmed via
`docs/00_governance_03_issue-and-uncertainty-management.md` (lines 709-745) that
MCP-001 and MCP-002 are both currently `Status: resolved`.

### Details
No production code changes — documentation-only correction of test citations and
deviation status.

## Compatibility considerations
N/A: documentation-only, no code or API surface affected.

## Security considerations
N/A: no security-relevant behavior change; this corrects evidence citations only.

## Rollback considerations
Revert via `git checkout` on this file alone if a check_docs_quality/structure finding
appears after the edit — no dependency from any other file on this ADR's exact
wording.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md`
- `uv run python tools/check_docs_structure.py docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md`
- Manual repository-wide search: confirm every test name newly cited actually exists
  under that name in `tests/mcp_servers/git/test_git_security_compliance.py` at the
  time of the edit (re-run `rg` immediately before committing, per Assumptions).

## Completion criteria
- `## Verification` cites at least one live-path (`TestClient`) test for INV-03,
  Decision Details #5, #6, and #9.
- `## Known Deviations` no longer states "no deviations, all resolved" without
  qualification; it accurately reflects MCP-001/MCP-002's `resolved` status and
  references row 4 for any newly-discovered gap.
- `check_docs_quality.py`/`check_docs_structure.py` report no new finding.

## Out of scope
- `docs/00_governance_03_issue-and-uncertainty-management.md` itself — tracked in
  seq 04.
- Any ADR-012 section other than `## Verification` and `## Known Deviations`.

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
- **Requirement ID**: REQ-005 (Verification test citations), REQ-006 (Known Deviations), REQ-008 (invariant-to-evidence mapping)
- **Source issue**: issues/20260902-144914_gitcleanup_remove_placeholders_and_align_docs_with_verified_implementation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-192746_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-135247
- **Related target files**: docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md
