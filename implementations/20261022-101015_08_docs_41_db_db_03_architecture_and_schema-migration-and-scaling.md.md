## Goal
Rewrite the EventBus parts of `db_03` to describe a create-only schema and remove the open decision about two initialization paths (REQ-006).

## Scope
- Section 8b, the `eventbus.sqlite` row of 8e, the sentence of section 9 that names `_migrate()`, the section 8 bullets that describe EventBus migration, and the "two paths" open decision.
- The workflow parts, section 8d, and the offset-seeding subsection are edited by other procedures of this batch.

## Assumptions
- After the code change `create_eventbus_schema()` runs the DDL only and `open_db()` creates the schema from `schema.sql` when `events` is absent and otherwise does nothing; a database older than the baseline is recreated.
- The "separate data seeding" bullet of 8b names `migrate_legacy_offsets()`, which another procedure removes; this rewrite drops that bullet together with 8b's migration text.
- The docs content policy forbids migration identifiers, DDL, and counts.

## Design decisions
- Rename 8b to a create-only heading and describe: `schema.sql` is the only DDL definition read by the bootstrap and by the service; an older database is recreated; the `published_at` default note stays because it explains an existing difference.
- Keep the open decision about an EventBus schema-version marker; remove only the two-paths decision.

## Alternatives considered
N/A: wording rewrite fixed by the Plan.

## Implementation
### Target file
`docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`

### Procedure
1. Section 8 bullets: remove `eventbus.sqlite (section 8b below)` from the list of databases with their own migration mechanisms and the EventBus migration clause from the `create_schema()` description, including the closing sentence about which initializers migrate an existing file.
2. Section 8b: rename the heading and replace the body with the create-only description; delete the migration rules list.
3. Section 8e: update the `eventbus.sqlite` row's "Why the migration code is kept" and "Removal condition" cells.
4. Section 9: replace the sentence about `_migrate()` applying additive changes with a statement that schemas are created from their DDL and recreated when older than the baseline.
5. Open decisions: delete the bullet about whether the two EventBus migration paths stay separate.

### Method
- Minimal in-place edits; re-read the file before editing (three other procedures edit it); apply sequentially.
- Check inbound anchors for the renamed heading with `rg "8b"` and the anchor check before and after.

### Details
- Keep the 8e table structure and the mdq row for its own procedure.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain deployment`.
- `rg "apply_eventbus_migrations|_migrate" docs/41_db` shows no EventBus migration reference.

## Completion criteria
- No sentence describes EventBus migration, two initialization paths, or code kept until removal; the two-paths decision is gone; docs checkers pass.

## Out of Scope
- Workflow, MDQ, and offset-seeding passages.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite section 8 bullets, 8b, the 8e EventBus row, the section 9 sentence, and the open decision | Pending | — | — | |
| 2 | Run the documentation checkers named in `routing.md` Tools | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (docs describe a create-only EventBus schema)
- **Source issue**: `issues/20261021-102130_rmebmig_remove-the-eventbus.sqlite-schema-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093935_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101015
- **Related target files**: docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md
