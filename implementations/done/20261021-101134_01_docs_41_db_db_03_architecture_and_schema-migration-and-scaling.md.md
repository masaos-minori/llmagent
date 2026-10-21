## Goal
Record in `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` the minimum supported source schema, keep reason, removal condition, and owner for each of `workflow.sqlite`, `eventbus.sqlite`, and `mdq.sqlite` (REQ-001), classify every migration as removable (REQ-004), and record the EventBus decisions as open decisions with an owner (REQ-003).

## Scope
- In: one new subsection `8e. Supported Upgrade Baseline` after section 8d, and a one-sentence pointer from section 9.
- Out: sections 8a, 8b, 8d bodies (they keep describing the mechanisms that still exist in code); the deployment guide (row 02); any file under `scripts/` or `tests/`; the legacy file-offset import (`compat002`); the MDQ destructive-upgrade operating procedure (`compat006`).

## Assumptions
- Owner decision of 2026-10-21 (Plan Background): the baseline of every database is the current release schema, and a database older than the baseline is recreated, not migrated.
- Owner naming follows `docs/41_db/db_08_active_databases.md` (the component that owns the database).
- The section stays at the level of intent and constraints: no migration identifiers and no DDL (Plan Implementation Intent).

## Design decisions
- One table keeps the four required facts per database comparable; the three open EventBus decisions follow as a short list with their owners.
- Present-tense statements only; no history of how the baseline was fixed (Current-Specification-Only Policy).

## Alternatives considered
N/A: the Plan fixes the location (this document) and the content (baseline, keep reason, removal condition, owner).

## Implementation
### Target file
`docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`

### Procedure
1. Insert the subsection below between the end of section 8d (the sentence ending "are unaffected.") and the `---` that precedes `## 9. Schema Evolution`.
2. In section 9's first paragraph, append one sentence pointing to section 8e for the supported baseline.
3. Run the documentation checkers; if `check_docs_content_policy.py --strict` flags implementation detail, reduce the wording to intent rather than suppressing the check.

### Method
New subsection text (English; adjust only to satisfy the checkers):

```markdown
### 8e. Supported Upgrade Baseline

The minimum supported source schema of each database is the schema of the current release. A database older than that is recreated, not migrated, so no supported database depends on the migration mechanisms of sections 8a, 8b, and 8d. Every one of those migrations is classified removable; each database's migration code is removed by its own change.

| Database | Minimum supported source schema | Why the migration code is kept | Removal condition | Owner |
|---|---|---|---|---|
| `workflow.sqlite` | The current release schema: the recorded workflow schema version equals the current `WORKFLOW_SCHEMA_VERSION` | It stays until the change that removes it lands; no supported database needs it | No supported database is older than the minimum supported source schema | The workflow engine |
| `eventbus.sqlite` | The current release schema defined by `scripts/eventbus/schema.sql` | Same | Same | The EventBus service |
| `mdq.sqlite` | The current `chunks` shape, keyed by `chunk_id` | Same; a rebuilt store is recovered by re-indexing the Markdown files | Same | The `mdq-mcp` server |

How to read a database's current schema without changing it: [Deployment Guide](../90_deployment/deployment_01_deployment.md), section 3.1.

Open decisions (owner in parentheses):

- Whether the two EventBus migration paths of section 8b stay separate while they exist (the EventBus service).
- Whether `eventbus.sqlite` needs a schema-version marker; it has none (the EventBus service).
- Whether a failed migration needs a rollback beyond the pre-upgrade backup of `workflow.sqlite` that the deployment guide requires (the repository maintainers).
```

### Details
- Verified 2026-10-21: `WORKFLOW_SCHEMA_VERSION` is `1.1.0` in `scripts/db/schema_sql.py`; the deployed `workflow.sqlite` records `1.1.0`; the deployed `mdq.sqlite` `chunks` starts with `chunk_id`.
- Do not write the word "Needs confirmation" (the inventory checker tracks it); the open decisions use the heading "Open decisions".
- The legacy file-offset import stays described in "Offset Seeding" and is out of this table.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py`, `check_needs_confirmation_inventory.py`, `check_db_separation.py`.
- Confirm no file under `scripts/` or `tests/` changed (`git diff --name-only`).
- Confirm the three claims in Details against code (`rg WORKFLOW_SCHEMA_VERSION scripts/db/schema_sql.py`) before finishing.

## Completion criteria
- Section 8e states, for all three databases, the minimum supported source schema, the keep reason, the removal condition, and the owner (AC-1).
- The three EventBus-related decisions are recorded as open decisions with owners (AC-3).
- Every migration of sections 8a, 8b, and 8d is covered by the removable classification (AC-4).
- The listed checkers pass (AC-5).

## Out of Scope
- Editing sections 8a, 8b, 8d; adding migration identifiers or DDL; changing any code or test.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add section 8e and the section 9 pointer (REQ-001, REQ-003, REQ-004) | Completed | 20261021-101306 | 20261021-101332 | Changed: docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md (new section 8e; one sentence in section 9). WORKFLOW_SCHEMA_VERSION 1.1.0 re-verified. |
| 2 | Run the documentation checkers named in Validation plan (REQ-005) | Completed | 20261021-101306 | 20261021-101332 | check_docs_quality, check_docs_structure, check_docs_content_policy --strict, check_docs_japanese, check_needs_confirmation_inventory, check_db_separation all exit 0; no scripts/ or tests/ change. Docs-only: no test run. |

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
- **Requirement ID**: `REQ-001` (per-database baseline), `REQ-003` (EventBus decisions), `REQ-004` (every migration classified), `REQ-005` (checkers pass)
- **Source issue**: `issues/20261020-122549_compat001_define-the-supported-from-schema-baseline-and-retire-or-keep-decision-for-each-db-migration.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261020-233138_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-101134
- **Related target files**: `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`