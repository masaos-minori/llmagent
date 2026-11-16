## Goal
- Make every awaited startup stage honor a shutdown request: a SIGINT or SIGTERM received at any point of the startup sequence ends it with `StartupInterrupted` after the servers started so far are rolled back, before the banner is printed or a session is started.

## Priority
Medium

## Scope
- **In-Scope**: racing the two awaited stages that do not observe the shutdown event today (`StartupOrchestrator._check_services`, `StartupOrchestrator._setup_prompt`) against it; shutdown checks at the stage boundaries and at the end of `StartupOrchestrator.run`; setting the RAG stop event when the services stage is cancelled; tests per stage; correcting the interruption description in the startup design document.
- **Out-of-Scope**: signal registration and the Windows fallback in `SignalHandler`; the input loop's handling after startup; the synchronous, bounded steps (`ComponentInitializer.initialize` and the config-only stage), which cannot be raced and are covered by boundary checks only; making individual probes or discovery calls event-aware; the stop mechanism of the RAG check itself (added by `plans/20261115-220927_startrev006_rag-check-timeout-executor.md`).
- **Dependencies**: related and sequencing: `plans/20261115-220927_startrev006_rag-check-timeout-executor.md` (this Plan consumes the stop event that Plan adds, in its REQ-003 only), and `plans/20261115-220913_startrev005_posture-probed-twice-startup.md` (edits the head of `StartupValidationPipeline.check_services`; implement it before this Plan).
  - **Depends on**: plans/20261115-220927_startrev006_rag-check-timeout-executor.md | phase 2 | the stop event that REQ-003 sets on cancellation is added there; every other requirement is independent of it

## Background
- Found by an adversarial review of the agent startup path at commit `490fccc50` (Issue `issues/20261115-214904_startrev004_startup-ignores-shutdown-signal.md`).
- `AgentREPL.run` registers `SignalHandler`, which replaces the default `KeyboardInterrupt` with a handler that sets `ctx.conv.shutdown_requested` and the shared event; it runs before `StartupOrchestrator.run` (Explicit in code, read in Step 3).
- `StartupOrchestrator.__init__` passes `shutdown_event` only to `McpServerStarter`. `StartupValidationPipeline`, `ReadinessReporter`, `PromptSetup` and `ComponentInitializer` are built without it; `check_readiness`, `collect_server_postures` and `McpToolDiscoveryService.discover_all` take only the context (Explicit in code).
- Found in Step 2 of this cycle (beyond the Issue): after startup completes with the event already set, `ReplInputLoop.run` still calls `banner_callback()` and `ctx.session.start()` (which creates a session record) before `_repl_loop` reaches `_should_exit`; so an ignored signal costs a banner and a started session, not only a wait.
- Found in Step 2: `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` says that if SIGINT/SIGTERM is received during the startup sequence a `StartupInterrupted` is raised and triggers a rollback (section "SIGINT/SIGTERM Interruption During Startup", and a sentence near line 39 about delays). In the code that holds only while `McpServerStarter` waits; the documentation overstates the behavior for the later stages.
- Existing handling that must keep working: `StartupOrchestrator.run` has a dedicated `except StartupInterrupted` branch that rolls back and re-raises; `AgentREPL.run` warns and re-raises; `main` returns quietly with status 0 (`tests/agent/test_startup_rollback.py::TestStartupRollback` covers the rollback branch).
- Related, already closed and not overlapping: `issues/done/20261021-093421_repl001_sigint-sigterm-never-reach-repl-input-loop.md` connected the event to the input loop; it did not cover the startup stages.

## Problem
While an unguarded stage runs (service and posture probes, tool discovery, the RAG consistency wait, prompt setup), Ctrl-C has no visible effect and the default interrupt is no longer available, so an operator facing a hung dependency cannot stop the process short of SIGKILL. When the stage finally ends, the already-set event is honored only after the banner and a session start.

## Reason for Change
Slow or hung dependencies are exactly the situation in which an operator reaches for Ctrl-C. The behavior is an operational hazard rather than a correctness bug, and the design document already promises the interruption, so closing the gap is Medium, not High.

## Implementation Intent
Reuse the pattern the starter already uses, at the one place that sequences the stages. `StartupOrchestrator` gets a private helper that runs a stage as a task and races it against the shutdown event; when the event wins it cancels the stage, waits for the cancellation to finish, and raises `StartupInterrupted` naming the stage, which flows into the existing rollback branch. The helper is applied to `_check_services` and `_setup_prompt`. A plain event check runs before each stage that cannot be raced and once more at the end of `run`, so a signal that arrives between stages or just after the last stage is not lost. The RAG step of the services stage sets its stop event when it is cancelled, so the worker thread stops (the event comes from Plan 006). With no event set nothing changes: the sequence, the outcomes and the exceptions are the same.

## Requirements
- `REQ-001`: A shutdown request set during `_check_services` or `_setup_prompt` ends startup with `StartupInterrupted`, after the stage is cancelled and the servers started so far are rolled back, within a short, tested bound.
- `REQ-002`: A shutdown request set between stages, or after the last stage, ends startup with `StartupInterrupted` before the next stage starts and before `run` returns its result.
- `REQ-003`: When the services stage is cancelled while the RAG consistency check is running, the RAG stop event is set so the worker thread stops.
- `REQ-004`: Without a shutdown request the startup sequence, outcomes and exceptions are unchanged, and the handling of `StartupInterrupted` in `AgentREPL.run` and `main` is unchanged.
- `REQ-005`: Tests cover each stage, the stage boundaries, the rollback, the quiet exit and the RAG cancellation.
- `REQ-006`: The startup design document states which startup stages observe a shutdown request and what is rolled back, matching the code.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/startup.py | Race the unguarded stages and check the boundaries | Add a private stage helper that races a stage task against `self._shutdown_event`, cancels and awaits the stage on shutdown and raises `StartupInterrupted`; use it for `_check_services` and `_setup_prompt` in `run`; add event checks before the unraced stages and at the end of `run` | REQ-001, REQ-002, REQ-004; AC-1, AC-2, AC-4 | `run` at line 63 calls `_check_config`, `_start_servers`, `_verify_mcp_health`, `_check_services`, `_setup_prompt` in order inside one `try`; `except StartupInterrupted` at line 74; `shutdown_event` is passed only to `McpServerStarter` in `__init__`; 6993 bytes, radon all A or B (checked in Step 3 and Step 5) | `tests/agent/test_startup_rollback.py` | Verified |
| scripts/agent/startup_validation.py | Stop the RAG check on cancellation | In the RAG step of `check_services`, set the RAG stop event (added by Plan 006) when the awaiting coroutine is cancelled, then re-raise the cancellation | REQ-003; AC-3 | The RAG step runs `run_in_executor` under `asyncio.wait_for`; a cancelled await leaves the worker thread running (reproduced for the timeout case in the review; checked in Step 3) | `tests/agent/test_startup_validation.py` | Verified |
| tests/agent/test_startup_rollback.py | Stage interruption tests | Add tests using `_make_rollback_startup`: an event set while `_check_services` blocks, while `_setup_prompt` blocks, between stages, and after the last stage each raise `StartupInterrupted` with `shutdown_all` awaited once and within a short bound; no event leaves the sequence unchanged | REQ-001, REQ-002, REQ-004, REQ-005; AC-1, AC-2, AC-4, AC-5 | `TestStartupRollback` (line 48) holds `test_startup_interrupted_triggers_rollback_like_any_other_exception` (line 261) which mocks `_start_servers` to raise; `_make_rollback_startup` at line 35 builds the orchestrator with a mocked lifecycle (checked in Step 3) | tests/agent/test_startup_rollback.py | Verified |
| tests/agent/test_startup_validation.py | RAG cancellation test | Add a test: cancelling `check_services` while a fake consistency check blocks sets the stop event passed to the fake | REQ-003, REQ-005; AC-3, AC-5 | The file patches `RagMaintenanceService` as `MagicMock(return_value=rag_service)` (lines 66, 222, 352) and drives `check_services` (checked in Step 3) | tests/agent/test_startup_validation.py | Verified |
| docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md | Correct the interruption description | Rewrite the sentence near line 39 and the section "SIGINT/SIGTERM Interruption During Startup" (lines 91-93) to say which startup stages observe a shutdown request, that the stages are cancelled, and that started servers are rolled back before a quiet exit | REQ-006; AC-6 | The section says a `StartupInterrupted` is raised on a signal during startup and names only the HTTP subprocess health polling; the code covered only the MCP start and verify waits (checked in Step 2 and Step 3) | N/A: documentation | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/startup_mcp_starter.py | The existing event-race pattern (`_interruptible_sleep`) and the `StartupInterrupted` raising points to mirror | REQ-001, REQ-002 |
| scripts/agent/repl.py | `AgentREPL.run` and `main` handle `StartupInterrupted`; their behavior must not change | REQ-004 |
| scripts/agent/repl_input_loop.py | `ReplInputLoop.run` prints the banner and starts the session before honoring the flag, which the end-of-`run` check prevents | REQ-002 |
| scripts/agent/signal_handler.py | Sets the shutdown event and the `shutdown_requested` flag; unchanged | REQ-001 |
| scripts/agent/services/rag_maintenance_service.py | After Plan 006 it takes the stop event this Plan sets on cancellation | REQ-003 |

## Acceptance Criteria
- AC-1 (REQ-001): Setting the shutdown event while `_check_services` or `_setup_prompt` blocks ends `run` with `StartupInterrupted` within a short bound, the blocked stage is cancelled, and `shutdown_all` is awaited once.
- AC-2 (REQ-002): Setting the event between stages, or after the last stage, ends `run` with `StartupInterrupted` before the next stage starts and before `run` returns `(cmds, orchestrator)`.
- AC-3 (REQ-003): Cancelling `check_services` while the fake consistency check blocks sets the stop event passed to it.
- AC-4 (REQ-004): With no event set, the stage order, results and exceptions are unchanged; `AgentREPL.run` still warns and re-raises, and `main` still returns quietly.
- AC-5 (REQ-005): `uv run pytest tests/agent/test_startup_rollback.py tests/agent/test_startup_validation.py tests/agent/test_startup.py tests/agent/test_repl.py tests/agent/shared/test_startup_validation_pipeline.py` passes with the new cases, and the stage-interruption tests fail against the pre-change code.
- AC-6 (REQ-006): The startup document names the stages that observe a shutdown request and what is rolled back; `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_content_policy.py` pass.
- AC-7 (REQ-001, REQ-002, REQ-003): `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/` and `PYTHONPATH=scripts uv run lint-imports` pass; `uv run python tools/check_module_size.py` and `uv run python tools/generate_reference_table.py --check` pass.

## Tests
- REQ-001: per-stage tests with a stage coroutine that blocks until cancelled and an event set after a short delay; assert `StartupInterrupted`, the elapsed bound, that the stage saw `CancelledError`, and `shutdown_all` awaited once.
- REQ-002: boundary tests with the event set before a stage and after the last stage; assert the next stage never starts and `run` does not return a result.
- REQ-003: a `check_services` test with a fake consistency check that blocks until its stop event is set; cancel the awaiting task; assert the event was set and the fake returned.
- REQ-004: the existing startup, rollback and repl tests run unchanged and pass.
- REQ-005: write the stage-interruption tests first and confirm they fail on the current code.
- REQ-006: documentation checks listed under AC-6.

## Documentation Impact
`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` must be updated (REQ-006): the section on interruption during startup and the sentence near line 39 are corrected to describe which stages observe a shutdown request, that the stage in progress is cancelled, that started servers are rolled back, and that the process then exits quietly. Policy only: no timeouts, counts or file lists (`skills/DESIGN.md` Docs content policy). `docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md` only links to that section and needs no change.

## Assumptions
- Leaving `ComponentInitializer.initialize` and the config-only stage uninterruptible is acceptable because they are synchronous, bounded and local (no network); a boundary check after each covers a signal that arrives during them. Falsifiable by reading both: neither awaits an external service (Step 3).
- Racing at the orchestrator is preferred to threading the event into every probe: it covers all awaited stages with one mechanism and no signature change to the services; its cost is that a cancelled stage is abandoned rather than finished, which is correct for an abort.
- A fourth copy of the event-race pattern (`_interruptible_sleep` exists in the starter, the retry helper and the health checker) is accepted here to keep this Plan small; consolidating the copies is a separate cleanup and is not planned here.
- Overlap judgment (Step 8b): `tools/check_plan_target_overlaps.py` reports three findings naming this Plan. (1) `scripts/agent/startup_validation.py`, shared with `plans/20261115-220913_startrev005_posture-probed-twice-startup.md` (head of `check_services`) and `plans/20261115-220927_startrev006_rag-check-timeout-executor.md` (RAG step: stop event, named bound): compatible, with a hard order for the RAG step: this Plan adds one cancellation handler to the RAG step and sets the event that Plan 006 introduces, so the order is Plan 005, Plan 006, then this Plan (recorded in Scope Dependencies as a `Depends on` line for Plan 006 phase 2). (2) `tests/agent/test_startup_validation.py`, shared with Plan 006: compatible; Plan 006 adds timeout and stop tests, this Plan adds one cancellation test with the same fake; implement after Plan 006. (3) `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, shared with Plans 005 and 006: compatible; Plan 005 edits the readiness description (line 75), Plan 006 the startup-validation description (line 60), this Plan the interruption passages (line 39 and lines 91-93); no sentence is shared.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether a cancelled `McpToolDiscoveryService.discover_all` can leave a half-published `runtime_tools` that matters after an abort | Reading of the discovery publish order | Startup aborts anyway, so nothing consumes it; confirm while writing the cancellation test | False |
| UNK-02 | Order against `plans/20261115-220927_startrev006_rag-check-timeout-executor.md`, whose Phase 2 adds the stop event that REQ-003 consumes (open sibling Plan; only REQ-003 depends on it, so the Plan as a whole is not blocked) | The stop event existing in the code | Implement Plan 006 Phase 2 before this Plan's REQ-003 step: `plans/20261115-220927_startrev006_rag-check-timeout-executor.md` | False |
| UNK-03 | Order against `plans/20261115-220913_startrev005_posture-probed-twice-startup.md`, which edits the head of `check_services` (open sibling Plan, related, not blocking) | Merge order of edits to one method | Implement Plan 005 first; this Plan edits only the RAG step of `check_services`: `plans/20261115-220913_startrev005_posture-probed-twice-startup.md` | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/startup.py | Modify | High: every agent startup runs through `StartupOrchestrator.run`; behavior changes only when a shutdown request arrives, but a mistake in the race helper would affect every start | 9 | High: one author | not applicable (rsynced): `deploy/deploy.sh` rsyncs `scripts/` |
| scripts/agent/startup_validation.py | Modify | Medium: every agent startup passes through `check_services`; the change adds one cancellation handler in the RAG step | 10 | High: one author | not applicable (rsynced): `deploy/deploy.sh` rsyncs `scripts/` |
| tests/agent/test_startup_rollback.py | Modify | Low: tests only | 8 | High: one author | not applicable (rsynced): `tests/` is not deployed |
| tests/agent/test_startup_validation.py | Modify | Low: tests only | 8 | High: one author | not applicable (rsynced): `tests/` is not deployed |
| docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md | Modify | Low: two passages of one design document | 17 | High: one author | not applicable (rsynced): `docs/` is not deployed |

## Design
- **Design decision (where to race)**: options weighed. (1) Pass the event into the validation pipeline and `PromptSetup` and check it inside every probe and discovery call: rejected, it changes several service signatures and leaves each new probe to remember the check. (2) Check the event only between stages: rejected, a hung probe would still block. (3) Race each awaited stage at the orchestrator and check the boundaries: chosen; one mechanism, no service signature change. Compatibility impact: none without a shutdown request.
- **Cancellation semantics**: when the event wins, the stage task is cancelled and awaited so its `finally` blocks and executor hand-offs run; the resulting `CancelledError` of the stage is swallowed and replaced by `StartupInterrupted`, which `run` already turns into a rollback. An exception raised by the stage at the same moment as the event is not hidden: the event is checked at the next boundary.
- **Architecture analysis**: `lint-imports` reports 6 contracts kept, 0 broken at this commit; `startup.py` already imports `asyncio`; no new import is needed; `StartupInterrupted` stays defined in `startup.py` (checked in Step 5).
- **Dependency graph**: `StartupOrchestrator.run` is called only by `AgentREPL.run`; `_check_services` and `_setup_prompt` are private wrappers over the pipeline and `PromptSetup` (checked in Step 3).
- **Historical analysis**: `startup.py` 9, `startup_validation.py` 10, `test_startup_rollback.py` 8, `test_startup_validation.py` 8, `test_repl.py` 15 and the startup document 17 commits in the last 30 days; one contributor (two spellings of one name) in the last 90 days (checked in Step 5).
- **Operational dependency inspection**: no port or service is touched; the tests use fakes and no real signals (checked in Step 5).
- **Validation quality baseline**: radon: `startup.py` has no method above B (`_finish_validation_stage` B (7)) and `check_services` is C (17); the change adds no branch to `check_services` beyond one handler; vulture and bandit: no finding in the target files; diff-cover baseline: the working tree equals `master`, so the diff has no coverage lines (no current number); baseline test run 12261 passed, 2 failed, 7 skipped, the two failures being the pre-existing posture tests `tests/mcp_servers/test_posture_gate_start_path.py::test_running_the_mdq_entry_module_goes_through_real_run_http` and `tests/mcp_servers/mdq/test_mdq_health_posture.py::TestBindGate::test_validated_posture_does_not_block_bind`, unrelated to this Plan; the Plan must raise diff coverage to the `rules/toolchain.md` threshold.

## Implementation steps
1. **Phase 1: Orchestrator stage race**
   - [ ] Write the stage-interruption and boundary tests first and confirm they fail on the current code (REQ-001, REQ-002, REQ-004, REQ-005; tests/agent/test_startup_rollback.py)
   - [ ] Add the stage helper and the boundary checks, and apply the helper to `_check_services` and `_setup_prompt` (REQ-001, REQ-002, REQ-004; scripts/agent/startup.py)
2. **Phase 2: RAG cancellation** (after Plan 006 Phase 2)
   - [ ] Write the cancellation test with a blocking fake and confirm it fails before the change (REQ-003, REQ-005; tests/agent/test_startup_validation.py)
   - [ ] Set the RAG stop event when the RAG step is cancelled and re-raise (REQ-003; scripts/agent/startup_validation.py)
3. **Phase 3: Documentation**
   - [ ] Correct the interruption description to match the code (REQ-006; docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md)
4. **Phase 4: Deployment & verification**
   - [ ] Run the validation plan; hand off to `skills/deploy/SKILL.md` only after the change is committed and pushed, and deploying is the user's decision (REQ-001, REQ-002, REQ-003; scripts/agent/startup.py, scripts/agent/startup_validation.py)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/startup.py | Unit | `uv run pytest tests/agent/test_startup_rollback.py tests/agent/test_startup.py -q` | New stage and boundary tests pass; existing startup and rollback tests pass |
| scripts/agent/startup_validation.py | Unit | `uv run pytest tests/agent/test_startup_validation.py tests/agent/shared/test_startup_validation_pipeline.py -q` | The RAG cancellation test passes; existing pipeline tests pass |
| AgentREPL and main handling | Unit | `uv run pytest tests/agent/test_repl.py -q` | `StartupInterrupted` handling unchanged |
| Changed Python files | Static | `uv run ruff check scripts/ && uv run mypy --no-namespace-packages scripts/ && PYTHONPATH=scripts uv run lint-imports` | No findings; 6 contracts kept |
| Module size and reference table | Static | `uv run python tools/check_module_size.py && uv run python tools/generate_reference_table.py --check` | No module over its limit; no drift |
| docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md | Documentation | `uv run python tools/check_docs_quality.py && uv run python tools/check_docs_content_policy.py` | No findings |
| Diff coverage | Coverage | `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan"`, then `uv run coverage xml` and `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | At or above the threshold in `rules/toolchain.md` |

## Risks
- **Risk**: A bug in the race helper affects every startup, not only interrupted ones (likelihood low, impact high) → **Mitigation**: the helper is small and the no-event path is covered by the existing startup and rollback tests; a test asserts that a stage completing normally returns its result unchanged.
- **Risk**: A cancelled stage leaves a half-initialized state that something later reads (likelihood low) → **Mitigation**: startup aborts and the rollback plus `close_resources` run on every exit path; UNK-01 is checked while writing the cancellation test.
- **Risk**: The cancelled RAG worker thread keeps running if Plan 006 is not implemented first (likelihood medium if the order is not followed) → **Mitigation**: the `Depends on` line and UNK-02; REQ-003 is implemented in Phase 2 only after Plan 006 Phase 2.
- **Risk**: Four Plans touch `StartupValidationPipeline.check_services` and the startup document (likelihood medium) → **Mitigation**: the implementation order is Plan 005, Plan 006, then this Plan; each edit touches a different part of the method or document.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Orchestrator stage race and its tests (scripts/agent/startup.py, tests/agent/test_startup_rollback.py) | In Progress | — | — |  |
| 2 | RAG cancellation and its test (scripts/agent/startup_validation.py, tests/agent/test_startup_validation.py) | In Progress | — | — |  |
| 3 | Documentation (docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md) | In Progress | — | — |  |
| 4 | Deployment and verification (scripts/agent/startup.py, scripts/agent/startup_validation.py) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261116-095731_01_scripts_agent_startup.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261116-095731_02_scripts_agent_startup_validation.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261116-095731_05_docs_23_agent_agent_10_01_operations-and-observability-startup-and-health.md.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261115-214904_startrev004_startup-ignores-shutdown-signal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-221200
- **Related target files**: scripts/agent/startup.py, scripts/agent/startup_validation.py, tests/agent/test_startup_rollback.py, tests/agent/test_startup_validation.py, docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (2), (3); `StartupOrchestrator.__init__` passes the event only to the starter | scripts/agent/startup.py | Phase 1 | AC-1 | per-stage interruption tests | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes (2); banner and session start before `_should_exit` in `ReplInputLoop.run` | scripts/agent/startup.py | Phase 1 | AC-2 | boundary tests | Confirmed by repository evidence |
| REQ-004 | Issue Constraints (`StartupInterrupted` handling and fail-closed outcomes unchanged) | scripts/agent/startup.py | Phase 1 | AC-4 | existing startup, rollback and repl tests | Explicit in issue |
| REQ-003 | Issue Dependencies (RAG wait abandoned on shutdown needs the stop); Required Changes (3) | scripts/agent/startup_validation.py | Phase 2 | AC-3 | RAG cancellation test | Derived from confirmed evidence |
| REQ-001 | Issue Required Changes (4); Testing Expectations | tests/agent/test_startup_rollback.py | Phase 1 | AC-1, AC-5 | `uv run pytest tests/agent/test_startup_rollback.py -q` | Explicit in issue |
| REQ-002 | Issue Acceptance Criteria (1) | tests/agent/test_startup_rollback.py | Phase 1 | AC-2, AC-5 | boundary tests | Explicit in issue |
| REQ-004 | Issue Acceptance Criteria (2) | tests/agent/test_startup_rollback.py | Phase 1 | AC-4, AC-5 | no-event sequence test | Explicit in issue |
| REQ-005 | Issue Testing Expectations | tests/agent/test_startup_rollback.py | Phase 1 | AC-5 | stage tests fail on the pre-change code | Explicit in issue |
| REQ-003 | Issue Testing Expectations | tests/agent/test_startup_validation.py | Phase 2 | AC-3, AC-5 | RAG cancellation test | Derived from confirmed evidence |
| REQ-005 | Issue Testing Expectations | tests/agent/test_startup_validation.py | Phase 2 | AC-5 | RAG cancellation test fails before the change | Explicit in issue |
| REQ-006 | Issue Documentation Impact; the startup document's claim about interruption (found in Step 2) | docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md | Phase 3 | AC-6 | `check_docs_quality`, `check_docs_content_policy` | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261116-095731 -->