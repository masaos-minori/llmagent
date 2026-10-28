# Procedure: add NACK update failure, failed inline promotion and inline-then-sweep tests

## Goal

Cover a failed NACK update, a NACK whose inline promotion fails, and idempotency of inline promotion followed by the sweep (Plan REQ-002, REQ-004, REQ-006).

## Scope

- Modify only `tests/eventbus/test_eventbus_dlq_promotion.py`.
- Test-only change; no source file is edited.

## Assumptions

- Rows 1 and 2 have landed; the new test names are created by this procedure.
- Overlap (compatible): `plans/done/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md` (archived, procedures pending) also targets `scripts/eventbus/ack_route.py` (authorization at the start of the routes) and `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` (Authentication section and error table); this procedure edits only the promotion block of `_nack_and_promote` and one transition-table row.

## Design decisions

- Locate edit points by test or fixture name, never by line number.
- Assert observable behavior; use barriers or events, never sleeps.

## Alternatives considered

N/A: lightweight row; the Plan fixes the approach.

## Implementation

### Target file

`tests/eventbus/test_eventbus_dlq_promotion.py`

### Procedure

- Add `test_nack_with_failing_inline_promotion_returns_200_and_sweep_promotes` (new): reach the retry limit as `test_dlq_promotion_when_consumer_delivery_failure_count_gte_max_retry` does, monkeypatch `eventbus.dlq._atomic_write` to raise `OSError` for the last NACK; assert 200 without `dlq_promoted`, `dlq_at` NULL, then restore the function, call `sweep_orphans` and assert the event is promoted; repeat the NACK with the same idempotency key and assert it is a no-op.
- Add `test_nack_update_failure_leaves_delivery_state_unchanged` (new): make `delivery_repo.nack_event` fail through a connection proxy whose `execute` raises `sqlite3.OperationalError` at the delivery `UPDATE`; assert the error status and that `consumer_delivery` is unchanged after the rollback.
- Add `test_inline_promotion_then_sweep_returns_zero` (new): promote inline, call `sweep_orphans`, assert it returns 0.

### Method

Edit the existing tests in place and reuse the file's fixtures and helpers.

### Details

- Row 2 (`scripts/eventbus/ack_route.py`) has landed; the file's `client` fixture, `_event` and `_get_field` helpers are reused.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_dlq_promotion.py -q` | Pass |
| 2 | `uv run ruff format tests/eventbus/test_eventbus_dlq_promotion.py`; `uv run ruff check tests/eventbus/test_eventbus_dlq_promotion.py` | No finding |

## Completion criteria

- The failed-inline-promotion test fails on the pre-change code (HTTP 500) and passes after row 2.

## Out of Scope

- Source files and other test files.
- Documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or update tests per Validation plan | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-002, REQ-004, REQ-006 (NACK/promotion failure points)
- **Source issue**: issues/20261027-155846_ebdurable003_define-publish-dlq-durability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093155_ebdurable003_define-publish-dlq-durability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115345
- **Related target files**: tests/eventbus/test_eventbus_dlq_promotion.py
