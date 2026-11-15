## Goal
- State whole-unit failure-path semantics and quarantine retention in the recovery contract docs.

## Scope
**Release unit**: whole-unit-rollback-retention (Phase 4 of the plan; lands after the code/test documents and after Plan 002's docs procedure `20261115-080732_3`)

- In scope: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` — the staging helper text (line 34) and the verification/restore contract bullets (line 63) (REQ-006).
- Cross-plan overlap `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` (shared by Plans 004/008/009): **compatible sections, sequencing** — this document edits lines 34 and 63; Plan 002's doc procedure already landed edits at 64-66 (re-read the landed text before editing); Plan 004 owns the probe section, Plan 009 edits section 12, Plan 008 edits section-12 lifecycle text (its quarantine sweep consumes this document's retention decision).

## Assumptions
- The plan's original line-77 citation does not exist (plan Correction 1, verified this cycle): the cleanup/quarantine claims to edit are at `db_07:34` ("Staging is fail-closed... caller's cleanup handler") and `db_07:63` ("A candidate that fails verification is never activated: the live database is untouched... cleans up the half-written temp files and preserves the archive").
- Retention is the maintainer decision recorded 2026-11-15 (retain on success; cleanup delegated to artifact-retention policy) — stated in behavior/intent terms, no implementation identifiers beyond existing vocabulary.

## Design decisions
- Extend the two existing sentences in place (whole-unit reassembly clause at line 63; records/deferral clause at line 34) plus one new bullet for retention after success — keeps the shared file's bullet structure stable for the later plans' disjoint edits.

## Alternatives considered
- Adding a new subsection for sidecar handling: rejected — four other plans edit adjacent bullets of this section; a new subsection increases edit conflict surface without adding clarity.

## Implementation
### Target file
`docs/41_db/db_07_api_and_operations-recovery-and-reference.md`

### Procedure
1. Line 34 (restore file staging bullet): state that staging returns the quarantine records (live name → quarantine path) to `db/recovery.py`, and the quarantine directory is created only when a sidecar is actually quarantined (REQ-006).
2. Line 63 (restoration contract bullet): extend "A candidate that fails verification is never activated: the live database is untouched" with the whole-unit clause — its quarantined `-wal`/`-shm` sidecars are moved back to their live names before the failure is reported, so the live directory always holds the complete original unit on failure; a post-activation rollback additionally removes candidate sidecars activated at live names before restoring the archived original and moving the quarantined originals back (REQ-006, AC-4).
3. Add a retention sentence in the same bullet region: after a successful restore the quarantine directory and its copies are retained as a forensic archive (the corrupt WAL may contain transactions the backup lacks); lifetime/cleanup is owned by the artifact-retention policy documented in ADR-008 and section 12 (REQ-006, AC-4).
4. Do not restate Plan 002's lines 64-66 rollback wording; re-read the landed text first and keep this document's edits adjacent-but-disjoint (plan overlap scan record).

### Method
- Direct markdown edit after the code documents have landed.

### Details
- Vocabulary check: no new action/state tokens appear; only filesystem-behavior descriptions are added.

## Compatibility considerations
- Docs-only; `tools/check_docs_consistency.py --domain db` gate.

## Security considerations
- N/A: documentation text only.

## Rollback considerations
- Checkout revert; revert together with the code documents when the whole unit rolls back.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain db` → No findings (AC-4).
- Read-back: the retention sentence and whole-unit clause match the landed behavior asserted by companion `_3` tests.

## Completion criteria
- Lines 34 and 63 region state whole-unit failure semantics and retention; docs checker clean.

## Out of Scope
- ADR-008 retention decision record (companion `_5`).
- Section 12 lifecycle/cleanup text (Plan 008).
- Probe section (Plan 004).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261115-104412 | 20261115-104412 | staging section (whole-unit staging, lazy mkdir dir <db-stem>_sidecar_quarantine_<ts>, retention, mid-quarantine rollback) + failure-semantics bullets (pre-activation quarantine-back, activation-failure whole-unit restore) landed |
| 2 | Add or update tests per Validation plan | Completed | 20261115-104412 | 20261115-104412 | N/A: docs-only validation plan (checkers) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261115-104412 | 20261115-104412 | check_docs_quality/structure/content-policy --strict/consistency --domain db all exit 0; ADR-008 size ceiling re-recorded 36570->37175 in check_docs_structure.py |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261115-104412 | 20261115-104412 | N/A: this file is the documentation |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/done/20261114-092850_dbreview003_restore-sidecar-handling.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-041125_dbreview003_restore-sidecar-handling.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-082016
- **Related target files**: docs/41_db/db_07_api_and_operations-recovery-and-reference.md