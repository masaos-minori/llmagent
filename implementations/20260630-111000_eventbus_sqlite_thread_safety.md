## Goal
- Fix incorrect "single async event loop thread" description in Event Bus persistence docs — DB operations execute in `asyncio.to_thread()` thread pool, serialized by `threading.Lock`.

## Scope
- `docs/06_eventbus_03_persistence_schema_and_replay.md`: fix L7 description of SQLite thread safety model

## Findings

### Code verification
`scripts/eventbus/app.py:L29`: `get_db_lock` imported from `eventbus.db` ✓
`scripts/eventbus/app.py:L100-L102`: DB operations wrapped in `with get_db_lock():` ✓
`scripts/eventbus/app.py:L295-L310`: subscribe replay also uses `get_db_lock()` ✓

All 12 DB operation sites use `with get_db_lock():` ✓

### Docs verification
`docs/06_eventbus_03_persistence_schema_and_replay.md:L7`:
- Current: "FastAPI runs on a single async event loop thread. All DB operations execute on that thread."
- Issue: DB operations are NOT on the event loop thread — they run in `asyncio.to_thread()` thread pool
- Fix: Update to reflect actual implementation

### FastAPI thread pool issue in known issues
- No existing entry for FastAPI thread pool issue in `docs/06_eventbus_90_inconsistencies_and_known_issues.md` ✓ (no change needed)

## Conclusion
Only change needed: fix L7 description in 06_eventbus_03 to reflect actual thread safety model.
