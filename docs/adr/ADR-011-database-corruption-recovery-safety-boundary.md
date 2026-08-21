---
title: "ADR-011: Database Corruption Recovery Safety Boundary"
category: adr
status: proposed
date: "2026-08-21"
last_updated: "2026-08-21"
owners:
  - agent-team
reviewers:
  - architecture-reviewer
decision_scope:
  - shared/db
related: []
supersedes: []
superseded_by: null
---

# ADR-011: Database Corruption Recovery Safety Boundary

## Status

Proposed

Allowed values: `Proposed`, `Accepted`, `Rejected`, `Deprecated`, `Superseded`. Changing an Accepted decision requires a new ADR that supersedes this one, not an edit to this body.

## Summary

Database corruption recovery MUST classify failures before acting on them, MUST NOT overwrite the only recoverable copy of a database before a candidate backup is independently validated, and MUST NOT let recovery policy differ by accident rather than by explicit persistence-domain decision. This ADR establishes the safety boundary that `recover_corruption()` and its callers MUST satisfy, and records where the current implementation does not yet satisfy it.

## Context

### Problem

The system persists state across separate SQLite files (`rag`, `session`, `workflow`, `eventbus`) with different recoverability profiles. A recovery mechanism exists (`recover_corruption()`) but was implemented incrementally without an explicit safety contract: it does not classify *why* a database failed to open, it can restore from a backup that was never itself validated, and it writes directly onto the live database file rather than through a verified staging step. The `workflow` and `eventbus` persistence domains have no recovery path at all.

### Constraints

- Single-host, single-process SQLite deployment; no external replication.
- Recovery is currently a manual, operator-triggered action, not an automatic startup step.
- No migration framework exists; schema changes require full DB recreation, which is out of scope here.

### Assumptions

- Target environment: single host, single agent process.
- Backups are periodic file copies (`rotate_all_dbs()`), not continuously verified snapshots.
- Re-evaluate if: multi-host/replicated storage is introduced, or backups move to a different mechanism (e.g., WAL shipping).

## Decision

### Decision Details

1. Recovery MUST classify the database condition (healthy / confirmed corruption / lock contention / permission failure / invalid format / unknown) before choosing an action. Lock contention and permission failures MUST NOT be classified as physical corruption.
2. A candidate backup MUST be validated independently (e.g., its own integrity check) before it is used to replace a target database.
3. Restoration MUST stage the candidate at a temporary location, verify it, and only then atomically replace the target. The target database MUST NOT be overwritten before the candidate passes validation.
4. The damaged database SHOULD be preserved for diagnostics before any replacement is attempted, on every failure path — not only the paths that currently happen to reach the preservation step.
5. Dry Run MUST NOT move, replace, truncate, delete, or rewrite the target database under any classification outcome, including the physical-corruption path.
6. Recovery policy is explicit per persistence domain: reconstructable derived data (RAG indexes) may rebuild from its authoritative source; session data may restore from backup; workflow/approval data and event-delivery state require an explicit decision (recovery path or accepted unrecoverability) rather than silent reinitialization.
7. Unknown or unclassifiable failures MUST preserve the target database and require operator intervention rather than triggering automatic restoration.

### Scope

- **Components**: `db/recovery.py`, `db/maintenance.py`, `db/helper.py`, callers in `agent/services/db_maintenance_service.py` and `agent/services/rag_maintenance_service.py`.
- **Data**: `rag.sqlite`, `session.sqlite`, `workflow.sqlite`, `eventbus.sqlite`.
- **Processes**: manual CLI-triggered recovery; startup-time DB-open failure handling.

### Out of Scope

- Automatic (unattended) triggering of recovery — recovery remains operator-initiated until a separate decision introduces automation.
- Migration/schema-versioning strategy.
- Continuous backup verification or replication design.

## Rationale

### 1. Correctness

A recovery mechanism that cannot tell corruption apart from a transient lock is more dangerous than no recovery mechanism, because it can be invoked (or scripted to run) against a database that was never actually broken.

### 2. Data Integrity

Restoring from an unvalidated backup, or overwriting the target non-atomically, converts a single-file corruption incident into a risk of losing both the damaged original and a working backup.

### 3. Operability

Undefined behavior for the `workflow`/`eventbus` persistence domains means operators have no documented action to take when those domains are the ones that fail — this ADR forces that gap to be visible rather than silently assumed away.

## Alternatives Considered

### Alternative A: Treat every DB-open failure as corruption and always restore from backup

#### Advantages
Simple, single code path.

#### Disadvantages
Restores over transient lock/permission failures unnecessarily; risks discarding recent writes when the "corruption" was actually a temporary condition.

#### Reason for Rejection
Violates the classification invariant (Decision Details #1); observed lock-contention behavior in the current implementation already avoids this trap and this ADR codifies keeping it that way.

### Alternative B: Leave `workflow`/`eventbus` unrecoverable by policy, permanently

#### Advantages
No implementation work required.

#### Disadvantages
An unannounced permanent gap; operators may assume recovery exists because it exists for `rag`/`session`.

#### Reason for Rejection
Acceptable only if made an explicit, documented decision with a stated operator procedure — not as an unstated default. This ADR requires the decision to be explicit, not that it be resolved in a particular direction.

## Consequences

### Positive Consequences
- Recovery actions become auditable against a stated safety contract.
- Backup corruption or partial restores are caught before they replace a working (if damaged) database.

### Negative Consequences
- Recovery becomes more code and more steps (validate candidate, stage, verify, atomic replace) than the current single-copy implementation.

### Operational Consequences
- Operators need a documented procedure for `workflow`/`eventbus` corruption even if that procedure is "no automated recovery; restore from operational backup manually."

### Security Consequences
- Error messages and audit records for recovery actions MUST continue to avoid embedding row-level DB content, per current observed behavior (paths and exception text only).

## Invariants

- INV-01: `sqlite3.DatabaseError` MUST NOT propagate from the recovery boundary unclassified.
- INV-02: A backup MUST be validated before being used to replace a target database.
- INV-03: The target database MUST NOT be overwritten before the candidate passes validation.
- INV-04: Dry Run MUST NOT modify the target database under any classification outcome.
- INV-05: Lock contention and permission failures MUST NOT be classified as physical corruption.

## Exceptions

None.

## Failure Policy

### Fail-Fast Conditions
- Unknown or unclassifiable integrity-check failure.
- Backup candidate fails independent validation.

### Fail-Open or Degraded Conditions
- None — corruption recovery is a Fail-Closed domain by design; when in doubt, preserve state and require operator action rather than acting automatically.

### Retry Policy
- Not applicable — recovery is a single, operator-triggered attempt; no automatic retry loop exists or is introduced by this decision.

### Fallback Policy
- Not applicable.

## Data Ownership and Persistence

- **System of Record**: `rag.sqlite`, `session.sqlite`, `workflow.sqlite`, `eventbus.sqlite`.
- **Derived Data**: RAG full-text/vector indexes (reconstructable from the `chunks` table).
- **Ownership**: `db/recovery.py` (recovery coordination), `RagMaintenanceService` (derived-index rebuild).
- **Recovery Source**: operator-supplied backup file path.
- **Deletion Rule**: the preserved damaged-database archive is retained for diagnostics; its retention/cleanup policy is not yet defined (Known Issue).

## Verification

### Automated Tests
- **Test**: physical-corruption path does not silently trigger restoration — **Verifies**: INV-01 — **Type**: Integration — **Blocking**: Yes
- **Test**: lock-contention path does not classify as corruption — **Verifies**: INV-05 — **Type**: Regression — **Blocking**: Yes (already covered by existing test suite per investigation)
- **Test**: Dry Run leaves the target database byte-identical on every classification path — **Verifies**: INV-04 — **Type**: Integration — **Blocking**: Yes

### Manual Review
- Review of the persistence-domain policy decision for `workflow`/`eventbus` before closing the corresponding Known Issue.

## Migration and Rollout

Existing implementation partially satisfies this decision (classification of lock contention is already correct); the remaining gaps are tracked as Known Issues (SHARED-001, SHARED-002, SHARED-003) rather than requiring a rollout plan of their own.

### Compatibility
No backward-compatibility impact — `recover_corruption()`'s external call signature is unaffected by closing these gaps.

### Rollback
Not applicable pre-implementation.

### Completion Criteria
This ADR moves to Accepted once SHARED-001/002/003 are resolved and the invariants above are covered by passing tests.

## Implementation Notes

- Implementation files: `scripts/db/recovery.py`, `scripts/db/maintenance.py`
- Key functions: `recover_corruption()`, `_run_integrity_check()`, `_restore_from_backup()`
- Corresponding tests: `tests/db/test_db_maintenance.py`, `tests/integration/test_session_recovery.py`

## Known Deviations

- **Known Issue**: SHARED-001 — `sqlite3.DatabaseError` propagates uncaught instead of being classified.
- **Known Issue**: SHARED-002 — backup is not validated before use; restoration is not atomic; no post-restore re-verification.
- **Known Issue**: SHARED-003 — `workflow`/`eventbus` domains have no recovery path.

## Review Triggers

- A migration framework or replicated storage backend is introduced.
- Backup strategy changes from periodic file copy to a different mechanism.
- An automated (unattended) recovery trigger is proposed.

## Approval

### Required Reviewers
- Architecture Owner
- Data Owner

### Approval Record
- **Approved By**: pending
- **Approval Date**: pending

## Related Documents

### Specifications
- [DB API and Operations — Recovery and Reference](../90_shared_05_04_db_api_and_operations-recovery-and-reference.md)

### Known Issues
- SHARED-001, SHARED-002, SHARED-003 in [Shared/DB Known Issues](../90_shared_90_inconsistencies_and_known_issues.md)

### Implementation References
- `scripts/db/recovery.py` — `recover_corruption()`, `_run_integrity_check()`, `_restore_from_backup()`

## Change History

- 2026-08-21: Created as Proposed.
