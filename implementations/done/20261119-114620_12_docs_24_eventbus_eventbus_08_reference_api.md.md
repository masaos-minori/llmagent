## Goal
- Confirm the guarded block of the EventBus reference guide is re-rendered from the regenerated manifest, with no `schema_version` row (REQ-008: generated blocks are never hand-edited; REQ-006: the removed accessor leaves the block).

## Scope
**Release unit**: eventbus-supervision-and-cleanup

- In scope: the `AUTO-GENERATED` block of `docs/24_eventbus/eventbus_08_reference_api.md`. The seq 11 command already re-renders it as a side effect; this document verifies it and re-runs the generator only if the block still differs.
- Depends on the seq 11 document.

## Assumptions
- The generator writes only between the guard comments, and re-running it is idempotent (verified in Step 3a from the guard constants of `tools/generate_reference_table.py`).

## Design decisions
- Never edit the block by hand; correct drift only by re-running the generator.

## Alternatives considered
N/A: generated block.

## Implementation
### Target file
`docs/24_eventbus/eventbus_08_reference_api.md`

### Procedure
1. After the seq 11 run, read the guarded block and confirm there is no row for `schema_version`.
2. If the block still differs, run `uv run python tools/generate_reference_table.py --manifests` again and re-check.
3. Run `uv run python tools/generate_reference_table.py --check`; it MUST exit 0.

### Method
- Compare the block against `registry/manifests/eventbus_api.yaml`; the table is derived from it.

### Details
- Text outside the guard comments MUST be unchanged.

## Compatibility considerations
N/A: derived artifact.

## Security considerations
N/A: derived artifact.

## Rollback considerations
- Revert with the release unit.

## Validation plan
- `uv run python tools/generate_reference_table.py --check`; `check_docs_quality.py`, `check_docs_structure.py docs/24_eventbus/eventbus_08_reference_api.md`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py`, `check_docs_consistency.py --domain eventbus`.

## Completion criteria
- The block matches the committed manifest, lists no `schema_version`, and every checker passes.

## Out of Scope
- Hand edits and any text outside the guard comments.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify the regenerated block, re-run the generator only if it differs | Completed | 20261119-120426 | 20261119-120426 | Changed: docs/24_eventbus/eventbus_08_reference_api.md (guarded block re-rendered by the seq 11 run; only the schema_version row removed; text outside the guard comments unchanged) |
| 2 | Run the drift check and the documentation checkers named in `routing.md` Tools | Completed | 20261119-120426 | 20261119-120426 | Drift check and docs checkers pass: quality, structure, content-policy strict, japanese, consistency eventbus |

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
- **Requirement ID**: `REQ-008` (regenerate generated artifacts), `REQ-006` (removed accessor)
- **Source issue**: issues/20261117-123017_adrchk017_eventbus-task-supervision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-113711_adrchk017_eventbus-task-supervision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-114620
- **Related target files**: `docs/24_eventbus/eventbus_08_reference_api.md`