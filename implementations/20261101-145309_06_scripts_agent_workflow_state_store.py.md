<!-- workitem: {"kind":"implementation-procedure","batch_id":"20261101-145309","seq":6,"source_plan":"plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md","source_issue":null,"source_review":null,"target_file":"scripts/agent/workflow/state_store.py","generated_at":"2026-11-01T14:53:09Z","schema_version":"1.0","schema_hash":"488513b688446992"} -->

## Goal

Strip the duplicated attempt/task SQL from `scripts/agent/workflow/state_store.py`, delegate to the canonical operation modules, and make `recover_stale_attempts` fail the stale attempt and its owning `running` task in one transaction (REQ-003, REQ-005, REQ-006, REQ-010, REQ-012 / AC-3, AC-5, AC-7).

## Scope

- Delete the duplicated `start_attempt` (`state_store.py:128-147`) and re-point `finish_attempt` (`:149-172`) and `update_task_status` (`:63-69`, inline duplicate) to `attempt_ops`/`task_ops`.
- `recover_stale_attempts` (`:279-316`): per stale attempt, one transaction doing the optimistic attempt update (`running -> failed`, `error` names stale recovery) plus `UPDATE tasks SET status='failed' ... WHERE task_id=? AND status='running'`; repeating recovery changes nothing further.
- Correct the stale comments (REQ-010) about started markers and task-status neutrality.

## Assumptions

- Plan `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` is Frozen; its 26-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` commit `384eb72` on 2026-11-01.
- Canonical semantics come from the Plan REQs (Plan `:41-52`): REQ-001 matrix `pending->{running,halted}`, `running->{completed,failed,halted}`, `failed->{running}`, `completed->failed` transitional, `halted` terminal; exactly three typed errors in `scripts/agent/workflow/errors.py`; `processed_events` as the completed-stage ledger (Plan UNK-02 default); recovery atomically fails the stale attempt and its owning `running` task (Plan UNK-03); claim accepts `pending` or `failed` only (Plan UNK-01).
- Landing-order dependency (Plan UNK-05): the wftaskapi001 procedures (`implementations/20261101-140834_*`, plan `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md`) are generated but Pending; the shared migration ledger code is fixed at landing time.
- Startup call site `orchestrator.py:92` (`recover_stale_attempts()`) stays unchanged; only its semantics tighten (Plan UNK-03: recovery also fails the owning task).

## Design decisions

- `find_stale_running_attempts` (`:250-277`, grace period `_STALE_GRACE_SEC`) keeps its query; the change is the per-attempt transactional effect.
- Task side-effect is conditional on `status='running'`: a task already terminal (owner wrote it after the crash) is left untouched — that is what makes repeated recovery idempotent.
- Remaining aggregates/diagnostics (`get_task_count`, `get_workflow_count`, `get_execute_attempt_count`, `get_artifact_uris`) stay in `StateStore` (wftaskapi001 row 01 moves only task aggregates, Pending).

## Alternatives considered

- Leaving the task status untouched (current behavior): rejected by Plan UNK-03 owner decision — a crashed turn must not leave a permanently `running` task.

## Implementation
### Target file
`scripts/agent/workflow/state_store.py`

### Procedure
1. Replace the three duplicate method bodies with delegations.
2. Wrap the per-attempt recovery in `db.transaction()` semantics (attempt UPDATE + task UPDATE + commit).
3. Update docstrings to state the atomic attempt+task effect and the idempotent repeat.

### Method
Direct edit; deletions plus body rewrites; public method names preserved.

### Details
- Current recovery (`:299-304`) updates only `attempts` and commits once at the end (`:314`); it never touches `tasks`.
- File size guard: `state_store.py` (11164 B) must stay under 20480 B — deletions and delegations reduce it.

## Compatibility considerations

- 7 test files reference `StateStore` (84 references, Plan blast-radius table); rows 12/13 update the workflow-state ones in Phase 3.
- Coordinate with wftaskapi001 row `implementations/20261101-140834_06_*` (Pending) on the delegation shape to avoid two different delegate layers (Plan UNK-05).

## Security considerations

- Status/attempt values written to SQL come only from the `models.py` enums, never from caller strings; all state SQL stays parameter-bound.
- Recovery `error` string is a fixed constant (`stale recovery`), not attacker-influenced.

## Rollback considerations

- Revert rows 04/05/06 as one unit; recovery revert restores attempt-only semantics, which stays safe on migrated rows (columns are additive).

## Validation plan

- `uv run pytest tests/agent/workflow/test_state_store.py -v` (row 13) and `tests/agent/workflow/test_workflow_state_store.py -v` (row 12).
- `uv run pytest tests/agent/workflow/test_workflow_recovery.py -v` (row 17: repeated recovery).
- Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`.

## Completion criteria

- No attempt or task SQL remains in `StateStore` except cross-table diagnostics; recovery atomically fails stale attempts and their `running` tasks, and re-running it is a no-op (AC-3, AC-5, AC-7).

## Out of Scope

- Task-aggregate ownership migration (wftaskapi001); grace-period tuning.

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
- **Workflow phase**: Phase 3 (Attempt lifecycle, ledger, and recovery)
- **Requirement ID**: `REQ-003`, `REQ-005`, `REQ-006`, `REQ-010`, `REQ-012`
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-145309
- **Related target files**: `scripts/agent/workflow/state_store.py`, `scripts/agent/workflow/attempt_ops.py`, `scripts/agent/workflow/task_ops.py`, `tests/agent/workflow/test_state_store.py`, `tests/agent/workflow/test_workflow_state_store.py`
