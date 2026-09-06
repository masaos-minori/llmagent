## Goal
Update section 9.5 (Safe restoration sequence) and 9.7 (Persistence-domain policy) to
state the new RAG/Session logical-verification stage and which checks are automated
vs. operator-only (REQ-009); correct section 9.5's stale "Current implementation
gaps" bullets discovered during this cycle's investigation, bundled into the same
edit since they occupy the exact same subsection this row already targets.

## Scope
- In scope: section 9.5 (lines 53-64) and section 9.7 (lines 71-81) only.
- Out of scope: sections 9.1-9.4, 9.6, 9.8, 9.9, or any other section of this
  document; any other `docs/*.md` file.

## Assumptions
- This row executes after seq 01/02/03 land, so the "automated vs. operator-only"
  breakdown can be stated accurately (e.g. the write smoke test's final
  in-scope/operator-only disposition depends on seq 03's UNK-02 resolution).

## Design decisions
- Bundle a correction of section 9.5's stale "Current implementation gaps" bullets
  into this same row rather than filing it as a separate, unrelated documentation
  task: this cycle's direct read of `scripts/db/recovery.py` (Method below) found
  those bullets describe a pre-`SHARED-002`-fix state of the code that no longer
  matches current source — leaving them stale while adding new logical-verification
  content directly beneath them in the same subsection would read as self-contradictory
  (the corrected bullets and the new content both describe verification that already
  exists). This is a bounded correction to the exact subsection REQ-009 already
  targets, not an expansion to a different file or section.
- State the automated/operator-only breakdown as a short bullet list appended to 9.5
  (mirroring 9.8's existing prose style), rather than a new subsection — keeps the
  section count stable and matches this document's existing granularity.

## Alternatives considered
- Leave section 9.5's stale bullets untouched and only add new 9.5/9.7 content:
  rejected per Design decisions — would leave a documentation-governance defect
  identical in kind to the one `SHARED-002`/`NC-021`-style entries already exist to
  prevent (a doc claiming a gap that current code has already closed).
- File the 9.5 staleness as a separate follow-up issue instead of fixing it here:
  considered, but rejected since it is a small, mechanical correction (replacing 4
  bullets with accurate ones) well within the effort of a single documentation row,
  and leaving it stale would undermine this same row's own new content's credibility.

## Implementation
### Target file
`docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md`

### Procedure
1. Replace section 9.5's "Current implementation gaps against this sequence" bullets
   (currently 4 bullets claiming: damaged-DB preservation is conditional; backup
   integrity is never verified; restoration is not atomic; the restored DB is not
   reopened/re-verified) with corrected bullets stating: backup integrity IS verified
   before use (`_run_integrity_check(backup, target)`, confirmed at
   `_restore_from_backup()`'s current line 117); restoration IS atomic (copy to a
   temp file via `shutil.copy2()`, then `os.replace()`, confirmed at current lines
   136-137); the restored DB IS reopened and re-verified before success is reported
   (`_run_integrity_check(db_path, target)`, confirmed at current line 140) — cite
   symbol/method names per `skills/DESIGN.md` No source-code line numbers (do not
   carry the line numbers themselves into the doc text, only into this procedure
   document's own evidence).
2. Add a new bullet (or short sub-list) to section 9.5 stating: after the physical
   re-check succeeds, a RAG or Session logical-verification stage runs
   (`check_rag_consistency()`/`check_session_consistency()` per `target`) before
   `success=True` is returned; a logical-verification failure produces `success=False`
   with an `action` value distinct from `restore_verify_failed`.
3. Update section 9.7's RAG/Session bullets to note that `recover_corruption()`'s
   restoration path for both domains now includes this logical-verification stage,
   cross-referencing 9.5 rather than restating it.
4. Add a short "automated vs. operator-only" breakdown (per REQ-009's explicit
   wording) — re-derive from seq 01/03's landed implementation which checks run
   unconditionally inside `check_rag_consistency()`/`check_session_consistency()`
   (automated) versus which repair actions the logical-verification stage only
   recommends but does not itself perform (e.g. `/session rag-rebuild-fts`,
   operator-triggered).

### Method
Confirmed this cycle (2026-09-06) via direct read of `scripts/db/recovery.py`
(lines 90-164, already read in full for seq 01): section 9.5's current 4 "gap"
bullets are stale — backup verification (line 117), atomic temp-file restoration
(lines 127, 136-137), and post-restore re-verification (line 140) are all already
implemented, contradicting the doc's claim that these are "open implementation gaps,
not yet satisfied." Confirmed section 9.7 (lines 71-81) already correctly states
`recover_corruption(target='session')`/`target='rag')` support restoration — only the
new logical-verification-stage detail is missing, not a wholesale rewrite.

### Details
No change to sections 9.1-9.4 (Purpose, Responsibility boundaries, Integrity-result
model, Exception policy), 9.6 (Dry Run contract — already accurate per this cycle's
read), 9.8 (Operational considerations), or 9.9 (Implementation references) — confirm
9.9's symbol list does not need a new entry for `check_rag_consistency`/
`check_session_consistency` only if REQ-009's own scope is read to include it;
default to leaving 9.9 unchanged since REQ-009 names only 9.5/9.7.

## Compatibility considerations
N/A: documentation-only.

## Security considerations
N/A.

## Rollback considerations
Revert via `git checkout` on this file alone if `check_docs_quality.py`/
`check_docs_structure.py` flag a structural issue after the edit.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md`
- `uv run python tools/check_docs_structure.py docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md`
- Manual cross-check: section 9.5's corrected bullets match `scripts/db/recovery.py`'s
  then-current line-level behavior (re-verify, do not assume this document's citations
  are still accurate at implementation time).

## Completion criteria
- Section 9.5 no longer states that atomicity, backup-validation, or
  post-restore-verification are open gaps.
- Section 9.5 states the new logical-verification stage and its
  `action`-value-distinguishing behavior.
- Section 9.7 cross-references the logical-verification stage for both domains.
- An automated-vs-operator-only breakdown is present per REQ-009.
- `check_docs_quality.py`/`check_docs_structure.py` report no new finding.

## Out of scope
- Sections 9.1-9.4, 9.6, 9.8, 9.9.
- Any other `docs/*.md` file.

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
- **Requirement ID**: REQ-009
- **Source issue**: issues/20260903-110305_h0707_add-rag-session-recovery-verification.md
- **Source plan**: plans/20260905-163508_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-144010
- **Related target files**: docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md
