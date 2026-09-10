## Goal
Call the new legacy-offset migration function once, after `open_db()` returns in
`lifespan()`, passing `app.state.config.offsets_dir` (REQ-004). This target file was
not in the source Issue's own Target Files list — discovered during this Plan's Step 3
inspection, since `lifespan()` is the only place both `db_path` (via `open_db()`) and
`offsets_dir` (via `app.state.config`) are available together at startup.

## Scope
In scope: one new function call inside `lifespan()`, immediately after `app.state.db =
open_db(...)`. Out of scope: any other part of `lifespan()` (broker/DLQ-task
initialization, shutdown sequence) or any route handler in this file.

## Assumptions
- `migrate_legacy_offsets(conn, offsets_dir)` (row 03) is synchronous and safe to call
  directly inside the `async def lifespan()` body without `await` or an executor —
  confirm at implementation time whether its file I/O (`.map` file enumeration) is
  significant enough to warrant `run_with_db_lock()` wrapping or an executor hand-off;
  since this runs once at startup before any request is served, blocking here briefly
  does not violate `skills/DESIGN.md` Pythonic safety constraints' async-blocking-I/O
  rule in the same way a per-request handler would.
- `app.state.config.offsets_dir` is populated before this call (confirmed:
  `app.state.config = load_config(...)` runs on the line immediately before `open_db()`).

## Design decisions
Call `migrate_legacy_offsets(app.state.db, app.state.config.offsets_dir)` directly
after `app.state.db = open_db(...)`, before any other startup step that could accept
`/subscribe` traffic (the DLQ task and broker are created after, so no request can
race this migration).

## Alternatives considered
Running the migration lazily on first `/subscribe` request (inside `subscribe_route.py`)
was considered and rejected: it would require a guard against repeated invocation per
request and could race the first real request against the migration itself; running it
once at startup, before the app can accept traffic, is simpler and matches the Plan's
Design section.

## Implementation
### Target file
`scripts/eventbus/app.py`

### Procedure
1. Import `migrate_legacy_offsets` from `eventbus.db` alongside the existing
   `from eventbus.db import open_db` import.
2. Insert the call immediately after `app.state.db = open_db(app.state.config.db_path)`
   inside `lifespan()`.

### Method
Single added line plus one import; no change to `lifespan()`'s control flow, signature,
or the rest of its startup sequence.

### Details
```python
from eventbus.db import migrate_legacy_offsets, open_db

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """FastAPI lifespan: initialize broker/db/lifecycle on startup; clean up on shutdown."""
    app.state.config = load_config(get_config_path())
    app.state.db = open_db(app.state.config.db_path)
    migrate_legacy_offsets(app.state.db, app.state.config.offsets_dir)
    app.state.envelope_schema = orjson.loads(get_schema_path().read_bytes())
    ...
```
The rest of `lifespan()` is unchanged.

## Compatibility considerations
Runs once per process startup; idempotent per row 03's design (`INSERT OR IGNORE`), so
a restart re-running this call against an already-migrated `consumer_offsets` table is
a safe no-op. No change to any route's external contract.

## Security considerations
No new external input; `offsets_dir` is an existing, already-trusted config value, not
user-supplied per-request input.

## Rollback considerations
Revert this file's diff to remove the startup call. Since `migrate_legacy_offsets()`
only ever adds rows (never deletes legacy files or `consumer_offsets` rows), reverting
this call leaves any already-migrated `consumer_offsets` rows in place harmlessly —
they simply go unused again until `subscribe_route.py` (row 05) is also reverted.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_offsets.py -v` (row 07): migration
  idempotency assertions, exercised via the shared `make_eventbus_client()` fixture
  which triggers `lifespan()` on client construction (confirmed via
  `tests/eventbus/eventbus_helpers.py`, a Reference File).
- Manual: start the service twice against the same `db_path`/`offsets_dir` and confirm
  no error and no duplicate/changed rows on the second startup.

## Completion criteria
`migrate_legacy_offsets()` is called exactly once per `lifespan()` invocation, after
`open_db()` and before any route can serve a `/subscribe` request; a second startup
against the same data is a no-op.

## Out of scope
Any change to the DLQ task loop, broker initialization, or shutdown sequence in this
same function.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Import and call `migrate_legacy_offsets()` after `open_db()` in `lifespan()` | Pending | — | — | |
| 2 | Add or update tests per Validation plan (row 07) | Pending | — | — | |
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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260907-125042_eb_h01_transactional_ack_offset_delivery_state.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-094115_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-092106
- **Related target files**: scripts/eventbus/app.py
