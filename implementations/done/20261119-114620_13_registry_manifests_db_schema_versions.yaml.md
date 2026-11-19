## Goal
- Confirm the schema-version manifest carries the new `content_hash` after the `schema.sql` comment edit (REQ-008: generated files are regenerated, never hand-edited; REQ-005: the comment edit changes the hash).

## Scope
**Release unit**: eventbus-supervision-and-cleanup

- In scope: `registry/manifests/db_schema_versions.yaml`. The seq 11 command already rewrites it as a side effect; this document verifies it and re-runs the generator only if it differs.
- Depends on the seq 06 and seq 11 documents.

## Assumptions
- `content_hash` is the SHA-256 of the whole `scripts/eventbus/schema.sql` text (verified in Step 3a from `tools/generate_reference_table.py`), so a comment edit changes it even though the structural fingerprint does not.
- The entry's `version` stays `unversioned`; only the hash line is expected to change.

## Design decisions
- Never edit the manifest by hand; correct drift only by re-running the generator.

## Alternatives considered
N/A: generated file.

## Implementation
### Target file
`registry/manifests/db_schema_versions.yaml`

### Procedure
1. After the seq 11 run, check that `git diff registry/manifests/db_schema_versions.yaml` shows only the `content_hash` line of the `eventbus` entry.
2. If the hash still differs from the live file, re-run `uv run python tools/generate_reference_table.py --manifests`.
3. Run `uv run python tools/generate_reference_table.py --check`; it MUST exit 0.

### Method
- Compare against `sha256sum scripts/eventbus/schema.sql`.

### Details
- Any other changed line means unrelated generator drift: stop and report.

## Compatibility considerations
N/A: derived artifact.

## Security considerations
N/A: derived artifact.

## Rollback considerations
- Revert with the release unit.

## Validation plan
- `uv run python tools/generate_reference_table.py --check`; `uv run python tools/check_db_separation.py`.

## Completion criteria
- The `content_hash` equals the SHA-256 of `schema.sql` and `--check` exits 0.

## Out of Scope
- Hand edits and any other manifest entry.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify the hash change, re-run the generator only if it differs | Completed | 20261119-120426 | 20261119-120426 | Changed: registry/manifests/db_schema_versions.yaml (generated; only the eventbus content_hash line, now equal to the sha256 of schema.sql) |
| 2 | Run the drift check | Completed | 20261119-120426 | 20261119-120426 | generate_reference_table.py --check: no drift; check_db_separation: no violations |

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
- **Requirement ID**: `REQ-008` (regenerate generated artifacts), `REQ-005` (comment edit changes the hash)
- **Source issue**: issues/20261117-123017_adrchk017_eventbus-task-supervision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-113711_adrchk017_eventbus-task-supervision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-114620
- **Related target files**: `registry/manifests/db_schema_versions.yaml`