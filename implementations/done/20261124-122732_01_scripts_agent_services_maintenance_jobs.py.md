## Goal

Create the single owner of maintenance job records so every Session, RAG, and Memory maintenance run is recorded, gated by an approval level, cancellable when the operation can be interrupted, and closed with a verified or explicitly unknown outcome (REQ-001: one record per run and one writer per store; REQ-002: cancellation; REQ-003: approval as an operation property; REQ-004: verified outcomes).

## Scope
**Release unit**: R1-registry-core (Phase 1)

- In scope: the registry, the job record, the state machine, the per-store guard, the cancellation event, the outcome recording.
- Out of scope: the command handlers that call the registry (rows 3, 5, 7) and the `AppServices` wiring (rows 17, 18).

## Assumptions

- The registry is constructed once and reached through `AppServices`, so the one-writer-per-store guard is process-global; this document assumes rows 17 and 18 land in the same phase.
- `session.sqlite` already has a single-writer contract (`docs/10_adr/adr_02_05_008_db-six-sqlite-store-separation.md`); the registry enforces that rule in-process, it does not acquire a database lock.
- Cancellation is cooperative through the existing progress-handler mechanism (`scripts/db/helper.py:158-162`), so the registry only owns the `threading.Event` and the state transition; the worker performs the interrupt.
- The new module stays under the 24576 B gate (`tools/check_module_size.py`).

## Design decisions

- One registry instance, not one per command mixin: a per-mixin registry would not see a Memory rebuild started from another mixin, so the guard would be per-command rather than per-store (Plan Design, framework decision).
- A second write job against the same store is rejected with the running job id in the message, not queued — queueing would make the caller wait on a writer it cannot observe.
- `outcome_unknown` is a terminal state entered when the awaiter is cancelled or the process dies while the worker is running; it is never reported as success and never re-run.
- Approval level is declared with the operation record, not read from the command line: `none`, `confirm`, `guard`. `guard` requires a stored precondition that must hold before the run starts.
- Cancelability is declared per operation at registration (`cooperative` or `not_cancelable` (new)), because a statement past its last progress callback cannot be interrupted.

## Alternatives considered

- Reusing `MemoryOpResult` as the job result type — rejected: it is the Memory write result type, and the plan keeps the verified-result types separate (Consumer and historical coverage, `MemoryOpResult` row).
- Storing jobs in a table so the record survives a restart — rejected for this phase: the plan's requirement is an in-process registry; persistence would add a schema change outside this Plan's scope.

## Implementation
### Target file
`scripts/agent/services/maintenance_jobs.py` (new)

### Procedure
1. Define `JobState` (new) (pending, running, completed, failed, cancelled, outcome_unknown), `ApprovalLevel` (new) (none, confirm, guard), and `Cancelability` (new) (cooperative, not_cancelable) as enums.
2. Define `MaintenanceJob` (new) with the fields the Plan's Design section lists: `job_id`, `operation`, `store`, `approval_level` (new), `cancelability`, `state`, `started_at`, `progress`, `outcome`, `verified`, `session_target` (new).
3. Define `MaintenanceJobRegistry` (new) with: register (creates the record, rejects a second write job on a store that already has one running), start, finish (records the terminal outcome and `verified`), cancel (sets the event for a cooperative job and returns the stated reason for a `not_cancelable` (new) one), and lookup by `job_id`.
4. Keep the module data-and-transition only: no SQL, no command formatting, no import of `agent.commands`.

### Method
- `register()` takes the operation record (operation name, store, approval level, cancelability) and returns the job; the per-store guard is a dict of store → running job id checked inside `register()`.
- `cancel()` returns a typed result: interrupted, or refused with the reason, so the caller can state it instead of guessing.
- The worker-facing surface is `job.stop_event` — a `threading.Event` the caller passes to `SQLiteHelper.interrupt_when`.

### Details
- `session_target` (new) carries the cliplc002 generation identity so a job can be attributed to the session that started it; the value is passed in by the caller, this module does not compute it.
- `guard` levels call an injected precondition callable before `start()`; the result is recorded on the job.
- `import` and `reindex` appear in the operation names listed in the Plan's Design section; the registry stores them as opaque strings, so no operation-specific behavior belongs here.

### Companion test files
- `tests/agent/services/test_maintenance_jobs.py` (new)
  - Procedure: state transitions, the one-writer-per-store refusal naming the running job id, cancellation through the event, each approval level, and the `outcome_unknown` path.
  - Validation: `uv run pytest tests/agent/services/test_maintenance_jobs.py -q` (AC-1, AC-2, AC-3, AC-4).

## Compatibility considerations

- Nothing consumes this module yet; the first consumers are rows 3, 5, 7 and 17. No public API is removed, so no existing test changes.

## Security considerations

- The registry is the place where approval is enforced; a caller that bypasses it re-creates the current behavior where a flag grants permission by itself (REQ-003).

## Rollback considerations

- Remove the module and its test file; no persisted state and no config key depend on it.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/services/maintenance_jobs.py` | Unit (with the companion) | `uv run pytest tests/agent/services/test_maintenance_jobs.py -q` | States, one-writer refusal, cancellation, approval levels, `outcome_unknown` pass |
| Same file | Size gate | `uv run python tools/check_module_size.py` | New module under 24576 B |
| Same file | Quality gates | `uv run ruff check scripts/agent/services/maintenance_jobs.py`, `uv run mypy scripts/agent/services/maintenance_jobs.py`, `uv run bandit -c pyproject.toml scripts/agent/services/maintenance_jobs.py` | No finding |

## Completion criteria

- A job record exists for every run registered through the registry, the second write job on a busy store is refused with the running id, a cooperative job reaches `cancelled` when its event is set, and a run whose awaiter was cancelled ends `outcome_unknown` rather than success.

## Out of Scope

- The `/jobs` commands and their completion entries (rows 9, 10, 11), the command-side message format, and the service-graph wiring.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Define the enums, the job record, and the registry per Procedure | Completed | — | 20261124-160811 | Tests are written first in the same phase Done. Deviation from the procedure: register() derives approval level and cancelability from OPERATION_PROFILES/profile_for() rather than receiving the operation record from the caller; the profile table is the operation record the plan describes. Approved through the existing request-bound confirmation API per the owner decision of 2026-11-24. |
| 2 | Add the companion test file per Validation plan | Completed | — | 20261124-160811 | `tests/agent/services/test_maintenance_jobs.py` Written: tests/agent/services/test_maintenance_jobs.py, 24 passed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261124-160811 | ruff, mypy, bandit, check_module_size pass; targeted pytest passes. |

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
- **Requirement ID**: REQ-001 (one record per maintenance run, one writer per store), REQ-002 (cancellation), REQ-003 (approval levels), REQ-004 (verified outcomes)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `scripts/agent/services/maintenance_jobs.py`, `tests/agent/services/test_maintenance_jobs.py`