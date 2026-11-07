## Goal

- Add the no-migration policy statement to the DB-recreation procedure (section 11) of `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` and make the archive-before-remove order explicit (REQ-009 / AC-009).

## Scope
**Release unit**: N/A: not part of a release unit (documentation row, Plan Phase 4)

## Assumptions

- Section 11 ("## 11. DB Recreation Procedure", line 111 region) already exists with archive → delete → recreate steps; the policy sentence must be added, not the procedure invented (Plan row evidence).
- Plan overlap (`tools/check_plan_target_overlaps.py` candidate): this file is also targeted by plan compatrm004 — judged compatible: this Plan runs first and 004 layers onto its result.

## Design decisions

- One policy sentence at the head of section 11: databases that do not match the current schema are never migrated, stamped, or rewritten — they are archived, then removed, then recreated from the current schema (REQ-004 wording family).

## Alternatives considered

- N/A: single-section addition dictated by REQ-009.

## Implementation
### Target file
`docs/41_db/db_07_api_and_operations-recovery-and-reference.md`

### Procedure
1. After Plan Phases 1-3 land, edit section 11 (Phase 4).

### Method
- At section 11's opening paragraph ("Schema changes require DB recreation — a migration feature does not exist."), extend: automatic migration and version stamping are not supported; a database carrying `schema_migrations` or `workflow_schema_version` is a legacy database and must be archived (step 1) before removal (step 2), never repaired in place; also update section 11a's "does not match → recreated, not migrated" paragraph (line 147 region) to drop registered-step language if any remains after Phases 1-3.

### Details
- Keep the existing steps 1-3 commands (`rotate_all_dbs()`, path keys, `create_schema()`) unchanged.

## Compatibility considerations

- N/A: docs-only.

## Security considerations

- N/A: docs-only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py docs/41_db/db_07_api_and_operations-recovery-and-reference.md`; `uv run python tools/check_docs_content_policy.py`; `uv run python tools/check_docs_consistency.py --domain db` (routing.md Tools).

## Completion criteria

- Section 11 states the no-migration policy and archive-before-remove order unambiguously (AC-009).

## Out of Scope

- Other operations text in db_07 — unchanged.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the no-migration policy sentence and archive-before-remove ordering to section 11 (Plan Phase 4) | Completed | — | 20261107-131732 | Docs row: no release unit §11 policy sentence + §11a snippet/baseline reworded to gate semantics (required tables/columns, marker refusal, unstamped refusal) |
| 2 | Run the docs checkers named in the Validation plan | Completed | — | 20261107-131732 | all four checkers exit 0 |

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
- **Related target files**: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`