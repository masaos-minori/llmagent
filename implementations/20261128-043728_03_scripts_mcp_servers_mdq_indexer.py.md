## Goal

Separate the per-file decision from the write in the refresh and index paths, so a preview call
runs discovery, authorization, and the decision and reports planned counts without mutating the
database.

## Scope
**Release unit**: preview path

- The decision functions in `scripts/mcp_servers/mdq/indexer.py` and the two write paths that
  currently decide and mutate in the same call.
- The planned-count tally for a preview run, using the existing tally shape.

## Assumptions

- The preview path reads `index_state` for the comparison, which is a read-only operation and
  does not need the mdqmcp005 transaction owner; it never opens a write transaction.
- Add and update are action labels derived from the decision (file absent from `index_state`
  versus present with a changed mtime), not new DTO statuses.
- Discovery is reused from `scripts/mcp_servers/mdq/index_scan.py` `iter_indexable_files()`, which
  holds no database access, so no change is needed there.

## Design decisions

- Decision and write become two calls with the decision as the only shared part: the write path
  calls the decision then mutates, the preview path calls the decision only. Alternative
  considered — run the writer with a rollback; rejected, a rollback is still a write transaction
  and the mdqmcp005 design makes transaction ownership explicit.
- The planned counts come from the same tally the execution path uses, so parity is a property of
  the shared decision, not of a second counting implementation.

## Alternatives considered

- A separate preview module that re-implements the scan and comparison: rejected, it would create
  a second decision source that can diverge from execution.

## Implementation
### Target file
`scripts/mcp_servers/mdq/indexer.py`

### Procedure
1. Extract the per-file decision from `_refresh_changed_file()` (line 304) into a decision
   function that returns the action label for one file from `index_state` and the file's current
   mtime, and performs no write.
2. Keep the write side as a separate call that runs only when the caller is executing, and have
   `_refresh_changed_file()` call the decision then the write.
3. Split `_detect_deleted_files()` (line 258): compute the planned delete set from the current
   state and the discovered files, and delete rows only in the execution branch.
4. Add the preview entry point that runs discovery, `authorize_path()`, and the decision for each
   path and fills the planned counts.

### Method

- The decision function is the single source of the action label for both modes; the write
  functions keep their current transaction behavior from the mdqmcp005 pass.
- The preview entry point takes the same service and connection the execution path uses but does
  not commit; it must not call the writer.

### Details

- Action labels: `add` when the file is absent from `index_state`, `update` when present with a
  changed mtime, `skip` when the recorded mtime matches, `delete` when a recorded file is no
  longer discovered, `warning` for a parser warning record, `failure` for a per-file failure.
- The preview path must not acquire a dedup row: the dispatcher preview branch
  (`scripts/mcp_servers/dispatch.py`, 432-449) already skips dedup for a preview, so the mdq path
  must not create durable state on its own.
- Authorization runs in preview exactly as in execution (`scripts/mcp_servers/mdq/auth.py`
  `authorize_path()`); a denial stops the run before any decision output.
- The tests this change must keep passing (`tests/mcp_servers/mdq/test_mdq_incremental_refresh.py`
  and `tests/mcp_servers/mdq/test_index_delete.py`) are not Plan rows, so they are not companions; they
  are regression guards run by the Validation plan.

## Compatibility considerations

- `RefreshSummary` and the executed metadata keep their meanings; the planned counts are reported
  through the new metadata model (row 2), so existing consumers of executed counters are
  unaffected.
- Cross-plan overlap: this file is also a target of mdqmcp003, mdqmcp004, and mdqmcp005; this
  document changes only the decision/write split and consumes the vocabularies those plans define.

## Security considerations

- Preview performs no mutation, so an unauthorized path cannot change indexed state; the denial
  path is the same one execution uses.

## Rollback considerations

- Revert the commit; the split is internal to the module and no persisted state depends on it.

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_dry_run.py tests/mcp_servers/mdq/test_mdq_incremental_refresh.py tests/mcp_servers/mdq/test_index_delete.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- A preview run performs no write, no `index_state` change, and no row deletion, and its planned
  counts equal the executed counts under an unchanged filesystem and index state (AC-2, AC-3).

## Out of Scope

- The request model field and the metadata model: rows 2.
- The handler pass-through: row 5.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | New dry-run tests are row 10 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docs row 16 records the contract |

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
- **Requirement ID**: REQ-004, REQ-005
- **Source issue**: `issues/20261119-142129_mdqmcp007_mdq-approval-dry-run.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-173835_mdqmcp007_mdq-approval-dry-run.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-043728
- **Related target files**: `scripts/mcp_servers/mdq/indexer.py`
