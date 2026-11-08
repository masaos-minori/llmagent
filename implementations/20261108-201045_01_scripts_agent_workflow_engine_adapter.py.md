## Goal
Replace the two production `assert` guards in `workflow_engine_adapter.py` with explicit `if ... is None: raise <typed>` forms backed by two new module-local typed errors — `WorkflowEngineWiringError` (new) and `TurnBoundaryMissingError` (new) — and delete the inert `# noqa: B101` directive that annotates the second assert (`REQ-001`/`REQ-002`/`REQ-004`).

## Scope
**Release unit**: wfaudit013-full

- Covers Plan `plans/20261108-084014_wfaudit013_adapter-production-asserts.md` row 1 only: `scripts/agent/workflow_engine_adapter.py`.
- The guard-behavior tests for `REQ-002` live in sibling document `implementations/20261108-201045_02_tests_agent_workflow_test_adapter_guards.py.md` (row 2).

## Assumptions
- Line numbers refer to HEAD `ad48bfa28`. Landing order: `implementations/20261108-155554_01_scripts_agent_workflow_engine_adapter.py.md` (wfaudit006, regions L104, L254-258, L290-294) and `implementations/20261108-162804_01_scripts_agent_workflow_engine_adapter.py.md` (wfaudit008, regions L106-146, L336-341, module docstring L7-8) land first per batch chronology; their 46-line deletion shifts this document's HEAD anchors (engine guard L172 → L130, boundary guard L407 → L361). All sites below are located by quoted text; the shifted numbers are reference only. The sibling documents are design references, not implemented code.
- The constructor kwarg `workflow_engine` is typed `WorkflowEngine` (L86, non-Optional): the engine guard fires only on wiring bugs (callers passing `None` against the annotation); `Orchestrator.__init__` (`scripts/agent/orchestrator.py` L137-148) always injects a real engine in production, so healthy-path behavior cannot change (`REQ-003`).
- Propagation is behavior-preserving: `execute_turn` catches only `WorkflowTimeoutError`, `WorkflowHaltError`, `WorkflowStageFailure`, and `asyncio.CancelledError`, so both current asserts and the new plain-`Exception` subclasses pass through its try/finally unchanged; `_record_exit_status` runs in the `finally` and writes nothing for these exit reasons (`_status_for_exit` maps only "cancelled" to a status); the orchestrator's `except BaseException` branch (`scripts/agent/orchestrator.py` L190) records `error_kind = exc.__class__.__name__` and re-raises. `grep -rn "AssertionError" scripts/` confirms the turn path never special-cases `AssertionError` (only startup paths do: `startup_validation.py` L50, `startup_prompt_setup.py` L25).
- RUF100 currently reports exactly 1 error on the file (the L407 directive); the file's only other directive (`# noqa: BLE001`, L274) annotates a selected rule family and stays untouched.

## Design decisions
- Two new module-local error classes, inserted between the `TYPE_CHECKING` block (L42-44) and the "Private helpers" section header (L46): above every guard site, outside both sibling procedures' regions (wfaudit014's drafted L49-62 region starts at `_status_for_exit` and is not touched), and module-local so the tests import them from `agent.workflow_engine_adapter` without extending the `agent.workflow` package exports.
- Plain `Exception` subclasses: identical propagation to today's `AssertionError` (uncaught in `execute_turn`, logged through the orchestrator's generic branch) while replacing the disableable construct with real types.
- Message text is preserved: the engine guard keeps the assert message verbatim; the boundary guard merges the assert message with the noqa rationale ("None means writes bypass the atomic boundary") into the raise message, per the plan Design section.

## Alternatives considered
- Reuse `WorkflowHaltError` for the boundary guard: rejected — `_run_stage_with_retry` treats halts raised by stage callbacks as terminal and `execute_turn` routes them into `except WorkflowHaltError` (halt handler, `error_kind = "workflow_halted"`), which changes observable behavior at the guard point and misuses the type's documented meaning (max-attempts exhaustion).
- Reuse `RuntimeError`: rejected per `REQ-002` — a generic type where a typed error is being created.
- Move the guards into `__init__` / turn start: rejected — the plan mandates identical guard points ("Changing when the guards fire" is Out-of-Scope).
- Define the errors in `agent/workflow/workflow_engine.py` next to the three existing `Workflow*` errors: rejected — that file is owned by sibling procedure `175155_02` (wfaudit015), and adapter-local definition keeps this release unit's edits in one file.

## Implementation
### Target file
`scripts/agent/workflow_engine_adapter.py`

### Procedure
Insert the two typed error classes, convert both assert statements to `if ... raise` guards, and delete the noqa comment together with the second assert.

### Method
1. Insert after the `TYPE_CHECKING` block (currently L44, before the blank line preceding the "Private helpers" header at L46) a new section, 9 added lines total:

```
# ── Typed guard errors ────────────────────────────────────────────────────────


class WorkflowEngineWiringError(Exception):
    """Constructor wiring bug: the adapter was built without a WorkflowEngine."""


class TurnBoundaryMissingError(Exception):
    """Turn-protocol violation: a persist-as-assistant turn has no persistence boundary."""
```

2. Replace the engine-injection guard (currently L172-174, in `execute_turn` between `self._activate_workflow(...)` and `engine = self._workflow_engine`):

# Before:
```
            assert self._workflow_engine is not None, (
                "WorkflowEngine must be injected via constructor"
            )
```
# After:
```
            if self._workflow_engine is None:
                raise WorkflowEngineWiringError(
                    "WorkflowEngine must be injected via constructor"
                )
```

3. Replace the persistence-boundary guard and delete the noqa with the assert (currently L406-407, in `_run_execute_stage` before `await boundary.save("assistant", answer)`):

# Before:
```
            boundary = ctx.turn.persistence_boundary
            assert boundary is not None, "persistence boundary not set for this turn"  # noqa: B101 — boundary required inside a turn; None means writes bypass the atomic boundary
```
# After:
```
            boundary = ctx.turn.persistence_boundary
            if boundary is None:
                raise TurnBoundaryMissingError(
                    "persistence boundary not set for this turn; "
                    "None means writes bypass the atomic boundary"
                )
```

### Details
- No import changes: both errors are module-local; the guard sites reference them unqualified within the module.
- The `boundary = ctx.turn.persistence_boundary` line and the `await boundary.save(...)` line stay byte-identical; only the assert line between them changes (net +3 lines at this site, +1 at the engine-guard site, +9 at the class insertion).
- The module docstring (L1-11) is not edited here: its extracted-names-list edit is owned by `162804_01`.
- Untouched regions: `__init__`, the alias block L106-146 and deactivate twin L336-341 (owned by `162804_01`), `_owns_state_store` statements L104/L254-258/L290-294 (owned by `155554_01`), `_status_for_exit` L49-62 (drafted wfaudit014 target — if this document lands before wfaudit014's procedure pass, its anchors shift +9 and that plan's own pass re-anchors by text).
- Identical text sites of the boundary assert exist in three other files (`llm_turn_runner.py` L154, `conversation_state_manager.py` L122, `tool_round_completion.py` L133): the text search during step 3 must anchor on the occurrence inside `_run_execute_stage` (followed by `await boundary.save("assistant", answer)`), not the other files.

## Compatibility considerations
- `error_kind` strings surfaced by the orchestrator's generic branch change from "AssertionError" to the new class names on the (unreachable in production) guard paths; `grep -rn "AssertionError" tests/agent/test_orchestrator.py` confirms no test pins the old class name.
- No public API removal; two new public class names are added to the module. Healthy-path outputs are unchanged (`REQ-003`).

## Security considerations
- Both guards now survive `python -O`: production invariant enforcement no longer depends on a construct the interpreter can strip.
- The file's bandit `B101` findings drop from 2 to 0 at the source; no `# nosec` suppression is introduced.

## Rollback considerations
- Single-commit revert restores both asserts and the noqa; the sibling guard tests then fail again on HEAD behavior (they expect the typed errors). No persisted state is involved.

## Validation plan
- `grep -n "assert " scripts/agent/workflow_engine_adapter.py` returns nothing and `grep -n "noqa: B101" <file>` returns nothing (`REQ-001`).
- `uv run bandit -q scripts/agent/workflow_engine_adapter.py | grep -c ">> Issue: \[B101"` returns 0, down from the measured 2 (`REQ-004`).
- `uv run ruff check --select RUF100 scripts/agent/workflow_engine_adapter.py` reports no errors (1 before the change).
- Guard tests from sibling `20261108-201045_02` (`test_missing_engine_raises_wiring_error` (new), `test_missing_boundary_raises_protocol_error` (new)) pass after this procedure and fail on HEAD (HEAD raises `AssertionError` instead of the typed errors).
- `uv run pytest tests/agent/ -q` then full `uv run pytest tests/ -q`; lint/type/architecture gates per `rules/toolchain.md` (`uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`).

## Completion criteria
- The file contains zero `assert ` statements and zero `# noqa: B101` directives; the two typed guards raise `WorkflowEngineWiringError` (new) and `TurnBoundaryMissingError` (new) at the identical guard points; bandit file count for `B101` is 0; RUF100 clean; all existing suites green.

## Out of Scope
- The guard tests (plan row 2, sibling document `20261108-201045_02`).
- `pyproject.toml` lint-select changes (plan row demoted to Reference Files by the 2026-11-08 measurement: ruff 0.15.16 has no `B101` rule and `--select B` measures 171 findings); the plan's follow-up issue branch (REQ-005, carrying the measured counts) is outside this release unit and has not been filed in this pass.
- The identical assert sites in `llm_turn_runner.py`, `conversation_state_manager.py`, and `tool_round_completion.py` (plan Out-of-Scope; 27 bandit `B101` findings remain across `scripts/` after this procedure).
- Module docstring updates (owned by `162804_01`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | tests are hosted by sibling `20261108-201045_02` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | docs verified no-change; out of scope |

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
- **Requirement ID**: `REQ-001` (no asserts/noqa), `REQ-002` (typed guards), `REQ-003` (behavior preserving), `REQ-004` (bandit clean)
- **Source issue**: `issues/20261107-203226_wfaudit013_adapter-production-asserts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084014_wfaudit013_adapter-production-asserts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-201045
- **Related target files**: `scripts/agent/workflow_engine_adapter.py`

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-201045 -->
