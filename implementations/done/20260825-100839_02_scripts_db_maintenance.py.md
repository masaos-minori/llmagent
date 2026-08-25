## Goal
- REQ-010: implement a retention/cleanup policy for the timestamped `*_corrupt_*`
  archive files that `_restore_from_backup()` (in `scripts/db/recovery.py`) creates
  before restoring, following the same pattern as `maintenance.py`'s existing session
  retention logic.

## Scope
- In scope: `scripts/db/maintenance.py` (one new dataclass, two new private helpers,
  one new public function), `scripts/db/__init__.py` (export additions), and two new
  `config/agent.toml` keys.
- Out of scope: `scripts/db/recovery.py` (archive creation side) and
  `scripts/db/rotation.py` (`rotate_*_db()`, a different mechanism) — not touched.

## Assumptions
- Archives are created as `db_path.with_name(f"{stem}_corrupt_{ts}{suffix}")` in the
  same directory as the live DB file (distinct from `sqlite_archive_dir`, which
  `rotation.py::_resolve_archive_dir()` uses).
- `_restore_from_backup()` is only reachable via `recover_corruption()` for
  `target in {"rag", "session"}` (workflow/eventbus are rejected by
  `no_recovery_allowed`), so corrupt archives only ever arise from the `rag`/`session`
  databases.
- Follows the Plan's Risk section guidance: conservative defaults, log every deletion.
- `docs/adr/ADR-011-database-corruption-recovery-safety-boundary.md`'s note that this
  retention policy is not yet defined (Known Issue) documents the same gap; the ADR
  itself is not updated by this change.

## Design decisions
- Mirror the existing `RetentionConfig`/`purge_old_sessions()` shape: add a frozen
  `CorruptArchiveRetentionConfig(max_files: int = 10, max_age_days: int = 30)` with a
  `.from_config()` reusing the existing `_load_agent_config()` helper, reading two new
  `agent.toml` keys: `sqlite_corrupt_archive_max_files` /
  `sqlite_corrupt_archive_max_age_days`.
- Add `purge_corrupt_archives(cfg: CorruptArchiveRetentionConfig | None = None, mode: MaintenanceMode = MaintenanceMode.STRICT) -> MaintenanceResult`, mirroring
  `purge_old_sessions()`'s two-stage (age-based, then count-based) structure via new
  `_delete_corrupt_archives_by_age()` / `_delete_corrupt_archives_beyond_limit()`
  helpers.
- Apply the retention policy independently per source database (rag vs. session):
  mixing both under one count limit could wipe all diagnostic history for one
  database because the other happened to corrupt more recently.
- Sort by `Path.stat().st_mtime`, not by parsing the filename timestamp — avoids
  coupling to `format_timestamp()`'s exact format.
- Scan only the parent directory of `rag_db_path`/`session_db_path` (from
  `build_db_config()`), using a strict per-stem glob (`f"{stem}_corrupt_*{suffix}"`),
  not a broad `*_corrupt_*` pattern.
- Log every deletion via `logger.info()`, matching
  `_delete_sessions_by_age`/`_delete_sessions_beyond_limit`.
- Reuse the existing `_handle_maintenance_error()` for error handling, catching
  `OSError` (filesystem operation) instead of `sqlite3.Error`.

## Alternatives considered
- Reusing the existing `RetentionConfig`/`sqlite_retention_max_sessions`/
  `max_age_days` keys directly — rejected; it would mix two unrelated retention
  concerns (session rows vs. corrupt-archive files) under one setting, preventing
  operators from configuring separate windows.
- A single global count/age limit across rag+session archives — rejected (see Design
  decisions, risk of skewed diagnostic-history loss).
- Deleting old archives immediately inside `_restore_from_backup()` at archive-creation
  time — rejected; mixes the recovery hot path with an unrelated retention concern,
  and contradicts the Plan's Design section ("additive changes to existing functions,
  no new module... alongside the existing session-retention logic in maintenance.py").
- A new module (e.g. `db/archive_retention.py`) — rejected; the Plan explicitly states
  "No new module."

## Implementation
### Target file
`scripts/db/maintenance.py` (plus two lines in `scripts/db/__init__.py`'s
import/`__all__`, and two new keys in `config/agent.toml`)

### Procedure
1. Add `CorruptArchiveRetentionConfig` and its `.from_config()` near the existing
   `RetentionConfig`.
2. Add `_delete_corrupt_archives_by_age()` / `_delete_corrupt_archives_beyond_limit()`
   near `_delete_sessions_by_age`/`_delete_sessions_beyond_limit`.
3. Add `purge_corrupt_archives()` near `purge_old_sessions()`, resolving the scan
   directories via `build_db_config()`.
4. Export `CorruptArchiveRetentionConfig` and `purge_corrupt_archives` from
   `db/__init__.py`.
5. Add a line to the module docstring's "Typical maintenance schedule" comment for
   the new function.
6. Add `sqlite_corrupt_archive_max_files = 10` / `sqlite_corrupt_archive_max_age_days
   = 30` to `config/agent.toml` near the existing `sqlite_retention_*`/
   `sqlite_archive_dir` keys.

### Method
- `CorruptArchiveRetentionConfig.from_config()`: `cfg.get("sqlite_corrupt_archive_max_files", 10)` / `cfg.get("sqlite_corrupt_archive_max_age_days", 30)`.
- **Adversarial verification note**: the original design (globbing once and passing
  the same in-memory path list to both age-based and count-based helpers) would let
  the count-based step operate on a stale list — either double-deleting a path the
  age-based step already removed, or miscounting `max_files` against files that no
  longer exist. `purge_old_sessions()` avoids this by having
  `_delete_sessions_beyond_limit()` re-query the DB fresh (reflecting the prior
  `DELETE`). The filesystem equivalent is for each helper to `glob()` fresh itself,
  not receive a pre-globbed list — revised below.
- `_delete_corrupt_archives_by_age(archive_dir: Path, pattern: str, max_age_days: int) -> int`: `max_age_days <= 0` disables age-based deletion (matching
  `RetentionConfig`'s existing convention); otherwise glob fresh and delete files
  whose `time.time() - path.stat().st_mtime` exceeds the threshold, logging the
  count.
- `_delete_corrupt_archives_beyond_limit(archive_dir: Path, pattern: str, max_files: int) -> int`: glob fresh (reflecting any deletions the age-based step already made),
  sort by mtime descending, delete anything beyond `max_files`, logging the count.
- `purge_corrupt_archives()`: for each of `db_cfg.rag_db_path`/`db_cfg.session_db_path`
  (from `build_db_config()`), compute `archive_dir = db_path.parent` and
  `pattern = f"{db_path.stem}_corrupt_*{db_path.suffix}"`, call both helpers in
  order (age-based, then count-based) and sum their results across both databases,
  and return `MaintenanceResult(success=True, action="purge_corrupt_archives", mode=mode, data={...})`; delegate `OSError` to
  `_handle_maintenance_error(e, "purge_corrupt_archives", mode, extra_data={...})`.

### Details
- Both new `agent.toml` keys are optional (`cfg.get(key, default)` with defaults).
- `max_age_days=0` disables age-based deletion, matching `RetentionConfig`'s existing
  convention.
- `purge_corrupt_archives()` takes no `db: SQLiteHelper` argument (filesystem-only,
  no DB connection needed), unlike `purge_old_sessions(db, cfg, mode)`.

## Compatibility considerations
- Fully additive: new dataclass, two new private helpers, one new public function,
  new exports, one new docstring line, two new optional `agent.toml` keys. No
  existing function's signature or behavior changes.
- Both new `agent.toml` keys are optional with defaults.
- `purge_corrupt_archives()` is not auto-wired to any scheduler/cron/recovery path
  (this repository has no existing auto-invocation mechanism for
  `purge_old_sessions()`/`rotate_all_dbs()` either, so this matches the existing
  pattern) — an operator or a future job must call it explicitly.

## Security considerations
- Deletion decisions rely only on glob patterns and mtime; filenames are never
  embedded in a shell command or SQL string (pure `pathlib`/`os` filesystem
  operations) — no injection surface.
- Bounded, logged deletion mitigates the Plan's "unbounded disk growth" risk without
  adding any new privileged path (uses only the filesystem permissions the process
  already has on the DB directory).
- The Plan's "deleting evidence during an active incident" risk is mitigated by
  conservative defaults, the ability to disable age-based deletion (`max_age_days=0`),
  and an INFO log line for every deletion (timestamps remain traceable in logs after
  deletion).

## Rollback considerations
- Additive changes to `maintenance.py`/`__init__.py`/`agent.toml` only; revert via a
  single commit revert. No schema or persistent-data migration.
- No existing call path invokes `purge_corrupt_archives()`, so rolling back (or
  deploying without configuring the new keys) simply preserves today's behavior
  (unbounded accumulation) — low blast radius either way.

## Validation plan
- Add a `TestPurgeCorruptArchives` class to `tests/db/test_db_maintenance.py`,
  creating dummy `*_corrupt_*` files under `tmp_path` and controlling mtime via
  `os.utime()` (mirroring how `TestPurgeOldSessions` controls `created_at`).
- Cases: age-based deletion (beyond `max_age_days`), count-based deletion (beyond
  `max_files`), boundary values (at/above/below, mirroring
  `test_boundary_at_max_sessions`), `max_age_days=0` disabling age-based deletion,
  and `MaintenanceMode.BEST_EFFORT`/`STRICT` behavior differences on `OSError`
  (patching `Path.unlink`, mirroring `TestMaintenanceMode`).
- `uv run pytest tests/db/test_db_maintenance.py -v` (per the Plan's Validation plan
  row).
- Full regression: `uv run pytest` and `uv run pre-commit run --all-files`.

## Out of scope
- Auto-wiring `purge_corrupt_archives()` to a scheduler/cron — no existing mechanism
  for this in the repository today; file as a future issue if needed.
- Changing `_restore_from_backup()`'s archive naming/location — not required by
  REQ-010.
- REQ-001/REQ-002 — separate document for `scripts/db/recovery.py`.
- Exposing `purge_corrupt_archives()` via `DbMaintenanceService`/a `cmd_db` CLI
  command — not required by REQ-010's Acceptance criterion.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260825-110500 | 20260825-111200 | Adversarial verification found the originally-planned single-glob-reused-by-both-helpers design was stale-list-prone; revised to per-helper fresh `glob()`, matching `purge_old_sessions()`'s fresh-requery pattern |
| 2 | Add or update tests per Validation plan | Completed | 20260825-111200 | 20260825-111700 | Added `TestPurgeCorruptArchives` (8 cases) to `tests/db/test_db_maintenance.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260825-111700 | 20260825-112200 | ruff/mypy/lint-imports/bandit clean; diff-cover 95% (2 uncovered lines are `.from_config()`'s config-loading branch, consistent with `RetentionConfig.from_config()` also being untested); targeted suite: 2 pre-existing failures only (unchanged from doc01) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260825-112200 | 20260825-112300 | No update needed: neither `90_shared_90_inconsistencies_and_known_issues.md` nor `90_shared_05_01_...md` (the two routing.md-mapped DB/Shared docs) has an existing entry for corrupt-archive retention to correct — this is new capability, not a documented gap being closed |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `scripts/db/maintenance.py` change | 1 | Code Change | Completed | — | — |
| `scripts/db/__init__.py` export update | 1 | Code Change | Completed | — | — |
| `config/agent.toml` new keys | 1 | Code Change | Completed | — | — |
| `tests/db/test_db_maintenance.py::TestPurgeCorruptArchives` | 2 | Test | Completed | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: issues/20260821_h3-h4-m1-followup-implementation-tasks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-095817_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-100839
- **Related target files**: scripts/db/maintenance.py
