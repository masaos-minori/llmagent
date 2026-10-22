## Goal
Remove the claim that the MDQ service rebuilds the legacy `chunks` shape at start from the baseline list of `db_07` (REQ-005).

## Scope
- The `mdq.sqlite` bullet of the "database at the supported baseline shows" list only.

## Assumptions
- After the code change the MDQ service no longer rebuilds anything; a database that does not match the baseline is recreated (the sentence after the list already says so).

## Design decisions
- Keep the observable baseline fact ("`chunk_id` as the first `chunks` column") and drop the parenthetical about the legacy shape and the start-time rebuild.

## Alternatives considered
N/A: one-bullet docs edit.

## Implementation
### Target file
`docs/41_db/db_07_api_and_operations-recovery-and-reference.md`

### Procedure
1. Change the bullet to state only that `mdq.sqlite` shows `chunk_id` as the first `chunks` column.

### Method
- Minimal in-place edit; keep the other bullets and the closing sentence ("A database that does not match is recreated").

### Details
- No history wording.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`.

## Completion criteria
- The bullet no longer mentions a start-time rebuild or the legacy shape; docs checkers pass.

## Out of Scope
- Other sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the `mdq.sqlite` baseline bullet | Completed | 20261022-111752 | 20261022-111752 | Changed: docs/41_db/db_07_api_and_operations-recovery-and-reference.md |
| 2 | Run the documentation checkers named in `routing.md` Tools | Completed | 20261022-111752 | 20261022-111752 | validated; docs checkers pass; full suite 9692 passed |

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
- **Requirement ID**: `REQ-005` (baseline list no longer claims a start-time rebuild)
- **Source issue**: `issues/20261021-102212_rmmdqmig_remove-the-mdq.sqlite-legacy-chunks-rebuild.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-094132_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101247
- **Related target files**: docs/41_db/db_07_api_and_operations-recovery-and-reference.md