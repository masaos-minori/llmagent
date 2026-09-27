## Goal

Add a `consumer_id` query parameter to all 5 `/nack` POST calls in `tests/eventbus/test_eventbus_dlq.py`, fixing 4 tests that currently receive a uniform 422 (Unprocessable Entity) because `consumer_id` became a required query parameter on `/nack` (REQ-001).

## Scope

In scope: the 5 `client.post(f"/nack?event_id=...")` / `client.post("/nack?event_id=nonexistent")` call sites in this file only. Out of scope: `scripts/eventbus/ack_route.py`'s `nack()` handler (confirmed already correct and intentional, per commit `a5b2b011`'s "REQ-007").

## Assumptions

- A simple literal `consumer_id` value (e.g. `"test-consumer"`) is sufficient for all 5 call sites, since none of these 4 tests assert anything about consumer-specific ownership (this file's `client` fixture is not principal/ownership-scoped, unlike `eb001`'s `principal_client`).

## Design decisions

- Add `&consumer_id=test-consumer` to each call's query string (or an equivalent `params={...}` dict form, matching whichever style — f-string query concatenation vs. `params=` kwarg — each specific call site already uses), directly mirroring the already-applied fix pattern in the sibling file `tests/eventbus/test_eventbus_dlq_promotion.py` (commit `a5b2b011`).

## Alternatives considered

- Adding a shared `_nack(client, event_id)` helper function that always includes `consumer_id`, refactoring all 5 call sites to use it: rejected as unnecessary scope expansion beyond the minimal fix — 5 direct edits are simpler and match this file's existing style (no such helper currently exists for `/nack` calls in this file).

## Implementation

### Target file

`tests/eventbus/test_eventbus_dlq.py`

### Procedure

1. Re-confirm each of the 5 `/nack` call sites' exact current line/form via `rg -n 'client.post\(.*"/nack' tests/eventbus/test_eventbus_dlq.py` (adversarial re-verification — line numbers may have shifted since the Plan was written).
2. For each call, add `&consumer_id=test-consumer` to the query string (matching each site's existing f-string/literal style).

### Method

Direct query-string addition at 5 call sites — no structural change.

### Details

- `test_inline_dlq_promotion_on_nack` (2 calls, lines ~192, 198): `client.post(f"/nack?event_id={ev['event_id']}")` → `client.post(f"/nack?event_id={ev['event_id']}&consumer_id=test-consumer")`.
- `test_inline_dlq_promotion_skipped_below_threshold` (1 call, line ~226): same pattern.
- `test_inline_dlq_promotion_not_found` (1 call, line ~242): `client.post("/nack?event_id=nonexistent")` → `client.post("/nack?event_id=nonexistent&consumer_id=test-consumer")`.
- `test_nack_on_already_dlq_event_does_not_repromote` (1 call, line ~264): same pattern as the first.
- Reference: `tests/eventbus/test_eventbus_dlq_promotion.py`'s already-applied fix (commit `a5b2b011`) for the exact pattern to replicate.

## Compatibility considerations

- No production code changes; test-only fix restoring compatibility with the already-shipped `consumer_id`-required contract (REQ-007).

## Security considerations

N/A: test-only fix, no security-relevant behavior change.

## Rollback considerations

- `git revert` the commit, or manually remove the added `consumer_id` query parameters.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/eventbus/test_eventbus_dlq.py` | Integration | `uv run pytest tests/eventbus/test_eventbus_dlq.py -q` | All 4 previously-failing tests return their originally-intended status codes |

## Completion criteria

- `uv run pytest tests/eventbus/test_eventbus_dlq.py -q` passes with no failures.

## Out of scope

- Other eventbus test files (`eb001`, `eb002`, `eb004`-`eb007` — each tracked under its own separate Plan/implementation procedure).
- `scripts/eventbus/ack_route.py`'s `nack()` handler (confirmed already correct).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: fixing the existing 5 call sites is itself the fix |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no docs/00_index.md task-scope mapping for this test file |

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
- **Requirement ID**: REQ-001: add `consumer_id` to all 5 `/nack` call sites
- **Source issue**: issues/20260927-075243_eb003_eventbus-dlq-endpoint-returns-422-for-all-requests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-082814_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-092001
- **Related target files**: tests/eventbus/test_eventbus_dlq.py
