## Goal
Remainder of the Plan's row for `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` (REQ-001): section 8e points to the schema check in the deployment guide, but the check now lives in `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` (section 11a). Repoint the sentence so it does not dangle.

## Scope
- In: the one sentence in section 8e that begins "How to read a database's current schema without changing it".
- Out: the baseline table, the open decisions, every other section, the deployment guide.

## Assumptions
- This is the "Partially implemented" remainder of row 1: the earlier procedure (`implementations/done/20261021-101134_01_docs_41_db_db_03_architecture_and_schema-migration-and-scaling.md.md`) added section 8e with a pointer to the deployment guide, which is no longer the location (Plan Background, Location amendment of 2026-10-21). Its filename carries `seq` 03 only because `seq` 01 already exists in `done/`; the row position is still 1.
- Row 02 adds the section 11a target in the same change, so the link target exists after both land.

## Design decisions
- Replace the sentence instead of adding one, so section 8e keeps exactly one pointer.

## Alternatives considered
N/A: a one-sentence pointer fix.

## Implementation
### Target file
`docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`

### Procedure
1. Replace the sentence below in section 8e.
2. Run the documentation checkers (the new link must resolve).

### Method
Old sentence: "How to read a database's current schema without changing it: [Deployment Guide](../90_deployment/deployment_01_deployment.md), section 3.1."

New sentence: "How to read a database's current schema without changing it: [DB API and Operations](db_07_api_and_operations-recovery-and-reference.md#11a-identifying-a-databases-current-schema) (section 11a)."

### Details
- Do not touch the rest of section 8e.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py`, `check_needs_confirmation_inventory.py`, `check_db_separation.py`.
- `rg "deployment_01_deployment" docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` returns no match.

## Completion criteria
- Section 8e links to section 11a of the operations document and no longer to the deployment guide.
- The listed checkers pass.

## Out of Scope
- Editing the baseline wording; editing the deployment guide.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the pointer sentence in section 8e (REQ-001) | Completed | 20261021-103530 | 20261021-103558 | Changed: docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md (section 8e pointer now targets db_07 section 11a) |
| 2 | Run the documentation checkers (REQ-005) | Completed | 20261021-103530 | 20261021-103558 | check_docs_quality, check_docs_structure, check_docs_content_policy --strict, check_docs_japanese, check_needs_confirmation_inventory, check_db_separation all exit 0; no deployment_01 pointer left. Docs-only: no test run. |

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
- **Requirement ID**: `REQ-001` (baseline record; pointer to the schema check); `REQ-005` (checkers pass)
- **Source issue**: `issues/20261020-122549_compat001_define-the-supported-from-schema-baseline-and-retire-or-keep-decision-for-each-db-migration.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261020-233138_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-101134
- **Related target files**: `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`