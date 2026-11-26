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
In `handle_getpgid_failure` (verified 2026-11-26: `:142`), replace the unconditional pops at `:181-182` with the record release gated on `outcome.confirmed`; change the unconfirmed log (`:166-172`) to name the pid from the record and state that the record is retained. Register the record (pgid `None`) before the termination attempt so the retained path has an entry to keep.

### Method
Condition-flip on the existing termination branch; the stderr release stays unconditional (docstring at `:134-136` already releases stderr regardless of outcome — keep it, stderr is not process ownership).

### Details
- `pgid` population stays on the success path (verified 2026-11-26: `:130`); on failure the record's `pgid` remains `None` and the log must not print a stale dict value.
- The manual-cleanup sentence keeps the `kill -TERM -<pgid>` form only when a pgid exists; otherwise it names the pid alone (maintainer decision 2026-11-25: no new command).

## Compatibility considerations
- The launcher's `create_and_validate_proc` signature is unchanged; `__init__` changes: `http_procs`/`http_pgids` kwargs are replaced by `records: dict[str, ManagedProcessRecord]` (verified 2026-11-26: the manager injects `records=self._records` per row 03, so the dict kwargs cannot survive). Only the tracking side effect changes otherwise.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-132500 | 20261126-133500 | Apply after cliplc006's launcher procedure (UNK-04) Changed files: scripts/agent/http_lifecycle_subprocess_launcher.py; __init__ takes records kwarg (Compatibility corrected during verification); getpgid-failure record registered before the attempt, released only on confirmed outcome |
| 2 | Add or update tests per Validation plan | N/A | — | — | Companion row 12 N/A: companion row 12 writes the unconfirmed-retention tests (tests/agent/test_http_lifecycle.py) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-133600 | 20261126-133051 | Fast gates pass (ruff/format/mypy/lint-imports/bandit -ll/check_module_size/check_docstrings); launcher records= mypy call-arg error from row 03 resolved. Allowed red (Failure Log): 45 testmon failures all pin removed dicts (test_http_lifecycle.py row 12, test_http_lifecycle_integration.py row 14, test_lifecycle.py row 11, test_startup_mcp_lifecycle.py amended 22, test_http_lifecycle_warning.py amended 23). Full-suite run at end of batch End-of-batch full-suite run: 15103 passed, 5 skipped; coverage xml + diff-cover --compare-branch=master --fail-under=90: 93% (99 new lines, 6 missing). Allowed-red set fully retired |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Docs rows 19-23 N/A: docs covered by rows 19-23 |

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