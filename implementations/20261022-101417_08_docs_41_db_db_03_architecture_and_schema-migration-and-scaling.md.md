## Goal
Remove the "Offset Seeding" subsection and any sentence citing `migrate_legacy_offsets()` from `db_03`, keeping every link target valid (REQ-006).

## Scope
- The "Offset Seeding" subsection of section 9.
- The 8b bullet that names the function is removed by the EventBus schema procedure (it rewrites 8b); the section 9 sentence about `_migrate()` is also rewritten by that procedure.

## Assumptions
- After the code change the service does not read offset files, so no schema-evolution text should describe seeding.
- The only inbound link to the operations-section heading `#legacy-offset-files` was in this subsection (verified); the heading itself stays in `eventbus_07`.

## Design decisions
- Delete the whole subsection; no replacement text is needed because section 9 already states the evolution rules per database.

## Alternatives considered
N/A: removal required by the Plan.

## Implementation
### Target file
`docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`

### Procedure
1. Delete the "### Offset Seeding" heading and its paragraph, keeping the horizontal rule structure of the surrounding sections.
2. Run `rg "migrate_legacy_offsets|offset_migrator|Offset Seeding" docs/41_db` and fix any remaining mention in this file.

### Method
- Minimal in-place edit; re-read the file before editing (other procedures of this batch edit it); apply sequentially.

### Details
- Keep section 10 onward unchanged.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`; the anchor check if available.

## Completion criteria
- No mention of the removed function or module remains in the file; no broken link; docs checkers pass.

## Out of Scope
- Sections 8 through 8e and other documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the "Offset Seeding" subsection | Pending | — | — | |
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
- **Requirement ID**: `REQ-006` (remove the offset-seeding description)
- **Source issue**: `issues/20261021-102244_rmoffimp_remove-the-legacy-offset-import.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-094316_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101417
- **Related target files**: docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md
