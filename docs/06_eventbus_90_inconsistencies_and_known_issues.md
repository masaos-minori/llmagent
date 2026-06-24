# Event Bus: Known Inconsistencies and Issues

## Schema vs implementation differences

| Field | Schema definition | Runtime behavior | Status |
|---|---|---|---|
| `acked_at` | TEXT | Never set by any code path | Reserved/unused — documented in schema.sql comment |
| `retry_count` | INTEGER DEFAULT 0 | Incremented only on DLQ requeue; not incremented during normal delivery | By design |
| `/subscribe` | SSE endpoint | Polling-based internally (not push) | By design; documented |

## Unconfirmed items (Needs Confirmation)

| Item | How to confirm |
|---|---|
| `/health` HTTP status on degraded state (200 vs 503) | Confirm with operational requirements |
| FastAPI thread pool worker usage | Confirm from startup configuration |
