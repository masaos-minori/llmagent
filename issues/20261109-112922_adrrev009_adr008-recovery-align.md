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

## Adversarial Verification Results

Verified against current source on 2026-11-10. Overall: the core problem is real and
well-founded; the items are almost entirely documentation-consistency work; no code
change is warranted for the central claims because the automated recovery path already
implements the safe behavior. Two genuine self-contradictions are confirmed; one apparent
contradiction narrows to a wording issue; a few items need a maintainer decision.

| # | Claim in issue | Verified against | Verdict |
|---|---|---|---|
| 1 | Copying a backup over a DB that still has stale `-wal`/`-shm` can let SQLite replay those frames onto the restored file and produce a corrupted/mixed DB. | SQLite WAL semantics; `scripts/db/recovery_restore.py::_quarantine_sidecar_files()` (deliberately moves sidecars aside) vs `agent_10_01` Manual Recovery Step 5 (lines 127-134: `cp ... workflow.sqlite`, no sidecar handling). | CONFIRMED. Technically sound. The automated path treats leaving sidecars as hazardous (it quarantines them); the manual path does not. Deterministic test reproduction is non-trivial, but the hazard is real and the code's own behavior confirms it. |
| 2 | Restoring `eventbus.sqlite` while a service holds it open can leave the service writing to an unlinked file. | `scripts/eventbus/app.py` (lines 231-265: a persistent uvicorn HTTP server, `eventbus.app:app`); ADR-008 Scope "Target processes: the Agent process, the ingester process, the EventBus process" (separate from the agent). | CONFIRMED. The EventBus is a standalone persistent uvicorn process, not a subprocess of the agent. `cp` over a held-open file unlinks the original inode; the service keeps writing to it. |
| 3 | `agent_10_01` Manual Recovery: Step 1 stops the agent; Step 2 copies only main DB files; Step 4 verifies with `PRAGMA integrity_check`; Step 5 copies over the live file WITHOUT moving `-wal`/`-shm`; Step 6 removes them; the EventBus service is not named as something to stop. | `agent_10_01` lines 100-143. | CONFIRMED, all sub-parts. Step 5 (127-134) performs only `cp` + `PRAGMA integrity_check` (no sidecar handling). Step 6 (137-143) runs `rm -f ...-wal ...-shm`. The EventBus service is never named; Step 1's "ensure no remaining subprocesses" does not cover a top-level process. |
| 4 | The automated path already quarantines sidecars and stages a verified candidate. | `scripts/db/recovery_restore.py::_stage_restore()`, `_quarantine_sidecar_files()`, `_stage_backup_sidecars()`; `scripts/db/recovery.py::_restore_from_backup()`, `_verify_candidate()`, `_activate_candidate()`. | CONFIRMED. |
| 5 | `db_07` section 9.2 says nothing validates the backup's integrity before use, while 9.5 says it is verified; which matches code? | `db_07` line 36 (9.2): "Nothing in the current implementation validates the backup's own integrity before it is used — see 9.4 and 9.5." vs line 62 (9.5): "Backup integrity IS verified before use (`_run_integrity_check(backup, target)`)." Code: `recovery.py::_backup_is_usable()` runs `_run_integrity_check(backup, target)` before any copy. | CONFIRMED — genuine self-contradiction. 9.5 matches the code; line 36 in 9.2 is stale/wrong. Resolves the issue's "Needs confirmation". |
| 6 | ADR-008 INV-14 requires independent verification before restore. | ADR-008 INV-14 (line 261). | CONFIRMED. |
| 7 | ADR-008 INV-16 says Dry Run never rewrites the target DB; the verification test notes a rollback-journal file is switched to WAL when opened and is not covered; Known Deviations says "Not applicable". | ADR-008 INV-16 (line 263); Automated Tests table line 311 (`test_recover_dry_run_corrupt_file_unchanged`... "a rollback-journal file is switched to WAL when opened and is not covered"); Known Deviations line 349. | CONFIRMED present. The tension is real but narrow: the journal-mode change only affects a rollback-journal-mode DB, which the ADR states should not occur (WAL enforced). "Not applicable" is defensible for standard WAL deployments but is inconsistent with the test-note documenting the edge case. Fix-vs-record remains a maintainer decision. |
| 8 | Decision Detail #7 (Event ID relates data across DBs) contradicts #8 (no runtime component publishes/consumes from the EventBus). | ADR-008 Decision Details #7 (line 120) and #8 (line 121); `scripts/agent/eventbus_subscriber.py` (`EventBusSubscriber` defined, imported nowhere else); publish reachable only via the HTTP endpoint in `scripts/eventbus/app.py` (no runtime publisher found in `scripts/`). | PARTIALLY CONFIRMED. Both statements are present. However #8 is FACTUALLY ACCURATE against current source: nothing runtime publishes to or consumes from the EventBus. The tension with #7 is textual/logical, not a factual error. Narrows to a wording clarification, like adrrev007. |
| 9 | `memories_vec` classification (system of record versus derived). | ADR-008 Recovery Policy Matrix: "System of record" row lists `memories_vec` (line 92); "Derived or rebuildable data" row also lists `memories_vec` (from memories, line 93). | CONFIRMED — genuine self-contradiction. A store cannot be both system of record and derived. Needs a maintainer decision on the correct classification. |
| 10 | "Negative Consequences" wording on composite transactions. | ADR-008 Negative Consequences lines 229-230 ("Composite transactions become necessary"). | NEEDS REVIEW (uncertain). Ambiguous wording; possibly at odds with the cross-DB-transaction rejection. Not clearly wrong. Flagged for maintainer review. |
| 11 | Implementation References list contains `processed_events`, `consumer_delivery`, `consumer_offsets`, `dlq_outbox`. | ADR-008 Implementation References lines 396-411. | MISCHARACTERIZED. These table names exist in the codebase (`processed_events` in `workflow.sqlite`; `consumer_delivery`/`consumer_offsets`/`dlq_outbox` in `eventbus.sqlite` per `eventbus_06`), but they do NOT appear in ADR-008's Implementation References, which lists `eventbus.sqlite` (`events`) and `workflow.sqlite` (`tasks`, `attempts`, `artifacts`) — omitting them. The ADR is high-level and this omission is arguably acceptable. Confirm what the memo actually observed before treating it as a defect. |
| 12 | INV-18 citation in `agent_10_01`. | `agent_10_01` line 100 cites "ADR-008 INV-18"; ADR-008 INV-18 (line 265). | CONFIRMED. The citation exists and is correct. |

### Unresolved Question from the issue

- **"Does the EventBus service hold `eventbus.sqlite` open in the standard deployment, so the service stop is mandatory?"** → RESOLVED: yes. `scripts/eventbus/app.py` is a persistent uvicorn HTTP server (subscribers stay connected for SSE), separate from the agent process. In a standard deployment with the EventBus enabled it holds the file open, so stopping it during manual recovery is meaningful. Whether it runs in a given deployment depends on topology, but the ADR lists it as a distinct target process, so the manual procedure should name it explicitly rather than relying on Step 1's "no remaining subprocesses".

### Conclusion

- The core problem (manual recovery is less safe than the automated path: stale `-wal`/`-shm` replay + writing to an unlinked file held by the standalone EventBus service) is REAL and reproducible-in-principle. The fix is a documentation change to `agent_10_01` (add the EventBus service stop and move `-wal`/`-shm` aside before Step 5's `cp`, mirroring the automated `_quarantine_sidecar_files`), not a code change.
- Two self-contradictions are confirmed and should be fixed in-doc: `db_07` line 36 (9.2) vs line 62 (9.5), and ADR-008 `memories_vec` dual-listing (lines 92 vs 93).
- One apparent contradiction (#7/#8) is not a factual error; keep it as a wording clarification.
- Items 7 (Dry Run), 10 (Negative Consequences), 11 (Implementation References) and the `memories_vec` classification require a maintainer decision; do not fabricate approvals.
- No code change is required by the central claims; the automated restore path already quarantines sidecars and verifies the backup before use.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261109-112922
- **Related target files**: `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/10_adr/adr_01_index.md`, `scripts/db/recovery.py`, `scripts/db/recovery_restore.py`, `scripts/db/recovery_drill.py`, `tests/db/test_db_recovery.py`
