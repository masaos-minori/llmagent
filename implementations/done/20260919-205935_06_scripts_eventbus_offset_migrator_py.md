## Goal

Create `scripts/eventbus/offset_migrator.py` — Legacy offset migration with isolated file I/O per REQ-001, REQ-005. Extracts `migrate_legacy_offsets()` from `db.py`.

## Scope

New file containing legacy offset migration logic with its own file I/O dependencies isolated from database operations.

## Assumptions

- Shared column constants (`_COL_CONSUMER_ID`, `_COL_OFFSET`) imported from `_constants.py`.
- `Path.iterdir()`, `read_text()` used for file I/O.
- `ValueError` sufficient for collision exception.
- `_sanitize_consumer_id()` imported from `eventbus.offsets` (deferred import to avoid circular dependency).

## Design decisions

- Offset migrator owns all legacy offset migration logic.
- File I/O is a completely different concern from database operations; isolating it prevents coupling.
- Deferred import of `_sanitize_consumer_id()` avoids circular import with `eventbus.offsets`.
- Uses `INSERT OR IGNORE` for idempotent migration.

## Alternatives considered

- Keeping everything in `db.py` rejected because file I/O is a completely different concern from database operations.
- Using `os.path` instead of `pathlib.Path` rejected because `pathlib` is more modern and readable.

## Implementation

### Target file

`scripts/eventbus/offset_migrator.py`

### Procedure

Extract legacy offset migration logic from `db.py` into this module.

### Method

1. Import shared column constants from `_constants.py`.
2. Import `_sanitize_consumer_id()` from `eventbus.offsets` (deferred).
3. Implement `migrate_legacy_offsets(conn, offsets_dir)` — migrate legacy file-based offsets.
4. Export public symbols.

### Details

```python
"""Offset migrator: legacy offset migration with isolated file I/O."""

import logging
from pathlib import Path
from sqlite3 import Connection

# Shared column constants
from eventbus._constants import _COL_CONSUMER_ID, _COL_OFFSET

logger = logging.getLogger(__name__)

def migrate_legacy_offsets(
    conn: Connection,
    offsets_dir: str,
) -> list[str]:
    """Migrate legacy file-based offsets into the consumer_offsets table.

    Reads each .map file under offsets_dir, recovers the original consumer_id
    from the .map companion file, reads its offset via read_offset(), and inserts
    a row into consumer_offsets using INSERT OR IGNORE (idempotent).

    For any offset file with no .map companion, falls back to the sanitized
    filename as consumer_id, logging a warning.

    Does NOT delete or modify any legacy files.

    Returns:
        List of consumer_ids that were migrated.
    """
    # Deferred import to avoid circular import with eventbus.offsets
    from eventbus.offsets import _sanitize_consumer_id  # noqa: PLC0415

    migrated: list[str] = []
    dir_path = Path(offsets_dir)

    if not dir_path.exists():
        logger.warning("offsets_dir does not exist: %s", offsets_dir)
        return migrated

    # Collect all legacy files first for collision detection
    legacy_files = sorted(f.name for f in dir_path.iterdir() if f.is_file())

    # Build sanitized name mapping for collision detection (O(n))
    sanitized_names: dict[str, list[str]] = {}
    for fname in legacy_files:
        if fname.endswith(".map"):
            continue
        sanitized = _sanitize_consumer_id(fname.replace(".offset", ""))
        sanitized_names.setdefault(sanitized, []).append(fname)

    # Process each file
    for safe_id in legacy_files:
        if safe_id.endswith(".map"):
            continue
        map_file = dir_path / f"{safe_id}.map"
        try:
            stored_id = map_file.read_text().strip()
            if stored_id:
                consumer_id = stored_id
            else:
                # Empty .map file — fall back to sanitized filename
                consumer_id = _sanitize_consumer_id(safe_id)
                logger.warning(
                    "empty .map file for %s, using sanitized filename as consumer_id",
                    safe_id,
                )
        except FileNotFoundError:
            # No .map companion — use sanitized filename
            sanitized = _sanitize_consumer_id(safe_id)
            if len(sanitized_names[sanitized]) > 1:
                # Collision detected — refuse to proceed
                raise ValueError(
                    f"Collision detected: {sanitized} maps to multiple legacy files: "
                    f"{', '.join(sorted(sanitized_names[sanitized]))}"
                )
            consumer_id = sanitized
            logger.warning(
                "no .map companion for %s, using sanitized filename as consumer_id",
                safe_id,
            )

        # Read directly from the on-disk file rather than via read_offset(),
        # which re-sanitizes its consumer_id argument to build the path
        try:
            offset_val = int((dir_path / safe_id).read_text().strip())
        except (FileNotFoundError, ValueError):
            offset_val = 0
        if offset_val > 0:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO consumer_offsets(consumer_id, offset) VALUES (?, ?)",
                    (consumer_id, offset_val),
                )
                migrated.append(consumer_id)
                logger.debug(
                    "migrated offset: consumer=%s offset=%d",
                    consumer_id,
                    offset_val,
                )
            except Exception as exc:
                logger.warning(
                    "failed to migrate offset for consumer %s: %s",
                    consumer_id,
                    exc,
                )

    return migrated
```

## Compatibility considerations

- Function signature matches existing `db.py` export.
- Return type unchanged: `list[str]`.
- `ValueError` raised for collision detection (same as original).

## Security considerations

- All SQL statements use parameterized queries for values.
- Column names come from module-level constants (not user input) — safe from SQL injection.
- File I/O uses `pathlib.Path` — safe path handling.

## Rollback considerations

- If migration fails, rollback via `conn.rollback()`.
- Keep original `db.py` until full test suite passes.
- Test migration edge cases separately: missing `.map` files, empty `.map` files, collision detection.

## Validation plan

- Run full eventbus test suite: `uv run pytest tests/eventbus/` — 311 collected tests.
- Verify migration path works: create DB with old schema, apply `_migrate()`, confirm new columns exist.
- Verify `migrate_legacy_offsets()` handles edge cases: missing `.map` files, empty `.map` files, collision detection.
- Verify thread-safety preserved: `_db_lock` serialization model unchanged.

## Completion criteria

- `migrate_legacy_offsets()` exists under `scripts/eventbus/offset_migrator.py`.
- All 311 eventbus tests pass.
- No behavioral regression in offset migration.

## Out of scope

- Changing HTTP API surface.
- Adding new database indexes beyond `_migrate()`.
- Migrating from SQLite to another engine.
- Adding connection pooling/async drivers.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create offset_migrator.py with shared constant imports | Pending | — | — | |
| 2 | Implement migrate_legacy_offsets() | Pending | — | — | |
| 3 | Run full eventbus test suite | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-005
- **Source issue**: issues/20260919-160141_refactor_001_eventbus_db_py_refactoring.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-170923_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-205935
- **Related target files**: scripts/eventbus/offset_migrator.py
