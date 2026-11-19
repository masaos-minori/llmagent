## Goal
- Regenerate the EventBus API manifest after the `db_tools` removal (REQ-008: generated files are regenerated, never hand-edited; REQ-006: the removed accessor leaves the manifest).

## Scope
**Release unit**: eventbus-supervision-and-cleanup

- In scope: `registry/manifests/eventbus_api.yaml`, produced by the generator. The same command rewrites the guarded block of `docs/24_eventbus/eventbus_08_reference_api.md` and the content hash in `registry/manifests/db_schema_versions.yaml`, which the seq 12 and seq 13 documents verify.
- Depends on the seq 05 and seq 06 documents (and the seq 01 to 04 changes for a clean tree).

## Assumptions
- The generator reads live symbols under `scripts/eventbus`; it MUST run after the code changes are applied.
- No new public top-level symbol is added by this Plan (the new helpers are private), so the expected manifest change is the removal of the `schema_version` entry (verified in Step 3a).
- A previous run of the generator rewrote other manifests with identical content, so only the files that really differ show in `git status`.

## Design decisions
- Run the generator and review the diff instead of editing any generated file.

## Alternatives considered
- Hand-edit the manifest: rejected, generated files are never hand-edited.

## Implementation
### Target file
`registry/manifests/eventbus_api.yaml`

### Procedure
1. Confirm the seq 01 to 06 changes are applied.
2. Run `uv run python tools/generate_reference_table.py --manifests`.
3. Run `uv run python tools/generate_reference_table.py --check`; it MUST exit 0.
4. Run `git status --short registry docs`; only this manifest, `registry/manifests/db_schema_versions.yaml`, and `docs/24_eventbus/eventbus_08_reference_api.md` may differ.

### Method
- Expected diff in this file: the entry named `schema_version` disappears.

### Details
- If any other file changes, stop and report: it is generator drift outside this Plan.
- Do not edit the generated file after the run.

## Compatibility considerations
N/A: derived artifact.

## Security considerations
N/A: derived artifact.

## Rollback considerations
- Revert with the release unit; the generator reproduces the file from the reverted source.

## Validation plan
- `uv run python tools/generate_reference_table.py --check` exits 0; `uv run python tools/check_docs_consistency.py --domain eventbus`.

## Completion criteria
- The manifest matches live sources and holds no `schema_version` entry for `db_tools`.

## Out of Scope
- Hand edits and any other manifest.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Run the generator | Completed | 20261119-120404 | 20261119-120426 | Step 2 stale check clean; Step 3a: seq 01-06 applied; drift expected (db_tools accessor and schema.sql content hash); manifests clean at baseline Changed: registry/manifests/eventbus_api.yaml (generated; schema_version entry removed). Only the three expected files changed; memory_api.yaml rewritten with identical content |
| 2 | Run the drift check and review the diff | Completed | 20261119-120426 | 20261119-120426 | generate_reference_table.py --check: no drift; drift before the run was exactly db_schema_versions.yaml and eventbus_api.yaml |

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
- **Related target files**: `registry/manifests/eventbus_api.yaml`