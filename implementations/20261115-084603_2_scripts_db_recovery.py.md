## Goal
- Make recovery probes read-only, classify a missing database as `DbCondition.MISSING` with a distinct missing_database result, and fix the stale docstring consumer claim.

## Scope
**Release unit**: ro-probes-missing-policy (Phases 2-3 of the plan; lands with `_3`, `_5`, `_6` — the classification changes results asserted by existing tests only through the new MISSING branch, which no existing test exercises)

- In scope: `scripts/db/recovery.py` — enum addition, existence-first integrity probe, read-only probe selection, missing_database result, docstring fix (REQ-002, REQ-003, REQ-004, REQ-007).

## Assumptions
- Line citations are the current tree at generation time; Plans 001-003 land first in the batch, so citations past the restore region (the `_NO_RESTORE_CONDITIONS`/`_result_for_condition`/`recover_corruption` area, currently `:447-529`) shift after Plan 003's edits — re-read the landed file and anchor by content (`_result_for_condition` body, `DbCondition` enum block) at execution time.
- `_failure` (`:120-127`) already carries `active_db_state` and `dry_run` — no signature change needed (checked this cycle).
- Consumers `db_maintenance_service.py`/`rag_maintenance_service.py` only branch on `action == "restored"` and otherwise log `action`/`detail` (Plan 002 cycle verification), so the new missing_database action needs no consumer edit.

## Design decisions
- `MISSING` gets its own action missing_database and is NOT added to `_NO_RESTORE_CONDITIONS` (`:447-453`) — a missing live DB deserves its own label, and the maintainer decision (no automatic restore) is expressed by `_result_for_condition` returning early (Plan Design).
- `_run_integrity_check` gains a keyword-only `read_only` (new) with no default: every probe call site states its mode explicitly, so the candidate integrity stage (`:277`) cannot inherit read-only by accident (Issue Constraint: candidate may need WAL recovery).
- The existence check lives inside `_run_integrity_check` (not at call sites): every path into the probe, including the public wrapper used by rotation/drill, gets MISSING classification with no open and no creation (REQ-002).

## Alternatives considered
- Returning `PERMISSION_FAILURE` for a missing file: rejected — mislabels absence as an access error and routes it into the `bad_backup`/`error` families.
- Auto-restore on MISSING: rejected by maintainer decision 2026-11-15 (Plan Requirements).

## Implementation
### Target file
`scripts/db/recovery.py`

### Procedure
1. `DbCondition` enum (`:31-36`): append `MISSING = "missing"` (new) after `UNKNOWN` (REQ-002; StrEnum consumers compare by value).
2. `_run_integrity_check` (`:91-116`): add keyword-only `read_only` (new); at the top, before any open, `if not db_path.exists(): return DbCondition.MISSING, f"database file not found: {db_path}"` (path-carrying detail, REQ-002/AC-2); pass the flag through the open call (`:99`) as `open(read_only=read_only)` — the `SQLiteHelper` kwarg landed by companion `20261115-084603_1` (REQ-001 dependency order within Plan 004).
3. Call sites get explicit modes (REQ-003): `_backup_is_usable` (`:186`) → `read_only=True`; public `run_integrity_check` wrapper (`:219`) → `read_only=True`; post-activation live re-check (`:250`) → `read_only=True`; `recover_corruption` main probe (`:529`) → `read_only=True`; `_verify_candidate` integrity stage (`:277`) → `read_only=False` (Issue Constraint — candidate WAL recovery must stay possible; Plan 003's candidate tests stay green, AC-3).
4. `_verify_domain_identity` (`:157-176`): open (`:167`) as `open(read_only=True)` (REQ-003).
5. `_result_for_condition` (`:456-479`): add a `DbCondition.MISSING` branch before the `_NO_RESTORE_CONDITIONS` branch returning `_failure("missing_database", f"{condition.value}: {detail}", dry_run, active_db_state="missing")` — no vacuum, no restore attempt, identical under `dry_run=True` (REQ-004/AC-2). Keep `_NO_RESTORE_CONDITIONS` unchanged.
6. Docstring fix in `run_integrity_check` (`:214-216`): replace "Consumers are the migration gate (rows 01/06), the drill harness (row 11), and rotation verification (row 12)." with the drill-harness-and-rotation wording only (grep-verified this cycle: no migration-gate consumer exists) (REQ-007).

### Method
- Direct edits in the probe/classification region (`:31-235`) plus the two late-file changes (steps 5-6 semantics, content-anchored after 002/003 land).

### Details
- Vocabulary: new action token missing_database (new) and `DbCondition.MISSING`/`"missing"` (new) — docs enumerate them in companions `_7`/`_8` (docs-first for external parsers, Plan Risk mitigation).
- A ro open that fails on permissions (e.g. WAL sidecar on read-only media) still flows through the existing broad `except Exception` → `_classify_error` → `PERMISSION_FAILURE` → honest `permission_failure`/`bad_backup` reporting (Plan Risks row 2); no new exception handling needed.
- No import changes; `lint-imports` stays 6 kept (Plan Architecture check).

## Compatibility considerations
- `rotation.py` and `recovery_drill.py` need no call-site change: they use the public wrapper, which now probes read-only (Reference Files row).
- `RecoveryResult` fields unchanged; `active_db_state` gains the documented value `"missing"` in docs only (`scripts/db/models.py` untouched — Reference Files row).

## Security considerations
- No new suppression; bandit baseline 45 low / 0 medium / 0 high.

## Rollback considerations
- Inside the ro-probes-missing-policy unit: revert together with `_3`/`_5`/`_6` (new action values asserted by new tests). Checkout revert.

## Validation plan
- `uv run pytest tests/db/test_db_recovery.py -v` → MISSING/missing_database, read-only probe, and invariance tests pass (companion `_5`; AC-1..AC-3).
- `uv run pytest tests/db` → rotation/drill regressions green (read-only wrapper covers their probes).
- `uv run radon cc scripts/db/recovery.py -s` → no function exceeds its baseline rank (the existence-check branch adds ~1 to `_run_integrity_check`, currently low).
- `uv run ruff check` / `uv run mypy` (CI form) / `uv run bandit -r scripts/ -c pyproject.toml -ll` / `uv run lint-imports` → baselines clean.

## Completion criteria
- Missing paths report `action="missing_database"` + `active_db_state="missing"` with a path-carrying detail and no file created (also under `dry_run=True`); every probe except the candidate integrity stage opens read-only; docstring consumer claim fixed.

## Out of Scope
- `recovery_verification.py` read-only logical stage (companion `_3`).
- Test additions (companions `_4`/`_5`/`_6`).
- Docs updates (companions `_7`/`_8`).
- `_verify_candidate` integrity stage mode (stays read-write by Issue Constraint).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-002, REQ-003, REQ-004, REQ-007
- **Source issue**: issues/20261114-092852_dbreview004_integrity-probe-side-effects.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-041859_dbreview004_integrity-probe-side-effects.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-084603
- **Related target files**: scripts/db/recovery.py
