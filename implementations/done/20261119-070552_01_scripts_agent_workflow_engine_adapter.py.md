## Goal

Refactor `WorkflowEngineAdapter.execute_turn` (`scripts/agent/workflow_engine_adapter.py`, radon C(13)) by extracting its four mixed responsibilities into small named methods — turn-entry preparation, per-attempt execute, and exit-status bookkeeping — without changing any behavior, so each concern is independently reviewable and testable (`REQ-001`–`REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit — every extraction preserves behavior, so all phases land together in one commit.

## Assumptions

- The public adapter surface (`execute_turn`, `deactivate_workflow`) signatures and return contract stay fixed, so `scripts/agent/orchestrator.py` needs no change (`REQ-005`).
- The three `nonlocal` values (`answer`, `error_kind`, `is_partial`) and their mutation sites are preserved exactly; extracted closures receive them as parameters rather than relying on closure capture.
- `engine.run(task, plan_fn, execute_fn, verify_fn)` still receives three awaitable/callable callbacks; if `verify_fn` becomes a module-level no-op it must remain awaitable to satisfy the same call contract.
- Behavior is byte-for-byte identical: same task statuses written on every exit path, same returned tuple, same `on_error`/`_handle_workflow_halt` routing (`REQ-005`).

## Design decisions

- **Turn-entry preparation → `_run_turn_entry(line, ctx)`** (async): owns the `with self._tool_override(self._allowed_tools)` scope, calls the existing independent `_prepare_turn_input(line, ctx)`, and maps exceptions: re-raise `WorkflowHaltError`/`WorkflowTimeoutError`; any other exception → mark the task `"halted"` via `self._state_store.update_task_status(task.task_id, "halted")` then raise `WorkflowHaltError`. Reproduces the inline L185-201 routing exactly (`REQ-001`).
- **Per-attempt execute → narrow `execute_fn`** (`REQ-002`): keep `execute_fn` as a thin wrapper that resets `self._ctx.turn.attempt_side_effect = False`, calls a small named attempt helper, and converts `error_kind` to `WorkflowStageFailure` (AC-5/AC-6). Move the attempt body (`_run_execute_stage` call + `attempt_side_effect` terminal check) into the helper. The reset is attempt-scoped (TurnState is not recreated per attempt), which is what makes retries safe — preserve this semantics.
- **Exit-status bookkeeping → collapse the `exit_reason` state machine** (`REQ-003`): replace the inline `exit_reason` string threaded through six branches with a direct outcome-to-status mapping; make `_status_for_exit`'s sole `"cancelled"` → `"halted"` branch explicit rather than a `None`-return convention. Leave `_record_exit_status` and the `_owns_state_store` close-on-exit in `finally` unchanged (`REQ-004`).
- **UNK-01** (`verify_fn` closure vs module-level no-op): leave `verify_fn` as a closure passed to `engine.run` for now; either choice preserves behavior and is an owner preference resolved during implementation.

## Alternatives considered

- `verify_fn` as a module-level no-op awaitable callback instead of a closure — acceptable if owner prefers it, but the closure is retained until UNK-01 is confirmed, so the `engine.run` callback contract is unchanged.
- Keep the `_status_for_exit`/`_record_exit_status` `None`-return convention vs. introducing an outcome enum for the single adapter-owned write — keep the current convention unless the owner prefers an enum (UNK-02); both preserve behavior.

## Implementation
### Target file
`scripts/agent/workflow_engine_adapter.py`
### Procedure
Extract three named responsibility methods from `execute_turn` while preserving behavior byte-for-byte; add the early-exit regression test to the companion test file.
### Method
1. **Extract turn-entry preparation.** Add async `_run_turn_entry(line, ctx)` that owns `with self._tool_override(self._allowed_tools)`, calls `await self._prepare_turn_input(line, ctx)`, and reproduces L185-201 routing: `except (WorkflowHaltError, WorkflowTimeoutError): raise`; `except Exception as prepared_exc:` → `if task is not None and task.task_id: self._state_store.update_task_status(task.task_id, "halted")` then `raise WorkflowHaltError(f"Turn-entry preparation failed: {prepared_exc}") from prepared_exc`. Replace the inline L185-201 block in `execute_turn` with `await self._run_turn_entry(line, self._ctx)`.
2. **Narrow the per-attempt execute closure.** Move the attempt body (`answer, error_kind, is_partial = await self._run_execute_stage(...)` plus the `attempt_side_effect` terminal check and the `error_kind` → `WorkflowStageFailure` conversion) into a small named async helper. Rewrite `execute_fn` as a thin wrapper: reset `self._ctx.turn.attempt_side_effect = False`, call the helper, keep the `nonlocal answer, error_kind, is_partial` mutation, and convert `error_kind` to `WorkflowStageFailure` when set (AC-5/AC-6). Keep `plan_fn`/`verify_fn` as the two remaining callbacks passed to `engine.run` until UNK-01 is resolved.
3. **Collapse the `exit_reason` state machine.** Replace the six inline `exit_reason = ...` assignments with a direct mapping from the engine outcome to the status the adapter writes; make the `"cancelled"` → `"halted"` branch explicit. Leave `_record_exit_status` and the `_owns_state_store` close-on-exit in the `finally` block (L220-224) unchanged.
### Details
- Preserve the returned tuple `(answer, error_kind, is_partial)` at L226 exactly.
- Preserve `_owns_state_store` close-on-exit in `finally` unchanged (`REQ-004`).
- Keep `engine.run(task, plan_fn, execute_fn, verify_fn)` receiving three awaitable callbacks.
- Do not change `execute_turn`'s signature or any public method name (`REQ-005`).

## Compatibility considerations

Only external caller is `scripts/agent/orchestrator.py`, which uses only the public `WorkflowEngineAdapter` surface (`execute_turn`/`deactivate_workflow`) that this refactor does not change (`REQ-005`, Reference Files).

## Security considerations

N/A: no change to `allowed_tools` scoping, the attempt-side-effect guard semantics, or halt/error routing; the `attempt_side_effect` reset stays attempt-scoped.

## Rollback considerations

N/A: revert the commit. Each extraction preserves behavior, so the suite stays green after every step and each step is independently revertable.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/workflow_engine_adapter.py` | Static: format, lint, types, architecture, security, complexity | `uv run ruff format --check scripts/agent/workflow_engine_adapter.py`; `uv run ruff check scripts/agent/workflow_engine_adapter.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports`; `uv run bandit scripts/agent/workflow_engine_adapter.py`; `uv run radon cc scripts/agent/workflow_engine_adapter.py -s` | ruff/mypy/lint-imports/bandit clean; radon shows `execute_turn` complexity below C(13) |
| `tests/agent/workflow/test_adapter_guards.py`, `tests/agent/workflow/test_adapter_store_ownership.py` | Unit: existing exit-path assertions pass unchanged; new early-exit regression test passes | `uv run pytest tests/agent/workflow/test_adapter_guards.py tests/agent/workflow/test_adapter_store_ownership.py -v` | All pass, asserting the same task statuses and returned tuples |
| `scripts/` changed lines (all) | Diff-scoped coverage across the refactor diff | `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan"` → `uv run coverage xml` → `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥90% on changed lines (`rules/toolchain.md` completion checklist) |

## Completion criteria

- `execute_turn` control flow no longer exceeds ~60 lines; the four responsibilities each live in a named method (AC-1).
- Every existing exit-path test passes unchanged, asserting the same task statuses and returned tuples (AC-2).
- No exit path leaves a task status unwritten that the current code writes; the new early-exit regression test covers a fresh exception type raised after `engine.run` starts (AC-3).
- ruff format/check, mypy, lint-imports, and bandit are clean; radon confirms complexity reduced, not behavior altered.

## Out of Scope

- Changing the execute-stage retry/halt semantics (AC-5/AC-6).
- Changing the workflow engine, `state_store.py`, or `orchestrator.py`.
- Renaming public adapter methods or changing `execute_turn`'s signature.
- Adding new behavior beyond the current exit paths.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extract turn-entry preparation into `_run_turn_entry` (new) (`scripts/agent/workflow_engine_adapter.py`, REQ-001) | Completed | 20261119-094443 | 20261119-094443 | — |
| 2 | Narrow the per-attempt execute closure (`scripts/agent/workflow_engine_adapter.py`, REQ-002) | Completed | 20261119-094443 | 20261119-094443 | — |
| 3 | Collapse the `exit_reason` state machine and verify (`scripts/agent/workflow_engine_adapter.py`, `tests/agent/workflow/test_adapter_guards.py`, REQ-003/004/005) | Completed | 20261119-094443 | 20261119-094443 | — |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`, `REQ-005`
- **Source issue**: `issues/20261118-221314_wfrev001_execute-turn-complexity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-231012_wfrev001_execute-turn-complexity.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-070552
- **Related target files**: `scripts/agent/workflow_engine_adapter.py`
