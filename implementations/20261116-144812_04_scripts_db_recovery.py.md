## Goal

Route the three recovery working-file names (`corrupt_archive`, `temp_restore`, `quarantine_dir`) built from a single timestamp through `resolve_unique_path`, so two same-second restores never overwrite each other's forensic artifacts (REQ-004, AC-6).

## Scope
**Release unit**: collision-safe-naming

- In scope: the three name-construction lines in `_restore_from_backup` and the `db.config` import.
- Out of scope: the staging/activation/rollback flow around them (Plan 002/003 landed shapes); quarantine-record reassembly logic; the sweep that prunes these directories (row 1).

## Assumptions
- Anchors re-verified 2026-11-16. In `_restore_from_backup`: `ts = format_timestamp()` at `recovery.py:423`; `corrupt_archive` `:424`, `temp_restore` `:425`, `quarantine_dir` `:426` (a directory built from `db_path.parent`). `db.config` is already imported for `format_timestamp`.
- `resolve_unique_path` is created by the row-02 procedure; Plan 003 landed quarantine records carry the actual (now possibly suffix-bearing) paths, so `_restore_quarantine_sidecars` moves back the uniquified paths automatically.

## Design decisions
- Naming-site routing only: wrap each already-built candidate path; do not change any surrounding control flow, the `_ActivationProgress` bound at `:431-432`, or the `finally`/OSError cleanup that references these names.

## Alternatives considered
- N/A: single-region wrap.

## Implementation
### Target file
`scripts/db/recovery.py`

### Procedure
1. Add `resolve_unique_path` to the existing `from db.config import ... format_timestamp ...` import.
2. Wrap the three constructions at `:424-426`: `corrupt_archive = resolve_unique_path(db_path.with_name(f"{db_path.stem}_corrupt_{ts}{db_path.suffix}"))`, `temp_restore = resolve_unique_path(db_path.with_name(f"{db_path.stem}.tmp_{ts}{db_path.suffix}"))`, `quarantine_dir = resolve_unique_path(db_path.parent / f"{db_path.stem}_sidecar_quarantine_{ts}")`.

### Method
- All three share the one `ts` at `:423`; each candidate is uniquified independently. The quarantine path is a directory path — the uniquifier only checks `exists()`, creation stays in `recovery_restore`.

### Details
- Do not alter the staging/verification/rollback flow or the `_cleanup_staged` call sites; only the three name expressions change.
- Same-layer import; confirm `lint-imports` stays green.

## Compatibility considerations
- Existing collision-free restores keep identical names (free candidate returned unchanged), so existing recovery tests and quarantine-record assertions are unaffected.

## Security considerations
- N/A here: no deletion is introduced; the sweep's recursive delete is in `maintenance.py` (row 1).

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/db/test_db_recovery.py -v` (existing collision-free naming re-run) and `uv run pytest tests/db -q`; `uv run ruff check`, basedpyright (CI form), `uv run lint-imports`.

## Completion criteria
- Two same-second restores produce distinct corrupt / tmp / sidecar_quarantine names; no forensic artifact is overwritten; the rollback path still finds its recorded (uniquified) quarantine paths.

## Out of Scope
- Pruning these quarantine directories (row 1).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Import `resolve_unique_path` and wrap the three names | Pending | — | — | |
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
- **Requirement ID**: REQ-004 (route the three recovery names through the uniquifier)
- **Source issue**: issues/20261114-092857_dbreview008_artifact-retention-gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-054021_dbreview008_artifact-retention-gaps.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-144812
- **Related target files**: `scripts/db/recovery.py`
