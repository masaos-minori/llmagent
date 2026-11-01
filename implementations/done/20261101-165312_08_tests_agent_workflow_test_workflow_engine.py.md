## Goal

Rewrite the timeout test and add the engine kind/retry/budget/side-effect tests in `tests/agent/workflow/test_workflow_engine.py` (REQ-002, REQ-003, REQ-005, REQ-006, REQ-009 / AC-2, AC-3, AC-5, AC-6).

## Scope

- Rewrite `test_timeout_raises_workflow_timeout_error` (`:163-181`, re-verified 2026-11-01: currently accepts `pytest.raises((WorkflowHaltError, WorkflowTimeoutError))`) to assert exactly `WorkflowTimeoutError` and that the attempt row persisted kind `timeout`.
- New cases (Plan REQ-009 list): inner `TimeoutError` from the callback records kind `exception` and is retried when `exception` is in `retry_on`; timeout retried when `retry_on` includes `timeout` (timeout then success); timeout exhaustion halts with the shipped config; exception exhaustion halts after consuming the full budget (attempt-row count equals `max_attempts`); non-retryable kind is terminal at once (no backoff sleep, one attempt row); LLM-failure stage failure via `WorkflowStageFailure` persisted with kind `llm_failure` and terminal under the shipped config; side-effect suppression — a callback that raises `WorkflowHaltError` is not retried even when `retry_on` includes `exception`.
- Shipped-configuration pin (REQ-003 / AC-3): one test loads the real `config/workflows/default.json` through the loader and asserts the shipped policy pins timeout-not-retried / exception-retried behavior.

## Assumptions

- Plan `plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` is Frozen; its 12-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table (re-verified 2026-11-01: all 12 paths exist on `master`, no row replaced).
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record'); drifted citations carry `(re-verified 2026-11-01)` markers.
- Canonical semantics come from the Plan REQs (Plan `:38-48`): `retry_policy.retry_on` list drawn from `exception`/`timeout`/`llm_failure` with default `["exception"]` (REQ-001); deadline-versus-inner timeout classification via the deadline's `expired()` state (REQ-002); every failed attempt consumes one budget unit and ineligible kinds are terminal at once (REQ-003); typed outward kinds `workflow_halted` / `workflow_timeout` on the `(answer, error_kind, is_partial)` tuple (REQ-004); LLM-level failure results enter the engine as stage failures of kind `llm_failure` (REQ-005); per-attempt side-effect flag on `TurnState` set by `tool_runner` (REQ-006); attempt kinds `timeout`/`exception`/`llm_failure` distinct from outward kinds (REQ-007); no turn ends with empty answer, `error_kind` `None`, and a `halted`/`failed` task (REQ-008).
- Owner decisions (Plan UNK-01, UNK-02, 2026-10-30): timeouts and LLM-failure results are not retried by default; the shipped `retry_on` pins this, and the landed engine already treats timeouts as terminal (`workflow_engine.py:208-209`, re-verified 2026-11-01).
- Landing order (Plan Assumptions 'Re-verification record'; updated by the 2026-11-02 execution verification): wftaskapi001 `20261101-140834` and wflease001 `20261101-163219` have landed on `master` (wflease001 registered migration code 4 / "1.4.0"); the wfrecovery001 `20261101-145309` procedures remain Pending and this batch lands ahead of them by owner decision, so those Pending procedure docs must be re-verified against the landed source before their own execution. Shared-file edits (`workflow_engine.py`, `models.py`, `workflow_engine_adapter.py`, `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/test_orchestrator.py`, `docs/23_agent/agent_03_03_...md`) rebase predictably. The wfrecovery001 Phase 4 attempt/budget contract itself is already landed on `master` (per-attempt event ids `{task_id}:{stage_id}:{attempt}`, `begin_stage_if_new` at `workflow_engine.py:264`, `finish_attempt` kinds at `:280-298`), so the Phase 2 gate is open.
- Side-effect rule (Plan Assumptions, UNK-06): every non-READ operation, including `classify_operation_type` results of `UNKNOWN`, counts as a side effect (conservative) until the owner decides a relaxation on top of the landed toolexec001 replay protocol.
- This Plan touches no schema, migration, or migration-registry file: the workflow migration ledger (`scripts/db/migrations_workflow.py`, landed HEAD code 4 / "1.4.0") is not a target row and needs no change here.
- Existing fixtures (per-test store/engine, `StageDefinition(timeout_sec=...)`) are reused; retry/timeout tests at `:113`, `:133`, `:165`, `:212`, `:242`, `:263`, `:303` stay green where their behavior is unchanged.

## Design decisions

- Assertions read persisted attempt rows through the store (kind column), locking the REQ-007 contract, not engine internals.

## Alternatives considered

- Spying on `finish_attempt` call arguments — rejected: the ACs are about persisted kinds and attempt counts.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_engine.py`

### Procedure
1. Rewrite the named timeout test first (it is the Plan's designated rewrite).
2. Add a `TestWorkflowEngineRetryKinds` class with the seven cases above, parametrizing `retry_on` through `WorkflowDef(retry_policy=RetryPolicy(..., retry_on=(...)))` fixtures.
3. Add the shipped-config test using `WorkflowLoader().load("default")`.

### Method
Test-only edits in the existing file layout (one rewritten case, one new class).

### Details
- The side-effect case raises `WorkflowHaltError` from the stage callback directly — at engine level this is the contract procedure 01 implements and procedure 05 triggers in production.
- Inner-`TimeoutError` fixtures raise `TimeoutError` from the callback well before its `timeout_sec` so classification cannot be time-ambiguous.

## Compatibility considerations

- File is shared with wftaskapi001/wfrecovery001/wflease001 test procedures (`20261101-140834_06` and `20261101-163219_11` landed, `20261101-145309_14/15` Pending); Plan Assumptions classify the overlap as compatible (additive tests in different classes) — this batch lands before the remaining wfrecovery001 procedures and rebases ahead of them.

## Security considerations

- No new SQL surface: attempt persistence stays on the existing parameter-bound `finish_attempt` path; the new `error_kind` values are engine-produced literals, never caller- or user-supplied strings.

## Rollback considerations

- Delete the new class; restore the rewritten test.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_engine.py -v` — new cases fail on pre-change `master` and pass after procedures 01-05.

## Completion criteria

- AC-2, AC-3, AC-5, AC-6 (engine half), AC-7 covered by this file.

## Out of Scope

- Adapter/orchestrator tuple tests (procedure 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Rewrote test_timeout_raises_workflow_timeout_error to assert exactly WorkflowTimeoutError plus persisted kind timeout (kept the wflease001 lease-horizon assertions). Added TestWorkflowEngineRetryKinds (7 cases: inner-TimeoutError kind exception retried; deadline timeout retried when retry_on includes timeout then success; deadline timeout terminal under shipped retry_on; exception exhaustion consumes full budget with 3 kind-exception rows; terminal kind no backoff sleep and single attempt via asyncio.sleep patch assertion; WorkflowStageFailure persisted kind llm_failure terminal under shipped config with typed attributes and task failed; callback-raised WorkflowHaltError not retried even with exception in retry_on) and TestShippedRetryPolicyPin (loaded config/workflows/default.json pins retry_on == ('exception',); engine behavior under the shipped policy: timeout terminal, exception retried). Added _attempt_error_kinds helper reading attempt rows by rowid (attempt_id is TEXT, started_at second-resolution - insertion order required). |
| 2 | Add or update tests per Validation plan | Completed | — | — | test_workflow_engine.py now 28 tests (19 pre-existing + 9 new); cases assert persisted kinds and attempt counts, not engine internals (Design decisions). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | ruff format/check, mypy clean, pytest tests/agent/workflow/test_workflow_engine.py 28 passed, tests/agent/workflow/ 128 passed; full-suite run at end of batch. |
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
- **Workflow phase**: Phase 2 (Engine semantics)
- **Requirement ID**: `REQ-002`, `REQ-003`, `REQ-005`, `REQ-006`, `REQ-009`
- **Source issue**: issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-165312
- **Related target files**: `tests/agent/workflow/test_workflow_engine.py`, `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/workflow/models.py`, `config/workflows/default.json`