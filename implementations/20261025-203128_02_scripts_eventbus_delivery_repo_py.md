## Goal

Confirm the latest-key-only NACK idempotency dedup scope in `scripts/eventbus/delivery_repo.py::nack_event()` (`REQ-004`) and internalize the unreachable `consumer_id=None` path (`REQ-007`), so the repository guard that seq 01 makes live actually deduplicates a repeated delivery attempt (`REQ-003`).

## Scope

- **In-Scope** (`scripts/eventbus/delivery_repo.py` only):
  - Confirm the dedup scope is latest-key-only (single `consumer_last_nack_attempt` comparison) — the current guard already implements the recommended model; no logic change.
  - Internalize the `consumer_id=None` path with an explicit internal-only comment (`REQ-007`, option a).
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - Route key source + keyless handling (`scripts/eventbus/ack_route.py`, seq 01) — this is what makes the guard live.
  - Dedup-scope schema change IF the bounded-set model were adopted (`scripts/eventbus/schema.sql`, seq 04) — not adopted.
  - SSE delivery-attempt identity (`scripts/eventbus/subscribe_route.py`, seq 03) — not adopted (client-generated key).
  - Tests (seq 05/06), contract doc (seq 07), ADR close (seq 08).

## Assumptions

- UNK-03 recommended = latest-key-only: the single column `consumer_last_nack_attempt` is sufficient; no schema change. The current guard already compares the incoming key against that one remembered key.
- UNK-02 = client-generated stable key: the route passes the caller key unchanged (seq 01); `subscribe_route.py` needs no SSE delivery-attempt field.
- The `consumer_id=None` path is unreachable via the `/nack` route (which requires `consumer_id`); it survives only for direct repository calls in `tests/eventbus/test_eventbus_ack_nack.py`.
- DLQ promotion stays gated on the per-consumer failure count (`INV-13`); this row changes only the key bookkeeping, not promotion.
- Column constants (`_COL_CONSUMER_LAST_NACK_ATTEMPT`, `_COL_CONSUMER_DELIVERY_FAILURE_COUNT`, `_COL_DLQ_AT`, `_COL_EVENT_ID`) live in `scripts/eventbus/_constants.py` and are imported by `nack_event()`.

## Design decisions

- **Latest-key-only (no change).** The recommended UNK-03 model matches the current guard: compare the incoming `last_nack_attempt` against the single remembered `consumer_last_nack_attempt`. No new store, no `user_version` bump. The guard at delivery_repo.py:86-108 is retained as-is; it becomes live once seq 01 passes the caller key.
- **Internalize `consumer_id=None` (`REQ-007`, option a).** Keep the branch but annotate it as internal-only (unreachable via the route). Lower risk than removal, which would force updates to the 3 direct-repo tests.

## Alternatives considered

- **Remove the `consumer_id=None` path (`REQ-007`, option b):** delete the branch and update the direct-repo tests to supply a `consumer_id`. Adopted only if the owner prefers a stricter signature; higher risk.
- **Bounded set of recent keys (UNK-03 option 2):** remember the last K keys per `(consumer_id, event_id)` — requires a new store and a `user_version` bump (schema.sql, seq 04). Rejected as default; kept as a documented branch.

## Implementation

### Target file

`scripts/eventbus/delivery_repo.py`

### Procedure

1. Verify the dedup scope is latest-key-only: the guard at delivery_repo.py:86-108 compares `last_attempt[_COL_CONSUMER_LAST_NACK_ATTEMPT] == last_nack_attempt`. Under the recommended model this is correct — leave the comparison unchanged.
2. Internalize the `consumer_id=None` path: annotate the `consumer_id: str | None = None` parameter and the two `if consumer_id is not None:` blocks (delivery_repo.py:75, :114) as internal-only, since the `/nack` route always supplies `consumer_id`.
3. Run the validation sequence.

### Method

Current `nack_event()` (delivery_repo.py:37-143) accepts `consumer_id: str | None = None` (delivery_repo.py:40) and `last_nack_attempt: str | None = None` (delivery_repo.py:41, the `REQ-001` idempotency key). The dedup guard (delivery_repo.py:86-108) returns the current count without incrementing when the stored `consumer_last_nack_attempt` equals the incoming key; otherwise the update block (delivery_repo.py:114-122) increments `consumer_delivery_failure_count` and stores the new key. When `consumer_id is None`, both the ack/idempotency checks (delivery_repo.py:75) and the update block (delivery_repo.py:114) are skipped, so the function commits and returns `NackResult("ok")` (delivery_repo.py:140) — the internal-only path.

```python
# delivery_repo.py — nack_event() signature (edit existing signature comment)
def nack_event(
    conn: sqlite3.Connection,
    event_id: str,
    consumer_id: str | None = None,  # internal-only: the /nack route always supplies consumer_id
    last_nack_attempt: str | None = None,  # REQ-001: idempotency key for NACK
) -> NackResult:
    ...
```

```python
# delivery_repo.py — dedup guard is latest-key-only (UNCHANGED under recommended UNK-03)
# delivery_repo.py:86-108 — compares the incoming key against the single remembered key
last_attempt = conn.execute(
    f"SELECT {_COL_CONSUMER_LAST_NACK_ATTEMPT} FROM consumer_delivery "
    f"WHERE consumer_id = ? AND event_id = ?",
    (consumer_id, event_id),
).fetchone()
if (
    last_attempt
    and last_attempt[_COL_CONSUMER_LAST_NACK_ATTEMPT] == last_nack_attempt
):
    # Idempotent: return current counts without incrementing
    ...
```

### Details

- **`REQ-003` (retry does not increment):** the guard at delivery_repo.py:86-108 deduplicates a repeat of the same attempt key; a distinct key falls through to the increment at delivery_repo.py:114-122. This is already the current behavior and is correct under latest-key-only.
- **`REQ-004` / UNK-03 (dedup scope):** latest-key-only is the current and recommended model — the single column `consumer_last_nack_attempt` (schema.sql:27) is compared; no schema change (seq 04 stays unmodified).
- **`REQ-007` (`consumer_id=None`):** the branch is retained and annotated as internal-only. The route requires `consumer_id`, so this path is exercised only by direct repository calls in `tests/eventbus/test_eventbus_ack_nack.py`.
- **Guard becomes live via seq 01:** the dead-key problem (per-request UUID) is fixed in `scripts/eventbus/ack_route.py`; this row's logic is unchanged, but it now receives a stable caller key instead of a fresh per-request UUID.
- **Preserve `INV-13`:** DLQ promotion is driven by `consumer_delivery_failure_count` via `is_promotable`/`promote_single` (`scripts/eventbus/dlq.py`); this row does not touch promotion.

## Compatibility considerations

- No public-contract change: `nack_event()`'s signature is unchanged (the `consumer_id=None` default is retained). The dedup semantics are unchanged from the current (documented) behavior.
- The `/nack` route's new mandatory key (seq 01) is what drives the dedup; this row alone introduces no external contract change.

## Security considerations

- No new credentials or secrets. The dedup comparison is a plain string equality on a caller-supplied key; no injection surface beyond the existing parameterized queries (column names come from module-level constants).

## Rollback considerations

- Revert the `delivery_repo.py` edit (`git checkout scripts/eventbus/delivery_repo.py`) restores the prior state. Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `nack_event()` dedup | Unit: same key repeat = no-op, distinct key = +1, boundary at `max_retry - 1` | `uv run pytest tests/eventbus/test_eventbus_ack_nack.py` | Same-key repeat = no-op; distinct = +1; no DLQ acceleration |
| `consumer_id=None` path retained | Unit: direct repo call with `consumer_id=None` still returns `NackResult("ok")` | `uv run pytest tests/eventbus/test_eventbus_ack_nack.py` | Existing no-consumer-id test still passes |
| `delivery_repo.py` static | Complexity/dead code/security | `uv run radon cc scripts/eventbus/delivery_repo.py`; `uv run vulture scripts/eventbus/`; `uv run bandit scripts/eventbus/ -c pyproject.toml` | `nack_event` complexity ≤ C(12); bandit/vulture clean |
| Import boundary | Architecture | `PYTHONPATH=scripts uv run lint-imports` | `eventbus-is-isolated` KEPT |

## Completion criteria

- The dedup guard at delivery_repo.py:86-108 remains latest-key-only and compares the incoming `last_nack_attempt` against the single remembered key.
- The `consumer_id=None` path is annotated as internal-only (unreachable via the route).
- ruff, mypy, bandit, vulture, lint-imports pass; `test_eventbus_ack_nack.py` asserts same-key no-op and distinct-key +1.

## Out of Scope

- Route key source + keyless handling (`scripts/eventbus/ack_route.py`, seq 01).
- Dedup-scope schema change (`scripts/eventbus/schema.sql`, seq 04) — not adopted (latest-key-only).
- SSE delivery-attempt identity (`scripts/eventbus/subscribe_route.py`, seq 03) — not adopted.
- Tests (seq 05/06), contract doc (seq 07), ADR close (seq 08).
- `REQ-007` option b (removal) — recorded, not implemented here.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm latest-key-only dedup scope (current guard unchanged); internalize `consumer_id=None` path as internal-only (`REQ-007`) | Pending | — | — | Latest-key-only is the recommended default (recorded); guard becomes live via seq 01 |
| 2 | Add/update tests per Validation plan | Pending | — | — | Repo-level idempotency tests authored in seq 05 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003`, `REQ-004`, `REQ-007`
- **Source issue**: `issues/20261023-154326_eventbus005_nack-idempotency-retries.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-120857_eventbus005_nack-idempotency-retries.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-203128
- **Related target files**: `scripts/eventbus/delivery_repo.py`
