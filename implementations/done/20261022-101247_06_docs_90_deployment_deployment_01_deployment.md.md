## Goal
Remove the "recreating a legacy chunk schema" clause from the MDQ paragraph of the deployment guide (REQ-006).

## Scope
- One clause of the MDQ paragraph; the derived-store and re-indexing statements stay.

## Assumptions
- After the code change the MDQ service creates its tables when it starts and never recreates a legacy schema.
- The clause links to `db_03` section 8d; the rewritten 8d no longer describes recreation, so the link target must be removed with the clause.

## Design decisions
- Keep: derived index owned by the MDQ server; `init_db.sh` does not create it; the service creates the file and its tables at start; recovery is by re-indexing; backup and rotation helpers do not cover it; the health check reports a missing file or an unhealthy schema as degraded.

## Alternatives considered
N/A: one-clause docs edit.

## Implementation
### Target file
`docs/90_deployment/deployment_01_deployment.md`

### Procedure
1. In the `mdq.sqlite` paragraph delete ", recreating a legacy chunk schema as described in [DB migration and scaling](...) (section 8d)" and fix the sentence.

### Method
- Minimal in-place edit; re-read the file before editing (the workflow and EventBus procedures edit other passages).

### Details
- Keep the other links of the paragraph (ADR-008, active databases).

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain deployment`.

## Completion criteria
- The paragraph no longer mentions recreating a legacy chunk schema and keeps the re-indexing recovery statement; docs checkers pass.

## Out of Scope
- Other passages and sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the legacy-schema clause | Completed | 20261022-111753 | 20261022-111753 | Changed: docs/90_deployment/deployment_01_deployment.md |
| 2 | Run the documentation checkers named in `routing.md` Tools | Completed | 20261022-111753 | 20261022-111753 | validated; docs checkers pass; full suite 9692 passed |

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
- **Requirement ID**: `REQ-006` (deployment guide no longer mentions legacy chunk recreation)
- **Source issue**: `issues/20261021-102212_rmmdqmig_remove-the-mdq.sqlite-legacy-chunks-rebuild.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-094132_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101247
- **Related target files**: docs/90_deployment/deployment_01_deployment.md