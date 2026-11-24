## Goal

Make each Session maintenance operation return a result object that carries its postcondition outcome, and accept the job's cancellation event, so the caller can report a verified run instead of printing success before anything is checked (REQ-004: success only after the postcondition; REQ-002: cooperative interruption).

## Scope
**Release unit**: R1-registry-core (Phase 1, cancellation plumbing); the postconditions are R4-verified-results (Phase 4)

- In scope: the `DbSessionOps` operation methods and their return types.
- Out of Scope: the message formatting in `cmd_session.py` (row 3), the `DbMaintenanceService` wrapper (row 21).

## Assumptions

- `DbSessionOps` is constructed with `AgentContext` and `OutputPort` (`scripts/agent/commands/db_session_ops.py:15`); the job and its event are passed in by the caller, not fetched from a global.
- The consumer scan recorded 6 direct scripts and 23 tests for this module, so the signature change lands with the call-site updates in the same commit.
- `scripts/db/maintenance.py` is 20367 B and close to the 24576 B gate; the postcondition code lives here, not in that file.

## Design decisions

- Each operation returns a result dataclass (new) with its measured outcome instead of a dict or `None`, because the caller must be able to distinguish "ran" from "ran and verified" (REQ-004).
- The postcondition is measured inside the operation, so a result object cannot be constructed by a caller that did not run the check.
- Cancellation is accepted as an optional `threading.Event` and forwarded to `DbMaintenanceService`; the operation does not decide whether an operation is interruptible — the registry declares that at registration.

## Alternatives considered

- Keeping the dict returns and adding a separate `verify()` call — rejected: two calls that can be skipped independently is the failure mode REQ-004 removes.

## Implementation
### Target file
`scripts/agent/commands/db_session_ops.py`

### Procedure
1. Change `checkpoint` (`db_session_ops.py:33`), `vacuum` (`:42`), `purge` (`:47`), and `recover` (`:79`) to take a `stop` event and return a result object.
2. Add the postconditions the Plan's Design section names: `checkpoint` re-measures `journal_mode` and WAL size; `vacuum` re-measures `page_count` and reports the delta; `purge` re-counts the removed rows; `recover` re-runs the existing consistency check.
3. Remove the success string from each method: the caller emits the message from the result, so an interrupted run cannot print success.
4. Keep `health` (`:20`) read-only; it registers with `ApprovalLevel.NONE` and returns its measurements unchanged.

### Method
- Return one result shape per operation (`CheckpointResult` (new), `VacuumResult` (new), `PurgeResult` (new), `RecoverResult` (new)) (new), each carrying `verified: bool`, the measured values, and the interrupted flag.
- On an interrupt (`sqlite3.OperationalError`, message `interrupted`) the result reports the pre-run state, not a partial delta.

### Details
- `DbMaintenanceService(self._ctx.cfg.db, self._ctx.cfg.maintenance)` is constructed per call in this file (`db_session_ops.py:21-24,34-36,43`); it must be the injected instance so the same registry carries the job (row 21).
- The `_retention_guard` and config-loading behavior in `scripts/db/maintenance.py` is not replicated here.

## Compatibility considerations

- 23 tests reference these operations; the change lands with `tests/db/test_db_maintenance.py` (row 61, covered by row 20's document) and `tests/agent/commands/test_agent_cmd_session.py` (row 42, its own document).
- `tests/agent/commands/test_command_blocking_offload.py` (row 47) currently locks "the offloaded callable runs to completion"; that lock is replaced in the same phase by the cooperative-interruption behavior.

## Security considerations

- `vacuum` is a `guard`-level operation: the free-space and single-writer conditions are checked by the registry before this module runs, so no approval logic belongs in this file.

## Rollback considerations

- Revert the Phase 1 commit; the result types are not referenced outside the command path.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/commands/db_session_ops.py` | Unit | `uv run pytest tests/db/test_db_maintenance.py tests/agent/commands/test_agent_cmd_session.py -q` | Cancellation event honored; each operation returns a verified result |
| Same file | Quality gates | `uv run ruff check scripts/agent/commands/db_session_ops.py`, `uv run mypy scripts/agent/commands/db_session_ops.py`, `uv run bandit -c pyproject.toml scripts/agent/commands/db_session_ops.py` | No finding |

## Completion criteria

- Each operation returns a result object with a measured postcondition, the success message comes from that object, and an interrupted run reports `cancelled` or `outcome_unknown` — never success.

## Out of Scope

- The registry itself (row 1), the command messages (row 3), the `DbMaintenanceService` pass-through (row 21).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the cancellation event and the result types per Procedure | Completed | — | 20261124-160831 | Phase 1 Phase 1 part done: operations take stop and return the result objects; success strings removed; health returns DbHealth. Deviation: the service instance is built once per handler instance in _service_for_call so the existing class-patch fixtures still work. |
| 2 | Add the postcondition measurements per Procedure step 2 | Pending | — | — | Phase 4 (R4) |
| 3 | Update the affected tests per Validation plan | Completed | — | 20261124-160831 | Row 42 is its own document (named by two rows); `tests/db/test_db_maintenance.py` (row 61) is covered by row 20 Phase 1 part done in row 42 and tests/db/test_db_maintenance.py: pinned purge call assertions now pass stop=, typed result dataclasses replace MagicMock results. |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261124-160831 | Phase 1 part: ruff, mypy pass; targeted pytest passes. |

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
- **Requirement ID**: REQ-004 (verified result before the success line), REQ-002 (cancellation through the progress handler)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `scripts/agent/commands/db_session_ops.py`