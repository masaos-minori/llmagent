## Goal
Describe MDQ as create-only in `db_03`: rewrite section 8d, update the `mdq.sqlite` row of 8e, and fix the section 10 "auto-update source" phrase, keeping the re-indexing recovery statement and removing the data-loss warning (REQ-004).

## Scope
- Section 8d, the mdq row of 8e, and the section 10 phrase.
- Workflow, EventBus, and offset passages are edited by other procedures of this batch.

## Assumptions
- After the code change `create_production_tables()` creates tables with `IF NOT EXISTS` on every MDQ start and never drops anything; a store older than the baseline is recovered by deleting the file and re-indexing (documented in `db_08_active_databases.md`).
- No inbound anchor links target the heading of 8d (verified by search), so it may be renamed.
- Docs content policy: no counts, identifiers, or DDL.

## Design decisions
- Rename 8d to a create-only heading and state: tables are created at every MDQ start, nothing is dropped, MDQ is a derived store recovered by re-indexing the Markdown files, and a store older than the baseline is recreated.
- Update the 8e mdq row cells ("Why the migration code is kept", "Removal condition") so they no longer say the rebuild code stays until a removal lands.
- Section 10: call the module the schema creation source, not "schema/auto-update source".

## Alternatives considered
N/A: wording rewrite fixed by the Plan.

## Implementation
### Target file
`docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`

### Procedure
1. Replace the body of 8d (trigger, detection, action, comparison, data-loss warning) with the create-only description and rename its heading; keep the paragraph about `chunks_vec` and `memories_vec` being unrelated.
2. Update the mdq row of the 8e table.
3. Change "mdq.sqlite schema/auto-update source" in section 10 to "mdq.sqlite schema creation source".
4. In the section 8 bullet that lists databases with incremental migration/auto-update mechanisms, leave only `eventbus.sqlite` there and describe `workflow.sqlite` (8a) and `mdq.sqlite` (8d) as create-only (found by verification; same file); in the 8e intro change "sections 8b and 8d" to "section 8b".

### Method
- Minimal in-place edits; re-read the file before editing (three other procedures edit it); apply sequentially.
- Keep the 8e table structure.

### Details
- The 8d comparison to 8a is removed with the old body, so no cross-reference to 8a remains.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`.
- `rg "Data Loss Warning|old chunks schema|auto-update" docs/41_db` returns no match for MDQ.

## Completion criteria
- No text describes automatic legacy detection, the unconditional drop, or the data-loss warning; the re-indexing recovery statement remains; docs checkers pass.

## Out of Scope
- Other sections and documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite 8d, update the 8e mdq row and the section 10 phrase | Completed | 20261022-111751 | 20261022-111751 | Changed: docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md |
| 2 | Run the documentation checkers named in `routing.md` Tools | Completed | 20261022-111751 | 20261022-111751 | validated; docs checkers pass; full suite 9692 passed |

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
- **Requirement ID**: `REQ-004` (docs describe MDQ as create-only)
- **Source issue**: `issues/20261021-102212_rmmdqmig_remove-the-mdq.sqlite-legacy-chunks-rebuild.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-094132_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101247
- **Related target files**: docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md