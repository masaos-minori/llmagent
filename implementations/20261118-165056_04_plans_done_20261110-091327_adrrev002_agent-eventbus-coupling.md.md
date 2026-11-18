## Goal
- Make the archived adrrev002 plan match the repository: record that its `AC-04` search returns no match once the accessor is removed (`REQ-006`, `REQ-001`), and add the Phase 6 deployment preconditions (`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md` only, corrected in place (the user confirmed this method on 2026-11-18). The `AC-04` text stays unchanged.
- Plan step: Phase 3 of `plans/20261118-164413_adrchk009_plan-code-reconcile.md`. It runs after procedure 01, so the `AC-04` evidence reflects the final tree.

## Assumptions
- Phase 6 of adrrev002 is its only `Pending` Phase and every Work Items row is `Completed`; verified in Step 3a of this cycle with the plan text and the sync tool for the sibling plan. Falsifiable by `uv run python tools/manage_workitem_stage.py show plan plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md`.
- `deploy/init_db.sh` now runs the fingerprint gate of the adrrev005 work on the existing databases, so adrrev002 Phase 6 shares its blockers; falsifiable by reading the gate comment in `deploy/init_db.sh`.
- Procedure 01 has been executed before this one, so the `AC-04` search returns no match; if it still returns one, stop and report `Blocked` instead of recording it as passing.

## Design decisions
- Only Notes cells and one bullet under Phase 6 change; no Status value changes.
- The adrrev005 unknowns are named by id (`UNK-02`, `UNK-03` of the adrrev005 plan), not by a `plans/` path.

## Alternatives considered
N/A: the method (in-place correction) was chosen by the user.

## Implementation
### Target file
`plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md`

### Procedure
1. Run `rg -n "DbTarget\.EVENTBUS|build_eventbus_schema_sql|create_eventbus_schema|rotate_eventbus_db|eventbus_db_path" scripts/db/ scripts/shared/ scripts/agent/`; keep the output (it must return no match).
2. Edit the file as described in Method.
3. Validate (Validation plan).

### Method
- **`AC-04` evidence (`REQ-001`, `REQ-006`)**: append to the Notes cell of the step 3 row of the Execution Status table: `AC-04 search returns no match (checked 20261118 after the EventBus DDL accessor was removed from scripts/db/) (adrchk009).` Leave the `AC-04` text in `## Acceptance Criteria` as it is.
- **Phase 6 preconditions (`REQ-003`)**: under Phase 6 of `## Implementation steps` add one non-checkbox bullet: `Preconditions (adrchk009, 20261118), all open: (1) the data lifecycle decision text in ADR-008 Decision Details 22 and 23 is recorded, with its approval pending in AAL-025 and AAL-026; (2) UNK-02 and UNK-03 of the adrrev005 plan are resolved by the maintainer, because init_db.sh now applies its fingerprint gate to the existing databases; (3) each deployed database that fails the fingerprint is archived and recreated by the operator; (4) deployment stays the user's decision after commit and push, and no document edit runs it.` In the step 6 row of the Execution Status table append to Notes: `Preconditions open: see Implementation steps Phase 6.`

### Details
- Do not change any Status value, any Work Items row, or any other section.
- Write no approval statement.

## Compatibility considerations
N/A: an archived workflow document; tools read its tables only.

## Security considerations
N/A: documentation-only edit with no secret or approval path.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- The `AC-04` search of step 1 returns no match (`AC-06`).
- `uv run python tools/check_workitem_structure.py --archived-status` reports no new finding (`AC-07`).
- Read back the Phase 6 bullet and the two Notes additions (`AC-03`, `AC-06`); `rg -n "AAL-025|AAL-026" plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md` finds them.

## Completion criteria
- The step 3 Notes record the `AC-04` result, the Phase 6 bullet and the step 6 Notes are present, and no Status value or `AC-04` text changed.
- No approval statement appears in the file.

## Out of Scope
- Changing code or other documents, amending `AC-04` or `REQ-004`, resolving the adrrev005 unknowns, and running any deployment.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-run the `AC-04` search and keep the output | Pending | — | — | |
| 2 | Edit the step 3 and step 6 Notes and add the Phase 6 preconditions bullet | Pending | — | — | |
| 3 | Run the archived-plan checker and read the edits back | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (attach evidence), `REQ-003` (deployment preconditions), `REQ-006` (`AC-04` matches the tree)
- **Source issue**: issues/20261117-123009_adrchk009_plan-code-reconcile.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-164413_adrchk009_plan-code-reconcile.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-165056
- **Related target files**: `plans/done/20261110-091327_adrrev002_agent-eventbus-coupling.md`
