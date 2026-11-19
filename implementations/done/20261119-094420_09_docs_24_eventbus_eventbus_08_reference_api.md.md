## Goal
- Confirm the guarded block of the EventBus reference guide is re-rendered from the regenerated manifest (REQ-007: generated blocks are never hand-edited), with no `get_auth_token` row (REQ-002) and the renamed function row (REQ-003).

## Scope
**Release unit**: eventbus-api-surface

- In scope: the `AUTO-GENERATED` block of `docs/24_eventbus/eventbus_08_reference_api.md`. The seq 08 command already re-renders it as a side effect; this document verifies and, only if the block still differs, re-runs the generator.
- Depends on the seq 08 document.

## Assumptions
- The generator writes only between the guard comments and never touches text outside them (verified in Step 3a from the guard constants of `tools/generate_reference_table.py`).
- Re-running the generator is idempotent.

## Design decisions
- Never edit the block by hand; correct drift only by re-running the generator.

## Alternatives considered
N/A: generated block.

## Implementation
### Target file
`docs/24_eventbus/eventbus_08_reference_api.md`

### Procedure
1. After the seq 08 run, read the guarded block and confirm there is no row for `get_auth_token` and the former `attach_auth_middleware` row is named `attach_request_id_middleware`.
2. If the block still differs, run `uv run python tools/generate_reference_table.py --type eventbus --manifests` again and re-check.
3. Run `uv run python tools/generate_reference_table.py --type eventbus --check`; it MUST exit 0.

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
- `uv run python tools/generate_reference_table.py --check`.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py`.
- `uv run python tools/check_docs_consistency.py --domain eventbus`.

## Completion criteria
- The block matches the committed manifest, lists no `get_auth_token`, and names the renamed function; every checker above passes.

## Out of Scope
- Hand edits and any text outside the guard comments.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify the regenerated block, re-run the generator only if it differs | Completed | 20261119-100634 | 20261119-100634 | Changed: docs/24_eventbus/eventbus_08_reference_api.md (guarded block re-rendered by the seq 08 run; text outside the guard comments unchanged) |
| 2 | Run the drift check and the documentation checkers named in `routing.md` Tools | Completed | 20261119-100634 | 20261119-100634 | Drift check and docs checkers pass: quality, structure, content-policy strict, japanese, consistency eventbus |

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
- **Requirement ID**: `REQ-007` (regenerate generated artifacts), `REQ-002` (removed helper), `REQ-003` (renamed function)
- **Source issue**: issues/20261117-123002_adrchk002_eventbus-authz-model.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-092411_adrchk002_eventbus-authz-model.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-094420
- **Related target files**: `docs/24_eventbus/eventbus_08_reference_api.md`