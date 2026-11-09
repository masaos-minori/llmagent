# Align ADR-008 with reality: safe manual recovery, consistent backup verification, Dry Run deviation, and correct decisions

## Priority
High

## Summary
Make the manual recovery procedure for `workflow.sqlite` and `eventbus.sqlite` as safe as the automated rag and session recovery (stop every process that holds the file, deal with `-wal` / `-shm` sidecars, verify the backup), remove the self-contradictions in `db_07` and ADR-008, and record the Dry Run journal-mode deviation truthfully.

## Background
- Source: `memo-issue.md` items H-11 and M-03, re-checked against current source on 2026-11-09.
- `Explicit in documentation` (`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, "Manual Recovery"): Step 1 stops "the agent process completely"; Step 2 copies only the main database files for forensics; Step 4 verifies a candidate backup with `PRAGMA integrity_check`; Step 5 copies the backup over the live file and does not move aside or remove existing `-wal` / `-shm` files (Step 6, the empty-database path, does remove them). The EventBus service is not mentioned as something to stop. This supports the memo's claim (`Needs confirmation`: whether the EventBus service holds eventbus.sqlite open in a standard deployment).
- `Explicit in code`: the automated path already quarantines sidecars and stages a verified candidate (`scripts/db/recovery_restore.py`, `recover_corruption()` in `scripts/db/recovery.py`).
- `Explicit in documentation` (`docs/41_db/db_07_api_and_operations-recovery-and-reference.md`): section 9.2 says nothing validates the backup's integrity before use, while section 9.5 says backup integrity is verified before use. ADR-008 INV-14 requires independent verification before restore. `Needs confirmation` against code which one is true for `recover_corruption()` (9.5 describes `_run_integrity_check(backup, target)` before use).
- `Explicit in documentation` (ADR-008, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`): INV-16 says Dry Run never rewrites the target database; the verification matrix notes that a rollback-journal file is switched to WAL when opened and is not covered, while Known Deviations says "Not applicable". Decision Detail #7 says Logical IDs including Event ID relate data across databases, and #8 says no runtime component publishes to or consumes from the EventBus, so events are not a consistency mechanism (an internal contradiction).
- `Needs confirmation` (not yet checked in this review): the classification of `memories_vec` (system of record versus derived), the "Negative Consequences" wording on composite transactions, the Implementation References list (`processed_events`, `consumer_delivery`, `consumer_offsets`, `dlq_outbox`), and the INV-18 citation in `agent_10_01`. INV-18 does exist in ADR-008 (automatic restore of workflow and eventbus prohibited).
- Related archived: `compat001` / `compat006` and the `rm*mig` issues under `issues/done/`.

## Problem
- Copying a backup over a database that still has stale `-wal` / `-shm` files can let SQLite replay those frames onto the restored file on next open, which can produce a corrupted or mixed database (`Needs confirmation` by reproduction).
- Restoring eventbus.sqlite while a service holds it open can leave the service writing to an unlinked file.
- The documents disagree on whether backup verification happens, so an operator cannot rely on them; Dry Run's journal-mode change is a persistent write that the ADR calls compliant.
- ADR-008 decisions that misstate correlation keys or classification can lead operators to rebuild data that cannot be rebuilt or to skip data that must be backed up.

## Reason for Change
- Manual recovery is the only restore path for workflow and eventbus (ADR-008 INV-18); an unsafe procedure defeats the purpose of recovery.
- Timing: depends on the schema-validation mechanism (post-restore verification) and the mcp_dedup classification in this batch.

## Implementation Intent
- Manual recovery is at least as safe as the automated rag and session recovery, and reuses the `recover_corruption` staging logic where possible.
- ADR-008 states ownership, derivation, verification, and deviations accurately, so the recovery matrix can be followed without reading code.
- Fix documentation and, where the documents correctly describe a missing safeguard, implement the safeguard; keep the automated restore prohibition for workflow and eventbus (INV-18).

## Target Files or Areas
- `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/10_adr/adr_01_index.md`
- `scripts/db/recovery.py`, `scripts/db/recovery_restore.py`, `scripts/db/recovery_drill.py` (only if backup verification or Dry Run needs a code change)
- `tests/db/test_db_recovery.py`

## Required Changes
- Rewrite the manual procedure: stop the EventBus service and the Agent, move `-wal` / `-shm` sidecars aside, verify the backup (`PRAGMA integrity_check` plus the schema fingerprint check from the schema-validation issue), restore, then start. Reuse the `recover_corruption` staging logic where possible.
- Implement backup verification before restore where it is missing, and make `db_07` sections 9.2 and 9.5 consistent with code.
- Make Dry Run never change the journal mode, or record the deviation in ADR-008 Known Deviations and the governance ledger (see the governance-ledger issue in this batch).
- Rewrite Decision Detail #7 to describe the actual correlation keys, classify `memories_vec` as derived only (after confirming), and fix Negative Consequences.
- Complete Implementation References, number the Decision items explicitly, and reconcile the INV numbering (INV-18 citation in `agent_10_01`).
- Add tests: a restore with a stale WAL present must not apply that WAL; a corrupted backup is refused.

## Constraints
- ADR-008 INV-18: automatic restore of workflow and eventbus stays prohibited; the procedure remains manual.
- A recovery change must keep the damaged database preserved before it is replaced.
- ADR amendments need approval records (governance-ledger issue); the implementer must not fabricate approvals.
- Follow the docs content policy: describe intent and failure behavior, not command-by-command catalogs beyond the minimal operator steps this procedure must contain (these are operator instructions, which the existing section already carries).

## Acceptance Criteria
- The manual procedure lists the EventBus service stop and the sidecar handling explicitly.
- Tests prove: a restore with a stale `-wal` present does not apply it; a corrupted backup is refused.
- No contradictions remain inside ADR-008 or `db_07`, and every cited INV exists.
- `check_adr_structure.py`, `check_adr_invariant_matrix.py`, `check_known_deviation_sync.py`, `check_docs_consistency.py --domain db` and `--domain agent` pass.

## Testing Expectations
- `uv run pytest tests/db/test_db_recovery.py -v` plus new tests for the stale-WAL and corrupted-backup cases; the full validation sequence from `rules/toolchain.md` if code changes.
- Documentation checkers listed above.

## Documentation Impact
- ADR-008, `db_07`, `agent_10_01`, and the ADR index change: recovery ordering, verification, deviations, ownership, and Known Issues. State failure behavior and operator responsibilities.

## Out of Scope
- Implementing the schema fingerprint (schema-validation issue in this batch).
- Deciding the mcp_dedup.sqlite classification (mcp_dedup issue in this batch).
- Automating restore for workflow and eventbus.

## Dependencies
- Depends on: `issues/20261109-112715_adrrev005_schema-fingerprint-unify.md` (post-restore fingerprint verification).
- Related: `issues/20261109-112844_adrrev008_mcp-dedup-ownership.md` (classification recorded in the same ADR-008 matrix), `issues/20261109-112538_adrrev002_agent-eventbus-coupling.md` (ownership of eventbus.sqlite).

## Unresolved Questions
- `Needs confirmation`: does the EventBus service hold eventbus.sqlite open in the standard deployment, so the service stop is mandatory?
- `Needs confirmation`: which of `db_07` 9.2 or 9.5 matches the code.
- `Needs confirmation`: the `memories_vec` classification and the other ADR-008 misstatements listed in the memo.
- Maintainer decision: fix Dry Run to avoid the journal-mode change, or accept and record the deviation.

## AI Implementation Instruction
- Reproduce the stale-WAL hazard in a test before changing the procedure; if it does not reproduce, report it and keep the procedure change minimal.
- Do not weaken INV-14, INV-16, or INV-18; do not add automatic restore for workflow or eventbus.
- Do not write approval records on a maintainer's behalf.
- Write documentation in English and follow the docs content policy; do not commit.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261109-112922
- **Related target files**: `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/10_adr/adr_01_index.md`, `scripts/db/recovery.py`, `scripts/db/recovery_restore.py`, `scripts/db/recovery_drill.py`, `tests/db/test_db_recovery.py`
