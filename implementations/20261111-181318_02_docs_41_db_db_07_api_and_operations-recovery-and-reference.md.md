## Goal

Remove the self-contradiction in `db_07` section 9.2 so its "Backup provider" claim matches 9.5 and `scripts/db/recovery.py::_backup_is_usable()`: backup integrity IS verified before use, per `REQ-002`.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The contradiction is between two bullets in the same document: 9.2 (line 36) says nothing validates a backup's integrity before use, while 9.5 (line 62) says it IS verified. Both describe the same current code.
- The resolution is unambiguous and wording-only: the code (`_backup_is_usable()`) does verify the backup, so 9.2 is the stale half and 9.5 is correct.
- No other section contradicts 9.5; the fix restores a single consistent claim.

## Design decisions

- Change only the stale 9.2 bullet; leave 9.5 (line 62) and all other text byte-identical.
- Keep the corrected 9.2 wording consistent with the "Backup provider" bullet's role (it describes what the backup-provider/caller side guarantees and how validity is established).

## Alternatives considered

- N/A: documentation-only; no runtime behavior, persistence, or public-interface impact.

## Implementation
### Target file
`docs/41_db/db_07_api_and_operations-recovery-and-reference.md`

### Procedure

1. Edit the **9.2 Responsibility boundaries** "Backup provider" bullet (current line 36). Replace the sentence "Nothing in the current implementation validates the backup's own integrity before it is used — see 9.4 and 9.5" with a statement that the backup's integrity IS verified before it is used, pointing to `db/recovery.py::_backup_is_usable()` (which runs `_run_integrity_check(backup, target)` and a domain-identity check before any copy) and to 9.5. Keep the rest of the bullet ("the caller-supplied `backup_path`") intact.

### Method

- Suggested replacement for the stale sentence: "The caller-supplied `backup_path`. The backup's own integrity IS verified before it is used: `db/recovery.py::_backup_is_usable()` runs `_run_integrity_check(backup, target)` plus a domain-identity check and rejects a corrupt or wrong-domain backup before any copy (see 9.5). A corrupted backup is detected and rejected."

### Details

- Evidence (verified against current source, HEAD `e700efa5f`):
  - **9.2 "Backup provider"** (line 36) currently reads: "Nothing in the current implementation validates the backup's own integrity before it is used — see 9.4 and 9.5."
  - **9.5** (line 62) reads: "Backup integrity IS verified before use (`_run_integrity_check(backup, target)`). A corrupted backup is detected and rejected."
  - `recovery.py::_backup_is_usable()` (line 180) calls `_run_integrity_check(backup, target)` (via `_run_integrity_check()`, line 91) and `_verify_domain_identity()`, returning `"bad_backup"` on failure — i.e., the backup IS validated before it is copied in (`_restore_from_backup()`, line 354 checks the result before staging).
- Do not touch 9.5 or any other section. Keep every other byte identical (Plan Risks: scope the edit to the single clause; re-run `check_docs_consistency.py --domain db` against `HEAD` before committing).

## Compatibility considerations

- N/A: documentation-only; no source, config, schema, migration, deployment, or public-interface change.

## Security considerations

- N/A: no security-relevant behavior change; the correction aligns documentation with existing fail-closed backup validation.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

| Action | Tool / Command | Expected Outcome |
|---|---|---|
| Cross-domain claim consistency (9.2 vs 9.5, and vs code) | `uv run python tools/check_docs_consistency.py --domain db` | Pass |
| Japanese-text policy | `uv run python tools/check_docs_japanese.py` | Pass (English only) |

## Completion criteria

- 9.2's "Backup provider" bullet states that backup integrity IS verified before use.
- 9.2 and 9.5 no longer contradict; 9.5 (line 62) is unchanged.
- `check_docs_consistency.py --domain db` and `check_docs_japanese.py` pass.

## Out of Scope

- Re-describing the full restore sequence (already covered by 9.5).
- Any change outside the 9.2 "Backup provider" bullet.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (make `db_07` 9.2/9.5 consistent on backup-integrity verification)
- **Source issue**: `issues/20261109-112922_adrrev009_adr008-recovery-align.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261110-233648_adrrev009_adr008-recovery-align.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-181318
- **Related target files**: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`
