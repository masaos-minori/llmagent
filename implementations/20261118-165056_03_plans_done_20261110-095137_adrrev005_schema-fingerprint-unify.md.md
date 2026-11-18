## Goal
- Make the archived adrrev005 plan match the repository (`REQ-002`: Work Items and Execution Status; `REQ-003`: Phase 7 deployment preconditions; `REQ-004`: Phase 6 approval references; `REQ-006`: the `scripts/db/schema_sql.py` target row follows the "no EventBus DDL in `scripts/db/`" rule; `REQ-001`: evidence attached to every change).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md` only, corrected in place (the user confirmed this method on 2026-11-18).
- Plan step: Phase 2 of `plans/20261118-164413_adrchk009_plan-code-reconcile.md`. It runs after procedure 01 (the accessor removal), so the evidence searches reflect the final tree.

## Assumptions
- `tools/sync_plan_workitem_status.py` sets only rows whose archived procedure has a complete Execution Status; its dry-run on 2026-11-18 listed 35 rows. Falsifiable by the dry-run repeated in step 1.
- Phase 7 stays `Pending`: it is a deployment phase and this procedure runs no deployment. Falsifiable by the Execution Status table after the edit.
- The ADR approval ledger (`governance_03` Part 5) holds `AAL-025` and `AAL-026` with approver `Not recorded`, and no row for the ADR-001 or ADR-006 Phase 6 edits; falsifiable by `rg -n "^#### AAL-0(25|26|29)$"` on that file.

## Design decisions
- Rows of `### Work Items Created` change only through the sync tool; every text change uses Edit and cites ledger IDs and Unknown IDs, never approval wording.
- Notes name the adrchk009 plan by id, not by a `plans/` path, so `tools/plan_dependency_order.py` reads no new dependency.

## Alternatives considered
N/A: the method (in-place correction) was chosen by the user; `tools/amend_plan.py` refuses an archived Plan.

## Implementation
### Target file
`plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md`

### Procedure
1. Run `uv run python tools/sync_plan_workitem_status.py plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md --dry-run`; keep the output. Run it again without `--dry-run`, then run the dry-run once more and confirm it reports no row to change.
2. Edit the file as described in Method and Details.
3. Validate (Validation plan).

### Method
- **Execution Status notes (`REQ-001`, `REQ-002`)**: append to the Notes cell of step 1: `Work Items Created: 35 Pending rows set Completed from the archived procedures (sync tool dry-run 35 rows, then applied; a second dry-run reports none) (adrchk009, 20261118).` Append to the Notes cell of step 3: `AC-04 deviation (adrchk009, 20261118): the AC-04 search also returns scripts/eventbus/db_tools.py (schema_version() reads PRAGMA user_version) and comment mentions of the retired marker tables in scripts/agent/services/workflow_schema.py, deploy/init_db.sh, and deploy/setup_services.sh, besides the named scripts/shared/execution_snapshot.py header read; open, decision tracked as UNK-02 of the adrchk009 plan.` Keep every Status value unchanged.
- **Phase 6 approval references (`REQ-004`)**: under Phase 6 of `## Implementation steps` add one non-checkbox bullet: `Approval references (adrchk009, 20261118): ADR-001 lease-less clause removal (commit 5e8e89203): no ledger row; pending. ADR-008 drift-check wording (commit c3573341e): related ledger row AAL-025 (governance_03 Part 5); approval pending, approver and date Not recorded. ADR-006 version-stamp clause removal (commit 8f5c5825c): no ledger row (AAL-029 covers a different statement); pending. No approval is recorded here.`
- **Phase 7 preconditions (`REQ-003`)**: under Phase 7 add one non-checkbox bullet: `Preconditions (adrchk009, 20261118), all open: (1) the data lifecycle decision text in ADR-008 Decision Details 22 and 23 is recorded, with its approval pending in AAL-025 and AAL-026; (2) UNK-02 and UNK-03 of this plan are resolved by the maintainer; (3) each deployed database that fails the fingerprint is archived and recreated by the operator; (4) deployment stays the user's decision after commit and push, and no document edit runs it.` In the step 7 row of the Execution Status table append to Notes: `Preconditions open: see Implementation steps Phase 7.`
- **Target row wording (`REQ-006`)**: in the `Implementation Target Files` row for `scripts/db/schema_sql.py`, replace `Modify: Expose the canonical DDL of every database through one accessor family` with `Modify: Expose the canonical DDL of the workflow, session, and rag databases through one accessor family; the EventBus DDL is owned by eventbus.db_tools`, and replace the second cell's leading `Expose the canonical DDL of every database through one accessor family;` with `Expose the canonical DDL of the workflow, session, and rag databases through one accessor family;`. Leave the rest of the row and the Phase 3 text unchanged (Phase 3 names no EventBus accessor).

### Details
- Do not change any Status value, any other row, or the `Work Items Created` rows by hand.
- Write no approval statement and no `Gated:` marker (that marker is for procedure rows).

## Compatibility considerations
N/A: an archived workflow document; tools read its tables only.

## Security considerations
N/A: documentation-only edit with no secret or approval path.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/sync_plan_workitem_status.py plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md --dry-run` reports no row to change (`AC-02`).
- `uv run python tools/check_workitem_structure.py --archived-status` reports no new finding (`AC-07`); `uv run python tools/check_workitem_traceability.py --active-only` passes.
- Read back the Phase 6 and Phase 7 bullets, the two notes, and the `scripts/db/schema_sql.py` row (`AC-03`, `AC-04`, `AC-06`); `rg -n "AAL-025|AAL-026" plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md` finds them.

## Completion criteria
- No Phase marked `Completed` has a `Pending` Work Item.
- The Phase 6 and Phase 7 bullets, the two Notes additions, and the reworded target row are present, and no Status value changed.
- No approval statement appears in the file.

## Out of Scope
- Changing code or other documents, resolving UNK-02 and UNK-03 of adrrev005 or of the adrchk009 plan, editing ADR-001, ADR-006, ADR-008, or `governance_03`, and running any deployment.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Run the sync tool (dry-run, apply, dry-run again) | Pending | — | — | |
| 2 | Edit the Execution Status notes, Phase 6 and Phase 7 bullets, and the `scripts/db/schema_sql.py` target row | Pending | — | — | |
| 3 | Run the archived-plan checkers and read the edits back | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (attach evidence), `REQ-002` (reconcile status), `REQ-003` (deployment preconditions), `REQ-004` (approval references), `REQ-006` (follow the DDL rule)
- **Source issue**: issues/20261117-123009_adrchk009_plan-code-reconcile.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-164413_adrchk009_plan-code-reconcile.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-165056
- **Related target files**: `plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md`
