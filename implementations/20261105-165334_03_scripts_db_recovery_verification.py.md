# Implementation Procedure — `scripts/db/recovery_verification.py`

## Goal

Make mandatory logical verification fail closed in
`scripts/db/recovery_verification.py` (`REQ-005`): a `sqlite3.Error` that blocks
opening the candidate, and an unknown mandatory target, now return an explicit
failure (`verification_unavailable` (new)) instead of `(True, None)` success.

## Scope
**Release unit**: contract activation

## Assumptions

- `_run_logical_verification` (current L111-L128) is the sole consumer-facing entry
  for mandatory post-restore logical verification; it is imported and called only
  by `scripts/db/recovery.py` `_post_restore_failure` (L243). The recovery drill
  uses `_verify_rag_logic` / `_verify_session_logic` directly and is unaffected.
- The current docstring rationale ("a verification gap must never block a
  completed physical restore") is the defect; it must be rewritten, not just
  patched.
- Cross-plan: `_session_inconsistency_detail` (current L63-L84) still carries the
  `write_smoke_fail` trigger (L81) left by `sessmoke001`. That trigger is removed
  by `sessmoke001`, which is sequenced before this Plan. This Plan does **not**
  touch `_session_inconsistency_detail` or `_verify_session_logic`; it changes
  only `_run_logical_verification`.
- Cross-plan: `scripts/db/recovery.py` (seq 02) maps the returned
  `"verification_unavailable"` detail string to the `verification_unavailable` (new)
  action value; keep the contract identical.

## Design decisions

- Distinguish mandatory from non-mandatory unknown targets. The mandatory
  logical-verification domains are `rag` and `session` (they have registered
  verifiers and a restore for them must prove logical consistency before it can
  be reported successful). `workflow` and `eventbus` are unknown here
  (`_LOGICAL_VERIFIERS` has no entry) but are **non-mandatory**: workflow has no
  corruption-recovery path and eventbus has no restoration path (ADR-008), so
  their logical verification is intentionally skipped. Fail closed only for the
  mandatory domains; keep `(True, None)` for non-mandatory unknown targets.
- Concretely: if `target` is a mandatory domain (`rag` or `session`) but
  `_LOGICAL_VERIFIERS.get(target)` is `None`, return
  `(False, "verification_unavailable")`. If `target` is not a mandatory domain,
  return `(True, None)` (unchanged skip).
- For a `sqlite3.Error` while opening the candidate return
  `(False, "verification_unavailable")` and log at error level (the candidate
  cannot be verified, which is a hard failure, not a warning).
- Rewrite the docstring to state that an unverifiable mandatory target fails
  closed.

## Alternatives considered

- Returning `(False, None)` and letting the caller synthesize a message was
  rejected: the caller needs a stable discriminator between
  `logical_verify_failed` and `verification_unavailable` (new), so the detail string is
  returned explicitly.

## Compatibility considerations

- Return type unchanged (`tuple[bool, str | None]`); only the `True` outcomes for
  the two failure cases become `False`. Existing successful-consistency results
  are unchanged.
- No new imports; no change to `_verify_rag_logic` / `_verify_session_logic` or
  the `_LOGICAL_VERIFIERS` table.

## Security considerations

- N/A: behavior change only; no new file or access handling.

## Rollback considerations

- Revert the commit; the pre-change pass-on-unknown behavior is the defect.

## Implementation

### Target file

`scripts/db/recovery_verification.py`

### Procedure

1. In `_run_logical_verification` (current L111-L129): replace the
   `if verify is None: return True, None` branch with a mandatory-target guard:
   return `(False, "verification_unavailable")` when `target` is a mandatory
   domain (`rag` or `session`) with no registered verifier, and keep
   `(True, None)` for non-mandatory unknown targets (`workflow`, `eventbus`).
2. Replace the `except sqlite3.Error` handler (current L126-L128) with
   `return False, "verification_unavailable"` and change the log level from
   `warning` to `error`.
3. Rewrite the docstring to reflect the fail-closed contract.

### Method

```python
_MANDATORY_LOGICAL_TARGETS = frozenset({"rag", "session"})

def _run_logical_verification(db_path: Path, target: str) -> tuple[bool, str | None]:
    """Run logical consistency verification on the restored database.

    Returns (consistent, detail_string) — detail contains a short summary
    of counts/identifiers only (no row content), matching REQ-010/AC-7.

    An unknown mandatory target, or a database this stage cannot open, fails
    closed as (False, "verification_unavailable"): a verification gap must never
    be reported as success for a mandatory check. Non-mandatory targets
    (workflow, eventbus) keep the skip result.
    """
    verify = _LOGICAL_VERIFIERS.get(target)
    if verify is None:
        if target in _MANDATORY_LOGICAL_TARGETS:
            return False, "verification_unavailable"
        return True, None
    try:
        with SQLiteHelper(target, db_path=str(db_path)).open() as db:
            return verify(db)
    except sqlite3.Error as e:
        logger.error("Logical verification could not open DB: %s", e)
        return False, "verification_unavailable"
```

### Details

The returned detail `"verification_unavailable"` is matched by
`scripts/db/recovery.py` `_restore_from_backup` (seq 02) to select the
`verification_unavailable` (new) action value. Do not rename it. Leave
`_session_inconsistency_detail`'s `write_smoke_fail` entry (L81) to
`sessmoke001`; it is out of scope here.

## Validation plan

- `uv run pytest tests/db/test_db_recovery.py -k "logical"` — an injected
  `sqlite3.Error` and an unknown **mandatory** target (`rag`/`session`) return
  the failure action (`verification_unavailable` (new)), not `(True, None)`.
- `uv run pytest tests/db/test_db_recovery.py -k "skips_verification"` — the
  non-mandatory `workflow` target still returns `(True, None)`; this test is
  preserved by seq 05.
- `uv run ruff check . && uv run ruff format --check .`, `uv run lint-imports` —
  clean.

## Completion criteria

- Unknown mandatory target and `sqlite3.Error` both return `(False,
  "verification_unavailable")`.
- The pass-on-unknown behavior no longer exists anywhere in the file; the
  docstring reflects the fail-closed contract.

## Out of Scope

- The verify-before-activation ordering and rollback
  (`scripts/db/recovery.py`, seq 02); the `RecoveryResult` field addition
  (`scripts/db/models.py`, seq 04); sidecar staging
  (`scripts/db/recovery_restore.py`, seq 01).

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
- **Requirement ID**: `REQ-005` (fail-closed mandatory logical verification)
- **Source issue**: issues/20261104-143443_sqliterec001_atomic-fail-closed-sqlite-recovery.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-231726_sqliterec001_atomic-fail-closed-sqlite-recovery.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-165334
- **Related target files**: `scripts/db/recovery_verification.py`
