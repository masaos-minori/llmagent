## Goal
- Make `HttpServerLifecycleManager.start` never report success for a process that a failed start left tracked with its exit unconfirmed: it re-terminates that process and proceeds only on a confirmed exit, otherwise it raises the startup failure again and keeps the process tracked.

## Priority
Medium

## Scope
- **In-Scope**: a failed-start marker inside `HttpServerLifecycleManager`, its use in `start`, its release wherever tracking is released, tests at the manager level and through `McpServerStarter`, and one paragraph of the lifecycle design document.
- **Out-of-Scope**: termination timeouts and the terminator's confirmation logic; the retry count and delay (`plans/20261115-215900_startrev002_mcp-start-retry-attempts.md`); the failure cooldown of `ensure_ready` and `restart`; `restart()` launching a new process while the old one is unconfirmed (recorded as UNK-03, not changed here); `HealthChecker.poll_until_ready` and `McpServerStarter` code.
- **Dependencies**: related, not blocking: `plans/20261115-215900_startrev002_mcp-start-retry-attempts.md` (re-verify the reachability of the reuse branch after that Plan lands, because a delayed retry gives the process more time to exit; both Plans add tests to `tests/agent/test_startup_mcp_lifecycle.py`, in different test classes).

## Background
- Found by an adversarial review of the agent startup path at commit `490fccc50` (Issue `issues/20261115-214903_startrev003_retry-reuses-unconfirmed-process.md`).
- `HealthChecker.poll_until_ready` terminates the child on a timeout or a shutdown request; when the termination outcome is not confirmed it calls `HttpServerLifecycleManager._raise_startup_failure_unconfirmed`, which keeps the process, pgid and stderr tracking so `shutdown_all` can name it.
- `HttpServerLifecycleManager.start` begins with a reuse branch: a tracked process whose `poll()` is `None` returns immediately ("already running (reusing)") with no health check.
- Reproduced in Step 2 of this cycle with a real `sleep` child, a terminator forced to return `EXIT_UNCONFIRMED` and `startup_timeout_sec=1`: the first `start` raised `HttpStartupError`, the process stayed tracked and alive, and the second `start` returned normally with no health check and no error. The issue's earlier statement was a reading of the code; it is now confirmed by execution.
- Through the starter the second `start` is reached by `McpServerStarter._start_http_subprocess_once` via `_ServerLifecycleRouter.start_http_subprocess`, whose `_run_lifecycle_transition` then marks the server RUNNING and the starter records the process as spawned (Explicit in code, read in Step 3).
- The later `McpServerStarter.verify_health` normally rejects the unhealthy process, so the end state is usually still a startup failure, reached by a misleading path.
- Correction to the Issue: it named "the agent runtime architecture" document for the documentation update. The paragraph that already describes `TerminationOutcome` and unconfirmed handling is in `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md` (Implementation Note, Shutdown Termination), so that is the target.

## Problem
The reuse branch cannot tell a healthy server started earlier from a process that failed its health poll and could not be proven dead. The second case is reported as a successful start. The failure is caught only if the later health verification also fails.

## Reason for Change
The tracking was retained on purpose so an unconfirmed process is never lost; the reuse branch silently undoes the intent of marking it failed. The risk is bounded by the later health verification, so it is not urgent, but it is a state-machine gap in the start path that a delayed retry (Plan 002) does not remove.

## Implementation Intent
Record on the manager that a key's tracked process is the leftover of a failed start with an unconfirmed exit. `start` consults that record before reusing: for a recorded key it asks the terminator again; a confirmed exit releases the tracking (and the record) and the start proceeds as a fresh launch; an unconfirmed exit raises the startup failure through `_raise_startup_failure_unconfirmed`, keeping the tracking and the record. A process with no record is reused exactly as today. The record is released wherever the key's tracking is released. No signature changes, and neither `HealthChecker` nor `McpServerStarter` is modified.

## Requirements
- `REQ-001`: `start` for a key whose tracked live process is the leftover of a failed, unconfirmed-exit start does not return success without a health check: it re-terminates and starts fresh on a confirmed exit, and raises the startup failure with tracking kept otherwise.
- `REQ-002`: `start`, `ensure_ready` and repeated `start` calls still reuse a healthy running process that has no failed-start record.
- `REQ-003`: `shutdown_all` still returns an entry for a process whose exit is never confirmed, and the pid and pgid logging for manual cleanup is unchanged.
- `REQ-004`: Tests cover the manager-level behavior and the path through `McpServerStarter.start_servers`.
- `REQ-005`: The lifecycle design document states what a later start does with a process whose failed start was not confirmed stopped.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/http_lifecycle.py | Own the failed-start record and honor it in `start` | Add a per-key record that maps the key to the leftover process object, set in `_raise_startup_failure_unconfirmed`; the reuse branch of `start` honors it only when the tracked process is that same object; release it in `cleanup_server_key`, `remove_process_entry`, `_raise_startup_failure` and `restart`; re-terminate a recorded process and proceed or raise | REQ-001, REQ-002, REQ-003; AC-1, AC-2, AC-3 | `start` reuse branch at lines 319-325; `_raise_startup_failure_unconfirmed` at line 243; `cleanup_server_key` at line 147; 15326 bytes, limit 24576 (checked in Step 2 and Step 3) | `tests/agent/test_http_lifecycle_integration.py` | Verified |
| tests/agent/test_http_lifecycle_integration.py | Manager-level tests | Add to `TestStartupFailureTerminateOrTrack`: a second `start` after an unconfirmed failure re-terminates and raises while the exit stays unconfirmed; starts fresh after a confirmed re-termination; a healthy tracked process is still reused; `shutdown_all` still names the unconfirmed server | REQ-001, REQ-002, REQ-003, REQ-004; AC-1, AC-2, AC-3, AC-4 | `TestStartupFailureTerminateOrTrack` at line 1157 holds `test_timeout_with_unconfirmed_exit_keeps_process_tracked` (line 1280) using the `mgr` fixture and a terminator `AsyncMock` (checked in Step 3) | tests/agent/test_http_lifecycle_integration.py | Verified |
| tests/agent/test_startup_mcp_lifecycle.py | Test through the starter | Add one test in `TestStartupOrchestratorStartServers` that wires a real `HttpServerLifecycleManager` behind the lifecycle stub path so an unconfirmed first failure followed by the retry ends in a startup failure and not in a recorded spawn | REQ-004; AC-4 | `TestStartupOrchestratorStartServers` at line 86 mocks `start_http_subprocess` today; `test_genuine_runtime_error_still_retries` shows the retry shape (checked in Step 3) | tests/agent/test_startup_mcp_lifecycle.py | Verified |
| docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md | Document the later-start rule | Add to the Implementation Note (Shutdown Termination) paragraph that a process left by a failed start with an unconfirmed exit stays tracked and is not reused by a later start (policy only, no values) | REQ-005; AC-5 | The paragraph at line 97 describes `TerminationOutcome` and retained tracking for an unconfirmed exit, and says nothing about a later start (checked in Step 3) | N/A: documentation | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/http_lifecycle_health_checker.py | `poll_until_ready` is the only caller of `_raise_startup_failure_unconfirmed` and decides when a start is unconfirmed | REQ-001 |
| scripts/agent/http_lifecycle_shutdown_coordinator.py | `shutdown_all` and `_terminate_one` define when `cleanup_server_key` releases tracking | REQ-003 |
| scripts/agent/lifecycle_router.py | `_ServerLifecycleRouter.start_http_subprocess` and `_run_lifecycle_transition` carry the second `start` to the starter | REQ-001 |
| scripts/agent/startup_mcp_starter.py | `_start_http_subprocess_once` records a returned process as spawned | REQ-001, REQ-004 |
| scripts/agent/http_lifecycle_process_terminator.py | `ProcessTerminator.terminate_with_timeout` is the call re-issued by `start` | REQ-001 |

## Acceptance Criteria
- AC-1 (REQ-001): With a terminator that reports an unconfirmed exit, a second `start` for the same key re-terminates, and while the exit stays unconfirmed it raises `HttpStartupError` and does not return success; the process stays tracked.
- AC-2 (REQ-001, REQ-002): If the re-termination confirms the exit, `start` launches a fresh process and the record is released; a tracked healthy process without a record is still reused by repeated `start` calls and by `ensure_ready`.
- AC-3 (REQ-003): `shutdown_all` still returns an entry for a process whose exit is never confirmed, and the manual-cleanup log line is unchanged.
- AC-4 (REQ-004): `uv run pytest tests/agent/test_http_lifecycle_integration.py tests/agent/test_startup_mcp_lifecycle.py tests/agent/test_http_lifecycle_health_check.py` passes with the new cases, and the new unconfirmed-reuse tests fail against the pre-change code.
- AC-5 (REQ-005): The lifecycle design document states that a process left by a failed start with an unconfirmed exit is not reused by a later start; `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_content_policy.py` pass.
- AC-6 (REQ-001, REQ-002, REQ-003): `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/` and `PYTHONPATH=scripts uv run lint-imports` pass; `uv run python tools/check_module_size.py` and `uv run python tools/generate_reference_table.py --check` pass.

## Tests
- REQ-001: manager-level tests with a terminator `AsyncMock` returning `EXIT_UNCONFIRMED` then `EXITED`, and a fake process that stays alive; a test with the real child pattern of `test_real_child_terminated_and_reaped_on_shutdown_request` is optional.
- REQ-002: a tracked process with no record is reused on repeated `start`; no terminator call is made. A record naming a different (older) process object than the tracked one is ignored: the tracked process is reused and no terminator call is made.
- REQ-003: after an unconfirmed failure and an unconfirmed re-termination, `shutdown_all` returns the server; the log line names pid and pgid.
- REQ-004: a test through `McpServerStarter.start_servers` showing that the retry after an unconfirmed first failure ends in a startup error; write the unconfirmed-reuse tests first and confirm they fail on the current code.
- REQ-005: documentation checks listed under AC-5.

## Documentation Impact
`docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md` must be updated (REQ-005): the Implementation Note on shutdown termination already documents unconfirmed handling and gains the rule for a later start. Policy only: no timeouts, no file lists, no counts (`skills/DESIGN.md` Docs content policy).

## Assumptions
- A per-key set on the manager is enough because the manager already owns the per-key tracking dicts (`_http_procs`, `_http_pgids`, `_stderr_files`, `_last_health_check`); falsifiable by the dict inventory read in Step 3.
- Re-issuing the terminator call from `start` is acceptable because `start` already awaits the launcher and the health poll, and the terminator is already injected into the manager (`process_terminator` property).
- Overlap judgment (Step 8b): `tools/check_plan_target_overlaps.py` reports one finding naming this Plan: `tests/agent/test_startup_mcp_lifecycle.py`, also targeted by `plans/20261115-215900_startrev002_mcp-start-retry-attempts.md`. Judged compatible with a sequencing preference: both Plans only add test cases (Plan 002 counts attempts and gaps; this Plan adds one unconfirmed-failure case) and neither changes or removes the other's assertions; implement Plan 002 first so the new case is written against the final retry shape. Recorded in Scope Dependencies as a sequencing note.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|----|---|---|---|---|
| UNK-01 | Whether an unconfirmed exit is reachable in normal operation (a process in uninterruptible sleep) or only on a broken host; this sets how much weight the fix deserves | Operational observation of an unconfirmed outcome | Implementation phase: keep the fix small regardless; observe the agent log for `exit not confirmed` lines | False |
| UNK-02 | Reachability of the reuse branch after `plans/20261115-215900_startrev002_mcp-start-retry-attempts.md` lands (open sibling Plan, related, not blocking) | The branch's reachability once the immediate second attempt is gone | Re-run the unconfirmed-reuse test after that Plan: `plans/20261115-215900_startrev002_mcp-start-retry-attempts.md` | False |
| UNK-03 | `HttpServerLifecycleManager.restart` pops the old process from tracking, logs an unconfirmed termination and still starts a new process, which can leave an untracked old process and a port conflict | A runtime check of the old process after an unconfirmed termination | A separate issue if confirmed; out of scope here | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/http_lifecycle.py | Modify | Medium: every subprocess MCP server start, restart and shutdown goes through this manager; behavior changes only after an unconfirmed failed start | 7 | High: one author | not applicable (rsynced): `deploy/deploy.sh` rsyncs `scripts/` |
| tests/agent/test_http_lifecycle_integration.py | Modify | Low: tests only | 4 | High: one author | not applicable (rsynced): `tests/` is not deployed |
| tests/agent/test_startup_mcp_lifecycle.py | Modify | Low: tests only | 2 | High: one author | not applicable (rsynced): `tests/` is not deployed |
| docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md | Modify | Low: one paragraph of one design document | 4 | High: one author | not applicable (rsynced): `docs/` is not deployed |

## Design
- **Design decision (failed-start record)**: options weighed. (1) Make `start` always re-terminate a live tracked process: rejected, it would kill healthy servers on every idempotent `ensure_ready`/`start`. (2) Drop the process from tracking on an unconfirmed failure: rejected, `shutdown_all` would stop naming it, which the tracking retention exists to prevent. (3) A per-key record set in `_raise_startup_failure_unconfirmed` and consulted only by the reuse branch: chosen. Compatibility impact: no signature changes; behavior changes only for a key that failed a start with an unconfirmed exit.
- **Release points of the record**: `cleanup_server_key` (confirmed shutdown), `remove_process_entry` (`shutdown_all` pops the process entry before termination and keeps the pgid when the exit stays unconfirmed, so the next `start` launches fresh), `_raise_startup_failure` (confirmed failure), `restart` (tracking cleared), and a confirmed re-termination in `start`. Corrected in the plan-to-implementation-procedure cycle: the first version of this bullet missed `remove_process_entry` (and the launcher's own failure cleanup that pops `_http_procs`), which would leave a key-only record behind and make a later `start` re-terminate a healthy, freshly launched process.
- **Identity binding (added in the same correction)**: the record stores the leftover process object, not only the key. The reuse branch re-terminates only when the tracked process `is` the recorded object; a record that outlived its process (any release path missed now or added later) never matches a new process and is ignored, and a fresh launch overwrites the tracked process. The explicit releases above stay, so the mapping does not accumulate stale entries.
- **Architecture analysis**: `lint-imports` reports 6 contracts kept, 0 broken at this commit; `http_lifecycle.py` already imports the terminator, the health checker and the shutdown coordinator, so no new import is needed (checked in Step 5).
- **Dependency graph**: `_raise_startup_failure_unconfirmed` has two callers, both in `HealthChecker.poll_until_ready`; `cleanup_server_key` is called by `ShutdownCoordinator`; `start` is called by `_SubprocessLifecycleManager.start_http_subprocess` and `ensure_ready` (checked in Step 3).
- **Historical analysis**: `http_lifecycle.py` 7 commits and `test_http_lifecycle_integration.py` 4 commits in the last 30 days, one contributor (two spellings of one name) in the last 90 days (checked in Step 5).
- **Operational dependency inspection**: the change touches no port, database or service; the reproduction used a throwaway child that was killed afterwards, and no process remained (checked in Step 5).
- **Validation quality baseline**: radon: `HttpServerLifecycleManager` methods are all below C in the Step 5 listing for related files (no target method is C or worse); vulture and bandit: no finding in the target files (project-wide baseline: five unrelated vulture findings elsewhere); diff-cover baseline: the working tree equals `master`, so the diff has no coverage lines (no current number); baseline test run 12261 passed, 2 failed, 7 skipped, the two failures being the pre-existing posture tests `tests/mcp_servers/test_posture_gate_start_path.py::test_running_the_mdq_entry_module_goes_through_real_run_http` and `tests/mcp_servers/mdq/test_mdq_health_posture.py::TestBindGate::test_validated_posture_does_not_block_bind`, unrelated to this Plan; the Plan must raise diff coverage to the `rules/toolchain.md` threshold.

## Implementation steps
1. **Phase 1: Manager change**
   - [ ] Write the manager-level unconfirmed-reuse tests first and confirm they fail on the current code (REQ-001, REQ-002, REQ-003, REQ-004; tests/agent/test_http_lifecycle_integration.py)
   - [ ] Add the per-key failed-start record, set it in `_raise_startup_failure_unconfirmed`, release it at the release points, and make the reuse branch of `start` re-terminate a recorded process (REQ-001, REQ-002, REQ-003; scripts/agent/http_lifecycle.py)
2. **Phase 2: Starter-level test**
   - [ ] Add the test through `McpServerStarter.start_servers` and confirm the retry after an unconfirmed failure ends in a startup error (REQ-004; tests/agent/test_startup_mcp_lifecycle.py)
3. **Phase 3: Documentation**
   - [ ] Add the later-start rule to the shutdown termination note (REQ-005; docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md)
4. **Phase 4: Deployment & verification**
   - [ ] Run the validation plan; hand off to `skills/deploy/SKILL.md` only after the change is committed and pushed, and deploying is the user's decision (REQ-001, REQ-002, REQ-003; scripts/agent/http_lifecycle.py)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle.py | Unit and integration | `uv run pytest tests/agent/test_http_lifecycle_integration.py tests/agent/test_http_lifecycle.py tests/agent/test_http_lifecycle_health_check.py tests/agent/test_http_lifecycle_shutdown_coordinator.py -q` | New cases pass; existing lifecycle tests pass |
| scripts/agent/startup_mcp_starter.py (path) | Unit | `uv run pytest tests/agent/test_startup_mcp_lifecycle.py tests/agent/test_startup_rollback.py -q` | The starter-level test passes; rollback tests pass |
| Changed Python files | Static | `uv run ruff check scripts/ && uv run mypy --no-namespace-packages scripts/ && PYTHONPATH=scripts uv run lint-imports` | No findings; 6 contracts kept |
| Module size and reference table | Static | `uv run python tools/check_module_size.py && uv run python tools/generate_reference_table.py --check` | No module over its limit; no drift |
| docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md | Documentation | `uv run python tools/check_docs_quality.py && uv run python tools/check_docs_content_policy.py` | No findings |
| Diff coverage | Coverage | `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan"`, then `uv run coverage xml` and `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | At or above the threshold in `rules/toolchain.md` |

## Risks
- **Risk**: Re-terminating a process in `start` signals a process that is really healthy because the record is stale (likelihood low) → **Mitigation**: the record is set only on an unconfirmed failed start and released at every point where tracking is released; the record is bound to the process object, so a leftover record can never match a different process; tests cover release on a confirmed exit, a confirmed failure, `restart` and `shutdown_all`, and a stale record against a new process.
- **Risk**: A second unconfirmed outcome raises on every later start for that key until the process dies (likelihood low, and intended) → **Mitigation**: the failure keeps the process tracked and named for `shutdown_all` and the manual `kill` hint.
- **Risk**: Both this Plan and Plan 002 edit `tests/agent/test_startup_mcp_lifecycle.py` (likelihood medium) → **Mitigation**: different test classes; implement in order 002 then this Plan.
- **Risk**: `UNK-03` (`restart` with an unconfirmed old process) remains (likelihood unknown) → **Mitigation**: recorded and routed to a separate issue if confirmed.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Manager change and manager-level tests (scripts/agent/http_lifecycle.py, tests/agent/test_http_lifecycle_integration.py) | In Progress | — | — |  |
| 2 | Starter-level test (tests/agent/test_startup_mcp_lifecycle.py) | In Progress | — | — |  |
| 3 | Documentation (docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md) | In Progress | — | — |  |
| 4 | Deployment and verification (scripts/agent/http_lifecycle.py) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261116-094943_01_scripts_agent_http_lifecycle.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261116-094943_03_tests_agent_test_startup_mcp_lifecycle.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261116-094943_04_docs_22_mcp_mcp_03_04_tool-call-tracing-and-lifecycle.md.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261115-214903_startrev003_retry-reuses-unconfirmed-process.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-220300
- **Related target files**: scripts/agent/http_lifecycle.py, tests/agent/test_http_lifecycle_integration.py, tests/agent/test_startup_mcp_lifecycle.py, docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (1), (2); reproduction in Step 2; `start` lines 319-325 | scripts/agent/http_lifecycle.py | Phase 1 | AC-1, AC-2 | manager-level unconfirmed-reuse tests | Confirmed by repository evidence |
| REQ-002 | Issue Acceptance Criteria (2); `start` reuse branch | scripts/agent/http_lifecycle.py | Phase 1 | AC-2 | healthy-reuse test | Explicit in issue |
| REQ-003 | Issue Constraints (shutdown tracking must still name an unconfirmed process); Acceptance Criteria (3) | scripts/agent/http_lifecycle.py | Phase 1 | AC-3 | `shutdown_all` names the server test | Explicit in issue |
| REQ-001 | Issue Required Changes (3); `TestStartupFailureTerminateOrTrack` | tests/agent/test_http_lifecycle_integration.py | Phase 1 | AC-1, AC-2, AC-4 | `uv run pytest tests/agent/test_http_lifecycle_integration.py -q` | Explicit in issue |
| REQ-004 | Issue Testing Expectations | tests/agent/test_http_lifecycle_integration.py | Phase 1 | AC-4 | new tests fail on the pre-change code | Explicit in issue |
| REQ-004 | Issue Testing Expectations (one test through `McpServerStarter.start_servers`) | tests/agent/test_startup_mcp_lifecycle.py | Phase 2 | AC-4 | `uv run pytest tests/agent/test_startup_mcp_lifecycle.py -q` | Explicit in issue |
| REQ-005 | Issue Documentation Impact; paragraph at line 97 of the lifecycle note (the Issue named another document: corrected) | docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md | Phase 3 | AC-5 | `check_docs_quality`, `check_docs_content_policy` | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261116-094943 -->