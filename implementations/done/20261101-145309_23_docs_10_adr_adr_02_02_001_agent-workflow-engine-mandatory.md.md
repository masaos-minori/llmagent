<!-- workitem: {"id": "20261101-145309", "generated_at": "2026-11-01T14:53:09Z", "schema_hash": "488513b688446992", "schema_version": 1, "source": "plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md", "target_file": "docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md", "target_kind": "documentation", "seq": 23} -->

## Goal

Amend ADR-001 invariants INV-07/INV-08 and their test-citation rows to the new recovery and ledger semantics (REQ-010 / AC-11).

## Scope

- Append an `### Amendment (wfrecovery001, 2026-11-XX)` block following the `docs/10_adr/adr_02_05_008_*.md` precedent (`### Amendment (dbmig001, 2026-10-30)` at `:73`).
- Revised INV-07 text: startup recovery fails the stale `running` attempt and atomically moves its owning `running` task to `failed`; repeated recovery is a no-op.
- Revised INV-08 text: stage idempotency keys on the completed-stage ledger row for the (task, stage) pair; a concurrent start of the same stage raises `StageAlreadyRunningError`.
- Update the test-citation rows (`adr_02_02_001:187-188`) to the new homes: `tests/agent/workflow/test_workflow_recovery.py`, `tests/agent/workflow/test_state_store.py`, `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_workflow_stage_persistence.py`.

## Assumptions

- Plan `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` is Frozen; its 26-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` commit `384eb72` on 2026-11-01.
- Canonical semantics come from the Plan REQs (Plan `:41-52`): REQ-001 matrix `pending->{running,halted}`, `running->{completed,failed,halted}`, `failed->{running}`, `completed->failed` transitional, `halted` terminal; exactly three typed errors in `scripts/agent/workflow/errors.py`; `processed_events` as the completed-stage ledger (Plan UNK-02 default); recovery atomically fails the stale attempt and its owning `running` task (Plan UNK-03); claim accepts `pending` or `failed` only (Plan UNK-01).
- Landing-order dependency (Plan UNK-05): the wftaskapi001 procedures (`implementations/20261101-140834_*`, plan `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md`) are generated but Pending; the shared migration ledger code is fixed at landing time.
- The ADR stays `Accepted`; the amendment records the change rather than rewriting history (ADR change protocol, `check_adr_preservation.py`).

## Design decisions

- Old invariant sentences remain quoted inside the amendment block for diffability.

## Alternatives considered

- Silently editing the invariant text in place: rejected by the ADR change protocol.

## Implementation
### Target file
`docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`

### Procedure
1. Draft the amendment block at the end of the Decision/Invariants region.
2. Update the two test-table rows in place.
3. Record the change in the commit message and the cycle report (docs checker requires an explanation per ADR change).

### Method
Direct edit: one appended section, two table-row updates.

### Details
- `adr_01_index.md:45` carries the ADR one-liner; re-check it for staleness when the amendment lands (docs checkers, not a frozen target row).

## Compatibility considerations

- INV-07/INV-08 wording also appears in `agent_03_03`/`agent_04_03`; rows 24/25 keep those docs consistent in the same phase.

## Security considerations

- Status/attempt values written to SQL come only from the `models.py` enums, never from caller strings; all state SQL stays parameter-bound.

## Rollback considerations

- Revert the amendment block with rows 24/25.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain agent`, `check_docs_japanese.py`, `check_adr_preservation.py`.

## Completion criteria

- AC-11: ADR invariants describe the implemented semantics and cite existing tests.

## Out of Scope

- Other ADRs; `agent_09_*` data-layer docs.

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
- **Workflow phase**: Phase 5 (Documentation and ADR)
- **Requirement ID**: `REQ-010`
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-145309
- **Related target files**: `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`, `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`

## Implementation Result (2026-11-03: superseded by upstream)

This wfrecovery001 procedure implemented an attempt-number-based recovery state
machine. Upstream (`origin/master`) superseded this design with a lease-based
stale-attempt recovery (wflease001, AC-2/AC-4/AC-5/AC-7). The batch was
therefore NOT merged into `origin/master`.

- **Decision (2026-11-03):** full supersession. Every one of the ~32 code files
  the batch touched was rewritten or replaced by upstream (lease columns on
  `attempts`, a `disable_foreign_keys` migration-runner rebuild, fail-closed
  tool audit, schema manifest bumped to workflow version 1.4.0). No substantive
  delta survives.
- **Action:** the 3-way merge (`git merge --no-commit backup-batch` onto branch
  `rederive` from `origin/master`) was aborted (`git merge --abort`), returning
  to a clean `origin/master` at `7d6744fd`.
- **Residual:** `attempt_number` / `CHECK` are entangled with upstream's
  lease/local-retry design and cannot be integrated as a clean, bounded
  addition; reintroducing them would fight the lease architecture.
- **Outcome:** divergent code is not integrated. The batch remains on
  `backup-batch` as a superseded historical record. All 26 procedures were
  executed and marked Completed on `backup-batch`; this note records the
  supersession.

