# Procedure: handle an inline promotion OSError after a committed NACK

## Goal

Make `_nack_and_promote` convert an `OSError` from inline promotion into a deferred promotion instead of an HTTP 500 (Plan REQ-004).

## Scope

- Modify only `scripts/eventbus/ack_route.py`.
- In scope: the promotion block at the end of `_nack_and_promote` inside `nack`.
- Out of scope: authorization at the start of the routes (another Plan), ack logic, tests and docs.

## Assumptions

- `nack_event()` has already committed the NACK when promotion starts, and `_atomic_write` runs before any DB write in the inline path, so catching `OSError` leaves the event live and consistent.
- A repeated NACK with the same idempotency key is a no-op that still reaches the promotion check.
- Overlap (compatible): `plans/done/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md` (archived, procedures pending) also targets `scripts/eventbus/ack_route.py` (authorization at the start of the routes) and `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` (Authentication section and error table); this procedure edits only the promotion block of `_nack_and_promote` and one transition-table row.

## Design decisions

- Catch only `OSError`; a `sqlite3.Error` means the database is unhealthy and stays an HTTP 500.

## Alternatives considered

N/A: the Plan fixes the approach (see its Design section).

## Implementation

### Target file

`scripts/eventbus/ack_route.py`

### Procedure

- Wrap `promoted = is_promotable(db, event_id, cfg.max_retry) and promote_single(db, cfg.deadletter_dir, event_id, consumer_failure_count)` in `try`/`except OSError`.
- In the handler log `logger.exception("nack: inline DLQ promotion failed, deferred to sweep event_id=%s", event_id)` and set `promoted = False`.
- Leave the returned tuple and the response shape unchanged: the 200 body omits `dlq_promoted` when `promoted` is false.

### Method

Add a six-line `try`/`except` around one expression.

### Details

- The existing `from eventbus.dlq import is_promotable, promote_single` stays inside the same `if` block.
- `logger` is already defined at module level.

## Compatibility considerations

- A committed NACK whose DLQ file write fails now returns 200 instead of 500 (UNK-03 in the Plan); the NACK is durable and the sweep promotes the event.

## Security considerations

- No new input; the failure detail is logged, not returned.

## Rollback considerations

Revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_dlq_promotion.py tests/eventbus/test_eventbus_dlq.py -q` | Pass |
| 2 | `uv run ruff format scripts/eventbus/ack_route.py`; `uv run ruff check scripts/eventbus/ack_route.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` | No finding; six import contracts kept |
| 3 | `uv run bandit -r scripts/eventbus/ack_route.py -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` | No finding; module under the size gate |

## Completion criteria

- A NACK with a failing inline file write returns 200 without `dlq_promoted` and leaves `dlq_at` NULL.

## Out of Scope

- Authorization, ACK handling, DLQ module changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-10-28 | 2026-10-28 |  |
| 2 | Add or update tests per Validation plan | Completed | — | — | test lands in row 4 of this batch |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-28 | 2026-10-28 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | docs land in row 7 of this batch |

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
- **Requirement ID**: REQ-004 (committed NACK stays 200 when the inline DLQ file write fails)
- **Source issue**: issues/20261027-155846_ebdurable003_define-publish-dlq-durability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093155_ebdurable003_define-publish-dlq-durability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115345
- **Related target files**: scripts/eventbus/ack_route.py