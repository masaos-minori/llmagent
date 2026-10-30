## Goal

Make `scripts/agent/workflow_engine_adapter.py` return a typed failure for every terminal workflow failure and route LLM-level failure results through the engine (`REQ-004`, typed `workflow_halted` (new) / `workflow_timeout` (new) results with and without callbacks; `REQ-005`, LLM failure results as stage failures and no `completed`-then-`failed` overwrite; `REQ-006`, per-attempt side-effect flag handling; `REQ-008`, no empty answer with no error kind).

## Scope

- Modify only `scripts/agent/workflow_engine_adapter.py`.
- The resume guard and the attempt number in the audit event are the wfrecovery001 Plan's changes in the same file.

## Assumptions

- Plan Dependencies (`plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` Scope): Plan Phase 4, after row 01 (`StageFailure` in the engine), row 06 (`TurnState` flag), row 07 (the flag is set by the tool runner), and `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` Phase 4. Execution order follows the Plan's phases, not `seq`.
- Plan overlap judgment (Step 8b): `workflow_engine_adapter.py` is also a target of the wfrecovery001 Plan (resume guard, audit attempt number): sequencing dependency; different methods of `execute_turn` and `_run_execute_stage`; the later change rebases.
- Verified in Step 3 of the Plan: `Orchestrator._execute_turn` forwards the returned `error_kind` to `emit_turn_end`; production supplies `on_error` (`startup_component_init.py:77-81`, `self._view.write_llm_error`); `error_kind` has no other consumer in `repl.py` or `cli_view.py` (UNK-03: no new rendering is added).
- `audit_stage_completed` is emitted inside `_run_execute_stage` before it returns, even for a failure result; that emission stays before a stage failure is raised.
- Module size is 15702 B (limit 20480 B); failure-mapping helpers live in the engine module.
- Names created by earlier rows of this Plan, flagged by `tools/stale_detector.py` and acceptable because they exist when `code-implementation` executes the rows in order: `StageFailure` (row 01 document), `side_effects_started` (row 06 document).

## Design decisions

- Boundary contract: the typed tuple `(answer, error_kind, is_partial)` stays the single outward result; halt and timeout set `error_kind` to `workflow_halted` (new) / `workflow_timeout` (new); `on_error` remains a notification only.
- An LLM-level failure result is raised as `StageFailure` from `_run_execute_stage` (after the existing audit call), so the engine owns retry and the single `failed` status write; `execute_turn` catches it and returns the same `error_kind`, answer, and partial flag the old return path produced.
- At each attempt start the adapter clears `side_effects_started`; any stage failure raised while the flag is set carries `side_effects=True`.
- `_status_for_exit` loses the `completed` with `error_kind` branch (the engine now writes `failed` itself); cancellation still records `halted`.

## Alternatives considered

- Make failures return values everywhere: rejected, the engine already routes by exception and the orchestrator already consumes the tuple (Plan Design).

## Implementation

### Target file

`scripts/agent/workflow_engine_adapter.py`

### Procedure

1. In `execute_turn` (`:149-222`), set `error_kind` in the `except (WorkflowHaltError, WorkflowTimeoutError)` branch (`:210`): `workflow_timeout` (new) for `WorkflowTimeoutError`, `workflow_halted` (new) otherwise, before calling `_handle_workflow_halt`.
2. Add an `except StageFailure` branch that assigns `answer`, `error_kind`, and `is_partial` from the exception and records the exit reason as a failure (no status write: the engine already wrote `failed`).
3. In the `execute_fn` closure (`:179-190`), clear `self._ctx.turn.side_effects_started` before running the attempt, and wrap a non-`StageFailure` exception raised while the flag is set into a `StageFailure` with `side_effects=True`.
4. In `_run_execute_stage` (`:327-375`), when `result.action != "continue"`: build the existing `error_kind` and partial flag, emit the existing `audit_stage_completed`, then raise `StageFailure` instead of returning them.
5. Simplify `_status_for_exit` (`:49-59`) to the cancellation case only and adjust `_record_exit_status` accordingly.

### Method

- Keep the `_handle_workflow_halt` log line and the `on_error` call exactly as they are.
- Keep `_prepare_turn_input` failure handling (`pending` to `halted` write, then `WorkflowHaltError`) unchanged.

### Details

- Line numbers are from the pre-change file; the wfrecovery001 documents change this file earlier, so locate by symbol.
- After this change no turn can return `("", None, False)` with a task status of `halted` or `failed`.

## Compatibility considerations

- For LLM-level failures the outward `error_kind` and final task status (`failed`) are unchanged; only the attempt row (now `failed`, kind llm_failure) and the removal of the transient `completed` write are new.
- Callers of `execute_turn` get a populated `error_kind` for halts and timeouts where they got `None` before; the orchestrator already forwards it.

## Security considerations

- N/A: no new input boundary.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_orchestrator.py tests/integration/test_orchestrator_integration.py -v`
- `uv run ruff format scripts/agent/workflow_engine_adapter.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_module_size.py`

## Completion criteria

- A halted and a timed-out turn return `workflow_halted` (new) / `workflow_timeout` (new) with and without `on_error`.
- An LLM-level failure ends with task status `failed` written once and the same outward `error_kind` as before.
- No path ends with an empty answer, `error_kind` `None`, and task status `halted` or `failed`.

## Out of Scope

- The engine (row 01), the turn-state flag (row 06), the tool runner (row 07), REPL rendering, resume-guard and audit changes (wfrecovery001 Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Typed halt and timeout results; `StageFailure` handling; flag reset and wrapping | Pending | — | — | Plan Phase 4; after rows 01, 06, 07 |
| 2 | Raise `StageFailure` for LLM failure results; simplify `_status_for_exit` | Pending | — | — | |
| 3 | Add or update tests per Validation plan | Pending | — | — | Row 10 document |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-004 (typed failure result), REQ-005 (stage failures), REQ-006 (flag handling), REQ-008 (no empty failed turn)
- **Source issue**: issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-130229
- **Related target files**: scripts/agent/workflow_engine_adapter.py
