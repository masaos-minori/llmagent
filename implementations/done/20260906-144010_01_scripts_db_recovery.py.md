## Goal
Integrate RAG and Session logical verification into `_restore_from_backup()`'s
existing post-restore stage, immediately after the physical `_run_integrity_check()`
re-check succeeds (line 140) and before `success=True` is returned (line 155-157),
gated on `target` (REQ-002, REQ-004, REQ-010).

## Scope
- In scope: `_restore_from_backup()` (lines 90-164) only — insert a new
  logical-verification stage between the existing physical re-check and the success
  return; add a small private dispatch helper (per Risks' complexity mitigation) if
  the inline branch would push `radon cc`'s grade for this function beyond its current
  `B (10)`.
- Out of scope: the physical-verification sequence preceding it (backup validation,
  atomic staging via `shutil.copy2()`/`os.replace()`, corrupt-archive) — already
  correct and resolved (`SHARED-002`); `_run_integrity_check()` itself;
  `recover_corruption()`/`_classify_error()` (unrelated call paths in the same file,
  confirmed by direct read not to need modification for this row).

## Assumptions
- `check_rag_consistency()`/`is_consistent()` (Reference Files) are reused unmodified;
  this document does not implement RAG-side counting/orphan-detection logic.
- `check_session_consistency()`/`is_consistent()` (seq 03,
  `scripts/db/session_consistency.py`) exists by the time this row's `target=="session"`
  branch is implemented — process seq 03 first if implementing out of the Plan's own
  listed order, or implement both call sites together in one pass.
- The result type REQ-001 adds to `scripts/db/models.py` (seq 02) is available before
  this row's branch can populate it — implement seq 02 first, or together with this row.

## Design decisions
- Add a `target`-gated branch rather than two separate call sites, mirroring
  `_run_integrity_check(db_path, target)`'s own existing `target`-parameterized call
  one stage earlier in the same function — keeps the two domains' integration
  syntactically parallel per the Plan's Design section.
- Extract the new branch into a small private helper (e.g.
  `_run_logical_verification(db, target)`) rather than inlining an `if/elif` directly
  in `_restore_from_backup()`, per the Plan's Risks mitigation for the
  cyclomatic-complexity risk — confirmed this cycle via `radon cc` (see Method) that
  `_restore_from_backup()` is currently `B (10)`.
- On logical-verification failure, return `success=False` with a new, distinct
  `action` value (not `restore_verify_failed`, which is reserved for the existing
  physical-check failure) — per REQ-002/AC-5, so a caller can distinguish physical
  from logical failure by `action` value alone.

## Alternatives considered
- Inline the RAG/Session branch directly into `_restore_from_backup()` without a
  helper: rejected — Plan's Risks section explicitly flags the complexity risk;
  extracting mirrors the file's own existing `_classify_error()` extraction pattern.
- Reuse `restore_verify_failed` for both physical and logical failure, distinguishing
  only via `detail` string: rejected — AC-5 explicitly requires the `action` value
  itself to be distinct, not just the free-form detail text.

## Implementation
### Target file
`scripts/db/recovery.py`

### Procedure
1. Re-confirm current line numbers for the post-restore stage (this cycle: physical
   re-check at line 140, success return at line 155-157) before editing — re-run
   `grep -n "_run_integrity_check\|success=True" scripts/db/recovery.py` if this row
   is implemented after other rows have already landed.
2. Add a private helper (e.g. `_run_logical_verification(db_path: Path, target: str)
   -> tuple[bool, str | None]` or returning the new result type REQ-001 adds) that:
   - for `target == "rag"`: opens the restored `db_path` via `SQLiteHelper`
     (Reference Files), calls `check_rag_consistency(db)`, returns
     `is_consistent(report)` plus a summarized detail string (no row content — see
     Security considerations).
   - for `target == "session"`: same shape, calling
     `check_session_consistency(db)`/`is_consistent()` (seq 03).
3. Call this helper immediately after the line-140 physical re-check succeeds
   (`post_condition == DbCondition.HEALTHY`), before the line-155 success return.
   On a failing result, return `RecoveryResult(success=False, action=<new distinct
   value>, detail=<summarized>, dry_run=dry_run)` instead of falling through to the
   success return.
4. Populate the new `RecoveryResult` field REQ-001 adds (seq 02) with the logical
   result on both the success and failure paths, so callers always receive it.
5. Re-run `radon cc scripts/db/recovery.py -s` after implementation; if
   `_restore_from_backup()` (or the new helper) grades `C` or worse, extract further
   per the Plan's Risks mitigation rather than accepting it silently.

### Method
Confirmed this cycle (2026-09-06) via direct read: `_restore_from_backup()` (lines
90-164) — physical re-check at line 140 (`post_condition, post_detail =
_run_integrity_check(db_path, target)`), success return at lines 155-157
(`RecoveryResult(success=True, action="restored", ...)`), the pre-existing atomic
restore already committed at line 137 (`os.replace(temp_restore, db_path)`) —
confirms the file is already the live target by the time this row's new stage would
run (relevant to seq 03's write-smoke-test resolution, UNK-02). `RecoveryResult`
(`scripts/db/models.py:123-129`) confirmed to have only `success`/`action`/`detail`/
`dry_run` today — no drift from the Plan's citation.

### Details
No change to the preceding physical-verification sequence (lines 90-152) or the
`except OSError` error path (lines 158-164) — this row's change is additive, inserted
strictly between the existing physical re-check and the existing success return.

## Compatibility considerations
`RecoveryResult`'s existing fields (`success`, `action`, `detail`, `dry_run`) are
unchanged in meaning — only a new field is added (seq 02) and a new `action` string
value is introduced. Existing callers matching on `action in {"restored",
"restore_verify_failed", ...}` are unaffected unless they enumerate all possible
values exhaustively; confirm via `rg 'action ==' scripts/ tests/` during
implementation whether any caller needs updating for the new value (not found in this
cycle's investigation, but re-confirm at implementation time per
`rules/ai-execution.md` Adversarial Verification).

## Security considerations
The new stage's `detail` string must not include row content (document/message/
memory text) — only counts, identifiers, and category labels, matching
`check_rag_consistency()`'s own existing `RagConsistencyReport` shape (counts/flags,
no content) and REQ-010/AC-7.

## Rollback considerations
Revert via `git checkout` on this file alone if the full `tests/db/` /
`tests/integration/test_session_recovery.py` regression run fails after this row and
seq 02/03 land together — this row has no independent effect without seq 02's result
field and seq 03's Session function, so revert all three together if reverting.

## Validation plan
- `uv run pytest tests/db/test_db_recovery.py -v` (RAG fault-injection cases, seq 08).
- `uv run pytest tests/integration/test_session_recovery.py -v` (Session
  fault-injection cases, seq 10) — confirm the 3 pre-existing unrelated failures
  (`test_e02_recover_corruption_raises_uncaught_database_error`,
  `test_e03_recover_corruption_no_backup_raises_uncaught_database_error`,
  `test_e04_recover_corruption_dry_run_raises_before_mutation_check`) remain
  unchanged in count, not conflated with this row's new-test results.
- `uv run radon cc scripts/db/recovery.py -s` — confirm `_restore_from_backup()` (and
  any new helper) stays at grade `B` or better.
- `uv run mypy scripts/db/`, `PYTHONPATH=scripts uv run lint-imports`,
  `uv run bandit -r scripts/db/ -c pyproject.toml`.

## Completion criteria
- `_restore_from_backup()` calls the new logical-verification stage for both
  `target` values, strictly between the physical re-check and the success return.
- A logical-verification failure returns `success=False` with an `action` value
  distinct from `restore_verify_failed`.
- `radon cc` grades `_restore_from_backup()` (and any extracted helper) `B` or
  better.
- Validation plan's full command set passes with no new failure.

## Out of scope
- `scripts/db/models.py`'s new result field itself — tracked in seq 02.
- `scripts/db/session_consistency.py`'s implementation — tracked in seq 03.
- Any change to `recover_corruption()` or the physical-verification sequence
  preceding line 139.

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
- **Requirement ID**: REQ-002 (RAG logical verification integration), REQ-004 (Session logical verification integration), REQ-010 (no content leakage in results)
- **Source issue**: issues/20260903-110305_h0707_add-rag-session-recovery-verification.md
- **Source plan**: plans/20260905-163508_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-144010
- **Related target files**: scripts/db/recovery.py
