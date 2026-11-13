## Goal
Regenerate `registry/manifests/eventbus_api.yaml` so it carries the new `sweep_orphans` and `promote_single` signatures (REQ-006 / AC-6).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers are from the 2026-11-13 plan revalidation; locate each passage by its quoted text and skip and report it if it is already correct.
- Verified 2026-11-13: the manifest is a generated artifact (`generate_reference_table.py`); its `scripts/eventbus/dlq.py` block contains `signature: def sweep_orphans(db, deadletter_dir, max_retry) -> int` (lines 293-294) and the `promote_single` entry; the `/nack` endpoint block is already query-parameter based with no body schema, so the Issue's "advertises a JSON body" wording does not apply to the current manifest.
- Run this document after rows 01-08 (all eventbus code changes) so one regeneration settles all entries; the file MUST NOT be hand-edited (Plan Assumptions on generated artifacts).
- `plans/20261112-122030_rmcompat007_history-comment-sweep.md` also regenerates this manifest later (judged compatible in the Plan Assumptions); its regeneration will supersede cleanly.

## Design decisions
- Regeneration-only change: every manifest delta must come from the tool reading the changed sources.

## Alternatives considered
N/A: generated artifact; hand-editing is prohibited.

## Implementation
### Target file
`registry/manifests/eventbus_api.yaml`

### Procedure
1. Run `uv run python tools/generate_reference_table.py --type eventbus` after rows 01-04, 06, 07 have been executed.
2. Confirm the delta is limited to: `sweep_orphans` signature `def sweep_orphans(db, max_retry) -> int`, `promote_single` signature `def promote_single(db, event_id, consumer_failure_count) -> bool`, and any `RequeueResult` docstring-derived summary text after row 04.

### Method
- If the tool reports drift outside that delta, stop and report (it would mean a code row changed an unlisted public surface).

### Details
- The `DlqEventRecord` summary ("...as a JSON file on disk") stays: artifact generation still writes files via the outbox worker; row 01 does not change that class.

## Compatibility considerations
- The manifest feeds `docs/24_eventbus/eventbus_08_reference_api.md` generation (row 14); regenerate both in the same cycle.

## Security considerations
N/A: generated registry data.

## Rollback considerations
N/A: revert the commit.

## Validation plan
| Target | Testing strategy | Tool / command | Expected outcome |
|---|---|---|---|
| Manifest drift | Generator | `uv run python tools/generate_reference_table.py --check` | No drift |

## Completion criteria
- AC-6 for the manifest: `--check` passes and the signatures match the post-change code.

## Out of Scope
- The `/nack` endpoint description (already correct, Assumptions); non-eventbus manifests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Related target files**: `registry/manifests/eventbus_api.yaml`
