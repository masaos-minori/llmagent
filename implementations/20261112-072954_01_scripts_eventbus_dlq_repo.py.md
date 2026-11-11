## Goal

Add one read-only repository function that counts the terminal-failed `dlq_outbox` rows, so `/health` can report how many outbox generations reached a terminal `failed` state (`REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- A terminal-failed row is any `dlq_outbox` row with `status = 'failed'` (schema CHECK values: `pending`, `done`, `failed`); the count is a gauge, not a per-event list.
- The `status` column carries an index in `scripts/eventbus/schema.sql`, so `WHERE status = 'failed'` is an indexed lookup, not a table scan — the count adds negligible lock time under `run_with_db_lock` (resolves UNK-06).
- The function is pure and side-effect free: it takes a connection and returns an int, matching the existing `get_outbox_state` / `done_outbox_event_ids` signatures. It must not open its own connection or commit.
- `scripts/eventbus/_constants.py` owns the `dlq_outbox` status strings; reuse the existing status literal `'failed'` rather than introducing a new constant, so the count and the promotion path agree on the terminal value.

## Design decisions
- Name the function `count_failed_outbox(db)` (new) and place it immediately after `done_outbox_event_ids`, grouped with the other read-only `dlq_outbox` selectors, so callers and readers find it beside its peers.
- Return a plain `int` (row count), not a `sqlite3.Row`, because the caller only needs the number; cast the aggregate column explicitly.

## Alternatives considered
- Returning a dict of `{status: count}`: rejected — `/health` needs only the terminal-failed gauge, and a narrower return keeps the query and the route simple.
- Counting in `health_route.py` directly: rejected — `dlq_repo` is the single owner of `dlq_outbox` reads; the route-to-repository direction (`dlq_route`, `ack_route` already use `dlq_repo`) must hold.

## Implementation
### Target file
`scripts/eventbus/dlq_repo.py`

### Procedure
1. Open `scripts/eventbus/dlq_repo.py` and locate `done_outbox_event_ids` (ends around line 218).
2. Add `count_failed_outbox` (new) directly after it, before the next top-level blank-line boundary.
3. Keep the module imports unchanged (the query uses only the `'failed'` literal and `COUNT(*)`).
4. Run `uv run python tools/stale_detector.py` on this procedure before executing, and re-run after.

### Method
```python
def count_failed_outbox(db: sqlite3.Connection) -> int:
    """Return the number of dlq_outbox rows in the terminal 'failed' status.

    Read-only, indexed on the status column; safe to call under run_with_db_lock.
    """
    row = db.execute(
        "SELECT COUNT(*) FROM dlq_outbox WHERE status = 'failed'"
    ).fetchone()
    return int(row[0])
```

### Details
- Signature mirrors `done_outbox_event_ids(db)` and `get_outbox_state(db)` — a single `sqlite3.Connection`, no `now`/`event_id` arguments, no commit.
- The predicate reuses the string literal `'failed'` that `dlq.py` `promote_single()` writes as the terminal status; if `_constants.py` ever gains a named constant for that terminal status, bind to it here and in `dlq.py` together so the two never diverge.
- `int(row[0])` unwraps the single-column `COUNT(*)` result; an empty table returns `0`, never `None`.
- No new import, dataclass, or module-level constant; the function is self-contained.

## Compatibility considerations
- Additive only: no existing symbol, signature, or import changes. Callers of `insert_outbox_row`, `get_outbox_state`, `done_outbox_event_ids`, etc. are untouched.
- `scripts/eventbus/app.py` (`process_outbox`) will call the new function in a sibling procedure; until then the function is unused, which is fine for a repository selector.

## Security considerations
- Read-only `SELECT`; no write, no parameter that reaches DDL. The single `?`-less literal `'failed'` is a compile-time constant, so there is no injection surface.

## Rollback considerations
- N/A: revert the commit; the function is isolated and referenced nowhere else until the `/health` wiring lands.

## Validation plan
- `uv run ruff format scripts/eventbus/dlq_repo.py`, `uv run ruff check scripts/eventbus/dlq_repo.py` — clean.
- `uv run mypy scripts/eventbus/dlq_repo.py` — passes (explicit `int` return).
- `uv run lint-imports` — no new import crosses the `eventbus-is-isolated` boundary.
- `uv run python tools/check_module_size.py` — module stays under the size gate.
- `uv run pytest tests/eventbus -v` — the `test_eventbus_health.py` companion asserts the count appears in `/health` (added by the sibling procedure); existing outbox tests still pass.

## Completion criteria
- `count_failed_outbox(db)` (new) exists in `dlq_repo.py`, returns an `int`, filters `status = 'failed'` on the indexed column, and contains no write path or new import.
- `ruff format`, `ruff check`, `mypy`, and `lint-imports` pass; `check_module_size.py` passes.

## Out of Scope
- Calling `count_failed_outbox` (new) from `app.py`/`health_route.py` — that is the sibling procedure for `scripts/eventbus/app.py` and `scripts/eventbus/health_route.py`.
- Any schema change to `dlq_outbox` or its index (`schema.sql` is read-only for this Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `count_failed_outbox(db)` (new) to `dlq_repo.py` (REQ-005) | Pending | — | — | |
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
- **Requirement ID**: `REQ-005` — add a read-only function counting terminal-failed `dlq_outbox` rows for `/health`
- **Source issue**: issues/20261109-113152_adrrev014_eventbus-spec-gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-103238_adrrev014_eventbus-spec-gaps.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-072954
- **Related target files**: `scripts/eventbus/dlq_repo.py`
