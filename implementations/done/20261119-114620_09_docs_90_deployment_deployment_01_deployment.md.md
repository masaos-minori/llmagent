## Goal
- Align the readiness-gate sentence in the deployment guide with the predicate the script reads, now that liveness covers the sweep task (REQ-007: the guide matches the gate).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the `setup_services.sh` readiness sentence in `docs/90_deployment/deployment_01_deployment.md`. Depends on the seq 02 document.

## Assumptions
- The sentence states the gate as the readiness predicate `db == ok` AND `dlq_task == running`, while `deploy/setup_services.sh` reads the `liveness` and `readiness` fields of the `/health` body (verified in Step 3a); the edit aligns the guide with the script and changes no deployment behavior.
- The capacity-only reasons the sentence lists as tolerated stay as they are.

## Design decisions
- State the predicate as `liveness` and `readiness`, and say in one clause what liveness now covers, instead of naming individual body fields.

## Alternatives considered
N/A: a one-sentence wording update.

## Implementation
### Target file
`docs/90_deployment/deployment_01_deployment.md`

### Procedure
1. In the paragraph that describes `setup_services.sh`, replace "the readiness predicate `db == ok` AND `dlq_task == running`" with the `liveness` and `readiness` predicate, stating that liveness requires the DLQ sweep task and the authorization sweep task to be running and readiness requires a connectable database.
2. Leave the capacity-only list, the other sentences of the paragraph, and the rest of the file unchanged.

### Method
- English only; one sentence changed.

### Details
- The file is 27634 bytes; the edit adds a few dozen bytes.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py docs/90_deployment/deployment_01_deployment.md`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py`, `check_docs_consistency.py --domain deployment`.

## Completion criteria
- The sentence names the `liveness` and `readiness` predicate and what liveness covers, and all checkers pass.

## Out of Scope
- Any other part of the deployment guide.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the readiness sentence | Completed | 20261119-120328 | 20261119-120348 | Step 2 stale check clean; Step 3a: sentence text and the script predicate (liveness and readiness) verified; clean at baseline Changed: docs/90_deployment/deployment_01_deployment.md (one sentence: readiness predicate stated as liveness and readiness with what liveness covers; 27634 to 27764 bytes) |
| 2 | Run the documentation checkers named in `routing.md` Tools | Completed | 20261119-120348 | 20261119-120348 | Checkers pass: quality, structure, content-policy strict, japanese, consistency deployment |

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
- **Requirement ID**: `REQ-007` (the guide matches the readiness gate)
- **Source issue**: issues/20261117-123017_adrchk017_eventbus-task-supervision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-113711_adrchk017_eventbus-task-supervision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-114620
- **Related target files**: `docs/90_deployment/deployment_01_deployment.md`