## Goal
- Make Git MCP write outcomes evidence-based: verify every write against a fresh post-operation snapshot with an operation-specific postcondition, run network writes in a cancellable subprocess, report ambiguous outcomes as `outcome_unknown`, and release every repository handle on every path.

## Priority
Medium

## Scope
- **In-Scope**: fresh post-operation `RepositoryState` capture in the write pipeline; per-operation postconditions for `git_add`, `git_commit`, `git_checkout`, `git_pull`, `git_push`; cancellable subprocess execution for pull and push with process-group termination and state reconciliation; the `confirmed-not-applied` / `outcome_unknown` outcome split in the shared write-outcome vocabulary; handle closure on success, rejection, dry-run, error, and timeout; real-repository and bare-remote integration tests; the Git MCP documentation update for per-operation postconditions and timeout outcomes.
- **Out-of-Scope**: the dedup state machine (mcpai001); GitHub and File MCP behavior; the authorization behavior of `verify_authorization()` (this Plan verifies postconditions only); protected-branch tests for the HEAD-destination check, which belong to the work that follows the maintainer's ADR-012 Invariant decision (governance MCP-005).
- **Dependencies**: mcpai001 (outcome-unknown and retry/review semantics) and mcpai006 (shared write-outcome vocabulary) are both closed — their Plans are archived and their procedure rows are `Completed`; no ordering dependency remains. mcpai012 owns the final documentation sweep of the same Git MCP document; see Assumptions.

## Background
Source: consolidated review backlog (`memo-issue.md`, Issue 8). The archived plan for `RepositoryState` cleanup (`plans/done/20261026-223348_mcp005_repositorystate-repo-no-cleanup.md`) added `close()` and context-manager support, and those are present in the current source (`repository_state.py:110-125`); this cycle re-checked what that plan actually closed and found the live call sites still do not use them.

## Problem
The write pipeline reports success without fresh evidence: `WriteProtectionPipeline.run()` passes the same object as both pre-state and post-state (`scripts/mcp_servers/git/write_protection_pipeline.py:216`, `:221`), so Stage 7 compares a snapshot with itself. `RepositoryState.verify_postcondition()` implements one check only, for `git_pull` unresolved conflicts (`scripts/mcp_servers/git/repository_state.py:177-199`); `git_add`, `git_commit` and `git_push` have no Stage 7 check. Pull and push run on a worker thread (`scripts/mcp_servers/git/git_service.py:157-175`), so `asyncio.wait_for` cancels the await but not the synchronous operation, which continues and can succeed after the caller was told it timed out. `RepositoryState` handles are opened without closing them on the live paths (`scripts/mcp_servers/git/git_service.py:149`, `scripts/mcp_servers/git/format_output.py:152`, `scripts/mcp_servers/git/git_server.py:338`, `:359`).

## Reason for Change
Reliability and correctness of write outcomes reported to the Agent: a reported success must be backed by post-operation state, and a timeout must not leave an unmanaged operation running.

## Implementation Intent
Capture a second snapshot after the mutating call and verify it against an operation-specific postcondition. Move pull and push from the worker-thread path to a cancellable subprocess using the existing process-group pattern already implemented in the shell MCP server. Classify an ambiguous write as `outcome_unknown` and a verified non-application as `confirmed-not-applied`, and never retry the former automatically. Release the `git.Repo` handle on every path through a context manager.

## Requirements
- `REQ-001`: The pipeline captures a fresh post-operation `RepositoryState` after the mutating call; `PipelineResult.post_state` is that snapshot, not the pre-operation snapshot.
- `REQ-002`: Each write tool has a documented, operation-specific postcondition: add (index entry present), commit (HEAD commit created with the expected message/author state), checkout (HEAD lands on the requested branch), pull (no unresolved conflicts and the fetched ref advanced), push (the remote ref equals the expected local commit).
- `REQ-003`: `git_pull` and `git_push` run in a cancellable subprocess; on timeout the process group is terminated and repository and remote state are reconciled before the result is reported.
- `REQ-004`: Write outcomes distinguish `confirmed-not-applied` from `outcome_unknown` using the shared vocabulary; `outcome_unknown` is never retried automatically.
- `REQ-005`: The `git.Repo` handle is closed on success, rejection, dry-run, exception, and timeout paths.
- `REQ-006`: Postcondition coverage is exercised by integration tests on a real temporary repository and a bare remote, not only by mocks that simulate a postcondition failure.
- `REQ-007`: Documentation records the per-operation postconditions and the timeout outcomes as failure behavior, not as a blanket guarantee.

## Implementation Target Files
**Freeze status**: Frozen — `issue-to-plan` Step 8's Implementation Target Files
Validation passed for every row on 20261126; see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/mcp_servers/git/write_protection_pipeline.py` | Modify | Capture a fresh post-operation snapshot after Stage 6 and pass it to Stage 7; carry the write outcome in `PipelineResult` | REQ-001, AC-1 | `post_state=self._state` at lines 216 and 221 passes the pre-state object as post-state (checked in Step 2) | `tests/mcp_servers/git/test_repository_state.py` | Verified |
| `scripts/mcp_servers/git/repository_state.py` | Modify | Add operation-specific postcondition branches for add, commit, checkout, and push, including the push remote-ref comparison | REQ-002, AC-2 | `verify_postcondition()` at lines 177-199 checks only `git_pull` unresolved conflicts (checked in Step 2) | `tests/mcp_servers/git/test_repository_state.py` | Verified |
| `scripts/mcp_servers/git/git_service.py` | Modify | Keep the `asyncio.to_thread` dispatch so the event loop stays responsive; remove the `asyncio.wait_for` deadline for pull and push, since the timeout is enforced inside the synchronous subprocess call in Stage 6's op; carry the pipeline's write outcome in a `GitServiceError` subclass defined in this file, which is the only channel the server layer has for it; close the snapshot handle on every path | REQ-003, REQ-004, REQ-005, AC-3, AC-4, AC-5 | worker-thread timeout at lines 157-175; `RepositoryState.snapshot()` at line 149 is never closed (checked in Step 2); `DispatchResult` carries `result` and `is_error` only (`scripts/mcp_servers/dedup_gate.py:33`), so this file is where the outcome channel is added (added in Step 3a) | `tests/mcp_servers/git/test_git_service_dispatch.py` | Verified |
| `scripts/mcp_servers/git/format_output.py` | Modify | `format_pull()` and `format_push()` run the mutating call through a synchronous `subprocess` call with `start_new_session=True` and `os.killpg()` on timeout inside Stage 6's op, and report the outcome instead of assuming success | REQ-003, REQ-004, AC-2, AC-3 | `format_pull()` docstring states the deadline cannot be applied inside the synchronous helper (`format_output.py:185-192`); its own snapshot refresh at line 152 is not closed (checked in Step 2) | `tests/mcp_servers/git/test_format_output.py` | Verified |
| `scripts/mcp_servers/git/git_server.py` | Modify | Report the pipeline's write outcome in the audit record instead of the current `ok`/`rejected`/`error` mapping only, reading it from the `GitServiceError` subclass raised by `scripts/mcp_servers/git/git_service.py`, and close the two snapshots it opens (REQ-005) | REQ-004, REQ-005, AC-4, AC-5 | `outcome` is set to `ok`/`rejected`/`error` at `git_server.py:342-358` and passed to `_audit_log_safe()` at line 370 (checked in Step 3); `RepositoryState.snapshot()` at `git_server.py:338` and `:359` is never closed (added in Step 3a) | `tests/mcp_servers/test_write_dangerous_audit.py` | Verified |
| `scripts/shared/write_outcome.py` | Modify | Add the `confirmed-not-applied` member to `WriteOutcome` and to the no-auto-retry vocabulary | REQ-004, AC-4 | `WriteOutcome = Literal["outcome_unknown", "applied_audit_failed"]` at line 20 has no `confirmed-not-applied` member; the term appears nowhere else in the repository (checked in Step 3) | `tests/shared/test_write_outcome.py` | Verified |
| `tests/shared/test_write_outcome.py` | Modify | Test the new vocabulary member and that it is not in the automatic-retry set | REQ-004, AC-4 | existing file covers the two current members only (checked in Step 3) | itself | Verified |
| `tests/mcp_servers/git/test_repository_state.py` | Modify | Convert the remaining mock-based postcondition assertions into real-repository cases that perform the write and verify against a fresh post-state; the push characterization test at line 171 and the Stage 7 characterization test at line 970 (`assert result.post_state is state`) change when the fresh post-state and the push postcondition land | REQ-006, AC-1, AC-2 | `MagicMock(spec=RepositoryState)` at lines 298, 656, 945 and `_make_mock_repo()` at line 557 simulate the repository; real-repository fixtures already exist at line 39 (`working_repo`) and are used by the postcondition tests at lines 347, 357, 363 (corrected in Step 3a) | itself | Verified |
| `tests/mcp_servers/git/test_git_service_dispatch.py` | Modify | Add timeout-before-application and timeout-near-success cases for the cancellable subprocess path | REQ-003, REQ-006, AC-3 | `test_slow_pull_raises_timeout` at line 867 asserts the current thread-based behavior (checked in Step 3) | itself | Verified |
| `tests/mcp_servers/git/test_git_write_postconditions.py` | Create | New file: temporary-repository integration tests for add, commit, checkout, pull, and bare-remote tests for push, plus resource-close tests for the five paths | REQ-005, REQ-006, AC-2, AC-5 | New file; `tests/mcp_servers/git/` already has real-repository fixtures (`test_repository_state.py:39` `working_repo`, `test_git_service_dispatch.py:615`), but no test performs a write and verifies its postcondition against a fresh post-operation snapshot produced by the pipeline (corrected in Step 3a) | itself | Verified |
| `docs/22_mcp/mcp_04_05_git.md` | Modify | Record the per-operation postconditions and the timeout outcomes; the current text states that add, commit and push have no Stage 7 check | REQ-007, AC-6 | `mcp_04_05_git.md:117` states one Stage 7 check for `git_pull` only and no check for add/commit/push (checked in Step 3) | `uv run python tools/check_docs_quality.py` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories, glob
patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/mcp_servers/shell/subprocess_runner.py` | The existing cancellable-subprocess pattern to follow: `start_new_session=True` and `os.killpg()` on timeout (`run_subprocess()` lines 54-111) | REQ-003 |
| `tests/mcp_servers/git/test_git_security_compliance.py` | `TestPostConditionBypassPrevention` (line 763) is ADR-cited for INV-06; it must keep passing and is not replaced by this Plan | REQ-006 |
| `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md` | INV-06 and INV-09 define the Stage 7 postcondition obligation and the stage order this Plan must not reorder | REQ-002 |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | MCP-005 (line 174) is the open Invariant gap this Plan must not be read as covering | REQ-002 |
| `scripts/mcp_servers/git/git_models.py` | `GitPullRequest` and `GitPushRequest` field shapes used by the subprocess path | REQ-003 |
| `scripts/mcp_servers/git/git_tools.py` | Per-tool `retry_policy` values that must stay aligned with the outcome classification | REQ-004 |

## Acceptance Criteria
- AC-1: Pipeline results contain a fresh post-operation state, and each Git write has a documented postcondition (REQ-001, REQ-002).
- AC-2: Push verifies the remote ref against the expected local commit (REQ-002).
- AC-3: A timeout cannot leave an unmanaged worker thread continuing the operation (REQ-003).
- AC-4: Outcome-unknown writes are not retried automatically, and `confirmed-not-applied` is reported separately from `outcome_unknown` (REQ-004).
- AC-5: Repeated execution does not leak repository handles or file descriptors on success, rejection, dry-run, exception, and timeout (REQ-005).
- AC-6: The Git MCP documentation states the per-operation postconditions and the timeout outcomes (REQ-007).

## Tests
- Temporary-repository integration tests for add, commit, checkout, and pull; bare-remote integration tests for push (REQ-002, REQ-006).
- Timeout-before-application and timeout-near-success tests for the subprocess path (REQ-003).
- Resource-close tests for success, rejection, dry-run, exception, and timeout (REQ-005).
- Vocabulary test that `confirmed-not-applied` is outside the no-auto-retry set while `outcome_unknown` is inside it (REQ-004).
- Run ruff, mypy, import-linter, bandit, and the full test suite per `rules/toolchain.md`.

## Documentation Impact
Yes. `docs/22_mcp/mcp_04_05_git.md` (Git MCP, per `docs/00_index.md` "Document References by Task" → MCP) records per-operation postconditions and timeout outcomes as failure behavior, not as a blanket guarantee (REQ-007). The final sweep of the same document is mcpai012's work; this Plan writes only the per-operation facts it establishes.

## Assumptions
- The subprocess path uses the standard library (`asyncio.subprocess`) and the process-group pattern already used by the shell MCP server; no new dependency is introduced.
- The ADR-cited mock tests in `tests/mcp_servers/git/test_git_security_compliance.py` are not replaced: they prove bypass prevention at the dispatch seam and are cited by ADR-012 INV-06. Real-repository tests are added alongside them; replacing them would require an ADR verification-table change with a maintainer approval record.
- mcpai012's documentation plan is compatible with this Plan on `docs/22_mcp/mcp_04_05_git.md`: this Plan writes the per-operation postcondition and timeout facts, mcpai012 performs the final consistency sweep afterward.
- The authorization behavior of `verify_authorization()` is unchanged; the HEAD-destination check is already covered by `TestHeadDestinationProtection` (`tests/mcp_servers/git/test_repository_state.py:1000`), which contradicts the Issue's claim that no protected-branch test covers it. The remaining gap is the missing Invariant (MCP-005), not test coverage.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the maintainer adds an ADR-012 Invariant for the HEAD-destination check or declares it out of scope (MCP-005); the postcondition tests added here must not be read as covering it | Maintainer decision, recorded in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Governance decision; this Plan changes no authorization behavior | False |
| UNK-02 | Whether the ADR-cited mock postcondition tests are to be replaced rather than supplemented | Maintainer intent for ADR-012 INV-06 verification entries | Maintainer decision; the Plan's default is to supplement, not replace | False |

Resolved during this cycle (no Unknown row): the Issue's `不明` question about subprocess compatibility is answered by `scripts/mcp_servers/shell/subprocess_runner.py`, which already implements a cancellable subprocess with process-group termination; the Issue's `不明` question about remaining handle leaks is answered by the four unclosed `RepositoryState.snapshot()` call sites listed in Problem.

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/mcp_servers/git/write_protection_pipeline.py` | Modify | Medium | 1 | High (single author, 75 commits in `scripts/mcp_servers/git/`) | not applicable (rsynced) |
| `scripts/mcp_servers/git/repository_state.py` | Modify | High (8 test files and 4 source files import it) | 2 | High (single author) | not applicable (rsynced) |
| `scripts/mcp_servers/git/git_service.py` | Modify | Medium | 1 | High (single author) | not applicable (rsynced) |
| `scripts/mcp_servers/git/format_output.py` | Modify | Medium | 1 | High (single author) | not applicable (rsynced) |
| `scripts/mcp_servers/git/git_server.py` | Modify | Medium | 3 | High (single author) | not applicable (rsynced) |
| `scripts/shared/write_outcome.py` | Modify | Medium (3 source consumers, 2 test files) | 1 | High (single author) | not applicable (rsynced) |
| `tests/shared/test_write_outcome.py` | Modify | Low | 1 | High (single author) | not applicable (rsynced) |
| `tests/mcp_servers/git/test_repository_state.py` | Modify | Low | 2 | High (single author) | not applicable (rsynced) |
| `tests/mcp_servers/git/test_git_service_dispatch.py` | Modify | Low | 0 | High (single author) | not applicable (rsynced) |
| `tests/mcp_servers/git/test_git_write_postconditions.py` | Create | Low | N/A (new file) | High (single author) | not applicable (rsynced) |
| `docs/22_mcp/mcp_04_05_git.md` | Modify | Low | 1 | High (single author) | not applicable (rsynced) |

## Design
- **Post-state ownership**: the pipeline, not the caller, owns the post-operation snapshot, so Stage 7 compares two distinct snapshots. `format_checkout()` already refreshes its own snapshot after the mutating call; the same ownership rule is applied uniformly to the other write tools, and the checkout-specific exception in `verify_postcondition()`'s docstring is removed once the pipeline supplies a real post-state.
- **Outcome channel (added in Step 3a)**: `PipelineResult` carries the write outcome, but the server layer receives only `DispatchResult` (`result`, `is_error`, `dedup_state`) from `dispatch_tool()`, so no existing object can carry the outcome from the pipeline to `git_server.py`'s audit call. Chosen: a `GitServiceError` subclass defined in `scripts/mcp_servers/git/git_service.py` that carries the outcome value and is raised on the paths where the effect cannot be confirmed; `git_server.py` catches it before the generic `GitServiceError` handler and writes the vocabulary value as the audit outcome. Alternative — add an `outcome` attribute to `GitServiceError` in `scripts/mcp_servers/git/errors.py` — rejected: that file is not a row of the frozen `Implementation Target Files` table. Alternative — extend `DispatchResult` in `scripts/mcp_servers/dedup_gate.py` — rejected for the same reason, and because the change would affect every MCP server.
- **Cancellable execution (Path B design decision)**: alternative A keeps `asyncio.to_thread` and adds a cooperative cancellation flag — rejected, because a synchronous GitPython call has no cancellation point and the thread continues after `wait_for` raises. Alternative B calls the `git` CLI through `asyncio.subprocess` with `start_new_session=True` and terminates the process group on timeout — rejected in Step 3a, because `WriteProtectionPipeline.run()` is synchronous (`op: Callable[[], str]`, `write_protection_pipeline.py:157`) and Stage 6 must stay inside the per-repository lock, so an awaited op would require an async seam in a file whose row responsibility covers only the post-state snapshot. Chosen instead: the synchronous `subprocess` module with `start_new_session=True` and `os.killpg()` on `subprocess.TimeoutExpired`, inside Stage 6's op, following the process-group pattern of `scripts/mcp_servers/shell/subprocess_runner.py` (`run_subprocess()`, lines 54-111 — the pattern is reused, its async call form is not). The timeout is enforced inside the call, so no thread continues past it; `asyncio.to_thread` is retained so the event loop stays responsive, and `asyncio.wait_for` is removed. Remote and branch validation (`git_ref_validation`, `allowed_remote_urls`) stay in front of the call, so the security controls are unchanged.
- **Outcome vocabulary**: `confirmed-not-applied` is added to `scripts/shared/write_outcome.py` as the outcome for a write whose postcondition proves it did not land; `outcome_unknown` stays the outcome for a terminated or unverified operation. The no-auto-retry set keeps `outcome_unknown` and does not gain `confirmed-not-applied`, because a confirmed non-application is safe to retry. GitHub behavior is not changed by the added member.
- **Predictable fallout**: no target file crosses the 24576 B module-size gate at its current size (`write_protection_pipeline.py` 10385 B, `repository_state.py` 13203 B, `git_service.py` 15234 B, `format_output.py` 8773 B, `git_server.py` 17284 B), so no split row is required. No test pins a count that this change alters. No tool is added or removed, so `tools/TOOL_DESCRIPTIONS.md` is not affected. Consumer scan for `verify_postcondition` (`tools/scan_change_consumers.py --seed verify_postcondition`, 8 testmon candidates) found only the files already listed as targets or references; `scripts/mcp_servers/git/git_models.py` and `git_tools.py` are recorded as reference rows, not affected as modification targets.
- **Validation quality baseline**: `radon cc -s` reports all five Python targets at grade A (highest function complexity: `format_push` A(4)). `vulture scripts/ --min-confidence 80` reports only the `__exit__` parameters in `repository_state.py:123`. `bandit -r scripts/mcp_servers/git/ -c pyproject.toml` reports 8 low-severity `B101` asserts in `format_output.py`, none medium or high. `diff-cover coverage.xml --compare-branch=master` currently reports no lines with coverage information (clean tree at Plan creation); the implementation must reach the `rules/toolchain.md` threshold of 90% on changed lines.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table.

1. **Phase 1: Real-repository tests first** (member of the `postcondition-tests-and-implementation` unit)
   - [ ] Write the temporary-repository and bare-remote postcondition tests against the unmodified pipeline and record which of them fail (REQ-002, REQ-006; `tests/mcp_servers/git/test_git_write_postconditions.py`)
   - [ ] Convert the mock-only postcondition assertions in the existing suite to real-repository cases, keeping the ADR-cited bypass-prevention tests unchanged (REQ-006; `tests/mcp_servers/git/test_repository_state.py`)
2. **Phase 2: Fresh post-operation snapshot**
   - [ ] Capture a second `RepositoryState` after Stage 6 and pass it to Stage 7 and to `PipelineResult` (REQ-001; `scripts/mcp_servers/git/write_protection_pipeline.py`)
3. **Phase 3: Operation-specific postconditions**
   - [ ] Add the add, commit, checkout, pull, and push branches, with push comparing the expected local commit against the remote ref (REQ-002; `scripts/mcp_servers/git/repository_state.py`)
   - [ ] Run the mutating call through a synchronous `subprocess` call with `start_new_session=True` and `os.killpg()` on timeout inside Stage 6's op, and report the outcome from the formatter path rather than assuming success (REQ-002, REQ-003, REQ-004; `scripts/mcp_servers/git/format_output.py`)
4. **Phase 4: Cancellable subprocess for pull and push** (member of the `outcome-vocabulary-and-timeout` unit)
   - [ ] Remove `asyncio.wait_for` for pull and push (the timeout is enforced inside the synchronous subprocess call in Stage 6's op), keep `asyncio.to_thread` for event-loop responsiveness, reconcile repository and remote state before reporting, and raise the outcome-carrying `GitServiceError` subclass for a write whose effect cannot be confirmed (REQ-003, REQ-004; `scripts/mcp_servers/git/git_service.py`)
   - [ ] Add the timeout-before-application and timeout-near-success tests (REQ-003, REQ-006; `tests/mcp_servers/git/test_git_service_dispatch.py`)
5. **Phase 5: Outcome vocabulary** (member of the `outcome-vocabulary-and-timeout` unit)
   - [ ] Add `confirmed-not-applied` to the shared vocabulary and its test, keeping `outcome_unknown` in the no-auto-retry set (REQ-004; `scripts/shared/write_outcome.py`, `tests/shared/test_write_outcome.py`)
   - [ ] Report the write outcome in the audit record, reading it from the outcome-carrying `GitServiceError` subclass raised by `scripts/mcp_servers/git/git_service.py` (REQ-004; `scripts/mcp_servers/git/git_server.py`)
6. **Phase 6: Handle release on all paths**
   - [ ] Close the `git.Repo` handle on success, rejection, dry-run, exception, and timeout, and add the resource-close tests (REQ-005; `scripts/mcp_servers/git/git_service.py`, `scripts/mcp_servers/git/format_output.py`, `scripts/mcp_servers/git/git_server.py`, `tests/mcp_servers/git/test_git_write_postconditions.py`)
7. **Phase 7: Documentation, validation, and deployment**
   - [ ] Record the per-operation postconditions and timeout outcomes in the Git MCP document (REQ-007; `docs/22_mcp/mcp_04_05_git.md`)
   - [ ] Run the full validation sequence (`rules/toolchain.md`: format → lint → type → arch → security → test → coverage) and the docs gates `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp` (REQ-007)
   - [ ] Hand off to `skills/deploy/SKILL.md`: the change must be committed and pushed first, and deploying is the user's decision (REQ-001..REQ-007)

### Release units
**Unit**: postcondition-tests-and-implementation | **Phases**: 1, 2, 3 | **Reason**: the Phase 1 tests fail until the Phase 2 and Phase 3 implementations land, so Phase 1 cannot be validated alone.

**Unit**: outcome-vocabulary-and-timeout | **Phases**: 4, 5 | **Reason**: the subprocess timeout path reports `outcome_unknown` through the vocabulary member added in Phase 5, so Phase 4 cannot be validated alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/git/write_protection_pipeline.py` | Integration on a temporary repository | `uv run pytest tests/mcp_servers/git/test_git_write_postconditions.py -v` | Post-state is a distinct object from pre-state; each write's postcondition is exercised |
| `scripts/mcp_servers/git/repository_state.py` | Integration on a temporary repository and a bare remote | `uv run pytest tests/mcp_servers/git/test_repository_state.py tests/mcp_servers/git/test_git_write_postconditions.py -v` | Per-operation postconditions pass and fail as designed |
| `scripts/mcp_servers/git/git_service.py` | Integration with a terminated subprocess | `uv run pytest tests/mcp_servers/git/test_git_service_dispatch.py -v` | Timeout terminates the process group; no thread continues the operation |
| `scripts/shared/write_outcome.py` | Unit | `uv run pytest tests/shared/test_write_outcome.py -v` | `confirmed-not-applied` present; `outcome_unknown` still not auto-retried |
| All Python targets | Static sequence | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | No new findings |
| Changed lines | Coverage | `uv run diff-cover coverage.xml --compare-branch=master` | ≥ 90% on changed lines |
| `docs/22_mcp/mcp_04_05_git.md` | Documentation consistency | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain mcp` | No findings |

## Risks
- **Risk**: running the mutating call in a subprocess changes the per-repository serialization model (`_get_repo_lock()` is process-local and never guarded a process outside this server) → **Mitigation**: the subprocess runs inside Stage 6, which is already inside `with _get_repo_lock(self._state.path)` (`write_protection_pipeline.py:193`), so writes to the same canonical path stay ordered; cover the ordering with the existing concurrency tests.
- **Risk**: the subprocess path bypasses GitPython's remote validation, so a remote or ref check could be lost → **Mitigation**: keep `validate_ref_allowlist()`, `validate_protected()` and the `allowed_remote_urls` gate in front of the subprocess call; the existing `TestWriteRefAllowlist` cases stay green.
- **Risk**: adding a member to `WriteOutcome` affects consumers that switch on the literal → **Mitigation**: the change is additive; blast radius measured as 3 source consumers and 2 test files, below the `rules/toolchain.md` threshold.
- **Risk**: the postcondition tests added here could be read as covering governance MCP-005 → **Mitigation**: the Plan states explicitly that authorization behavior is unchanged and MCP-005 remains open.
- **Risk**: `Bus Factor` is high for every target (single author across `scripts/mcp_servers/git/`) → **Mitigation**: keep each phase independently revertable and land the tests before the implementation.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Real-repository and bare-remote postcondition tests written first | In Progress | — | — | member of `postcondition-tests-and-implementation` |
| 2 | Fresh post-operation snapshot captured by the pipeline | In Progress | — | — | — |
| 3 | Operation-specific postconditions including the push remote-ref comparison | In Progress | — | — | member of `postcondition-tests-and-implementation` |
| 4 | Cancellable subprocess for pull and push with process-group termination | In Progress | — | — | member of `outcome-vocabulary-and-timeout` |
| 5 | `confirmed-not-applied` vocabulary member and audit outcome reporting | In Progress | — | — | member of `outcome-vocabulary-and-timeout` |
| 6 | Handle release on success, rejection, dry-run, exception, and timeout | In Progress | — | — | — |
| 7 | Documentation, validation, and deploy hand-off | In Progress | — | — | deploy is the user's decision |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded at Plan creation | N/A: no blocker recorded | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261126-111533_01_scripts_mcp_servers_git_write_protection_pipeline.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261126-111533_02_scripts_mcp_servers_git_repository_state.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261126-111533_03_scripts_mcp_servers_git_git_service.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261126-111533_04_scripts_mcp_servers_git_format_output.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261126-111533_05_scripts_mcp_servers_git_git_server.py.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261126-111533_06_scripts_shared_write_outcome.py.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261126-111533_08_tests_mcp_servers_git_test_repository_state.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261126-111533_09_tests_mcp_servers_git_test_git_service_dispatch.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261126-111533_10_tests_mcp_servers_git_test_git_write_postconditions.py.md` | 1, 6 | Procedure | Pending | — | — |
| `implementations/20261126-111533_11_docs_22_mcp_mcp_04_05_git.md.md` | 7 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261119-140515_mcpai008_git-postcondition-lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261126-004921
- **Related target files**: `scripts/mcp_servers/git/write_protection_pipeline.py`, `scripts/mcp_servers/git/repository_state.py`, `scripts/mcp_servers/git/git_service.py`, `scripts/mcp_servers/git/format_output.py`, `scripts/mcp_servers/git/git_server.py`, `scripts/shared/write_outcome.py`, `tests/shared/test_write_outcome.py`, `tests/mcp_servers/git/test_repository_state.py`, `tests/mcp_servers/git/test_git_service_dispatch.py`, `tests/mcp_servers/git/test_git_write_postconditions.py`, `docs/22_mcp/mcp_04_05_git.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem; `write_protection_pipeline.py:216,221` | `scripts/mcp_servers/git/write_protection_pipeline.py` | Phase 2 | AC-1 | `tests/mcp_servers/git/test_git_write_postconditions.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes; `repository_state.py:177-199` | `scripts/mcp_servers/git/repository_state.py` | Phase 3 | AC-1, AC-2 | `tests/mcp_servers/git/test_repository_state.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes; `format_output.py:185-192` | `scripts/mcp_servers/git/format_output.py` | Phase 3 | AC-2 | `tests/mcp_servers/git/test_format_output.py` | Confirmed by repository evidence |
| REQ-003 | Problem; `git_service.py:157-175` | `scripts/mcp_servers/git/git_service.py` | Phase 4 | AC-3 | `tests/mcp_servers/git/test_git_service_dispatch.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes; `scripts/shared/write_outcome.py:20` | `scripts/shared/write_outcome.py` | Phase 5 | AC-4 | `tests/shared/test_write_outcome.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes; `git_server.py:342-358` | `scripts/mcp_servers/git/git_server.py` | Phase 5 | AC-4 | `tests/mcp_servers/test_write_dangerous_audit.py` | Derived from confirmed evidence |
| REQ-005 | Problem; unclosed `RepositoryState.snapshot()` call sites | `scripts/mcp_servers/git/git_service.py` | Phase 6 | AC-5 | `tests/mcp_servers/git/test_git_write_postconditions.py` | Confirmed by repository evidence |
| REQ-005 | Problem; `git_server.py:338` and `:359` snapshots are never closed (row responsibility added in Step 3a) | `scripts/mcp_servers/git/git_server.py` | Phase 6 | AC-5 | `tests/mcp_servers/git/test_git_write_postconditions.py` | Confirmed by repository evidence |
| REQ-006 | Testing Expectations; `test_repository_state.py:298,557` | `tests/mcp_servers/git/test_repository_state.py` | Phase 1 | AC-1, AC-2 | `tests/mcp_servers/git/test_repository_state.py` | Confirmed by repository evidence |
| REQ-006 | Testing Expectations; no real-repository test exists under `tests/mcp_servers/git/` | `tests/mcp_servers/git/test_git_write_postconditions.py` | Phase 1 | AC-2, AC-5 | `tests/mcp_servers/git/test_git_write_postconditions.py` | Confirmed by repository evidence |
| REQ-007 | Documentation Impact; `mcp_04_05_git.md:117` | `docs/22_mcp/mcp_04_05_git.md` | Phase 7 | AC-6 | `uv run python tools/check_docs_consistency.py --domain mcp` | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261126-111533 -->