## Goal
Delete the dead `error_kind` parameter from `_status_for_exit` and `_record_exit_status` in `scripts/agent/workflow_engine_adapter.py`, from the `_status_for_exit` call inside `_record_exit_status`, and from the `finally` call site in `execute_turn`; remove the `error_kind` mention from the docstrings. Status-mapping behavior is unchanged (`REQ-001`).

## Scope
**Release unit**: wfaudit014-full

- Covers Plan `plans/20261108-084015_wfaudit014_retry-loop-dead-parameters.md` row 1 only: `scripts/agent/workflow_engine_adapter.py`.

## Assumptions
- Plan frozen at the 2026-11-08 procedure pass; every edit site below is located by the quoted HEAD `ad48bfa28` text, not by raw line numbers (L49-61, L255, L262-280 drift once sibling procedures land).
- Sibling landing order per the plan's Related Documents table: `implementations/20261108-155554_01_...md` (wfaudit006, removes the `_owns_state_store` finally branch) and `implementations/20261108-162804_01_...md` (wfaudit008, deletes the alias block) land before this procedure; `implementations/20261108-201045_01_...md` (wfaudit013) commutes either order. All three regions are disjoint from the regions edited here.
- At HEAD `_status_for_exit` already maps `cancelled` to `halted` and returns `None` for every other exit reason; this procedure changes only the signature/docstrings, never the mapping.
- The local `error_kind` computation in `execute_turn` (classification plus the `(answer, error_kind, is_partial)` return, L260) stays: `scripts/agent/orchestrator.py` L176 consumes the returned kind.

## Design decisions
- Three edit sites, all inside the dead parameter's blast radius: the `_status_for_exit` def, the `_record_exit_status` def plus its `_status_for_exit(...)` call, and the `execute_turn` `finally` call. No other `error_kind` site is touched.
- Docstring rewrite removes the `error_kind` sentence while keeping the REQ-008 single-write semantics ("the engine writes the task status exactly once per turn").

## Alternatives considered
- Keep the parameter and read it (e.g. write the kind into the status write): rejected — the engine already writes the terminal status itself; adding a second writer would regress the REQ-008 guarantee the current docstring describes.
- Move `_status_for_exit` inline into `_record_exit_status`: rejected — the module-level function is the testable seam the plan's test row pins (`tests/agent/test_orchestrator.py`).

## Implementation
### Target file
`scripts/agent/workflow_engine_adapter.py`

### Procedure
Strip the `error_kind` parameter from both helpers and both call sites; rewrite the docstring sentence that names it.

### Method
1. `def _status_for_exit(exit_reason: str, error_kind: str | None) -> str | None:` -> `def _status_for_exit(exit_reason: str) -> str | None:`. In its docstring, replace the clause "so a completed exit with a failure `error_kind` no longer triggers a second write here — the engine wrote `failed` for the terminal stage failure itself" with a clause that names no parameter, e.g. "so a completed exit does not trigger a second write here — the engine already wrote the terminal stage failure status". Body unchanged: `if exit_reason == "cancelled": return "halted"` then `return None`.
2. `def _record_exit_status(self, exit_reason: str, error_kind: str | None, task: TaskRecord | None) -> None:` -> `def _record_exit_status(self, exit_reason: str, task: TaskRecord | None) -> None:` and its body call `_status_for_exit(exit_reason, error_kind)` -> `_status_for_exit(exit_reason)`.
3. In `execute_turn`'s `finally`, the HEAD line `self._record_exit_status(exit_reason, error_kind, task)` -> `self._record_exit_status(exit_reason, task)`.

### Details
- After the edits, `grep -n "error_kind" scripts/agent/workflow_engine_adapter.py` must show only the local classification and return uses inside `execute_turn` and `_run_execute_stage` (`REQ-001` acceptance probe; the row's evidence: the body never reads the parameter).
- No import changes; no engine-side change (`workflow_engine.py` kind handling untouched, `REQ-001`).

## Compatibility considerations
- Both helpers are private to this module (underscore-prefixed function and method); no other module references them (census 2026-11-08 found call sites only inside this file). No config or deploy artifact is involved in this row.
- After this procedure lands, wfaudit006's quoted finally line `self._record_exit_status(exit_reason, error_kind, task)` no longer matches; the plan freezes its landing order before this procedure, so its quote matches HEAD at execution time.

## Security considerations
- No change to data handling or logging content.

## Rollback considerations
- Revert the commit; the parameter and docstring return, and the status-write behavior never changed, so no state needs unwinding.

## Validation plan
- Signature/mapping pin test added by procedure `implementations/20261108-211937_11_tests_agent_test_orchestrator.py.md` (row 11): `inspect.signature(_status_for_exit)` shows exactly one parameter and the cancelled/completed mappings hold.
- Existing halted-status assertions in `tests/agent/test_orchestrator.py` (the `statuses[0]["status"] == "halted"` and `("", "workflow_halted", False)` turn-result assertions near L659-662) stay green — this procedure must not alter any written status value.
- `uv run pytest tests/agent/test_orchestrator.py tests/agent/workflow/ -q`, then full `uv run pytest tests/ -q`; lint/type gates per `rules/toolchain.md`; the `grep -n error_kind` probe above.

## Completion criteria
- `REQ-001` grep probe clean (remaining `error_kind` uses are execute_turn/_run_execute_stage locals); both docstrings name no `error_kind`; full suite green with every previously written status value unchanged.

## Out of Scope
- Any change to the cancelled->halted / completed->None mapping (already HEAD behavior).
- The orchestrator's consumption of the returned `error_kind` (`scripts/agent/orchestrator.py` L176).

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
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`
- **Source issue**: `issues/20261107-203227_wfaudit014_retry-loop-dead-parameters.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084015_wfaudit014_retry-loop-dead-parameters.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-211937
- **Related target files**: scripts/agent/workflow_engine_adapter.py
