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
- Configuration changes require restarting the owning DB
- Incident response requires a recovery procedure per DB
- No automatic restore for `workflow.sqlite`/`eventbus.sqlite` physical corruption; operators must handle recovery manually
- Deletion of set-aside corrupted DB copies is left to the operator's manual judgment (no automatic deletion)

### Security Consequences

- Trust boundary: privileges granted only within each DB
- Authentication and authorization: permission decisions based on configuration files
- Secret handling: follow the principle of minimal exposure
- Fail-Closed: abort startup when a configuration file is missing
- Error Messages and Audit Records of physical-recovery operations must not include row-level DB content (Paths and exception text only)
- Audit Log: record configuration loading events

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

- Fallback targets: none
- Fallback destination: none
- Conditions that prohibit Fallback: consistency-check mismatches
- Where Fallback reasons are recorded: audit log

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

- **Test**: Each DB can be initialized, connected, Checkpointed, and Recovered independently
  - **Verifies**: INV-01, INV-02, INV-03, INV-04
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: sqlite-vec is not loaded into anything other than `rag.sqlite`
  - **Verifies**: INV-08
  - **Type**: Regression
  - **Blocking**: Yes

- **Test**: Corruption of one DB does not require initialization or recovery of the other DBs
  - **Verifies**: INV-11
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: Cross-DB processing can be re-executed idempotently
  - **Verifies**: INV-12
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: The Lock Contention path is not classified as physical corruption
  - **Verifies**: INV-13
  - **Type**: Regression
  - **Blocking**: Yes

- **Test**: Dry Run keeps the target DB Byte-identical for every classification result
  - **Verifies**: INV-16
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: A `recover_corruption()` call specifying `workflow`/`eventbus` does not perform an automatic restore
  - **Verifies**: INV-18
  - **Type**: Integration
  - **Blocking**: Yes

### Startup Validation

- Each DB's connection is confirmed at startup
- Whether configuration files are valid (parseable TOML, required fields)

### Deployment Validation

- Check each DB Schema before and after deployment
- The post-deployment consistency check passes

### Runtime Monitoring

- Health Check: connection state of each DB
- Metrics: number of connections, WAL mode, and checkpoint count per DB
- Logs: DB connection events, error events
- Alert conditions: `db_unavailable`
- Degraded condition: failure of a dependency

### Manual Review

- DB Schema verification before deployment
- A manual operator recovery procedure for `workflow.sqlite`/`eventbus.sqlite` (a concrete runbook) is not yet in place in this ADR and must be prepared separately as a Runbook

Register any Invariant without Verification as an unverified item in an Issue.

## Known Deviations

Not applicable. Known Deviations are recorded in `ADR-008-sqlite-4db-separation.md`.

## Keywords

- adr
- supporting-sections
