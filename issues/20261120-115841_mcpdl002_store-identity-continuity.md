# Detect loss and replacement of the dedup store with a store identity

## Priority
High

## Summary
Give the MCP dedup store a verifiable identity created at initialization, so that deletion, replacement, or an unverified legacy store is detected and blocks side-effecting calls until an operator resolves it.

## Background
Source: consolidated MCP deduplication two-layer defense backlog (`memo-issue.md`, Issue 2, store-continuity part). The ownership, lease, and immutable-evidence parts are carried by `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`, which was updated to hold them.

Evidence (`Explicit in code`, by reading): `scripts/shared/mcp_dedup.py` already detects some loss. `DedupStore.__init__` (lines 262-266) sets `lost_or_recreated` when the database file is absent and the out-of-band sentinel `.mcp_dedup_resolved` exists (`DEDUP_SENTINEL_NAME`, line 73). The sentinel is written only by `resolve_lost_store()` (lines 453-470), the operator-resolution step, which also calls `touch()` on the database path. Normal initialization writes no marker, so a store lost before any operator acknowledgement looks like a first run. Open-time validation compares only the table shape (`assert_matches`, line 281). `ADR-008` classifies the store as a disposable cache that is recreated after loss, with non-retryable tools rejected until an operator resolves the state, and `ADR-004` records an exception under which a retryable tool proceeds overlay-only when the store is unavailable, lost, or recreated; `scripts/mcp_servers/dispatch.py` (lines 168-177) implements that fail-open path. A store UUID, generation, and configuration fingerprint appear nowhere (`rg`).

## Problem
Without a marker written at normal initialization, a database that disappears or is replaced by an empty one cannot be told apart from a first start, and previously executed side effects lose their evidence; recovery by creating an empty file hides the loss.

## Reason for Change
Duplicate execution after store loss is a data-integrity risk. It can only be handled together with the ledger schema change of `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`, which changes the same DDL.

## Implementation Intent
Create a store UUID and generation at successful initialization and record them with the schema and configuration fingerprints in database metadata. Write an atomic external installation marker outside the database file at the same moment. Classify each open as first initialization, healthy, lost, replaced, legacy or unverified, or schema mismatch, and reject side-effecting calls in every state but the first two. Resolution is an explicit operator action that issues a new generation; creating an empty file is never a recovery.

## Target Files or Areas
- `scripts/shared/mcp_dedup.py`, `scripts/mcp_servers/dispatch.py`
- The dedup DDL, the schema fingerprint module, and the database schema version entry (exact files `Unknown`)
- Deployment initialization and operator-recovery scripts (`deploy/init_db.sh`, others `Unknown`)
- `tests/shared/test_mcp_dedup.py`, `tests/mcp_servers/test_mcp_dispatch.py`

## Required Changes
- Store UUID, generation, schema fingerprint, and configuration fingerprint in database metadata after successful initialization.
- Write the installation marker atomically at initialization; classify the start state as listed above.
- Reject side-effecting calls in the lost, replaced, legacy or unverified, and mismatch states; decide how the retryable overlay-only exception is treated (Unresolved Questions).
- Replace `resolve_lost_store()` by an operator resolution that records the decision and issues a new generation; remove the `touch()` recovery.
- Treat a database from before this change as legacy or unverified, not as healthy and not as a first start.

## Constraints
- A change to an ADR decision, invariant, or registered exception needs a maintainer approval record in the same change (`governance_01`, `governance_05`); changing the ADR-008 disposable-cache classification or the ADR-004 retryable overlay-only exception is such a change. Do not write or simulate that approval.
- Follow the Current-Specification-Only policy: no tolerant start for an unverified store.
- The DDL change forces database recreation; plan the rollout together with `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`.

## Acceptance Criteria
- [ ] Deleting the database after normal operation is detected as loss.
- [ ] Replacing it with another database is detected as an identity mismatch.
- [ ] A legacy database blocks side-effecting calls until resolved.
- [ ] Marker-only deletion is detected.
- [ ] Resolution issues a new generation and an empty file alone does not resolve.

## Testing Expectations
- Database-only deletion, marker-only deletion, database replacement, legacy database, schema mismatch, first initialization; operator resolution and generation rollover; dispatcher behavior per state.
- Run ruff, mypy, `tools/check_db_separation.py`, and the full test suite.

## Documentation Impact
Yes. The store identity, the start states, the operator resolution, and the retention of the ADR-008 and ADR-004 statements affected.

## Out of Scope
- The ledger ownership and lease redesign (`issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`); retention and monitoring (issues/20261120-115844_mcpdl005_retention-capacity-monitoring.md).

## Dependencies
- Depends on `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md` (same DDL and rollout). Blocks issues/20261120-115842_mcpdl003_dedup-config-isolation.md, issues/20261120-115844_mcpdl005_retention-capacity-monitoring.md, and issues/20261120-115845_mcpdl006_two-layer-failure-verification.md.

## Unresolved Questions
- `不明`: whether retryable tools also fail closed after loss, which removes the ADR-004 overlay-only exception (owner decision).
- `不明`: where the external marker lives and how the deployment mounts it.
- `不明`: how a legacy database is told from a first start.

## AI Implementation Instruction
Write the loss and replacement tests first. Do not recover by touching an empty file. Do not write ADR approval statements. Stop and report the ADR-008 and ADR-004 conflicts instead of resolving them.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261120-115841
- **Related target files**: `scripts/shared/mcp_dedup.py`, `scripts/mcp_servers/dispatch.py`, `deploy/init_db.sh`, `tests/shared/test_mcp_dedup.py`, `tests/mcp_servers/test_mcp_dispatch.py`
