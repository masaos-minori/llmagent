# Implementation Procedure — `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`

## Goal

Update the database-recovery reference in `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`
to describe the atomic, fail-closed protocol produced by seq 01–06 instead of
the defective behavior it currently documents: full-filename sidecar resolution
and fail-closed staging, verify-the-candidate-then-activate ordering, rollback /
non-serviceable actions, and the `RecoveryResult.active_db_state` contract.

## Scope
**Release unit**: contract activation

## Assumptions

- This doc is edited by this Plan (recovery protocol + result contract) and by
  `sessmoke001` (drill metric table) and `drillmetrics001` (RPO/RTO metric
  definitions). This row edits the recovery protocol (§9.2, §9.5, §9.5a) and the
  result-contract description; it does not touch the drill metric table.
- The current §9.2 boundary text (L34-L35) documents `_stage_restore()` as
  performing the swap and states "a verification gap never blocks a completed
  physical restore" — both are the defective behavior being removed.
- Cross-plan: ADR-008 is frozen; this doc must not contradict it. Workflow has no
  corruption-recovery path and eventbus has no restoration path (ADR-008); keep
  those statements (§9.7).

## Design decisions

- Rewrite the restore-file-staging boundary (L34) to state that staging resolves
  the full-filename `-wal`/`-shm` sidecars, quarantines/stages them with
  fail-closed semantics (failures raise, per `recovery_restore.py` seq 01), and
  no longer performs the atomic swap — activation moves to
  `recover_corruption()` after candidate verification.
- Remove the sentence "a verification gap never blocks a completed physical
  restore" (L35) and replace it with the fail-closed contract: a mandatory
  logical-verification gap fails closed as `verification_unavailable`.
- Update §9.5 "Safe restoration sequence" (L57-L65) to reflect
  verify-before-activate: stage the complete candidate unit, run integrity +
  logical verification on the staged candidate, activate only a fully verified
  set with a single atomic swap, and on post-activation failure restore the
  archived original or report a non-serviceable state.
- Document the `RecoveryResult.active_db_state` values (`restored`,
  `preserved_original`, `non_serviceable`) and the new `verification_unavailable`
  action value.

## Alternatives considered

- Editing only L34 was rejected: the "verification gap never blocks" sentence on
  L35 and the "restoration IS atomic ... replaces the target via os.replace"
  statement on L63 describe the defective protocol and would be left stale.

## Compatibility considerations

- This doc references `scripts/db/recovery.py`, `recovery_restore.py`,
  `recovery_verification.py`, and `scripts/db/models.py`; the prose must match
  their post-change contracts. No consumer code changes here.

## Security considerations

- N/A: documentation change only.

## Rollback considerations

- Revert the commit; the pre-change prose characterizes the defective protocol.

## Implementation

### Target file

`docs/41_db/db_07_api_and_operations-recovery-and-reference.md`

### Procedure

1. §9.2 (L34): rewrite the restore-file-staging bullet so it states that staging
   resolves the full-filename `-wal`/`-shm` sidecars (`<db>.sqlite-wal`,
   `<db>.sqlite-shm`), quarantines and stages them with fail-closed semantics
   (a quarantine/copy/rename/placement failure raises rather than logging a
   warning and proceeding), and no longer performs the atomic swap — activation
   is performed by `recover_corruption()` after candidate verification.
2. §9.2 (L35): delete the sentence "a verification gap never blocks a completed
   physical restore" and replace it with: a mandatory logical-verification gap
   fails closed as `verification_unavailable` and blocks activation.
3. §9.5 (L57-L65): update the "Current implementation status" bullets to reflect
   verify-before-activate — the candidate (database plus sidecars) is verified
   with `_run_integrity_check` and `_run_logical_verification` before the single
   atomic swap; a failed candidate verification leaves the live database
   untouched; a post-activation failure restores the archived original or reports
   a non-serviceable state.
4. Add a short note on the `RecoveryResult` active-state contract:
   `active_db_state` ∈ {`restored`, `preserved_original`, `non_serviceable`} and
   the `verification_unavailable` action value.
5. Preserve the ADR-008-consistent statements: workflow has no
   corruption-recovery path, eventbus has no restoration path (§9.7).

### Method

- Match the prose to the exact contract strings set by seq 02
  (`scripts/db/recovery.py`) and seq 03 (`scripts/db/recovery_verification.py`):
  the `verification_unavailable` detail/action and the three
  `active_db_state` values. Do not invent additional action values.

### Details

Before (defective, current L35):

> ... a verification gap never blocks a completed physical restore, and
> `db/recovery.py` turns the outcome into `logical_verify_failed`.

After (fail-closed):

> ... a mandatory logical-verification gap fails closed as
> `verification_unavailable` and blocks activation; `db/recovery.py` maps it to
> the `verification_unavailable` action value.

### Details (before/after, current L63):

Before:

> Restoration IS atomic: `_stage_restore()` copies the backup to a temporary file
> via `shutil.copy2()`, then replaces the target via `os.replace()` ...

After:

> Restoration IS atomic: the complete candidate unit (database plus its
> `-wal`/`-shm` sidecars) is staged under a temporary location, verified with the
> integrity and logical-verification checks, and only a fully verified candidate
> is activated by a single atomic `os.replace` of the database plus a move of
> each sidecar to its final full-filename location. A candidate that fails
> verification is never activated; the live database is untouched.

## Validation plan

- Re-read §9.2, §9.5, §9.5a against `scripts/db/recovery.py`,
  `recovery_restore.py`, `recovery_verification.py`, and `scripts/db/models.py`
  to confirm the prose matches the post-change contracts.
- Confirm no residual "verification gap never blocks" or "proceeding without it"
  language remains in the recovery section.

## Completion criteria

- §9.2 documents full-filename sidecar resolution, fail-closed staging, and
  verify-before-activate.
- The "verification gap never blocks" statement is removed.
- §9.5 reflects the candidate-then-activate ordering, rollback, and
  non-serviceable state.
- The `active_db_state` contract and `verification_unavailable` action value are
  documented.

## Out of Scope

- The recovery protocol source changes
  (`scripts/db/recovery.py` seq 02, `scripts/db/recovery_restore.py` seq 01,
  `scripts/db/recovery_verification.py` seq 03, `scripts/db/models.py` seq 04);
  this row documents them.
- The recovery-drill metric table (`sessmoke001`, `drillmetrics001`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Companion test row seq 05 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: docs updated by seq 07 |

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
- **Requirement ID**: `REQ-006`, `REQ-007` (restore protocol, result contract, exclusive-access requirement)
- **Source issue**: issues/20261104-143443_sqliterec001_atomic-fail-closed-sqlite-recovery.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-231726_sqliterec001_atomic-fail-closed-sqlite-recovery.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-165334
- **Related target files**: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`
