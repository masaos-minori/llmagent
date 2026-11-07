# Implementation Procedure: docs/41_db/db_07_api_and_operations-recovery-and-reference.md

## Goal
Residual sweep of the drill/reference sections: the version-gate fail-start sentence (line 147),
the `policy: migrate` drill field (line 177), and the `ledger` drill fields (line 184) describe
removed machinery and must state the current-only behavior.

## Scope
- Target file: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` (MODIFY, residual
  sweep after compatrm001's §11/§11a edits).
- Release unit: `policy-finalization`.
- Related requirement / acceptance criteria: REQ-005 / AC-004, AC-005 (frozen target row 13).

## Assumptions
- Anchors grep-verified: 147, 177, 184; §11 and §11a themselves are owned by compatrm001 and are
  out of this document's scope.
- `user_version` as the EventBus schema stamp is a live mechanism and stays; only workflow
  schema-version gating wording is retired. The line 147 sentence is rewritten so it no longer
  presents a retired version-table gate as startup behavior, without deleting EventBus stamp
  references elsewhere.

## Design decisions
- Drill fields (177, 184) are documentation of a diagnostics payload: fields whose backing
  machinery was removed are deleted from the reference; replacing them is not allowed since the
  payload no longer carries them.
- Line 147 becomes: startup fails when the deployed schema does not match the code exactly
  (archive-and-recreate is the remediation, cross-referencing doc 10's runbook).

## Alternatives considered
- Marking the drill fields historical and keeping them listed: rejected — API reference sections
  must describe the current payload exactly; retired fields listed as "historical" invite
  operators to look for them.

## Implementation

### Target file
- `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` (MODIFY).

### Procedure
1. Line 147: rewrite the fail-start sentence to the exact-match startup contract; keep EventBus
   `user_version` stamp semantics intact if mentioned.
2. Line 177: delete the `policy: migrate` field entry from the drill reference.
3. Line 184: delete the `ledger` drill field entries.
4. Sweep the file (outside §11/§11a) for the five doc-claim phrases and retired names; remove or
   mark historical.

### Method
- Anchor re-location by heading after compatrm001's edits (line numbers drift); checker
  doc-claim + doc-symbol pass.

### Details
- Cross-references from deleted fields point readers to the startup-error remediation runbook.

## Compatibility considerations
- Sequenced after compatrm001's §11/§11a edits (frozen overlap judgment: compatible, disjoint
  sections).

## Security considerations
- None.

## Rollback considerations
- Single-file revert.

## Validation plan
- Checker blocking run exit 0; docs consistency CI.

## Completion criteria
- Drill reference matches the current payload; no version-gate wording; checker green.

## Out of Scope
- §11/§11a (compatrm001), other db docs.

## Execution Status
| Step | Status | Notes |
|---|---|---|
| 1 Line 147 rewrite | Pending | EventBus stamp stays live |
| 2 Line 177 delete | Pending | |
| 3 Line 184 delete | Pending | |
| 4 Sweep | Pending | outside §11/§11a |

### Blocker Log
- None. (Dependency note: blocked until compatrm001's procedure for this file executes — planned
  sequencing.)

### Work Items Created
- None.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005 / AC-004, AC-005
- **Source issue**: issues/20261106-125145_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-064415_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-103000
- **Related target files**: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`
