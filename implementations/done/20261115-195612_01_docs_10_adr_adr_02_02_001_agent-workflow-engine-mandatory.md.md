## Goal

Amend ADR-001 so INV-07, Decision Details item 11, and the INV-07 Verification row describe the guarded parent-task reconciliation the code already performs (`running`→`failed` when no live attempt remains), so no ADR claim implies recovery leaves task status unchanged.

## Scope
**Release unit**: N/A: not part of a release unit

- Covers `REQ-001` (INV-07 + item 11 wording) and `REQ-002` (Verification row: add `tasks_reconciled` and the reconciliation scenarios, citing the reconciliation test).
- Also keeps the `## Known Deviations` entry consistent with the amended references (`REQ-005`, confirmed no change needed unless a drift appears).

## Assumptions
- Documenting existing, already-approved recovery behavior is an evidence correction (no reopened approval) per `docs/00_governance/governance_01_documentation-policy.md` line 296. Preserve INV-07's ID, the decision, and the approval record.
- The false `wflease001` "never-repairs" Amendment sentence was already removed by adrrev017 (commit `afa32e392`); verified absent from the current ADR-001. Re-verify current ADR-001 text before editing.
- `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` line 92 (verified 2026-11-15 re-verification; superseding the earlier "line 90" claim) already describes the reconciliation correctly and is the alignment model (reference file, not edited here).

## Design decisions
- Add reconciliation wording as current-tense description of existing behavior; do not reopen the approval record or change the decision (governance classification: evidence correction).
- Describe the guards explicitly: terminal tasks and tasks with a remaining live attempt are never reconciled; only attempts claimed by the current transaction trigger reconciliation; keep UTC `Z` as the canonical stored timestamp.

## Alternatives considered
- N/A: single obvious documentation correction; the Plan's Design section fixes the alignment direction (align to code + `db_07`).

## Implementation
### Target file
- `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`

### Procedure
1. INV-07 (line 172): expand "interrupted Attempts are recovered as `failed` by `recover_stale_attempts()`" to add that every claimed task with no remaining live attempt is reconciled from `running` to `failed` in the same transaction, and that terminal-status tasks and tasks with a live attempt are not reconciled.
2. Decision Details item 11 (line 70): add processed-event pair deletion (so a stage re-executes) and the guarded parent-task reconciliation, keeping the lease-based recovery wording and UTC `Z` timestamps.
3. INV-07 Verification row (line 188): add `tasks_reconciled` and the reconciliation scenarios to the description. The row already cites `tests/agent/workflow/test_state_store.py` alongside `test_workflow_state_store.py` / `test_stale_recovery_lease.py` (verified 2026-11-15 re-verification), so the remaining work is description wording only; no citation addition is needed.

### Method
- Wording-only edits; preserve every invariant ID, the decision text, and the existing approval record. Do not touch any other invariant row.

### Details
- Reconciliation semantics to state (from `scripts/agent/workflow/state_store.py` lines 294-314): a guarded UPDATE moves only a still-`running` task with no remaining live attempt to `failed`; `tasks_reconciled` is a report counter; `halted`/`completed` tasks are never reconciled.
- Do not edit the lease-less age-rule wording (out of this Plan's scope).

## Compatibility considerations
- N/A: documentation-only; no runtime interface or decision change. `check_adr_preservation.py` is expected to flag the intended INV-07/Verification wording change (intended ERROR), not a preservation violation.

## Security considerations
- N/A: no security surface; only aligns documentation with existing fail-closed recovery behavior.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run python tools/check_adr_invariant_matrix.py`, `uv run python tools/check_adr_structure.py`, `uv run python tools/check_known_deviation_sync.py` — invariant matrix cites the reconciliation test; Known Deviations stay in sync.
- `uv run python tools/check_adr_preservation.py` — reports the intended INV-07/Verification change (approved evidence correction), not an unintended decision change.

## Completion criteria
- INV-07, item 11, and the INV-07 Verification row all describe guarded reconciliation and `tasks_reconciled`; invariant IDs and the approval record are unchanged; ADR structure/preservation checkers accept the evidence-correction change.

## Out of Scope
- Editing `scripts/agent/workflow/state_store.py`; the lease-less age-rule wording (`agent_03_03` line 169, adrrev005-owned); any `db_07` edit (reference file); restoring the "never-repairs" Amendment wording (already removed by adrrev017).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Amend INV-07 and Decision Details item 11 wording (evidence correction) | Completed | 20261115 | 20261115 | REQ-001 INV-07 and item 11 amended with guarded reconciliation + processed_events pair deletion |
| 2 | Update INV-07 Verification row: `tasks_reconciled` + reconciliation scenarios + test citation | Completed | — | 20261115 | REQ-002 Verification row description extended with tasks_reconciled scenarios; citations already present |
| 3 | Run ADR checkers (`check_adr_invariant_matrix`, `check_adr_structure`, `check_known_deviation_sync`, `check_adr_preservation`) | Completed | — | 20261115 | REQ-005 consistency confirmed here invariant_matrix/structure/known_deviation_sync clean; check_adr_preservation reports the intended INV-07 evidence-correction change as predicted |

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
- **Requirement ID**: `REQ-001` (INV-07/item 11 reconciliation wording), `REQ-002` (Verification row `tasks_reconciled`)
- **Source issue**: `issues/20261111-163819_wfrecov001_adr001-recovery-reconciliation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-053822_wfrecov001_adr001-recovery-reconciliation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-195612
- **Related target files**: `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`