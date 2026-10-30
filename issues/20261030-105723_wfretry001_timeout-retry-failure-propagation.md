# Define timeout retry eligibility and propagate terminal workflow failure as a failed turn

## Priority
Medium

## Summary
The execute stage is marked retryable, but a stage timeout is never retried, and a halted or timed-out workflow returns to the caller as a normal turn with an empty answer and no `error_kind`. Define retry eligibility by error kind, and carry every terminal workflow failure through one typed contract that drives task status, turn-end audit, and user-visible output.

## Background
Source: `memo-issue.md` entry M-02 (consolidating M-03 and M-04). Re-checked against current source on 2026-10-30:

- Confirmed: `config/workflows/default.json` sets `execute` to `retryable: true`, `timeout_sec: 120`, with `retry_policy.max_attempts: 3`, `backoff_sec: 1`; `plan` and `verify` are `retryable: false`.
- Confirmed: in `WorkflowEngine._run_stage_with_retry()` (`scripts/agent/workflow/workflow_engine.py`) `except WorkflowTimeoutError: raise` precedes the generic handler, so a timeout never consumes the retry budget; `WorkflowEngine.run()` then writes task status `halted` and re-raises. Other exceptions are retried up to `max_attempts` and then raise `WorkflowHaltError`, also written as `halted`.
- Confirmed: `WorkflowEngineAdapter.execute_turn()` (`scripts/agent/workflow_engine_adapter.py`) catches `(WorkflowHaltError, WorkflowTimeoutError)`, calls `_handle_workflow_halt()` (logs, and calls `on_error` only if one was supplied), and falls through to `return answer, error_kind, is_partial`. After a raised halt those are still the initial `""`, `None`, `False`. `Orchestrator._execute_turn()` passes that `error_kind` to `emit_turn_end(...)`, so the turn-end audit records no error. Production does supply the callback: `scripts/agent/startup_component_init.py` constructs `Orchestrator(..., on_error=self._view.write_llm_error)`, so the user sees an LLM-error notice (rendering by the view port is not read here). That notice is the only outward signal; the returned tuple, the turn-end audit, and the diagnostics carry no error.
- Confirmed: a second, separate failure channel exists. `_run_execute_stage()` converts `result.action != "continue"` into an `error_kind` return value without raising, so the engine sees a successful stage (attempt `completed`), never retries it, writes task status `completed`, and the adapter's `_status_for_exit("completed", error_kind)` then overwrites it with `failed`. The retry rules therefore apply only to raised exceptions, not to LLM-level failure results.
- Confirmed: `_ERROR_KIND_TIMEOUT = "timeout"` and `_ERROR_KIND_EXCEPTION = "exception"` are written to `attempts.error_kind`; the names `workflow_timeout` and `workflow_halted` proposed in the memo do not exist in `scripts/`.
- Related closed work: `issues/done/20261021-093421_turn002_execute-stage-retry-duplicates-user-messages.md` (turn-entry work now runs once, outside the retry loop) and `issues/done/20261021-093421_turn003_task-status-overwritten-after-failure.md`. Not yet evidenced: how the REPL presents a turn that ends with `error_kind` set (versus the callback notice).

## Problem
- Timeout retry behavior cannot be read from configuration: the retry flag says yes, the code says no for timeouts, yes for other exceptions, and not at all for returned failure results.
- A turn that halted or timed out is indistinguishable, in the turn-end audit and in the returned tuple, from a turn with an empty answer; the only failure signal is the optional `on_error` callback (a callback-only signal, which the Implementation Intent forbids as sole carrier).
- Task status (`halted`), turn audit (no error), and the returned result (empty, no error) disagree for the same outcome; the callback notice is the only place the failure appears.
- Whether partial side effects are safe to repeat on retry is undefined.

## Reason for Change
Retry eligibility and outward failure reporting are one contract; operators cannot tell whether work was retried, exhausted, or reported as success. The audit gap is observable now, and the production user notice depends solely on the callback. Medium: it affects diagnosability and the correctness of the reported outcome, not stored task data.

## Implementation Intent
- Express retry eligibility per error kind in workflow policy (timeout, transport, exception, LLM-level failure result), including whether each consumes the retry budget, instead of one stage-level boolean plus a hard-coded exception.
- Choose one terminal-failure mechanism (typed failure result, or exception propagated to the caller) and use it for halt and timeout; do not leave the empty-answer, no-`error_kind` return possible.
- Derive task status, turn-end audit `error_kind`, diagnostics, and the user-visible message from the same normalized failure value.
- Callbacks (`on_error`) become observational only.
- State when a retry is allowed after a stage produced partial output or a side effect, and enforce it.

## Target Files or Areas
- `scripts/agent/workflow/workflow_engine.py` (retry loop, error-kind constants, halt/timeout exceptions)
- `scripts/agent/workflow/models.py`, `scripts/agent/workflow/workflow_loader.py`, `config/workflows/default.json` (retry policy schema), and the workflow definition validation path
- `scripts/agent/workflow_engine_adapter.py` (`execute_turn`, `_handle_workflow_halt`, `_status_for_exit`, `_run_execute_stage`)
- `scripts/agent/orchestrator.py` (`_execute_turn`, `emit_turn_end` call)
- `scripts/agent/startup_component_init.py` (`on_error` wiring), `scripts/agent/cli_view.py` and the view port behind `write_llm_error`; the turn-result / error models (exact files: 不明, to be located during implementation)
- `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/test_orchestrator.py`
- `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` ("Task Status Transitions" table, "Retry Mechanism", Operational Notes)
- `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` (decision 6, only if the timeout-to-`halted` outcome changes)

## Required Changes
- Decide and encode whether a timeout is retryable, and which attempts consume `max_attempts`.
- Add explicit retryable error kinds to the workflow definition schema and loader validation.
- Decide the treatment of LLM-level failure results (the non-raising channel): retry under the same policy, or terminal; make the engine and adapter agree.
- Introduce stable error kinds for terminal workflow failure (for example `workflow_timeout`, `workflow_halted`) and use them in attempt rows, task status handling, turn-end audit, and the returned result.
- Make `execute_turn()` return or raise so that a halted or timed-out workflow is visible as a failed turn with or without `on_error`.
- Define the partial-output / side-effect rule for retry and enforce it (for example, no retry after a persisted assistant message or a completed non-idempotent tool call unless the tool-call idempotency contract applies).
- Remove the transient `completed` write followed by an adapter overwrite to `failed`, or define it as intended.
- Update the `agent_03_03` passages listed under Documentation Impact, and ADR-001 decision 6 if the timeout outcome changes (ADR change protocol).

## Constraints
- Changing the workflow definition schema affects `config/workflows/*.json` and the startup preflight; retained configuration must still load or fail with a clear error.
- Task status vocabulary and transitions are owned by `issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md`; this issue must use whatever that contract defines for halted/failed.
- Fail-closed behavior must not weaken; a failure must never degrade to an apparently successful turn.
- Partial-side-effect safety must not rely on MCP tool-call deduplication that does not yet exist for all servers (see Dependencies).

## Acceptance Criteria
- Given the shipped configuration, a test documents whether a timed-out execute stage is retried, and the result matches the configuration.
- The retry budget is consumed identically for every error kind the policy marks retryable, and not consumed for those it marks non-retryable.
- A halted or timed-out turn yields a failed outcome with a stable `error_kind`, observable in the turn-end audit record, the returned result, and the REPL output, with no `on_error` configured and, when configured, without a duplicate notice.
- With and without `on_error`, task status, audit `error_kind`, and returned result report the same outcome.
- A retry after partial output or a completed side effect follows the stated rule and is tested.
- No turn can end with an empty answer, `error_kind` of `None`, and a task status of `halted`/`failed`.

## Testing Expectations
- Engine tests: timeout then success (if retryable), timeout exhaustion, exception exhaustion, non-retryable error, LLM-level failure result.
- Adapter/orchestrator tests: halt and timeout with callback and without callback; assert returned tuple, task status, and the emitted turn-end audit.
- Test for failure before and after partial output.
- Workflow-definition loader tests for the new policy fields, including a definition with unknown error kinds.
- Run the sequence in `rules/toolchain.md`.
- Docs checkers per `routing.md` Tools: `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain agent`, and `check_docs_japanese.py`; `check_needs_confirmation_inventory.py` if a Needs Confirmation marker is added.
- `uv run python tools/check_adr_preservation.py` if the ADR is edited.

## Documentation Impact
Yes (intent and failure behavior only; no code restatement per `skills/DESIGN.md`):

- `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`: the "Task Status Transitions" row "a retryable stage exhausts `max_attempts`, or a stage times out -> `halted`", the "Retry Mechanism" section (retry loop and `retryable` semantics), and the Operational Notes bullet on `halted`. They describe today's timeout-not-retried behavior and must follow the decided policy, the stable error kinds, and the terminal-failure contract.
- `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` decision 6 ("a Task that exceeds its retry budget is persisted as `halted`"): amend only if the timeout or failure outcome changes.
- Record unresolved owner decisions as Needs Confirmation items (register per `routing.md` Tools if markers are added).

## Out of Scope
- Stale-attempt recovery and leases (`issues/20261030-105723_wflease001_stale-attempt-lease.md`).
- Attempt-number persistence, event ledger, and transition validation (`issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md`).
- HTTP-transport retries inside a single tool call (`scripts/shared/http_transport.py`) and MCP-side deduplication (`plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md`).
- Redesigning REPL error presentation beyond showing the new failed outcome.

## Dependencies
- Depends on `issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md` for the attempt-count and status contract (retry budget must count persisted attempts); implement after it, or against its agreed interface.
- Related, not blocking: `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md` (replay rules for interrupted tool calls) bounds how safely a side-effecting call can be retried; the partial-side-effect rule here should reference it instead of defining a second protocol.

## Unresolved Questions
- 不明: whether a stage timeout should be retried. The memo asks the owner to decide; this issue does not assume either answer.
- 不明: whether LLM-level failure results (non-raising channel) should be retried, given they currently are not.
- 不明: how the view port renders `write_llm_error` for a halt versus how it renders a turn whose `error_kind` is set; confirm before choosing the user-visible output so the failure is not shown twice.
- 不明: choice between a typed failure result and exception propagation as the single terminal-failure mechanism.
- Assumption: a turn that ends `halted` should be shown to the user as failed rather than as an empty answer.

## AI Implementation Instruction
- Read the engine, adapter, orchestrator, `startup_component_init.py`, and the view port before editing; locate the unconfirmed files listed under Target Files or Areas first.
- Do not pick the open policy decisions (timeout retry, LLM-failure retry, failure mechanism) yourself; report them as missing input if the owner has not answered.
- Keep changes limited to retry policy and failure propagation; do not alter stale recovery or persistence schemas beyond what the agreed status contract requires.
- Write regression tests first and confirm they fail on the current code.
- Report changed files, commands run, and test results.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261030-105723
- **Related target files**: `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/workflow/models.py`, `scripts/agent/workflow/workflow_loader.py`, `config/workflows/default.json`, `scripts/agent/workflow_engine_adapter.py`, `scripts/agent/orchestrator.py`, `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`, `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`
