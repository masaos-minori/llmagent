"""Regenerate the wfrecovery001 implementation-procedure documents (batch 20261101-145309)
in the canonical 14-section format used by batch 20261101-140834.

Reads each existing skeleton file, keeps its line-1 workitem marker, and rewrites the
body from the verified content embedded below. Run: `uv run python tools/gen_wfrecovery_procedures.py`.
"""

from __future__ import annotations

from pathlib import Path

BATCH = "20261101-145309"
PLAN = "plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md"
ISSUE = "issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md"
GENERATED_AT = "20261101-145309"

COMMON_ASSUMPTIONS = [
    f"Plan `{PLAN}` is Frozen; its 26-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table.",
    "All baseline cites below were re-verified against branch `master` commit `384eb72` on 2026-11-01.",
    "Canonical semantics come from the Plan REQs (Plan `:41-52`): REQ-001 matrix `pending->{running,halted}`, `running->{completed,failed,halted}`, `failed->{running}`, `completed->failed` transitional, `halted` terminal; exactly three typed errors in `scripts/agent/workflow/errors.py`; `processed_events` as the completed-stage ledger (Plan UNK-02 default); recovery atomically fails the stale attempt and its owning `running` task (Plan UNK-03); claim accepts `pending` or `failed` only (Plan UNK-01).",
    "Landing-order dependency (Plan UNK-05): the wftaskapi001 procedures (`implementations/20261101-140834_*`, plan `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md`) are generated but Pending; the shared migration ledger code is fixed at landing time.",
]

TOOLCHAIN = "Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`."

EXEC_TABLE = """### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |"""

BLOCKER_PLACEHOLDER = """| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |"""

WORK_ITEMS_PLACEHOLDER = """| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |"""

DEFAULT_SECURITY = [
    "Status/attempt values written to SQL come only from the `models.py` enums, never from caller strings; all state SQL stays parameter-bound.",
]


TARGETS = {
    "01": "scripts/agent/workflow/models.py",
    "02": "scripts/agent/workflow/errors.py",
    "03": "scripts/agent/workflow/task_ops.py",
    "04": "scripts/agent/workflow/attempt_ops.py",
    "05": "scripts/agent/workflow/idempotency_ops.py",
    "06": "scripts/agent/workflow/state_store.py",
    "07": "scripts/agent/workflow/workflow_engine.py",
    "08": "scripts/agent/workflow_engine_adapter.py",
    "09": "scripts/agent/tool_audit.py",
    "10": "scripts/db/schema_sql.py",
    "11": "scripts/agent/services/workflow_schema.py",
    "12": "tests/agent/workflow/test_workflow_state_store.py",
    "13": "tests/agent/workflow/test_state_store.py",
    "14": "tests/agent/workflow/test_workflow_engine.py",
    "15": "tests/agent/workflow/test_workflow_stage_persistence.py",
    "16": "tests/agent/workflow/test_workflow_models.py",
    "17": "tests/agent/workflow/test_workflow_recovery.py",
    "18": "tests/agent/workflow/test_workflow_concurrency.py",
    "19": "tests/agent/test_orchestrator.py",
    "20": "tests/agent/test_repl_health.py",
    "21": "tests/agent/test_tool_audit.py",
    "22": "tests/db/test_create_schema.py",
    "23": "docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md",
    "24": "docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md",
    "25": "docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md",
    "26": "scripts/db/migrations_workflow.py",
}


def doc(
    path: Path,
    *,
    seq: str,
    goal: str,
    scope: list[str],
    assumptions: list[str],
    design: list[str],
    alternatives: list[str],
    procedure: list[str],
    method: str,
    details: list[str],
    compatibility: list[str],
    security: list[str],
    rollback: list[str],
    validation: list[str],
    completion: list[str],
    out_of_scope: list[str],
    reqs: str,
    phase: str,
    related: str,
    new_target: bool = False,
    blockers: str = BLOCKER_PLACEHOLDER,
) -> None:
    marker = path.read_text(encoding="utf-8").splitlines()[0]
    body = f"""{marker}

## Goal

{goal}

## Scope

{chr(10).join(f"- {s}" for s in scope)}

## Assumptions

{chr(10).join(f"- {s}" for s in COMMON_ASSUMPTIONS + assumptions)}

## Design decisions

{chr(10).join(f"- {s}" for s in design)}

## Alternatives considered

{chr(10).join(f"- {s}" for s in alternatives)}

## Implementation
### Target file
`{TARGETS[seq]}`{" (new)" if new_target else ""}

### Procedure
{chr(10).join(f"{i}. {s}" for i, s in enumerate(procedure, 1))}

### Method
{method}

### Details
{chr(10).join(f"- {s}" for s in details)}

## Compatibility considerations

{chr(10).join(f"- {s}" for s in compatibility)}

## Security considerations

{chr(10).join(f"- {s}" for s in DEFAULT_SECURITY + security)}

## Rollback considerations

{chr(10).join(f"- {s}" for s in rollback)}

## Validation plan

{chr(10).join(f"- {s}" for s in validation)}

## Completion criteria

{chr(10).join(f"- {s}" for s in completion)}

## Out of Scope

{chr(10).join(f"- {s}" for s in out_of_scope)}

## Execution Status

{EXEC_TABLE}

### Blocker Log
{blockers}

### Work Items Created
{WORK_ITEMS_PLACEHOLDER}

## Traceability
- **Workflow phase**: {phase}
- **Requirement ID**: {reqs}
- **Source issue**: {ISSUE}
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: {PLAN}
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: {GENERATED_AT}
- **Related target files**: `{TARGETS[seq]}`{', ' if related else ''}{related}
"""
    path.write_text(body, encoding="utf-8")
    print(f"generated {path.name}")


def main() -> None:
    root = Path("implementations")
    files = sorted(root.glob(f"{BATCH}_*.md"))
    by_seq = {f.name.split("_")[1]: f for f in files}
    if len(files) != 26:
        raise SystemExit(f"expected 26 batch files, found {len(files)}: {files}")

    doc(
        by_seq["01"],
        seq="01",
        goal="Replace the free-text status comments in `scripts/agent/workflow/models.py` with typed `TaskStatus`/`AttemptStatus` enums and one canonical transition matrix that every state-writing module imports (REQ-001 / AC-1).",
        scope=[
            "Add `TaskStatus` (`pending`, `running`, `completed`, `failed`, `halted`) and `AttemptStatus` (`running`, `completed`, `failed`).",
            "Add `TASK_TRANSITIONS` per the REQ-001 matrix and `ATTEMPT_TERMINAL_STATUSES` (`completed`, `failed`).",
            "Add `can_transition(current, target)` as the single query helper used by `task_ops.py`, `attempt_ops.py`, and the migration precondition.",
            "Replace the status comments at `models.py:20,34` with references to the enums.",
        ],
        assumptions=[
            "`TaskRecord.status`/`AttemptRecord.status` stay `str` fields; enum typing is enforced at the write sites, not by changing dataclass field types (avoids row-mapping churn)."
        ],
        design=[
            "`TASK_TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]]` is the only place the matrix is written; `completed -> failed` is included and marked transitional (removed by the retry issue per REQ-001).",
            "`halted` and `completed` (except the transitional edge) are terminal: empty target sets.",
            "Enum values are plain strings identical to the SQL `CHECK` vocabulary that row 10 adds, so the REQ-001 equality test can compare enum members against the parsed DDL.",
        ],
        alternatives=[
            "String constants instead of enums: rejected — the REQ-001 acceptance criterion requires an enum-to-CHECK equality test, which needs an enumerable source."
        ],
        procedure=[
            "Add `class TaskStatus(str, Enum)` with the five members and `class AttemptStatus(str, Enum)` with the three members.",
            "Add `TASK_TRANSITIONS` and `ATTEMPT_TERMINAL_STATUSES` constants with the REQ-001 matrix.",
            "Add `can_transition(current: TaskStatus, target: TaskStatus) -> bool`.",
            "Reword the comments at `:20` (task status) and `:34` (attempt status) to name the enums.",
        ],
        method="Direct edit; additive only — no existing function or dataclass field signature changes.",
        details=[
            "Matrix edges: `pending -> {running, halted}`; `running -> {completed, failed, halted}`; `failed -> {running}`; `completed -> {failed}` (transitional); `halted -> {}`.",
            "`models.py` currently has no status enum (comments at `:20,34`); importers must not re-declare status literals afterwards (enforced by the row 16 test).",
        ],
        compatibility=[
            "Rows 03/06/07/08 import the enums and matrix; the SQL `CHECK` vocabulary added by row 10 must equal the enum values exactly (REQ-001 test, row 16).",
        ],
        security=[],
        rollback=[
            "Purely additive change; revert is `git checkout -- scripts/agent/workflow/models.py` with no data impact."
        ],
        validation=[
            "`uv run pytest tests/agent/workflow/test_workflow_models.py -v` (row 16 adds the matrix and CHECK-vocabulary tests).",
            TOOLCHAIN,
        ],
        completion=[
            "The five/four-value vocabulary is defined once, the matrix is importable, and no other module defines its own status literal set (AC-1).",
        ],
        out_of_scope=[
            "SQL `CHECK` constraints (row 10); transition enforcement logic (rows 03/04/06)."
        ],
        reqs="`REQ-001`",
        phase="Phase 1 (Vocabulary, errors, and task transitions)",
        related="`scripts/agent/workflow/errors.py`, `scripts/agent/workflow/task_ops.py`, `scripts/db/schema_sql.py`, `tests/agent/workflow/test_workflow_models.py`",
    )

    doc(
        by_seq["02"],
        seq="02",
        goal="Create `scripts/agent/workflow/errors.py` with the three typed workflow-state errors that rows 03/04/05/06/07/08 raise (REQ-002, REQ-004 / AC-2, AC-4).",
        scope=[
            "New file in the existing directory `scripts/agent/workflow/`: `TaskNotFoundError(KeyError)`, `TaskTransitionError(RuntimeError)`, `StageAlreadyRunningError(RuntimeError)`.",
            "`TaskTransitionError.__init__(current: str, target: str, ...)` builds a message that names the current status.",
        ],
        assumptions=[
            "`TaskTransitionError` subclasses `RuntimeError` because `tests/agent/test_orchestrator.py:2116` matches on the message containing `halted` and the adapter already surfaces `RuntimeError` (`agent_03_03` `:40`); its message format must keep the current status string in it.",
            "Exactly three error classes exist in this Plan; no base `WorkflowPersistenceError` hierarchy is introduced.",
        ],
        design=[
            "`TaskNotFoundError` subclasses `KeyError` so a missing task also behaves like a lookup miss for existing callers.",
            "`TaskTransitionError` is reused for attempt-level zero-row transitions (its docstring states it covers task and attempt status transitions); its message names the current status so the orchestrator halted test keeps passing.",
            "`StageAlreadyRunningError` carries `task_id`/`stage_id` attributes for the row 18 concurrency test.",
        ],
        alternatives=[
            "One generic error class: rejected — REQ-002/REQ-004 name three distinct conditions (missing row, wrong current status, concurrent start) and tests assert each type."
        ],
        procedure=[
            "Create the module with the three classes and docstrings stating each raise condition.",
            "Message templates: `TaskNotFoundError(task_id)` names the id; `TaskTransitionError` renders `current` and `target` statuses; `StageAlreadyRunningError` names the task/stage.",
        ],
        method="New file creation (no imports from `scripts/agent/workflow/` siblings except `models` for enum typing).",
        details=[
            "No existing workflow error module exists; engine-local `WorkflowHaltError`/`WorkflowTimeoutError` stay in `workflow_engine.py:77,81` (control-flow, not persistence-state) and are not moved.",
        ],
        compatibility=[
            "`errors.py` is imported by rows 03/04/05/06/07/08; keeping the `RuntimeError` base preserves the adapter/orchestrator error contract (row 19 tests)."
        ],
        security=[],
        rollback=[
            "Delete the file and revert the importing rows together; nothing persists these classes."
        ],
        validation=[
            "Import smoke via the row 12/17/18 tests once those rows land; static: mypy + ruff.",
            TOOLCHAIN,
        ],
        completion=[
            "The three classes exist, are the only state-error types, and `TaskTransitionError` instances stringify with the current status (AC-2)."
        ],
        out_of_scope=[
            "Engine control-flow errors (`WorkflowHaltError`, `WorkflowTimeoutError`); HTTP/transport errors."
        ],
        new_target=True,
        reqs="`REQ-002`, `REQ-004`",
        phase="Phase 1 (Vocabulary, errors, and task transitions)",
        related="`scripts/agent/workflow/task_ops.py`, `scripts/agent/workflow/attempt_ops.py`, `scripts/agent/workflow/idempotency_ops.py`",
    )

    doc(
        by_seq["03"],
        seq="03",
        goal="Make task-status writes in `scripts/agent/workflow/task_ops.py` conditional single-row transitions and add the claim entry point used by engine and adapter (REQ-002, REQ-007 / AC-2, AC-6).",
        scope=[
            "Replace the unconditional `update_task_status` (`task_ops.py:21-36`, ignores row count) with `transition_task_status(db, task_id, current, target)` implementing the REQ-001 matrix.",
            "Add `claim_task_running(db, task_id)` accepting `pending` or `failed` only.",
            "Zero updated rows: `TaskNotFoundError` when the task row is absent, `TaskTransitionError` otherwise.",
        ],
        assumptions=[
            "`StateStore.update_task_status` (`state_store.py:63-69`) is an inline duplicate that row 06 converts into a delegate; both call paths land in one unit so no caller sees a half-migrated API."
        ],
        design=[
            "Transition is one statement: `UPDATE tasks SET status=?, updated_at=? WHERE task_id=? AND status=?`; `rowcount` decides the outcome — no read-then-write race window.",
            "Matrix legality is checked in Python via `can_transition` before the SQL runs, so an illegal edge never reaches the database.",
            "`claim_task_running` is the single claim surface (REQ-007: `running`, `completed`, `halted` rejected).",
        ],
        alternatives=[
            "Optimistic version column: rejected — the status column itself is the expected-value guard the REQs define; adding a column widens the migration."
        ],
        procedure=[
            "Add `transition_task_status` and `claim_task_running` using `models.TASK_TRANSITIONS`.",
            "Rewrite `update_task_status` to delegate to `transition_task_status` for the existing (engine/adapter) call sites, so its signature survives Phase 1 while rows 07/08 migrate callers to explicit transitions.",
            "Raise the row-02 errors on the zero-row branches (`SELECT 1 FROM tasks WHERE task_id=?` distinguishes not-found from wrong-status).",
        ],
        method="Direct edit; additive functions plus a body rewrite of `update_task_status`.",
        details=[
            "Existing SQL in `task_ops.py` is parameter-bound already (`:30-36`); the only behavioral change is the `AND status=?` clause and the row-count branch.",
            "Interaction with wftaskapi001 row `implementations/20261101-140834_01_*` (Pending): that procedure renames `idempotency_key` to `task_nonce` and rewords the same docstring region; whichever lands first is the baseline and the other re-applies on top (Plan UNK-05).",
        ],
        compatibility=[
            "`tests/agent/test_orchestrator.py` mocks `update_task_status` (`:2758-2896`); row 19 updates those assertions in Phase 4.",
            "The adapter halted-resume message contract (`RuntimeError` naming `halted`) is preserved via `TaskTransitionError` (row 02 decision).",
        ],
        security=[
            "No `eval`/string interpolation of statuses; enum-typed parameters only."
        ],
        rollback=[
            "Revert this file plus the row-06 delegate in one commit; no persisted shape changes."
        ],
        validation=[
            "`uv run pytest tests/agent/workflow/test_workflow_state_store.py -v` after row 12 adds the invalid-status/zero-row API tests.",
            "`uv run pytest tests/agent/workflow/test_workflow_concurrency.py -v` (row 18, claim race).",
            TOOLCHAIN,
        ],
        completion=[
            "Every task-status write goes through a conditional single-row update; illegal edges and zero-row outcomes raise typed errors; claim accepts only `pending`/`failed` (AC-2, AC-6).",
        ],
        out_of_scope=[
            "Attempt transitions (rows 04/05); engine/adapter call-site migration (rows 07/08)."
        ],
        reqs="`REQ-002`, `REQ-007`",
        phase="Phase 1 (Vocabulary, errors, and task transitions)",
        related="`scripts/agent/workflow/models.py`, `scripts/agent/workflow/errors.py`, `scripts/agent/workflow/state_store.py`, `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/workflow_engine_adapter.py`",
    )

    doc(
        by_seq["04"],
        seq="04",
        goal="Remove the bypass `start_attempt` from `scripts/agent/workflow/attempt_ops.py`, make the canonical attempt lifecycle (`begin_immediate` insert + terminal-only finish) the only path, and gate `finish_attempt` to terminal statuses with a conditional single-row update (REQ-003, REQ-005, REQ-012 / AC-3, AC-5, AC-9).",
        scope=[
            "Delete `start_attempt` (`attempt_ops.py:12-31`) — the marker-less, number-less direct insert.",
            "Rewrite `finish_attempt` (`:34-48`): `status` restricted to `ATTEMPT_TERMINAL_STATUSES`; `UPDATE attempts SET status=?, ended_at=?, error=? WHERE attempt_id=? AND status='running'`; one updated row required.",
            "Keep `count_attempts` (`:50-56`) unchanged (diagnostics use).",
        ],
        assumptions=[
            "The canonical attempt insert moves to `idempotency_ops.begin_immediate` (row 05); this row only removes the bypass and fixes finish."
        ],
        design=[
            "Zero-row finish: `TaskNotFoundError` when the attempt row is absent, `TaskTransitionError` when it exists but is not `running` (its docstring covers attempt-level transitions, row 02).",
            "Non-terminal `status` arguments raise `ValueError` before any SQL — the docstring correction REQ-005 documents terminal-only semantics.",
        ],
        alternatives=[
            "Keeping `start_attempt` as a deprecated wrapper: rejected — AC-9 forbids any caller path that bypasses the canonical transaction."
        ],
        procedure=[
            "Delete `start_attempt` and its import uses in `state_store.py` (row 06) and tests (rows 12/15).",
            "Rewrite `finish_attempt` signature to `finish_attempt(db, attempt_id, status: AttemptStatus, error: str | None)` with the conditional update.",
            "Fix the misleading docstring (it currently advertises idempotency the function never provided).",
        ],
        method="Direct edit; one deletion, one body rewrite.",
        details=[
            "Callers today: `state_store.finish_attempt` (`state_store.py:149`) and engine via store (`workflow_engine.py:280,291,300`); all land in rows 06/07.",
            "`error` naming for recovery writes is row 06's concern (`stale recovery` kind), not this function's.",
        ],
        compatibility=[
            "Removing `start_attempt` breaks the raw test helpers in rows 12/15 in the same phase; no production caller outside `StateStore`."
        ],
        security=[
            "Status value reaches SQL only through the enum-restricted parameter."
        ],
        rollback=[
            "Revert rows 04+05+06 as one unit; attempt rows written by the canonical path stay readable by the old code except for the new `attempt_number` column (row 10 DDL)."
        ],
        validation=[
            "`uv run pytest tests/agent/workflow/test_workflow_stage_persistence.py -v` (row 15).",
            '`rg "start_attempt" scripts tests` → no `attempt_ops`/`StateStore` bypass remains (AC-9).',
            TOOLCHAIN,
        ],
        completion=[
            "`finish_attempt` can only complete-or-fail a `running` attempt, one row; `start_attempt` no longer exists anywhere (AC-5, AC-9).",
        ],
        out_of_scope=[
            "Attempt-number allocation (row 05); recovery error-kind strings (row 06)."
        ],
        reqs="`REQ-003`, `REQ-005`, `REQ-012`",
        phase="Phase 3 (Attempt lifecycle, ledger, and recovery)",
        related="`scripts/agent/workflow/idempotency_ops.py`, `scripts/agent/workflow/state_store.py`, `tests/agent/workflow/test_workflow_stage_persistence.py`",
    )

    doc(
        by_seq["05"],
        seq="05",
        goal="Turn `scripts/agent/workflow/idempotency_ops.py` into the single canonical stage-start/finish pair: `begin_stage_if_new` starts the attempt with `attempt_number = MAX + 1` in one transaction and skips only on a completed-stage ledger row (REQ-003, REQ-004 / AC-3, AC-4).",
        scope=[
            'Remove the `processed_events` "started" marker writes (`idempotency_ops.py:18-67`, comments `started (not completed)`).',
            "`begin_stage_if_new(db, event_id, task_id, stage_id)` becomes `begin_immediate`-style canonical start: ledger check → running-attempt check → `INSERT INTO attempts(..., attempt_number)` in one transaction.",
            "Add `finish_stage(db, ...)` counterpart that marks the attempt terminal and writes the ledger row (`event_id`, `task_id`, `stage_id`, `attempt_id`, `attempt_number`) in the same transaction.",
        ],
        assumptions=[
            "Ledger choice is the completed-event ledger (Plan UNK-02 default): a stage is skipped only when a `processed_events` row for the (task, stage) pair exists."
        ],
        design=[
            "Concurrent start guard: a `running` attempt for the same (task, stage) raises `StageAlreadyRunningError` before any insert; the unique index `idx_attempts_task_stage_number` (row 10) is the race backstop.",
            "`attempt_number` is allocated as `MAX(attempt_number)+1` over the (task_id, stage_id) pair inside the same transaction as the attempt insert (REQ-003).",
            "`event_id` uniqueness stays the idempotency backstop for repeated finish attempts; `result_json` stays out — `REQ-008` adds only `attempt_id`/`attempt_number`.",
        ],
        alternatives=[
            "Attempt-status ledger (skip on attempt `completed` instead of a ledger row): recorded as the rejected alternative in the Plan (UNK-02) — it would drop `processed_events`, which the startup check, deploy check, and ADR name."
        ],
        procedure=[
            "Replace the started-marker insert with the attempts insert + numbering block.",
            "Rewrite the skip check to `SELECT 1 FROM processed_events WHERE task_id=? AND stage_id=?` (ledger semantics, REQ-004).",
            "Add `finish_stage` delegating the attempt update to `attempt_ops.finish_attempt` (row 04) then inserting the ledger row, one transaction.",
            "Update the module docstring and the two `started (not completed)` comments (`:18-67` region).",
        ],
        method="Direct edit; function bodies rewritten, module-level names kept where callers exist.",
        details=[
            "Engine call site: `workflow_engine.py:264` (`begin_stage_if_new`) and finish sites `:280,291,300` migrate in row 07; the function name stays stable through Phase 3.",
            "`event_id` generation (`workflow_engine.py:262`) is unchanged (row 07).",
        ],
        compatibility=[
            "Old databases still hold `started` marker rows; the row-26 migration rebuild decision for marker rows is governed by Plan UNK-07 (precondition fails closed and lists them) — do not silently map them."
        ],
        security=["Ledger lookups and inserts stay parameter-bound."],
        rollback=[
            "Revert with rows 04/06; the added ledger columns (row 10) tolerate the old code path, so a code revert alone is safe."
        ],
        validation=[
            "`uv run pytest tests/agent/workflow/test_workflow_stage_persistence.py -v` (row 15: double-completion skip, concurrent-start rejection).",
            "`uv run pytest tests/agent/workflow/test_workflow_concurrency.py -v` (row 18: numbering race).",
            TOOLCHAIN,
        ],
        completion=[
            "Exactly one code path inserts an attempt; a stage re-runs after failure, skips only on a ledger row, and rejects a concurrent start with `StageAlreadyRunningError` (AC-3, AC-4).",
        ],
        out_of_scope=[
            "Ledger DDL columns (row 10) and their migration (row 26); engine retry budget (row 07)."
        ],
        reqs="`REQ-003`, `REQ-004`",
        phase="Phase 3 (Attempt lifecycle, ledger, and recovery)",
        related="`scripts/agent/workflow/attempt_ops.py`, `scripts/agent/workflow/workflow_engine.py`, `scripts/db/schema_sql.py`, `scripts/db/migrations_workflow.py`",
    )

    doc(
        by_seq["06"],
        seq="06",
        goal="Strip the duplicated attempt/task SQL from `scripts/agent/workflow/state_store.py`, delegate to the canonical operation modules, and make `recover_stale_attempts` fail the stale attempt and its owning `running` task in one transaction (REQ-003, REQ-005, REQ-006, REQ-010, REQ-012 / AC-3, AC-5, AC-7).",
        scope=[
            "Delete the duplicated `start_attempt` (`state_store.py:128-147`) and re-point `finish_attempt` (`:149-172`) and `update_task_status` (`:63-69`, inline duplicate) to `attempt_ops`/`task_ops`.",
            "`recover_stale_attempts` (`:279-316`): per stale attempt, one transaction doing the optimistic attempt update (`running -> failed`, `error` names stale recovery) plus `UPDATE tasks SET status='failed' ... WHERE task_id=? AND status='running'`; repeating recovery changes nothing further.",
            "Correct the stale comments (REQ-010) about started markers and task-status neutrality.",
        ],
        assumptions=[
            "Startup call site `orchestrator.py:92` (`recover_stale_attempts()`) stays unchanged; only its semantics tighten (Plan UNK-03: recovery also fails the owning task)."
        ],
        design=[
            "`find_stale_running_attempts` (`:250-277`, grace period `_STALE_GRACE_SEC`) keeps its query; the change is the per-attempt transactional effect.",
            "Task side-effect is conditional on `status='running'`: a task already terminal (owner wrote it after the crash) is left untouched — that is what makes repeated recovery idempotent.",
            "Remaining aggregates/diagnostics (`get_task_count`, `get_workflow_count`, `get_execute_attempt_count`, `get_artifact_uris`) stay in `StateStore` (wftaskapi001 row 01 moves only task aggregates, Pending).",
        ],
        alternatives=[
            "Leaving the task status untouched (current behavior): rejected by Plan UNK-03 owner decision — a crashed turn must not leave a permanently `running` task."
        ],
        procedure=[
            "Replace the three duplicate method bodies with delegations.",
            "Wrap the per-attempt recovery in `db.transaction()` semantics (attempt UPDATE + task UPDATE + commit).",
            "Update docstrings to state the atomic attempt+task effect and the idempotent repeat.",
        ],
        method="Direct edit; deletions plus body rewrites; public method names preserved.",
        details=[
            "Current recovery (`:299-304`) updates only `attempts` and commits once at the end (`:314`); it never touches `tasks`.",
            "File size guard: `state_store.py` (11164 B) must stay under 20480 B — deletions and delegations reduce it.",
        ],
        compatibility=[
            "7 test files reference `StateStore` (84 references, Plan blast-radius table); rows 12/13 update the workflow-state ones in Phase 3.",
            "Coordinate with wftaskapi001 row `implementations/20261101-140834_06_*` (Pending) on the delegation shape to avoid two different delegate layers (Plan UNK-05).",
        ],
        security=[
            "Recovery `error` string is a fixed constant (`stale recovery`), not attacker-influenced."
        ],
        rollback=[
            "Revert rows 04/05/06 as one unit; recovery revert restores attempt-only semantics, which stays safe on migrated rows (columns are additive)."
        ],
        validation=[
            "`uv run pytest tests/agent/workflow/test_state_store.py -v` (row 13) and `tests/agent/workflow/test_workflow_state_store.py -v` (row 12).",
            "`uv run pytest tests/agent/workflow/test_workflow_recovery.py -v` (row 17: repeated recovery).",
            TOOLCHAIN,
        ],
        completion=[
            "No attempt or task SQL remains in `StateStore` except cross-table diagnostics; recovery atomically fails stale attempts and their `running` tasks, and re-running it is a no-op (AC-3, AC-5, AC-7).",
        ],
        out_of_scope=[
            "Task-aggregate ownership migration (wftaskapi001); grace-period tuning."
        ],
        reqs="`REQ-003`, `REQ-005`, `REQ-006`, `REQ-010`, `REQ-012`",
        phase="Phase 3 (Attempt lifecycle, ledger, and recovery)",
        related="`scripts/agent/workflow/attempt_ops.py`, `scripts/agent/workflow/task_ops.py`, `tests/agent/workflow/test_state_store.py`, `tests/agent/workflow/test_workflow_state_store.py`",
    )

    doc(
        by_seq["07"],
        seq="07",
        goal="Make `scripts/agent/workflow/workflow_engine.py` claim tasks through the transition API, run retries from the persisted attempt number with a budget that survives restarts, and expose the current attempt number for audit correlation (REQ-007, REQ-009 / AC-6, AC-8).",
        scope=[
            "`run()` (`workflow_engine.py:162-186`): replace the unconditional status writes (`:175,181,184,186`) with `claim_task_running` + terminal transitions via `StateStore` delegates.",
            "Retry loop: replace the in-memory `attempt = 0` (`:202`) with the persisted current attempt number from the canonical start (row 05) and enforce `max_attempts` across process restarts.",
            "Expose `current_attempt_number` on the engine for the adapter (row 08).",
        ],
        assumptions=[
            "`begin_stage_if_new` (`:264`) and `finish_attempt` sites (`:280,291,300`) keep their call shape through Phase 3; this row only wires claim/numbering."
        ],
        design=[
            "Claim happens before any stage runs; `running`/`completed`/`halted` tasks raise (`StageAlreadyRunningError` semantics for a live task, `TaskTransitionError` otherwise) instead of silently re-entering (`:172-176` today reuses any existing task).",
            "Budget rule: attempts already persisted for the (task, stage) pair count against `max_attempts`, so a restarted turn cannot restart a stage indefinitely.",
        ],
        alternatives=[
            "Resetting numbering per process (current behavior): rejected — REQ-007 requires the budget to span restarts, which in-memory counters cannot provide."
        ],
        procedure=[
            "Insert the claim call at the top of `run()`; remove the existing-task status-agnostic reuse.",
            "Read the persisted attempt number from the row-05 start result instead of `attempt = 0` (`:202`).",
            "Store the current attempt number on the engine instance after each stage start.",
            "Route terminal writes through `transition_task_status`.",
        ],
        method="Direct edit; control-flow rewrite of `run()` and `_execute_stage_with_retry`.",
        details=[
            "`event_id` composition (`:262`) is unchanged; ledger semantics come from row 05.",
            "`WorkflowHaltError`/`WorkflowTimeoutError` (`:77,81`) stay engine-local.",
        ],
        compatibility=[
            "Row 14 rewrites the engine tests that assume in-memory numbering (`test_workflow_engine.py:111-161,186-206`); row 19 updates orchestrator-level assertions."
        ],
        security=[],
        rollback=[
            "Engine revert alone is safe if rows 05/06 are reverted with it (the claim and numbering APIs they call are the changed surface)."
        ],
        validation=[
            "`uv run pytest tests/agent/workflow/test_workflow_engine.py -v` (row 14).",
            "`uv run pytest tests/agent/workflow/test_workflow_recovery.py -v` (row 17: resume after failed attempts continues numbering).",
            TOOLCHAIN,
        ],
        completion=[
            "A task can only enter `running` via claim; stage attempts continue across restarts and respect `max_attempts`; `current_attempt_number` is readable after each stage (AC-6, AC-8).",
        ],
        out_of_scope=["Adapter resume guard (row 08); audit payload (row 09)."],
        reqs="`REQ-007`, `REQ-009`",
        phase="Phase 4 (Engine, adapter, and audit correlation)",
        related="`scripts/agent/workflow/task_ops.py`, `scripts/agent/workflow/idempotency_ops.py`, `scripts/agent/workflow_engine_adapter.py`, `tests/agent/workflow/test_workflow_engine.py`",
    )

    doc(
        by_seq["08"],
        seq="08",
        goal="Route `scripts/agent/workflow_engine_adapter.py` status writes through the transition API, keep the halted-resume guard behavior, and pass the persisted attempt number to `audit_stage_completed` (REQ-007, REQ-009 / AC-6, AC-8).",
        scope=[
            "Resume guard (`workflow_engine_adapter.py:279-281`): replace the local `halted` check with the same claim contract (delegating to row 03 semantics); message keeps containing `halted` so `tests/agent/test_orchestrator.py:2116` still matches.",
            "Exit-status writes: `_status_for_exit` (`:49-59`) results are written via `transition_task_status` at the halted site (`:204`) and `_record_exit_status` (`:224-240`, write at `:235`), including the transitional `completed -> failed` edge.",
            "Audit call (`:375`): pass `attempt_number=engine.current_attempt_number`.",
        ],
        assumptions=[
            "Cancellation is recorded `halted` (docs `agent_03_03:83,88`); that vocabulary choice is unchanged by this Plan.",
        ],
        design=[
            "The adapter stops composing its own status SQL paths and only calls `task_ops` transitions exposed through `StateStore`.",
            "`attempt_id=turn_id` at `:353` (tool-loop audit correlation) is explicitly out of this Plan's scope (it belongs to the lease plan `plans/20261030-114516_wflease001_stale-attempt-lease.md` territory).",
        ],
        alternatives=[
            'Keeping the guard as a local `if status == "halted"`: rejected — two guards on one contract drift (REQ-007 names one contract).'
        ],
        procedure=[
            "Replace `:279-281` with a call that raises `RuntimeError` (message names `halted`) for `halted`, `TaskTransitionError` for `running`/`completed`, and claims `pending`/`failed` via `claim_task_running`.",
            "Convert the two status-write sites to `transition_task_status` calls.",
            "Add the `attempt_number` argument to the `audit_stage_completed` call at `:375`.",
        ],
        method="Direct edit at four cited sites.",
        details=[
            "Halted-then-cancelled repeat writes: the transition matrix makes a second `running -> halted` on a `halted` task raise — the adapter must not swallow it silently; row 19 pins the expected test outcome.",
        ],
        compatibility=[
            "Row 21 tests the audit payload change; row 19 keeps the orchestrator mock assertions consistent."
        ],
        security=[],
        rollback=[
            "Adapter changes are independent of schema changes and revert cleanly with row 07."
        ],
        validation=[
            "`uv run pytest tests/agent/test_orchestrator.py -v` and `uv run pytest tests/agent/test_tool_audit.py -v`.",
            TOOLCHAIN,
        ],
        completion=[
            "Adapter status writes equal the transition matrix; halted-resume still raises a `RuntimeError` naming `halted`; `stage_completed` audit carries the persisted attempt number (AC-6, AC-8).",
        ],
        out_of_scope=[
            "`attempt_id=turn_id` tool-loop correlation (`:353`); lease/stale-attempt semantics (wflease001 plan)."
        ],
        reqs="`REQ-007`, `REQ-009`",
        phase="Phase 4 (Engine, adapter, and audit correlation)",
        related="`scripts/agent/workflow/workflow_engine.py`, `scripts/agent/tool_audit.py`, `tests/agent/test_orchestrator.py`",
    )

    doc(
        by_seq["09"],
        seq="09",
        goal="Record the persisted attempt number in the `stage_completed` audit event written by `scripts/agent/tool_audit.py` (REQ-009 / AC-8).",
        scope=[
            "Extend `audit_stage_completed` (`tool_audit.py:125-132`) with an `attempt_number: int` parameter and add `attempt_number` to the event payload (`:136-145`).",
        ],
        assumptions=[
            "The caller supplies the value from `engine.current_attempt_number` (row 08); `tool_audit` does not query the database."
        ],
        design=[
            "`attempt_number` is emitted as a plain integer in the payload; the audit event keeps `workflow_id`/`task_id` as-is so attempt rows, ledger rows, artifact rows, and audit rows correlate on (task_id, stage_id, attempt_number)."
        ],
        alternatives=[
            "Deriving the number inside `audit_stage_completed` from `attempt_id`: rejected — `attempt_id` has no numbering relation, and `tool_audit` must stay DB-free."
        ],
        procedure=[
            "Add the parameter (keyword, required) and the payload field.",
            "Keep the function's `ctx` handling (`:125-132`) unchanged.",
        ],
        method="Direct edit; additive signature change (single caller at `workflow_engine_adapter.py:375`).",
        details=[
            "Existing `stage_completed` events in audit logs lack the field; no backfill is required (audit is append-only history)."
        ],
        compatibility=[
            "Audit-event consumers are read-side only (row 21 test); no schema impact."
        ],
        security=["Integer value passes JSON encoding as-is; no injection surface."],
        rollback=[
            "Revert with rows 07/08; older audit rows without the field stay valid."
        ],
        validation=[
            "`uv run pytest tests/agent/test_tool_audit.py -v` (row 21 adds the payload test).",
            TOOLCHAIN,
        ],
        completion=[
            "Every new `stage_completed` event carries `attempt_number` equal to the persisted attempt row number (AC-8).",
        ],
        out_of_scope=[
            "Audit schema docs beyond the payload field; historical event backfill."
        ],
        reqs="`REQ-009`",
        phase="Phase 4 (Engine, adapter, and audit correlation)",
        related="`scripts/agent/workflow_engine_adapter.py`, `tests/agent/test_tool_audit.py`",
    )

    doc(
        by_seq["10"],
        seq="10",
        goal="Add the status `CHECK` vocabularies, `attempt_number` with its unique index, and the ledger correlation columns to the canonical DDL in `scripts/db/schema_sql.py`, and bump `WORKFLOW_SCHEMA_VERSION` (REQ-008 / AC-10).",
        scope=[
            "`tasks` (`schema_sql.py:184-194`): `status TEXT NOT NULL CHECK (status IN ('pending','running','completed','failed','halted'))`.",
            "`attempts` (`:196-206`): `status ... CHECK (status IN ('running','completed','failed'))`, `attempt_number INTEGER NOT NULL`, and `CREATE UNIQUE INDEX idx_attempts_task_stage_number ON attempts(task_id, stage_id, attempt_number)`.",
            "`processed_events` (`:208-214`): add `attempt_id TEXT NOT NULL`, `attempt_number INTEGER NOT NULL`.",
            "`WORKFLOW_SCHEMA_VERSION` (`:27`) `1.2.0` -> `1.3.0`.",
        ],
        assumptions=[
            "Version-code landing-order caveat (Plan UNK-05): the Pending wftaskapi001 row `implementations/20261101-140834_12_scripts_db_migrations_workflow.py.md` already reserves ledger code `3` / version `1.3.0` for the `task_nonce` rename. If wftaskapi001 lands first, this row's DDL ships as version `1.4.0` / code `4` and the version constant matches that landing; if this Plan lands first, code `3`/`1.3.0` is taken here and wftaskapi001 renumbers to `4`/`1.4.0`. Fix the number at landing time; both orders must end with distinct codes.",
        ],
        design=[
            "DDL is the single source (`_WORKFLOW_SCHEMA`, `:178`) used by fresh creation; existing databases change only via the row-26 rebuild migration.",
            "`artifacts.attempt_number` (`:223`) already exists — the correlation tuple gains its missing members without touching `artifacts`.",
        ],
        alternatives=[
            "Adding columns without `CHECK`/index: rejected — REQ-008 names the constraints; the unique index is the concurrency backstop the row-18 tests assert."
        ],
        procedure=[
            "Edit the three `CREATE TABLE` statements inside `_WORKFLOW_SCHEMA` (`:178` region).",
            "Add the index statement next to the existing workflow index statements.",
            "Update the version constant and its guard comments.",
        ],
        method="Direct edit of DDL strings.",
        details=[
            "`check_db_separation.py` and the schema-ownership contract keep `schema_sql.py` as the only workflow DDL owner.",
            "Row 22's `_WORKFLOW_SCHEMA_NO_VEC0` copy must be updated to the same shape in the same commit (it is the migration-fixture source for row 22 tests).",
        ],
        compatibility=[
            "Row 11 required-column checks and row 20 fixtures must gain the new columns in the same phase; `tests/db/test_migrations_workflow.py` (existing suite, outside the frozen table) will need its expectations updated — flag it to the owner as a follow-up when the head version bumps."
        ],
        security=[
            "Constraints protect the vocabulary invariant at the storage layer; no new surface."
        ],
        rollback=[
            "DDL revert is only safe together with the row-26 migration revert (a migrated database keeps the rebuilt shape until restored from the backup copy)."
        ],
        validation=[
            "`uv run pytest tests/db/ -v` (row 22 constraint/index tests).",
            "`uv run python tools/check_db_separation.py`.",
            TOOLCHAIN,
        ],
        completion=[
            "Fresh databases enforce the five/four-status vocabularies, non-null unique attempt numbers per (task, stage), and ledger correlation columns; version constant bumped (AC-10).",
        ],
        out_of_scope=["Migration steps (row 26); startup column checks (row 11)."],
        reqs="`REQ-008`",
        phase="Phase 2 (Schema and migration)",
        related="`scripts/db/migrations_workflow.py`, `scripts/agent/services/workflow_schema.py`, `tests/db/test_create_schema.py`",
    )

    doc(
        by_seq["11"],
        seq="11",
        goal="Extend the startup workflow-schema check in `scripts/agent/services/workflow_schema.py` so the new columns are required (REQ-008 / AC-10).",
        scope=[
            "`REQUIRED_WORKFLOW_TABLES` (`workflow_schema.py:46-52`): add `attempt_number` to `attempts`, `attempt_id`/`attempt_number` to `processed_events`.",
            "The `PRAGMA table_info` comparison loop (`:93-100`) already consumes these lists; no new check logic.",
        ],
        assumptions=[
            "Check grade/score (Plan blast-radius: `check_workflow_schema` grade C) is not re-scored by this row."
        ],
        design=[
            "The check stays a column-presence check: `CHECK` constraints themselves are not validated here — the migration postcondition (row 26) and fresh DDL own constraint shape."
        ],
        alternatives=[
            "Reading `PRAGMA index_list` for the unique index: rejected — out of REQ-008's stated startup-check scope."
        ],
        procedure=[
            "Edit the two lists in `REQUIRED_WORKFLOW_TABLES`.",
            "Verify `check_workflow_schema` failure messages list the missing column names.",
        ],
        method="Direct edit; constant change only.",
        details=[
            "`tasks` list (`:47`) already requires `status`; the vocabulary itself is enforced by SQL, not here."
        ],
        compatibility=[
            "Deploy/startup path: a database migrated by row 26 passes; an un-migrated old database now fails fast at startup with the missing-column error (intended fail-closed behavior)."
        ],
        security=[],
        rollback=["Constant revert; paired with the row-10 revert."],
        validation=[
            "`uv run pytest tests/agent/test_repl_health.py -v` (row 20 fixtures) and `tests/unit/` startup-check tests if present; TOOLCHAIN below.",
            TOOLCHAIN,
        ],
        completion=[
            "Startup rejects a workflow database missing `attempts.attempt_number` or the ledger correlation columns (AC-10)."
        ],
        out_of_scope=["Migration execution (row 26)."],
        reqs="`REQ-008`",
        phase="Phase 2 (Schema and migration)",
        related="`scripts/db/schema_sql.py`, `tests/agent/test_repl_health.py`",
    )

    doc(
        by_seq["12"],
        seq="12",
        goal="Update `tests/agent/workflow/test_workflow_state_store.py` for the canonical attempt path and atomic recovery, and add the transition, error, and raw-SQL invalid-status tests (REQ-002, REQ-003, REQ-005, REQ-006, REQ-011 / AC-2, AC-3, AC-5, AC-7).",
        scope=[
            "Replace `start_attempt` helper use (`:140,147-148,153,162,232-234`) with the canonical `begin_stage_if_new` path.",
            "Recovery tests (`:449-542` region): assert the owning task moves `running -> failed` and repeats are no-ops.",
            "Raw INSERT fixtures (`:106,265,269,417,431,435,467,481,510,524`) gain `attempt_number` and stay within the new `CHECK` vocabularies.",
            "Add invalid-status raw-SQL tests (`IntegrityError`) and zero-row API transition tests (typed errors).",
        ],
        assumptions=[
            "The file's `create_task` fixture (`:106` region) keeps its parameter-bound inserts (Plan UNK-06 re-check satisfied at HEAD: raw seeds use only `pending`/`running`)."
        ],
        design=[
            "New tests are written to fail against the current code first (Plan REQ-011), committed with the Phase-3 implementation."
        ],
        alternatives=[
            "Rewriting the file from scratch: rejected — the existing 542-line fixture suite pins current behavior the Plan wants preserved for aggregates/diagnostics."
        ],
        procedure=[
            "Swap helper import/call sites to the canonical start.",
            "Extend recovery-class tests with task-status assertions.",
            "Add `TestTaskTransitionErrors` (API level) and `TestRawSqlStatusConstraints` (raw-SQL level) classes.",
        ],
        method="Direct edit of the existing test module plus new test classes.",
        details=[
            "Recovery fixture pattern: `workflow_db` factory (`:449-476` region) already inserts tasks/attempts via raw SQL — extend the attempt inserts with `attempt_number`."
        ],
        compatibility=[
            "This file is cited by the ADR test table (row 23 updates the citation rows)."
        ],
        security=[],
        rollback=["Test revert pairs with the row-03/04/05/06 revert."],
        validation=[
            "`uv run pytest tests/agent/workflow/test_workflow_state_store.py -v`.",
            "Pre-change run: new transition/recovery tests fail against HEAD; post-change: green (REQ-011 ordering).",
        ],
        completion=[
            "Transition, ledger, recovery, and constraint behaviors each have at least one test at API and raw-SQL level (AC-2, AC-3, AC-5, AC-7)."
        ],
        out_of_scope=["Concurrency tests (row 18); crash-scenario tests (row 17)."],
        reqs="`REQ-002`, `REQ-003`, `REQ-005`, `REQ-006`, `REQ-011`",
        phase="Phases 1 and 3 (tests land with their implementation phase)",
        related="`scripts/agent/workflow/task_ops.py`, `scripts/agent/workflow/state_store.py`, `tests/agent/workflow/test_workflow_recovery.py`",
    )

    doc(
        by_seq["13"],
        seq="13",
        goal="Update `tests/agent/workflow/test_state_store.py` recovery mocks/assertions for the atomic attempt+task recovery (REQ-006, REQ-011 / AC-7).",
        scope=[
            "The mocked recovery suite (`test_state_store.py:13-233`: mocks `find_stale_running_attempts`, asserts recovery counts) gains task-status assertions: each recovered attempt's owning `running` task becomes `failed`; an already-terminal owner is untouched.",
        ],
        assumptions=[
            "The suite mocks `SQLiteHelper` calls; assertions pin the per-attempt transaction shape (attempt UPDATE then task UPDATE before commit)."
        ],
        design=[
            "Count semantics: `recover_stale_attempts` return value keeps counting transitioned attempts; task-side transitions are asserted separately."
        ],
        alternatives=[
            "Porting all recovery coverage to raw-SQL integration tests (row 17): rejected — this file's mock style is the existing pattern the ADR test table cites."
        ],
        procedure=[
            "Extend the existing recovery test cases with `tasks` status assertions.",
            "Add a repeated-recovery case (second call returns 0 and changes nothing).",
        ],
        method="Direct edit; additive assertions plus one new case.",
        details=[
            "Mock call recording must expect the added conditional task UPDATE (`AND status='running'`)."
        ],
        compatibility=["ADR citation row is updated by row 23."],
        security=[],
        rollback=["Revert with row 06."],
        validation=[
            "`uv run pytest tests/agent/workflow/test_state_store.py -v`; fails pre-change (REQ-011)."
        ],
        completion=[
            "Recovery tests prove atomicity, owner-conditionality, and idempotent repeats (AC-7)."
        ],
        out_of_scope=["Concurrency or crash scenarios."],
        reqs="`REQ-006`, `REQ-011`",
        phase="Phase 3 (Attempt lifecycle, ledger, and recovery)",
        related="`scripts/agent/workflow/state_store.py`, `tests/agent/workflow/test_workflow_recovery.py`",
    )

    doc(
        by_seq["14"],
        seq="14",
        goal="Update `tests/agent/workflow/test_workflow_engine.py` so engine tests cover persisted attempt numbering, claim rejection, and the restart-spanning retry budget (REQ-007, REQ-009, REQ-011 / AC-6, AC-8).",
        scope=[
            "Existing idempotency/retry classes (`test_workflow_engine.py:111-161`, `:186-206`) currently assume the in-memory `attempt = 0` numbering (`workflow_engine.py:202`); align them with the persisted number.",
            "Add: resume of a `failed` task after N attempts continues at N+1; claim rejection for `running`/`completed`/`halted`; `max_attempts` enforced across simulated restarts.",
        ],
        assumptions=[
            "Fixture helpers in this file build a real workflow database via the schema — fixtures gain `attempt_number` when rows 10/15 land."
        ],
        design=[
            "Restart simulation: close the engine/store and re-run against the same database file, asserting persisted state drives behavior."
        ],
        alternatives=[
            "Mock-only engine tests: rejected — persisted numbering is the behavior under test."
        ],
        procedure=[
            "Fix helper inserts for the new columns.",
            "Adjust retry-budget assertions to count persisted attempts.",
            "Add `TestClaimRejection` and `TestPersistedAttemptBudget` classes.",
        ],
        method="Direct edit plus new test classes.",
        details=[
            "`TestRunStageWithRetryGeneralization` (cited by the ADR test table for INV-03) keeps its scenario; only the numbering expectations change."
        ],
        compatibility=["ADR citation (row 23) unchanged for INV-03."],
        security=[],
        rollback=["Revert with rows 05/07."],
        validation=[
            "`uv run pytest tests/agent/workflow/test_workflow_engine.py -v`; new classes fail pre-change."
        ],
        completion=[
            "Engine claims correctly, numbering and budget persist across restarts, and attempt number is exposed (AC-6, AC-8)."
        ],
        out_of_scope=["Adapter guard tests (row 19)."],
        reqs="`REQ-007`, `REQ-009`, `REQ-011`",
        phase="Phase 4 (Engine, adapter, and audit correlation)",
        related="`scripts/agent/workflow/workflow_engine.py`, `tests/agent/workflow/test_workflow_recovery.py`",
    )

    doc(
        by_seq["15"],
        seq="15",
        goal="Replace bypass-path usage and add ledger semantics tests in `tests/agent/workflow/test_workflow_stage_persistence.py` (REQ-003, REQ-004, REQ-011, REQ-012 / AC-3, AC-4, AC-9).",
        scope=[
            "Replace `start_attempt` calls (`:42,61,73`) with the canonical `begin_stage_if_new` path; keep the raw task INSERT fixture (`:29`, `pending` — within the new vocabulary).",
            "Add ledger tests: a completed stage is skipped on re-run; a stage whose attempt `failed` re-runs and gets the next `attempt_number`; starting while another attempt for the stage is `running` raises `StageAlreadyRunningError`.",
        ],
        assumptions=[
            'This file is the AC-9 verification home for "no bypass caller": after the change, `rg "start_attempt" tests` returns nothing.'
        ],
        design=[
            "Skip assertions key on the ledger row for (task, stage), matching the REQ-004 semantics chosen in row 05."
        ],
        alternatives=[
            "Testing skip via attempt status: rejected — the ledger is the contract (Plan UNK-02)."
        ],
        procedure=[
            "Swap helper imports/calls.",
            "Add `TestLedgerSkip`, `TestNumberingAfterFailure`, `TestConcurrentStageStart` classes.",
        ],
        method="Direct edit plus new test classes.",
        details=[
            "Fixture task row (`:29`) uses explicit column list; add `attempt_number` to its attempts inserts once row 10 lands."
        ],
        compatibility=[
            "`test_begin_stage_if_new_idempotent` (ADR INV-08 citation, `:187-188` region of the ADR test table) is re-pointed by row 23 if the test name changes."
        ],
        security=[],
        rollback=["Revert with rows 04/05."],
        validation=[
            "`uv run pytest tests/agent/workflow/test_workflow_stage_persistence.py -v`; ledger tests fail pre-change."
        ],
        completion=[
            "Stage skip, re-run numbering, and concurrent-start rejection are proven; no test uses the deleted bypass (AC-3, AC-4, AC-9)."
        ],
        out_of_scope=["Two-connection race tests (row 18)."],
        reqs="`REQ-003`, `REQ-004`, `REQ-011`, `REQ-012`",
        phase="Phase 3 (Attempt lifecycle, ledger, and recovery)",
        related="`scripts/agent/workflow/idempotency_ops.py`, `scripts/agent/workflow/attempt_ops.py`",
    )

    doc(
        by_seq["16"],
        seq="16",
        goal="Replace status literals with enum/matrix tests in `tests/agent/workflow/test_workflow_models.py` (REQ-001 / AC-1).",
        scope=[
            "Status literals at `test_workflow_models.py:24,39,50` become `TaskStatus`/`AttemptStatus` members.",
            "Add: full matrix test (every allowed and rejected edge, `halted` terminal, `completed -> failed` transitional); enum-vs-SQL test asserting the enum value set equals the `CHECK` vocabulary parsed from `schema_sql._WORKFLOW_SCHEMA`.",
        ],
        assumptions=[
            "The DDL parse in the vocabulary test reads the `CHECK (status IN (...))` literals from the canonical DDL string — it fails loudly when either side changes (REQ-001)."
        ],
        design=[
            "The matrix test enumerates edges from `TASK_TRANSITIONS` itself plus an explicit expected-edge table, so a silent matrix edit is caught."
        ],
        alternatives=[
            "Hard-coding the status tuple in the test: rejected — it would not catch divergence between enum and DDL."
        ],
        procedure=[
            "Literal swap in the three cited spots.",
            "Add `TestTransitionMatrix` and `TestStatusVocabularyMatchesDdl` classes.",
        ],
        method="Direct edit plus new test classes.",
        details=["This test file is also the row-01 acceptance home."],
        compatibility=[
            "Depends on row 10 landing for the DDL side of the vocabulary test; until then the vocabulary test targets the row-10 DDL and may be committed with Phase 2."
        ],
        security=[],
        rollback=["Revert with row 01."],
        validation=["`uv run pytest tests/agent/workflow/test_workflow_models.py -v`."],
        completion=[
            "AC-1: the CHECK vocabulary equals the enums and the matrix is test-pinned."
        ],
        out_of_scope=["Behavioral transition tests (rows 12/17/18)."],
        reqs="`REQ-001`",
        phase="Phase 1 (Vocabulary, errors, and task transitions)",
        related="`scripts/agent/workflow/models.py`, `scripts/db/schema_sql.py`",
    )

    doc(
        by_seq["17"],
        seq="17",
        goal="Create `tests/agent/workflow/test_workflow_recovery.py` with the crash, resume, and repeated-recovery regression scenarios (REQ-006, REQ-007, REQ-011 / AC-6, AC-7).",
        scope=[
            "New file in the existing `tests/agent/workflow/` directory (no recovery-scenario test file exists at HEAD).",
            "Scenarios (each fails against HEAD first, REQ-011): crash after the attempt row is written (no ledger row -> stage restartable with next number); crash after a side effect before the attempt is finished (stale `running` attempt -> recovery fails attempt + owning `running` task); repeated restart and recovery (idempotent); resume of a `failed` task after one or more attempts (numbering continues via row 14's engine path); resume of `completed`, `halted`, and `running` tasks is rejected.",
        ],
        assumptions=[
            "Scenario harness: build a workflow database via `schema_sql._WORKFLOW_SCHEMA`, simulate a crash by leaving rows in their written state, then run `recover_stale_attempts` and/or `WorkflowEngine.run` against the same file."
        ],
        design=[
            "One test class per scenario with names mirroring the REQ-011 list, so the traceability table maps 1:1."
        ],
        alternatives=[
            "Extending `test_workflow_state_store.py` instead: rejected — the frozen table names this new file for the crash/resume family."
        ],
        procedure=[
            "Create the module with a shared `workflow_db`-style fixture.",
            "Implement the five scenario groups.",
        ],
        method="New file creation.",
        details=[
            "Existing recovery-adjacent tests (`test_workflow_state_store.py:449-542`) stay in place; this file covers the engine-visible crash/resume contract."
        ],
        compatibility=["Row 23 cites this file in the ADR test table."],
        security=[],
        rollback=["Delete the file."],
        validation=[
            "`uv run pytest tests/agent/workflow/test_workflow_recovery.py -v` — red on HEAD, green after Phase 3/4."
        ],
        completion=["All REQ-011 recovery scenarios have named tests (AC-6, AC-7)."],
        out_of_scope=["Concurrency (row 18); migration fixtures (row 22)."],
        new_target=True,
        reqs="`REQ-006`, `REQ-007`, `REQ-011`",
        phase="Phase 3 (Attempt lifecycle, ledger, and recovery)",
        related="`scripts/agent/workflow/state_store.py`, `scripts/agent/workflow/workflow_engine.py`, `tests/agent/workflow/test_workflow_concurrency.py`",
    )

    doc(
        by_seq["18"],
        seq="18",
        goal="Create `tests/agent/workflow/test_workflow_concurrency.py` with two-connection claim and attempt-numbering race tests (REQ-002, REQ-003, REQ-011 / AC-5b).",
        scope=[
            "New file in the existing `tests/agent/workflow/` directory (no multi-connection workflow test exists at HEAD).",
            "Scenarios: two connections claim the same `pending` task — exactly one wins, the other raises `TaskTransitionError`; two concurrent `begin_stage_if_new` calls for one (task, stage) — one proceeds, the other raises `StageAlreadyRunningError`; `attempt_number` allocation under two connections never duplicates (unique index `idx_attempts_task_stage_number` backstop).",
        ],
        assumptions=[
            "Two `sqlite3` connections to one file with short busy timeouts; determinism via ordering assertions rather than wall-clock timing."
        ],
        design=[
            "Race outcomes are asserted as invariant sets (exactly-one-winner, unique numbers), not as specific interleavings — keeps the tests deterministic."
        ],
        alternatives=[
            "Threading stress with many iterations: rejected for the regression home — deterministic two-connection cases are the REQ-011 requirement."
        ],
        procedure=[
            "Create the module with a two-connection fixture.",
            "Implement the three race groups.",
        ],
        method="New file creation.",
        details=[
            'SQLite write serialization means "simultaneous" means interleaved committed transactions; the tests pin the conditional-update semantics that make the race safe.'
        ],
        compatibility=["Depends on rows 03/05/10 for the APIs and index it tests."],
        security=[],
        rollback=["Delete the file."],
        validation=[
            "`uv run pytest tests/agent/workflow/test_workflow_concurrency.py -v`; red until rows 03/05/10 land."
        ],
        completion=[
            "Claim, concurrent start, and numbering races each have a deterministic test (AC-5b)."
        ],
        out_of_scope=["Multi-process (spawned) races."],
        new_target=True,
        reqs="`REQ-002`, `REQ-003`, `REQ-011`",
        phase="Phase 3 (per the Plan traceability row: Testing Expectations 2-3)",
        related="`scripts/agent/workflow/task_ops.py`, `scripts/agent/workflow/idempotency_ops.py`, `scripts/db/schema_sql.py`",
    )

    doc(
        by_seq["19"],
        seq="19",
        goal="Update `tests/agent/test_orchestrator.py` status-write assertions for the transition API and pin the halted-resume message and audit attempt number (REQ-007, REQ-009, REQ-011 / AC-6, AC-8).",
        scope=[
            "Mocked `update_task_status` assertions (`test_orchestrator.py:2758-2896`) — expect transition-API calls instead of raw status writes.",
            'Halted-resume test (`:2226-2249`) and the `match="halted"` assertion (`:2116`): behavior must still pass after row 08\'s guard rewrite.',
            "Add an audit-argument assertion that `audit_stage_completed` receives `attempt_number`.",
        ],
        assumptions=[
            "This suite mocks `StateStore` at the boundary; the adapter (row 08) is the object under test."
        ],
        design=[
            "Keep the existing halted-resume tests untouched in intent — they are the acceptance anchor for the `TaskTransitionError` message contract (row 02)."
        ],
        alternatives=[
            "Rewriting the mocks against `task_ops` directly: rejected — the existing store-boundary mocks are this suite's stable seam."
        ],
        procedure=[
            "Update mock surfaces to the renamed/delegated methods the adapter now calls.",
            "Extend the exit-status assertions with the `completed -> failed` transitional case.",
            "Add the audit `attempt_number` assertion to the stage-completion orchestration test.",
        ],
        method="Direct edit of mock expectations plus one new assertion block.",
        details=[
            "The suite is 3211 lines and high-churn (14 edits/30d); limit changes to the cited regions."
        ],
        compatibility=["Depends on rows 06/08 method names landing first."],
        security=[],
        rollback=["Revert with rows 06/08."],
        validation=["`uv run pytest tests/agent/test_orchestrator.py -v`."],
        completion=[
            "Orchestrator-level tests prove claim semantics, halted guard, and attempt-number propagation (AC-6, AC-8)."
        ],
        out_of_scope=["Engine-internal numbering (row 14)."],
        reqs="`REQ-007`, `REQ-009`, `REQ-011`",
        phase="Phase 4 (Engine, adapter, and audit correlation)",
        related="`scripts/agent/workflow_engine_adapter.py`, `scripts/agent/tool_audit.py`, `tests/agent/test_tool_audit.py`",
    )

    doc(
        by_seq["20"],
        seq="20",
        goal="Update the minimal workflow-table fixtures in `tests/agent/test_repl_health.py` so they match the new required columns (REQ-008 / AC-10).",
        scope=[
            "`_create_workflow_db` (`test_repl_health.py:523` region, CREATE TABLE fixtures at `:535-554`): add `attempt_number` to `attempts`, `attempt_id`/`attempt_number` to `processed_events`.",
            "Missing-column diagnostic tests (`:548-554`, `missing_column` at `:548-549`; example INSERT at `:599`): extend to the new columns so the health report names them.",
        ],
        assumptions=[
            "This suite intentionally builds divergent minimal tables (not `schema_sql` DDL) to exercise the health check — fixtures must stay hand-written copies, kept shape-current by this row."
        ],
        design=[
            "Fixture divergence stays deliberate: the tests' value is detecting drift between a real database and the required-column list (row 11)."
        ],
        alternatives=[
            "Importing `_WORKFLOW_SCHEMA` into the fixtures: rejected — the suite's purpose is testing the checker against drifted schemas."
        ],
        procedure=[
            "Update the CREATE TABLE statements.",
            "Add one negative case: table missing `attempt_number` is reported.",
        ],
        method="Direct edit of fixture SQL and assertions.",
        details=["INSERT fixtures (`:599` region) gain the new columns to stay valid."],
        compatibility=[
            "Must land with rows 10/11 in Phase 2 or the health-check assertions drift."
        ],
        security=[],
        rollback=["Revert with rows 10/11."],
        validation=["`uv run pytest tests/agent/test_repl_health.py -v`."],
        completion=[
            "Health-report fixtures and diagnostics cover the new required columns (AC-10)."
        ],
        out_of_scope=["Real-migration fixtures (row 22)."],
        reqs="`REQ-008`",
        phase="Phase 2 (Schema and migration)",
        related="`scripts/agent/services/workflow_schema.py`, `scripts/db/schema_sql.py`",
    )

    doc(
        by_seq["21"],
        seq="21",
        goal="Add the `stage_completed` attempt-number test to `tests/agent/test_tool_audit.py` (REQ-009 / AC-8).",
        scope=[
            "New test class asserting `audit_stage_completed` writes `attempt_number` into the event payload (no `stage_completed` test exists at HEAD).",
        ],
        assumptions=[
            "Fixture pattern follows `_make_ctx` (`test_tool_audit.py:63`) and the existing audit-event capture style."
        ],
        design=[
            "Assert the exact payload key/value alongside the existing `workflow_id`/`task_id` keys."
        ],
        alternatives=[
            "Extending an approval-event test: rejected — separate event type, separate class keeps ADR INV-11 tests untouched."
        ],
        procedure=[
            "Add `TestAuditStageCompletedAttemptNumber` following the existing capture pattern.",
        ],
        method="Direct edit; additive test class.",
        details=["Payload source is row 09; this file tests only the emitted event."],
        compatibility=[
            "ADR test table already cites this file for INV-11 (unchanged)."
        ],
        security=[],
        rollback=["Delete the class."],
        validation=["`uv run pytest tests/agent/test_tool_audit.py -v`."],
        completion=[
            "The audit event contract for `stage_completed` is test-pinned with `attempt_number` (AC-8)."
        ],
        out_of_scope=["Adapter-side propagation tests (row 19)."],
        reqs="`REQ-009`",
        phase="Phase 4 (Engine, adapter, and audit correlation)",
        related="`scripts/agent/tool_audit.py`, `scripts/agent/workflow_engine_adapter.py`",
    )

    doc(
        by_seq["22"],
        seq="22",
        goal="Update the workflow DDL copy in `tests/db/test_create_schema.py` and add the constraint and migration behavior tests (REQ-008, REQ-011 / AC-10).",
        scope=[
            "`_WORKFLOW_SCHEMA_NO_VEC0` (`test_create_schema.py:375-421`, tasks copy at `:379-386`): mirror the new `CHECK` constraints, `attempt_number`, unique index, and ledger columns.",
            "New tests: `CHECK` rejects out-of-vocabulary status; the unique index rejects duplicate (task, stage, attempt_number); migration of a v1-shaped database (built from the pre-change DDL copy) preserves rows and backfills `attempt_number` by `ROW_NUMBER() OVER (PARTITION BY task_id, stage_id ORDER BY started_at, rowid)`; migration precondition refuses a database containing out-of-vocabulary status rows, listing the offending rows; `PRAGMA foreign_key_check` clean after rebuild.",
        ],
        assumptions=[
            "The pre-change (v1-era) shape already present at `:391` (attempts without `attempt_number`) doubles as the migration fixture source."
        ],
        design=[
            "Migration behavior is tested through the public runner API (row 26's registered specs), not by calling private helpers."
        ],
        alternatives=[
            "Fixture databases copied from production dumps: rejected — not available under `rules/ai-execution.md` repository tool usage."
        ],
        procedure=[
            "Update the embedded DDL copy.",
            "Add `TestWorkflowConstraints` and `TestWorkflowMigration` classes.",
        ],
        method="Direct edit plus new test classes.",
        details=[
            "Existing assertions in this file guard fresh-create behavior; they must keep passing after the row-10 DDL change in the same commit."
        ],
        compatibility=[
            "Note for the owner: `tests/db/test_migrations_workflow.py` (620 lines, registry expectations for head version 2) is outside the frozen table but will fail when `WORKFLOW_TARGET_VERSION` bumps — flag as a follow-up target at landing (no unauthorized edits)."
        ],
        security=[],
        rollback=["Revert with rows 10/26."],
        validation=[
            "`uv run pytest tests/db/ -v`.",
            "Migration tests must run valid and invalid databases end-to-end (REQ-011).",
        ],
        completion=[
            "Fresh-shape constraints, migration of valid databases, and fail-closed rejection of invalid databases are all proven (AC-10)."
        ],
        out_of_scope=["Startup required-column checks (row 11)."],
        reqs="`REQ-008`, `REQ-011`",
        phase="Phase 2 (Schema and migration)",
        related="`scripts/db/schema_sql.py`, `scripts/db/migrations_workflow.py`",
    )

    doc(
        by_seq["23"],
        seq="23",
        goal="Amend ADR-001 invariants INV-07/INV-08 and their test-citation rows to the new recovery and ledger semantics (REQ-010 / AC-11).",
        scope=[
            "Append an `### Amendment (wfrecovery001, 2026-11-XX)` block following the `docs/10_adr/adr_02_05_008_*.md` precedent (`### Amendment (dbmig001, 2026-10-30)` at `:73`).",
            "Revised INV-07 text: startup recovery fails the stale `running` attempt and atomically moves its owning `running` task to `failed`; repeated recovery is a no-op.",
            "Revised INV-08 text: stage idempotency keys on the completed-stage ledger row for the (task, stage) pair; a concurrent start of the same stage raises `StageAlreadyRunningError`.",
            "Update the test-citation rows (`adr_02_02_001:187-188`) to the new homes: `tests/agent/workflow/test_workflow_recovery.py`, `tests/agent/workflow/test_state_store.py`, `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_workflow_stage_persistence.py`.",
        ],
        assumptions=[
            "The ADR stays `Accepted`; the amendment records the change rather than rewriting history (ADR change protocol, `check_adr_preservation.py`)."
        ],
        design=[
            "Old invariant sentences remain quoted inside the amendment block for diffability."
        ],
        alternatives=[
            "Silently editing the invariant text in place: rejected by the ADR change protocol."
        ],
        procedure=[
            "Draft the amendment block at the end of the Decision/Invariants region.",
            "Update the two test-table rows in place.",
            "Record the change in the commit message and the cycle report (docs checker requires an explanation per ADR change).",
        ],
        method="Direct edit: one appended section, two table-row updates.",
        details=[
            "`adr_01_index.md:45` carries the ADR one-liner; re-check it for staleness when the amendment lands (docs checkers, not a frozen target row)."
        ],
        compatibility=[
            "INV-07/INV-08 wording also appears in `agent_03_03`/`agent_04_03`; rows 24/25 keep those docs consistent in the same phase."
        ],
        security=[],
        rollback=["Revert the amendment block with rows 24/25."],
        validation=[
            "`uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain agent`, `check_docs_japanese.py`, `check_adr_preservation.py`.",
        ],
        completion=[
            "AC-11: ADR invariants describe the implemented semantics and cite existing tests."
        ],
        out_of_scope=["Other ADRs; `agent_09_*` data-layer docs."],
        reqs="`REQ-010`",
        phase="Phase 5 (Documentation and ADR)",
        related="`docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`, `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`",
    )

    doc(
        by_seq["24"],
        seq="24",
        goal="Rewrite the state-semantics, resume, and startup-recovery sections of `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` to the implemented contract (REQ-010 / AC-11).",
        scope=[
            "`### Workflow State Semantics` (`:31`) gains the five-status vocabulary and the transition matrix summary.",
            "`### Resuming Existing Tasks` (`:35-40`): claim contract — `pending`/`failed` claimable, `running`/`completed` rejected, `halted` still raises the `RuntimeError` naming `halted` (`:40` wording stays compatible).",
            '`### Startup Recovery` (`:143-145`): replace "it never changes the persisted task status" with the atomic attempt+task failure semantics (Plan UNK-03 owner decision).',
            "Task Status Transitions table (`:74-90`) and Operational Notes (`:149-150`) reconciled with the matrix (cancellation-stays-`halted` policy unchanged).",
        ],
        assumptions=[
            "Docs are written in English (`skills/DESIGN.md` Output language); the frozen cite's `started (not completed)` phrase no longer exists in this file at HEAD — the rewrite targets the actual HEAD text, cite drift noted."
        ],
        design=[
            "Section-level edits only; the doc's structure and checker-relevant headings stay intact."
        ],
        alternatives=[
            "Regenerating the whole doc: rejected — unnecessary churn and churn-risk (23 edits/30d)."
        ],
        procedure=[
            "Apply the three section rewrites plus the table reconciliation.",
            "Re-run the docs checkers and record any Japanese/content-policy findings.",
        ],
        method="Direct edit of four cited regions.",
        details=[
            "`agent_04_03` (row 25) states the StateStore side of the same contract; the two docs must use identical wording for the claim matrix."
        ],
        compatibility=[
            "Row 23 ADR amendment lands in the same phase so invariants and flow doc agree."
        ],
        security=[],
        rollback=["Docs revert is data-free; pair with rows 23/25."],
        validation=["Full docs checker set (as row 23 lists)."],
        completion=[
            "AC-11: the flow doc describes claim, ledger, and recovery exactly as implemented."
        ],
        out_of_scope=["Approval-policy sections; retry-config reference tables."],
        reqs="`REQ-010`",
        phase="Phase 5 (Documentation and ADR)",
        related="`docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`",
    )

    doc(
        by_seq["25"],
        seq="25",
        goal="Update the StateStore responsibility-scope paragraph and the `begin_stage_if_new` bullet in `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` (REQ-010 / AC-11).",
        scope=[
            '`### StateStore Responsibility Scope` (`:70-72`): reword "stage-level idempotency (duplicate-event detection and atomic attempt initiation)" to the completed-stage-ledger contract.',
            "`begin_stage_if_new` bullet (`:100`): state the single canonical start (ledger check, running-attempt check, `attempt_number = MAX + 1` insert in one transaction) and the `StageAlreadyRunningError` rejection.",
            "Keep the `idempotency_key` vs `tool_call_state.idempotency_key` clarification (`:72`) — it is the wftaskapi001 rename's context paragraph and is not re-touched here (sequencing note in that plan's row 11).",
        ],
        assumptions=[
            "Frozen cite lines `234-242` are stale against HEAD (file is 106 lines); the rewrite targets the verified HEAD regions `:46,70-72,100`."
        ],
        design=["Bullet-level edits; no section restructuring."],
        alternatives=[
            "Moving the contract text into `agent_03_03` only: rejected — the frozen table requires both docs updated."
        ],
        procedure=[
            "Rewrite the two cited regions.",
            "Re-run the docs checkers.",
        ],
        method="Direct edit of two cited regions.",
        details=["DB-ownership paragraph (`:46`) stays unchanged."],
        compatibility=[
            "Coordinate wording with rows 23/24 for identical claim-matrix phrasing."
        ],
        security=[],
        rollback=["Docs revert is data-free."],
        validation=["Full docs checker set."],
        completion=[
            "AC-11: the platform doc's StateStore scope matches the implemented ledger contract."
        ],
        out_of_scope=[
            "Session/rag database sections; `tool_call_state` table description."
        ],
        reqs="`REQ-010`",
        phase="Phase 5 (Documentation and ADR)",
        related="`docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`, `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`",
    )

    doc(
        by_seq["26"],
        seq="26",
        goal="Register the workflow table-rebuild migration in `scripts/db/migrations_workflow.py` (vocabulary preconditions, rebuild with `attempt_number` backfill, postconditions, stamped version) (REQ-008 / AC-10).",
        scope=[
            "Append the rebuild `MigrationSpec` to `REGISTRY` (`migrations_workflow.py:245-262`): `from_version=2`, rebuild of `tasks`, `attempts`, `processed_events` (rename-to-old -> canonical `CREATE` from `schema_sql` -> parent-first copy -> child-first drop).",
            "Precondition SQL rejects out-of-vocabulary `tasks.status`/`attempts.status` rows and lists the offending rows in the failure message.",
            "`attempt_number` backfill via `ROW_NUMBER() OVER (PARTITION BY task_id, stage_id ORDER BY started_at, rowid)` during the copy.",
            "Postcondition: table shapes equal the canonical DDL, `PRAGMA foreign_key_check` clean; stamp `workflow_schema_version` row and `PRAGMA user_version`; update `WORKFLOW_VERSION_CODES` (`:42`) and `WORKFLOW_TARGET_VERSION` (`:48`).",
        ],
        assumptions=[
            "Ledger code landing order: wftaskapi001 row `implementations/20261101-140834_12_*` (Pending) registers `workflow_task_nonce` at code `3` / `1.3.0`. If that lands first this row takes code `4` / `1.4.0`; if this lands first it takes `3` / `1.3.0` and wftaskapi001 renumbers. Whichever lands second must re-verify the registry head (Plan UNK-05). `plans/20261101-133244_dbmigrunner001_runner-unsafe-table-rebuild.md` is open but reserves no code.",
            "`migration_sql` runs through `executescript` in one all-or-nothing transaction (`scripts/shared/db_migrations.py:404-415`); `PRAGMA foreign_keys` cannot toggle mid-transaction, so the rebuild relies on SQLite 3.25+ rename-follow semantics.",
        ],
        design=[
            "Precondition fails closed (Plan UNK-07): existing violating rows — stale `running` attempts, `processed_events` started markers without a completed attempt — are listed, not silently mapped; automatic mapping needs an owner decision before any production run.",
            "Documented rollback equals the dbmig001 backup gate: restore the pre-migration backup copy of `workflow.sqlite`; there is no down-migration.",
            "One spec (not three table-specific specs) keeps the rename-copy-drop sequence inside a single transaction.",
        ],
        alternatives=[
            "ALTER TABLE ADD COLUMN only: rejected — `CHECK` constraints and a unique index require table rebuilds, and `processed_events` gains NOT NULL columns the backfill must populate."
        ],
        procedure=[
            "Add the precondition check function and the `mutation_sql` script (rename, create, copy with backfill, drop).",
            "Register the spec in `REGISTRY` and bump `WORKFLOW_VERSION_CODES`/`WORKFLOW_TARGET_VERSION` at landing.",
            "Document the rollback procedure in the module docstring (backup-copy restore, dbmig001 gate).",
        ],
        method="Direct edit: one appended spec plus registry/version constants.",
        details=[
            "Copy statements order parent-first (`tasks` -> `attempts` -> `processed_events`) and drops child-first to keep FK integrity through the rebuild."
        ],
        compatibility=[
            "`tests/db/test_migrations_workflow.py` head-version expectations change with the bump — owner-visible follow-up (flagged in row 22)."
        ],
        security=[
            "Precondition listing uses parameter-bound queries; no dynamic SQL over data."
        ],
        rollback=[
            "Restore the backup copy (documented); code revert alone does not un-migrate data."
        ],
        validation=[
            "`uv run pytest tests/db/ -v` (row 22 migration tests: valid and invalid databases).",
            "`uv run python tools/check_db_separation.py`.",
            TOOLCHAIN,
        ],
        completion=[
            "A v2 database migrates to the new head with preserved rows and backfilled numbers; an invalid database is refused with the offending rows listed; the version is stamped (AC-10).",
        ],
        out_of_scope=[
            "Runner changes (`plans/20261101-133244_dbmigrunner001_*`, open); production execution (Phase 6 deploy)."
        ],
        reqs="`REQ-008`",
        phase="Phase 2 (Schema and migration)",
        related="`scripts/db/schema_sql.py`, `scripts/shared/db_migrations.py`, `tests/db/test_create_schema.py`",
        blockers=BLOCKER_PLACEHOLDER.replace(
            "| — | — | — | — |",
            "| 2 | Registry code `3`/`1.3.0` is also claimed by wftaskapi001 row 12 (Pending); landing order decides the number (Plan UNK-05) | No | — |\n| 2 | Plan UNK-07: owner decision on automatic mapping of violating retained rows before any production migration run | No | — |",
        ),
    )


if __name__ == "__main__":
    main()
