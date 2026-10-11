## Goal
- Make the ACK route answer HTTP 409 with `event already in dead letter queue` when the event is already in the DLQ (`REQ-003`), restoring the behavior approved in REQ-005 of `plans/done/20261008-160952_plan.md`.

## Scope
- One change in `_do_ack` of `scripts/eventbus/ack_route.py`: detect `events.dlq_at` for a non-new ACK and raise 409 with the existing `ERR_EVENT_IN_DLQ` constant.
- No change to the NACK path, authorization checks, 400/403/404 behavior, or the first-ACK and duplicate-ACK responses.

## Assumptions
- Verified in the current file: `_do_ack` raises 404 when `found` is false, returns `{event_id, acked: true, seq}` for a new ACK, and otherwise runs a locked `SELECT seq FROM events` and returns `already_acked: true`. It never reads `dlq_at`, so a DLQ-event ACK currently returns 200.
- `ERR_EVENT_IN_DLQ` is already imported in this module and is used by the NACK path, which reads `events.dlq_at` the same way.
- The repository function returns `(True, False, None)` without writing anything for a DLQ event (`scripts/eventbus/delivery_repo.py`), so the route only needs to map that case.

## Design decisions
- Read `dlq_at` in the route, matching the NACK path, instead of inferring DLQ from `seq is None`.
- Reuse the existing locked query: change it to `SELECT seq, dlq_at FROM events WHERE event_id = ?` so no extra round trip is added; evaluate `dlq_at` after the query and before building the duplicate-ACK response.
- Raise the `HTTPException` outside the `try/except (sqlite3.Error, TypeError)` block so a DB error is not turned into a 409, and a 409 is not swallowed.
- Keep the repository transaction untouched (INV-16).

## Alternatives considered
- Restore a 4-value return so the repository signals DLQ: rejected by the Plan.
- Decide DLQ from `seq is None`: rejected; fragile coupling to an incidental sentinel.
- Make DLQ-event ACK a 200 no-op and document it: rejected; contradicts the approved REQ-005 intent.

## Implementation
### Target file
`scripts/eventbus/ack_route.py`

### Procedure
1. Re-read `_do_ack` from the `found` check to the end of the function and confirm the structure described under Assumptions.
2. Extend the locked event query to return `seq` and `dlq_at`.
3. After the query, when `dlq_at` is not null, raise `HTTPException(status_code=409, detail=ERR_EVENT_IN_DLQ)`.
4. Keep the rest of the duplicate-ACK response unchanged, setting `seq` from the same row.

### Method
- Edit only the duplicate-ACK branch (the part after `if newly_acked:` returns).
- Keep the `logger.debug("event already acked ...")` message and the `already_acked` key as they are (the field-name question is Plan `UNK-03`, out of scope).

### Details
- Order of checks for a non-new ACK: DLQ first (409), then the existing duplicate-ACK 200 response.
- Because the repository returns before writing for a DLQ event, no `consumer_delivery` row or offset is created for it.
- Add a short comment citing the DLQ rejection, without a line-number reference.

## Compatibility considerations
- Public HTTP behavior: ACK on a DLQ event changes from 200 to 409 (documented in procedure 06 and pinned by the test in procedure 05).
- First ACK, duplicate ACK, unknown event, 400, and 403 responses are unchanged.
- Consumers that retried ACK for DLQ events and relied on 200 must now handle 409; this restores the previously approved behavior.

## Security considerations
- No new input; `event_id` stays a bound SQL parameter.
- The 409 detail is the existing constant and discloses no new data.

## Rollback considerations
- Single-file change; revert with `git revert` of the implementing commit, or `git checkout -- scripts/eventbus/ack_route.py` before it is committed.
- No data or deployment state is touched.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_ack_nack.py tests/eventbus/test_eventbus_ack_endpoint.py`: the new DLQ test passes and no previously passing test fails.
- `uv run ruff check`, `uv run mypy`, `uv run lint-imports`, and `uv run bandit -r scripts/eventbus -c pyproject.toml` report no new findings.
- Deployment script check: N/A; `scripts/eventbus/` is rsynced and no `deploy.sh` line changes.

## Completion criteria
- `POST /events/{event_id}/ack` for an event whose `dlq_at` is set returns 409 with `event already in dead letter queue`.
- All other ACK responses are unchanged.
- The DLQ check reads `events.dlq_at` in the route and does not depend on the repository's `seq`.

## Out of scope
- NACK path, repository code, schema, and the `already_acked` versus `newly_acked` field-name question (`UNK-03`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend the locked event query to return `seq` and `dlq_at` | Pending | — | — | |
| 2 | Raise 409 with `ERR_EVENT_IN_DLQ` when `dlq_at` is set | Pending | — | — | |
| 3 | Add or update tests per Validation plan | Pending | — | — | Covered by procedure 05 |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 5 | Update documentation, if in scope | Pending | — | — | N/A: documentation is handled by procedure 06 |

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
- **Requirement ID**: `REQ-003` (DLQ-event ACK returns 409)
- **Source issue**: issues/20261011-075321_eb012ack_resolve-ack_event_for_consumer-return-contract-mismatch-between-code-and-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261011-153619_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261011-175858
- **Related target files**: scripts/eventbus/ack_route.py
