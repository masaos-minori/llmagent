# Implementation: Resolve known issues and document adopted execution model

Source plan: `plans/20260625-140641_plan.md` (req #22)

## Goal

Update `docs/06_eventbus_90_inconsistencies_and_known_issues.md` to mark both "Unconfirmed items" as resolved and document the adopted execution model, so the known-issues file reflects the real post-implementation architecture.

## Scope

- Remove the `## Unconfirmed items (Needs Confirmation)` section
- Add a `## Resolved items` section with resolution details and cross-links
- Add an `## Adopted execution model` summary section
- No changes to the `## Schema vs implementation differences` section
- Prerequisite: req #14, #15, #16, #19 implemented

## Assumptions

1. The two unconfirmed items are: `/health` HTTP status, and FastAPI thread pool worker usage
2. `/health` HTTP status: resolved by req #19 — HTTP 200, `status` field carries ok/degraded/unavailable
3. Thread pool usage: resolved by req #14/#16 — `asyncio.to_thread()` + `threading.Lock`
4. The `## Schema vs implementation differences` section (3 rows) remains unchanged

## Implementation

### Target file

`docs/06_eventbus_90_inconsistencies_and_known_issues.md`

### Procedure

1. Remove the `## Unconfirmed items (Needs Confirmation)` section (lines 11-15 approximately)
2. Append `## Resolved items` section
3. Append `## Adopted execution model` section

### Method

Remove the unconfirmed section; append two new sections at the end of the file.

### Details

**Remove (lines 11-15):**
```markdown
## Unconfirmed items (Needs Confirmation)

| Item | How to confirm |
|---|---|
| `/health` HTTP status on degraded state (200 vs 503) | Confirm with operational requirements |
| FastAPI thread pool worker usage | Confirm from startup configuration |
```

**Append:**
```markdown
## Resolved items

| Item | Resolution | Reference |
|---|---|---|
| `/health` HTTP status on degraded state | HTTP 200 maintained. `status` field returns `ok`, `degraded`, or `unavailable`. New fields: `db_latency_ms`, `dlq_last_run_age_s`, `event_count`, `degraded_reasons` | req #19, `docs/06_eventbus_02_http_api_and_runtime.md` |
| FastAPI thread pool worker usage | All DB operations and file I/O are executed via `asyncio.to_thread()`. Shared SQLite connection is protected by a `threading.Lock` (`get_db_lock()` in `db.py`) | req #14, #15, #16, `docs/06_eventbus_03_persistence_schema_and_replay.md` |

## Adopted execution model

As of req #14–#16, the Event Bus uses the following execution model:

| Operation | Execution | Concurrency control |
|---|---|---|
| DB reads/writes | `asyncio.to_thread()` (thread-pool) | `threading.Lock` via `get_db_lock()` |
| JSONL archive write | `asyncio.to_thread()` | No lock needed (append-only, single writer) |
| Offset file write | `asyncio.to_thread()` | No lock needed (per-consumer file) |
| DLQ file write (`_atomic_write`) | `asyncio.to_thread()` via `promote_to_dlq` | Atomic via `os.replace()` |
| SSE poll sleep | `asyncio.sleep()` on event loop | N/A |

The shared SQLite connection (`check_same_thread=False`) is safe because `threading.Lock` ensures only one thread executes a DB operation at a time. WAL mode provides additional protection for concurrent readers.
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Unconfirmed section gone | `grep "Needs Confirmation" docs/06_eventbus_90_inconsistencies_and_known_issues.md` | 0 matches |
| Resolved section present | `grep "## Resolved items" docs/06_eventbus_90_inconsistencies_and_known_issues.md` | 1 match |
| Execution model present | `grep "## Adopted execution model" docs/06_eventbus_90_inconsistencies_and_known_issues.md` | 1 match |
| Schema section untouched | `grep "acked_at" docs/06_eventbus_90_inconsistencies_and_known_issues.md` | Still present |
| Markdown lint | `markdownlint docs/06_eventbus_90_inconsistencies_and_known_issues.md` | 0 errors (if installed) |
