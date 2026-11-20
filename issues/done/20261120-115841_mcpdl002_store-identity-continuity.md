# Rebuild the MCP dedup ledger as an atomic owner lease with store identity

## Priority
High

## Summary
Replace the lookup-then-record ledger with atomic execution ownership, renewable leases, immutable terminal evidence, and attempt history, and give the store a verifiable identity created at initialization, so that exactly one caller owns a logical call at a time and a lost, replaced, or unverified store blocks side-effecting calls until an operator resolves it.

## Background
Source: consolidated MCP deduplication two-layer defense backlog (`memo-issue.md`, Issue 2), the whole item. It also takes over the storage half of the earlier ledger redesign filed as `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`, which now keeps only the dispatcher integration and depends on this issue. The issue is implemented after `issues/20261120-115840_mcpdl001_approval-grant-intent.md` (logical call id format). Related archived work: `issues/done/20261109-112844_adrrev008_mcp-dedup-ownership.md` (store classified as a disposable cache, Option B) and `issues/done/20261117-123018_adrchk018_mcp-retry-classes.md`; re-verify this issue if either changed the store contract.

Evidence (`Explicit in code`, by reading): `scripts/shared/mcp_dedup.py` exposes separate `record_pending` (line 310), `lookup` (line 390), `record_completed`, `record_failed`, and `mark_interrupted`; writes use `BEGIN IMMEDIATE` per call, but lookup and pending write are separate transactions. `record_pending(force=True)` resets a terminal row to pending (lines 318-323). The store has no owner, lease, heartbeat, or attempt number. Store loss is partly detected: `DedupStore.__init__` (lines 262-266) sets `lost_or_recreated` when the database file is absent and the out-of-band sentinel `.mcp_dedup_resolved` exists (`DEDUP_SENTINEL_NAME`, line 73). The sentinel is written only by `resolve_lost_store()` (lines 453-470), the operator-resolution step, which also calls `touch()` on the database path, so a store lost before any acknowledgement looks like a first run. Open-time validation compares only the table shape (`assert_matches`, line 281). `ADR-008` classifies the store as a disposable cache that is recreated after loss, with non-retryable tools rejected until an operator resolves the state; `ADR-004` records an exception under which a retryable tool proceeds overlay-only when the store is unavailable, lost, or recreated, and `scripts/mcp_servers/dispatch.py` (lines 168-177) implements that fail-open path. A store UUID, generation, and configuration fingerprint appear nowhere (`rg`). The concurrency, state-classification, and snapshot-mismatch claims in Problem are from the review and `Needs confirmation` against the current dispatcher.

## Problem
- Two concurrent callers can both observe no active owner and both execute the same handler (`Needs confirmation`: reproduce with a concurrency test first).
- A terminal row can be reset to pending (the `force` path, a snapshot mismatch, or a truncated stored result), which destroys reconciliation evidence and can execute the same logical call again; a zero-row update can pass silently (`Needs confirmation`).
- Without a marker written at normal initialization, a database that disappears or is replaced by an empty one cannot be told apart from a first start, and previously executed side effects lose their evidence; recovery by creating an empty file hides the loss.

## Reason for Change
Duplicate execution of external side effects is a correctness and data-integrity risk. Ownership without identity would still let all evidence vanish, and identity without atomic ownership would only preserve an unsafe ledger, so both change the same schema in one rollout.

## Implementation Intent
One transaction atomically acquires an attempt for a logical call; only the current owner heartbeats or finalizes; an expired lease requires reconciliation and never authorizes a retry by itself; terminal rows and their original snapshots are immutable and further attempts go to an attempt-history table. A store UUID and generation are created at successful initialization with the schema and configuration fingerprints, and an external installation marker is written atomically at the same moment. Each open is classified as first initialization, healthy, lost, replaced, legacy or unverified, or schema mismatch, and side-effecting calls are rejected in every state but the first two. Resolution is an explicit operator action that issues a new generation; creating an empty file is never a recovery. Retryability is a property of a known recovery procedure, not of the transport.

## Target Files or Areas
- `scripts/shared/mcp_dedup.py`, `scripts/shared/execution_snapshot.py`
- The dedup DDL, the schema fingerprint module, and the database schema version manifest (`registry/manifests/db_schema_versions.yaml`, a generated file: regenerate it with `tools/generate_reference_table.py` and never hand-edit; it holds no dedup entry today, and whether one is required is `Needs confirmation`)
- Deployment initialization and operator-recovery scripts (`deploy/init_db.sh`, others `Unknown`)
- `tests/shared/test_mcp_dedup.py` and new concurrency test files (they do not exist yet and are created here)

## Required Changes
- Replace separate lookup and pending write with one typed acquisition operation (`try_acquire_execution()`): row lookup, classification, and ownership acquisition in one `BEGIN IMMEDIATE` transaction, returning `acquired`, `completed`, `in_progress`, `outcome_unknown`, `reconciliation_required`, contract or snapshot mismatch, or `replay_unavailable`; do not hold a SQLite transaction open during handler execution.
- Add `owner_id`, `lease_expires_epoch`, and `attempt_number`; add owner-conditional heartbeat and finalization that require exactly one updated row, and return a typed ownership conflict otherwise.
- Treat lease expiry only as a reconciliation trigger; separate the interrupted and failed recovery classification.
- Make terminal rows and their original snapshots immutable in code and in SQL predicates; record further attempts in an attempt-history table; add the schema fingerprint to the execution compatibility data.
- Remove the `force=True` path of `record_pending` and every lookup-plus-record caller pattern from production code.
- Store the store UUID, generation, schema fingerprint, and configuration fingerprint in database metadata; write the installation marker atomically at initialization; classify the start state as listed in Implementation Intent.
- Reject side-effecting calls in the lost, replaced, legacy or unverified, and mismatch states; decide how the retryable overlay-only exception is treated (Unresolved Questions).
- Replace `resolve_lost_store()` by an operator resolution that records the decision and issues a new generation; remove the `touch()` recovery.
- Treat a database from before this change as legacy or unverified, not as healthy and not as a first start.

## Constraints
- Exactly-once ownership must hold across async callers, connections, and processes.
- A change to an ADR decision, invariant, authority edge, or registered exception needs a maintainer approval record in the same change (`governance_01`, `governance_05`). ADR-008 Decision Details 22 and 23 (shape mismatch archives and recreates, no migration; unbounded growth accepted), the disposable-cache classification, and the ADR-004 retryable overlay-only exception are such decisions; do not write or simulate that approval.
- Existing incompatible dedup databases are rejected by the schema and fingerprint gate; the old table is not silently reinterpreted. The DDL change forces database recreation; plan the rollout with the dispatcher change of `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`.
- Follow the Current-Specification-Only policy: no tolerant start for an unverified store.

## Acceptance Criteria
- [ ] Exactly one caller acquires a new logical call under concurrency; a non-owner cannot heartbeat or finalize; an old owner cannot finalize after recovery.
- [ ] Terminal states cannot regress; a zero-row update is never a success.
- [ ] Only an expired lease can become interrupted, and expiry does not grant retry permission.
- [ ] Deleting the database after normal operation is detected as loss; replacing it is detected as an identity mismatch; marker-only deletion is detected.
- [ ] A legacy or unverified store blocks side-effecting calls until resolved; resolution issues a new generation and an empty file alone does not resolve.
- [ ] Production callers cannot invoke the force reset or a lookup-plus-record pattern.

## Testing Expectations
- One key submitted by 100 concurrent async callers acquires ownership exactly once; multi-connection and multi-process ownership; heartbeat versus stale recovery; finalization versus recovery; process kill during dispatch; terminal immutability.
- Database-only deletion, marker-only deletion, database replacement, legacy database, schema mismatch, first initialization; operator resolution and generation rollover.
- Run ruff, mypy, `tools/check_db_separation.py`, the schema and fingerprint checks, and the full test suite.

## Documentation Impact
Yes. The ownership and lease state machine, the store identity and start states, the operator resolution, and the ADR-008 and ADR-004 statements affected (final sweep: `issues/20261119-140519_mcpai012_mcp-design-docs-update.md`).

## Out of Scope
- The dispatcher integration: heartbeat task, structured tool results, and the dispatcher fail-closed rule (`issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`).
- The logical call id and Agent-side contracts (`issues/20261120-115840_mcpdl001_approval-grant-intent.md`); retention and monitoring (`issues/20261120-115844_mcpdl005_retention-capacity-monitoring.md`); reconciliation and result replay (`issues/20261120-115843_mcpdl004_call-state-control-api.md`).

## Dependencies
- Depends on `issues/20261120-115840_mcpdl001_approval-grant-intent.md` (logical call id format). Blocks `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md` (dispatcher integration), `issues/20261120-115842_mcpdl003_dedup-config-isolation.md`, `issues/20261120-115843_mcpdl004_call-state-control-api.md`, `issues/20261120-115844_mcpdl005_retention-capacity-monitoring.md`, and `issues/20261120-115845_mcpdl006_two-layer-failure-verification.md`.

## Unresolved Questions
- `不明`: whether the attempt-history table and immutable evidence are consistent with the disposable-cache classification (ADR-008); if the evidence must outlive the cache, an ADR-008 change with approval is needed.
- `不明`: whether retryable tools also fail closed after loss, which removes the ADR-004 overlay-only exception (owner decision).
- `不明`: heartbeat interval and lease duration values, and where the external marker lives and how deployment mounts it.
- `不明`: the final state vocabulary (`review_required`, `replay_unavailable`, `outcome_unknown`); this issue decides it once, for `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`, `issues/20261120-115843_mcpdl004_call-state-control-api.md`, and `issues/20261120-115845_mcpdl006_two-layer-failure-verification.md`.
- `不明`: whether the current dispatcher already serializes acquisition in-process; confirm by the concurrency test before changing storage.

## AI Implementation Instruction
Write the 100-caller concurrency test and the loss and replacement tests first and confirm they fail on current code. Do not recover by touching an empty file. Do not write ADR approval statements. Stop and report the ADR-008 and ADR-004 conflicts instead of resolving them.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261120-115841
- **Related target files**: `scripts/shared/mcp_dedup.py`, `scripts/shared/execution_snapshot.py`, `deploy/init_db.sh`, `tests/shared/test_mcp_dedup.py`
