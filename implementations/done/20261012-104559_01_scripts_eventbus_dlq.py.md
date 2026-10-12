## Goal
- Add one public promotion predicate to `scripts/eventbus/dlq.py` implementing the ADR-006 INV-13 rule and make the background sweep select events by the same rule (`REQ-001`, `REQ-002`, `REQ-006`).

## Scope
- `_shared_promote`, the new predicate, and the `sweep_orphans` docstring.
- No change to `_shared_promote_single`, `promote_single`'s signature, `_atomic_write`, the DLQ record format, or the schema.

## Assumptions
- Decision (`Explicit in user instruction`, 2026-10-12): the ADR rule is adopted; an event is promotable when it has at least one `consumer_delivery` row, no row has `acked = 1`, and every row has `consumer_delivery_failure_count >= max_retry`.
- Verified against current source: `_shared_promote` joins `events` to `consumer_delivery` and filters `consumer_delivery_failure_count >= ?` with `dlq_at IS NULL`, with no check of other rows or ACKs; `sweep_orphans` only calls it; `promote_single` checks only `dlq_at IS NULL`.
- Verified against current source: `consumer_delivery` rows are created only by the ACK and NACK upserts in `delivery_repo.py`.
- Verified against current source: existing tests that call `sweep_orphans` seed one consumer row with `acked = 0` and a count at the limit, except three tests in `test_eventbus_dlq_promotion.py` that seed `acked = 1` (handled in the test procedure).

## Design decisions
- Express the rule once as a SQL condition constant over `events e` with one `max_retry` parameter (an `EXISTS` for at least one row and a `NOT EXISTS` for any row that is ACKed or below the limit), used by both the sweep query and the predicate, so the two cannot drift apart.
- The predicate `is_promotable(db, event_id, max_retry)` returns whether that event is currently promotable and not yet in the DLQ (`dlq_at IS NULL`).
- Keep the per-event `MAX(consumer_delivery_failure_count)` lookup that fills the DLQ record.

## Alternatives considered
- Compute the rule in Python after fetching rows: rejected; a single SQL condition keeps the sweep and the predicate identical.
- Add a `max_retry` parameter to `promote_single`: rejected; it would change a signature that tests call directly.

## Implementation
### Target file
`scripts/eventbus/dlq.py`

### Procedure
1. Re-read `_shared_promote`, `sweep_orphans`, and `promote_single`.
2. Add the module-level SQL condition constant and the public function `is_promotable(db, event_id, max_retry) -> bool` with a docstring stating the rule.
3. Replace the sweep's `JOIN consumer_delivery ... WHERE cd.consumer_delivery_failure_count >= ?` selection with `FROM events e WHERE e.dlq_at IS NULL AND <condition>`, dropping `DISTINCT`, and keep the rest of the loop unchanged.
4. Update the `_shared_promote` and `sweep_orphans` docstrings to describe the rule (all attempting consumers exhausted, none ACKed).
5. Run `ruff` and `mypy` on the file.

### Method
- Use the Edit tool; add a `# nosec B608` comment with a justification (constant SQL fragment, parameterized values) where the repository's suppression convention requires it, and run `tools/check_suppression_justification.py` if one is added.

### Details
- Condition (parameter: `max_retry`): `EXISTS (SELECT 1 FROM consumer_delivery cd WHERE cd.event_id = e.event_id) AND NOT EXISTS (SELECT 1 FROM consumer_delivery cd WHERE cd.event_id = e.event_id AND (cd.acked = 1 OR cd.consumer_delivery_failure_count < ?))`.
- Predicate query: `SELECT 1 FROM events e WHERE e.event_id = ? AND e.dlq_at IS NULL AND <condition>`; return whether a row exists.

## Compatibility considerations
- Single-consumer behavior is unchanged when that consumer's row is not ACKed and is at or above the limit; `promote_single`'s signature is unchanged; the new function is additive.

## Security considerations
- No new input path; SQL values stay parameterized and the fragment is a module constant.

## Rollback considerations
Revert with `git revert` of the implementing commit, or `git checkout -- scripts/eventbus/dlq.py` before it is committed.

## Validation plan
- Run `uv run pytest tests/eventbus`, `ruff` (check and format), `mypy`, and `lint-imports` per `rules/toolchain.md`; after the test procedure, the new multi-consumer tests pass and previously promoting cases now fail before the change.

## Completion criteria
- The sweep promotes only events satisfying the rule, `is_promotable` exposes the same rule, and checks report no new failures.

## Out of scope
- `ack_route.py` (next procedure), tests, documents, and the schema.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the shared condition constant and the is_promotable predicate | Completed | 20261012-105300 | 20261012-105300 | — Added _PROMOTABLE_CONDITION and is_promotable |
| 2 | Switch the sweep query to the shared condition | Completed | 20261012-105300 | 20261012-105300 | — Sweep query now uses the shared condition |
| 3 | Add or update tests per Validation plan | Completed | 20261012-105300 | 20261012-105300 | Covered by the test procedure (seq 03) Covered by procedure 03 |
| 4 | Run tests, ruff, mypy, and lint-imports | Completed | 20261012-105300 | 20261012-105300 | — tests/eventbus 340 passed, 1 skipped; ruff, mypy and lint-imports clean; diff-cover 100% |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-006`
- **Source issue**: issues/20261012-100156_eb019dlqmulti_resolve-multi-consumer-dlq-promotion-rule-mismatch-between-adr-006-and-code.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-102459_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-104559
- **Related target files**: scripts/eventbus/dlq.py