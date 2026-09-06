## Goal
Add fault-injection tests for Session logical-corruption cases at the
`_restore_from_backup()` integration level to
`tests/integration/test_session_recovery.py`, without disturbing the 3 pre-existing
unrelated failures (REQ-008).

## Scope
- In scope: new test functions in `tests/integration/test_session_recovery.py`,
  covering the Session domain's fault-injection cases at the integration level (real
  `corrupt_wal_db`-style fixtures / real restore flow through `recover_corruption(target="session")`,
  matching this file's existing E01-E06 style), exercising seq 01's new
  logical-verification stage and seq 03's `check_session_consistency()`.
- Out of scope: fixing or altering `test_e02`/`test_e03`/`test_e04` (the 3
  pre-existing failures — unrelated to this Plan, see Risks); unit-level tests for
  `check_session_consistency()` itself (seq 09).

## Assumptions
- Seq 01 and seq 03 land before or together with this row.
- The 3 pre-existing failures (`test_e02_recover_corruption_raises_uncaught_database_error`,
  `test_e03_recover_corruption_no_backup_raises_uncaught_database_error`,
  `test_e04_recover_corruption_dry_run_raises_before_mutation_check`) are confirmed
  still failing this cycle (2026-09-06 baseline: `uv run pytest
  tests/integration/test_session_recovery.py -v` → 3 failed, 3 passed, exact same 3
  test names as the Plan's Risks section cites) — this row's new tests must not
  change that count.

## Design decisions
- Add new tests following the existing E-numbering convention (e.g. `test_e07_...`,
  `test_e08_...`) rather than renumbering or interleaving with E01-E06, so the
  pre-existing 3-failure baseline remains trivially diffable (same test names, same
  pass/fail set, plus new E07+ tests appended).
- Reuse `_patch_db_config()` (this file's existing helper, lines 32-53) and the
  `corrupt_wal_db`/real-file fixture pattern already established by E01/E06, rather
  than introducing a second, parallel fixture style for the new logical-corruption
  cases.

## Alternatives considered
- Mock `check_session_consistency()` at the integration-test level instead of using
  real corrupted `session.sqlite` fixtures: rejected — this file's own docstring
  explicitly frames itself as the "real corruption + recovery" integration
  complement to unit-level mock-based coverage (seq 09); mocking here would duplicate
  seq 09's role rather than adding integration-level confidence.

## Implementation
### Target file
`tests/integration/test_session_recovery.py`

### Procedure
1. Re-run the baseline (`uv run pytest tests/integration/test_session_recovery.py -v`)
   immediately before adding tests; confirm the 3-failed/3-passed split matches this
   document's Assumptions before proceeding — if it has changed, stop and reconcile
   against the Plan's Risks section before continuing (per
   `rules/ai-execution.md` Adversarial Verification).
2. Add fault-injection tests for: missing table (construct a `session.sqlite` backup
   file missing one required table via `sqlite3.connect()`+`executescript()` with a
   partial schema, then restore from it), orphaned message/invalid relationship
   (backup file with a `messages` row referencing a nonexistent `session_id`),
   invalid memory-link (backup file with a `memory_links` row referencing a
   nonexistent `memory_id`), read smoke-test failure, write smoke-test failure where
   applicable (per seq 03's UNK-02 resolution), confirming no content is leaked in a
   failure result's `detail` string.
3. Assert `recover_corruption(target="session")`'s result has `success=False` and the
   new distinct `action` value (seq 01) for each logical-corruption case, and
   `success=True` for a healthy fixture (regression, matching E01's existing healthy
   case shape).
4. Run the full file after adding tests; confirm exactly the same 3 pre-existing
   failures remain (by name), with no new failure and no accidental fix of those 3.

### Method
Confirmed this cycle (2026-09-06) via direct read (lines 1-100) and a live
`uv run pytest tests/integration/test_session_recovery.py -v` run: 6 existing tests
(E01-E06), 3 failing (`test_e02`/`test_e03`/`test_e04` — each expects
`sqlite3.DatabaseError` to propagate uncaught from `_run_integrity_check()`, but
`_classify_error()`'s dispatch (`scripts/db/recovery.py:57`, `except Exception as e:`)
now catches it and classifies it as `DbCondition.CORRUPTION` instead, per current
code), 3 passing (`test_e01`, `test_e05`, `test_e06`) — exact match to the Plan's
Risks section citation, no drift found.

### Details
No change to any existing E01-E06 test — this row is purely additive, using the same
`_patch_db_config()` helper and fixture conventions already established in this file.

## Compatibility considerations
N/A: test-only change.

## Security considerations
Assert failure-result `detail` strings contain only counts/category labels, never
`messages.content`/`memories.content` values (REQ-010/AC-7) — this file's real-SQLite
fixtures make it possible to insert recognizable placeholder content and assert it
does NOT appear in any result string, a stronger check than seq 09's unit-level
assertion alone.

## Rollback considerations
Revert via `git checkout` on this file alone if the new tests destabilize the
existing 3-failed/3-passed baseline — re-run the baseline check (Procedure step 1)
first to confirm whether the destabilization is this row's fault or an unrelated
change.

## Validation plan
- `uv run pytest tests/integration/test_session_recovery.py -v` — new tests pass;
  exactly `test_e02`/`test_e03`/`test_e04` remain failing (by name), unchanged from
  the pre-implementation baseline.

## Completion criteria
- Every Session logical-corruption case in the Issue's Testing Expectations has a
  corresponding passing integration test in this file.
- The pre-existing 3-failure baseline is unchanged in both count and identity (same
  3 test names).

## Out of scope
- `test_e02`/`test_e03`/`test_e04`'s own bug — explicitly out of scope per the Plan
  (see Risks); do not fix as part of this row.
- Unit-level `check_session_consistency()` tests — tracked in seq 09.

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
- **Requirement ID**: REQ-008
- **Source issue**: issues/20260903-110305_h0707_add-rag-session-recovery-verification.md
- **Source plan**: plans/20260905-163508_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-144010
- **Related target files**: tests/integration/test_session_recovery.py
