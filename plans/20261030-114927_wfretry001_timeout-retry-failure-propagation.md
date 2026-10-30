# Plan: Define timeout retry eligibility and propagate terminal workflow failure as a failed turn

**Task Classification:** Path B (more than 3 files; changes the workflow definition schema and the adapter / engine interfaces; adds a turn-state field). Path B analysis applied (`skills/issue-to-plan/workflow-path-b.md`); design choices recorded in `Design`.

## Goal
- Make timeout and LLM-failure retry behavior readable from the workflow configuration, and make every terminal workflow failure reach the caller, the task status, and the turn-end audit as the same typed outcome, without relying on an optional callback and without silently repeating side effects.

## Priority
Medium

## Scope
- **In-Scope**: an optional `retry_policy.retry_on` list of error kinds (schema, loader validation, shipped config); distinguishing stage-deadline expiry from an inner `TimeoutError`; retry-budget semantics per kind; typed boundary result with stable kinds `workflow_timeout` / `workflow_halted` from `execute_turn`; LLM-level failure results routed through the engine; removal of the `completed` then `failed` overwrite; a per-attempt side-effect flag and the retry rule built on it; tests; the `agent_03_03` passages.
- **Out-of-Scope**: stale recovery and leases (`plans/20261030-114516_wflease001_stale-attempt-lease.md`); attempt-number persistence, ledger, and transition validation (`plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md`); HTTP-transport retries inside one tool call; MCP-side deduplication (`plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md`); redesigning REPL error presentation; changing the shipped retry behavior for timeouts (defaults keep today's behavior).
- **Dependencies**: (1) Follows `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` Phase 4 (engine uses persisted attempt numbers and budget); the retry loop edits here assume that contract. (2) Related: `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md` bounds when a side-effecting call can be replayed; the side-effect rule here is conservative until that protocol lands. (3) Shared files with other Frozen Plans: see Assumptions.

## Background
- `WorkflowEngine._run_stage_with_retry()` (`scripts/agent/workflow/workflow_engine.py:134-181`) re-raises `WorkflowTimeoutError` before the generic handler, so a timeout never consumes the retry budget; `run()` writes task status `halted` for both timeout and halt; other exceptions retry up to `max_attempts` and then raise `WorkflowHaltError` (checked in Step 3).
- `_run_stage` (`:188-256`) uses `asyncio.wait_for(fn(), timeout)` and `except TimeoutError` (`:224`); on Python 3.13.5 (`asyncio.TimeoutError` is the builtin) an inner `TimeoutError` raised by the stage is caught the same way and labeled a stage timeout (reproduced in Step 2).
- `WorkflowEngineAdapter.execute_turn()` (`scripts/agent/workflow_engine_adapter.py:149-222`) catches `(WorkflowHaltError, WorkflowTimeoutError)`, calls `_handle_workflow_halt` (`:303-308`, `on_error` only if supplied), and returns the initial `("", None, False)`; `Orchestrator._execute_turn` (`orchestrator.py:166-200`) forwards that `error_kind` to `emit_turn_end`, so the audit records no error. Production supplies the callback (`startup_component_init.py:77-81`, `on_error=self._view.write_llm_error`), which is the only outward signal (checked in Step 3).
- `_run_execute_stage` (`:327-375`) converts `result.action != "continue"` into an `error_kind` return without raising, so the engine records a completed attempt and writes `completed`, and `_status_for_exit` (`:49-59`) then overwrites it with `failed`.
- `config/workflows/default.json`: `execute` is `retryable: true`, `timeout_sec: 120`; `retry_policy` is `max_attempts: 3`, `backoff_sec: 1`; `plan` and `verify` are not retryable. `workflow_loader._validate` (`workflow_loader.py:56-96`, radon grade C 18) checks required keys and ignores unknown ones; `deploy/setup_services.sh` validates the deployed definition with `python -m agent.workflow.validate`.
- No per-attempt side-effect record exists: `tool_runner.py:155-157` branches on `OperationType.READ` but `TurnState` (`context.py:213-226`) has no flag.

## Problem
Timeout retry behavior cannot be read from configuration; a halted or timed-out turn returns an empty answer with no `error_kind` and is indistinguishable in the audit from an empty answer; task status, audit, and result disagree for one outcome; retried attempts can repeat side effects.

## Reason for Change
Retry eligibility and outward failure reporting are one contract; operators cannot tell whether work was retried, exhausted, or reported as success, and the production user notice depends solely on an optional callback. Medium: it affects diagnosability and the reported outcome, not stored task data.

## Implementation Intent
- Retry eligibility is configuration per error kind; the shipped values keep today's behavior (exceptions retried; timeouts and LLM-failure results terminal), so the change makes behavior explicit before anyone changes it.
- The boundary contract for every terminal failure is the typed result `(answer, error_kind, is_partial)` the orchestrator already forwards to the audit; internally the engine routes failures by exception so status writes and retry logic stay in one place.
- The task status is written once, by the engine; the adapter writes only what the engine cannot observe (cancellation).
- A retry never follows a completed non-READ tool call in the same attempt.
- `on_error` stays an observational notification.

## Requirements
- `REQ-001`: Add an optional `retry_policy.retry_on` (list drawn from `exception`, `timeout`, `llm_failure`; default `["exception"]`) to `RetryPolicy`, the loader (validation in a separate helper; unknown kinds rejected with `WorkflowLoadError`), and the shipped `config/workflows/default.json` (explicit `["exception"]`); an absent key loads with the default; deployed older loaders ignore it.
- `REQ-002`: Distinguish expiry of the stage deadline from a `TimeoutError` raised inside the stage callback (use the deadline's `expired()` state); only the former is kind `timeout`, the latter is kind `exception`.
- `REQ-003`: Retry semantics: every failed attempt consumes one unit of `max_attempts`; a failed attempt whose kind is not in `retry_on` is terminal at once; an eligible kind retries until the budget is exhausted and then halts; the shipped configuration is pinned by a test (timeout not retried, exception retried).
- `REQ-004`: `execute_turn()` returns a typed failure for a halted or timed-out workflow: `error_kind` `workflow_halted` or `workflow_timeout`, with and without `on_error`; the orchestrator's turn-end audit therefore carries it; `on_error` is still called as before and never carries the sole signal.
- `REQ-005`: An LLM-level failure result (`result.action != "continue"`) enters the engine as a stage failure of kind `llm_failure` carrying the answer, partial flag, and result `error_kind`; it is retried only when `retry_on` includes `llm_failure`; terminal, the engine writes `failed` once and the adapter returns the same outward `error_kind` as today; the `completed` then `failed` overwrite is removed.
- `REQ-006`: Add a per-attempt side-effect flag to `TurnState`, set by `tool_runner` before any non-READ tool call executes (the classification is hoisted above the gateway branch of `_execute_prepared_call`, which returns at `tool_runner.py:153` before `classify_operation_type` runs at `:155`, so production calls through the gateway would otherwise never set it) and cleared at each attempt start; when an attempt fails with the flag set, retry is suppressed and the failure is terminal (`workflow_halted`), regardless of `retry_on`.
- `REQ-007`: Attempt-level `error_kind` values persisted in `attempts` keep `timeout` and `exception` and gain `llm_failure`; the outward turn kinds `workflow_timeout` and `workflow_halted` are distinct from them.
- `REQ-008`: No turn ends with an empty answer, `error_kind` `None`, and a task status of `halted` or `failed`; a test enforces the invariant for halt, timeout, LLM failure, and cancellation paths.
- `REQ-009`: Tests: engine (timeout then success when configured, timeout exhaustion, exception exhaustion, non-retryable kind, inner `TimeoutError`, LLM-failure result, side-effect suppression), adapter and orchestrator (halt and timeout with and without callback; returned tuple, task status, turn-end audit), loader (valid, absent, unknown kinds), tool runner (flag), and the rewritten `test_timeout_raises_workflow_timeout_error`.
- `REQ-010`: Update the `agent_03_03` "Task Status Transitions" table, "Retry Mechanism", and Operational Notes; record unresolved owner decisions as Needs Confirmation items.
- `REQ-011`: Deployment compatibility: the new policy field is optional, the deployed `/opt/llm/config/workflows/default.json` is updated by the normal config sync, and the pre-flight `python -m agent.workflow.validate` passes on it.

## Implementation Target Files
**Freeze status**: Frozen (Step 8 Implementation Target Files Validation passed on 2026-10-30: every row exists, requires modification, cites checkable evidence, and links to a Requirement; existing paths confirmed on branch `docs/issues-workflow-persistence`).

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/workflow/workflow_engine.py` | Retry eligibility by kind, deadline-versus-inner timeout, stage-failure routing, terminal kinds | `except WorkflowTimeoutError: raise` bypasses the budget; `except TimeoutError` conflates inner timeouts | REQ-002, REQ-003, REQ-005, REQ-006, REQ-007 / AC-2, AC-3, AC-5, AC-6 | `workflow_engine.py:134-181,188-256` (checked in Step 3) | `tests/agent/workflow/test_workflow_engine.py` | Verified |
| `scripts/agent/workflow/models.py` | `RetryPolicy.retry_on` | Policy has only `max_attempts`, `backoff_sec` | REQ-001 / AC-1 | `models.py:61-67` (checked in Step 3) | `tests/agent/workflow/test_workflow_loader.py` | Verified |
| `scripts/agent/workflow/workflow_loader.py` | Parse and validate `retry_on` in a helper | `_validate` ignores unknown keys; grade C (18) | REQ-001 / AC-1 | `workflow_loader.py:47-48,56-96` (checked in Step 3) | `tests/agent/workflow/test_workflow_loader.py` | Verified |
| `config/workflows/default.json` | Explicit shipped `retry_on` | Shipped behavior must be readable from configuration | REQ-001, REQ-003, REQ-011 / AC-1, AC-3, AC-9 | `default.json:6-24` (checked in Step 3) | `tests/agent/workflow/test_workflow_loader.py` | Verified |
| `scripts/agent/workflow_engine_adapter.py` | Typed failure result, stage failure from `_run_execute_stage`, attempt flag reset, status writes limited to cancellation | Halt returns `("", None, False)`; completed-then-failed overwrite | REQ-004, REQ-005, REQ-006, REQ-008 / AC-4, AC-5, AC-6, AC-8 | `workflow_engine_adapter.py:49-59,149-222,303-308,327-375` (checked in Step 3) | `tests/agent/test_orchestrator.py` | Verified |
| `scripts/agent/context.py` | `TurnState` side-effect flag | No per-attempt side-effect record exists | REQ-006 / AC-6 | `context.py:213-226` (checked in Step 3) | `tests/agent/test_tool_runner.py` | Verified |
| `scripts/agent/tool_runner.py` | Set the flag before a non-READ call executes, ahead of the gateway branch | Classification happens only in the no-gateway branch (`:155`); the gateway branch returns first (`:151-153`), and production always has a gateway | REQ-006 / AC-6 | `tool_runner.py:134-166` (`op != OperationType.READ` at `:156`) (checked in Step 3) | `tests/agent/test_tool_runner.py` | Verified |
| `tests/agent/workflow/test_workflow_engine.py` | Engine tests; rewrite the timeout test | Existing test accepts either exception type | REQ-002, REQ-003, REQ-005, REQ-006, REQ-009 / AC-2, AC-3, AC-5, AC-6 | `test_workflow_engine.py:161-185` (checked in Step 3) | itself | Verified |
| `tests/agent/workflow/test_workflow_loader.py` | `retry_on` loader tests | Loader tests cover required keys only | REQ-001, REQ-009 / AC-1 | `test_workflow_loader.py` (churn 3 in 30 days; exists) (checked in Step 3) | itself | Verified |
| `tests/agent/test_orchestrator.py` | Halt and timeout outcome, callback present and absent, status and audit | Halt tests assert status only (`:667,764`) | REQ-004, REQ-005, REQ-008, REQ-009 / AC-4, AC-5, AC-8 | `test_orchestrator.py:667,764,2627-2765` (checked in Step 3) | itself | Verified |
| `tests/agent/test_tool_runner.py` | Flag set for non-READ calls only | No flag exists | REQ-006, REQ-009 / AC-6 | `test_tool_runner.py` (exists; churn 11) (checked in Step 3) | itself | Verified |
| `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Transitions table, retry mechanism, operational notes | Describe today's timeout-not-retried behavior | REQ-010 / AC-10 | `agent_03_03_...md:74-94,119-129,149-150` (checked in Step 3) | docs checkers | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. No directory, glob, component name, file group, or vague phrase appears as a row.
- A test, configuration, schema, migration, deployment, or documentation file is its own row when it requires modification.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section is `Frozen`.

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/orchestrator.py` | `_execute_turn` forwards `error_kind` to `emit_turn_end` (`:166-200`); unchanged | REQ-004 |
| `scripts/agent/audit_event_emitter.py` | `turn_end` event carries `error_kind` (`:105-140`) | REQ-004 |
| `scripts/agent/startup_component_init.py` | Production `on_error` wiring (`:77-81`) | REQ-004 |
| `scripts/agent/cli_view.py` | `write_llm_error` target of the callback (`:169`) | REQ-004 |
| `scripts/agent/tool_policy.py` | `classify_operation_type` and `OperationType` used for the flag | REQ-006 |
| `scripts/agent/workflow/validate.py` | Pre-flight validation entry run by deploy (`python -m agent.workflow.validate`) | REQ-011 |
| `deploy/setup_services.sh` | Runs the workflow definition validation before start | REQ-011 |
| `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` | Attempt and status contract this Plan builds on | REQ-003, REQ-005 |
| `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md` | Replay protocol that may later relax the side-effect rule | REQ-006 |

## Acceptance Criteria
- AC-1 (REQ-001): the shipped `default.json` carries `retry_on`; a definition without the key loads with the default `["exception"]`; an unknown kind raises `WorkflowLoadError`.
- AC-2 (REQ-002): a stage callback that raises `TimeoutError` records kind `exception`; a callback exceeding `timeout_sec` records kind `timeout`.
- AC-3 (REQ-003, REQ-001): with the shipped configuration a timed-out execute stage is not retried and an exception is retried up to `max_attempts`; with `retry_on` including `timeout` the timeout consumes the budget identically; each case is pinned by a test.
- AC-4 (REQ-004): a halted and a timed-out turn each return `error_kind` `workflow_halted` / `workflow_timeout`, the turn-end audit event carries it, and the same holds with `on_error=None`; with a callback it is called once.
- AC-5 (REQ-005): an LLM-level failure result ends with task status `failed` written once (no `completed` write), the same outward `error_kind` as before, and is retried only when `llm_failure` is in `retry_on`.
- AC-6 (REQ-006): after a non-READ tool call executed in the attempt, a failure is terminal with `workflow_halted` and no retry occurs even when the kind is in `retry_on`; READ-only attempts retry normally; the flag is cleared at each attempt start.
- AC-7 (REQ-007): persisted attempt rows use `timeout`, `exception`, or `llm_failure`; outward kinds are not written to `attempts.error_kind`.
- AC-8 (REQ-008): the invariant test finds no turn with empty answer, `error_kind` `None`, and task status `halted` or `failed` across halt, timeout, LLM failure, and cancellation.
- AC-9 (REQ-011): `python -m agent.workflow.validate` passes on the shipped `default.json`, and an older-format file (without `retry_on`) still validates.
- AC-10 (REQ-010): the `agent_03_03` passages describe the implemented policy and contract and pass the docs checkers.

## Tests
- `REQ-001`, `REQ-011`: `tests/agent/workflow/test_workflow_loader.py` (valid, absent, unknown kinds; shipped file).
- `REQ-002`, `REQ-003`, `REQ-005`, `REQ-006`, `REQ-007`: `tests/agent/workflow/test_workflow_engine.py` (timeout then success, exhaustion, non-retryable kind, inner `TimeoutError`, LLM-failure result, side-effect suppression).
- `REQ-004`, `REQ-005`, `REQ-008`: `tests/agent/test_orchestrator.py` (returned tuple, task status, turn-end audit, with and without callback; invariant).
- `REQ-006`: `tests/agent/test_tool_runner.py` (flag for non-READ calls only).
- `REQ-010`: docs checkers.

## Documentation Impact
Yes: `REQ-010`. `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` (located through `docs/00_index.md` "Document References by Task"): the Task Status Transitions table, the Retry Mechanism section, and the Operational Notes bullet on `halted`; intent and failure behavior only, no code restatement. `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` decision 6 stays true under the shipped configuration and is not a target; amend it (ADR change protocol) only if the owner changes the outcome. UNK-01 and UNK-02 are settled by the owner, so no Needs Confirmation item is required for them.

## Assumptions
- The owner chose on 2026-10-30 to keep today's retry behavior (UNK-01, UNK-02); the defaults preserve it, and `retry_on` can be changed later by configuration.
- The side-effect rule treats every non-READ operation, including unclassified ones, as a side effect (conservative) until the toolexec001 replay protocol exists (UNK-06).
- Step 8b overlap judgments (`tools/check_plan_target_overlaps.py`, 2026-10-30), one per reported file: `scripts/agent/workflow/workflow_engine.py` with wfrecovery001, wflease001, toolexec001: sequencing dependency (wfrecovery001 changes the claim and attempt numbering in `run()` and the retry loop; wflease001 passes the lease at attempt start; toolexec001 adds pending-call detection at turn entry; this Plan changes eligibility, timeout classification, and failure routing in the same functions; the designs do not contradict, this Plan lands after wfrecovery001 Phase 4 and rebases on the others). `scripts/agent/workflow/models.py` with wftaskapi001 and wfrecovery001: sequencing dependency (key rename and status enums versus a new `RetryPolicy` field; distinct dataclasses, no contradiction). `scripts/agent/workflow_engine_adapter.py` with wfrecovery001: sequencing dependency (wfrecovery001 aligns the resume guard with the transition API and passes the attempt number to the audit; this Plan changes the failure return, stage-failure raising, and status writes; the two edit different methods of `execute_turn` and `_run_execute_stage`, and the later change rebases). `tests/agent/workflow/test_workflow_engine.py` with toolexec001, wftaskapi001, wfrecovery001, wflease001: compatible (additive tests in different classes). `tests/agent/test_orchestrator.py` with wfrecovery001 and turnadr001: compatible (status-write and resume tests, halt-outcome tests, and a guard test are in different regions). `docs/23_agent/agent_03_03_...md` with wfrecovery001 and wflease001: sequencing dependency (different sections: state semantics and resume, startup recovery, and retry and transitions here; the transitions table is edited by both wfrecovery001 and this Plan, so the later change reconciles the rows).
- Verification record (second pass, 2026-10-30): no Implementation Target Files row changed on `origin/master` since the merge base; every `path:line` citation lies within its file; on Python 3.13.5 `asyncio.timeout()` reports `expired()` false for an inner `TimeoutError` and true when the deadline fires (tested); `classify_operation_type` returns `UNKNOWN` (non-READ) for unregistered tools and when no registry is given, so the conservative side-effect assumption holds; `workflow_loader._validate` ignores unknown keys, so older deployed loaders accept `retry_on`.
- The wfrecovery001 matrix keeps a transitional `completed -> failed` edge; this Plan's REQ-005 makes it unused, and that edge is removed in a follow-up edit of the wfrecovery001 implementation or after it lands.
- `Orchestrator`, `startup_component_init.py`, and `cli_view.py` need no change because the adapter returns the error kind and the existing callback wiring remains (checked in Step 3).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | (Decided by the owner on 2026-10-30) Stage timeouts are not retried by default | Resolved: the owner chose to keep today's behavior | `retry_on` excludes `timeout`; one config edit flips it later | False |
| UNK-02 | (Decided by the owner on 2026-10-30) LLM-level failure results are not retried by default | Resolved: the owner chose to keep today's behavior | `retry_on` excludes `llm_failure`; one config edit flips it later | False |
| UNK-03 | How the view port renders `write_llm_error` versus a returned `error_kind` | `error_kind` has no consumer in `repl.py` or `cli_view.py`; view port not read | Keep the existing callback display; no new rendering; revisit if a duplicate notice is observed | False |
| UNK-04 | Owner preference between a typed failure result and exception propagation as the single mechanism | Not recorded | Default: typed result at the boundary, exception routing inside the engine (Design) | False |
| UNK-05 | Landing order against wfrecovery001 | That Plan's rows are Pending | Open dependency `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md`; this Plan starts after its Phase 4 | False |
| UNK-06 | Whether the toolexec001 replay protocol will let retries follow side effects | That Plan's rows are Pending | Open dependency `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md`; the conservative rule stays until it lands | False |
| UNK-07 | Whether production stage callbacks ever raise an inner `TimeoutError` | Not shown by current evidence | REQ-002 makes the classification correct either way | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/workflow/workflow_engine.py` | Modify | High: 54 test references in 3 files | 1 | High (single contributor) | not applicable (rsynced) |
| `scripts/agent/workflow/models.py` | Modify | Medium | 1 | High (single contributor) | not applicable (rsynced) |
| `scripts/agent/workflow/workflow_loader.py` | Modify | Medium: deploy pre-flight uses it; grade C (18) | 3 | High (single contributor) | not applicable (rsynced) |
| `config/workflows/default.json` | Modify | Medium: read by deploy pre-flight | 2 | High (single contributor) | not applicable (rsynced) |
| `scripts/agent/workflow_engine_adapter.py` | Modify | High: turn path; 15702 B of the 20480 B module-size limit | 7 | High (single contributor) | not applicable (rsynced) |
| `scripts/agent/context.py` | Modify | High: shared context dataclasses | 12 | High (single contributor) | not applicable (rsynced) |
| `scripts/agent/tool_runner.py` | Modify | Medium | 9 | High (single contributor) | not applicable (rsynced) |
| `tests/agent/workflow/test_workflow_engine.py` | Modify | Low | 2 | High (single contributor) | not applicable (rsynced) |
| `tests/agent/workflow/test_workflow_loader.py` | Modify | Low | 3 | High (single contributor) | not applicable (rsynced) |
| `tests/agent/test_orchestrator.py` | Modify | Medium | 14 | High (single contributor) | not applicable (rsynced) |
| `tests/agent/test_tool_runner.py` | Modify | Low | 11 | High (single contributor) | not applicable (rsynced) |
| `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Modify | Low | 23 | High (single contributor) | not applicable (rsynced) |

## Design
- **Retry policy.** Alternatives: (a) per-kind `retry_on` list with defaults equal to today's behavior; (b) a boolean `retry_timeouts`. Chosen (a): it also covers `llm_failure` and later kinds without more booleans. The stage-level `retryable` stays the outer gate. Compatibility: an absent key means `["exception"]`; already-deployed loaders ignore unknown keys, so the config can ship before or with the code.
- **Budget.** Every failed attempt consumes one unit; ineligible kinds are terminal immediately rather than consuming the remainder, so exhaustion always means "retried and still failing". The persisted attempt count from wfrecovery001 is the counter.
- **Timeout classification.** Alternatives: keep `wait_for` and compare elapsed time; use `asyncio.timeout()` and its `expired()` state. Chosen the latter: it answers directly whether the deadline fired, without clocks.
- **Failure mechanism.** Alternatives: (a) return-value failures everywhere; (b) exceptions everywhere; (c) exception routing inside the engine and the existing typed tuple at the adapter boundary. Chosen (c): the engine keeps retry and status writes in one place, and the orchestrator and audit already consume the tuple, so no new caller contract is invented. An LLM-level failure becomes a stage failure inside the engine (so it can be retried by policy and fails the task once) and is converted back to the tuple by the adapter.
- **Outward kinds.** `workflow_timeout` and `workflow_halted` are turn-level and are not written to `attempts.error_kind`; attempt-level kinds stay `timeout`, `exception`, and the new `llm_failure`, so retained rows and tests keep their meaning.
- **Terminal exceptions that are not retried.** An exception whose kind is not in `retry_on` takes the same path as an exception from a non-retryable stage today: the original exception propagates, the engine writes `failed`, and the orchestrator records the exception class name as `error_kind`; `workflow_halted` is reserved for budget exhaustion and the side-effect rule. The `stage_completed` audit event that `_run_execute_stage` emits before returning stays emitted before a stage failure is raised, so existing audit consumers see the same event for a failed stage.
- **Side effects.** A boolean on `TurnState` is set by `tool_runner` when a non-READ call is about to run and cleared at each attempt start; a failure with the flag set is wrapped as non-retryable. Alternative (tracking tool call IDs per attempt) is heavier and not needed for a yes/no rule.
- **Layering.** `workflow_engine.py` stays free of agent-layer imports; the flag lives on `TurnState` and is read in the adapter; `lint-imports` baseline 6 kept, 0 broken (2026-10-30).

## Implementation steps
1. **Phase 1: Policy schema and loader**
   - [ ] Add `retry_on` to `RetryPolicy`, validate it in a separate loader helper, and make the shipped config explicit (REQ-001, REQ-011; `scripts/agent/workflow/models.py`, `scripts/agent/workflow/workflow_loader.py`, `config/workflows/default.json`).
   - [ ] Loader tests and the shipped-file check (REQ-001, REQ-009; `tests/agent/workflow/test_workflow_loader.py`).
2. **Phase 2: Engine semantics (after wfrecovery001 Phase 4)**
   - [ ] Deadline-versus-inner timeout classification, retry eligibility by kind, budget semantics, stage-failure routing, attempt kinds (REQ-002, REQ-003, REQ-005, REQ-007; `scripts/agent/workflow/workflow_engine.py`).
   - [ ] Engine tests including the rewritten timeout test (REQ-002, REQ-003, REQ-009; `tests/agent/workflow/test_workflow_engine.py`).
3. **Phase 3: Side-effect rule**
   - [ ] Add the `TurnState` flag and set it before non-READ calls (REQ-006; `scripts/agent/context.py`, `scripts/agent/tool_runner.py`).
   - [ ] Tool runner tests (REQ-006, REQ-009; `tests/agent/test_tool_runner.py`).
4. **Phase 4: Boundary contract**
   - [ ] Return typed kinds for halt and timeout, route LLM-failure results through the engine, reset the flag per attempt, limit status writes to cancellation (REQ-004, REQ-005, REQ-006, REQ-008; `scripts/agent/workflow_engine_adapter.py`).
   - [ ] Adapter and orchestrator tests with and without callback, status and audit alignment, invariant (REQ-004, REQ-005, REQ-008, REQ-009; `tests/agent/test_orchestrator.py`).
5. **Phase 5: Documentation**
   - [ ] Update the transitions table, retry mechanism, and operational notes (REQ-010; `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`); run the docs checkers.
6. **Phase 6: Deployment & Verification**
   - [ ] Hand off to `skills/deploy/SKILL.md` after the change is committed and pushed; deploying is the user's decision (approval gate). Prerequisite: the deployed `config/workflows/default.json` is synced; verify with `python -m agent.workflow.validate` and the pre-flight in `deploy/setup_services.sh` (REQ-011; `config/workflows/default.json`).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/workflow/` | Unit: loader, retry semantics, classification | `uv run pytest tests/agent/workflow/ -v` | All pass; new tests fail on the pre-change code |
| Adapter, orchestrator, tool runner | Integration: outcome, status, audit | `uv run pytest tests/agent/test_orchestrator.py tests/agent/test_tool_runner.py tests/integration/test_orchestrator_integration.py -v` | All pass |
| Shipped definition | Static | `PYTHONPATH=scripts uv run python -m agent.workflow.validate config/workflows/default.json` | Pass |
| Source quality | Static | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`, `uv run radon cc scripts/agent/workflow/workflow_loader.py -s -n C` | Clean; 6 contracts kept; adapter under 20480 B; loader complexity not above the recorded C (18) |
| Changed-line coverage | Coverage | `uv run coverage run -m pytest tests/`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | at least 90% (baseline without threshold: no covered lines in the current diff, which contains only documents) |
| Generated reference | Static | `uv run python tools/generate_reference_table.py --check` | `No drift found` |
| `docs/` | Static | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain agent`, `check_docs_japanese.py` | Pass |

Baselines recorded 2026-10-30: radon (grade C or worse in the scanned set): `workflow_loader._validate` C (18), `workflow_engine_adapter._run_execute_stage` C (11). vulture: 16 findings, none in these files. bandit: 0 medium or high repository-wide (51 low). Operational check: production database locks (`fuser`) not run; planning does not touch `/opt/llm/` (`rules/ai-execution.md` Repository Tool Usage item 7); `pip-audit` not applicable (no dependency change).

## Risks
- **Risk**: the side-effect rule changes today's behavior (an exception after a non-READ tool call is currently retried) → **Mitigation**: stated as intended in Scope and docs; AC-6 pins it; the conservative rule relaxes only when the toolexec001 protocol lands.
- **Risk**: routing LLM-level failures through the engine changes status and attempt rows for those turns (attempt `failed` with `llm_failure`, task `failed` written once) → **Mitigation**: outward `error_kind` and final task status are unchanged (`failed`); tests assert both; attempt rows are the only new observable.
- **Risk**: loader complexity grows beyond grade C (18) → **Mitigation**: validation in a separate helper; radon gate in the Validation plan.
- **Risk**: wide blast radius (`WorkflowEngine` 54 references in 3 test files, `WorkflowHaltError` 28 in 3, `WorkflowTimeoutError` 16 in 2; `context.py` 12 and `tool_runner.py` 9 commits in 30 days) exceeds the `rules/toolchain.md` Impact-radius threshold; recorded here → **Mitigation**: defaults preserve behavior; exception class names are kept; each phase leaves the suite green.
- **Risk**: a rolling deploy with the new config but an older code version → **Mitigation**: older loaders ignore the unknown key (checked in Step 3); the key is optional.
- **Risk**: adapter module growth toward the 20480 B size gate (15702 B) → **Mitigation**: failure-mapping helpers live in `workflow_engine.py`; `check_module_size.py` in the Validation plan.
- **Risk**: single-contributor files (bus factor High) → **Mitigation**: small, independently revertable phases.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Policy schema and loader | Pending | — | — | Independent |
| 2 | Phase 2: Engine semantics | Pending | — | — | After wfrecovery001 Phase 4 |
| 3 | Phase 3: Side-effect rule | Pending | — | — | |
| 4 | Phase 4: Boundary contract | Pending | — | — | |
| 5 | Phase 5: Documentation | Pending | — | — | |
| 6 | Phase 6: Deployment & Verification | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261030-114927
- **Related target files**: `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/workflow/models.py`, `scripts/agent/workflow/workflow_loader.py`, `config/workflows/default.json`, `scripts/agent/workflow_engine_adapter.py`, `scripts/agent/context.py`, `scripts/agent/tool_runner.py`, `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/workflow/test_workflow_loader.py`, `tests/agent/test_orchestrator.py`, `tests/agent/test_tool_runner.py`, `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 3; Constraints 1 | `scripts/agent/workflow/models.py` | Phase 1 | AC-1 | `tests/agent/workflow/test_workflow_loader.py` | Derived from confirmed evidence |
| REQ-001 | Required Changes 3; Constraints 1 | `scripts/agent/workflow/workflow_loader.py` | Phase 1 | AC-1 | `tests/agent/workflow/test_workflow_loader.py` | Confirmed by repository evidence |
| REQ-001 | Acceptance Criteria 1 | `config/workflows/default.json` | Phase 1 | AC-1, AC-3 | `tests/agent/workflow/test_workflow_loader.py` | Confirmed by repository evidence |
| REQ-001 | Testing Expectations 4 | `tests/agent/workflow/test_workflow_loader.py` | Phase 1 | AC-1 | `uv run pytest tests/agent/workflow/` | Explicit in issue |
| REQ-002 | Required Changes 1; Background (verification) | `scripts/agent/workflow/workflow_engine.py` | Phase 2 | AC-2 | `tests/agent/workflow/test_workflow_engine.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes 2; Acceptance Criteria 1-2 | `scripts/agent/workflow/workflow_engine.py` | Phase 2 | AC-3 | `tests/agent/workflow/test_workflow_engine.py` | Derived from confirmed evidence |
| REQ-003 | Acceptance Criteria 1 | `tests/agent/workflow/test_workflow_engine.py` | Phase 2 | AC-3 | `uv run pytest tests/agent/workflow/` | Explicit in issue |
| REQ-004 | Required Changes 5-6; Acceptance Criteria 3-4 | `scripts/agent/workflow_engine_adapter.py` | Phase 4 | AC-4 | `tests/agent/test_orchestrator.py` | Confirmed by repository evidence |
| REQ-004 | Testing Expectations 2 | `tests/agent/test_orchestrator.py` | Phase 4 | AC-4 | `uv run pytest tests/agent/test_orchestrator.py` | Explicit in issue |
| REQ-005 | Required Changes 4, 8; Background (second channel) | `scripts/agent/workflow/workflow_engine.py` | Phase 2 | AC-5 | `tests/agent/workflow/test_workflow_engine.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes 4, 8 | `scripts/agent/workflow_engine_adapter.py` | Phase 4 | AC-5 | `tests/agent/test_orchestrator.py` | Confirmed by repository evidence |
| REQ-005 | Testing Expectations 1 | `tests/agent/workflow/test_workflow_engine.py` | Phase 2 | AC-5 | `uv run pytest tests/agent/workflow/` | Explicit in issue |
| REQ-005 | Testing Expectations 2 | `tests/agent/test_orchestrator.py` | Phase 4 | AC-5 | `uv run pytest tests/agent/test_orchestrator.py` | Explicit in issue |
| REQ-006 | Required Changes 7; Acceptance Criteria 5 | `scripts/agent/context.py` | Phase 3 | AC-6 | `tests/agent/test_tool_runner.py` | Derived from confirmed evidence |
| REQ-006 | Required Changes 7 | `scripts/agent/tool_runner.py` | Phase 3 | AC-6 | `tests/agent/test_tool_runner.py` | Derived from confirmed evidence |
| REQ-006 | Required Changes 7 | `scripts/agent/workflow/workflow_engine.py` | Phase 2 | AC-6 | `tests/agent/workflow/test_workflow_engine.py` | Derived from confirmed evidence |
| REQ-006 | Required Changes 7 | `scripts/agent/workflow_engine_adapter.py` | Phase 4 | AC-6 | `tests/agent/test_orchestrator.py` | Derived from confirmed evidence |
| REQ-006 | Testing Expectations 3 | `tests/agent/test_tool_runner.py` | Phase 3 | AC-6 | `uv run pytest tests/agent/test_tool_runner.py` | Explicit in issue |
| REQ-007 | Required Changes 5; Background (error kinds) | `scripts/agent/workflow/workflow_engine.py` | Phase 2 | AC-7 | `tests/agent/workflow/test_workflow_engine.py` | Confirmed by repository evidence |
| REQ-008 | Acceptance Criteria 6 | `scripts/agent/workflow_engine_adapter.py` | Phase 4 | AC-8 | `tests/agent/test_orchestrator.py` | Explicit in issue |
| REQ-008 | Acceptance Criteria 6 | `tests/agent/test_orchestrator.py` | Phase 4 | AC-8 | `uv run pytest tests/agent/test_orchestrator.py` | Explicit in issue |
| REQ-009 | Testing Expectations; Required Changes (test rewrite) | `tests/agent/workflow/test_workflow_engine.py` | Phase 2 | AC-2, AC-3, AC-5, AC-6 | `uv run pytest tests/agent/workflow/` | Explicit in issue |
| REQ-009 | Testing Expectations 2 | `tests/agent/test_orchestrator.py` | Phase 4 | AC-4, AC-5, AC-8 | `uv run pytest tests/agent/test_orchestrator.py` | Explicit in issue |
| REQ-010 | Documentation Impact | `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Phase 5 | AC-10 | docs checkers | Confirmed by repository evidence |
| REQ-011 | Constraints 1; Background (loader) | `config/workflows/default.json` | Phase 1, Phase 6 | AC-9 | `python -m agent.workflow.validate` | Confirmed by repository evidence |
| REQ-011 | Constraints 1 | `scripts/agent/workflow/workflow_loader.py` | Phase 1 | AC-9 | `python -m agent.workflow.validate` | Confirmed by repository evidence |
