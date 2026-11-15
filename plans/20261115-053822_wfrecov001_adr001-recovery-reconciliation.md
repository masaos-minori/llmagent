## Goal
Align ADR-001 and the workflow-engine recovery reference with the implemented stale-attempt recovery, which reconciles an orphaned `running` parent task to `failed` in the same transaction, so no `docs/` claim states that recovery leaves task status unchanged.

## Priority
High

## Scope
- **In-Scope**:
  - Amend ADR-001 INV-07 and Decision Details item 11 to describe attempt recovery, processed-event deletion, and guarded parent-task reconciliation.
  - Add `tasks_reconciled` and the reconciliation scenarios to ADR-001's Verification table, citing the test that asserts reconciliation (`tests/agent/workflow/test_state_store.py`).
  - Correct the contradictory recovery statements in `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` (Startup Recovery and Known Limitations) so they state that a claimed task with no remaining live attempt is reconciled to `failed`, matching the code and `db_07`.
  - Confirm `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` already describes reconciliation consistently; treat it as the alignment model, not a modification target, unless a drift is found.
  - Confirm ADR-001's `## Known Deviations` entry stays consistent once all named references match.
- **Out-of-Scope**:
  - Removing the "never-repairs-task-status guarantee" Amendment wording — already removed by `plans/done/20261111-110144_adrrev017_docs-history-wording.md` (commit `afa32e392`).
  - Code changes to `scripts/agent/workflow/state_store.py`.
  - Lease-less legacy age-rule wording in `agent_03_03` (line 169, the 3600 s age rule removed by adrrev005) — owned by the adrrev005 schema-compatibility work, not this issue.
  - Changing the recovery decision itself, legacy lease-less removal, or `_LEGACY_STALE_AGE_SEC`/`legacy_recovered`/lease-less test removal.
- **Dependencies**:
  - **Depends on**: `plans/done/20261111-110144_adrrev017_docs-history-wording.md` | phase all | it removed ADR-001's `wflease001` Amendment (the false sentence); that work has landed, so the "remove the never-repairs claim" Required Change is already satisfied. Re-verify current ADR-001 text before editing.
  - **Depends on**: `plans/done/20261110-233648_adrrev009_adr008-recovery-align.md` | phase all | it edits `db_07`; sequence this issue's `db_07` alignment check after it lands. This issue treats `db_07` as an already-correct reference, so no `db_07` edit is expected.

## Background
The archived implementation `issues/done/20261107-203220_wfaudit007_task-status-never-reconciled.md` made `StateStore.recover_stale_attempts()` reconcile an orphaned parent task from `running` to `failed` in the same transaction. ADR-001 was edited around recovery, but its invariant and decision wording omit that reconciliation, and a related spec (`agent_03_03`) still states the opposite of the shipped behavior.

## Problem
ADR-001 INV-07 and Decision Details item 11 describe recovery as "interrupted Attempts are recovered as `failed`" but do not mention the guarded parent-task reconciliation the code performs, nor `tasks_reconciled`. `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` states in two places that recovery "repairs attempt records only: it never changes the persisted task status" and that "the task record itself is not repaired by that pass" — directly contradicting `scripts/agent/workflow/state_store.py` and `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`, which correctly describe the reconciliation. No document currently claims task status is never repaired (that Amendment wording was removed by adrrev017), but the residual contradiction still misleads a reader into thinking orphaned tasks stay `running`.

## Reason for Change
A documentation and code mismatch: an implementer or operator reading `agent_03_03` would expect orphaned tasks to remain `running` after recovery, while the code and `db_07` reconcile them. The wording must be corrected before further recovery work relies on these documents.

## Implementation Intent
Describe the recovery transaction as a single current-tense rule in INV-07 and Decision Details item 11: recover lease-expired attempts as `failed`, delete their `processed_events` pair so a stage re-executes, and reconcile the parent task from `running` to `failed` only when no live attempt remains. State the guards: terminal tasks and tasks with a remaining live attempt are not changed, and only attempts claimed by the current transaction trigger reconciliation. Keep UTC `Z` as the canonical stored timestamp. Classify the ADR edit under governance as an evidence correction (no reopened approval) because it documents existing, already-approved behavior.

## Requirements
- `REQ-001`: ADR-001 INV-07 and Decision Details item 11 describe attempt recovery, processed-event deletion, and guarded parent-task reconciliation.
- `REQ-002`: ADR-001's Verification table lists `tasks_reconciled` and the reconciliation scenarios, citing the test that asserts reconciliation.
- `REQ-003`: `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` no longer states that recovery never changes task status; it states the guarded reconciliation that the code performs.
- `REQ-004`: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` is confirmed to describe reconciliation consistently; no drift remains.
- `REQ-005`: ADR-001's `## Known Deviations` entry stays consistent with all named references after the edits.

## Implementation Target Files
**Freeze status**: Frozen (all rows `Verified`; `issue-to-plan` Step 8's Implementation Target Files Validation passed — see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Modify | Amend INV-07 (line 172) and Decision Details item 11 (line 70) to add guarded parent-task reconciliation; add `tasks_reconciled` and the reconciliation scenarios to the Verification table row for INV-07 (line 188), citing `tests/agent/workflow/test_state_store.py`. Preserve INV-07's ID, the decision, and the approval record. | REQ-001, REQ-002 | INV-07 (line 172) reads only "interrupted Attempts are recovered as `failed`"; item 11 (line 70) omits reconciliation; Verification row (line 188) names three test files but no reconciliation scenario or `tasks_reconciled`; the `wflease001` Amendment holding the false "never-repairs" sentence was already removed by adrrev017 (commit `afa32e392`) | `tests/agent/workflow/test_state_store.py` (asserts `tasks_reconciled`, `test_terminal_status_tasks_are_never_reconciled`, `test_two_stale_attempts_reconcile_one_task_once`) | Verified |
| `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Modify | Fix line 166 ("repairs attempt records only: it never changes the persisted task status") and line 197 ("The task record itself is not repaired by that pass") so they state the guarded reconciliation the code performs. | REQ-003 | line 166 says recovery "never changes the persisted task status"; line 197 says "the task record itself is not repaired by that pass" — both contradict `state_store.py` lines 294-314 and `db_07` line 90, which describe the reconciliation | Documentation checkers | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Already describes the reconciliation correctly (line 90: claimed task reconciled to `failed`, `tasks_reconciled` count, halted/completed never reconciled); the alignment model for `agent_03_03`. | REQ-003, REQ-004 |
| `scripts/agent/workflow/state_store.py` | Evidence for the reconciliation behavior: docstring lines 244-248 and body lines 294-314 (guarded `running`→`failed` reconciliation in the same transaction). | REQ-001, REQ-003 |
| `tests/agent/workflow/test_state_store.py` | Evidence that reconciliation is covered by tests (asserts `tasks_reconciled`, terminal-task exclusion, single-reconcile). | REQ-002 |
| `tests/agent/workflow/test_workflow_state_store.py` | Evidence for general recovery coverage (lease, unparseable, timezone-independence) that INV-07 retains. | REQ-001 |

## Acceptance Criteria
- `AC-001`: ADR-001 and the code describe the same recovery transaction. (`REQ-001`)
- `AC-002`: No document claims that task status is never repaired by recovery. (`REQ-003`)
- `AC-003`: ADR-001 states that terminal tasks and tasks with a live attempt are not reconciled, and that reconciliation applies only to attempts claimed by the current transaction. (`REQ-001`)
- `AC-004`: All named recovery tests are listed with correct repository paths. (`REQ-002`)
- `AC-005`: `agent_03_03` and `db_07` agree on the reconciliation behavior. (`REQ-003`, `REQ-004`)

## Tests
Not required (documentation-only). Run the documentation checkers: `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_invariant_matrix.py`, `uv run python tools/check_adr_preservation.py`, `uv run python tools/check_known_deviation_sync.py`, and `uv run python tools/check_docs_consistency.py --domain agent`. (`REQ-002`, `REQ-003`, `REQ-005`)

## Documentation Impact
Yes. Update ADR-001 (invariant INV-07, Decision Details item 11, Verification) and `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` (Startup Recovery, Known Limitations): intent, boundaries (guards), and failure behavior. Do not copy implementation catalogs or concrete values. Driven by `REQ-001`/`REQ-002`/`REQ-003`.

## Assumptions
- The reconciliation behavior documented in `db_07` (line 90) matches the code, so `agent_03_03` should be aligned to it rather than to its own stale wording. (Step 2)
- Editing INV-07 and Decision Details item 11 to describe reconciliation is an evidence correction (documents existing, already-approved behavior), not a decision change, per `docs/00_governance/governance_01_documentation-policy.md` line 296 ("an edit that does not change the decision (wording, evidence, references) does not reopen approval"); no reopened approval. (Step 2)
- The "remove the never-repairs claim" Required Change is already satisfied by adrrev017 (commit `afa32e392`). (Step 2)
- `deploy.sh` rsyncs `docs/` wholesale, so doc changes need no `deploy.sh` update.

## Unknowns
None blocking. The Issue's Decision 1 (governance class) is resolved by repository evidence: `governance_01` line 296 classifies documenting existing behavior as an evidence correction (no reopened approval). Recorded as a non-blocking note: if the maintainer instead treats expanding INV-07's stated scope as a substantive decision change, it needs same-change RACI approval before the ADR edit; `plan-to-implementation-procedure` stops on a blocking unknown, so this is surfaced a phase earlier.

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Modify | Medium — canonical workflow-engine contract referenced across docs and the invariant matrix | Low | Low | not applicable (rsynced) |
| `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Modify | Medium — workflow-engine spec read by operators implementing recovery | Low | Low | not applicable (rsynced) |

## Design
Path A: two documentation files, docs-only, no schema or public/runtime interface change. Two analyses below.

- **Historical analysis.** The reconciliation behavior was added by the archived `wfaudit007`; ADR-001's INV-07 and item 11 were written around recovery without describing it, and `agent_03_03` was written with the pre-reconciliation assumption ("repairs attempt records only"). The divergence is stale documentation, not churn.
- **Operational dependency.** `adrrev017` already removed the false Amendment sentence; this issue's remaining work is the invariant/decision/verification/spec alignment. `adrrev009` edits `db_07`; sequence after it, though `db_07` already describes reconciliation correctly.

**Design decisions:**
- **Alignment direction.** Align `agent_03_03` to `db_07` + `state_store.py`, because `db_07` (line 90) already correctly describes the reconciliation and `agent_03_03` is the stale document. Do not rewrite `db_07`.
- **Governance classification.** Documenting existing reconciliation is an evidence correction under `governance_01` line 296, not a decision change; no new approval record. Preserving INV-07's ID, the decision, and the approval record (per the Issue's constraint).
- **Scope boundary.** Exclude the lease-less age-rule wording (line 169) — owned by adrrev005 — even though it is also stale; flag it for separate handling.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.
Declare a release unit (see `### Release units` below) when a phase breaks existing callers or
tests until another phase lands (for example a `NOT NULL` column added before its write path):
one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be
validated alone}`.

1. **Phase 1: Amend ADR-001**
   - [ ] Expand INV-07 (`docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`) to state that a claimed task with no remaining live attempt is reconciled from `running` to `failed`, preserving the invariant ID and the lease-based recovery wording. (`REQ-001`)
   - [ ] Expand Decision Details item 11 to describe attempt recovery, processed-event deletion, and the guarded reconciliation, keeping UTC `Z` as the canonical timestamp. (`REQ-001`)
   - [ ] Add `tasks_reconciled` and the reconciliation scenarios to the INV-07 Verification row, citing `tests/agent/workflow/test_state_store.py` for reconciliation and the general-recovery test files for the lease/unparseable/timezone behavior. (`REQ-002`)
2. **Phase 2: Align the workflow-engine spec**
   - [ ] Correct line 166 of `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` to state the guarded reconciliation instead of "it never changes the persisted task status". (`REQ-003`)
   - [ ] Correct line 197 of the same file to state that a claimed task's parent IS reconciled when no live attempt remains. (`REQ-003`)
3. **Phase 3: Verification**
   - [ ] Confirm `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` still describes reconciliation consistently after any `adrrev009` landing; record `not affected` if a drift appears. (`REQ-004`)
   - [ ] Confirm ADR-001's `## Known Deviations` entry stays consistent once all named references match. (`REQ-005`)
   - [ ] Run the documentation checkers and hand off deployment. (`REQ-001`-`REQ-005`)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Static: invariant matrix, structure, Known Deviations sync, preservation (intended ERROR on INV-07/Verification change) | `uv run python tools/check_adr_invariant_matrix.py`, `check_adr_structure.py`, `check_known_deviation_sync.py`, `check_adr_preservation.py` | invariant matrix cites the reconciliation test; preservation reports the intended INV-07/Verification change |
| `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Static: doc quality, structure, content policy, agent-domain consistency | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain agent` | no contradictions with `db_07`; no Japanese; content policy clean |
| Whole change | Cross-doc consistency: ADR-001, `agent_03_03`, `db_07` all describe the same reconciliation | manual diff review + `check_docs_consistency.py` | all three agree on guarded reconciliation |

## Risks
- **Risk**: Expanding INV-07's wording is read as a substantive decision change requiring RACI approval. → **Mitigation**: `governance_01` line 296 classifies documenting existing approved behavior as an evidence correction (no reopened approval); the decision and invariant ID are preserved. If the maintainer disagrees, the same-change RACI approval is obtained before the edit (recorded as a non-blocking Unknown).
- **Risk**: Editing the `agent_03_03` Startup Recovery paragraph leaves other stale recovery wording (e.g. the adrrev005 lease-less age rule, line 169) unaddressed. → **Mitigation**: scope is reconciliation only; the lease-less wording is flagged out-of-scope and handled by the adrrev005 work.
- **Risk**: Overlap with `adrrev009` on `db_07`. → **Mitigation**: `db_07` is a reference file (already correct), not a target; sequence after `adrrev009` lands and re-confirm no drift.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Amend ADR-001 INV-07, Decision Details item 11, and Verification | In Progress | — | — |  |
| 2 | Align `agent_03_03` Startup Recovery and Known Limitations | In Progress | — | — |  |
| 3 | Confirm `db_07` alignment and Known Deviations, run doc checkers | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261115-195612_01_docs_10_adr_adr_02_02_001_agent-workflow-engine-mandatory.md.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261115-195612_02_docs_23_agent_agent_03_03_turn-processing-flow-workflow-engine.md.md` | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261111-163819_wfrecov001_adr001-recovery-reconciliation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-053822
- **Related target files**: `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes; Background | `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Phase 1 | AC-001, AC-003 | invariant matrix + manual review | Confirmed by repository evidence |
| REQ-002 | Required Changes; Testing Expectations | `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Phase 1 | AC-004 | `check_adr_invariant_matrix.py`, `check_adr_structure.py` | Confirmed by repository evidence |
| REQ-003 | Problem; Required Changes | `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Phase 2 | AC-002, AC-005 | `check_docs_consistency.py --domain agent` | Confirmed by repository evidence |
| REQ-004 | Dependencies; Required Changes | `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Phase 3 | AC-005 | manual diff review | Confirmed by repository evidence |
| REQ-005 | Constraints; Acceptance Criteria | `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Phase 3 | AC-005 | `check_known_deviation_sync.py` | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261115-195612 -->