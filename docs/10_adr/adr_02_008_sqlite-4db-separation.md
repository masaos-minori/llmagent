---
title: "ADR-008: Separating SQLite into Four Databases"
area: governance
tags:
  - system
  - sqlite
  - database-separation
related:
  - adr_02_002_config-isolation.md
  - db_02_architecture_and_schema-schema-reference.md
  - db_07_api_and_operations-recovery-and-reference.md
  - agent_09_01_data-layer-session-db.md
  - eventbus_06_persistence_schema_and_replay.md
  - eventbus_05_dlq_offsets_and_delivery_semantics.md
  - agent_10_01_operations-and-observability-startup-and-health.md
  - governance_03_issue-and-uncertainty-management.md
  - adr_02_005_rag-source-derived-index-relationships.md
  - adr_02_006_eventbus-sqlite-persistence-and-sse-delivery.md
  - adr_02_004_environment-failure-handling-policy.md
  - adr_02_013_eventbus-authentication-authorization.md
  - db_03_architecture_and_schema-migration-and-scaling.md
  - governance_01_documentation-policy.md
---

# ADR-008: Separating SQLite into Four Databases

## Keywords

- sqlite
- database separation
- recovery policy
- backup

## Status

Accepted

## Summary

This ADR canonicalizes the decision to separate data with different update frequencies, failure scopes, retention periods, and recovery methods into four SQLite DBs. It defines the responsibilities of `rag.sqlite`, `session.sqlite`, `workflow.sqlite`, and `eventbus.sqlite`, and explains that cross-DB Transactions are not used and how consistency is ensured. It limits the scope of sqlite-vec and organizes the Backup, Recovery, and retention policy per DB. It also canonicalizes the safety boundary for recovery from physical corruption (failure classification, independent verification of backup candidates, Atomic replacement, a no-change guarantee for Dry Run, and a recovery policy per persistence domain).

mdq.sqlite, owned by mdq-mcp, is a separate derived store outside the four platform persistence domains of this ADR; its policy is recorded under "Out of Scope" and "Derived Stores Outside the Four Domains".

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
- `rag.sqlite` and `session.sqlite` have no migration mechanism and are recreated on a schema change; `workflow.sqlite` and `eventbus.sqlite` apply incremental additive migrations (`db_03` sections 8a and 8b). Migration design is out of scope for this ADR.

## Assumptions

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
| Owning component | RAG layer | Agent layer | Workflow engine (Agent layer) | EventBus service |
| Required service stop scope | Agent process, rag-pipeline-mcp, and any running ingester | Agent process | Agent process (Workflow Engine runs in-process) | EventBus process |
| Supported diagnosis path | `_run_integrity_check()` + `check_rag_consistency()` | `_run_integrity_check()` | none through `recover_corruption()` (returns `no_recovery_allowed` before any check) | none through `recover_corruption()` (returns `no_recovery_allowed` before any check) |
| Supported recovery source | verified backup from operator for `documents`/`chunks`; FTS5 and Vector Index rebuilt from `chunks` (Decision Detail #20) | verified backup from operator | none (auto-restore prohibited per Decision Detail #20) | none (auto-restore prohibited per Decision Detail #20) |
| Automatic restore allowed or prohibited | allowed only inside an operator-initiated `recover_corruption()` call (per Decision Detail #20) | allowed only inside an operator-initiated `recover_corruption()` call (per Decision Detail #20) | prohibited (INV-18) | prohibited (INV-18) |
| Manual restore allowed or prohibited | allowed | allowed | operator intervention only | operator intervention only |
| Operator approval requirement | required for manual restore | required for manual restore | required (manual operation only) | required (manual operation only) |
| Backup retention requirement | regular file copy via `rotate_all_dbs()` | regular file copy via `rotate_all_dbs()` | archived via `rotate_all_dbs()` but no automated restoration | archived via `rotate_eventbus_db()` alongside other three databases |
| WAL checkpoint and backup consistency requirement | WAL mode enforced; checkpoint before backup | WAL mode enforced; checkpoint before backup | WAL mode enforced; checkpoint before backup | WAL mode enforced; checkpoint before backup |
| Physical integrity verification | independent validation before restore (INV-14) | independent validation before restore (INV-14) | not applicable (no automated restore) | not applicable (no automated restore) |
| Database-specific logical verification | `check_rag_consistency()` post-restore | `check_session_consistency()` post-restore | none automated (manual operator handling; pending approvals are recovered by `_recover_pending_approvals()` at Agent startup) | none automated (manual operator handling) |
| Service restart condition | Agent process, rag-pipeline-mcp, and any ingester restart after restore | Agent process restart after restore | Agent process restart after restore | EventBus process restart after restore |
| Rollback condition | atomic replacement leaves the original intact if a restore fails | atomic replacement leaves the original intact if a restore fails | not applicable (no automated restore) | not applicable (no automated restore) |
| Audit requirement | Error/Audit records exclude row-level DB content (Security Consequences) | Error/Audit records exclude row-level DB content (Security Consequences) | Error/Audit records exclude row-level DB content (Security Consequences) | Error/Audit records exclude row-level DB content (Security Consequences) |
| Data-loss disclosure requirement | loss between backup point and failure time must be reported | loss between backup point and failure time must be reported | loss between backup point and failure time must be reported | loss between backup point and failure time must be reported |

Future persistence domains: default policy is fail-closed—no automatic restore until an approved architectural decision defines its recovery policy.

### Decision Details

1. `rag.sqlite`: canonical store for documents, chunks, FTS5, and the Vector Index. Owned by the RAG layer.
2. `session.sqlite`: canonical store for Agent Sessions, Messages, and conversation state. Owned by the Agent layer.
3. `workflow.sqlite`: canonical store for Tasks, Attempts, Approvals, Artifacts, and processed Events. Owned by the workflow engine in the Agent layer.
4. `eventbus.sqlite`: canonical store for Events, Offsets, Delivery, and the DLQ. Owned by the EventBus service.
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

### Derived Stores Outside the Four Domains

- mdq.sqlite is owned by mdq-mcp and holds only documents, chunks, an FTS5 index and indexing state derived from Markdown files under `allowed_dirs`. It is rebuilt from those files by `index_paths` and `refresh_index`, and it is not backed up or restored by `recover_corruption()` or `rotate_all_dbs()` (Explicit in code — `scripts/mcp_servers/mdq/db_schema.py`, `scripts/mcp_servers/mdq/indexer.py`, `scripts/db/recovery.py`, `scripts/db/rotation.py`).
- Adding a store that is a system of record for any data requires extending the Recovery Policy Matrix of this ADR before deployment.

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
- mdq.sqlite (a rebuildable derived index; see Derived Stores Outside the Four Domains)

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

### Alternative A: Single SQLite Database

#### Description

Manage all data in a single SQLite DB.

#### Advantages

- Simple structure
- JOINs across DBs are possible
- Transactions are easy

#### Disadvantages

- Performance degradation from WAL contention
- Failure propagation
- More complex backups
- Retention periods must be unified

#### Reason for Rejection

Operability and Performance require preventing lock contention and failure propagation.

#### Reconsideration Conditions

- Concurrency is very low
- JOINs across DBs become necessary

### Alternative B: No sqlite-vec extension

#### Description

Do not use sqlite-vec for vector search.

#### Advantages

- No dependency on sqlite-vec
- Can be managed with standard SQLite only

#### Disadvantages

- Inferior vector search performance
- KNN search cannot be achieved
- Lower embedding search accuracy

#### Reason for Rejection

Performance requires high-accuracy KNN search via sqlite-vec.

#### Reconsideration Conditions

- sqlite-vec becomes supported as a standard SQLite extension
- Vector search is no longer needed

### Alternative C: Cross-database Transactions

#### Description

Allow transactions across DBs.

#### Advantages

- Consistency is ensured
- Composite queries are possible

#### Disadvantages

- The implementation becomes complex
- Performance degrades
- The failure scope expands

#### Reason for Rejection

Operability requires keeping the failure scope localized.

#### Reconsideration Conditions

- Consistency across DBs becomes mandatory
- Composite transactions become necessary

### Alternative D: Treat every DB-open failure as corruption and always restore from backup

#### Description

Always treat a DB open failure as corruption and always restore from a backup.

#### Advantages

- Simple, with a single code path

#### Disadvantages

- A restore runs needlessly even for temporary Lock/Permission failures
- If the state was actually temporary, there is a risk of losing recent writes

#### Reason for Rejection

Rejected because it violates the classification invariant (Lock Contention and Permission Failure are not treated as Corruption).

#### Reconsideration Conditions

- Not applicable

### Alternative E: Leave workflow/eventbus unrecoverable by policy, permanently

#### Description

Treat `workflow.sqlite`/`eventbus.sqlite` as permanently unrecoverable.

#### Advantages

- No implementation work required

#### Disadvantages

- It becomes an unannounced permanent gap, and operators may mistakenly believe they can recover it like `rag`/`session`

#### Reason for Rejection

Whether to make them unrecoverable or to provide a manual operator recovery procedure should be an explicit decision; this ADR adopts the latter (manual operator recovery), so this alternative was rejected.

#### Reconsideration Conditions

- Not applicable

## Consequences

### Positive Consequences

- The independence of each DB is ensured
- The failure scope is localized
- Backups become easier
- Retention periods can be managed individually
- The scope of sqlite-vec is limited
- physical-recovery operations become auditable against an explicitly documented safety contract
- Backup corruption or a partial restore is detected before it replaces a live DB (even a corrupted one)

### Negative Consequences

- JOINs across DBs are not possible
- Composite transactions become necessary
- Backup scripting is required
- Incident response requires checking multiple DBs
- physical-recovery requires more steps (verifying, Staging, re-verifying, and Atomically replacing the candidate) than a simple single-copy implementation

### Operational Consequences

- Each DB's connection is confirmed at startup
- Configuration changes require restarting the owning process
- Incident response requires a recovery procedure per DB
- No automatic restore for `workflow.sqlite`/`eventbus.sqlite` physical corruption; operators must handle recovery manually
- Deletion of set-aside corrupted DB copies is left to the operator's manual judgment (no automatic deletion)

### Security Consequences

- Trust boundary: privileges granted only within each DB
- Secret handling: follow the principle of minimal exposure
- Error Messages and Audit Records of physical-recovery operations must not include row-level DB content (Paths and exception text only)

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

### Fail-Fast Conditions

- `rag.sqlite` connection failure (RAG functionality stops)
- `session.sqlite` connection failure (session functionality stops)
- `workflow.sqlite` connection failure (workflow functionality stops)
- `eventbus.sqlite` connection failure (event delivery stops)
- Backup restore candidate fails independent verification
- Integrity check fails in an Unknown or unclassifiable way

### Fail-Open or Degraded Conditions

Not applicable. physical-recovery is designed as a Fail-Closed domain. When in doubt, it preserves the state and requires operator action instead of acting automatically.

### Retry Policy

- No automatic retry of recovery
- operator-restore is a single, operator-initiated attempt; no automatic retry loop

### Fallback Policy

Not applicable (no Fallback exists: a failed restore or an unclassifiable failure preserves the target DB and requires operator action, and no other database or empty replacement substitutes for it)

## Data Ownership and Persistence

- **System of Record**: the four SQLite DBs (`rag.sqlite`, `session.sqlite`, `workflow.sqlite`, `eventbus.sqlite`)
- **Derived Data**: regenerable derived data (FTS5, Vector Index)
- **Ownership**: RAG layer, Agent layer, workflow engine, EventBus service
- **Persistence**: file system (the configured DB directory)
- **Transaction Boundary**: per DB
- **Recovery Source**: for `rag.sqlite`/`session.sqlite`, verified backup files supplied by the operator. `workflow.sqlite`/`eventbus.sqlite` are not subject to automatic restore and are handled manually by the operator.
- **Deletion Rule**: each DB is deleted independently. Deletion of corrupted DB copies set aside for diagnosis (`*_corrupt_<timestamp>.sqlite`) is left to the operator's manual judgment; no automatic deletion is performed.

## Verification

### Automated Tests

- **Test**: Each DB has its own schema creation and its own recovery target path
  - **Verifies**: INV-01, INV-02, INV-03, INV-04
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/db/test_create_schema.py::TestCreateSchemaWrapper::test_calls_all_four_in_order`, `tests/db/test_db_recovery.py::test_recover_workflow_uses_correct_db_path`, `tests/db/test_db_recovery.py::test_recover_eventbus_uses_correct_db_path`

- **Test**: sqlite-vec is not loaded into anything other than `rag.sqlite`
  - **Verifies**: INV-08
  - **Type**: Regression
  - **Blocking**: Yes
  - **Implementation**: `tests/db/test_sqlite_helper.py::TestSQLiteHelperTargetValidation::test_dbtarget_enum_member_resolves_to_value` (asserts the `rag` default only; the non-`rag` default is set in `SQLiteHelper.__init__()`)

- **Test**: Lock Contention and Permission Failure are not classified as physical corruption
  - **Verifies**: INV-13
  - **Type**: Regression
  - **Blocking**: Yes
  - **Implementation**: `tests/db/test_db_recovery.py::test_recover_lock_contention`, `tests/db/test_db_recovery.py::test_recover_permission_failure`, `tests/db/test_db_recovery.py::test_classify_error_lock_contention_via_sqlite_errorcode`

- **Test**: Dry Run does not vacuum, restore, or otherwise act on the target DB for the covered classification results
  - **Verifies**: INV-16
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/db/test_db_recovery.py::test_recover_dry_run_healthy`, `tests/db/test_db_recovery.py::test_recover_dry_run_workflow_prohibited`, `tests/db/test_db_recovery.py::test_recover_dry_run_eventbus_prohibited` (no test asserts byte-identity of a corrupt DB under Dry Run)

- **Test**: A `recover_corruption()` call specifying `workflow`/`eventbus` does not perform an automatic restore
  - **Verifies**: INV-18
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/db/test_db_recovery.py::test_recover_corrupt_workflow_prohibited`, `tests/db/test_db_recovery.py::test_recover_healthy_eventbus_prohibited`

- **Test**: A restore candidate with a corrupt or wrong-domain backup is rejected and the target DB is left untouched
  - **Verifies**: INV-14, INV-15
  - **Type**: Unit
  - **Blocking**: Yes
  - **Implementation**: `tests/db/test_db_recovery.py::test_recover_bad_backup`, `tests/db/test_db_recovery.py::test_recover_wrong_domain_backup_rejected`, `tests/db/test_db_recovery.py::test_recover_wrong_domain_backup_leaves_db_untouched`

- **Test**: An unclassifiable integrity-check failure preserves the target DB and requires operator intervention
  - **Verifies**: INV-17
  - **Type**: Unit
  - **Blocking**: Yes
  - **Implementation**: `tests/db/test_db_recovery.py::test_recover_unknown_preserved_operator_intervention_required`

### Startup Validation

- Each DB's connection is confirmed at startup
- Required DB paths are resolved from configuration before a connection is opened

### Deployment Validation

- Check each DB Schema before and after deployment
- The post-deployment consistency check passes

### Runtime Monitoring

- Health Check: connection state of each DB
- Metrics: WAL checkpoint counts per DB (`WalCheckpointCounts`)
- Logs: DB connection events, error events
- Alert conditions: `db_unavailable` (EventBus health endpoint)
- Degraded condition: failure of a dependency

### Manual Review

- DB Schema verification before deployment
- Manual recovery of `workflow.sqlite`/`eventbus.sqlite` (INV-18): `agent_10_01` Manual Recovery
- INV-05, INV-06, INV-07, INV-09, INV-10, INV-11, INV-12 describe design rules without a dedicated automated test

## Implementation Notes

- `SQLiteHelper` resolves one of four targets (`rag`, `session`, `workflow`, `eventbus`) to its configured file path and loads the sqlite-vec extension by default only for `rag`.
- `create_schema()` creates the schema of each database separately.
- `recover_corruption()` rejects `workflow` and `eventbus` with `no_recovery_allowed` before any integrity check, classifies the other targets through `_run_integrity_check()` and `_classify_error()`, and restores from a verified backup through `_restore_from_backup()`.
- `rotate_all_dbs()` archives each of the four databases.

See Implementation References for the current file/symbol list.

## Known Deviations

- **Known Issue**: EVENTBUS-017 — tracked in governance_03 Part 1 (INV-07)

## Review Triggers

- The operational scale or concurrency changes significantly
- The deployment changes from a single host to multiple hosts or a distributed configuration
- Security or audit requirements change
- Performance targets or resource constraints change
- An external protocol or adopted library is changed or discontinued
- Failure history shows that the assumptions or the Failure Policy are no longer valid
- The reasons for rejecting an alternative no longer hold
- sqlite-vec is needed in a database other than `rag.sqlite`
- A store that is a system of record is added outside the four domains, mdq.sqlite starts holding data that cannot be rebuilt, or two domains are merged (a recovery policy must then be defined for it)
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

- **Approved By**: Task-level approval decision (repository owner; individual reviewer names are not recorded)
- **Approval Date**: Not recorded (individual approval dates are not recorded for a task-level approval decision)
- **Approval Reference**: `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard
- **Decision Change (2026-10-08)**: Task-level approval decision (repository owner instruction) covering the Derived Stores section and the Recovery Policy Matrix; reviewer names are not recorded.

This ADR's `Accepted` status uses the task-level approval decision defined by the governance document above as its acceptance evidence. No formal Approval Record with individual reviewer names and approval dates has been created.

## Related ADRs

- ADR-002: Per-Process Configuration Ownership and Config Isolation
- ADR-005: Relationship Between RAG Canonical Data and Derived Indexes
- ADR-006: EventBus SQLite Persistence and SSE Delivery
- ADR-004: Failure Handling Policy Across Environments
- ADR-013: EventBus Authentication and Authorization

## Implementation References

- `scripts/db/config.py` (`DbConfig`)
- `scripts/db/helper.py` (`SQLiteHelper.__init__()`, `load_vec()`)
- `scripts/db/create_schema.py` (`create_schema()`)
- `scripts/db/rag_consistency.py` (`check_rag_consistency()`)
- `scripts/db/recovery.py` (`recover_corruption()`, `_classify_error()`, `_run_integrity_check()`, `_restore_from_backup()`)
- `scripts/db/rotation.py` (`rotate_all_dbs()`, `rotate_eventbus_db()`)
- `scripts/db/session_consistency.py` (`check_session_consistency()`)
- `rag.sqlite` (`documents`, `chunks`, `chunks_fts`, `chunks_vec`)
- `session.sqlite` (`sessions`, `messages`, `memories`, `memories_vec`)
- `workflow.sqlite` (`tasks`, `attempts`, `artifacts`, `approvals`)
- `eventbus.sqlite` (`events`)
- Tests — `tests/db/test_db_maintenance.py`, `tests/db/test_db_recovery.py`, `tests/db/test_sqlite_helper.py`, `tests/db/test_create_schema.py`, `tests/integration/test_session_recovery.py`

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
- [ ] Each Invariant has a corresponding Verification (INV-05, INV-06, INV-07, INV-09, INV-10, INV-11, INV-12 have no automated test)
- [x] Automatable verification does not rely only on Manual Review
- [x] The relationship with existing ADRs is recorded
- [x] The ADR does not contradict related Specifications
- [x] Discrepancies with the current implementation are registered as Known Issues
- [x] The Owner and required Reviewers are defined
- [x] Review Triggers are recorded
- [x] The ADR is registered in the ADR index and the Document Guides of related areas
