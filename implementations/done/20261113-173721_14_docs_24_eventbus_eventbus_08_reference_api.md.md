## Goal
Regenerate the guarded reference-API block so the `sweep_orphans`/`promote_single` signatures and the `RequeueResult` row match the post-change source (REQ-006 / AC-6).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Verified 2026-11-13: the guarded block (lines 103-110 region) currently shows `def sweep_orphans(db, deadletter_dir, max_retry) -> int`, `def promote_single(db, deadletter_dir, event_id, consumer_failure_count) -> bool`, and the `RequeueResult` class row; all are generated from `scripts/eventbus/` source, so this file is never hand-edited.
- This document is shared with rmcompat007 (overlaps report): per the Plan Assumptions judgment, rmcompat005 runs first and this regeneration is re-run once after rmcompat007's code rows are applied.

## Design decisions
- Regeneration via the generator tool rather than targeted text edits: the whole block is a generated artifact, and any hand edit would drift from the generator output (`--check` would fail on the next cycle).

## Alternatives considered
- Hand-editing only the two signature rows: rejected — the generator owns the block and would silently disagree with hand edits.

## Implementation
### Target file
`docs/24_eventbus/eventbus_08_reference_api.md`

### Procedure
1. Run `uv run python tools/generate_reference_table.py --type eventbus` after rows 01-08 have been executed (the two signatures change with row 01 `dlq.py`; the `RequeueResult` row is affected by row 04 `dlq_repo.py` only in that it must remain unchanged — see step 2).
2. Confirm the regenerated rows: `sweep_orphans` without `deadletter_dir` and `promote_single` without `deadletter_dir` are the only expected changes. The `RequeueResult` row must stay unchanged: the generator emits only the class signature line (`class RequeueResult`) and the class docstring's first line ("Typed result of a redeliver_event() call..."), and row 04's dataclass-field removal (two fields, removed when row 04 executed) left both of those intact (verification pass 2026-11-13: row 04 edits two field declarations, neither is the class signature line or the docstring; the status vocabulary, including `"already_redelivered"`, survives per REQ-003). A changed `RequeueResult` row would indicate the docstring was edited out of scope.
3. (rmcompat007 handoff) Re-run the same command after rmcompat007's code rows are applied, so the block reflects both plans' final source state.

### Method
- Generator command only; no manual edits to the guarded block.

### Details
- If the generator produces additional incidental changes in other rows, review them: they indicate generator-source drift unrelated to this plan and must be reported, not silently accepted.

## Compatibility considerations
- Generated-artifact pipeline shared with the manifest row 09; both are regenerated with the same tool invocation.

## Security considerations
N/A: generated documentation change.

## Rollback considerations
N/A: revert the commit (or re-run the generator against reverted sources).

## Validation plan
| Target | Testing strategy | Tool / command | Expected outcome |
|---|---|---|---|
| Generated drift | Generator | `uv run python tools/generate_reference_table.py --check` | No drift |
| Doc staleness | Docs | `uv run python tools/stale_detector.py docs/24_eventbus/eventbus_08_reference_api.md` | No findings |

## Completion criteria
- AC-6 for `eventbus_08`: the guarded block matches generator output for the post-change source; `--check` exits clean.

## Out of Scope
- `registry/manifests/eventbus_api.yaml` (its own procedure row 09), any hand-written prose in the file outside the guarded block (there is none).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261114-003506 | guarded block regenerated via --manifests --type eventbus in the row-09 cycle (single shared invocation per Compatibility) |
| 2 | Add or update tests per Validation plan | Completed | — | 20261114-003506 | no test changes (generated doc row) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261114-003507 | --check No drift found; stale_detector no findings; regenerated delta was exactly the two dlq.py signature rows; RequeueResult row verified unchanged (class line + docstring first line only) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261114-003515 | the target is the generated documentation itself (regenerated in step 1) |

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
- **Requirement ID**: REQ-006 / AC-6
- **Source issue**: issues/20261110-170926_rmcompat005_eventbus-dlq-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-121134_rmcompat005_eventbus-dlq-leftovers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-173721
- **Related target files**: `docs/24_eventbus/eventbus_08_reference_api.md`