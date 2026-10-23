## Goal

Collapse the shutdown path's three dead timeout constants and the two hardcoded
`wait_for` literals into one named bound read by both `wait_for` calls (REQ-003), and
route the collected-error summary through the coordinator's `CLIView` in addition to
the log (REQ-007).

## Scope

Production behavior change to `scripts/agent/resource_shutdown_coordinator.py` only.
Reference reads: `scripts/agent/wal_checkpoint_manager.py` (the steps it awaits),
`scripts/agent/cli_view.py` (`write_warning`/`write_error`). Dependent tests:
`tests/agent/test_resource_shutdown_coordinator.py`, `tests/agent/test_repl.py`.

## Assumptions

- `self._view` is a `CLIView` already held (`:43`/`:57`) and exposes
  `write_warning`/`write_error`; confirm the method names and signatures at
  `cli_view.py` before calling them.
- The single bound value is a policy choice (UNK-01). Until UNK-01 decides otherwise
  keep the current outer values; this row only makes them *one named* value shared by
  both `wait_for` calls.
- At HEAD neither `wait_for` call reads a named constant — they hardcode
  `timeout=30.0` (`:74`) and `timeout=10.0` (`:93`) — and `_GRACEFUL_TIMEOUT_S`
  (`:29`) is defined but unused (verified at HEAD).

## Design decisions

- Introduce one module-level constant `_SHUTDOWN_TIMEOUT_S` (or, if UNK-01 decides
  the bound should be injected from config, one injected value) and use it for both
  `wait_for` calls; delete `_GRACEFUL_TIMEOUT_S` (`:29`) and the two literals.
- Because the two calls currently carry different literal bounds, collapsing to one
  value makes checkpoint and backup share a single bound; record that semantic
  consequence in the module docstring and let UNK-01 own the number.
- Add `self._view.write_warning(...)` (or `write_error`) alongside the existing
  `logger.error` at the summary (`:149-151`) so shutdown errors reach the
  human-visible channel as well as the log (REQ-007).

## Alternatives considered

- Injecting the bound from `cfg` via `repl.py` (the source issue's suggested route)
  vs keeping it in the coordinator: keep it in the coordinator — smaller
  single-sourced route, avoids colliding with `repl001`'s AC-5.

## Implementation

### Target file

`scripts/agent/resource_shutdown_coordinator.py`

### Procedure

Two independent edits, applied in this order:

1. **REQ-007 (not gated).** At the error summary (`:149-151`), after building
   `summary`, also call `self._view.write_warning(summary)` (or the appropriate
   severity method confirmed at `cli_view.py`). Keep the existing `logger.error`
   line. This is safe at HEAD and independent of the bound change.
2. **REQ-003 (gated on repl001).** Replace the two `timeout=` literals with one named
   bound used by both `wait_for` calls; delete `_GRACEFUL_TIMEOUT_S` (`:29`). Update
   the module docstring to state the single bound and its meaning ("bound expired").

### Details

- REQ-007 can be implemented and tested now; REQ-003 MUST wait until
  `plans/20261022-030840_plan.md` (repl001) is implemented, because repl001's AC-5
  holds `resource_shutdown_coordinator.py` byte-identical and this edit changes that
  file's bound constant. If forced earlier, gate the single-bound edit behind a
  clearly commented defer-to-repl001 note; do not leave two competing bound values.
- After REQ-003, `rg -n "_GRACEFUL_TIMEOUT_S" scripts/agent/resource_shutdown_coordinator.py`
  returns only the definition site removed (i.e. no reference remains), and both
  `wait_for` calls reference the single name.

## Compatibility considerations
Corrections found while implementing: the repl001 gate is satisfied (that plan is implemented); `CLIView` exposes `write_warning` and `write_fatal` but no `write_error`, so the summary uses `write_warning`; the single bound `_SHUTDOWN_TIMEOUT_S` is 30.0 for both steps, which loosens the backup bound from 10 s to 30 s (recorded in the module docstring), and the timeout entries now name the bound.


- Call shapes unchanged; only the timeout source and the error-summary side effect
  change. The live system's success path is unaffected.

## Security considerations

- N/A: no auth, secret, or permission change.

## Rollback considerations

- Two logical commits; `git checkout -- scripts/agent/resource_shutdown_coordinator.py`
  restores HEAD. Reversible; touches no config or DB.

## Validation plan

- `uv run pytest tests/agent/test_resource_shutdown_coordinator.py -q` (must pass;
  the five stubbed tests remain the ordering/error-collection contract).
- `uv run pytest tests/agent/test_repl.py -q` (no-production-change proof; green).
- `rg -n "time\.sleep" scripts/` → the shutdown retry site (now inside its worker) plus
  the unrelated `embedding.py` site; no `time.sleep` on the loop.
- `uv run ruff format`, `uv run ruff check`,
  `uv run mypy --no-namespace-packages scripts/agent/resource_shutdown_coordinator.py`,
  `uv run vulture scripts/agent/resource_shutdown_coordinator.py --min-confidence 80`.
- AC-5: a recorded shutdown error surfaces through `self._view` (assert the view call
  in the new/unstubbed coordinator test).

## Completion criteria

Both `wait_for` calls read one named bound, `_GRACEFUL_TIMEOUT_S` and the two
literals are gone, the error summary writes through `self._view` as well as `logger`,
and the module docstring states the single bound and its meaning. All gates pass.

## Out of Scope

- The step bodies themselves (`wal_checkpoint_manager.py`) — row 1.
- Choosing the bound number (UNK-01) — decided by reading the measurement in the new
  test file; this row only single-sources it.
- Docs updates — rows 6/7. Tests — rows 3/4/5.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Route error summary through `self._view` (REQ-007) | Completed | 20261023-144453 | 20261023-144453 | Not gated on repl001 implemented; full suite 9836 passed; procedures corrected (counts field names, step methods, TRUNCATE busy handling, single 30s bound, write_warning, mock counts) |
| 2 | Collapse to one named bound; delete `_GRACEFUL_TIMEOUT_S` and the two literals (REQ-003) | Completed | 20261023-144453 | 20261023-144453 | Gated on repl001 |
| 3 | Run validation sequence (`rules/toolchain.md`) | Completed | 20261023-144453 | 20261023-144453 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| REQ-003 | Changes the coordinator's bound constant, which `repl001` holds byte-identical (AC-5) | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| WI-02 | REQ-003 | Ordering | Open | implementer | after `plans/20261022-030840_plan.md` implemented |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003, REQ-007
- **Source issue**: `issues/20261021-093421_shutdown001-wal-checkpoint-timeout-guard-cannot-fire.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-043330_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-084708
- **Related target files**: `scripts/agent/resource_shutdown_coordinator.py`