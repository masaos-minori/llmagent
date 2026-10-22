## Goal
Remove the workflow migration wording from the deployment guide: the init responsibilities, the backup rationale and approval-stage sentences, and the `[FATAL]` recovery row (REQ-007).

## Scope
- The `init_db.sh` responsibilities bullet on migrations, the paragraph that says to back up `workflow.sqlite` because migrations are applied in place, and the recovery-table row "Apply migrations via `init_db.sh`".
- EventBus migration wording in the same bullet is changed by another procedure of this batch.

## Assumptions
- After the code change `init_db.sh` creates the workflow database and refuses to record over a different version; a workflow database older than the current schema is recreated (archive the file first).
- The statement that the workflow definition must not contain `require_approval` is unrelated to migration and stays.

## Design decisions
- Responsibilities bullet: the workflow, rag, and session databases are create-only and are not migrated; only the EventBus part keeps its current wording until its own procedure lands.
- Replace the backup/approval-stage migration sentences with a one-sentence recreate statement; keep the `require_approval` sentence.
- Recovery row: "Recreate the workflow database (archive the file, then run `init_db.sh`)".

## Alternatives considered
N/A: wording rewrite fixed by the Plan.

## Implementation
### Target file
`docs/90_deployment/deployment_01_deployment.md`

### Procedure
1. Rewrite the responsibilities bullet "Applies the incremental migrations of `workflow.sqlite` and `eventbus.sqlite` ..." so `workflow.sqlite` is listed with the create-only databases.
2. In the paragraph after the list, delete the backup-because-migrations-are-applied sentence and the two sentences about marking approval-stage tasks as failed and dropping the `approvals` table; add the recreate statement; keep "The workflow definition must not contain `require_approval`; the loader rejects the key."
3. Change the `[FATAL] Workflow schema version mismatch` recovery row to the recreate action.

### Method
- Minimal in-place edits; no migration identifiers or DDL in the text.
- Re-read the file before editing: the MDQ and EventBus procedures of this batch edit other passages of it.

### Details
- Keep the table row's other cells (source `setup_services.sh`).

## Compatibility considerations
N/A: documentation only; it describes the post-change `init_db.sh` and `setup_services.sh` behavior.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain deployment`.

## Completion criteria
- No workflow migration, in-place backup rationale, or "Apply migrations" recovery remains; the `require_approval` sentence is intact; docs checkers pass.

## Out of Scope
- EventBus and MDQ passages and other sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the responsibilities bullet, the backup paragraph, and the recovery row | Pending | — | — | |
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
- **Requirement ID**: `REQ-007` (docs describe create-only bootstrap and recreate-on-mismatch)
- **Source issue**: `issues/20261021-102049_rmwfmig_remove-the-workflow.sqlite-incremental-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093726_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-100642
- **Related target files**: docs/90_deployment/deployment_01_deployment.md
