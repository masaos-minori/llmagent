## Goal
Satisfy `REQ-001`/`REQ-002`/`REQ-003`: make `recover_corruption()` distinguish
`DbCondition.UNKNOWN` from `DbCondition.CORRUPTION`, preserving the target database
and returning a self-describing "preserved, operator intervention required" result
for UNKNOWN, without changing the CORRUPTION branch's restore behavior.

## Scope
Modify exactly `recover_corruption()` in `scripts/db/recovery.py`: insert one new
`DbCondition.UNKNOWN` branch between the existing early-return branch (lines
204-214) and the "CORRUPTION or UNKNOWN" fallthrough (line 216), and update the
function's docstring `action` value list. No other function (`_classify_error()`,
`_run_integrity_check()`, `_restore_from_backup()`) is touched.

## Assumptions
- Re-verified 2026-09-02: line numbers and behavior match the Plan's evidence
  exactly — no drift since Plan creation. `RecoveryResult.action: str` (plain string
  field, `scripts/db/models.py` line 127) accepts arbitrary values, so
  `"unknown_preserved"` needs no model change (Plan UNK-01, resolved).

## Design decisions
New `action` value `"unknown_preserved"`, distinct from `"no_recovery_allowed"`
(used for workflow/eventbus's domain-policy prohibition) and `"error"` (used for
lock/permission/invalid-format) — makes the UNKNOWN outcome self-describing rather
than conflating it with either existing category (Plan `Design`).

## Alternatives considered
Reusing `"no_recovery_allowed"` for UNKNOWN — rejected: that value's existing
semantics are "domain policy prohibits automatic recovery for this target"
(workflow/eventbus), a different reason than "classification itself is unknown,"
which applies to any target including rag/session.

## Implementation
### Target file
scripts/db/recovery.py

### Procedure
Insert an unconditional-preserve branch for `DbCondition.UNKNOWN` before the
existing CORRUPTION-or-UNKNOWN fallthrough; update the docstring.

### Method
1. Locate lines 204-216 (current):
   ```python
       if condition in (
           DbCondition.LOCK_CONTENTION,
           DbCondition.PERMISSION_FAILURE,
           DbCondition.INVALID_FORMAT,
       ):
           return RecoveryResult(
               success=False,
               action="error",
               detail=f"{condition.value}: {detail}",
               dry_run=dry_run,
           )

       # It's CORRUPTION or UNKNOWN
   ```
2. Insert a new branch immediately after the `LOCK_CONTENTION`/`PERMISSION_FAILURE`/
   `INVALID_FORMAT` block, before the "CORRUPTION or UNKNOWN" comment:
   ```python
       if condition == DbCondition.UNKNOWN:
           return RecoveryResult(
               success=False,
               action="unknown_preserved",
               detail=f"Unknown integrity failure: {detail}",
               dry_run=dry_run,
           )

       # It's CORRUPTION
   ```
   (the trailing comment changes from "It's CORRUPTION or UNKNOWN" to "It's
   CORRUPTION", since UNKNOWN is now handled above).
3. Update the docstring's `action values:` list (currently lines 176-185) to add:
   ```
         "unknown_preserved" — integrity check returned an unclassifiable result;
                                DB preserved, operator intervention required
   ```

### Details
This branch returns before the `dry_run` check at line 217 and before the domain
policy check at line 226 — UNKNOWN is preserved unconditionally for every target
(`rag`, `session`, `workflow`, `eventbus`), both in `dry_run` and normal mode, since
the new branch is placed before both of those checks.

## Compatibility considerations
Behavioral change for `rag`/`session` targets only: an UNKNOWN integrity-check
result no longer reaches `_restore_from_backup()`. `workflow`/`eventbus` targets
were already excluded from restore (via the domain-policy check) so their behavior
for UNKNOWN is unchanged in outcome (preserved either way), only the returned
`action` string changes from `"no_recovery_allowed"` to `"unknown_preserved"` for
those two targets under an UNKNOWN classification specifically.

## Security considerations
This closes a genuine data-integrity risk: an ambiguous failure could previously
trigger an automatic backup-restore that discards legitimate current data (Plan
`Reason for change`). No new capability is granted; behavior becomes more
conservative, not less.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file — but
re-introduces the ADR-008 INV-17 conformance gap.

## Validation plan
- `uv run pytest tests/db/test_db_maintenance.py -k unknown` — after seq 02 lands, the new UNKNOWN test passes (`action == "unknown_preserved"`, `success is False`).
- `uv run pytest tests/db/test_db_maintenance.py tests/integration/test_session_recovery.py` — no new failures (pre-existing 3 unrelated failures in `test_session_recovery.py` are baseline, not introduced by this row — see Plan Note).
- `uv run ruff format scripts/db/recovery.py && uv run ruff check scripts/db/recovery.py && uv run mypy scripts/db/recovery.py`.

## Completion criteria
`recover_corruption()` returns `action="unknown_preserved"`, `success=False` for any
`DbCondition.UNKNOWN` result, for every target, without calling
`_restore_from_backup()`; the docstring lists the new action value.

## Out of scope
`tests/db/test_db_maintenance.py` (seq 02), `tests/integration/test_session_recovery.py`
(seq 03), and `docs/adr/ADR-008-sqlite-4db-separation.md` (seq 04) — each covered by
its own implementation procedure document for this same Plan. The 3 pre-existing,
unrelated failing tests in `test_session_recovery.py` (see Plan Note) — not this
row's concern.

## Documentation
Not a `docs/*.md` file; the documentation consequence is covered by seq 04.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Insert UNKNOWN branch per Method | Pending | — | — | |
| 2 | Update docstring `action` value list | Pending | — | — | |
| 3 | Run validation sequence | Pending | — | — | |
| 4 | Documentation update | Pending | — | — | N/A: covered by seq 04 |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003 (UNKNOWN branch, self-describing result, docstring update)
- **Source issue**: `issues/20260831-181721_adr008_01_recover_corruption_unknown_classification_gap.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-111916_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-141419
- **Related target files**: `scripts/db/recovery.py`
