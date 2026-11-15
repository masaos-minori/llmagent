## Goal
- Make the logical-verification stage's open read-only.

## Scope
**Release unit**: ro-probes-missing-policy (Phase 2 of the plan; lands with `_2`)

- In scope: `scripts/db/recovery_verification.py` — `_run_logical_verification` opens its target with `read_only=True` (REQ-005).

## Assumptions
- Sequence: Plan 001's procedure `implementations/20261115-075008_1_scripts_db_recovery_verification.py.md` lands first and threads the `sqlite_vec_so` kwarg into the same open; this document adds `read_only` on top of that landed shape (plan Correction 2 — overlap invisible to the frozen-plan scan; sequencing 001 → 004, compatible). The `:141` citation is the pre-001 position; anchor on `_run_logical_verification`'s `try:` open statement at execution time.
- `load_vec` extension loading on a read-only connection is legal (Plan Design; Helper companion `20261115-084603_1` Details).

## Design decisions
- Read-only here is safe because the candidate flow's read-write guarantee lives in the integrity stage (`_verify_candidate`, `read_only=False` via companion `_2`): the integrity stage still runs read-write first, so the Plan 003 candidate WAL-recovery flow is not weakened (REQ-005, AC-3).

## Alternatives considered
- Leaving the logical stage read-write: rejected — its queries are pure reads (`verify(db)` callbacks), so any write pragmas it applies are pure side effects on the probe subject (Plan REQ-005).

## Implementation
### Target file
`scripts/db/recovery_verification.py`

### Procedure
1. In `_run_logical_verification`, change the `SQLiteHelper(target, db_path=str(db_path)).open()` call (currently `:141`, after Plan 001's edit) to pass `read_only=True` while keeping the landed `sqlite_vec_so` threading kwarg intact (REQ-005/AC-1).

### Method
- Single-line keyword addition on the landed call.

### Details
- The `except sqlite3.Error` → `verification_unavailable` behavior stays: a read-only open failure (e.g. permissions) reports fail-closed exactly as today.
- Helper kwarg availability comes from companion `20261115-084603_1` (Plan Phase 1 lands before Phase 2).

## Compatibility considerations
- `verify(db)` callbacks in callers (`check_rag_consistency`, `check_session_consistency`, drill checks) are pure reads; a write-attempting callback would now fail honestly instead of silently mutating — none exists in `scripts/` (grep this cycle).

## Security considerations
- N/A: no new surface.

## Rollback considerations
- Inside the ro-probes-missing-policy unit: revert together with `_2`/`_5`/`_6`. Checkout revert.

## Validation plan
- `uv run pytest tests/db/test_db_recovery.py -v` → directory-unchanged test for the logical stage passes (companion `_5`; AC-1).
- `uv run pytest tests/db` → Plan 001/003 verification and candidate tests stay green.
- `uv run ruff check scripts/db/recovery_verification.py` / `uv run mypy scripts/db/recovery_verification.py` → clean.

## Completion criteria
- The logical-verification open is `read_only=True` with vec threading preserved; no probe write side effects from this module (AC-1).

## Out of Scope
- Integrity-stage mode selection (companion `_2`).
- Helper read-only mode itself (companion `20261115-084603_1`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261115-113615 | 20261115-113615 | recovery: verification.py: logical: stage: ro: open |
| 2 | Add or update tests per Validation plan | Completed | 20261115-113615 | 20261115-113615 | covered by companion test procedures |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261115-113615 | 20261115-113615 | targeted gates green (tests/db, ruff, mypy) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261115-113615 | 20261115-113615 | N/A: docs handled by companion procedures _7/_8 |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261114-092852_dbreview004_integrity-probe-side-effects.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-041859_dbreview004_integrity-probe-side-effects.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-084603
- **Related target files**: scripts/db/recovery_verification.py