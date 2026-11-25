## Goal

Retain the process record after a `getpgid()` failure unless the exit is confirmed, and name the pid in the manual-cleanup log (REQ-002, REQ-004).

## Scope
**Release unit**: R3-ownership

## Assumptions
- This row overlaps cliplc006's pending procedure for the same file (`implementations/20261125-223712_04_scripts_agent_http_lifecycle_subprocess_launcher.py.md`, launch-spec scope); the Plan sequences this Plan after cliplc006 (UNK-04). Apply this change on top of that procedure, not in parallel.
- The record type is declared by row 02; the launcher reads it as a sibling-declared name.

## Design decisions
- Same release rule as the coordinator: the record is released only on a confirmed outcome; a failed `getpgid()` leaves `pgid` as `None` on the record, which is the honest state, not a missing entry.

## Alternatives considered
- Recording a fallback pgid equal to the pid — rejected: the process group may exist under a different id; guessing could direct a manual `kill` at the wrong group.

## Implementation
### Target file
`scripts/agent/http_lifecycle_subprocess_launcher.py`

### Procedure
In `handle_getpgid_failure` (`:126`), replace the unconditional pops at `:165-166` with the record release gated on `outcome.confirmed`; change the unconfirmed log (`:151`) to name the pid from the record and state that the record is retained.

### Method
Condition-flip on the existing termination branch; the stderr release stays unconditional (docstring at `:134-136` already releases stderr regardless of outcome — keep it, stderr is not process ownership).

### Details
- `pgid` population stays at `:114` on the success path; on failure the record's `pgid` remains `None` and the log must not print a stale dict value.
- The manual-cleanup sentence keeps the `kill -TERM -<pgid>` form only when a pgid exists; otherwise it names the pid alone (maintainer decision 2026-11-25: no new command).

## Compatibility considerations
- The launcher's public signature is unchanged; only the tracking side effect changes.

## Security considerations
- N/A: no change to signal delivery, only to tracking retention and logging.

## Rollback considerations
- Revert the commit.

## Validation plan
- Unit: `uv run pytest tests/agent/test_http_lifecycle.py` — unconfirmed records retained after PGID failure (REQ-004, AC-1).

## Completion criteria
- An unconfirmed `getpgid()` failure leaves the record in the registry and the log names the pid; a confirmed exit releases the record.

## Out of Scope
- Launch-spec and command-validation work already covered by cliplc006's pending procedures.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Apply after cliplc006's launcher procedure (UNK-04) |
| 2 | Add or update tests per Validation plan | Pending | — | — | Companion row 12 |
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
- **Requirement ID**: REQ-002 (confirmed-exit release), REQ-004 (retain records after PGID failure)
- **Source issue**: issues/20261119-145305_cliplc007_mcp-process-ownership.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-232847_cliplc007_mcp-process-ownership.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-235436
- **Related target files**: `scripts/agent/http_lifecycle_subprocess_launcher.py`
