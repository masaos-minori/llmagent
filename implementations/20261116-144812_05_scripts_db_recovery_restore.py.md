## Goal

Route the quarantined sidecar file name through `resolve_unique_path` so two same-second quarantines of the same sidecar never overwrite each other's forensic copy, and (per the maintainer-approved 2026-11-16 Plan amendment) host the new `build_restore_paths()` helper that holds the three recovery working-file name constructions with collision-safe naming — the shape that keeps `recovery.py` under the 24576 B module-size gate (REQ-004, AC-6).

## Scope
**Release unit**: collision-safe-naming

- In scope: the `quarantine_path` construction in `_quarantine_sidecar_files`, a new `db.config` import, and the new `build_restore_paths()` helper holding the three recovery name constructions moved from `recovery.py` (amended shape).
- Out of scope: the quarantine/stage/restore-file mechanics (Plan 003 landed return shapes); the sweep that prunes quarantine directories (row 1); the `recovery.py` call-site edit (row 4).

## Assumptions
- Anchors re-verified 2026-11-16. In `_quarantine_sidecar_files`: `ts = int(time.time())` at `recovery_restore.py:39`; the candidate is `quarantine_dir / f"{db_path.name}{suffix}_corrupt_{ts}"` at `:46-48`, then `shutil.copy2` at `:49`. `recovery_restore.py` does **not** currently import `db.config` (it imports `logging`, `shutil`, `time`, `collections.abc.Sequence`, `pathlib.Path` only), so importing `resolve_unique_path` here is a new same-layer edge to verify against `lint-imports` and the `skills/DESIGN.md` import contract.
- `resolve_unique_path` is created by the row-02 procedure. The module's docstring already declares this file the owner of the restore's file operations, so hosting the moved name constructions matches its responsibility. The name formats produced by `build_restore_paths` are byte-identical to today's `recovery.py:424-426` output (shared `ts = format_timestamp()`, `resolve_unique_path` only appends a counter suffix on collision).

## Design decisions
- Wrap the candidate before `shutil.copy2`; the recorded `(sidecar, quarantine_path)` tuple at `:51` carries the uniquified path, so `_restore_quarantine_sidecars` on the failure path (`:52-63`) moves back the exact name that was written.

## Alternatives considered
- Alternatives considered: keeping the three name constructions inline in `recovery.py` with direct wraps — rejected via the 2026-11-16 Plan amendment after measuring 24700 B (over the 24576 B gate); the helper stays under both files' gates with identical naming behavior.

## Implementation
### Target file
`scripts/db/recovery_restore.py`

### Procedure
1. Add `from db.config import format_timestamp, resolve_unique_path` to the imports (verify `lint-imports` and the import contract; no cycle — `db.config` does not import `db.recovery_restore`).
2. Wrap the candidate at `:46-48`: `quarantine_path = resolve_unique_path(quarantine_dir / f"{db_path.name}{suffix}_corrupt_{ts}")`.
3. Add `build_restore_paths(db_path: Path) -> tuple[Path, Path, Path]` (new): builds `ts = format_timestamp()` once, then returns `(resolve_unique_path(db_path.with_name(f"{db_path.stem}_corrupt_{ts}{db_path.suffix}")), resolve_unique_path(db_path.with_name(f"{db_path.stem}.tmp_{ts}{db_path.suffix}")), resolve_unique_path(db_path.parent / f"{db_path.stem}_sidecar_quarantine_{ts}"))` — the three constructions moved verbatim from `recovery.py:423-426`, each uniquified.

### Method
- No change to the sidecar `ts` (stays `int(time.time())`), the copy/unlink/records sequence, the `mkdir` at `:45`, or the OSError rollback at `:52-63`.

### Details
- Only the `quarantine_path` name expression changes; `-wal`/`-shm` sidecar resolution and record ordering are untouched.

## Compatibility considerations
- Collision-free quarantines keep identical names, so existing `test_db_recovery.py` quarantine assertions are unaffected.

## Security considerations
- N/A: no deletion introduced; this file only copies and records.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/db/test_db_recovery.py -v`; `uv run ruff check`, basedpyright (CI form), `uv run lint-imports`.

## Completion criteria
- Two same-second quarantines of the same live sidecar produce distinct `_corrupt_{ts}` / `_corrupt_{ts}_2` forensic copies; the rollback path reassembles the exact written names.

## Out of Scope
- Pruning quarantine directories (row 1).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `db.config` import, wrap `quarantine_path`, add `build_restore_paths` | Pending | — | — | |
| 2 | Run collision tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update docs only if in scope (see row 12) | Pending | — | — | |

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
- **Requirement ID**: REQ-004 (route the quarantined sidecar name through the uniquifier)
- **Source issue**: issues/20261114-092857_dbreview008_artifact-retention-gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-054021_dbreview008_artifact-retention-gaps.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-144812
- **Related target files**: `scripts/db/recovery_restore.py`
