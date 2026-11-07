## Goal

- Rewrite `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` (188 lines) as the current-schema-only policy document plus the manual archive-and-recreate runbook (REQ-009: the core migration-policy document is replaced).

## Scope
**Release unit**: N/A: not part of a release unit (documentation row, Plan Phase 4)

## Assumptions

- The document currently cites the ledger and dbmig001 (Plan row evidence); its scaling-limits/constraint sections (front matter tags `migration`, `constraints`, `scaling-limits`) keep their non-migration content where still true.
- Plan overlap (`tools/check_plan_target_overlaps.py` candidate): this file is also targeted by plan compatrm004 — judged compatible: this Plan runs first and 004 layers its wording sweep onto the rewritten document.

## Design decisions

- Full rewrite of the migration sections into: policy statement (no automatic migration or version stamping; refusal message wording per REQ-004) + the manual archive → remove/rename → recreate runbook aligned with `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` section 11.
- Keep the file name and Front Matter area/tags (renaming would ripple through `db_02` links; rename is out of scope).

## Alternatives considered

- Deleting the document: rejected — REQ-009 assigns the policy text to the docs, and other documents link to `db_03`.

## Implementation
### Target file
`docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`

### Procedure
1. After Plan Phases 1-3 land, rewrite the migration-policy sections (Phase 4).

### Method
- Remove: forward-only migration registry description, ledger/baseline text, dbmig001 references, and version-chain narratives (sections citing `schema_migrations` / `workflow_schema_version` / `WORKFLOW_SCHEMA_VERSION`).
- Add: current-schema-only acceptance rules per domain (eventbus: `user_version = 6` + fingerprint; workflow: exact shape, marker tables = legacy), the fixed refusal message text, and the operator runbook (archive with `rotate_all_dbs()`, remove/rename, recreate via `deploy/init_db.sh`) cross-linked to `db_07` section 11.
- Preserve the scaling-limits and constraint sections' still-valid content.

### Details
- Docs-only: no code claims beyond what Phases 1-3 actually shipped; verify each statement against post-change source before writing.

## Compatibility considerations

- N/A: docs-only.

## Security considerations

- N/A: docs-only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`; `uv run python tools/check_docs_content_policy.py`; `uv run python tools/check_docs_consistency.py --domain db` (routing.md Tools).

## Completion criteria

- The document contains no migration/ledger policy claims and states the current-schema-only + manual recreate policy (AC-009).

## Out of Scope

- ADR wording sweep — plan compatrm004.
- `db_07` section 11 policy sentence — own document (seq 28).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the migration sections as current-schema-only policy + manual runbook (Plan Phase 4) | Pending | — | — | Docs row: no release unit |
| 2 | Run the docs checkers named in the Validation plan | Pending | — | — | |

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
- **Related target files**: `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`
