## Goal

Cover the MDQ dry-run path: no mutation under a preview call, authorization still enforced, and
planned counts equal to the executed counts under unchanged inputs.

## Scope
**Release unit**: preview path

- A new test module under `tests/mcp_servers/mdq/` with three groups: no-op assertions,
  authorization in preview, and preview/execution parity.

## Assumptions

- The scratch database is created under `tmp_path`, never against `/opt/llm/`.
- The no-op assertions read `index_state` and the document rows through a separate connection, so
  the test does not depend on the service's own transaction.
- Parity is asserted only with the filesystem and index state unchanged between the preview and the
  subsequent execution, per the plan's risk mitigation.

## Design decisions

- The no-op group asserts absence of mutation by comparing state before and after the preview call,
  rather than by patching the writer away: patching would pass even if the preview path reached the
  writer.
- The dedup assertion is that no durable dedup row is created for a preview call, matching the
  dispatcher preview branch (`scripts/mcp_servers/dispatch.py`, 432-449).

## Alternatives considered

- Extending `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py` with preview cases: rejected,
  that file pins execution behavior and its fixtures assume a write path; a separate module keeps
  the no-op contract readable and keeps the parity cases together.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_dry_run.py` (new)

### Procedure
1. Reuse the fixture shape of `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py` (the
   `MdqService(db_path=...)` fixture with `_allowed_dirs` set to `tmp_path`, lines 39-44).
2. No-op group: run a preview call and assert no `index_state` change, no row deletion, no dedup
   row, and `side_effect_applied=False` with `execution_mode="preview"`.
3. Authorization group: a path outside `allowed_dirs` is denied in preview before any decision
   output.
4. Parity group: run the decision, then execute against the same unchanged state, and compare the
   planned counts with the executed counters.

### Method

- The parity group covers a directory case (multiple discovered files) and a large path list, so the
  counts describe files rather than requested paths, matching the mdqmcp003 counter units.
- The dispatch-level case uses the TestClient fixture so the autouse preview-capability seam in
  `tests/mcp_servers/conftest.py` (66-94) resolves `dry_run` as `preview`.

### Details

- Assert the action labels from the decision (`add`, `update`, `delete`, `skip`, `warning`,
  `failure`) against the planned model `PlannedOutcomeMetadata`, and the executed counters against
  `IndexPathsMetadata` and `RefreshSummary`.
- The test names the planned counts as planned, so a failure message distinguishes a preview count
  from an executed count.

## Compatibility considerations

- The module is new and imports only the mdq service, models, and the shared test fixtures, so no
  existing test is affected.

## Security considerations

- The authorization group is the security guard for the preview path: a preview must not report a
  decision for a path the caller cannot access.

## Rollback considerations

- Delete the new test file; nothing else depends on it.

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_dry_run.py tests/mcp_servers/mdq/test_mdq_incremental_refresh.py tests/mcp_servers/mdq/test_index_delete.py tests/mcp_servers/mdq/test_mdq_service.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- AC-2 and AC-3 pass for both write tools, including the directory and large-path-list cases.

## Out of Scope

- The decision split itself: row 3.
- The approval-risk tests: rows 11 and 12.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | This row is the test change |
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
- **Requirement ID**: REQ-004, REQ-005, REQ-007
- **Source issue**: `issues/20261119-142129_mdqmcp007_mdq-approval-dry-run.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-173835_mdqmcp007_mdq-approval-dry-run.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-043728
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_dry_run.py`
