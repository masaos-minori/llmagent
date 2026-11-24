## Goal

Give the database layer one authority that decides when a write is allowed: `WriteGate` (new) with the states `open`, `closing` and `closed`, an authorized-operation context for the shutdown steps that must still write, and a counter of refused writes that the shutdown report prints (REQ-004: writes stop when shutdown starts; REQ-005: the refusal is enforced in the db layer; AC-2: no write succeeds after the gate closes).

## Scope
**Release unit**: R2-write-gate (Phase 2)

- In scope: the gate object, its three states, the authorized-operation context, the refused-write counter, and the refusal exception.
- Out of scope: consulting the gate from the write paths (row 3 `scripts/db/helper.py`), the package exports (row 4 `scripts/db/__init__.py`), and who closes the gate and when (row 5 `scripts/agent/resource_shutdown_coordinator.py`).

## Assumptions

- The gate lives in `scripts/db/` because the import contract allows only `agent -> db`: an agent-side flag could not stop a write made from another db-layer caller, and a db module must not import from `agent`.
- The gate is process-wide and owned by the db layer, not passed per call: the shutdown coordinator closes it once and every write path consults the same object.
- The gate is a new module because `scripts/db/helper.py` is 21518 B, the file closest to the 24576 B module-size gate enforced by `tools/check_module_size.py`; adding the gate there risks the gate check.

## Design decisions

- Three states instead of a boolean: `closing` refuses new writes while the steps already authorized finish, and `closed` refuses everything, so the coordinator can distinguish "no new work" from "no work at all".
- Authorized writes use an explicit context (a context manager that names the step holding the authorization) rather than a bypass flag on each write function: the authorization is scoped, cannot leak past the `with` block, and is auditable.
- Refusals raise one exception type (`WriteGateClosed` (new)) and increment a counter, so a caller that swallows the error is still counted in the report (REQ-012).
- Compatibility impact: no existing signature changes; existing write calls behave identically while the gate is `open`.

## Alternatives considered

- refuse writes by closing the connection — rejected: reads must keep working for the snapshot and checkpoint steps (REQ-006, REQ-008), and a closed connection cannot be reopened inside the deadline.

## Implementation
### Target file
`scripts/db/write_gate.py` (new)

### Procedure
1. Define `WriteGateState` (new) with `open`, `closing`, `closed`.
2. Define `WriteGateClosed` (new), the exception raised when a write is refused.
3. Define `WriteGate` (new): `close()` (new) (open to closing, closing to closed), `close_now()` (new) (straight to closed), `check_write()` (new) raising `WriteGateClosed` (new) unless the state is `open` or the caller holds an authorization, `refused_count` (new), and `authorized(step_name)` (new) returning the scoped context manager.
4. Provide one module-level gate instance and an accessor the db layer uses internally.

### Method
- State machine plus a counter, no I/O: the gate decides and records, it does not own connections or transactions.
- The authorization context stores the step name so a refusal message can name the step that was denied, and clears the authorization on exit.

### Details
- `closing` is the state the coordinator sets before the settle-writers step; `closed` is set after it, which is what makes a late write from a background task a refusal rather than a silent success.
- The refusal message names the state and the step, never a file path or a DSN (REQ-013).

## Compatibility considerations

- New module: no existing importers until rows 3 and 4 land.
- While the gate is `open` every write path behaves exactly as today, so the change is inert until the coordinator closes it.

## Security considerations

- `WriteGateClosed` (new) carries no connection string, path, or SQL text (REQ-013); the statement that was refused is not recorded.

## Rollback considerations

- N/A: revert the Phase 2 commit; nothing consults the gate until row 3 lands.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/db/write_gate.py` | Unit | `uv run pytest tests/db/test_write_gate.py -q` | state transitions, refusal, authorized steps pass, counter increments |
| `scripts/db/write_gate.py` | Static | `uv run python tools/check_module_size.py` | the new module stays under the 24576 B gate |

## Completion criteria

- A write attempted in `closing` without authorization and any write in `closed` raise `WriteGateClosed` (new), and each refusal is counted.
- A write inside `authorized()` succeeds in `closing` and the authorization does not outlive the block.

## Out of Scope

- Consulting the gate from the write paths, exporting the symbols, closing the gate from the shutdown sequence, and the thread-safety tests (row 25).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | companion row 21 |
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
- **Requirement ID**: REQ-004 (writes stop at shutdown), REQ-005 (enforced in the db layer)
- **Source issue**: issues/20261119-145302_cliplc004_bounded-shutdown-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095950_cliplc004_bounded-shutdown-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-000005
- **Related target files**: `scripts/db/write_gate.py`, `tests/db/test_write_gate.py`
