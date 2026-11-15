## Goal
- Make the staging helpers report what they quarantined, and stop creating an empty quarantine directory when nothing is quarantined.

## Scope
**Release unit**: whole-unit-rollback-retention (Phase 1 of the plan; lands after Plan 002's procedures `20261115-080732_1/_2` — this document builds on their landed shapes)

- In scope: `scripts/db/recovery_restore.py` — `_quarantine_sidecar_files` returns records; `_stage_restore` surfaces them; `quarantine_dir` creation deferred to the first actual quarantine (REQ-001, Plan Assumption on the mkdir deferral).
- Cross-plan overlap `scripts/db/recovery_restore.py` (shared with Plan 008): **compatible (sequencing)** — Plan 008 edits only the quarantined-name construction (`:33`, wrapping the name in its planned unique-path resolver), disjoint from this document's return-shape change; 008 lands last in the batch.

## Assumptions
- Baseline this cycle: `_quarantine_sidecar_files` returns `None` (`recovery_restore.py:22-35`); `_stage_restore` returns only the staged dict (`:112`); sole production caller is `recovery.py:366`; no test calls `_stage_restore` (grep this cycle); helper tests call `_quarantine_sidecar_files`/`_stage_backup_sidecars` directly (`tests/db/test_db_recovery.py:683`, `:717`, `:749`, `:769`).
- Quarantine entries are `copy2` + `unlink` pairs; a record is `(live_name_path, quarantine_path)` so a caller can move each entry back byte-identically (Plan Assumption).
- `quarantine_dir.mkdir(exist_ok=True)` (`recovery_restore.py:91`) currently runs on every restore; deferral is a recorded behavior decision (Plan Assumption), not a silent side effect.

## Design decisions
- Record type `list[tuple[Path, Path]]` (live name → quarantine path) — plain tuples, no new dataclass. A failure partway through the suffix loop is rolled back by the helper itself (verification correction: an aborted loop used to discard the records it had already built), so the caller never receives a half-quarantined state.
- `mkdir` moves inside `_quarantine_sidecar_files`, executed with `parents=True, exist_ok=True` before the first `copy2` only when a sidecar actually exists — the directory then always contains at least one entry whenever it exists (Plan Assumption).
- `_stage_restore` returns a `tuple[dict[str, Path], list[tuple[Path, Path]]]` — staged dict first (existing caller usage), records second.

## Alternatives considered
- Storing records inside a mutable holder object (Plan 002 procedure's activation-progress holder style): rejected — quarantine records are produced entirely during staging and never mutated afterwards; a plain return value keeps `recovery_restore.py` free of `db.recovery` concepts (import-contract check: no new import edge).
- Returning records keyed by suffix instead of pairs: rejected — the live name must be restorable exactly as quarantined (`db_path.name + suffix` → recorded quarantine name), which pairs express directly.

## Implementation
### Target file
`scripts/db/recovery_restore.py`

### Procedure
1. Change `_quarantine_sidecar_files(db_path, quarantine_dir)` to return `list[tuple[Path, Path]]`: inside the suffix loop, when a sidecar exists, `quarantine_dir.mkdir(parents=True, exist_ok=True)` before `shutil.copy2` (execute once via a flag or call every time — `exist_ok` makes it idempotent); append `(sidecar, quarantine_path)` after the `unlink` completes. Fail-closed raise behavior unchanged (REQ-001).
2. Remove `quarantine_dir.mkdir(exist_ok=True)` from `_stage_restore` (`recovery_restore.py:91`); pass `quarantine_dir` through to `_quarantine_sidecar_files` unchanged (Plan Assumption on deferral).
3. `_stage_restore` captures the records returned by `_quarantine_sidecar_files` and returns `(staged, records)`; return-type annotation and docstring updated: "Returns the staged sidecar paths keyed by suffix and the quarantine records (live name → quarantine path) for the caller's failure-path reassembly" (REQ-001).
4. Verification correction (landed during testing): wrap the `_quarantine_sidecar_files` suffix loop in `try/except OSError` — on a mid-quarantine failure, call `_restore_quarantine_sidecars(records, quarantine_dir)` (its own failure is logged and swallowed; the original error is re-raised), so a failure on the second sidecar never strands the already-recorded first sidecar in an entry-holding quarantine directory.
5. Verification correction (placement): the quarantine lifecycle helpers live in this module — `_restore_quarantine_sidecars(records, quarantine_dir)` moves recorded pairs back byte-identically and rmdir's the emptied directory (guarded, logged); `_retain_quarantine_archive(quarantine_dir)` logs the retained archive on the success path. `db.recovery` imports both, keeping one move-back implementation and holding `recovery.py::_restore_from_backup` at its C(12) radon baseline.

### Method
- Direct edit; one new stdlib import (`collections.abc.Sequence`, for the restore-back helper signature).

### Details
- The quarantine file name format (`{db_path.name}{suffix}_corrupt_{ts}`) stays as-is; Plan 008 later wraps it in its planned unique-path resolver — this document must keep the construction on one line for that disjoint edit.

## Compatibility considerations
- Sole production caller `recovery.py:366` must unpack the new tuple in the same implementation pass (companion document `_2` step 1 lands together; the unit red-gates otherwise).
- Helper behavior otherwise unchanged (fail-closed copy/unlink; mid-loop failure self-rolls back recorded pairs).

## Security considerations
- No new inputs; paths derived from existing db path only. Bandit baseline unchanged.

## Rollback considerations
- Revert both this file and companion `_2` together by checkout; `recovery.py` unpacking depends on the new return shape.

## Validation plan
- Targeted: `uv run pytest tests/db/test_db_recovery.py -v` — helper tests extended by companion `_3` assert the returned records; existing helper tests keep their behavior assertions.
- Regression: `uv run pytest tests/db -v`; `uv run lint-imports` (6 contracts kept; no new import edges — Plan Design).
- Static: `uv run radon cc scripts/db/recovery_restore.py -s` (baseline all A; keep A), ruff, mypy (CI form) per `rules/toolchain.md`.

## Completion criteria
- Records returned and surfaced; no empty quarantine directory after a sidecar-free restore; companion `_2` green against the new shape.

## Out of Scope
- Calling the restore-back on failure paths (helper implemented here per step 5; call sites and policy in companion document `_2`).
- Quarantine retention on success and the success-path `rmtree` removal (companion `_2`, REQ-003).
- Name-construction change (planned unique-path resolver wrap) owned by Plan 008.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261115-104412 | 20261115-104412 | src+test landed; deferred mkdir; self-rollback on mid-quarantine failure added during testing (docs updated); targeted test green correction landed: quarantine self-rollback on mid-loop failure + lifecycle helpers (_restore_quarantine_sidecars, _retain_quarantine_archive) placed in recovery_restore.py; docs steps 4-5 updated |
| 2 | Add or update tests per Validation plan | Completed | 20261115-104412 | 20261115-104412 | radon scripts C-or-worse list unchanged (scripts/db/utils.py C(16) pre-existing); ruff/mypy clean |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261115-104412 | 20261115-104412 | tests/db 408 passed (full suite N/A: not run per user instruction); ruff/format/mypy clean; radon recovery_restore.py all A; lint-imports 6 kept; bandit clean; check_module_size ALL OK |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261115-104412 | 20261115-104412 | N/A for this file: docs handled by companion procedures _4/_5 |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/done/20261114-092850_dbreview003_restore-sidecar-handling.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-041125_dbreview003_restore-sidecar-handling.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-082016
- **Related target files**: scripts/db/recovery_restore.py