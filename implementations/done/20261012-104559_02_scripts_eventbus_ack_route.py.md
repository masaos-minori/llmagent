## Goal
- Make the NACK route promote inline only when the nacking consumer's count has reached the retry limit and the shared predicate holds (`REQ-003`, `REQ-006`).

## Scope
- The inline promotion condition inside the NACK handler only.
- No change to response shapes, error handling, or the ACK route.

## Assumptions
- Verified against current source: the handler calls `promote_single(db, cfg.deadletter_dir, event_id, consumer_failure_count)` when `consumer_failure_count is not None and consumer_failure_count >= cfg.max_retry`, with no other check.
- Verified against current source: the handler body runs inside `run_with_db_lock` and the NACK upsert is committed by `nack_event` before the promotion check, so the predicate sees the updated count.
- Depends on procedure 01: `eventbus.dlq.is_promotable` exists.

## Design decisions
- Add `is_promotable(db, event_id, cfg.max_retry)` to the existing condition and import it next to `promote_single` with the existing local-import style; `ack_route.py` is high-churn, so the change is that single condition.

## Alternatives considered
- Pass `max_retry` into `promote_single`: rejected; the signature stays unchanged.

## Implementation
### Target file
`scripts/eventbus/ack_route.py`

### Procedure
1. Re-read the NACK handler's promotion block.
2. Extend the local import to `from eventbus.dlq import is_promotable, promote_single`.
3. Add `and is_promotable(db, event_id, cfg.max_retry)` to the promotion condition and update the nearby comment to state that promotion needs every attempting consumer exhausted and none ACKed.
4. Review `git diff` for this file and confirm only that condition and comment changed.
5. Run `ruff` and `mypy` on the file.

### Method
- Use the Edit tool on the promotion block only.

### Details
- The response still carries `dlq_promoted: true` only when `promote_single` returned true.

## Compatibility considerations
- No response or status-code change; a NACK that no longer promotes returns 200 with the same body minus `dlq_promoted`.

## Security considerations
- No new input path.

## Rollback considerations
Revert with `git revert` of the implementing commit, or `git checkout -- scripts/eventbus/ack_route.py` before it is committed.

## Validation plan
- Run `uv run pytest tests/eventbus/test_eventbus_ack_nack.py tests/eventbus/test_eventbus_dlq.py tests/eventbus/test_eventbus_dlq_promotion.py`, then the full `tests/eventbus`, `ruff`, `mypy`, `lint-imports`.

## Completion criteria
- Inline promotion happens only when the predicate holds; the diff is limited to the condition and comment; checks report no new failures.

## Out of scope
- `dlq.py`, tests, documents, the ACK route.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the predicate pre-check to the inline promotion call | Completed | 20261012-105300 | 20261012-105300 | — Inline promotion now requires is_promotable |
| 2 | Add or update tests per Validation plan | Completed | 20261012-105300 | 20261012-105300 | Covered by the test procedure (seq 03) Covered by procedure 03 |
| 3 | Run the NACK and DLQ tests, ruff, mypy, and lint-imports | Completed | 20261012-105300 | 20261012-105300 | — NACK and DLQ tests pass; ruff, mypy and lint-imports clean |

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
- **Requirement ID**: `REQ-003`, `REQ-006`
- **Source issue**: issues/20261012-100156_eb019dlqmulti_resolve-multi-consumer-dlq-promotion-rule-mismatch-between-adr-006-and-code.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-102459_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-104559
- **Related target files**: scripts/eventbus/ack_route.py