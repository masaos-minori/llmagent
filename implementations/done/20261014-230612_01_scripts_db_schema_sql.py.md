## Goal

Persist the `/undo` compression boundary (`sessions.undo_floor_message_id`) in `session.sqlite` so that conversation turns existing at the last compression cannot be undone, while turns added after compression remain undoable, and the boundary survives `/session load`.

## Scope

Only the `sessions` table DDL string inside `_SESSION_SCHEMA_TEMPLATE` in `scripts/db/schema_sql.py`. The column value is populated atomically by `SessionMessageRepository.replace_messages()` (see row 02) and read back on restore (see row 10). This document names exactly one target file.

## Assumptions

- Recreation approach is confirmed (user, 2026-10-14); no migration path is required.
- `message_id` is `INTEGER PRIMARY KEY AUTOINCREMENT`; the boundary is a row ID, not a history index.
- `undo_floor_message_id = 0` means "never compressed" (no boundary).
- No existing code references this column yet.

## Design decisions

- Add the column inside the existing `CREATE TABLE IF NOT EXISTS sessions (...)` block so the schema stays a single self-contained template.
- `INTEGER NOT NULL DEFAULT 0` matches the `message_id` row-ID domain and reuses `0` as the "no boundary" sentinel.

## Alternatives considered

N/A: adding one DDL column with a default has no public-contract, persistence-migration, or security impact beyond the new column itself.

## Implementation

### Target file

`scripts/db/schema_sql.py`

### Procedure

Add `undo_floor_message_id` (new) `INTEGER NOT NULL DEFAULT 0` to the `sessions` table DDL inside `_SESSION_SCHEMA_TEMPLATE`.

### Method

Insert the new column line into the `sessions` `CREATE TABLE` block (currently lines 95-99, alongside `session_id`, `created_at`, `title`). Place it after `title`. Column order is cosmetic; the column is referenced by name.

### Details

Current `sessions` DDL (lines 95-99):

```sql
CREATE TABLE IF NOT EXISTS sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    title      TEXT
);
```

After the change the block contains the new column, e.g.:

```sql
CREATE TABLE IF NOT EXISTS sessions (
    session_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at              TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    title                   TEXT,
    undo_floor_message_id   INTEGER NOT NULL DEFAULT 0
);
```

This file only declares the column. The value is written by `replace_messages()` (row 02); do not query or populate it here.

## Compatibility considerations

N/A: a new column with a default does not affect existing rows or queries. Only newly created DBs gain it; existing files are recreated on next schema build.

## Security considerations

N/A: no new attack surface.

## Rollback considerations

Revert the commit that adds the column. No data-loss path exists (the column was never populated before this change).

## Validation plan

Run the schema test with the sandbox config:

```bash
uv run pytest tests/db/test_create_schema.py -p no.cacheprovider
```

Add a `TestCreateSessionSchema` assertion that the generated `sessions` DDL contains `undo_floor_message_id` (new) with `NOT NULL DEFAULT 0`. Also confirm `create_session_schema()` emits the column.

## Completion criteria

`build_session_schema_sql()` / `create_session_schema()` emit a `sessions` table whose DDL contains `undo_floor_message_id INTEGER NOT NULL DEFAULT 0` (new), and `tests/db/test_create_schema.py` passes.

## Out of scope

Migration mechanism, production recreation, data-preservation strategy (deferred to a future schema-change proposal), and any other table.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261015-125706 | 20261015-125706 | Procedure corrected before start: marked undo_floor_message_id (new) per template convention so stale_detector accepts it |
| 2 | Add or update tests per Validation plan | Completed | 20261015-125706 | 20261015-125706 | test_create_schema.py did not assert it; add an assertion for the new column Added test_build_session_schema_emits_undo_floor_column; prior note 'already asserts' was inaccurate |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261015-125706 | 20261015-125706 | ruff format+check, mypy (416 files), bandit, lint-imports, pytest (50 passed) all clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — |  |

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
- **Source issue**: N/A
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-214826_plan.md
- **Source implementation procedure**: N/A
- **Generated at**: 20261014-230612
- **Related target files**: scripts/db/schema_sql.py