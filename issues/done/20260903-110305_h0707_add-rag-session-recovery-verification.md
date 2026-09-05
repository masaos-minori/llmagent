# Add RAG and Session database recovery verification

## Priority
Medium

## Summary
Implement and test database-specific recovery verification for `rag.sqlite` and `session.sqlite` after physical restoration.

## Background
SQLite physical integrity does not guarantee that application-level relationships, FTS data, vector data, sessions, messages, memories, and links are usable. RAG and Session are the database targets described as supported by the current generic recovery path. Physical restoration and its verification are already implemented: `scripts/db/recovery.py`'s `_restore_from_backup()` validates the backup's physical integrity before use, performs atomic staged replacement (`shutil.copy2()` to a temp file, then `os.replace()`), archives the prior corrupt database, and re-runs `_run_integrity_check()` on the restored file before reporting success — returning `action="restore_verify_failed"` on failure (confirmed by direct read; also recorded as resolved in `docs/90_shared_90_inconsistencies_and_known_issues.md` SHARED-002).

## Problem
The existing post-restore verification in `_restore_from_backup()` re-runs only `_run_integrity_check()`, which performs SQLite-level physical integrity checking (confirmed by direct read of `scripts/db/recovery.py`) — it does not call `check_rag_consistency()` or any Session-specific logical check. A restored `rag.sqlite` or `session.sqlite` can therefore report `success=True` while missing required tables, having FTS/vector orphans, or containing invalid message/memory relationships.

## Reason for Change
Define and enforce the minimum logical conditions required before a restored RAG or Session database may be returned to service, closing the gap between "physically valid" and "usable by the application."

## Implementation Intent
Integrate database-specific logical verification into the existing post-restore verification step in `_restore_from_backup()`, immediately after the current physical `_run_integrity_check()` re-check succeeds and before `success=True` is returned.

### RAG verification requirements

Inspect the current RAG schema and consistency implementation, then verify at least:

- Required tables exist
- Required FTS and vector structures exist where configured
- Required triggers exist
- Document-to-chunk relationships are valid
- FTS gap is zero or is repaired through an explicitly approved rebuild
- FTS orphan count is zero
- Vector orphan count is zero
- Vector count requirements follow the actual embedding-failure model
- Read-only search smoke test succeeds
- Any permitted rebuild is distinguished from physical restoration

Reuse `check_rag_consistency()` (`scripts/db/rag_consistency.py`, confirmed to exist but confirmed not currently called from `scripts/db/recovery.py`) where it is authoritative and sufficient. Do not duplicate its logic without justification.

### Session verification requirements

Inspect the current Session schema and stores, then verify at least:

- Required tables exist
- Sessions can be read
- Messages reference valid sessions where foreign-key policy requires it
- Memories and memory links satisfy the approved logical rules
- Session diagnostics can be read
- A read smoke test succeeds
- A write smoke test succeeds only if the recovery policy allows mutation during verification
- Data loss between the backup point and failure point is reported without exposing message or memory content

## Target Files or Areas
- `scripts/db/rag_consistency.py`
- RAG schema, triggers, and vector definitions
- Session schema and stores
- `scripts/db/recovery.py` (the existing post-restore verification step in `_restore_from_backup()`)
- RAG maintenance service
- Session recovery CLI
- RAG and Session recovery tests
- DB recovery documentation

## Required Changes
1. Define a result model for domain logical verification.
2. Integrate the result with the existing post-restore verification step in `_restore_from_backup()` — do not re-implement physical verification, which is already correct.
3. Keep physical integrity and logical consistency as separate result fields.
4. Do not report recovery success when required logical checks fail.
5. Do not automatically delete data to make validation pass.
6. Do not rebuild authoritative data from derived indexes.
7. Record only safe counts, identifiers permitted by policy, and error categories.
8. Add fault-injection fixtures for logical corruption where practical.
9. Document any check that cannot be automated and mark it as an operator step.

## Constraints
Do not modify `_restore_from_backup()`'s existing physical-verification sequence (backup validation, atomic staging, corrupt-archive, physical re-check) — this issue only adds a logical-verification stage after that sequence succeeds.

## Acceptance Criteria
- [ ] RAG and Session have separate logical verification functions.
- [ ] Physical and logical results are distinguishable.
- [ ] RAG verification covers required tables, triggers, FTS, vector state, and read behavior.
- [ ] Session verification covers required tables, relationships, and read behavior.
- [ ] A logical verification failure prevents recovery success.
- [ ] Derived-data rebuild is not confused with physical restoration.
- [ ] Authoritative data is not reconstructed from a derived index.
- [ ] Verification logs do not expose document, message, memory, or row content.
- [ ] Fault-injection and regression tests cover required cases.
- [ ] Documentation states which checks are automated and which require an operator.

## Testing Expectations
### RAG

- Valid restored RAG database
- Missing required table
- Missing required trigger
- FTS gap
- FTS orphan
- Vector orphan
- Search smoke-test failure
- Approved derived-index rebuild succeeds
- Rebuild fails and recovery remains unsuccessful

### Session

- Valid restored Session database
- Missing required table
- Orphaned message or invalid relationship where schema permits simulation
- Invalid memory-link relationship
- Read smoke-test failure
- Write smoke-test failure where applicable
- Recovery result reports failure without logging content

## Documentation Impact
Yes — update DB recovery documentation to state that post-restore verification includes RAG/Session-specific logical checks in addition to the existing physical integrity re-check, and to state which checks are automated versus operator-only.

## Out of Scope
- Do not implement Workflow or EventBus logical verification in this issue (see `H-07-08`).
- Do not change RAG ingestion or Session retention policy.
- Do not silently repair authoritative data.
- Do not re-implement backup validation, atomic staging, or physical post-restore re-verification — these are already implemented in `_restore_from_backup()` (SHARED-002, resolved).

## Dependencies
Depends on `H-07-01` (filed alongside this issue, defines the persistence-domain terminology this issue's logical-verification stage is classified under). Does not depend on further physical-recovery implementation work — backup validation, atomic staged replacement, and post-restore physical re-verification are already implemented and resolved (SHARED-002, `docs/90_shared_90_inconsistencies_and_known_issues.md`).

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Read `scripts/db/recovery.py`'s `_restore_from_backup()` and `scripts/db/rag_consistency.py`'s `check_rag_consistency()` in full before implementing — confirm the exact integration point (after the existing physical `_run_integrity_check()` re-check, before `success=True` is returned) rather than assuming where logical verification belongs. Do not re-implement or modify the existing physical-verification sequence; SHARED-002 is already resolved and out of this issue's scope. If `check_rag_consistency()` cannot be reused as-is (e.g. it assumes a different call context), state why in the implementation rather than duplicating its logic silently.
