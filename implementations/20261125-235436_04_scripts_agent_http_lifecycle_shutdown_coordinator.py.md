## Goal

Stop deleting the process entry before termination; settle cleanup and state per server from the termination outcome, and re-terminate retained records on repeated shutdown (REQ-002, REQ-003, REQ-010).

## Scope
**Release unit**: R3-ownership

## Assumptions
- Budget clamping and SIGINT forwarding (cliplc004, OD-05) are untouched; re-termination runs inside the same `budget.remaining()` and interrupt-event semantics (Plan Risks).
- The record type is declared by row 02; this document uses it as a sibling-declared name.

## Design decisions
- Per-server settling moves into the record module so `ShutdownCoordinator.shutdown_all` (radon C today) does not grow past C (Plan Design, Validation quality baseline).
- Repeated shutdown mirrors the existing `_reterminate_recorded_failed_start` pattern (`scripts/agent/http_lifecycle.py:363-394`).

## Alternatives considered
- Keeping the pre-termination pop and re-adding the entry on failure — rejected: the retained record is the visibility contract (AC-1); re-adding after a failed pop recreates the split-dict divergence.

## Implementation
### Target file
`scripts/agent/http_lifecycle_shutdown_coordinator.py`

### Procedure
Remove the pre-termination `remove_process_entry` call at `:210-211`; after termination, release the record only when `outcome.confirmed` (`:134-147` already gates `cleanup_server_key` on confirmation); on unconfirmed outcomes retain the record and keep the manual-cleanup log (`:138-146`). Add the repeated-shutdown pass that re-terminates retained records.

### Method
Call-path change: the coordinator operates on `manager._records` entries instead of `manager._http_procs`; the per-server outcome-to-state mapping is delegated to the record settling helper (row 02).

### Details
- `shutdown_all` (`:149`) iterates records, not configured-server dicts, so retained unconfirmed servers are visible and re-terminatable.
- The retained-record log must keep printing `kill -TERM -<pgid>` with the record's pgid (REQ-010, maintainer decision 2026-11-25: no new command).

### Companion test files
- `tests/agent/test_http_lifecycle_shutdown_coordinator.py`
  - Procedure: no-pre-termination-removal, per-server outcome, and repeated-shutdown tests (REQ-011 defect-pinning set, Phase 1); pin that a spent budget still signals and reports, never waits.
  - Validation: `uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py`.

## Compatibility considerations
- `remove_process_entry` callers: only `:211` today (consumer scan, Plan Design); row 03 keeps it as the post-confirmation helper.

## Security considerations
- N/A: signal delivery semantics unchanged.

## Rollback considerations
- Revert the commit.

## Validation plan
- Unit: `uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py` — entries live until confirmed; repeated shutdown re-terminates (REQ-003, REQ-010).
- `radon cc` re-run at Phase 7: no block worse than C.

## Completion criteria
- No entry is removed before termination; every unconfirmed server keeps its record and its state; a second `shutdown_all` re-terminates retained records within the budget (AC-1, AC-5).

## Out of Scope
- The record type itself (row 02), the router's per-server state mapping (row 06), the PGID-failure path (row 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Companion row 13 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docs rows 19-23 |

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
- **Requirement ID**: REQ-002 (confirmed-exit release), REQ-003 (no pre-termination deletion), REQ-010 (repeated shutdown, manual cleanup)
- **Source issue**: issues/20261119-145305_cliplc007_mcp-process-ownership.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-232847_cliplc007_mcp-process-ownership.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-235436
- **Related target files**: `scripts/agent/http_lifecycle_shutdown_coordinator.py`, `tests/agent/test_http_lifecycle_shutdown_coordinator.py`
