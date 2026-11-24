## Goal

Give the shutdown sequence one clock and one outcome vocabulary: `ShutdownBudget` (new) armed by the first shutdown request, `remaining()` for every step, `ShutdownPhase` (new) acceptance states, and the `ShutdownStepRecord` (new) plus `ShutdownReport` (new) types the coordinator records (REQ-001: one owner and sequence; REQ-002: one global deadline; REQ-012: every step reported).

## Scope
**Release unit**: R1-budget-and-config (Phase 1)

- In scope: the budget object, the acceptance phase, the step names, the outcome vocabulary, the step record and report types.
- Out of scope: running the steps (row 5 `scripts/agent/resource_shutdown_coordinator.py`), the write gate (row 2), and every consumer of the budget (rows 7, 8, 10, 11).

## Assumptions

- The budget is constructed unarmed during the REPL wiring (`scripts/agent/repl.py:85-92`) and armed by the first shutdown request; `arm()` returning `False` for later requests is what makes the first signal win (Plan Design, "One budget, many consumers").
- Arming and the interrupt request can arrive from a signal-handler thread while the event loop reads `remaining()`, so the mutable state is guarded by a `threading.Lock` and the clock is monotonic rather than wall-clock.
- The total is passed in by the caller from the `AgentConfig` deadline field (row 17); this module reads no configuration itself.
- Overlap: `scripts/agent/repl.py` was also a target of the cliplc003 Plan (`plans/done/20261124-001800_cliplc003_maintenance-job-framework.md`). cliplc003 landed upstream (commits `7e31a92e7..dfb9862e3`, procedures archived under `implementations/done/`), so this Plan's row 7 edits build on the landed wiring.

## Design decisions

- One object owns the clock and the phase together: the phase that decides acceptance is driven by the same arming event that starts the deadline, so no consumer can observe a draining phase with an unarmed budget.
- `ShutdownStepRecord` (new) and `ShutdownReport` (new) are frozen dataclasses assembled by appending records; the report is not mutated after a step finishes.
- One outcome enum (`completed`, `timed_out`, `failed`, `not_started` (new), `outcome_unknown`) is shared with the MCP step, which maps the existing `TerminationOutcome` values into it instead of inventing a second vocabulary (REQ-012).
- `detail` (new) on the record holds a reason category plus a bounded, path-free summary; paths and exception text stay in the logger (REQ-013).
- Concrete API (decided at execution 2026-11-25): `ShutdownBudget(total_seconds, clock=time.monotonic)` takes an injectable monotonic clock so the clamping and idempotence tests are deterministic; `armed` and `interrupt_requested` are properties; `mark_closed()` moves the phase to `closed` when the sequence finishes; the eight step names are module constants plus a `SHUTDOWN_STEPS` tuple in the REQ-001 order.

## Alternatives considered

- Keep the deadline in the coordinator and hand each step its own timeout — rejected: the coordinator would still be a second clock, and a step that never started could not be told apart from one that timed out (REQ-012).
- Let each consumer track its own shutdown state — rejected: two sources of truth is the failure mode the Plan's Problem section names, and row 8 reads the acceptance phase from this object.
- Carry the exception text and the file path in `ShutdownStepRecord.detail` — rejected: the record is rendered on the console, which is where REQ-013 forbids a path or raw exception text.

## Implementation
### Target file
`scripts/agent/shutdown_budget.py` (new)

### Procedure
1. Define `ShutdownPhase` (new) with the states accepting, draining, closed.
2. Define `ShutdownBudget` (new): `arm()` (new) returning `False` for every request after the first (arming also moves the phase to `draining`), `remaining()` (new) clamped at zero, `armed` (new) and `interrupt_requested` (new) properties, `phase`, `mark_closed()` (new), and `request_interrupt()` (new).
3. Define the eight step-name constants: `enter_shutdown` (new), `settle_writers` (new), `persist_snapshot` (new), `checkpoint` (new), `backup` (new), `terminate_lifecycles` (new), `close_hooks` (new), `report` (new), plus the `SHUTDOWN_STEPS` tuple in the REQ-001 order.
4. Define `ShutdownOutcome` (new) with the five values, `ShutdownStepRecord` (new) (name, outcome, elapsed_s, detail), and `ShutdownReport` (new) (records, refused-write count, unsettled-writer names).

### Method
- Pure model plus one small stateful object: no I/O, no asyncio, no import from `agent` services, so every layer may hold it without violating the `.importlinter` contracts.
- `remaining()` (new) computes the deadline minus the monotonic clock, clamped to zero, and never extends the deadline.

### Details
- `arm()` (new) records only the first request, which is what stops repeated Ctrl-C from pushing the deadline outward.
- `ShutdownReport` (new) carries the refused-write count and the unsettled-writer names that the report step prints (REQ-012).

### Companion test files
- `tests/agent/test_shutdown_budget.py` (new)
  - Procedure: write the tests before the module exists: arming, first-request-wins idempotence, `remaining()` clamping at and past the deadline, phase transitions, and the five outcome values.
  - Validation: `uv run pytest tests/agent/test_shutdown_budget.py -q`

## Compatibility considerations

- New file: no existing importers and no signature changes elsewhere.
- The existing fixed windows stay as fallbacks until rows 5 and 11 read the budget, so an unbudgeted call path keeps today's behavior.

## Security considerations

- `detail` (new) is bounded and path-free by construction (REQ-013); absolute paths and raw exception text belong to the logger that already carries `attach_redaction_filter` (`scripts/shared/logger.py:64`).

## Rollback considerations

- N/A: revert the Phase 1 commit; nothing imports the module until rows 5, 7, 8, 10 and 11 land.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/shutdown_budget.py` | Unit | `uv run pytest tests/agent/test_shutdown_budget.py -q` | arming, idempotence, clamping, phase transitions and the vocabulary pass |
| `scripts/agent/shutdown_budget.py` | Static | `uv run python tools/check_module_size.py` | the new module stays under the 24576 B gate |

## Completion criteria

- One armed budget yields a fixed deadline that later requests cannot extend, and `remaining()` reaches zero and stays there.
- Every step outcome is expressible with one value from the one vocabulary, and a record names its step, outcome, elapsed time and bounded detail.

## Out of Scope

- Executing or ordering the steps, the write gate, signal routing, and the documentation rows 45-55.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the budget tests first (companion file) | Completed | 20261125-073338 | 20261125-074347 | Phase 1 lists tests first |
| 2 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261125-074347 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-074347 | 20261125-075448 |  |

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
- **Requirement ID**: REQ-001 (one owner and sequence), REQ-002 (one global deadline), REQ-012 (every step reported)
- **Source issue**: issues/20261119-145302_cliplc004_bounded-shutdown-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095950_cliplc004_bounded-shutdown-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-000005
- **Related target files**: `scripts/agent/shutdown_budget.py`, `tests/agent/test_shutdown_budget.py`