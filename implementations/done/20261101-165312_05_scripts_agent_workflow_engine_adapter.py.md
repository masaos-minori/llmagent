## Goal

Make the turn boundary typed in `scripts/agent/workflow_engine_adapter.py`: return `error_kind` `workflow_halted` / `workflow_timeout` on halted/timed-out turns, route LLM-level failure results through the engine as `WorkflowStageFailure`, wrap side-effect-flagged attempt failures as terminal, clear the flag at each attempt start, and limit adapter status writes to cancellation (REQ-004, REQ-005, REQ-006, REQ-008 / AC-4, AC-5, AC-6, AC-8).

## Scope

- Typed halt/timeout kinds (REQ-004 / AC-4): in the `except (WorkflowHaltError, WorkflowTimeoutError)` branch (`workflow_engine_adapter.py:210-212`) set `error_kind` to `"workflow_halted"` or `"workflow_timeout"` (split the catch into two branches) before the return at `:222`, so `execute_turn` no longer returns `("", None, False)` for a halted turn and the orchestrator's turn-end audit (`orchestrator.py:166-200` → `audit_event_emitter`) carries the kind; `on_error` stays observational (called once via `_handle_workflow_halt` `:307-313`, never the sole signal).
- LLM-failure routing (REQ-005 / AC-5): in `execute_fn` (`:180-186`), when `_run_execute_stage` (`:331-383`) returns a failure result (`result.action != "continue"` classification at `:359-365`), raise `WorkflowStageFailure(kind="llm_failure", answer=..., error_kind=..., is_partial=...)` instead of returning the tuple; the engine applies the `retry_on` gate (procedure 01); under the shipped config the failure is terminal: the engine writes task `failed` once (`workflow_engine.py:183-185`) and the adapter's halt/exception handling converts the typed error back to the outward `(answer, error_kind, is_partial)` with the same outward `error_kind` value as today.
- Remove the completed-then-failed overwrite (REQ-008): `_status_for_exit` (`:49-60`) drops the `exit_reason == "completed" and error_kind is not None` branch (`:58-59`); the engine already wrote `failed` for the terminal stage failure, so the adapter writes status only for cancellation (`:56-57`) (Plan 'The task status is written once, by the engine; the adapter writes only what the engine cannot observe').
- Side-effect terminal wrap (REQ-006 / AC-6): in `execute_fn`, clear `ctx.turn.attempt_side_effect` (procedure 06's field) at attempt start; if `_run_execute_stage` raises and the flag is set, raise `WorkflowHaltError("stage execute halted: side effect attempted")` from it — the engine re-raises halts without retry (procedure 01); the outward kind is `workflow_halted` regardless of `retry_on`.
- `audit_stage_completed` stays emitted before a stage failure is raised (Plan Design): keep the emission at `_run_execute_stage:374-382` before raising `WorkflowStageFailure`.

## Assumptions

- Plan `plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` is Frozen; its 12-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table (re-verified 2026-11-01: all 12 paths exist on `master`, no row replaced).
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record'); drifted citations carry `(re-verified 2026-11-01)` markers.
- Canonical semantics come from the Plan REQs (Plan `:38-48`): `retry_policy.retry_on` list drawn from `exception`/`timeout`/`llm_failure` with default `["exception"]` (REQ-001); deadline-versus-inner timeout classification via the deadline's `expired()` state (REQ-002); every failed attempt consumes one budget unit and ineligible kinds are terminal at once (REQ-003); typed outward kinds `workflow_halted` / `workflow_timeout` on the `(answer, error_kind, is_partial)` tuple (REQ-004); LLM-level failure results enter the engine as stage failures of kind `llm_failure` (REQ-005); per-attempt side-effect flag on `TurnState` set by `tool_runner` (REQ-006); attempt kinds `timeout`/`exception`/`llm_failure` distinct from outward kinds (REQ-007); no turn ends with empty answer, `error_kind` `None`, and a `halted`/`failed` task (REQ-008).
- Owner decisions (Plan UNK-01, UNK-02, 2026-10-30): timeouts and LLM-failure results are not retried by default; the shipped `retry_on` pins this, and the landed engine already treats timeouts as terminal (`workflow_engine.py:208-209`, re-verified 2026-11-01).
- Landing order (Plan Assumptions 'Re-verification record'; updated by the 2026-11-02 execution verification): wftaskapi001 `20261101-140834` and wflease001 `20261101-163219` have landed on `master` (wflease001 registered migration code 4 / "1.4.0"); the wfrecovery001 `20261101-145309` procedures remain Pending and this batch lands ahead of them by owner decision, so those Pending procedure docs must be re-verified against the landed source before their own execution. Shared-file edits (`workflow_engine.py`, `models.py`, `workflow_engine_adapter.py`, `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/test_orchestrator.py`, `docs/23_agent/agent_03_03_...md`) rebase predictably. The wfrecovery001 Phase 4 attempt/budget contract itself is already landed on `master` (per-attempt event ids `{task_id}:{stage_id}:{attempt}`, `begin_stage_if_new` at `workflow_engine.py:264`, `finish_attempt` kinds at `:280-298`), so the Phase 2 gate is open.
- Side-effect rule (Plan Assumptions, UNK-06): every non-READ operation, including `classify_operation_type` results of `UNKNOWN`, counts as a side effect (conservative) until the owner decides a relaxation on top of the landed toolexec001 replay protocol.
- This Plan touches no schema, migration, or migration-registry file: the workflow migration ledger (`scripts/db/migrations_workflow.py`, landed HEAD code 4 / "1.4.0") is not a target row and needs no change here.
- Outward `error_kind` values `workflow_halted` / `workflow_timeout` are turn-level literals (REQ-007); they are never written to `attempts.error_kind`.
- LLM-level failure keeps today's outward `error_kind` (the `result.error_kind or result.reason or result.action` value at `:360`) so existing REPL behavior is unchanged (Plan Risk mitigation).

## Design decisions

- Boundary contract stays the existing typed tuple (Plan Design 'Failure mechanism', UNK-04 default); no new caller contract is invented — `Orchestrator._execute_turn` already forwards `error_kind` to `emit_turn_end` (`orchestrator.py:166-200`).
- The flag check lives here (the agent layer) because `workflow_engine.py` stays free of agent-layer imports (Plan Design 'Layering').

## Alternatives considered

- Keep returning failure tuples from `execute_fn` and let the engine infer failure — rejected (REQ-005): the engine could not apply retry policy or write `failed` once for LLM-level failures.

## Implementation
### Target file
`scripts/agent/workflow_engine_adapter.py`

### Procedure
1. Split the halt catch (`:210-212`) into `except WorkflowTimeoutError` (kind `workflow_timeout`) and `except WorkflowHaltError` (kind `workflow_halted`), plus a `WorkflowStageFailure` branch that restores the outward tuple fields from the error attributes.
2. Raise `WorkflowStageFailure` from `execute_fn` on LLM-level failure results; keep the persistence and partial-flag classification logic in `_run_execute_stage` (`:356-372`).
3. Clear and check `ctx.turn.attempt_side_effect` in `execute_fn` as described; import nothing from `agent.workflow` beyond the shared `WorkflowStageFailure` export.
4. Drop the completed-then-failed branch in `_status_for_exit` (`:58-59`).

### Method
Edits across `execute_turn`, `execute_fn`, and `_status_for_exit`; failure-mapping helpers stay in `workflow_engine.py` (module-size mitigation).

### Details
- HEAD anchors (re-verified 2026-11-01): `execute_turn` `:149-222` (tuple init `:157-159`, halt catch `:210-212`, return `:222`), `_status_for_exit` `:49-60`, `_handle_workflow_halt` `:307-313`, `_run_execute_stage` `:331-383` (LLM-failure classification `:359-365`, audit `:374-382`).
- Module size gate (Plan Risks): the file is 15702 B at baseline of the 20480 B limit; this procedure adds branches, not helpers — `check_module_size` in the Validation plan.
- Cancellation path (`:213-215`) and `finally` block (`:216-220`) keep their current shape.

## Compatibility considerations

- Blocked until procedures 01 and 06 land (`WorkflowStageFailure` and the `TurnState` field must exist; see Blocker Log).
- Rebases on the pending wfrecovery001 adapter procedure (`implementations/20261101-145309_08_scripts_agent_workflow_engine_adapter.py.md`) and wflease001 landing order; Plan Assumptions record the overlap as different methods, non-contradicting.
- `orchestrator.py`, `startup_component_init.py`, `cli_view.py` need no change (Plan Assumptions).

## Security considerations

- No new SQL surface: attempt persistence stays on the existing parameter-bound `finish_attempt` path; the new `error_kind` values are engine-produced literals, never caller- or user-supplied strings.
- The new outward kinds are fixed literals; no error text from the engine or LLM is copied into `error_kind` for halt/timeout (the LLM-failure branch keeps today's classification only).

## Rollback considerations

- Single-commit revert restores the silent halt tuple, the completed-then-failed overwrite, and tuple-returning `execute_fn`.

## Validation plan

- `uv run pytest tests/agent/test_orchestrator.py tests/integration/test_orchestrator_integration.py -v` (procedure 10 pins AC-4/AC-5/AC-8).
- Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports` (baseline 6 kept, 0 broken), `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`.

## Completion criteria

- AC-4: halted and timed-out turns return `workflow_halted` / `workflow_timeout` with and without `on_error`, and the turn-end audit carries it.
- AC-5: LLM-failure turns write `failed` once (no `completed` write) with the same outward kind as before.
- AC-6: a flag-set failed attempt is terminal with `workflow_halted` even when its kind is in `retry_on`.
- AC-8: the invariant test (procedure 10) passes for halt, timeout, LLM failure, and cancellation.

## Out of Scope

- Engine kind logic (procedure 01); the `TurnState` field itself (procedure 06); tool_runner flag setter (procedure 07).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Implemented Procedure 1-4: halt catch split into WorkflowTimeoutError (error_kind=workflow_timeout) and WorkflowHaltError (error_kind=workflow_halted), plus a WorkflowStageFailure branch restoring (answer, error_kind, is_partial) from error attributes (no on_error call, matching today's LLM-failure behavior); execute_fn clears ctx.turn.attempt_side_effect at attempt start, wraps raise-with-flag-set as WorkflowHaltError('stage execute halted: side effect attempted'), and raises WorkflowStageFailure(kind default llm_failure) when _run_execute_stage classifies a failure result (classification and audit_stage_completed-before-raise ordering kept in _run_execute_stage); _status_for_exit drops the completed-then-failed branch (signature kept, cancellation-only write); WorkflowStageFailure imported from the agent.workflow shared export only. Blocker Log rows resolved. |
| 2 | Add or update tests per Validation plan | Completed | — | — | No new tests in this procedure; AC-4/AC-5/AC-6/AC-8 tests land in procedure 10. 117 of 120 tests/agent/test_orchestrator.py pass unchanged; 3 failures are old-behavior assertions scheduled for rewrite by procedure 10: error_kind-is-None-on-halt (superseded by AC-4), adapter writes failed on execute failure (superseded by REQ-008 single engine write), and the completed-then-failed db-write-failure rescue path (now engine-owned). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | ruff format/check, mypy clean, lint-imports 6 kept 0 broken, bandit clean, check-module-size OK (adapter under the 20480 B limit); full-suite run at end of batch. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | Out of scope for this procedure; docs updated by procedure 12. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Blocked until procedure 01 (`WorkflowStageFailure`, terminal halt re-raise) and procedure 06 (`TurnState` field) land | Yes | 2026-11-02: procedures 01 and 06 of this batch landed immediately before this one |
| 1 | Landing order: rebase on the pending wfrecovery001 adapter procedure `20261101-145309_08` (plan-order landing, Plan Assumptions) | Yes | 2026-11-02: wfrecovery001 remains Pending and this batch lands ahead of it by owner decision (Assumptions landing-order bullet); `20261101-145309_08` must be re-verified against this landed shape |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: Phase 4 (Boundary contract)
- **Requirement ID**: `REQ-004`, `REQ-005`, `REQ-006`, `REQ-008`
- **Source issue**: issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-165312
- **Related target files**: `scripts/agent/workflow_engine_adapter.py`, `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/context.py`, `scripts/agent/tool_runner.py`, `tests/agent/test_orchestrator.py`