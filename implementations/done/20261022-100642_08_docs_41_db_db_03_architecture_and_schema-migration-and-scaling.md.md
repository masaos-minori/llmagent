## Goal
Rewrite the workflow parts of `db_03` so they describe a create-only bootstrap with recreate-on-mismatch, and drop the "kept until removal lands" wording (REQ-007: no description of in-place workflow migration).

## Scope
- Section 8 bullets that name workflow migrations, section 8a, the `workflow.sqlite` row of 8e, and the open-decision bullet about rollback and the pre-upgrade backup.
- Sections 8b and 8d, and the offset-seeding subsection, belong to other procedures of this batch.

## Assumptions
- After the code change `create_workflow_schema()` creates base tables with `IF NOT EXISTS`, records the version when none exists, and refuses to record over a different latest version; the startup check rejects a mismatch.
- No anchor links point to the heading of 8a (verified by search), so the heading may be renamed.
- The docs content policy forbids copying migration identifiers, DDL, or counts.

## Design decisions
- Rename 8a to a create-only heading and describe: base DDL, version log, recreate (not migrate) a database older than the baseline, refusal to record over a different version.
- Remove history sentences about the removal (Current-Specification-Only policy).

## Alternatives considered
N/A: wording rewrite fixed by the Plan.

## Implementation
### Target file
`docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`

### Procedure
1. Section 8 bullets: remove `workflow.sqlite (section 8a)` from the list of databases with their own incremental mechanisms, and change the `create_workflow_schema()` description to "runs the DDL and records the schema version" without migrations; adjust the closing sentence about which initializers migrate an existing file so workflow is not listed.
2. Section 8a: rename the heading and replace the body with the create-only description under Design decisions; delete the final sentence contrasting with rag/session.
3. Section 8e: update the `workflow.sqlite` row's "Why the migration code is kept" and "Removal condition" cells so they no longer say the code stays until a removal lands (state that the baseline is enforced by recreation).
4. Open decisions: delete the bullet about a rollback beyond the pre-upgrade backup of `workflow.sqlite` required by the deployment guide.

### Method
- Minimal in-place edits; leave all eventbus and mdq passages as they are.
- Re-read the file before editing: three other procedures of this batch edit the same file; apply sequentially.

### Details
- Keep the 8e table structure (columns and the other two rows); the "kept" column is revisited once all removals have landed.
- Do not put version numbers, identifiers, or DDL into the text.

## Compatibility considerations
N/A: documentation only. Section numbering stays (8a remains 8a).

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain deployment`.
- `rg "apply_workflow_migrations" docs/41_db` returns no match.

## Completion criteria
- No sentence in the file describes an in-place workflow migration, a pre-upgrade backup requirement, or code that "stays until removal".
- Docs checkers pass.

## Out of Scope
- Sections 8b, 8d, offset seeding, and any other document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the section 8 bullets, 8a, the 8e workflow row, and the rollback bullet | Completed | 20261022-105310 | 20261022-105310 | Changed: docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md |
| 2 | Run the documentation checkers named in `routing.md` Tools | Completed | 20261022-105310 | 20261022-105310 | validated; docs checkers pass; full suite 9690 passed |

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
- **Requirement ID**: `REQ-007` (docs describe create-only bootstrap and recreate-on-mismatch)
- **Source issue**: `issues/20261021-102049_rmwfmig_remove-the-workflow.sqlite-incremental-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093726_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-100642
- **Related target files**: docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md