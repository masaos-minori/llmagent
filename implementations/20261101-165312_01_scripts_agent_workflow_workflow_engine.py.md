## Goal

Implement kind-based retry semantics in `scripts/agent/workflow/workflow_engine.py`: distinguish stage-deadline expiry from an inner `TimeoutError` using `asyncio.timeout()`'s `expired()` state, gate retry eligibility on `retry_policy.retry_on`, make every failed attempt consume one budget unit, route terminal kinds, add the `llm_failure` attempt kind, and treat side-effect-wrapped and callback-raised halts as terminal (REQ-002, REQ-003, REQ-005, REQ-006, REQ-007 / AC-2, AC-3, AC-5, AC-6, AC-7).

## Scope

- Deadline-versus-inner timeout (REQ-002 / AC-2): replace `asyncio.wait_for(fn(), timeout=timeout)` (`workflow_engine.py:278`) with `async with asyncio.timeout(timeout)` around the stage callback; in the `except TimeoutError` branch, decide by the deadline context's `expired()` state — deadline expiry keeps today's path (kind `timeout`, `WorkflowTimeoutError` raise at `:279-289`), an inner `TimeoutError` from the callback is classified kind `exception` (persisted with `_ERROR_KIND_EXCEPTION` at `:291-298`) and the original exception propagates instead of being relabeled `WorkflowTimeoutError`.
- Retry eligibility by kind (REQ-003 / AC-3): in `_run_stage_with_retry` (`:188-240`) classify each failure (kind `timeout` for deadline expiry, `exception` otherwise, `llm_failure` for the new stage-failure error, terminal for callback-raised `WorkflowHaltError`); when the kind is not in `self._wdef.retry_policy.retry_on`, re-raise the original exception at once — the engine writes `failed` via the existing catch in `run()` (`:183-185`) and no backoff sleep or extra attempt occurs; eligible kinds keep the current consume-budget-then-halt loop (`:211-221`).
- `except WorkflowTimeoutError: raise` at `:208-209` stays for the shipped default (timeout is not in `retry_on`), but becomes a consequence of the kind gate rather than a hardcoded bypass, so `retry_on: ["exception", "timeout"]` retries a deadline timeout identically to an exception (AC-3 second half).
- Stage-failure error (REQ-005 / AC-5, REQ-007 / AC-7): define `WorkflowStageFailure(Exception)` in this module next to `WorkflowHaltError`/`WorkflowTimeoutError` (`:75-81`) carrying `kind` (`"llm_failure"`), `answer`, `error_kind`, `is_partial`; add `_ERROR_KIND_LLM_FAILURE = "llm_failure"` beside `_ERROR_KIND_TIMEOUT`/`_ERROR_KIND_EXCEPTION` (`:27-28`); the engine persists it through `finish_attempt` with that kind and applies the `retry_on` gate; a terminal stage failure writes task `failed` exactly once via `run()` and propagates the typed error for the adapter (procedure 05) to convert back to the tuple.
- Terminal halts from callbacks (REQ-006 / AC-6): a `WorkflowHaltError` raised by the stage callback itself (the adapter wraps side-effect-flagged failures with it, procedure 05) is re-raised without retry — add `WorkflowHaltError` to the terminal re-raise branch beside `WorkflowTimeoutError` at `:208-209`; halts synthesized by budget exhaustion (`:219-221`) remain the engine's own and stay distinguishable from callback halts by their message.
- Outward kinds (`workflow_timeout`, `workflow_halted`) are turn-level and are NOT written to `attempts.error_kind` (REQ-007 / AC-7): the persisted kinds stay `timeout`, `exception`, `llm_failure`.

## Assumptions

- Plan `plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` is Frozen; its 12-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table (re-verified 2026-11-01: all 12 paths exist on `master`, no row replaced).
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record'); drifted citations carry `(re-verified 2026-11-01)` markers.
- Canonical semantics come from the Plan REQs (Plan `:38-48`): `retry_policy.retry_on` list drawn from `exception`/`timeout`/`llm_failure` with default `["exception"]` (REQ-001); deadline-versus-inner timeout classification via the deadline's `expired()` state (REQ-002); every failed attempt consumes one budget unit and ineligible kinds are terminal at once (REQ-003); typed outward kinds `workflow_halted` / `workflow_timeout` on the `(answer, error_kind, is_partial)` tuple (REQ-004); LLM-level failure results enter the engine as stage failures of kind `llm_failure` (REQ-005); per-attempt side-effect flag on `TurnState` set by `tool_runner` (REQ-006); attempt kinds `timeout`/`exception`/`llm_failure` distinct from outward kinds (REQ-007); no turn ends with empty answer, `error_kind` `None`, and a `halted`/`failed` task (REQ-008).
- Owner decisions (Plan UNK-01, UNK-02, 2026-10-30): timeouts and LLM-failure results are not retried by default; the shipped `retry_on` pins this, and the landed engine already treats timeouts as terminal (`workflow_engine.py:208-209`, re-verified 2026-11-01).
- Landing order (Plan Assumptions 'Re-verification record'): this batch lands after the pending procedure batches in plan order — wftaskapi001 `20261101-140834`, wfrecovery001 `20261101-145309`, wflease001 `20261101-163219` — so shared-file edits (`workflow_engine.py`, `models.py`, `workflow_engine_adapter.py`, `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/test_orchestrator.py`, `docs/23_agent/agent_03_03_...md`) rebase predictably. The wfrecovery001 Phase 4 attempt/budget contract itself is already landed on `master` (per-attempt event ids `{task_id}:{stage_id}:{attempt}`, `begin_stage_if_new` at `workflow_engine.py:264`, `finish_attempt` kinds at `:280-298`), so the Phase 2 gate is open.
- Side-effect rule (Plan Assumptions, UNK-06): every non-READ operation, including `classify_operation_type` results of `UNKNOWN`, counts as a side effect (conservative) until the owner decides a relaxation on top of the landed toolexec001 replay protocol.
- This Plan touches no schema, migration, or migration-registry file: the workflow migration ledger (`scripts/db/migrations_workflow.py`, HEAD code 2 / "1.2.0") is not a target row and needs no change here.
- `asyncio.timeout()` is the chosen mechanism (Plan Design 'Timeout classification'); the Plan's own verification record (2026-10-30) tested on Python 3.13.5 that `expired()` is false for an inner `TimeoutError` and true when the deadline fires.
- Every engine-started attempt already consumes one idempotency/ledger record (`begin_stage_if_new` at `:264-270`, event id `{task_id}:{stage_id}:{attempt}` at `:262`), so 'every failed attempt consumes one budget unit' holds on the landed wfrecovery001 Phase 4 contract without new attempt bookkeeping.

## Design decisions

- Exception routing inside the engine, typed tuple only at the adapter boundary (Plan Design 'Failure mechanism', UNK-04 default): retry logic and status writes stay in `run()`/`_run_stage_with_retry`.
- Terminal exceptions not in `retry_on` take today's non-retryable-stage path (original exception propagates, engine writes `failed`, orchestrator records the exception class name as `error_kind`); `workflow_halted` is reserved for budget exhaustion and the side-effect rule (Plan Design).
- Failure-mapping helpers live here, not in the adapter (Plan Risk mitigation: adapter is at 15702 B of the 20480 B `check_module_size` limit).

## Alternatives considered

- Keep `wait_for` and compare elapsed time — rejected (Plan Design): `asyncio.timeout().expired()` answers the deadline question directly without clocks.
- Return-value failure routing for LLM-level failures — rejected (UNK-04 default): it would split retry/status logic across engine and adapter.

## Implementation
### Target file
`scripts/agent/workflow/workflow_engine.py`

### Procedure
1. Add `_ERROR_KIND_LLM_FAILURE` (`:27-28` region) and `WorkflowStageFailure` (`:75-81` region).
2. Rewrite the `_run_stage` timeout block (`:277-298`): `async with asyncio.timeout(timeout)`; classify by `expired()`; persist kind `timeout` only for deadline expiry, kind `exception` for inner `TimeoutError`; keep `finish_attempt` calls parameter-bound.
3. Rewrite `_run_stage_with_retry` (`:203-240`): after a failure, compute its kind (timeout / exception / llm_failure / halt), consult `self._wdef.retry_policy.retry_on`, re-raise terminal kinds immediately, keep the existing budget/backoff/`workflow.retry` span path for eligible kinds, and re-raise callback-raised `WorkflowHaltError` without retry.
4. Persist `WorkflowStageFailure` in `_run_stage`'s failure branch with kind `llm_failure` and re-raise it unchanged.
5. Do not change `run()`'s status writes (`:180-186`): `halted` for halt/timeout, `failed` for terminal exceptions, `completed` on success — REQ-008 depends on exactly one status write per turn.

### Method
In-place edits of `_run_stage_with_retry` and `_run_stage` plus two module-level additions; no agent-layer imports (Plan Design 'Layering': the engine stays free of agent-layer imports).

### Details
- HEAD anchors (re-verified 2026-11-01): `run()` `:162-186`; retry loop `:188-240` (`retryable` gate `:196-199`, timeout bypass `:208-209`, halt-after-max `:210-221`, backoff and retry span `:222-240`); stage body `:242-309` (`timeout` computed `:261`, event id `:262`, `begin_stage_if_new` `:264-270`, `wait_for` `:278`, kind persistence `:279-298`, artifact record `:300-308`).
- `WorkflowStageFailure` lives in `workflow_engine.py` and is exported through `agent.workflow.__init__` exactly like `WorkflowHaltError` (the adapter imports it from `agent.workflow`); the pending wfrecovery001 errors-module procedure (`implementations/20261101-145309_02_scripts_agent_workflow_errors.py.md`) is the place where all three move together if it lands first — coordinate at implementation time.
- The `workflow.retry` span attributes (`retry.attempt`, `retry.max_attempts`, `retry.error_type` at `:231-239`) gain the kind value as `retry.error_type` stays the exception class name; no new span is required.

## Compatibility considerations

- `retry_policy.retry_on` must exist before this procedure compiles: Blocked until procedures 02-04 land (see Blocker Log).
- Blast radius per Plan Risks: `WorkflowEngine` 54 test references in 3 files, `WorkflowHaltError` 28, `WorkflowTimeoutError` 16 — defaults preserve behavior and exception class names are kept; each commit leaves the suite green.
- Rebases on the pending wfrecovery001 engine procedure (`implementations/20261101-145309_07_scripts_agent_workflow_workflow_engine.py.md`) and the pending wflease001 engine procedure (`implementations/20261101-163219_05_scripts_agent_workflow_workflow_engine.py.md`): the lease margin and conditional-finish edits touch the same functions; this batch lands last in plan order.

## Security considerations

- No new SQL surface: attempt persistence stays on the existing parameter-bound `finish_attempt` path; the new `error_kind` values are engine-produced literals, never caller- or user-supplied strings.
- Classification is derived from the deadline context, never from exception strings or user input.

## Rollback considerations

- Single-commit revert restores today's behavior: timeouts terminal via the hardcoded bypass, inner `TimeoutError` relabeled as `WorkflowTimeoutError`, no `llm_failure` rows.

## Validation plan

- `uv run pytest tests/agent/workflow/ -v` — procedure 08's new tests fail against pre-change `master` and pass after this procedure (Plan Validation plan).
- Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports` (baseline 6 kept, 0 broken), `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`.

## Completion criteria

- AC-2: a callback raising `TimeoutError` records kind `exception`; a callback exceeding `timeout_sec` records kind `timeout`.
- AC-3: with shipped config a timed-out execute stage is not retried and an exception is retried up to `max_attempts`; with `retry_on` including `timeout` the timeout consumes the budget identically.
- AC-5/AC-7 hold for stage failures persisted with kind `llm_failure`; no outward kind is ever written to `attempts.error_kind`.

## Out of Scope

- The adapter tuple/status contract (procedure 05), the `TurnState` flag (procedure 06), and the tool_runner side-effect setter (procedure 07).
- `retry_on` parsing/validation (procedure 03) and config (procedure 04).

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
| 1 | Blocked until procedures 02-04 land (`RetryPolicy.retry_on` must exist before the engine consults it) | No | — |
| 1 | Landing order: rebase on pending wfrecovery001 procedures 04/07 and wflease001 procedure 05 for the same functions (plan-order landing, Plan Assumptions) | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: Phase 2 (Engine semantics; after wfrecovery001 Phase 4 — gate open)
- **Requirement ID**: `REQ-002`, `REQ-003`, `REQ-005`, `REQ-006`, `REQ-007`
- **Source issue**: issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-165312
- **Related target files**: `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/workflow/models.py`, `scripts/agent/workflow/workflow_loader.py`, `config/workflows/default.json`, `scripts/agent/workflow_engine_adapter.py`, `tests/agent/workflow/test_workflow_engine.py`
