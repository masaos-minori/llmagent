## Goal
- Fix deploy/init_db.sh to use external schema.sql instead of inline DDL for Event Bus DB

## Findings
- `deploy/init_db.sh` had inline DDL heredoc for Event Bus DB creation — should reference `schema.sql` as canonical source
- `scripts/eventbus/schema.sql` already exists with all required tables and indexes ✓
- No existing `EVENTBUS_SCHEMA` variable or existence check in init_db.sh

## Changes Made
1. Added `EVENTBUS_SCHEMA="${DEPLOY_SCRIPTS}/eventbus/schema.sql"` variable after L12
2. Added schema.sql existence check (L24-L29) with error message and exit 1 if missing — same pattern as create_schema.py check
3. Replaced inline DDL heredoc (L46-L67) with `sqlite3 "${EVENTBUS_DB}" ".read ${EVENTBUS_SCHEMA}"` (L54)

## Validation
- `bash -n deploy/init_db.sh` → Syntax OK ✓

## Conclusion
Code change applied. Schema.sql is the canonical source for Event Bus DB schema.
