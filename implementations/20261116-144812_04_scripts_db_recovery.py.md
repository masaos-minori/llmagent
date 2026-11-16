## Goal

Replace the three recovery working-file name constructions (`corrupt_archive`, `temp_restore`, `quarantine_dir`) with one call to `recovery_restore.build_restore_paths()`, which holds the collision-safe naming (REQ-004, AC-6). The helper placement is the maintainer-approved 2026-11-16 Plan amendment: inline `resolve_unique_path` wraps in this file measured 24700 B against the 24576 B module-size gate (`tools/check_module_size.py`, pre-commit + CI); the single call keeps `recovery.py` under the gate without splitting it.

## Scope
**Release unit**: collision-safe-naming

- In scope: the `ts`/`corrupt_archive`/`temp_restore`/`quarantine_dir` block in `_restore_from_backup`, the `db.config` import, and the `db.recovery_restore` import block.
- Out of scope: the staging/activation/rollback flow around them (Plan 002/003 landed shapes); quarantine-record reassembly logic; the sweep that prunes these directories (row 1); the helper itself (row 5, amended shape).

## Assumptions
- Anchors re-verified 2026-11-16. In `_restore_from_backup`: `ts = format_timestamp()` at `recovery.py:423`; `corrupt_archive` `:424`, `temp_restore` `:425`, `quarantine_dir` `:426` (a directory built from `db_path.parent`). `ts` is used only by those three lines, and `format_timestamp` has no other use in this file, so the import can drop it. `db.recovery_restore` is already imported (`:21-26`).
- `build_restore_paths` is created by the row-05 procedure (the amended shape; row 5 executes before this row); `resolve_unique_path` by row 02. Plan 003 landed quarantine records carry the actual (now possibly suffix-bearing) paths returned by the helper, so `_restore_quarantine_sidecars` moves back the uniquified paths automatically.

## Design decisions
- Naming-site routing only, moved one layer down: the name formats and shared-`ts` semantics stay identical; no surrounding control flow, the `_ActivationProgress` bound at `:431-432`, or the `finally`/OSError cleanup that references these names changes.

## Alternatives considered
- N/A: single-region wrap.

## Implementation
### Target file
`scripts/db/recovery.py`

### Procedure
1. Drop `format_timestamp` from the `from db.config import build_db_config, format_timestamp` line (`:18`).
2. Add `build_restore_paths` to the existing `from db.recovery_restore import (...)` block (`:21-26`).
3. Replace the four lines at `:423-426` with one line: `corrupt_archive, temp_restore, quarantine_dir = build_restore_paths(db_path)`.

### Method
- The helper (row 5) builds all three names from one `format_timestamp()` call and uniquifies each independently, preserving the current shared-`ts` semantics and exact name formats. The quarantine path is a directory path — the uniquifier only checks `exists()`, creation stays where it is today.

### Details
- Do not alter the staging/verification/rollback flow or the `_cleanup_staged` call sites; only the name block and the two import edges change.
- Same-layer imports (`db.recovery` → `db.recovery_restore`, already the established edge); confirm `lint-imports` stays green.
- Byte budget (why the amended shape): current 24574 B; inline wraps measured 24700 B after `ruff format` (over the 24576 B gate); this shape removes 4 lines (~-285 B) and adds one call + one import token (~+110 B) → ~24.4 KB, under the gate.

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
| 1 | Replace the name block with the `build_restore_paths` call and adjust the two import edges | Pending | — | — | |
| 2 | Run collision tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update docs only if in scope (see row 12) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Module-size gate: inline `resolve_unique_path` wraps grow `recovery.py` from 24574 B to 24700 B after `ruff format` (measured 2026-11-16), exceeding the 24576 B gate in `tools/check_module_size.py` (pre-commit + CI). | Yes — maintainer approved the scope-class Plan amendment (2026-11-16): the three name constructions move to `recovery_restore.build_restore_paths()` (Plan rows 4/5 amended); `recovery.py` stays under the gate without splitting or baseline registration. | 2026-11-16 |

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
