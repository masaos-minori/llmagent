## Goal
- Update the readiness-gate comment in `setup_services.sh` so it defines liveness correctly (REQ-007: the script comment matches the health contract). Comment only.

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the comment block above `EB_READY=0` in `deploy/setup_services.sh`. This file is not in the issue's Target Files; it is fallout of the liveness change and is a row of the Plan's frozen table.

## Assumptions
- The comment says "liveness: the DLQ task is running" (verified in Step 3a); the gate code reads `liveness` and `readiness` and needs no change.
- The summary line "READY (db ok, dlq_task running)" stays true and is not changed.

## Design decisions
- Change the one parenthetical that defines liveness; keep the capacity-only explanation as it is.

## Alternatives considered
N/A: a one-line comment update.

## Implementation
### Target file
`deploy/setup_services.sh`

### Procedure
1. In the comment that starts "Ready only when the /health body reports liveness AND readiness", change "liveness: the DLQ task is running" to say that liveness means the DLQ task and the authorization sweep task are running.
2. Change no executable line.

### Method
- Keep the comment line width and the surrounding text.

### Details
- `git diff deploy/setup_services.sh` MUST show comment lines only.

## Compatibility considerations
N/A: comment only.

## Security considerations
N/A: comment only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `bash -n deploy/setup_services.sh` exits 0; `git diff deploy/setup_services.sh` shows comment lines only.

## Completion criteria
- The comment names both tasks and no executable line changed.

## Out of Scope
- The gate logic, the summary echo, and every other part of the script.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the comment | Completed | 20261119-120348 | 20261119-120404 | Step 2 stale check clean; Step 3a: comment text verified; the gate reads liveness and readiness so no executable line changes; clean at baseline Changed: deploy/setup_services.sh (comment only: liveness now names both tasks; bash -n ok; no executable line changed) |
| 2 | Run `bash -n` and confirm the diff is comment-only | Completed | 20261119-120404 | 20261119-120404 | bash -n exit 0; diff is comment-only |

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
- **Requirement ID**: `REQ-007` (script comment matches the health contract)
- **Source issue**: issues/20261117-123017_adrchk017_eventbus-task-supervision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-113711_adrchk017_eventbus-task-supervision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-114620
- **Related target files**: `deploy/setup_services.sh`