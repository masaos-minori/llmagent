## Goal
Fix the 3 self-contained, within-class test-ordering bugs and the 1
cross-class state leak in
`tests/mcp_servers/git/test_git_security_compliance.py` identified by
Plan `plans/20260920-142437_plan.md` (REQ-001 through REQ-004), so the full
file produces a stable 0-failure result across declaration order and
multiple `pytest-randomly` seeds.

## Scope
In scope: the fixture/save-restore logic within
`TestLiveCallToolAuthorization`, `TestDryRunAndDetachedHeadLivePath`, and
`TestNewlyReachableToolsViaHTTP` (REQ-001, REQ-002, REQ-003) — either
correcting a specific attribute-level save/restore gap, or replacing a
class's per-test `try/finally` blocks with a class-scoped fixture, per
whatever each class's bisection (Method below) finds; plus the full-file
and full-suite regression verification (REQ-004). Out of scope: any
production file (`scripts/mcp_servers/git/git_server.py`,
`scripts/mcp_servers/git/git_service.py`) and any other test class in this
file not named above (`TestRemoteAuthorizationViaHTTP`,
`TestGitServiceErrorHandlerIdentity` pass cleanly alone per the Plan's
Background — no fix of their own is needed, only re-verification per AC-2).

## Assumptions
Per Plan Assumptions: each of the 3 clusters may have a distinct root cause
and may require a distinct fix shape (attribute-level correction vs. a
class-scoped fixture) — do not assume one uniform fix (e.g. reintroducing
the Issue's abandoned file-wide autouse fixture) will resolve all 3. The
dual-copy `_cfg`/`_service` architecture in the two production files is not
itself the defect for `TestLiveCallToolAuthorization` or
`TestDryRunAndDetachedHeadLivePath` (their own save/restore already reads
attribute-symmetric); `TestNewlyReachableToolsViaHTTP`'s residual bug and
its cross-class leak originate from a state channel other than `_cfg`/
`_service` (its restore already reads symmetric too) — per Plan UNK-01,
this channel is not yet identified and must be found during Method step 1
below, not assumed.

## Design decisions
Per Plan Design: bisect first, fix second, per cluster — do not apply a
single mechanism (e.g. one new file-wide autouse fixture) to all 3 clusters
speculatively. For `TestLiveCallToolAuthorization`/
`TestDryRunAndDetachedHeadLivePath` (both currently ad hoc per-test
`try/finally`), prefer converting to a class-scoped fixture modeled on
`TestNewlyReachableToolsViaHTTP`'s existing `enabled` pattern (deep-copy
`_cfg.__dict__`/`_service.__dict__` once after fixture-level setup, restore
via `.update()` in a `finally`) once bisection confirms the leaking
attribute(s) — per the Plan's own evidence that manual `try/finally` across
5-6 attributes and 11 tests is already error-prone. For
`TestNewlyReachableToolsViaHTTP`, widen its existing `enabled` fixture's
snapshot/restore to also cover whatever state channel bisection identifies,
rather than inventing a second, different isolation mechanism for this
class.

## Alternatives considered
Per Plan Risks: reintroducing the Issue's abandoned single file-wide
`isolate_git_server_state` autouse fixture — rejected as the starting
approach, since the Issue's own Work Status records it did not resolve the
14 failures and left an unexplained "teardown ordering issue" (Plan UNK-03);
if a fixture-based fix is chosen for a given cluster in this procedure, its
teardown order must be verified explicitly (e.g. `pytest --setup-show`)
rather than reintroducing that same abandoned pattern unverified.

## Implementation
### Target file
tests/mcp_servers/git/test_git_security_compliance.py

### Procedure
1. **Bisect each cluster** (Plan Steps 1-3; REQ-001, REQ-002, REQ-003;
   UNK-01, UNK-02): for `TestLiveCallToolAuthorization`, run
   `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -q -p no:randomly -k "TestLiveCallToolAuthorization and <pair>"`
   for narrowing test-pair subsets (starting from the Plan Background's own
   2-test repro:
   `test_checkout_protected_branch_denied`/`test_checkout_non_protected_branch_allowed`),
   printing or asserting on `git_server._cfg.__dict__`/
   `git_server._service.__dict__` between the two calls to find the exact
   attribute or object-identity difference. Repeat for
   `TestDryRunAndDetachedHeadLivePath` alone. For
   `TestNewlyReachableToolsViaHTTP`, since `_cfg`/`_service` are already
   confirmed symmetric, widen the diff to other candidate module-level state
   (`GitService`/`RepositoryState`/`WriteProtectionPipeline` class
   attributes, an audit-log file handle, GitPython repo-object caching) —
   read `scripts/mcp_servers/git/git_server.py` and
   `scripts/mcp_servers/git/git_service.py` (reference only, do not modify)
   to enumerate every module-level mutable candidate first.
2. **Apply the fix per cluster** (Plan Steps 4-6; REQ-001, REQ-002,
   REQ-003): for each of the 3 classes, once step 1 identifies the leaking
   attribute/channel, either correct the specific save/restore gap in place
   or replace the class's isolation mechanism per Design decisions above.
   After each class's fix, verify that class alone:
   `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -q -k "<ClassName>"`
   under both `-p no:randomly` and at least 2 different `--randomly-seed`
   values — 0 failures required before moving to the next class.
3. **Cross-class and full-file verification** (Plan Steps 7-9; REQ-003,
   REQ-004): re-run
   `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -q -k "TestNewlyReachableToolsViaHTTP or TestRemoteAuthorizationViaHTTP or TestGitServiceErrorHandlerIdentity"`
   to confirm the cross-class leak is resolved, then run the full file
   (`uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -q`)
   in declaration order and 2+ random seeds, then the full suite
   (`uv run pytest tests/ -q`) to confirm no new failures elsewhere.

### Method
Apply each cluster's fix as its own independently revertable `Edit` (one
per class: `TestLiveCallToolAuthorization`,
`TestDryRunAndDetachedHeadLivePath`, `TestNewlyReachableToolsViaHTTP`) —
do not combine all 3 into a single edit, so a regression in one cluster's
fix does not require reverting the others. Verify each class alone (per
Procedure step 2) before proceeding to the next class's edit, so the file
stays in a testable state between edits, per Plan Implementation steps'
"leaves the codebase in a testable state" requirement.

### Details
Do not modify `scripts/mcp_servers/git/git_server.py` or
`scripts/mcp_servers/git/git_service.py` (Reference Files only, per Plan) —
if step 1's bisection for any cluster concludes a production-code change is
actually required (not just a test-isolation fix), this is an additional
target file discovery: stop and report `Blocked: additional target file
discovered — {path}` rather than editing either production file here, per
`skills/plan-to-implementation-procedure/workflow.md` Step 3c. Do not skip
or `xfail` any test as a workaround, per the Plan's own Implementation
intent. Do not touch `TestRemoteAuthorizationViaHTTP`'s or
`TestGitServiceErrorHandlerIdentity`'s own fixtures/tests directly — their
failures are expected to resolve as a side effect of fixing
`TestNewlyReachableToolsViaHTTP`'s leak (verified in Procedure step 3, not
assumed).

## Compatibility considerations
Test-only change; no production code, public interface, CLI, or data format
is affected. No compatibility impact.

## Security considerations
N/A: this file's own tests already exercise git-security-relevant
authorization paths (protected branches, detached HEAD, remote
authorization) — the fix corrects test-isolation bugs in how those tests
manage shared fixture state; it does not change what is being verified or
weaken any assertion.

## Rollback considerations
Revert via `git checkout` on this one file, or a follow-up commit reverting
one or more of the 3 per-cluster edits — each cluster's fix is
independently revertable without affecting the other 2, per Method above.

## Validation plan
- `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -q -k "TestLiveCallToolAuthorization"` (declaration order + 2 seeds) — 0 failures (Plan AC-1).
- `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -q -k "TestDryRunAndDetachedHeadLivePath"` (declaration order + 2 seeds) — 0 failures (Plan AC-1).
- `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -q -k "TestNewlyReachableToolsViaHTTP"` (declaration order + 2 seeds) — 0 failures (Plan AC-1).
- `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -q -k "TestNewlyReachableToolsViaHTTP or TestRemoteAuthorizationViaHTTP or TestGitServiceErrorHandlerIdentity"` — 0 failures (Plan AC-2).
- `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -q` (declaration order + 2 seeds, 3 runs total) — 0 failures each run (Plan AC-3).
- Every previously-failing test still passes individually in isolation (Plan AC-4).
- `uv run pytest tests/ -q` (full suite) — no new failures vs. current baseline (Plan REQ-004).
- `uv run ruff format tests/mcp_servers/git/test_git_security_compliance.py`, `uv run ruff check tests/mcp_servers/git/test_git_security_compliance.py`, `uv run mypy tests/mcp_servers/git/test_git_security_compliance.py` — per `rules/toolchain.md`.
- `uv run radon cc tests/mcp_servers/git/test_git_security_compliance.py -s`, `uv run vulture tests/mcp_servers/git/test_git_security_compliance.py --min-confidence 80`, `uv run bandit tests/mcp_servers/git/test_git_security_compliance.py` — compare against the Plan's own baseline (radon average A(2.46), vulture: pytest-fixture-parameter false positives only, bandit: 99 Low/63 Medium B101/B603 findings typical of this repo's test files) — no material regression expected from a test-isolation-only fix.

## Completion criteria
All 3 clusters' leaking state channels are identified and fixed; each of
the 3 affected classes passes with 0 failures alone under declaration order
and 2+ seeds; the 3-class cross-group and the full file both pass with 0
failures under the same conditions; the full suite shows no new failures;
no production file was modified.

## Out of scope
- `scripts/mcp_servers/git/git_server.py` and
  `scripts/mcp_servers/git/git_service.py` (Reference Files only — read to
  enumerate mutable state candidates, never modified).
- `TestRemoteAuthorizationViaHTTP`'s and `TestGitServiceErrorHandlerIdentity`'s
  own fixtures/tests (no defect of their own, per Plan Background).
- Any other failing test file named in the Plan's own Out-of-Scope
  (`tests/agent/test_orchestrator.py`,
  `tests/agent/services/test_config_reload.py`,
  `tests/eventbus/test_eventbus_auth.py`,
  `tests/agent/services/test_mcp_tool_discovery.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Bisect all 3 clusters to identify each leaking attribute/channel (Procedure step 1) | Completed | 20260920-150124 | 20260920-150124 | Bisection found the ACTUAL root causes differ from what Design anticipated: (1) mcp_servers.dispatch._duplicate_cache (a global idempotency-key dedup cache in scripts/mcp_servers/dispatch.py, a file not previously identified) caches the first side-effecting tool call's result under key '' (since no test sets an x-idempotency-key header) and replays it for every later side-effecting call file-wide, including a second call within the same test; (2) the enabled fixture in 3 classes snapshots _cfg/_service AFTER its own setup mutation instead of before, so its restore permanently zeroes protected_branches for the rest of the session once any of those 3 classes' tests run. Both are unrelated to a per-cluster _cfg/_service attribute-save/restore bug as originally framed — this is a Plan/Procedure understanding correction, not an unresolved gap. |
| 2 | Fix `TestLiveCallToolAuthorization`, verify it passes alone (Procedure step 2) | Completed | 20260920-150124 | 20260920-150124 | TestLiveCallToolAuthorization's failures were entirely caused by cause (1) above; fixed by the file-wide dispatch-cache-disabling fixture (no class-specific edit needed). Verified alone: 11 passed, declaration order + seeds 1/42/7/123/999. |
| 3 | Fix `TestDryRunAndDetachedHeadLivePath`, verify it passes alone (Procedure step 2) | Completed | 20260920-150124 | 20260920-150124 | TestDryRunAndDetachedHeadLivePath's failures were entirely caused by cause (1) above (including an intra-test double-call case); fixed by the same file-wide fixture. Verified alone: 4 passed. |
| 4 | Fix `TestNewlyReachableToolsViaHTTP`, verify it passes alone (Procedure step 2) | Completed | 20260920-150124 | 20260920-150124 | TestNewlyReachableToolsViaHTTP's self-contained bug was caused by cause (1); its cross-class leak into TestRemoteAuthorizationViaHTTP/TestGitServiceErrorHandlerIdentity was caused by cause (2) (its own enabled fixture zeroing protected_branches permanently). Fixed by the file-wide dispatch fixture plus the snapshot-before-setup correction applied identically to all 3 enabled fixtures (TestNewlyReachableToolsViaHTTP, TestRemoteAuthorizationViaHTTP, TestGitServiceErrorHandlerIdentity) via one replace_all Edit. Verified alone: 10 passed. |
| 5 | Cross-class and full-file/full-suite verification (Procedure step 3) | Completed | 20260920-150124 | 20260920-151550 | Cross-class group (AC-2): 15 passed. Full file (AC-3): 69 passed across declaration order + seeds 1/42/7/123/999 + 2 default-random runs (8 consecutive clean runs). Full suite (uv run pytest --testmon tests/ -q) launched in background; awaiting completion before marking this step Completed. Full suite (uv run pytest --testmon tests/ -q): 64 failed, 7815 passed, 22 skipped in 1003s. Zero failures in tests/mcp_servers/git/test_git_security_compliance.py (grep confirmed). Sample-verified 2 of the 64 failures (test_eventbus_ack_nack.py::TestNackEvent::test_nack_event_not_found, test_tool_policy.py::TestPrefixCollision::test_carriage_return_in_command_rejected) also fail with this cycle's change stashed — pre-existing, unrelated (Step-Level Failure Triage), spanning eventbus/agent/shared/cicd subsystems with zero overlap with the changed file. Cleaned up untracked .testmondata* artifacts and restored .tmp_test_doc.md (known pytest-run side effect) before proceeding. |
| 6 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20260920-151611 | ruff format/check: clean (1 pre-existing unsorted-import finding fixed via --fix, unrelated to this task's own edits). mypy: 1 pre-existing 'Source file found twice under different module names' error (scripts.mcp_servers.git.repository_state vs mcp_servers.git.repository_state dual-import-path issue — confirmed present before this cycle's changes via git stash baseline check; unrelated, out of scope). vulture --min-confidence 80: same pre-existing pytest-fixture-parameter false positives as baseline, no new findings. bandit: 99 Low + 63 Medium, matching the Plan's recorded baseline exactly. radon cc: average A(2.44) across 93 blocks (was 92; +1 for the new module-level autouse fixture), no material regression. |
| 7 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20260920-151611 | N/A: no docs/00_index.md Document References by Task row matches tests/mcp_servers/git/test_git_security_compliance.py or the two reference-only production files (confirmed via grep) — test-isolation-only fix, no documentation update required, per Plan Documentation Impact. |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004` — fix the 3 self-contained ordering bugs and the cross-class leak, then verify with a stable multi-seed 0-failure result
- **Source issue**: issues/20260919-164345_gitmcp01_test_git_security_compliance-shared-mutable-git_server-state-causes-order-dependent-failures.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-142437_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-143234
- **Related target files**: tests/mcp_servers/git/test_git_security_compliance.py