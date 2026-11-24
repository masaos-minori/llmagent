## Goal

Make `close_resources()` the single ordered step machine: settle the writers, persist the snapshot, checkpoint, back up, terminate lifecycles, run the close hooks, then report, with one record per step and the `not_started` rule for steps the deadline makes impossible (REQ-001: one owner and sequence; REQ-005: the gate is closed by this owner; REQ-006: the sequence is bounded; REQ-012: every step is reported; AC-1, AC-2, AC-3, AC-4).

## Scope
**Release unit**: R4-sequence-and-snapshot (Phase 4); the checkpoint and backup steps of R5-checkpoint-and-backup (Phase 5) land on the same function

- In scope: `close_resources()`, the step order, the per-step records, the docstring and class invariants, and the report output.
- Out of scope: the budget object (row 1), the gate (rows 2-4), the checkpoint and backup internals (row 6), the termination internals (rows 11-16), and the REPL wiring (row 7).

## Assumptions

- The current docstring states the opposite order: `scripts/agent/resource_shutdown_coordinator.py:41-45` records "Checkpoint-before-cancellation ordering", and `tests/agent/test_repl.py:1331-1372` pins it with an event-sequence assertion. The Plan's Owner decision OD-01 supersedes that ordering (`REQ-RSC001B-1` in `plans/done/20260908-065641_plan.md:4,17,84`), so both the docstring and the test change in this Plan.
- The 30 s window at `scripts/agent/resource_shutdown_coordinator.py:32` bounds only the checkpoint and cancel steps today; the budget replaces it as the authority once this row lands.
- The interrupt and cancellation machinery already exists: `interrupt_when` (`scripts/db/helper.py:158-184`) aborts a running statement through the sqlite3 progress handler, and `_cancel_tracked_tasks` (`scripts/agent/resource_shutdown_coordinator.py:173-196`) cancels and joins the tracked tasks. The settle step composes them under one window instead of replacing them.
- Steps that cannot start because `remaining()` is already zero are recorded as `not_started` (new) rather than skipped silently (REQ-012).

## Design decisions

- Settle writers before the checkpoint: a checkpoint cannot be trusted while a writer can still commit, so the gate closes, in-flight writers are given the settle window, and only then does the checkpoint run. This is the deliberate behavior change of OD-01.
- One step list, one loop: each step is a name plus a callable, so the order is readable in one place and each iteration produces one `ShutdownStepRecord` (new) regardless of outcome.
- The class keeps ownership: no consumer runs a step on its own; consumers arm the budget and read the report.
- Compatibility impact: the observable order of shutdown events changes; anything that asserted the old order must be updated (row 27).

## Alternatives considered

- keep the checkpoint first and cancel after — rejected: it is the ordering the Plan supersedes, and it leaves a committed write uncheckpointed when the cancel step consumes the window.

## Implementation
### Target file
`scripts/agent/resource_shutdown_coordinator.py`

### Procedure
1. Replace the fixed window at `scripts/agent/resource_shutdown_coordinator.py:32` with the budget's `remaining()` (row 1).
2. Rewrite the class docstring at `scripts/agent/resource_shutdown_coordinator.py:41-51` to state the settle-first order and the invariants: one owner, one deadline, one record per step.
3. Restructure `close_resources()` (`scripts/agent/resource_shutdown_coordinator.py:76-171`) into the ordered steps: `enter_shutdown` (new), `settle_writers` (new), `persist_snapshot` (new), `checkpoint` (new), `backup` (new), `terminate_lifecycles` (new), `close_hooks` (new), `report` (new).
4. Keep the checkpoint body (`scripts/agent/resource_shutdown_coordinator.py:81-101`) and the cancellation body (`scripts/agent/resource_shutdown_coordinator.py:124-128`) as the step callables, moved into the new order.
5. Implement `settle_writers` (new): interrupt each tracked SQLite connection through `interrupt_when` (`scripts/db/helper.py:158-184`), then cancel and join the tracked tasks with the existing `_cancel_tracked_tasks` (`scripts/agent/resource_shutdown_coordinator.py:173-196`), waiting at most `shutdown_settle_seconds` (new) (row 17); a writer still running when the window ends is recorded `outcome_unknown` with its task name (REQ-005).
6. Close the write gate at the start of `settle_writers` (new) and carry the refused-write count into the report assembled from the step records.

### Method
- Each step is bounded by `remaining()` (new) at the moment it starts; a step that would start past the deadline is recorded `not_started` (new) and its side effects are skipped.
- A step that raises is recorded `failed` with a bounded detail and the sequence continues to the next step, so one failure cannot hide the rest of the report.

### Details
- The step names are the constants defined in row 1, so the report and the budget use one vocabulary.
- The report line carries the step name, outcome, elapsed seconds, and the refused-write count (REQ-012), with no absolute paths (REQ-013).

### Companion test files
- `tests/agent/test_resource_shutdown_coordinator.py`
  - Procedure: assert the settle-first step order, one `ShutdownStepRecord` (new) per step, the `not_started` rule when no time remains, and per-step clamping.
  - Validation: `uv run pytest tests/agent/test_resource_shutdown_coordinator.py -q` (REQ-001, REQ-005, REQ-006, REQ-012; AC-1, AC-3).

## Compatibility considerations

- The shutdown event order is an observable change: `tests/agent/test_repl.py:1331-1372` and the coordinator's own tests must be updated in the same release unit (rows 26, 27).
- Step callables keep their existing signatures, so the checkpoint and cancel implementations are reused unchanged apart from the budget parameter.
- Overlap: `scripts/agent/repl.py` is also a target of the cliplc003 Plan (`plans/done/20261124-001800_cliplc003_maintenance-job-framework.md`); its procedures under `implementations/20261124-122732_` must land before row 7 edits the same wiring. No symbol is shared with `close_resources()`.

## Security considerations

- Report details are reason categories and bounded summaries; paths and exception text stay in the logger (REQ-013).

## Rollback considerations

- Revert the Phase 4 commit as a unit with rows 26 and 27: reverting the coordinator alone leaves tests that assert the new order, and reverting the tests alone leaves the old order asserted against new code.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/resource_shutdown_coordinator.py` | Unit | `uv run pytest tests/agent/test_resource_shutdown_coordinator.py tests/agent/test_repl.py -q` | settle-before-checkpoint order, per-step records, `not_started` rule, per-step clamping pass |
| `scripts/agent/resource_shutdown_coordinator.py` | Integration | `uv run pytest tests/agent/test_http_lifecycle_integration.py -q` | the sequence reaches the termination path within the budget |

## Completion criteria

- The recorded step order is settle, snapshot, checkpoint, backup, terminate, hooks, report, and every step has exactly one record with an outcome from the shared vocabulary.
- No step runs outside the budget, and a step the budget cannot cover is recorded `not_started` (new).

## Out of Scope

- The gate implementation, the checkpoint and backup internals, the termination internals, and the REPL wiring.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | companion row 26, row 27 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (one owner and sequence), REQ-005 (refusal in the db layer), REQ-006 (bounded sequence), REQ-012 (every step reported)
- **Source issue**: issues/20261119-145302_cliplc004_bounded-shutdown-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095950_cliplc004_bounded-shutdown-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-000005
- **Related target files**: `scripts/agent/resource_shutdown_coordinator.py`, `tests/agent/test_resource_shutdown_coordinator.py`
