## Goal
- Regenerate the EventBus API manifest after the symbol changes (REQ-007: generated files are regenerated, never hand-edited), reflecting the removal of `get_auth_token` (REQ-002) and the rename in REQ-003.

## Scope
**Release unit**: eventbus-api-surface

- In scope: `registry/manifests/eventbus_api.yaml`, produced by the generator. The same command also re-renders the guarded block of `docs/24_eventbus/eventbus_08_reference_api.md`, which the seq 09 document verifies.
- Depends on the seq 01, 02, and 04 documents.

## Assumptions
- The generator reads live symbols under `scripts/eventbus`, so it MUST run after the symbol changes are applied.
- The baseline is clean: `uv run python tools/generate_reference_table.py --type eventbus --check` reported no drift before this Plan (verified in Step 3a).
- Restricting the run with `--type eventbus` keeps unrelated manifests out of the diff.

## Design decisions
- Run the generator for the eventbus domain only and review the diff instead of editing the manifest.

## Alternatives considered
- Hand-edit the manifest entries: rejected, the constraint forbids editing generated files by hand.
- Run the generator for every domain: rejected, it could pull unrelated drift into this change.

## Implementation
### Target file
`registry/manifests/eventbus_api.yaml`

### Procedure
1. Confirm the seq 01, 02, and 04 changes are applied.
2. Run `uv run python tools/generate_reference_table.py --type eventbus --manifests`.
3. Run `uv run python tools/generate_reference_table.py --type eventbus --check`; it MUST exit 0.
4. Run `git diff --stat`; only this manifest and the `eventbus_08_reference_api.md` guarded block may differ.

### Method
- Expected manifest diff: the entry named `attach_auth_middleware` becomes `attach_request_id_middleware`, and the entry named `get_auth_token` disappears.

### Details
- If any other file changes, stop and report: it is generator drift outside this Plan and needs its own issue.
- Do not edit the generated file after the run.

## Compatibility considerations
N/A: derived artifact.

## Security considerations
N/A: derived artifact.

## Rollback considerations
- Revert with the release unit; the generator reproduces the file from the reverted source.

## Validation plan
- `uv run python tools/generate_reference_table.py --check` exits 0 (all domains).
- `uv run python tools/check_docs_consistency.py --domain eventbus`.

## Completion criteria
- The manifest matches live sources and holds no `get_auth_token` or `attach_auth_middleware` entry for EventBus.

## Out of Scope
- Hand edits and any other manifest.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Run the generator for the eventbus domain | Pending | — | — | |
| 2 | Run the drift check and review the diff | Pending | — | — | |

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
- **Related target files**: `registry/manifests/eventbus_api.yaml`
