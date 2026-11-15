## Goal

Correct the two contradictory recovery statements in `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` so they state the guarded parent-task reconciliation the code performs, matching `scripts/agent/workflow/state_store.py` and `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`.

## Scope
**Release unit**: N/A: not part of a release unit

- Covers `REQ-003`: this spec no longer claims recovery never changes task status; it states the guarded reconciliation.

## Assumptions
- `db_07` line 90 already describes the reconciliation correctly; align this spec to it (and to `state_store.py`), not the reverse. (Verified: `state_store.py` lines 294-314 reconcile a claimed `running` task to `failed` when no live attempt remains; `db_07` line 90 states the same.)

## Design decisions
- Rewrite only the two reconciliation claims (lines 166 and 197) into the guarded-reconciliation rule; keep the lease-based wording and the terminal/live-attempt guards explicit.

## Alternatives considered
- N/A: single obvious documentation correction; the Plan fixes aligning this stale spec to `db_07` + `state_store.py`.

## Implementation
### Target file
- `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`

### Procedure
1. Startup Recovery (line 166): replace "repairs attempt records only: it never changes the persisted task status, so a task left `running` or `halted` by an earlier process stays as it was" with text stating that a claimed task whose last live attempt was just failed is reconciled from `running` to `failed` in the same transaction, while terminal (`halted`/`completed`) tasks and tasks with a remaining live attempt are not reconciled.
2. Known Limitations (line 197): replace "The task record itself is not repaired by that pass" with text stating that the parent task IS reconciled to `failed` once no live attempt remains.

### Method
- Wording-only; keep the surrounding lease-expiry description intact.

### Details
- Do NOT touch line 169 (lease-less pre-migration 3600 s age rule) — it is out of this Plan's scope (owned by adrrev005).

## Compatibility considerations
- Documentation-only; no runtime interface change.

## Security considerations
- N/A: documentation-only; removes a misleading claim that would make an operator expect orphaned tasks to remain `running`.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py` — clean.
- `uv run python tools/check_docs_consistency.py --domain agent` — no contradiction with `db_07`.

## Completion criteria
- Lines 166 and 197 no longer claim task status is never repaired; they state the guarded reconciliation; `agent_03_03` and `db_07` agree.

## Out of Scope
- The lease-less age-rule wording (line 169, adrrev005-owned); editing `db_07` or `state_store.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite Startup Recovery line 166 to the guarded reconciliation | Pending | — | — | REQ-003 |
| 2 | Rewrite Known Limitations line 197 to state parent reconciliation | Pending | — | — | REQ-003 |
| 3 | Run doc checkers (`check_docs_quality`, `check_docs_structure`, `check_docs_content_policy`, `check_docs_consistency --domain agent`) | Pending | — | — | Confirms agreement with `db_07` |

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
- **Requirement ID**: `REQ-003` (spec states the guarded reconciliation instead of "never changes task status")
- **Source issue**: `issues/20261111-163819_wfrecov001_adr001-recovery-reconciliation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-053822_wfrecov001_adr001-recovery-reconciliation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-195612
- **Related target files**: `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`
