## Goal

Honor `dry_run` on the two MDQ write request models at the service layer and return the planned
metadata for a preview call, so the service is the place that chooses between the decision-only
path and the write path.

## Scope
**Release unit**: preview path

- `index_paths()` (lines 281-292) and `refresh_index()` (lines 295-307): the branch that selects
  the decision-only path, and the metadata returned for a preview call.

## Assumptions

- The index lock and `_validate_paths()` stay on both paths: a preview still serializes against a
  running index and still rejects a path outside `allowed_dirs`.
- The preview text names its counts as planned, not executed, so a reader cannot mistake a
  preview for a completed write.

## Design decisions

- The branch is at the service layer, not in the handler: the handler only passes the argument
  through, and the service owns the decision/write selection.
- The planned metadata is returned as the same tuple shape the callers already consume, so the
  audit detail builder keeps reading metadata keys from one place.

## Alternatives considered

- Returning the executed metadata with a `planned` flag: rejected, the executed counters would
  carry a meaning that depends on the mode.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_service.py`

### Procedure
1. In `index_paths()`, when `req.dry_run` is true, run the decision-only path from
   `scripts/mcp_servers/mdq/indexer.py` and return `PlannedOutcomeMetadata` instead of the executed
   `IndexPathsMetadata`.
2. In `refresh_index()`, the same branch: decision-only path for a preview call, executed
   `RefreshSummary` for an execution call.
3. Build the preview text from the planned counts and the representative paths.

### Method

- The existing execution branches are unchanged; the new branch calls the decision path and never
  reaches the writer, so no transaction is opened here.
- `_format_refresh_summary()` keeps its current behavior for execution; the preview formatting is a
  separate small helper that names each count as planned.

### Details

- Return annotations widen to the planned model for a preview call; callers that read specific
  keys are unaffected because the planned model is additive.
- The service does not report `execution_mode` or `side_effect_applied`: those come from the
  dispatcher envelope, and the preview branch is what makes `side_effect_applied` false.

- The test this change must keep passing (`tests/mcp_servers/mdq/test_mdq_service.py`) is not a Plan
  row, so it is not a companion; it is a regression guard run by the Validation plan.

## Compatibility considerations

- Cross-plan overlap: this file is also a target of mdqmcp001, mdqmcp003, and mdqmcp004; this
  document adds only the mode branch and consumes their counter and status vocabularies.
- `tests/mcp_servers/mdq/test_mdq_index_serialization.py` pins the lock behavior, which stays on
  both paths.

## Security considerations

- Authorization and the path jail are enforced before any decision output, so a preview cannot
  leak a decision for a path the caller is not allowed to read.

## Rollback considerations

- Revert the commit; the branch is additive and no persisted state depends on it.

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_service.py tests/mcp_servers/mdq/test_mdq_dry_run.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- A preview call reports planned counts with `side_effect_applied=False` (AC-2), and the planned
  counts equal the executed counts under unchanged inputs (AC-3).

## Out of Scope

- The decision logic itself: row 3.
- The display formatting of the preview: row 6.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | New dry-run tests are row 10 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docs row 16 names the planned fields |

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
- **Related target files**: `scripts/mcp_servers/mdq/mdq_service.py`
