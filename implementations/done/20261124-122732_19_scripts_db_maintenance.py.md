## Goal

Accept a cancellation event on the long-running maintenance primitives and pass it to `SQLiteHelper.interrupt_when`, so a running maintenance operation can actually stop (REQ-002: cooperative cancellation through the progress handler).

## Scope
**Release unit**: R1-registry-core (Phase 1)

- In scope: the maintenance function signatures and the `interrupt_when` calls.
- Out of scope: the service wrapper (`db_maintenance_service.py`, row 21), the result-object contract (row 21, Phase 4), the command layer.

## Assumptions

- `interrupt_when` only fires at progress callbacks, so an operation whose work is a single long statement may not be interruptible; those operations are declared `not_cancelable` in their operation record rather than given a process boundary (UNK-01, UNK-04 resolved in the Phase 1 tests).
- `scripts/db/maintenance.py` is 20367 B against the 24576 B module gate, so the change must stay within the existing functions and not add a new helper layer here.

## Design decisions

- The event is an optional parameter on each long-running operation; the module does not decide whether an operation is cancelable — the registry declares that at registration.

## Alternatives considered

- Running maintenance in a separate process to make it interruptible — rejected for this phase: no evidence in this repository that a process boundary is needed, and it would change the deployment shape.

## Implementation
### Target file
`scripts/db/maintenance.py`

### Procedure
1. Add `stop: threading.Event | None` to `checkpoint_wal` (`:244`), `vacuum_db` (`:259`), `purge_old_sessions` (`:362`), `purge_corrupt_archives` (`:474`), and `prune_old_memories` (`:519`).
2. Call `db.interrupt_when(stop)` inside each operation's `SQLiteHelper` context; keep `check_every` at its default.
3. Return the measured outcome with an interrupted flag so the caller can distinguish a completed run from a stopped one.

### Method
- The existing `_handle_maintenance_error` (`:69`) and the retention guards (`:96`, `:107`) are unchanged; an interrupt is reported as a stopped run, not as an error.

### Details
- This module has no `interrupt_when` call today; the only existing use in the repository is `scripts/agent/services/rag_maintenance_service.py:69` (the plan's earlier `:426` citation was a docstring line, corrected at procedure time).

### Companion test files
- `tests/db/test_db_maintenance.py`
  - Procedure: assert the cancellation parameter is honored for each operation and the interrupted outcome is reported.
  - Validation: `uv run pytest tests/db/test_db_maintenance.py -q` (REQ-002; AC-2).

## Compatibility considerations

- Callers pass the new optional argument; existing behavior with `stop=None` is unchanged.

## Security considerations

- N/A: no trust boundary changes; the guard decision happens in the registry.

## Rollback considerations

- N/A: revert the Phase 1 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/db/maintenance.py` | Unit | `uv run pytest tests/db/test_db_maintenance.py -q` | Cancellation honored |
| Same file | Size gate | `uv run python tools/check_module_size.py` | Stays under the 24576 B gate |
| Same file | Quality gates | `uv run ruff check scripts/db/maintenance.py`, `uv run mypy scripts/db/maintenance.py`, `uv run bandit -c pyproject.toml scripts/db/maintenance.py` | No finding |

## Completion criteria

- Every long-running maintenance operation stops at a progress callback when its event is set, and a stopped run is reported as stopped rather than as a completed count.

## Out of Scope

- The service wrapper, the postconditions (Phase 4), the registry.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the cancellation event and `interrupt_when` calls | Completed | — | 20261124-160811 | Phase 1 stop parameter added to the five operations; interrupt_when installed only when stop is not None, so stop=None behavior is unchanged. |
| 2 | Update the companion test per Validation plan | Completed | — | 20261124-160811 | Covered by this document Test class TestCancellationIsHonored added: 123 passed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261124-160811 | ruff, mypy, bandit, check_module_size pass (23302 B, under the 24576 B gate). |

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
- **Requirement ID**: REQ-002 (cancellation through the progress handler)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `scripts/db/maintenance.py`, `tests/db/test_db_maintenance.py`