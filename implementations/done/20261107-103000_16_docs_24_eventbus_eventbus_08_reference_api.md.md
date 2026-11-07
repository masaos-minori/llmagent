# Implementation Procedure: docs/24_eventbus/eventbus_08_reference_api.md

## Goal
Remove the API reference rows for the deleted `scripts/eventbus/migrate.py main` and
`scripts/eventbus/migrations.py verify_backup` (lines 130-131) and the scripts-directory
description that presents `migrate.py`/`migrations.py` as live modules.

## Scope
- Target file: `docs/24_eventbus/eventbus_08_reference_api.md` (MODIFY).
- Release unit: `policy-finalization`.
- Related requirement / acceptance criteria: REQ-001, REQ-005 / AC-004 (frozen target row 16).

## Assumptions
- Anchors grep-verified: lines 130-131 list the two deleted entry points as live API; no
  prerequisite plan (compatrm001/002/003 procedure docs) owns this document, so the correction is
  owned here. The modules themselves are deleted by the compatrm001 procedures.
- The EventBus `user_version` schema stamp remains live and is not part of this removal.

## Verification findings (adversarial re-verification 2026-11-07, HEAD `be4d74463`)

- Already satisfied by the compatrm001-era reference-table regeneration: `grep migrate|migrations|
  verify_backup` over the file returns zero hits — the two retired API rows and the
  scripts-directory description were removed when `tools/generate_reference_table.py --manifests`
  refreshed the table from `registry/manifests/eventbus_api.yaml` after the modules were deleted.
  Sweep of the five doc-claim phrases: zero hits. VERIFY row: no edit needed.

## Design decisions
- Rows are deleted outright: this is an API reference section, and reference sections must list
  only callable entry points (same principle as doc 13's drill-field deletion).
- The scripts-directory description becomes the post-removal module list (no
  `migrate.py`/`migrations.py`).

## Alternatives considered
- Marking the rows historical in place: rejected — a reference table invites use; historical
  context lives in the eventbus overview docs, not the API reference.

## Implementation

### Target file
- `docs/24_eventbus/eventbus_08_reference_api.md` (MODIFY).

### Procedure
1. Delete lines 130-131 rows (the two retired entry points) from the API table.
2. Update the scripts-directory description paragraph to the post-removal module list.
3. Sweep the file for other citations of the deleted modules (grep `migrate.py`, `migrations.py`,
   `verify_backup` in this file) and for the five doc-claim phrases; remove or mark historical.

### Method
- Text edits; checker `--check-doc-symbols` pass (backticked function references to deleted
  definitions are exactly what this flag catches).

### Details
- Sequenced after compatrm001's module deletion: until then the symbols exist and the reference
  rows are technically accurate; the whole cycle lands as one release unit.

## Compatibility considerations
- docs consistency CI; cross-links from other eventbus docs to the deleted rows must not break —
  check inbound references when editing.

## Security considerations
- None.

## Rollback considerations
- Single-file revert.

## Validation plan
- Checker blocking run exit 0 (doc-symbol sweep in particular); docs consistency CI.

## Completion criteria
- API reference lists only live entry points; no live `migrate.py`/`migrations.py` description;
  checker green.

## Out of Scope
- Other eventbus docs; the module deletion itself (compatrm001).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete rows 130-131 | Completed | 20261107-184026 | 20261107-184026 |  |
| 2 | Module-list rewrite | Completed | 20261107-184026 | 20261107-184026 |  |
| 3 | Citation sweep | Completed | 20261107-184026 | 20261107-184026 | doc-symbol pass |
### Blocker Log
- None.

### Work Items Created
- None.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-005 / AC-004
- **Source issue**: issues/20261106-125145_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-064415_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-103000
- **Related target files**: `docs/24_eventbus/eventbus_08_reference_api.md`