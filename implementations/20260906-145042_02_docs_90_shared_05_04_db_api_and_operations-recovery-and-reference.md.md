## Goal
Correct section 9.5's stale "Current implementation gaps" list to describe the
actual current, already-correct restoration sequence (REQ-005).

## Scope
- In scope: section 9.5 (lines 53-64) only.
- Out of scope: any other section of this document.

## Assumptions
- **Cross-Plan overlap, check before implementing**: `plans/done/20260905-163508_plan.md`
  (`H-07-07`)'s own implementation procedure
  (`implementations/20260906-144010_11_docs_90_shared_05_04_db_api_and_operations-recovery-and-reference.md.md`,
  seq 11) independently targets this exact same section 9.5, bundling the identical
  stale-gap-list correction this row implements, plus adding new RAG/Session
  logical-verification content (that Plan's own REQ-009). If that row lands first,
  section 9.5's gap-list will already be corrected — this row's implementer MUST
  re-read section 9.5's current state before editing and treat "already corrected by
  H-07-07's seq 11" as satisfying REQ-005 directly (confirm, do not blindly re-apply
  the same edit twice or produce a conflicting second version of the same bullets).
  If this row lands first instead, H-07-07's seq 11 implementer faces the same
  reconciliation in reverse — this is a known, accepted overlap between two Plans
  from the same issue batch, not a defect in either Plan.

## Design decisions
- Write the corrected bullets to be substantively identical in meaning to what
  H-07-07's seq 11 would produce (both cite the same evidence:
  `scripts/db/recovery.py::_restore_from_backup()` lines 117/126-137/140) — so
  whichever lands first, the second implementer's re-check confirms consistency
  rather than finding a conflict.

## Alternatives considered
- Skip this row entirely, relying on H-07-07's seq 11 to cover it: rejected — this
  Plan's own Freeze status commits to this row as one of its 3 Implementation Target
  Files; skipping it would leave `REQ-005`/`AC-8` unimplemented if H-07-07's Plan is
  never executed (it is not a hard dependency of this Plan, per Background/Unknowns
  UNK-02). Implement it here regardless, with the cross-Plan check in Procedure
  step 1.

## Implementation
### Target file
`docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md`

### Procedure
1. Re-read section 9.5 immediately before editing; if its "Current implementation
   gaps" bullets are already corrected (matching this document's Design decisions),
   confirm they are accurate and stop — do not re-apply a duplicate edit.
2. Otherwise, replace the 4 stale bullets (damaged-DB preservation conditional;
   backup integrity never verified; non-atomic replacement; no post-restore
   re-verification) with corrected text stating: backup integrity IS verified before
   use; restoration IS atomic (temp file + `os.replace()`); the restored DB IS
   reopened and re-verified before success is reported — citing
   `_restore_from_backup()` by name, not by line number (per `skills/DESIGN.md` No
   source-code line numbers).

### Method
Confirmed this cycle (2026-09-06) via direct read of `scripts/db/recovery.py`
(lines 90-164, full function read): section 9.5's current 4 "gap" bullets
contradict the actual implementation — backup verification (line 117), atomic
temp-file restoration (lines 126-137), and post-restore re-verification (line 140)
are all already implemented. Confirmed the cross-Plan overlap via direct read of
`implementations/20260906-144010_11_docs_90_shared_05_04_db_api_and_operations-recovery-and-reference.md.md`
(already generated this session, `H-07-07`'s seq 11 — same target section, same
underlying finding).

### Details
No change to any other section.

## Compatibility considerations
N/A: documentation-only.

## Security considerations
N/A.

## Rollback considerations
Revert via `git checkout` on this file alone if `check_docs_quality.py`/
`check_docs_structure.py` flag an issue.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md`
- `uv run python tools/check_docs_structure.py docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md`

## Completion criteria
- Section 9.5 no longer states that atomicity, backup-validation, or
  post-restore-verification are open gaps.
- `check_docs_quality.py`/`check_docs_structure.py` report no new finding.

## Out of scope
- `docs/00_governance_03_issue-and-uncertainty-management.md` — tracked in seq 01.
- `docs/adr/ADR-008-sqlite-4db-separation.md` — tracked in seq 03.
- Section 9.5's RAG/Session logical-verification addition — that is `H-07-07`'s
  REQ-009 (seq 11 of `plans/done/20260905-163508_plan.md`), not this Plan's scope.

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20260903-110307_h0709_reconcile-shared-001-002-003-and-nc-021.md
- **Source plan**: plans/20260905-164204_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-145042
- **Related target files**: docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md
