## Goal

Add `dry_run` to the two MDQ write request models and add the planned-outcome metadata model that
carries the preview counts, so a preview call has a typed contract and a place to report what it
decided without having written anything.

## Scope
**Release unit**: preview path

- `IndexPathsRequest` and `RefreshIndexRequest`: one new optional field each.
- One new metadata model for the preview outcome, consumed by the service layer and the audit
  detail builder.

## Assumptions

- `dry_run` defaults to `False`, so existing callers and the handler pass-through keep the
  execution behavior when the argument is absent.
- The planned counts reuse the mdqmcp003 per-file DTO statuses and reason codes; add and update
  are action labels derived from the decision, not new status vocabulary.
- Field names follow the UNK-05 plan default: the mdqmcp003 counters with a planned_ prefix.
  They are not published as a public shape until the shared-contract owner confirms them.

## Design decisions

- The preview metadata is a separate model, not extra fields on `IndexPathsMetadata`: executed
  counts and planned counts describe different things and must not be conflated in one record.
- The model is a `TypedDict` like `IndexPathsMetadata` (line 389), because the audit detail
  builder consumes metadata as a plain mapping.

## Alternatives considered

- Reusing `RefreshSummary` with a flag that says the counts were planned: rejected, the summary
  has no delete, warning, or representative-path fields and a flag would make the same counters
  mean two things.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_models.py`

### Procedure
1. Add `dry_run: bool = False` to `IndexPathsRequest` (line 215) and `RefreshIndexRequest`
   (line 221).
2. Add `PlannedOutcomeMetadata` (new) as a `TypedDict` after `IndexPathsMetadata`.

### Method

- Request models stay plain Pydantic models with no validation change; the field is read by the
  service layer to choose the decision-only path.
- `PlannedOutcomeMetadata` (new) is import-only: no behavior lives in this module.

### Details

- `PlannedOutcomeMetadata` (new) fields: planned_path_count, planned_discovered_count,
  planned_add_count, planned_update_count, planned_delete_count, planned_skip_count,
  planned_warning_count, planned_failed_count, representative_paths (`list[str]`).
- representative_paths holds the paths the display layer can show without the full argument
  dump; the common root is derived by the formatter, not stored here.
- The shared execution-mode fields (`execution_mode`, `side_effect_applied`) are not added to this
  model: they already come from the dispatcher envelope.

## Compatibility considerations

- `IndexPathsMetadata` and `RefreshSummary` keep their current fields and meanings; the audit
  detail builder that reads metadata keys is unaffected by an additive model.
- `tests/mcp_servers/mdq/test_mdq_metadata_consistency.py` reads existing metadata keys and does
  not assert an exact key set, so an additive model does not break it.

## Security considerations

- representative_paths carries path strings that authorization already accepted; no secret
  fields are added, and masking stays in the display layer.

## Rollback considerations

- Revert the commit; the model is additive and no persisted state depends on it.

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_service.py tests/mcp_servers/mdq/test_mdq_dry_run.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- A preview call returns the planned model with `side_effect_applied=False` (AC-2, AC-3).

## Out of Scope

- The decision logic that fills the counts: `scripts/mcp_servers/mdq/indexer.py`.
- The public input schema property: `scripts/mcp_servers/mdq/mdq_tools.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by row 10 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docs row 16 names the planned-count fields |

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
- **Requirement ID**: REQ-003, REQ-005
- **Source issue**: `issues/20261119-142129_mdqmcp007_mdq-approval-dry-run.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-173835_mdqmcp007_mdq-approval-dry-run.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-043728
- **Related target files**: `scripts/mcp_servers/mdq/mdq_models.py`
