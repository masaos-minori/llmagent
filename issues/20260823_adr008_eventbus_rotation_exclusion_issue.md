# ADR-008: eventbus database excluded from rotation

## Status
Open

## Severity
Medium

## Area
Database Operations

## Related ADR
ADR-008: SQLite 4DB Separation

## Conflicting Source
- **Design**: ADR-008 defines four separate databases: `rag.sqlite`, `session.sqlite`, `workflow.sqlite`, `eventbus.sqlite`
- **Implementation**: `scripts/db/rotation.py:63-69` — `rotate_all_dbs()` only archives three databases (rag, session, workflow), excluding eventbus

## Expected Design
All four databases should be archived by `rotate_all_dbs()`:
```python
def rotate_all_dbs(...) -> tuple[Path, Path, Path, Path]:
    """Archive all four databases; returns (rag, session, workflow, eventbus)"""
```

## Observed Implementation
```python
def rotate_all_dbs(archive_dir: str | Path | None = None) -> tuple[Path, Path, Path]:
    """Archive all three databases (rag, session, workflow); returns (rag_archive_path, session_archive_path, workflow_archive_path)."""
    db_cfg = build_db_config()
    rag_dest = _archive_db_file(Path(db_cfg.rag_db_path), archive_dir)
    ses_dest = rotate_session_db(archive_dir)
    wf_dest = rotate_workflow_db(archive_dir)
    return rag_dest, ses_dest, wf_dest
```

No `rotate_eventbus_db()` function exists anywhere in the codebase.

## Impact
- Eventbus data cannot be rotated/archived through the standard maintenance procedure
- Inconsistent with ADR-008's design intent of treating eventbus as an independent persistence domain
- Recovery procedures that rely on `rotate_all_dbs()` will leave eventbus data unarchived

## Recommended Action
1. Add `rotate_eventbus_db()` function following the same pattern as `rotate_session_db()` and `rotate_workflow_db()`
2. Update `rotate_all_dbs()` to include eventbus: `tuple[Path, Path, Path, Path]`
3. Update docstring to reflect four databases instead of three
4. Add corresponding test coverage

## Owner
Unassigned

## Resolution Target
Next maintenance cycle
