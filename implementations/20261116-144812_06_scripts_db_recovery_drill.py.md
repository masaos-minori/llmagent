## Goal

Make the drill's working and artifact names collision-safe and make the isolated `_restored` working copy short-lived: uniquify `isolated` and the artifact JSON, and delete `isolated` after `_persist_artifact` so every completed drill leaves only the recovery-point archive and the JSON artifact (REQ-004, REQ-005, AC-6, AC-7).

## Scope
**Release unit**: retention-sweeps-and-drill-lifecycle

- In scope: `isolated` and JSON name uniquification, the end-of-drill `isolated` unlink, and the drill lifecycle test (companion).
- Out of scope: the recovery-point archive creation and the verify/drift logic (Plan 009 landed shapes); the sweep that removes crashed-orphan `_restored` files (row 1).

## Assumptions
- Anchors re-verified 2026-11-16 against the repo's landed drill shape. `_drill_one_domain` at `recovery_drill.py:145`; `isolated = drill_dir_path / f"{recovery_point.name}_restored{live_path.suffix}"` at `:212`, `shutil.copy2` at `:215`; verification try/finally at `:217-228` (no early return between copy and persist); `_persist_artifact(drill_dir, artifact)` at `:254`, `return artifact` at `:255`. `_persist_artifact` at `:258`, JSON name `{artifact['domain']}_{format_timestamp()}.json` at `:262`. `from db.config import build_db_config, format_timestamp` at `:32`.
- `isolated` exists only on the path where `:212` runs (the two early no-recovery-point returns at `:187-192` and `:193-201` never create it). `resolve_unique_path` is created by the row-02 procedure.

## Design decisions
- Delete `isolated` after `_persist_artifact` (not before) so failure forensics (JSON + archive) always survive even when verification fails; the isolated copy is a verification working file, not a recovery point (the archive is). A crash between verification and unlink leaves an orphan `_restored` that the row-1 sweep removes under the 1-day stale rule.
- Uniquify both `isolated` and the JSON so a same-second second run no longer overwrites the first run's artifact (the current fixed-shape timestamped name collides on a same-second repeat).

## Alternatives considered
- Leaving `_restored` for the sweep alone — rejected: maintainer decision is immediate deletion after the drill, with the sweep as a crash backstop only.

## Implementation
### Target file
`scripts/db/recovery_drill.py`

### Procedure
1. Add `resolve_unique_path` to the `from db.config import build_db_config, format_timestamp` line (`:32`).
2. Wrap the isolated copy name at `:212`: `isolated = resolve_unique_path(drill_dir_path / f"{recovery_point.name}_restored{live_path.suffix}")`.
3. Wrap the artifact JSON name in `_persist_artifact` at `:262`: `artifact_path = resolve_unique_path(drill_dir_path / f"{artifact['domain']}_{format_timestamp()}.json")`.
4. After `_persist_artifact(drill_dir, artifact)` at `:254` and before `return artifact` at `:255`, add `isolated.unlink(missing_ok=True)`.

### Method
- The unlink sits after persist on the single path where `isolated` is defined, so every completed or verification-failed drill removes the working copy; the early no-recovery-point returns (`:187-201`) are unaffected because no `isolated` exists there.

### Details
- Do not change the archive creation, `_verify_*`, `_schema_drift_error`, artifact field population, or `run_drill`. Confirm `lint-imports` stays green (same-layer import).

### Companion test files
- `tests/db/test_recovery_drill.py`
  - Procedure: extend `test_all_domains_drill_passes_and_live_dbs_untouched` (`:238`) — after `run_drill("all", ...)`, assert `list(drill.glob("*_restored*")) == []` and `_load_artifacts(drill)` (`:201-202`) is non-empty; add a same-second repeat test asserting two artifact JSONs coexist (distinct names, no overwrite).
  - Validation: `uv run pytest tests/db/test_recovery_drill.py -v`.

## Compatibility considerations
- Collision-free drills keep identical names; existing drill assertions (`_load_artifacts`) still pass. Adding the unlink changes only the post-drill filesystem state (the `_restored` copy no longer lingers).

## Security considerations
- The only new deletion is `isolated.unlink(missing_ok=True)` on a drill-created working file in the drill directory; it never targets a live DB or a recovery-point archive.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/db/test_recovery_drill.py -v` and `uv run pytest tests/db -q`; `uv run ruff check`, basedpyright (CI form), `uv run lint-imports`.

## Completion criteria
- After any completed drill (pass or verification-fail) no `*_restored*` file remains in the drill dir; two same-second drills for one domain produce two distinct artifact JSONs; the recovery-point archive and JSON survive.

## Out of Scope
- Removing crashed-orphan `_restored` files older than 1 day (row 1 sweep).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Uniquify `isolated` and JSON, add end-of-drill unlink | Pending | — | — | |
| 2 | Add/update drill tests per Validation plan | Pending | — | — | |
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
- **Requirement ID**: REQ-004 (uniquify drill names), REQ-005 (delete `_restored` after the drill)
- **Source issue**: issues/20261114-092857_dbreview008_artifact-retention-gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-054021_dbreview008_artifact-retention-gaps.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-144812
- **Related target files**: `scripts/db/recovery_drill.py`, `tests/db/test_recovery_drill.py`
