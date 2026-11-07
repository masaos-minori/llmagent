## Goal

- Update `docs/41_db/db_01_architecture_and_schema-overview-and-config.md` so the DB overview describes the current-schema-only lifecycle (no migration or ledger statements), matching post-cutover behavior (REQ-009: docs describe only the current-schema and manual archive-and-recreate policy).

## Scope
**Release unit**: N/A: not part of a release unit (documentation row, Plan Phase 4)

## Assumptions

- At HEAD the overview carries no migration/ledger sentence (lines 17-20 are document-guide links; lifecycle sentences are §2 (line 30) and §3 (line 40)) — the row is a lifecycle-description alignment update, not a removal (Plan row, re-verified 2026-11-07).
- Plan overlap (`tools/check_plan_target_overlaps.py` candidate): this file is also targeted by plan compatrm003 — judged compatible: this Plan runs first and 003 layers onto its result.

## Design decisions

- Add one lifecycle sentence per section (§2 DB layer structure, §3 `DbConfig` file-creation paragraph); no structural rewrite (docs_01 stays the overview).

## Alternatives considered

- N/A: single-file overview alignment dictated by REQ-009.

## Implementation
### Target file
`docs/41_db/db_01_architecture_and_schema-overview-and-config.md`

### Procedure
1. After Plan Phases 1-3 land, edit §2 and §3 (Phase 4).

### Method
- §2 (line 30 paragraph, "idempotent DDL creation (`create_schema.py`)"): state that workflow and eventbus databases are validated against the current schema on startup/health check and incompatible (legacy-marker or version-mismatched) databases are refused for manual archive-and-recreate — no migration.
- §3 (line 40 paragraph, "DB files themselves are created on first open"): align the creation statement with the no-migration policy (creation uses current canonical DDL only).

### Details
- Keep existing wording about the four DB files, table definitions in `db_02`, and WAL rationale unchanged.

## Compatibility considerations

- N/A: docs-only; link targets (`db_02`, `db_07`) unchanged.

## Security considerations

- N/A: docs-only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py docs/41_db/db_01_architecture_and_schema-overview-and-config.md`; `uv run python tools/check_docs_content_policy.py`; `uv run python tools/check_docs_consistency.py --domain db` (routing.md Tools).

## Completion criteria

- The overview's lifecycle statements match post-cutover behavior with zero migration/ledger claims (AC-009).

## Out of Scope

- Repository-wide `dbmig001` wording sweep — plan compatrm004 (REQ-009 boundary).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update §2/§3 lifecycle sentences to the current-schema-only policy (Plan Phase 4) | Completed | — | 20261107-131217 | Docs row: no release unit §2 validation/refusal paragraph + §3 creation wording |
| 2 | Run the docs checkers named in the Validation plan | Completed | — | 20261107-131217 | quality/structure/content-policy green; consistency --domain db exit 0 with 3 warnings on db_03_07 (other-batch file, deferred to batch 20261107-103000) |

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
- **Related target files**: `docs/41_db/db_01_architecture_and_schema-overview-and-config.md`