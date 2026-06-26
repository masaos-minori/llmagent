# Event Bus: Known Inconsistencies and Issues

## Schema vs implementation differences

| Field | Schema definition | Runtime behavior | Status |
|---|---|---|---|
| `acked_at` | TEXT | Never set by any code path | Reserved/unused — see inline DDL in deploy/init_db.sh |
| `retry_count` | INTEGER DEFAULT 0 | Incremented only on DLQ requeue; not incremented during normal delivery | By design |
| `/subscribe` | SSE endpoint | Polling-based internally (not push) | By design; documented |

## Resolved Items

| Item | Resolution |
|---|---|
| `/health` HTTP status on degraded state (200 vs 503) | **Resolved** — now returns HTTP 503 for non-ok states (fail-closed) |
| SQLite/JSONL dual read path | **Resolved** — SQLite-only reads; JSONL is write-only |
| Consumer ID collision possibility | **Resolved** — hash-based stable IDs with collision detection |

## Unconfirmed items (Needs Confirmation)

| Item | How to confirm |
|---|---|
| FastAPI thread pool worker usage | Confirm from startup configuration |
