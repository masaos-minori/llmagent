# Implementation Procedure: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` (drill runbook)

## Goal
Add the recovery-drill runbook (procedure, frequency placeholder, artifact retention location) to the DB recovery/reference doc, and reflect that archives are now verified recovery points (Plan row 23; REQ-007, AC-6).

## Scope
- In scope: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` runbook and rotation-section updates.
- Out of scope: harness implementation (row 11), rotation code (row 12), migration contract text (row 22).

## Current shape (facts)
- `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` is the DB recovery doc (Plan evidence; confirmed 2026-10-30) and already carries the rotation procedure referenced as "db_07 section 11, step 1" from db_03 (`db_03:80`).
- No drill/runbook content exists today (issue absence search: no "recovery drill"/"restore drill" text in docs).

## Assumptions
- Drill cadence and artifact retention duration remain undecided (Plan UNK-01 / Blocker Log step 5): the runbook states the procedure and marks frequency/retention as placeholders awaiting owner decision, explicitly flagged so the docs checker's Needs-Confirmation convention carries the open question.
- Artifact location documented as configured: `{archive_dir}/drills/{domain}_{timestamp}.json` with `archive_dir` resolved from `agent.toml` `sqlite_archive_dir` (the `rotation.py` hardcoded fallback default; the directory may not exist until the first rotation), matching row 11 and `rotation.py::_resolve_archive_dir` (`scripts/db/rotation.py:15-22`).

## Design decisions
- New numbered section placed after the existing recovery/rotation sections so "section 11" cross-refs from db_03 keep resolving; the drill section references the rotation section rather than duplicating archive mechanics.
- Runbook is operator-level commands (`scripts/db/recovery_drill.py --domain all`, optional init hook per row 13) plus what each artifact field means for RPO/RTO reading — measurement semantics, not thresholds.

## Alternatives considered
- Putting the runbook in `docs/02_deployment.md` — rejected: Plan row names db_07 (DB recovery doc) and keeps recovery procedure + reference together.

## Implementation
### Target file
- `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` (modify)

### Procedure
1. Add a "Recovery drills" section: purpose, per-domain command examples, opt-in flag note for `deploy/init_db.sh` (row 13), artifact path and field list (row 11 schema), live-DB immutability statement.
2. Update the rotation section (section 11 area): archived files are integrity-checked and domain-identity-checked at creation (row 12), so a drill restores a verified recovery point; failed-verification archives are left in place and named in the error — operator action: re-rotate or investigate.
3. Add frequency/retention placeholder lines marked Needs Confirmation with the UNK-01 owner question.
4. Verify db_03's "db_07 section 11, step 1" reference still resolves; adjust numbering references only if the doc checker flags drift.

### Method
Append a section + two in-place sentences; no renumbering unless checkers require it.

### Details
- Re-locate "section 11" by heading text at edit time; line anchors shift after prior rows land.

## Compatibility considerations
- Docs checkers must pass; keep canonical metadata schema for the doc (title/tags area untouched).

## Security considerations
- None (documentation only). Commands documented operate on sandbox-safe harness semantics (never mutate live DBs).

## Rollback considerations
- `git checkout` the file.

## Validation plan
- Automated: docs checkers per `routing.md`; stale detector on this procedure doc.
- Manual: operator walkthrough against a sandbox drill artifact produced by row 19 fixtures.

## Completion criteria
- Runbook section exists with commands, artifact schema, retention/frequency placeholders flagged; rotation section states verification-at-archive; cross-doc references resolve.

## Out of Scope
- Numeric RPO/RTO targets (UNK-01). Scheduling automation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Land after code rows per Plan sequencing Added '## 12. Recovery drills' section (purpose, --domain all/per-domain commands, exit codes, optional deploy/init opt-in hook note, artifact location + field table with RPO/RTO measurement semantics, live-DB immutability, UNK-01 frequency/retention placeholder via {defer...until UNK-01}). Added archive-verified-recovery-point bullet to section 11 Important notes. Renumbered Verification Plan 12->13. Verified module paths/fields against recovery_drill.py + rotation.py. |
| 2 | Add or update tests per Validation plan | Completed | — | — | Docs checkers only Docs checkers only. check_docs_quality OK; check_docs_content_policy --strict OK; check_docs_structure OK; check_docs_consistency --domain db OK (no issues); check_docs_japanese OK. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | Docs checker subset Confirmed db_03 'section 11/11a' cross-refs still resolve (unchanged); no forbidden tokens (REQ-/Added/issues/done/strikethrough/Traceability/to-be-determined/pending) introduced. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | This row is the documentation Procedure doc itself is the deliverable; archived after doc gates pass. |

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
- **Requirement ID**: `REQ-007`
- **Source issue**: `issues/20261029-104500_dbmig001_forward-only-db-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-214108_dbmig001_forward-only-db-migrations.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-071336
- **Related target files**: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`