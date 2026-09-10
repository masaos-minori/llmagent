## Goal

Wire the legacy-offset-file migration function (`migrate_legacy_offsets`) into `scripts/eventbus/app.py`'s `lifespan()` right after `open_db()`, so the new `consumer_offsets` table is seeded from existing `offsets_dir` files on every EventBus startup.

## Scope

- Call `migrate_legacy_offsets(app.state.db, app.state.config.offsets_dir)` in `lifespan()` after `app.state.db = open_db(...)`.
- No changes to shutdown/cleanup logic.
- No changes to route handlers.

## Assumptions

- `app.state.db` is set by `open_db()` before the migration call.
- `app.state.config.offsets_dir` is available after `load_config(get_config_path())`.
- The `consumer_offsets` table exists (created by the migration in the related procedure document).

## Design decisions

- **Startup-time migration**: Migrate on every startup, not just once. The `INSERT OR IGNORE` semantics make this safe to re-run.
- **No error handling**: If migration fails, log a warning but don't block startup. The legacy file-based path remains available as a fallback.
- **Minimal integration**: Only add the one-line call; no new configuration fields or flags.

## Alternatives considered

- **One-time migration flag**: Track whether migration has completed using a marker file or database flag. Rejected because `INSERT OR IGNORE` makes repeated runs safe without needing a flag.
- **Background migration task**: Run migration asynchronously after startup. Rejected because the migration is fast (enumerating `.map` files) and blocking startup ensures consistency before any subscriber connects.

## Implementation

### Target file

`scripts/eventbus/app.py`

### Procedure

1. Import `migrate_legacy_offsets` from `eventbus.db`.
2. Call it in `lifespan()` after `app.state.db = open_db(...)`.

### Method

#### Step 1: Update imports

Change lines 26-27:
```python
from eventbus.db import open_db
from eventbus.dlq import sweep_orphans
```

to:
```python
from eventbus.db import migrate_legacy_offsets, open_db
from eventbus.dlq import sweep_orphans
```

#### Step 2: Add migration call in lifespan

Change lines 56-63:
```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """FastAPI lifespan: initialize broker/db/lifecycle on startup; clean up on shutdown."""
    app.state.config = load_config(get_config_path())
    app.state.db = open_db(app.state.config.db_path)
    app.state.envelope_schema = orjson.loads(get_schema_path().read_bytes())
    Path(app.state.config.storage_dir).mkdir(parents=True, exist_ok=True)
    app.state.broker = EventBroker()
    app.state.dlq_task = asyncio.create_task(_dlq_loop(app))
```

to:
```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """FastAPI lifespan: initialize broker/db/lifecycle on startup; clean up on shutdown."""
    app.state.config = load_config(get_config_path())
    app.state.db = open_db(app.state.config.db_path)
    # Migrate legacy offset files into the new consumer_offsets table (idempotent)
    try:
        migrate_legacy_offsets(app.state.db, app.state.config.offsets_dir)
    except Exception:
        logger.exception("failed to migrate legacy offsets")
    app.state.envelope_schema = orjson.loads(get_schema_path().read_bytes())
    Path(app.state.config.storage_dir).mkdir(parents=True, exist_ok=True)
    app.state.broker = EventBroker()
    app.state.dlq_task = asyncio.create_task(_dlq_loop(app))
```

### Details

The key changes are:

1. **Import addition**: `migrate_legacy_offsets` is imported alongside `open_db` from `eventbus.db`.

2. **Migration call placement**: The migration is called immediately after `open_db()` returns, before any routes can be served. This ensures:
   - The database connection is available.
   - The `consumer_offsets` table exists (created by `_migrate()` during `open_db()`).
   - The `offsets_dir` config value is available.

3. **Error handling**: A `try/except` block catches any exceptions from the migration and logs them without blocking startup. This is intentional — if the migration fails, the legacy file-based path remains available as a fallback.

4. **Idempotency**: The `INSERT OR IGNORE` semantics in `migrate_legacy_offsets()` ensure the migration is safe to re-run on every startup.

## Compatibility considerations

- The migration is additive — it does not modify or delete legacy files.
- The legacy file-based offset path remains available as a fallback (see subscribe_route.py procedure document).
- No new configuration fields required.

## Security considerations

- No new authentication or authorization boundaries introduced.
- File enumeration uses the existing `_sanitize_consumer_id()` function for filename safety.
- No user input flows directly into file operations.

## Rollback considerations

- To rollback: remove the import and the migration call.
- The rollback restores the pre-change state where offsets are only read from the file system.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/app.py` | Structural verification | Read file, confirm migration call present | One-line call added after `open_db()` |
| `tests/eventbus/test_eventbus_offsets.py` | Migration idempotency test | `uv run pytest tests/eventbus/test_eventbus_offsets.py -v` | Re-running migration is a no-op; no corruption on failure |

## Completion criteria

- `migrate_legacy_offsets()` is called in `lifespan()` after `open_db()`.
- Error handling wraps the call (logs exception without blocking startup).
- No other code paths modified.

## Out of scope

- Modifying the shutdown path — not affected by this change.
- Adding DDL to schema files — covered by separate procedure documents.
- Modifying route handlers — not affected by this change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add migrate_legacy_offsets import | Completed | — | — | |
| 2 | Wire migration call in lifespan() | Completed | — | — | |
| 3 | Run validation (pytest + structural check) | Completed | — | — | |

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
- **Generated at**: 20260910-161316
- **Related target files**: scripts/eventbus/app.py
