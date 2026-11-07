## Goal

- Update `docs/41_db/db_02_architecture_and_schema-schema-reference.md` to remove the `workflow_schema_version` append-only-log and version-comparison-gate description from the workflow.sqlite schema section (REQ-009: docs describe only the current-schema policy).

## Scope
**Release unit**: N/A: not part of a release unit (documentation row, Plan Phase 4)

## Assumptions

- The schema description sentence at section 7 (line 46 region: "`workflow_schema_version` is an append-only log ... recreate the workflow database") is the exact HEAD text to replace (Plan row evidence: line 46).

## Design decisions

- Replace the version-log/version-comparison sentences with the shape-only acceptance statement plus the legacy-marker rejection behavior; keep the `task_nonce` and following paragraphs byte-identical.

## Alternatives considered

- N/A: single-section update dictated by REQ-009.

## Implementation
### Target file
`docs/41_db/db_02_architecture_and_schema-schema-reference.md`

### Procedure
1. After Plan Phases 1-3 land, edit section 7 (Phase 4).

### Method
- In the section 7 paragraph (line 46 region): delete the `workflow_schema_version` log description, the `WORKFLOW_SCHEMA_VERSION` recording/comparison sentences, and the mismatch `[FATAL]/RuntimeError` sentence; state instead that `check_workflow_schema()` and deploy pre-flight accept the exact current table/column shape and reject databases carrying `schema_migrations` or `workflow_schema_version` as legacy markers to be archived and recreated ([db_07 section 11] link kept).

### Details
- No other table sections change (the marker tables disappear from DDL per documents 08-09).

## Compatibility considerations

- N/A: docs-only; keep the existing `db_07` section 11 link.

## Security considerations

- N/A: docs-only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py docs/41_db/db_02_architecture_and_schema-schema-reference.md`; `uv run python tools/check_docs_content_policy.py`; `uv run python tools/check_docs_consistency.py --domain db` (routing.md Tools).

## Completion criteria

- The workflow schema reference describes the marker-free current shape and legacy-marker rejection, with no version-log claims (AC-009).

## Out of Scope

- Other db docs — own documents (seq 25, 27, 28).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the section 7 version-log sentences with shape-only + marker-rejection text (Plan Phase 4) | Completed | — | 20261107-131302 | Docs row: no release unit §7 version-log sentences replaced with shape-only acceptance + marker rejection |
| 2 | Run the docs checkers named in the Validation plan | Completed | — | 20261107-131302 | checkers green (db consistency warnings belong to batch 20261107-103000 file db_03_07) |

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
- **Requirement ID**: REQ-009 (documentation describes the current-schema-only policy)
- **Source issue**: issues/20261106-125142_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-061846_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-081028
- **Related target files**: `docs/41_db/db_02_architecture_and_schema-schema-reference.md`