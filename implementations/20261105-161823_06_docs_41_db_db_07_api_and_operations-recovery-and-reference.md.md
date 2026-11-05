## Goal

Replace the "write smoke test" wording in the recovery/reference doc so it describes the
read-only session/RAG verification contract. The automated logical-verification stage now
performs only read-only probes; there is no write smoke test.

## Scope
**Release unit**: session report contract removal

## Assumptions

- The doc wording change is cosmetic relative to behavior: it reflects the source change in
  `scripts/db/session_consistency.py` (seq 01) where the write probe is deleted. It must
  land in the same release unit so the doc does not describe a probe that no longer exists.
- The rest of the sentence's claims (FTS/index health + chunk-to-FTS referential integrity
  for RAG; table existence + orphaned messages/memory links for Session) are accurate and
  unchanged.

## Design decisions

- Edit the single clause in place rather than rewrite the paragraph: the only false claim is
  "and a write smoke test (both)". Replace it with language stating both domains verify
  read-only.

## Alternatives considered

- Rewriting the whole paragraph versus editing one clause. Chose in-place clause edit: the
  task requires changing only what the current task needs (AGENTS.md global rule 5), and the
  surrounding claims are correct.

## Implementation
### Target file
`docs/41_db/db_07_api_and_operations-recovery-and-reference.md`

### Procedure
1. Open the doc and locate the sentence in section 9.5a (current L69):
   ```
   ...table existence and orphaned messages / memory links (Session), and a write smoke
   test (both). The logical-verification stage only **recommends** repair...
   ```
2. Replace the clause `and a write smoke test (both)` so the sentence reads:
   ```
   ...table existence and orphaned messages / memory links (Session); both domains verify
   read-only (no write smoke test). The logical-verification stage only **recommends**
   repair...
   ```
3. Grep the doc for `write smoke` / `write_smoke_test_ok` and confirm zero remaining references.

### Method
In-place clause replacement. No structural change.

### Details
- The sentence enumerates what each automated logical-verification stage checks. The only
  stale token is the write-smoke mention; removing it leaves an accurate read-only contract
  statement (REQ-006/AC-006).
- This doc change must land in the same release unit as seq 01; otherwise the doc describes a
  write smoke test that the code no longer performs.

## Compatibility considerations
Doc-only wording change reflecting the read-only contract (REQ-006/AC-006). No behavioral or
API change.

## Security considerations
N/A: documentation wording only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Manual review of the edited sentence for accuracy.
- Confirm no other doc in `docs/41_db/` or `docs/10_adr/` asserts a session write smoke test
  (repo-wide grep for `write smoke` in `docs/`).

## Completion criteria
- Section 9.5a no longer states that session/RAG verification includes a write smoke test.
- The sentence describes both domains as read-only.
- Zero remaining "write smoke" references in the affected doc.

## Out of Scope
The probe/wiring removal (`scripts/db/session_consistency.py`, seq 01), the field removal
(`scripts/db/models.py`, seq 02), the trigger removal (`scripts/db/recovery_verification.py`,
seq 03), and the tests (seq 04/05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | In-place clause edit. |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: docs only. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | This document is the doc change. |

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
- **Requirement ID**: `REQ-006` (doc describes read-only verification contract)
- **Source issue**: issues/20261104-143443_sessmoke001_atomic-session-smoke-test.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-230832_sessmoke001_atomic-session-smoke-test.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-161823
- **Related target files**: docs/41_db/db_07_api_and_operations-recovery-and-reference.md
