## Goal
- Update the recovery action/state contract text so it states that in-activation failures roll back with the same vocabulary as post-activation verification failures.

## Scope
**Release unit**: activation-rollback-reporting (Phase 4 of the plan; docs land after the code and test documents)

- In scope: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` lines 64-66 region (post-activation failure paragraph and the Result contract bullet) (REQ-006).
- Cross-plan overlap `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` (shared by Plans 003/004/008/009): **compatible sections, sequencing** — this document edits only the failure-paragraph and Result-contract bullets; Plan 003 later edits line 77 ("Staged candidates are removed on every terminal path") and the quarantine retention text; Plan 004 owns the probe section; Plan 009 edits section 12; Plan 008 edits section-12 lifecycle text. Batch order 002 → 003 → 004 → 008/009; re-read the landed text before the later plans' doc procedures.

## Assumptions
- Baseline this cycle: the current paragraph (line 65) already describes the post-activation rollback and `rollback_failed`; the change is extending it to in-activation failures and stating that `active_db_state` is always populated on the `OSError` handler path (checked in Step 3 consumer scan; `scan_change_consumers.py --seed rollback_failed` named this file).
- ADR-008 (`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`) needs no edit: its state enumeration (`restored`/`preserved_original`/`non_serviceable`) and test-citation table stay accurate (Plan Reference Files); update only if `check_docs_consistency.py` fails after the code lands.

## Design decisions
- Edit in behavior/intent terms (shared docs rules): describe what the handler does, not implementation identifiers beyond the existing action/state vocabulary.
- Keep the existing bullet structure; extend rather than restructure so Plan 003/004/008/009's later edits to other bullets stay disjoint.

## Alternatives considered
- Rewriting the whole section 9.5 block: rejected — enlarges the shared-file edit window and risks conflicts with the four later plans that touch adjacent bullets.
- Adding a new vocabulary row for activation failures: rejected — the plan's Design keeps the existing tokens (`error`, `rollback_failed`, `preserved_original`, `non_serviceable`).

## Implementation
### Target file
`docs/41_db/db_07_api_and_operations-recovery-and-reference.md`

### Procedure
1. In the failure paragraph (the bullet beginning "The logical-verification stage runs on the candidate before activation and again after activation", line 65): state that a failure during activation itself — after the atomic database `os.replace` has completed but before every sidecar move finished — is treated as a post-activation failure: sidecars the activation already moved to live names are removed, the archived original is put back (`active_db_state="preserved_original"`), and a failed rollback reports `action="rollback_failed"` with `active_db_state="non_serviceable"` (REQ-006, AC-4).
2. In the Result contract bullet (line 66): state that `active_db_state` is populated on every failure path that begins after the database swap completed, and that `rollback_failed` covers rollback failures on both the verification-failure and activation-failure paths (REQ-006, AC-4).
3. Do not touch line 63 (whole-unit wording is Plan 003's scope) or line 77 (retention wording is Plan 003's scope).

### Method
- Direct markdown edit after the code document (`20261115-080732_1`) has landed, so the text describes shipped behavior.

### Details
- Re-read the landed lines 63-77 first; if Plan 003's procedures are generated against stale wording they must be regenerated — this document lands before Plan 003's doc procedure by batch order.

## Compatibility considerations
- Docs-only; no code consumer. `tools/check_docs_consistency.py --domain db` must stay clean.

## Security considerations
- N/A: documentation text only.

## Rollback considerations
- Revert the file by checkout; docs describe code behavior, so revert together with the code document if the whole unit is rolled back.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain db` → No findings (AC-4).
- Read-back check: the paragraph names the same four vocabulary tokens the code emits; no new action token appears anywhere in the docs.

## Completion criteria
- Lines 64-66 region states in-activation rollback behavior and always-populated `active_db_state`; docs checker clean.

## Out of Scope
- Line 77 terminal-path cleanup text and quarantine retention decision (Plan 003 REQ-006).
- ADR-008 edits (Plan 003 REQ-006 owns the retention decision record there).
- Probe section (Plan 004) and drill artifacts section 12 (Plan 009).

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/done/20261114-092849_dbreview002_partial-activation-rollback.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-035004_dbreview002_partial-activation-rollback.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-080732
- **Related target files**: docs/41_db/db_07_api_and_operations-recovery-and-reference.md
