## Goal
Replace the `else 60` stage-timeout fallback in `scripts/agent/workflow/workflow_engine.py` with a typed error that names the missing stage and is raised before any attempt row or lease is created (`REQ-002`), and make the retry wait read the renamed `retry_wait_sec` (new) policy field (`REQ-003`/`REQ-004`).

## Scope
**Release unit**: wfaudit014-full

- Covers Plan `plans/20261108-084015_wfaudit014_retry-loop-dead-parameters.md` row 2 only: `scripts/agent/workflow/workflow_engine.py`.

## Assumptions
- Landing order: this procedure lands after procedure `implementations/20261108-211937_03_scripts_agent_workflow_models.py.md` (row 3), because the read of the renamed `retry_wait_sec` (new) policy attribute requires the renamed `RetryPolicy` field; the plan's Phase 3 order is models -> loader -> engine.
- Sibling `implementations/20261108-175155_02_scripts_agent_workflow_workflow_engine.py.md` (wfaudit015 facade rewrite of the `begin_stage_if_new` and artifact calls) is symbol-anchored and its regions are disjoint from the two edit sites here; either landing order works (plan Related Documents row).
- `WorkflowStageNotFoundError` (new) is not exported through `agent/workflow/__init__.py` in this procedure: the frozen target table has no `__init__.py` row, and tests import from `agent.workflow.workflow_engine` directly (the file's existing import block style).
- The fallback is currently unreachable through normal operation (`run` passes the literal stage ids `plan`, `execute`, `verify`; the loader enforces `_REQUIRED_STAGES`), which is why the issue classifies it as dead: the typed error converts the unreachable path into a stated contract (`REQ-002`).

## Design decisions
- Raise inside `_run_stage` immediately after `self._wdef.get_stage(stage_id)` returns `None` — before `begin_stage_if_new` and before the `asyncio.timeout` block — so no attempt row, event id, or lease horizon is created for the rejected stage (`REQ-002` acceptance).
- Subclass `Exception`, matching the file's existing engine error classes (`WorkflowHaltError`, `WorkflowTimeoutError`, `WorkflowStageFailure` at L84-92); the message names the workflow and the offending stage id.
- `_run_stage_with_retry` keeps its "no stage_def or not retryable -> single `_run_stage` call" gate unchanged: the single-call path now raises for an unknown stage id, which is the same contract.

## Alternatives considered
- Keep `else 60` but log a warning: rejected — a silent magic timeout is the exact behavior `REQ-002` removes.
- Raise inside `_run_stage_with_retry` only: rejected — `_run_stage` is the function that consumes `timeout` and creates the attempt row; guarding there leaves direct and future callers still able to reach the literal.

## Implementation
### Target file
`scripts/agent/workflow/workflow_engine.py`

### Procedure
Add the `WorkflowStageNotFoundError` (new) exception class, replace the timeout fallback in `_run_stage` with the raise, and rename the policy field read in `_run_stage_with_retry`.

### Method
1. After `class WorkflowStageFailure(Exception):` (the last of the three engine error classes), add:
   `WorkflowStageNotFoundError` (new) with docstring "Raised when a requested stage_id has no `StageDefinition` in the loaded workflow definition." — a plain `Exception` subclass with no extra behavior.
2. In `_run_stage`, HEAD lines:
   `stage_def = self._wdef.get_stage(stage_id)` / `timeout = stage_def.timeout_sec if stage_def else 60`
   become:
   `stage_def = self._wdef.get_stage(stage_id)` then `if stage_def is None: raise WorkflowStageNotFoundError(f"Workflow '{self._wdef.name}' has no stage '{stage_id}'")` then `timeout = stage_def.timeout_sec`. The raise sits above the `event_id` line and the `begin_stage_if_new(...)` call, so the rejected stage produces no attempt row and no lease.
3. In `_run_stage_with_retry`, HEAD line `wait = policy.backoff_sec` -> `wait = policy.retry_wait_sec` (new), keeping the local `wait` name.

### Details
- No other reads of the wait value: the retry log line and `await asyncio.sleep(wait)` already consume the local `wait`; the span attributes and lease math (`timeout + _LEASE_MARGIN_SEC`) are untouched.
- No import, `__all__`, or facade edits in this file or `agent/workflow/__init__.py`.

## Compatibility considerations
- A definition that actually reaches `_run_stage` with an unknown stage id now raises instead of running with a 60-second timeout — no known production path does this today (loader enforces the three required stage ids); the change surfaces contract violations instead of masking them.
- Deploy: no artifact tied to this file alone; it ships with the plan's config-sync step (row 6).

## Security considerations
- The error message interpolates the stage id and workflow name (internal identifiers), not user input.

## Rollback considerations
- Revert the commit: `else 60` returns and the wait read returns to `backoff_sec` (coordinate with rows 3-4 reverts, which the plan sequences as one release unit).

## Validation plan
- `tests/agent/workflow/test_workflow_engine.py` (procedure `implementations/20261108-211937_08_tests_agent_workflow_test_workflow_engine.py.md`): the missing-stage test asserts `WorkflowStageNotFoundError` and zero attempt rows (`count_attempts == 0`); the constant-wait test pins the `retry_wait_sec` (new) numerics against `asyncio.sleep` arguments.
- `uv run pytest tests/agent/workflow/ tests/agent/test_orchestrator.py -q`, then full `uv run pytest tests/ -q`; lint/type gates per `rules/toolchain.md`.
- `grep -n "else 60" scripts/agent/workflow/workflow_engine.py` returns nothing (plan Validation plan grep gate).

## Completion criteria
- `REQ-002`: unknown stage id raises `WorkflowStageNotFoundError` (new) with the stage name before any attempt row/lease; `REQ-003`/`REQ-004`: the wait is read from `retry_wait_sec` (new) with identical numerics; suite green.

## Out of Scope
- Exporting `WorkflowStageNotFoundError` (new) through the package facade (`agent/workflow/__init__.py`) — no frozen row covers that file.
- Engine-side failure-kind handling (`_ERROR_KIND_*` classification and `retry_on` gating), unchanged per `REQ-001`.

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
- **Requirement ID**: `REQ-002`, `REQ-003`, `REQ-004`
- **Source issue**: `issues/20261107-203227_wfaudit014_retry-loop-dead-parameters.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084015_wfaudit014_retry-loop-dead-parameters.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-211937
- **Related target files**: scripts/agent/workflow/workflow_engine.py
