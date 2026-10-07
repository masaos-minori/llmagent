---
title: "ADR-008 Supporting Sections: Alternatives, Consequences, Failure Policy, Ownership and Verification"
area: governance
tags:
  - adr
  - governance
  - sqlite
  - alternatives
  - consequences
  - verification
related:
  - ADR-008-sqlite-4db-separation.md
  - adr_00_document-guide.md
---
# ADR-008 Supporting Sections: Alternatives, Consequences, Failure Policy, Ownership and Verification

## Purpose

Companion to `ADR-008-sqlite-4db-separation.md` (ADR-008: Separating SQLite into Four Databases). It holds supporting sections moved out of the ADR to keep the ADR within the documentation size limit. The ADR remains the authority for the decision; the section headings in the ADR link here. This document is not a basis for design decisions.

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
- **Ownership**: the RAG team, the Agent team, the Workflow team, the EventBus team
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
- A manual operator recovery procedure for `workflow.sqlite`/`eventbus.sqlite` (a concrete runbook) is not yet in place in this ADR and must be prepared separately as a Runbook
- INV-05, INV-06, INV-07, INV-09, INV-10, INV-11, INV-12 describe design rules without a dedicated automated test

## Known Deviations

Known Deviations are recorded in `ADR-008-sqlite-4db-separation.md`.

## Keywords

- adr
- supporting-sections
