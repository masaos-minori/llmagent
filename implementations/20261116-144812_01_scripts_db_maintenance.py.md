## Goal

Add an ArtifactRetentionConfig dataclass and a purge_archive_artifacts() four-sweep entry point to `scripts/db/maintenance.py`, bounded by the maintainer defaults, following the already-landed 006 mode contract and 007 value semantics. This is the retention half of Plan 008 (REQ-001, REQ-002).

## Scope
**Release unit**: retention-sweeps-and-drill-lifecycle

- In scope: one new config dataclass, one new public sweep function, four internal sweep helpers, one module constant, and the weekly cadence table line in the module docstring.
- Out of scope: changing `purge_corrupt_archives` (its scope, tests, and docstring stay untouched), scheduler wiring (operator-side).

## Assumptions
- Anchors re-verified 2026-11-16 against the git repo (the deployed `/opt/llm` tree is not the target). `purge_corrupt_archives` is at `maintenance.py:404-449` (rag/session only at `:426`, pattern at `:429`); reusable helpers `_delete_corrupt_archives_by_age` at `:352-374` and `_delete_corrupt_archives_beyond_limit` at `:377-401`; cadence table at `:11-17`; reusable value guards `_retention_guard` at `:99` and `_non_negative_int` at `:110`.
- Sweep age uses file/directory `mtime` (the existing corrupt helpers do the same, `:362` / `:387-388`).
- `drill_dir` is `<archive_dir>/drills` (derived from `rotation._resolve_archive_dir()`; a custom `--drill-dir` is not swept) — UNK-02.
- Most-recent-never-deleted is applied per source database stem, matching `purge_corrupt_archives` ("applied independently per source database", `:410`).

## Design decisions
- New entry point, not a broadened `purge_corrupt_archives`: purge_archive_artifacts is a sibling sweep for the remaining artifact classes so the documented corrupt contract (referenced by plans 006/007) stays intact.
- Reuse the two helper shapes (age rule then count rule, most-recent protected) via pattern-parameterized sweeps rather than duplicating glob-age-count logic; the age rule gets an explicit `min_keep=1` guard for the archives and quarantine classes so the newest artifact survives even when older than the age limit.
- 006 mode contract: `STRICT` raises; `BEST_EFFORT` returns `MaintenanceResult(success=False)` with partial counts; config-load and negative-value `ValueError`s propagate in both modes.

## Alternatives considered
- Extending `purge_corrupt_archives` — rejected: it would change a documented contract three other plans reference.

## Implementation
### Target file
`scripts/db/maintenance.py`

### Procedure
1. Add `ArtifactRetentionConfig` (new) as a frozen dataclass beside `CorruptArchiveRetentionConfig` (`:144-170`), fields `archive_max_files=14`, `archive_max_age_days=30`, `drill_artifact_max_files=14`, `drill_artifact_max_age_days=30`, `quarantine_max_files=10`, `quarantine_max_age_days=90`; `from_config()` reads the six `agent.toml` keys through `_non_negative_int` (007 semantics).
2. Add the module constant `_STALE_WORK_FILE_MAX_AGE_SECONDS` (new), value 86400.
3. Add four sweep helpers (new) mirroring `_delete_corrupt_archives_by_age`/`_delete_corrupt_archives_beyond_limit`, each pattern-parameterized and most-recent-protected.
4. Add `purge_archive_artifacts` (new) returning `MaintenanceResult(action="purge_archive_artifacts")` with per-class `data` counts; signature `purge_archive_artifacts(cfg=None, mode=MaintenanceMode.STRICT)`.
5. Add the `Weekly : purge_archive_artifacts()` line to the module-docstring cadence table (`:11-17`).

### Method
- purge_archive_artifacts calls, in order, the four sweeps below and aggregates counts:
  1. archives in `rotation._resolve_archive_dir()`: glob `{stem}_*{suffix}` per domain (rag/session/workflow) excluding `{stem}_corrupt_*` (safety guard; corrupt files live in the DB dir and belong to `purge_corrupt_archives`); age 30d (min_keep=1) then count 14.
  2. drill JSON in `<archive_dir>/drills`: glob `{domain}_*.json` per domain; age 30d then count 14.
  3. quarantine directories in each domain DB dir: full-name regex `^{stem}_sidecar_quarantine_[0-9_]*$`, `is_dir` only, age 90d (min_keep=1) then count 10, `shutil.rmtree(..., ignore_errors=False)` only after the full-name match.
  4. stale work leftovers: `{stem}.tmp_*{suffix}` files in DB dirs and `*_restored{suffix}` files in the drills dir whose `mtime` is older than _STALE_WORK_FILE_MAX_AGE_SECONDS; younger ones untouched.
- Resolve the archive dir via `rotation._resolve_archive_dir()`; add `from db.rotation import _resolve_archive_dir` only if not already present (it is not currently imported here) — verify before adding, per the import-layer contract in `skills/DESIGN.md`.

### Details
- Import additions expected: `re` (stdlib, for the quarantine regex) and `shutil` (stdlib, for `rmtree`). Confirm `lint-imports` stays green.
- Do not alter `RetentionConfig`, `CorruptArchiveRetentionConfig`, `_retention_guard`, `_non_negative_int`, `_handle_maintenance_error`, or `purge_corrupt_archives`.

## Compatibility considerations
- Purely additive to `maintenance.py`; no existing function signature or return shape changes. Existing 006/007 landed shapes must be re-read before appending.

## Security considerations
- The quarantine sweep is the only recursive delete: guard with a full-name regex (`re.fullmatch`), `is_dir` check, per-source-DB most-recent protection, and `ignore_errors=False` so `STRICT` surfaces real failures. Tests must assert a non-matching directory and stray live files are untouched (AC-4).

## Rollback considerations
- Revert the single commit; the entry point has no in-repo caller, so no runtime callers to unwind.

## Validation plan
- `uv run pytest tests/db/test_db_maintenance.py -v` (config-boundary and four-sweep matrix tests are specified in the row-09 procedure document).
- `uv run ruff check`, `uv run bandit -ll scripts/`, `uv run lint-imports`, basedpyright (CI form).

## Completion criteria
- ArtifactRetentionConfig and purge_archive_artifacts exist and are exercised by the sweep matrix; age-then-count, most-recent-never-deleted, `_corrupt_`/non-matching exclusion, and the 1-day stale rule each hold; the mode matrix matches 006.

## Out of Scope
- Production scheduling and adding the keys to the deployed `agent.toml` (WI-008-1, operator-side).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add config class, constant, sweeps, cadence line | Pending | — | — | |
| 2 | Add or update tests per Validation plan (see row 09) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update `db_06` cadence/keys docs (see row 11) | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (bounded retention config), REQ-002 (four-sweep entry point)
- **Source issue**: issues/20261114-092857_dbreview008_artifact-retention-gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-054021_dbreview008_artifact-retention-gaps.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-144812
- **Related target files**: `scripts/db/maintenance.py`
