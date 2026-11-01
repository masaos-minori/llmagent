## Goal

Add halt/timeout outcome, LLM-failure, callback, and invariant tests to `tests/agent/test_orchestrator.py` (REQ-004, REQ-005, REQ-008, REQ-009 / AC-4, AC-5, AC-8).

## Scope

- Typed outcomes (REQ-004 / AC-4): a halted turn and a timed-out turn return `error_kind` `workflow_halted` / `workflow_timeout` from the turn path, with and without `on_error`; with a callback it is called exactly once with the typed exception; the turn-end audit event (`emit_turn_end`) carries the same `error_kind` (assert through the mocked emitter the file already uses).
- The existing halt tests (`:663-667` region, re-verified 2026-11-01: they assert task status and `on_error`'s `WorkflowHaltError`) are extended — not replaced — with the returned-tuple assertion.
- LLM failure (REQ-005 / AC-5): the fake-adapter/fake-result pattern already in this file drives a `result.action != "continue"` turn; assert task status written once as `failed` (no `completed` row state) and the outward `error_kind` equals today's value.
- Invariant (REQ-008 / AC-8): one parametrized test over halt, timeout, LLM failure, and cancellation asserts no turn has empty answer + `error_kind=None` + task status `halted`/`failed` simultaneously.

## Assumptions

- Plan `plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` is Frozen; its 12-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table (re-verified 2026-11-01: all 12 paths exist on `master`, no row replaced).
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record'); drifted citations carry `(re-verified 2026-11-01)` markers.
- Canonical semantics come from the Plan REQs (Plan `:38-48`): `retry_policy.retry_on` list drawn from `exception`/`timeout`/`llm_failure` with default `["exception"]` (REQ-001); deadline-versus-inner timeout classification via the deadline's `expired()` state (REQ-002); every failed attempt consumes one budget unit and ineligible kinds are terminal at once (REQ-003); typed outward kinds `workflow_halted` / `workflow_timeout` on the `(answer, error_kind, is_partial)` tuple (REQ-004); LLM-level failure results enter the engine as stage failures of kind `llm_failure` (REQ-005); per-attempt side-effect flag on `TurnState` set by `tool_runner` (REQ-006); attempt kinds `timeout`/`exception`/`llm_failure` distinct from outward kinds (REQ-007); no turn ends with empty answer, `error_kind` `None`, and a `halted`/`failed` task (REQ-008).
- Owner decisions (Plan UNK-01, UNK-02, 2026-10-30): timeouts and LLM-failure results are not retried by default; the shipped `retry_on` pins this, and the landed engine already treats timeouts as terminal (`workflow_engine.py:208-209`, re-verified 2026-11-01).
- Landing order (Plan Assumptions 'Re-verification record'; updated by the 2026-11-02 execution verification): wftaskapi001 `20261101-140834` and wflease001 `20261101-163219` have landed on `master` (wflease001 registered migration code 4 / "1.4.0"); the wfrecovery001 `20261101-145309` procedures remain Pending and this batch lands ahead of them by owner decision, so those Pending procedure docs must be re-verified against the landed source before their own execution. Shared-file edits (`workflow_engine.py`, `models.py`, `workflow_engine_adapter.py`, `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/test_orchestrator.py`, `docs/23_agent/agent_03_03_...md`) rebase predictably. The wfrecovery001 Phase 4 attempt/budget contract itself is already landed on `master` (per-attempt event ids `{task_id}:{stage_id}:{attempt}`, `begin_stage_if_new` at `workflow_engine.py:264`, `finish_attempt` kinds at `:280-298`), so the Phase 2 gate is open.
- Side-effect rule (Plan Assumptions, UNK-06): every non-READ operation, including `classify_operation_type` results of `UNKNOWN`, counts as a side effect (conservative) until the owner decides a relaxation on top of the landed toolexec001 replay protocol.
- This Plan touches no schema, migration, or migration-registry file: the workflow migration ledger (`scripts/db/migrations_workflow.py`, landed HEAD code 4 / "1.4.0") is not a target row and needs no change here.
- The file's `_temp_workflow_store` / fake `WorkflowEngine` fixtures (`:670+` region) are the existing pattern for driving real engine paths; reuse them.

## Design decisions

- Assert the boundary tuple plus the persisted status plus the audit argument triple in one place per scenario (Plan Design: audit already consumes the tuple).

## Alternatives considered

- New integration file — rejected: the frozen table names this file and its fixtures already cover the turn path.

## Implementation
### Target file
`tests/agent/test_orchestrator.py`

### Procedure
1. Extend the halt tests with the returned-tuple and audit assertions.
2. Add `TestTurnFailureKinds` with the AC-4 (with/without callback), AC-5, and AC-8 invariant cases.

### Method
Test-only additions plus two assertion extensions in existing tests.

### Details
- Cancellation scenario drives the adapter's `asyncio.CancelledError` path (`workflow_engine_adapter.py:213-215`) and expects outward kind handling per procedure 05 plus `halted` status (the adapter-owned write).
- No change to the bg-failure tests around `:2627-2765` (re-verified 2026-11-01: that region is bg-task failure handling, not workflow halt); the Plan's `:764` cite maps to the recorder tests, untouched here.

## Compatibility considerations

- File shared with pending wfrecovery001 (`20261101-145309_19`) and turnadr001 regions; Plan Assumptions: compatible (different regions).

## Security considerations

- No new SQL surface: attempt persistence stays on the existing parameter-bound `finish_attempt` path; the new `error_kind` values are engine-produced literals, never caller- or user-supplied strings.

## Rollback considerations

- Delete the new class; revert the two extended assertions.

## Validation plan

- `uv run pytest tests/agent/test_orchestrator.py -v`, plus `uv run pytest tests/integration/test_orchestrator_integration.py -v` (Plan Validation plan).

## Completion criteria

- AC-4, AC-5, AC-8 covered by this file.

## Out of Scope

- Engine-level kind tests (procedure 08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Added TestTurnFailureKinds (8 cases: halt typed tuple with/without callback; timeout typed tuple with/without callback; turn-end audit carries workflow_timeout; LLM-failure status written once by the engine via _status_harness with attempt-row kind llm_failure; parametrized no-silent-failure over halt/timeout/llm_failure; cancellation adapter-owned halted write). Extended the existing retry-halt test with the returned typed tuple and the TestTurnEndBracket halt test with the typed audit kind. Re-wrote the 3 old-behavior tests to the new contract: test_writes_failed_on_execute_failure -> test_execute_failure_returns_typed_tuple_without_adapter_status_write (adapter writes no status, restores typed tuple); test_status_write_failure_logs_error_without_on_error -> test_status_write_failure_propagates_from_engine_owned_write (RuntimeError propagates, task stays running, on_error not invoked). |
| 2 | Add or update tests per Validation plan | Completed | — | — | test_orchestrator.py now 130 tests (122 pre-existing + 8 new, 2 rewrites in place). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | ruff format/check clean; mypy matches the pre-change baseline exactly (56 pre-existing errors, 0 new - fixed the 4 mypy errors my additions initially introduced via adapter: Any indirection and a typed stages dict); pytest tests/agent/test_orchestrator.py 130 passed; the 3 intentional failures left by procedure 05 are now resolved; full-suite run at end of batch. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | Out of scope for this procedure; docs updated by procedure 12. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: Phase 4 (Boundary contract)
- **Requirement ID**: `REQ-004`, `REQ-005`, `REQ-008`, `REQ-009`
- **Source issue**: issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-165312
- **Related target files**: `tests/agent/test_orchestrator.py`, `scripts/agent/workflow_engine_adapter.py`, `scripts/agent/orchestrator.py`