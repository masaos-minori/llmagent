## Goal
Reword the operator message printed on a workflow schema-version mismatch so it directs the operator to recreate the database rather than to migrate it (REQ-009).

## Scope
- Change one `echo` line in the pre-flight schema check.

## Assumptions
- The line is printed to stderr right after the `[FATAL] Workflow schema version mismatch` line and is not parsed by other scripts (verified: no other file in `deploy/` or `tests/` references the text).

## Design decisions
- New message: recreate the workflow database (archive the file, then run `deploy/init_db.sh`) before starting services.

## Alternatives considered
N/A: one-line message change.

## Implementation
### Target file
`deploy/setup_services.sh`

### Procedure
1. Replace the message "Run deploy/init_db.sh to migrate the workflow schema before starting services." with the recreate wording.

### Method
- Edit the string only; keep `exit 1` and the surrounding conditional unchanged.

### Details
- Because `deploy/` changes, the deploy skill's pre-deploy check applies; the change takes effect only after deployment.

## Compatibility considerations
Output text only; exit code and conditions are unchanged.

## Security considerations
N/A: text change only.

## Rollback considerations
Revert the commit and redeploy the script.

## Validation plan
- `bash -n deploy/setup_services.sh` (syntax) and the deploy skill's pre-deploy check.
- `uv run python tools/check_docs_consistency.py --domain deployment` if the deployment doc quotes the message.

## Completion criteria
- The message no longer says "migrate" and the script passes the syntax check.

## Out of Scope
- Pre-flight logic and other messages.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reword the message | Pending | — | — | |
| 2 | Run the syntax check and the pre-deploy check | Pending | — | — | |

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
- **Requirement ID**: `REQ-009` (recreate wording in the operator message)
- **Source issue**: `issues/20261021-102049_rmwfmig_remove-the-workflow.sqlite-incremental-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093726_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-100642
- **Related target files**: deploy/setup_services.sh
