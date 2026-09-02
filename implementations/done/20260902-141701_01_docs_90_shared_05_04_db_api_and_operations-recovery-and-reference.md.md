## Goal
Complete `REQ-003`'s remaining portion: fix section 9.7's eventbus bullet, which
still states "`rotate_all_dbs()` excludes this domain" — confirmed false by current
`scripts/db/rotation.py` (`rotate_all_dbs()` calls `rotate_eventbus_db()`).

## Scope
This document covers only this Plan's not-yet-implemented remainder. REQ-001
(section 9.3), REQ-002 (section 9.4), and REQ-004 (ADR-008 cross-reference) are
already **Completed** per the Plan's own Execution Status (verified 2026-09-01,
re-verified 2026-09-02) — not repeated here. REQ-003's "MUST NOT pass
'workflow'/'eventbus'" framing was also already corrected; only the eventbus
bullet's backup-rotation half remains stale. Modify exactly line 79 of
`docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md`.

## Assumptions
- **Corrected 2026-09-02** (Plan Unknowns UNK-02, discovered during this Plan's own
  prior `plan-to-implementation-procedure` Step 3 revalidation): `eventbus.sqlite`
  IS included in `rotate_all_dbs()`'s backup rotation (confirmed:
  `scripts/db/rotation.py` line 76, `eb_dest = rotate_eventbus_db(archive_dir)`).
  Only the corruption-*recovery* half of the bullet ("no corruption-recovery...
  coverage", `no_recovery_allowed`) is accurate — the backup-*rotation* half is
  stale and must be corrected without touching the accurate half.

## Design decisions
Split the bullet's single claim ("no corruption-recovery **or backup-rotation**
coverage") into two independently accurate claims, since the two halves now have
different truth values — mirrors this Plan's own Design principle #3 (scope
discipline: touch only the stale portion).

## Alternatives considered
Removing the backup-rotation claim entirely rather than correcting it — rejected:
leaving no statement about backup-rotation coverage would be a regression in
completeness; the corrected, accurate statement (eventbus IS archived) is strictly
more informative.

## Implementation
### Target file
docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md

### Procedure
Correct the backup-rotation claim in the eventbus bullet (line 79) while preserving
the accurate corruption-recovery claim.

### Method
1. Locate line 79 (current):
   ```
   - **Event delivery state** (`eventbus.sqlite`): has **no corruption-recovery or backup-rotation coverage**. Calling `recover_corruption(target='eventbus')` returns `no_recovery_allowed`; `rotate_all_dbs()` excludes this domain (ADR-008 Decision Details #20).
   ```
2. Replace with:
   ```
   - **Event delivery state** (`eventbus.sqlite`): has **no corruption-recovery path**, but **is included in backup rotation**. Calling `recover_corruption(target='eventbus')` returns `no_recovery_allowed`; `rotate_all_dbs()` archives `eventbus.sqlite` alongside the other three databases (`scripts/db/rotation.py::rotate_eventbus_db()`), but no automated *restoration* path consumes that archive for this domain (ADR-008 Decision Details #20).
   ```

### Details
This correction does not change the sentence's ADR-008 cross-reference (REQ-004,
already satisfied) or the `workflow.sqlite` bullet (line 78, unaffected — that
bullet does not make a backup-rotation claim to begin with).

## Compatibility considerations
Documentation-only change; no code, schema, or runtime behavior affected.

## Security considerations
N/A: no security-relevant content in a backup-rotation-coverage correction.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md` → no new issues.

## Completion criteria
The eventbus bullet no longer claims `rotate_all_dbs()` excludes this domain; it
accurately states eventbus is archived but has no automated restoration path.

## Out of scope
Section 9.5 (UNK-03: a separately-flagged, unconfirmed possible contradiction with
9.4) — explicitly out of this Plan's In-Scope (9.3/9.4/9.7 only); a maintainer
decision is needed on whether to expand scope or file a separate follow-up issue,
per the Plan's own Unknowns table.

## Documentation
This file is itself the Specification being corrected; no separate
`docs/00_index.md` task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct eventbus bullet's backup-rotation claim per Method | Pending | — | — | |
| 2 | N/A: no test to add (doc-only change) | Pending | — | — | N/A |
| 3 | Run validation sequence | Pending | — | — | |
| 4 | Documentation update | Pending | — | — | N/A: this file is the documentation being updated |

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
- **Requirement ID**: REQ-003 (remaining portion: eventbus backup-rotation claim)
- **Source issue**: `issues/20260831-181721_adr008_04_db_api_recovery_spec_staleness.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-131844_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-141701
- **Related target files**: `docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md`
