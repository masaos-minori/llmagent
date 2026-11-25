## Goal

Create `ManagedProcessRecord` (new) — one record that owns process, pid, pgid, stderr log, lifecycle state, and last termination outcome, released only on confirmed exit (REQ-001, REQ-002).

## Scope
**Release unit**: R3-ownership

## Assumptions
- The record is mutable: outcome and state update in place during termination (Plan Design).
- The stderr log is referenced, not owned by value: `scripts/agent/http_lifecycle_stderr_log_manager.py` remains the stderr owner via its `forget`/`read_tail` API (Reference Files).

## Design decisions
- New leaf module `scripts/agent/http_lifecycle_process_record.py` importing stdlib plus `agent.http_lifecycle_errors` only, consistent with the import-layer contract (`skills/DESIGN.md` Shared Vocabulary); keeps `http_lifecycle.py` clear of the 24576 B module-size gate as the contract grows.
- A small mutable dataclass, not frozen: the last outcome and state change during termination.

## Alternatives considered
- A fourth dict alongside the existing three — rejected per Plan Design: the defect is exactly dict divergence per path.
- A frozen dataclass — rejected: outcome and state must update in place.

## Implementation
### Target file
`scripts/agent/http_lifecycle_process_record.py` (new)

### Procedure
Define `ManagedProcessRecord` (new) with fields: `process` (`subprocess.Popen[bytes]`), `pid`, `pgid` (`int | None`), `stderr_log` (stderr-manager handle), `state` (`LifecycleState`), `last_outcome` (new) (`TerminationOutcome | None`), `failed_start` (new) (`bool`, the startup-failure retention flag that replaces `_failed_start_procs`).

### Method
Plain dataclass; no methods beyond field storage and a `confirmed`-outcome convenience check delegating to `TerminationOutcome.confirmed` (`scripts/agent/http_lifecycle_errors.py:61`).

### Details
- The record is the single source of tracking: `HttpServerLifecycleManager` holds one `_records: dict[str, ManagedProcessRecord]` (row 03); the three parallel dicts disappear.
- Do not import `agent.lifecycle` for the state type if it creates a cycle; `LifecycleState` lives in `scripts/agent/lifecycle.py` (`:26-30`) and `agent.lifecycle` is already imported by the lifecycle cluster per grimp — verify with `lint-imports` after adding the import.

## Compatibility considerations
- New module: no existing consumers; the lifecycle cluster imports it once row 03 lands.

## Security considerations
- N/A: data storage only; no subprocess or signal behavior in this module.

## Rollback considerations
- N/A: revert the commit (delete the new file).

## Validation plan
- Unit: record field semantics and confirmed-release rule via `tests/agent/test_http_lifecycle.py`; `lint-imports` contract check for the new module (`rules/toolchain.md`).

## Completion criteria
- The module exists with the six fields, passes `lint-imports` and the record-ownership tests, and `check_module_size.py` reports it under the gate.

## Out of Scope
- The registry and its call-path changes (row 03).
- Per-path release rules in the coordinator and launcher (rows 04, 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Companion row 12 (tests/agent/test_http_lifecycle.py) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Includes `lint-imports` and `check_module_size.py` |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Generated reference artifacts covered by rows 21-23 |

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
- **Requirement ID**: REQ-001 (single record type), REQ-002 (release only on confirmed exit)
- **Source issue**: issues/20261119-145305_cliplc007_mcp-process-ownership.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-232847_cliplc007_mcp-process-ownership.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-235436
- **Related target files**: `scripts/agent/http_lifecycle_process_record.py`
