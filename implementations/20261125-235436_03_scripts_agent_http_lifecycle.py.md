## Goal

Replace the three parallel tracking dicts with the `ManagedProcessRecord` registry, re-express startup-failure retention on the record, and make `restart()` refuse to start a replacement over a live process (REQ-001, REQ-002, REQ-005, REQ-010).

## Scope
**Release unit**: R3-ownership

## Assumptions
- Startup-failure retention is already implemented (`_raise_startup_failure_unconfirmed`, verified in the Plan's Step 2); this row re-expresses it on the record, not re-implements it (REQ-002 regression scope).
- `RestartBlockedError` (new) is declared by row 08 (`scripts/agent/http_lifecycle_errors.py`); this document uses it as a sibling-declared name.

## Design decisions
- One record per key: `self._records: dict[str, ManagedProcessRecord]` replaces `_http_procs` (`:87`), `_http_pgids` (`:88`), `_failed_start_procs` (`:91`); every pop site (`:162-165`, `:174-175`, `:399-400`, `:413`) becomes a record release gated on confirmed exit.
- `restart()` on an unconfirmed outcome retains the record, sets the server state to `EXIT_UNCONFIRMED` (new), and raises `RestartBlockedError` (new) without starting a replacement (Plan Design, AC-2).

## Alternatives considered
- Keeping the dicts and gating each pop individually — rejected per Plan Design: path-dependent popping is the defect itself.

## Implementation
### Target file
`scripts/agent/http_lifecycle.py`

### Procedure
Swap the three dicts for the record registry `_records` (new) (`dict[str, ManagedProcessRecord]`); rewire `_clear_server_tracking_data` (`:162-165`), `remove_process_entry` (`:174-175`), `_build_snapshot` (`:189-193`), the startup-failure path (`:254-281`), `start()` re-termination (`:318`, `:332-341`, `:363-394`), and `restart()` (`:396-414`) to the record; add the refusal branch in `restart()`.

### Method
Mechanical dict-to-record substitution plus one new refusal branch; the terminator and stderr-manager APIs are unchanged (Reference Files).

### Details
- `restart()` currently clears tracking at `:398`, pops at `:399-400`, logs only on unconfirmed exit (`:406-412`), pops pgid at `:413`, then starts at `:414`; the new branch raises after the unconfirmed log and skips `start()`.
- `_build_snapshot` returns None once the entry is popped (`:191-193`); with retained records it must build the snapshot from the record, including the outcome field added by row 09.
- `remove_process_entry` (`:174-175`) loses its pre-termination callers (row 04); keep it only as the post-confirmation release helper or fold it into the record release, per row 04's procedure.

## Compatibility considerations
- `ProcessInfoSnapshot` gains the outcome field in row 09 (defaulted, 19 importers unaffected); `_build_snapshot` sets it.
- The launcher and stderr-manager receive the record instead of dict lookups; their public signatures change only in rows 02/05.

## Security considerations
- N/A: no new signal or subprocess behavior beyond the existing termination path.

## Rollback considerations
- Revert the commit; the record module (row 02) can stay unused without breaking callers.

## Validation plan
- Unit: record ownership, restart refusal, port-conflict prevention — `uv run pytest tests/agent/test_http_lifecycle.py`.
- Integration: retained-record visibility end to end — `uv run pytest tests/agent/test_http_lifecycle_integration.py`.
- Regression: `uv run pytest tests/agent/test_http_lifecycle_process_terminator.py` (unchanged green, REQ-002).

## Completion criteria
- No path pops a record before its exit is confirmed; `restart()` raises `RestartBlockedError` (new) on an unconfirmed old exit and starts no second live process (AC-2); the startup-failure regression tests stay green.

## Out of Scope
- Coordinator call-path changes (row 04), launcher PGID handling (row 05), the error class definitions (row 08), the snapshot field (row 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Companion rows 12, 14 |
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
- **Requirement ID**: REQ-001 (record registry), REQ-002 (confirmed-exit release), REQ-005 (restart confirmation), REQ-010 (repeated shutdown)
- **Source issue**: issues/20261119-145305_cliplc007_mcp-process-ownership.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-232847_cliplc007_mcp-process-ownership.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-235436
- **Related target files**: `scripts/agent/http_lifecycle.py`
