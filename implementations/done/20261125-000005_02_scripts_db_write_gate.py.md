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
- Verified against source 2026-11-25 (execution): the Plan's REQ-004 names the method `gate.authorize(operation_name)` (`plans/done/20261124-095950_cliplc004_bounded-shutdown-machine.md:78`), so the context manager is `authorize(step_name)`, not `authorized(step_name)`. `WriteGateClosed` subclasses `RuntimeError`, the repository convention for an operational refusal (`scripts/mcp_servers/file/common.py:34`, `scripts/mcp_servers/cicd/cicd_models.py:63`).
- Authorization is held in a `contextvars.ContextVar` stack, not a plain instance field: the shutdown steps run their DB work on `asyncio.to_thread` workers (`scripts/agent/wal_checkpoint_manager.py:66,134`, `scripts/agent/turn_persistence.py:105-207`), and `asyncio.to_thread` copies the caller's context, so a step authorized by the coordinator covers the write its worker performs, while a thread that was not started inside the `with` block (a background writer left over from normal operation) does not inherit it.
- `reset()` (new) returns the gate to `open` with a zero counter, documented the way `clear_shutdown_flag` is (`scripts/eventbus/db_conn.py:54-61`): a fresh app lifecycle or a fresh test context must not inherit a previous shutdown's state. Without it the process-wide gate would leak a closed state into the next test in the same xdist worker.
- `is_write_statement(sql)` (new) exists because `SQLiteHelper.execute` is not a write-only entry point: 22 call sites in `scripts/` pass a literal `SELECT` through it (`grep -c "\.execute(\s*[\"']SELECT" scripts/`), and REQ-006 and REQ-008 require reads to keep working while writes are refused. The rule is: strip leading whitespace and `--` / block comments, take the first keyword, treat `SELECT`, `EXPLAIN`, and a bare `PRAGMA name` as reads, and treat everything else — including `WITH`, `VALUES`, and an assigned or argument-bearing `PRAGMA` — as a write (fail closed). `scripts/` contains no CTE, so the fail-closed branch refuses no read that exists today.

## Alternatives considered

- refuse writes by closing the connection — rejected: reads must keep working for the snapshot and checkpoint steps (REQ-006, REQ-008), and a closed connection cannot be reopened inside the deadline.

## Implementation
### Target file
`scripts/db/write_gate.py` (new)

### Procedure
1. Define `WriteGateState` (new) with `open`, `closing`, `closed`.
2. Define `WriteGateClosed` (new), the exception raised when a write is refused.
3. Define `WriteGate` (new): `state` and `refused_count` (new) properties, `close()` (new) (open to closing, closing to closed, idempotent), `close_now()` (new) (straight to closed), `check_write(operation)` (new) raising `WriteGateClosed` (new) unless the state is `open` or the caller holds an authorization, `authorize(step_name)` (new) returning the scoped context manager, and `reset()` (new).
4. Define `is_write_statement(sql)` (new): the classifier the helper consults, fail-closed on an unknown leading keyword (see Design decisions).
5. Provide one module-level gate instance with `get_write_gate()` (new) as the accessor, following the existing db shutdown-flag precedent `scripts/eventbus/db_conn.py:34-61` (`set_shutdown_flag` / `is_shutting_down` / `clear_shutdown_flag`), which the Plan cites as the model.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-082622 | 20261125-082622 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261125-082622 | 20261125-082622 | companion row 21 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-082622 | 20261125-082622 | R2 unit run: fast gates Pass; full suite 14217 passed / 7 skipped; diff-cover 100% |

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