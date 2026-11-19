## Goal
- Document the sweep task fields, the two new degraded reasons, and the extended liveness in the health endpoint guide (REQ-007: the guide matches the health contract).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `docs/24_eventbus/eventbus_10_health_endpoint.md`. Depends on the seq 02 document (the contract it describes).

## Assumptions
- The guide defines liveness as "the DLQ sweep task is running" and lists reasons without a sweep entry (verified in Step 3a); the response-content paragraph names `last_dlq_sweep` and refers to `health_route.py` for the exact schema.
- The guide is far below the file size limit (verified in Step 3a), and the edit adds only a few sentences and two table rows.

## Design decisions
- Describe the contract in prose and the reasons table; add no response example.

## Alternatives considered
N/A: a direct update of the existing sections.

## Implementation
### Target file
`docs/24_eventbus/eventbus_10_health_endpoint.md`

### Procedure
1. In "Response Content", add that the body reports the authorization sweep task state and `last_authz_sweep` (`result` is `ok`, `failed`, or `not_run`; `time` is an ISO-8601 string or `null`), kept in memory like the DLQ sweep state.
2. In the reasons table, add `authz_sweep_task_stopped` (the authorization sweep background task has stopped) and `authz_sweep_failing` (the last authorization sweep cycle failed).
3. In "Health Tiers", change the `liveness` meaning to the DLQ sweep task and the authorization sweep task both running; state that `authz_sweep_failing` is a real failure with HTTP 503 that changes neither `liveness` nor `readiness`, like `dlq_sweep_failing`.
4. In the paragraph before the readiness gate, add `authz_sweep_task_stopped` to the reasons that fail the gate (it lowers liveness) beside `dlq_task_stopped`.

### Method
- English only; reuse the guide's wording and table style; no port, token value, or file listing.

### Details
- Mention that a stopped sweep leaves expired authorization grants active, since that is why it is a liveness reason.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py docs/24_eventbus/eventbus_10_health_endpoint.md`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py`, `check_docs_consistency.py --domain eventbus`.

## Completion criteria
- The guide lists the new fields, both reasons, and the extended liveness, and all checkers pass.

## Out of Scope
- Any other guide; the contract itself (seq 02 document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the four places in the guide | Completed | 20261119-120241 | 20261119-120306 | Step 2 stale check clean; Step 3a: guide text verified against the implemented contract (fields authz_sweep_task, last_authz_sweep; reasons; liveness); guide 5114 bytes; clean at baseline Changed: docs/24_eventbus/eventbus_10_health_endpoint.md (intro, response content, reasons table, gate sentence, liveness row, real-failure sentence; 5114 to 5731 bytes). Every documented name exists in health_route.py |
| 2 | Run the documentation checkers named in `routing.md` Tools | Completed | 20261119-120306 | 20261119-120306 | Checkers pass: quality, structure, content-policy strict, japanese, consistency eventbus |

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
- **Requirement ID**: `REQ-007` (document the extended health contract)
- **Source issue**: issues/20261117-123017_adrchk017_eventbus-task-supervision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-113711_adrchk017_eventbus-task-supervision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-114620
- **Related target files**: `docs/24_eventbus/eventbus_10_health_endpoint.md`