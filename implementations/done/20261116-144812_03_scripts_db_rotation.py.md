## Goal

Route the rotation archive destination name through `resolve_unique_path` so a same-second rotation no longer silently overwrites an existing archive (REQ-004, AC-6).

## Scope
**Release unit**: collision-safe-naming

- In scope: one name-construction line in `_archive_db_file` and its `db.config` import.
- Out of scope: adding any prune/retention logic here (that is `maintenance.py`, row 1); the archive/verify/backup flow is otherwise unchanged.

## Assumptions
- Anchors re-verified 2026-11-16. `ts = format_timestamp()` at `rotation.py:47`, `dest = dest_dir / f"{db_path.stem}_{ts}{db_path.suffix}"` at `:48`, then `sqlite3.connect(str(dest))` at `:50-51`; `_archive_db_file` (118-line module) has no existing prune function. `db.config` is already imported for `build_db_config`/`format_timestamp` at `:10`.
- `resolve_unique_path` is created by the row-02 procedure of this plan.

## Design decisions
- Wrap the already-built `dest` candidate, after the timestamp is formatted, so name ordering (retention sweeps sort by `mtime`, not name) is unaffected.

## Alternatives considered
- N/A: single-site wrap; the uniquifier itself is decided in row 02.

## Implementation
### Target file
`scripts/db/rotation.py`

### Procedure
1. Extend the `from db.config import build_db_config, format_timestamp` line (`:10`) to also import `resolve_unique_path`.
2. Wrap the `dest` construction at `:48`: `dest = resolve_unique_path(dest_dir / f"{db_path.stem}_{ts}{db_path.suffix}")` before `sqlite3.connect` at `:50`.

### Method
- No other line changes; `_verify_archive`, `backup`, size logging, and the return value all use the uniquified `dest` automatically.

### Details
- Same-layer import (`db.rotation` → `db.config`); confirm `lint-imports` stays green.

## Compatibility considerations
- Existing same-second archives now get a `_2`/`_3` suffix instead of being overwritten; no existing archive filename changes when there is no collision.

## Security considerations
- N/A: no deletion; name selection only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/db/test_db_maintenance.py -v` (rotation same-second collision test, row 09); `uv run ruff check`, basedpyright (CI form), `uv run lint-imports`.

## Completion criteria
- Two rotations landing in the same second produce two distinct archive files (`{stem}_{ts}{suffix}` and `{stem}_{ts}_2{suffix}`); the backup API never opens an existing path.

## Out of Scope
- Retention of these archives (row 1 sweep).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Import `resolve_unique_path` and wrap `dest` | Completed | 20261116-183515 | 20261116-184426 | import extended; dest wrapped at :48 import extended; dest wrapped; same-second collision test owned by row 09 |
| 2 | Add collision test per Validation plan (see row 09) | Completed | 20261116-195856 | 20261116-195856 | collision test delivered in row 09 (TestRotationSameSecondCollision) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261116-195856 | 20261116-195856 | full suite green; diff-cover 97% >= 90 (rotation.py 100%) |
| 4 | Update docs only if in scope (see row 11) | Completed | 20261116-195856 | 20261116-195856 | no docs change owned; covered by row 11 |

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
- **Requirement ID**: REQ-004 (route the rotation `dest` name through the uniquifier)
- **Source issue**: issues/20261114-092857_dbreview008_artifact-retention-gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-054021_dbreview008_artifact-retention-gaps.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-144812
- **Related target files**: `scripts/db/rotation.py`