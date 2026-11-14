# A failure during candidate activation leaves an unverified backup live with no rollback

## Priority
High

## Summary
In `db.recovery._restore_from_backup`, the `activated` flag is set only after `_activate_candidate` returns. If `os.replace` succeeds and a later sidecar `shutil.move` raises `OSError`, the live path already holds the unverified candidate but the handler skips the rollback and reports a plain `error`.

## Background
Found by an adversarial review of `scripts/db` at commit 0fe68d3 (Review finding F-002). The `except OSError` handler contains a rollback branch guarded by `activated and corrupt_archive.exists()` whose comment says the live path must never hold an unverified file; the flag ordering defeats that guarantee. Evidence label: `Verified by test` (ad hoc reproduction), confidence High.

## Problem
- `_activate_candidate` performs `os.replace(temp_restore, db_path)` and then moves each staged sidecar. Any failure after the replace leaves the candidate live.
- `activated = True` is assigned on the line after the call, so the exception skips it.
- Reproduction (target `workflow`, `_activate_candidate` replaced by a function that calls `os.replace` and then raises `OSError`): result `action="error"`, `active_db_state=None`, and the live database contained the backup's table (`fromBackup`) instead of the original (`orig`). The caller is told nothing about the live state.
- `_cleanup_staged` also runs inside the handler and can itself raise `OSError`, escaping the function.

## Reason for Change
The restore contract (REQ-002/REQ-003) is fail-closed: an unverified file must never be the live database, and the result must state the live database state. Both are violated on this path.

## Implementation Intent
Track activation so that any failure after the swap begins triggers the same rollback and state reporting as the post-activation verification failure, and make the handler's cleanup non-raising. Report `active_db_state` explicitly on every failure path.

## Target Files or Areas
- `scripts/db/recovery.py` (`_restore_from_backup`, `_activate_candidate`, `_cleanup_staged`, `_rollback_or_non_serviceable`)
- `tests/db/test_db_recovery.py`

## Required Changes
- Mark the swap as started before or inside `_activate_candidate` so a partial activation is rolled back.
- Ensure the rollback also removes any sidecars already moved in (see the sidecar issue below).
- Report `active_db_state` (`preserved_original` or `non_serviceable`) for the activation-failure path.
- Make `_cleanup_staged` tolerate `OSError` per file and log it.

## Constraints
- Keep the single atomic `os.replace` of the database file.
- Do not change the `RecoveryResult` action vocabulary without a documented reason.

## Acceptance Criteria
- A forced `OSError` after `os.replace` restores the archived original and returns `active_db_state="preserved_original"`.
- If that rollback also fails, the result is `rollback_failed` / `non_serviceable`.
- A failing `_cleanup_staged` unlink no longer raises out of `_restore_from_backup`.

## Testing Expectations
Unit tests that inject a failure at each step of `_activate_candidate` (after replace, after first sidecar move) and assert the live file content and the reported state. Run `uv run pytest tests/db`.

## Documentation Impact
Update the recovery action/state description in the ADR-008 documentation only if the set of reported states changes.

## Out of Scope
- Verification logic and the vec extension problem (`issues/20261114-092848_dbreview001_logical-verify-vec-extension.md`).
- Sidecar quarantine semantics beyond what the rollback needs.

## Dependencies
- Coordinate with `issues/20261114-092850_dbreview003_restore-sidecar-handling.md`, which edits the same functions.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Follow `skills/python-implementation/SKILL.md`. Modify only the listed files. Preserve the existing result field semantics. English comments and logs only.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261114-092849
- **Related target files**: scripts/db/recovery.py, tests/db/test_db_recovery.py
