---
title: "ADR-008: Separating SQLite into Four Databases"
area: governance
tags:
  - system
  - sqlite
  - database-separation
decision_scope:
  - system
related:
  - ADR-002-config-isolation.md
  - adr_08_sqlite-4db-supporting-sections.md
  - db_02_architecture_and_schema-schema-reference.md
  - db_07_api_and_operations-recovery-and-reference.md
  - agent_09_01_data-layer-session-db.md
  - eventbus_06_persistence_schema_and_replay.md
  - eventbus_05_dlq_offsets_and_delivery_semantics.md
  - agent_10_01_operations-and-observability-startup-and-health.md
  - governance_03_issue-and-uncertainty-management.md
---

# ADR-008: Separating SQLite into Four Databases

## Keywords

sqlite
database separation
recovery policy
backup

## Status

Accepted

## Summary

This ADR canonicalizes the decision to separate data with different update frequencies, failure scopes, retention periods, and recovery methods into four SQLite DBs. It defines the responsibilities of `rag.sqlite`, `session.sqlite`, `workflow.sqlite`, and `eventbus.sqlite`, and explains that cross-DB Transactions are not used and how consistency is ensured. It limits the scope of sqlite-vec and organizes the Backup, Recovery, and retention policy per DB. It also canonicalizes the safety boundary for recovery from physical corruption (failure classification, independent verification of backup candidates, Atomic replacement, a no-change guarantee for Dry Run, and a recovery policy per persistence domain).

## Context

### Problem

The RAG index, session state, workflow state, and event bus state differ in update frequency, lock contention, failure scope, retention period, and recovery method. Single-DB management causes WAL contention, failure propagation, and complex backups.

When separated into multiple SQLite files, a recovery mechanism without an explicit safety contract is dangerous. One that cannot distinguish physical corruption from temporary lock contention may run against a DB that is not actually broken—more dangerous than no recovery at all. Restoring from an unverified backup or non-atomic DB overwrite turns a single-file corruption into loss of both original and backup.

### Constraints

- Single host with multiple processes execution
- Each DB file existence confirmed before startup in the deployment environment
- sqlite-vec extension loaded only into `rag.sqlite`
- Physical foreign keys, SQL JOINs, and distributed Transactions across DBs are not assumed
- A persistence failure in Workflow or EventBus is not treated as success with only a log entry
- operator-restore is currently a manual, operator-initiated CLI operation, not an automatic process at startup
- No migration mechanism exists; a Schema change requires recreating the whole DB (out of scope for this ADR)

### Assumptions

- Single host, multiple processes
- Limited concurrency
- Privileges granted only within each DB
- No external dependencies (SQLite is a local file)
- Backups are periodic file copies (`rotate_all_dbs()`), not continuously verified Snapshots
- Re-evaluate if assumptions no longer hold: multi-host configuration, distributed execution, integration with an external event store, migration to replicated storage

## Decision

### Recovery Category Glossary

- **initialization**: Creating a fresh, empty database or required schema when no valid database exists (`scripts/db/create_schema.py`; section 11 "DB Recreation Procedure").
- **schema-repair**: Correcting a missing or incompatible schema through an approved migration or initialization path (`apply_workflow_migrations()` / `_migrate()` in `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` sections 8a/8b); distinct from recreate-only paths.
- **logical-repair**: Correcting application-level inconsistencies while the SQLite file remains physically valid (`RagMaintenanceService.consistency()` in `scripts/agent/services/rag_maintenance_service.py`).
- **derived-data-rebuild**: Recreating indexes or other data that can be derived from an authoritative source (`RagMaintenanceService.rebuild_fts()` / `rebuild_vec()` in `scripts/agent/services/rag_maintenance_service.py`; `rag.sqlite`-only per Decision Detail #20).
- **physical-recovery**: Restoring usability after SQLite file corruption (`DbCondition.CORRUPTION` path in `scripts/db/recovery.py`; DbCondition StrEnum members: HEALTHY/CORRUPTION/LOCK_CONTENTION/PERMISSION_FAILURE/INVALID_FORMAT/UNKNOWN).
- **operator-restore**: Restoring a validated backup through an explicit operator-controlled procedure (Decision Detail #14/#17; Invariant INV-18).

### Recovery Policy Matrix

| Field | rag.sqlite | session.sqlite | workflow.sqlite | eventbus.sqlite |
|---|---|---|---|---|
| Persistence-domain identifier | rag | session | workflow | eventbus |
| Database file | rag.sqlite | session.sqlite | workflow.sqlite | eventbus.sqlite |
| System of record | documents, chunks, FTS5, Vector Index | sessions, messages, memories, memories_vec | tasks, attempts, artifacts, approvals, processed events | events, offsets, deliveries, DLQ state |
| Derived or rebuildable data | FTS5, Vector Index (from chunks) | memories_vec (from memories) | none | none |
| Owning component | RAG team | Agent team | Workflow team | EventBus team |
| Required service stop scope | RAG process | Agent process | Agent process (Workflow Engine runs in-process) | EventBus process |
| Supported diagnosis path | `_run_integrity_check()` + `check_rag_consistency()` | `_run_integrity_check()` | `_run_integrity_check()` | `_run_integrity_check()` |
| Supported recovery source | verified backup from operator for `documents`/`chunks`; FTS5 and Vector Index rebuilt from `chunks` (Decision Detail #20) | verified backup from operator | none (auto-restore prohibited per Decision Detail #20) | none (auto-restore prohibited per Decision Detail #20) |
| Automatic restore allowed or prohibited | allowed (per Decision Detail #20) | allowed (per Decision Detail #20) | prohibited (INV-18) | prohibited (INV-18) |
| Manual restore allowed or prohibited | allowed | allowed | operator intervention only | operator intervention only |
| Operator approval requirement | required for manual restore | required for manual restore | required (manual operation only) | required (manual operation only) |
| Backup retention requirement | regular file copy via `rotate_all_dbs()` | regular file copy via `rotate_all_dbs()` | archived via `rotate_all_dbs()` but no automated restoration | archived via `rotate_eventbus_db()` alongside other three databases |
| WAL checkpoint and backup consistency requirement | WAL mode enforced; checkpoint before backup | WAL mode enforced; checkpoint before backup | WAL mode enforced; checkpoint before backup | WAL mode enforced; checkpoint before backup |
| Physical integrity verification | independent validation before restore (INV-14) | independent validation before restore (INV-14) | independent validation before restore (INV-14) | independent validation before restore (INV-14) |
| Database-specific logical verification | `check_rag_consistency()` post-restore | connection test + message count check post-restore | `_recover_pending_approvals()` post-restore | offset/delivery reconciliation post-restore |
| Service restart condition | RAG process restart after restore | Agent process restart after restore | Agent process restart after restore | EventBus process restart after restore |
| Rollback condition | atomic replacement enables rollback if restore fails | atomic replacement enables rollback if restore fails | atomic replacement enables rollback if restore fails | atomic replacement enables rollback if restore fails |
| Audit requirement | Error/Audit records exclude row-level DB content (Security Consequences) | Error/Audit records exclude row-level DB content (Security Consequences) | Error/Audit records exclude row-level DB content (Security Consequences) | Error/Audit records exclude row-level DB content (Security Consequences) |
| Data-loss disclosure requirement | loss between backup point and failure time must be reported | loss between backup point and failure time must be reported | loss between backup point and failure time must be reported | loss between backup point and failure time must be reported |

Future persistence domains: default policy is fail-closed—no automatic restore until an approved architectural decision defines its recovery policy.

### Decision Details

1. `rag.sqlite`: canonical store for documents, chunks, FTS5, and the Vector Index. Owned by the RAG team.
2. `session.sqlite`: canonical store for Agent Sessions, Messages, and conversation state. Owned by the Agent team.
3. `workflow.sqlite`: canonical store for Tasks, Attempts, Approvals, Artifacts, and processed Events. Owned by the Workflow team.
4. `eventbus.sqlite`: canonical store for Events, Offsets, Delivery, and the DLQ. Owned by the EventBus team.
5. Reasons for DB separation: differences in write characteristics, lock contention, failure isolation, retention periods, recovery methods, and extension-loading scope.
6. Physical foreign keys, SQL JOINs, and distributed Transactions across DBs are not assumed.
7. Logical IDs such as Session ID, Workflow ID, and Event ID are used to relate data across DBs.
8. Cross-DB consistency is guaranteed by Events, idempotent processing, and state reconciliation.
9. sqlite-vec is loaded only into `rag.sqlite`.
10. Each DB defines its own Backup, Recovery, WAL Checkpoint, Health Check, and retention period.
11. RAG: rebuildability; Session: history retention; Workflow: resumption and auditing; EventBus: unprocessed Events and Offsets.
12. A persistence failure in Workflow or EventBus is not treated as success with only a log entry.
13. Prioritize avoiding lock contention, failure isolation, and simpler recovery over cross-DB Transaction difficulty.
14. Physical recovery must classify DB state (healthy/corruption/lock contention/permission failure/invalid format/unknown) before acting. Lock Contention and Permission Failure must not be classified as physical corruption.
15. A backup that is a restore candidate must have its own integrity verified independently before it replaces the target DB.
16. Restore stages candidate in temporary location, verifies it, then atomically replaces target DB per current design limits. Target DB must not be overwritten before candidate passes verification.
17. An Unknown or unclassifiable failure preserves the target DB and requires operator intervention instead of an automatic restore; `recover_corruption()` returns `action="preserved_operator_intervention_required"` for `DbCondition.UNKNOWN` and does not call `_restore_from_backup()`.
18. Dry Run must not move, replace, Truncate, delete, or rewrite the target DB for any classification result.
19. Corrupted DB is set aside as diagnostic copy before replacement. Retention/deletion left to operator manual judgment; no automatic deletion.
20. Recovery policy defined per persistence domain: `rag.sqlite` derived indexes (FTS5, Vector Index) rebuilt from canonical data (`chunks` table), with canonical tables restored from a verified backup; `session.sqlite` restored from backup; `workflow.sqlite` and `eventbus.sqlite` prohibit automatic restore—manual operator handling only (no silent re-initialization).

### Scope

- **Target components**: `DbConfig`, `SQLiteHelper`, `create_schema()`, `db/recovery.py`, `db/maintenance.py`
- **Target processes**: the Agent process, the ingester process, the EventBus process
- **Target data**: `rag.sqlite`, `session.sqlite`, `workflow.sqlite`, `eventbus.sqlite`
- **Target Environment Profile**: production (the only supported execution mode; ADR-004 applies one failure-handling policy to every environment)
- **Target APIs or processing paths**: `DbConfig.rag_db_path`, `DbConfig.session_db_path`, `DbConfig.workflow_db_path`, `DbConfig.eventbus_db_path`, `recover_corruption()`

### Out of Scope

- Details of individual DB schemas
- Detailed WAL Checkpoint parameters
- Implementation of Backup tools and scripts
- Automatic (unattended) triggering of operator-restore (currently operator-initiated only; automation requires a separate decision)
- Migration and Schema versioning strategy
- Continuous backup verification and replication design
- Monitoring and metrics design (handled by a separate ADR)

## Rationale

### 1. Primary Reason for Adoption — Operability

Because each DB can be initialized, connected, Checkpointed, and Recovered independently, the failure scope is localized. Corruption of one DB does not require initialization or recovery of the other DBs.

### 2. Second Reason for Adoption — Performance

When data with different update frequencies is in the same DB, WAL contention degrades performance. RAG is write-heavy and read-heavy, Session is append-heavy, Workflow is low-frequency but transaction-critical, and EventBus prioritizes real-time delivery. Because these characteristics differ, separation avoids lock contention.

### 3. Third Reason for Adoption — Data Integrity

Each DB can define its own Backup, Recovery, WAL Checkpoint, Health Check, and retention period. This accommodates the differences: RAG emphasizes rebuildability, Session history retention, Workflow resumption and auditing, and EventBus unprocessed Events and Offsets. Because restoring from an unverified backup or a non-Atomic overwrite turns an incident into the risk of losing both the corrupted original and a good backup, independent verification of the candidate and Atomic replacement are required.

### 4. Fourth Reason for Adoption — Correctness (Recovery Safety)

A recovery mechanism that cannot distinguish corruption from a temporary lock may run even against a DB that is not actually broken, so it is more dangerous than having no recovery mechanism at all. If the recovery policy for the `workflow`/`eventbus` domains were left undefined, there would be no action for operators to take when a failure actually occurs in those domains, so this ADR defines that policy explicitly.

## Alternatives Considered

This section is maintained in the companion document: [Alternatives Considered](adr_08_sqlite-4db-supporting-sections.md#alternatives-considered).

## Consequences

This section is maintained in the companion document: [Consequences](adr_08_sqlite-4db-supporting-sections.md#consequences).

## Invariants

- INV-01: `rag.sqlite` is the canonical store for documents, chunks, FTS5, and the Vector Index.
- INV-02: `session.sqlite` is the canonical store for Agent Sessions, Messages, and conversation state.
- INV-03: `workflow.sqlite` is the canonical store for Tasks, Attempts, Approvals, Artifacts, and processed Events.
- INV-04: `eventbus.sqlite` is the canonical store for Events, Offsets, Delivery, and the DLQ.
- INV-05: Physical foreign keys, SQL JOINs, and distributed Transactions across DBs are not assumed.
- INV-06: Logical IDs such as Session ID, Workflow ID, and Event ID are used to relate data across DBs.
- INV-07: Cross-DB consistency is guaranteed by Events, idempotent processing, and state reconciliation.
- INV-08: sqlite-vec is loaded only into `rag.sqlite`.
- INV-09: Each DB defines its own Backup, Recovery, WAL Checkpoint, Health Check, and retention period.
- INV-10: A persistence failure in Workflow or EventBus is not treated as success with only a log entry.
- INV-11: Corruption of one DB does not require initialization or recovery of the other DBs.
- INV-12: Cross-DB processing can be re-executed idempotently.
- INV-13: A physical-recovery action is chosen only after classifying the DB state (healthy / corruption / lock contention / permission failure / invalid format / unknown). Lock Contention and Permission Failure must not be classified as physical corruption.
- INV-14: A backup that is a restore candidate must be verified independently before it replaces the target DB.
- INV-15: The target DB must not be overwritten before the candidate passes verification. Replacement is done Atomically to the extent supported by the current design.
- INV-16: Dry Run must not move, replace, Truncate, delete, or rewrite the target DB for any classification result.
- INV-17: An Unknown or unclassifiable failure preserves the target DB and requires operator intervention instead of an automatic restore; `recover_corruption()` returns `action="preserved_operator_intervention_required"` for `DbCondition.UNKNOWN` and does not call `_restore_from_backup()`.
- INV-18: Automatic restore of `workflow.sqlite` and `eventbus.sqlite` is prohibited. Recovery is manual operator handling only, explicitly applying a policy different from `rag.sqlite` (rebuild) and `session.sqlite` (restore from backup).

## Failure Policy

This section is maintained in the companion document: [Failure Policy](adr_08_sqlite-4db-supporting-sections.md#failure-policy).

## Data Ownership and Persistence

This section is maintained in the companion document: [Data Ownership and Persistence](adr_08_sqlite-4db-supporting-sections.md#data-ownership-and-persistence).

## Verification

This section is maintained in the companion document: [Verification](adr_08_sqlite-4db-supporting-sections.md#verification).

## Known Deviations

- **Known Issue**: EVENTBUS-008 — tracked in governance_03 Part 1 (EventBus authentication model)

## Review Triggers

- The operational scale or concurrency changes significantly
- The deployment changes from a single host to multiple hosts or a distributed configuration
- Security or audit requirements change
- Performance targets or resource constraints change
- An external protocol or adopted library is changed or discontinued
- Failure history shows that the assumptions or the Failure Policy are no longer valid
- The reasons for rejecting an alternative no longer hold
- sqlite-vec supports FK constraints
- FTS5 supports standard DELETE
- A new shared configuration file becomes necessary
- Persistent storage moves to something other than files
- A migration mechanism or a replicated storage foundation is introduced
- The backup strategy changes from periodic file copies to another method
- An operator-restore trigger is proposed
- The recovery policy for `workflow.sqlite`/`eventbus.sqlite` changes from manual handling to an automated path

## Approval

### Required Reviewers

- Architecture Owner
- Affected Component Owner
- Security Reviewer: when there is a security impact
- Operations Reviewer: when operations, monitoring, or recovery are affected
- Data Owner: when data ownership, schema, or retention are affected

### Approval Record

- **Approved By**: Task-level approval decision (repository administrator; individual reviewer names are not recorded)
- **Approval Date**: Not recorded (individual approval dates are not recorded for a task-level approval decision)
- **Approval Reference**: `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard

This ADR's `Accepted` status uses the task-level approval decision defined by the governance document above as its acceptance evidence. No formal Approval Record with individual reviewer names and approval dates has been created.

## Related Documents

### Companion Document

- [ADR-008 Supporting Sections](adr_08_sqlite-4db-supporting-sections.md)

### Related ADRs

- ADR-002: Per-Process Configuration Ownership and Config Isolation
- ADR-005: Relationship Between RAG Canonical Data and Derived Indexes
- ADR-006: EventBus SQLite Persistence and SSE Delivery
- ADR-004: Failure Handling Policy Across Environments
- ADR-013: EventBus Authentication and Authorization

### Specifications

- [DB Architecture and Schema](../41_db/db_02_architecture_and_schema-schema-reference.md)
- [DB API and Operations — Recovery and Reference](../41_db/db_07_api_and_operations-recovery-and-reference.md)
- [Agent Session and DB Data Layer](../23_agent/agent_09_01_data-layer-session-db.md)
- [EventBus Persistence Schema and Replay](../24_eventbus/eventbus_06_persistence_schema_and_replay.md)
- [DLQ Offsets and Delivery Semantics](../24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md)

### Operations

- [Operations and Observability](../23_agent/agent_10_01_operations-and-observability-startup-and-health.md)
- [Manual Recovery: workflow.sqlite / eventbus.sqlite](../23_agent/agent_10_01_operations-and-observability-startup-and-health.md#manual-recovery-workflowsqlite-eventbussqlite)

### Known Issues

- [Issue and Uncertainty Management](../00_governance/governance_03_issue-and-uncertainty-management.md)

### Implementation References

- `scripts/db/config.py` (`DbConfig`)
- `scripts/db/helper.py` (`SQLiteHelper.__init__()`, `load_vec()`)
- `scripts/db/create_schema.py` (`create_schema()`)
- `scripts/db/rag_consistency.py` (`check_rag_consistency()`)
- `scripts/db/recovery.py` (`recover_corruption()`, `_classify_error()`, `_run_integrity_check()`, `_restore_from_backup()`)
- `rag.sqlite` (`documents`, `chunks`, `chunks_fts`, `chunks_vec`)
- `session.sqlite` (`sessions`, `messages`, `memories`, `memories_vec`)
- `workflow.sqlite` (`tasks`, `attempts`, `artifacts`, `approvals`)
- `eventbus.sqlite` (`events`)
- Tests — `tests/db/test_db_maintenance.py`, `tests/integration/test_session_recovery.py`

## Completion Checklist

Confirm the following before changing the ADR to Accepted.

- [x] The problem to solve is clear
- [x] The Decision is narrowed to one primary design decision
- [x] The Decision is stated in clear terms such as mandatory, prohibited, canonical, or Fallback conditions
- [x] The reasons for adoption are explained from perspectives other than the current implementation
- [x] Substantive alternatives and the reasons for rejecting them are recorded
- [x] Positive Consequences are recorded
- [x] Negative Consequences are recorded
- [x] The impact on Security has been evaluated
- [x] The impact on Operations, Monitoring, and Recovery has been evaluated
- [x] Verifiable Invariants are defined
- [x] Exceptions or out-of-scope cases are clear
- [x] Each Invariant has a corresponding Verification
- [x] Automatable verification does not rely only on Manual Review
- [x] The relationship with existing ADRs is recorded
- [x] The ADR does not contradict related Specifications
- [x] Discrepancies with the current implementation are registered as Known Issues
- [x] The Owner and required Reviewers are defined
- [x] Review Triggers are recorded
- [x] The ADR is registered in the ADR index and the Document Guides of related areas
