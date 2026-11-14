# Correct ADR-001 recovery and task-status reconciliation wording

## Priority
High

## Summary
Align ADR-001 and the related recovery references with the implemented stale-attempt recovery, which also reconciles an orphaned `running` task to `failed` in the same transaction.

## Background
Source: `memo-issue.md` (Issue A), re-verified against current source on 2026-11-11.

- `Explicit in code`: `StateStore.recover_stale_attempts()` in `scripts/agent/workflow/state_store.py` reconciles tasks and reports `RecoveryReport.tasks_reconciled`. The memo describes the transaction steps (classify, compare-and-swap claim, mark failed, delete the processed-event pair, reconcile the parent task only if no `running` attempt remains, commit together); these steps were not re-read in full in this pass (`Needs confirmation`).
- `Explicit in code`: `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` Amendment text says "the never-repairs-task-status guarantee of INV-07 [is] unchanged". INV-07 itself reads only "interrupted Attempts are recovered as `failed`".
- `Explicit in code`: ADR-001 `## Known Deviations` says `Not applicable`, and its Verification table lists three test files for `recover_stale_attempts()`.
- `Explicit in code`: `tests/agent/workflow/test_stale_recovery_lease.py` exists. The memo names `tests/test_workflow_state_store.py`; the ADR cites `tests/agent/workflow/test_workflow_state_store.py`; the actual location is `Needs confirmation`.
- Related archived work: `issues/done/20261107-203220_wfaudit007_task-status-never-reconciled.md` (the reconciliation itself).

## Problem
ADR-001 asserts that task status is never repaired by recovery, while the code and tests reconcile it. The ADR also does not describe `tasks_reconciled` or the reconciliation scenarios, and its Known Deviations section claims no deviation.

## Reason for Change
A critical documentation and code mismatch: an implementer or operator reading the ADR would expect orphaned tasks to remain `running` after recovery. The wording must be corrected before further recovery work (including legacy lease-less removal) relies on the ADR.

## Implementation Intent
- Describe the recovery transaction as a single current-tense rule in Decision Details item 11 and INV-07: attempt recovery, processed-event deletion, and guarded parent-task reconciliation.
- State the guards: terminal tasks and tasks with a remaining live attempt are not changed, and only attempts claimed by the current transaction trigger reconciliation.
- Keep UTC `Z` as the canonical stored timestamp representation.
- Classify the ADR edit under governance: an evidence correction does not reopen approval; a substantive decision change needs same-change RACI approval.

## Target Files or Areas
- `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`
- `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` (path `Needs confirmation`)
- `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`
- `tests/agent/workflow/test_state_store.py`, `tests/agent/workflow/test_stale_recovery_lease.py`, and the legacy-recovery test file (verify path)

## Required Changes
- Remove the "never-repairs-task-status guarantee" claim from ADR-001.
- Amend Decision Details item 11 and INV-07 to describe attempt recovery, processed-event deletion, and guarded parent-task reconciliation.
- Add `tasks_reconciled` and the reconciliation scenarios to ADR-001 Verification, citing the correct test paths.
- Reconcile the Known Deviations entry until all related reference documents match.
- Align the workflow and DB recovery references named above.

## Constraints
- Documentation-only change; no code change.
- Documents under `docs/` are written in English (`skills/DESIGN.md` Output language) and must not carry change-history wording or line numbers.
- Removal of `_LEGACY_STALE_AGE_SEC`, `legacy_recovered`, and lease-less recovery tests is not part of this issue; it is owned by the schema-compatibility work (the archived `plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md` and the compatibility-removal issues).

## Acceptance Criteria
- ADR-001 and the code describe the same recovery transaction.
- No document claims that task status is never repaired by recovery.
- ADR-001 states that terminal tasks and tasks with a live attempt are not reconciled, and that reconciliation applies only to attempts claimed by the current transaction.
- All named recovery tests are listed with correct repository paths.
- Legacy lease-less removal is not duplicated across plans.

## Testing Expectations
Not required (documentation-only). Run the documentation checkers: `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_invariant_matrix.py`, `uv run python tools/check_adr_preservation.py`, `uv run python tools/check_known_deviation_sync.py`, and `uv run python tools/check_docs_consistency.py --domain agent`.

## Documentation Impact
Yes. Update ADR-001 (decision, invariant, verification, Known Deviations) and the workflow and DB recovery references: intent, boundaries (guards), and failure behavior. Do not copy implementation catalogs or concrete values.

## Out of Scope
- Code changes to `state_store.py`.
- Legacy lease-less recovery removal.
- Changing the recovery decision itself.

## Dependencies
Duplicate and overlap check (2026-11-11): no open issue duplicates this one. Overlapping items:
- `issues/done/20261107-203220_wfaudit007_task-status-never-reconciled.md` (overlap: archived, code side): reconcile task rows after stale-attempt recovery so crashed tasks do not stay `running`. It produced the behavior that ADR-001 still contradicts; this issue is the documentation follow-up only.
- `plans/20261111-110144_adrrev017_docs-history-wording.md` (overlap: partial): remove ADR Amendment sections, including ADR-001's `wflease001` Amendment that holds the false sentence. It removes history wording but does not correct INV-07, item 11, Verification, or Known Deviations.
- `plans/20261110-233648_adrrev009_adr008-recovery-align.md` (overlap: partial): make the manual recovery of `workflow.sqlite` and `eventbus.sqlite` safer and fix `db_07` and ADR-008 contradictions (documentation only).

Ordering and other dependencies:
- `plans/20261111-110144_adrrev017_docs-history-wording.md` removes ADR-001's Amendment section, which contains the false sentence. Re-verify this issue against current ADR-001 text after that plan lands; the INV-07 and item 11 corrections remain required either way.
- `plans/20261110-233648_adrrev009_adr008-recovery-align.md` edits `db_07`; sequence the two edits to that file.

## Unresolved Questions
Decision required from the maintainer before implementation:
- Decision 1 (governance class): whether the ADR-001 edit is an evidence correction (no reopened approval) or a substantive decision change that needs same-change RACI approval. Without it the approval record cannot be updated correctly.

Open facts (不明):
- 不明: the actual path of the workflow-engine reference document and the legacy-recovery test file.
- Assumption: the memo's description of the transaction steps is accurate.

## AI Implementation Instruction
- Edit only the named documents; do not touch code or tests.
- Preserve every decision, invariant ID, and approval record other than the corrected statements.
- Stop and report if the reconciliation behavior differs from the memo description.
- Do not implement out-of-scope items.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261111-163819
- **Related target files**: `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`, `scripts/agent/workflow/state_store.py`, `tests/agent/workflow/test_state_store.py`, `tests/agent/workflow/test_stale_recovery_lease.py`
