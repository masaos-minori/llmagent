---
title: "ADR-005: Relationship Between RAG Canonical Data and Derived Indexes"
area: governance
tags:
  - rag
  - index
  - canonical-source
decision_scope:
  - rag
related:
  - ADR-002-config-isolation.md
supersedes: []
superseded_by: null
---

# ADR-005: Relationship Between RAG Canonical Data and Derived Indexes

## Keywords
<placeholder>

## Status

Accepted

The available Status values are as follows.

- `Proposed`: Under proposal; before review or approval
- `Accepted`: Adopted and effective as the current design
- `Rejected`: Considered but not adopted
- `Deprecated`: No longer recommended, but partially remaining
- `Superseded`: Replaced by a successor ADR

To change the decision after acceptance, do not edit the body directly; create a new ADR and change this ADR to Superseded.

## Summary

`documents` and `chunks` are defined as the canonical data for document and chunk content, and `chunks_fts` and `chunks_vec` as rebuildable derived indexes, making the criteria for consistency checks, deletion order, and recovery unambiguous. The DESIGN-3 decision is integrated into this ADR.

## Context

### Problem

The RAG infrastructure has four data stores, `documents`, `chunks`, `chunks_fts`, and `chunks_vec`, each with a different role. There is a risk of mistakenly updating canonical data from a derived index, and of orphan records arising from an inconsistent deletion order. A design guarantee is also needed that the data can be rebuilt even if FTS5 or the Vector Engine is replaced.

### Constraints

- Multiple tables coexist in a single SQLite database
- `chunks_fts` is an FTS5 virtual table and does not support standard FK constraints
- `chunks_vec` is a sqlite-vec extension and does not support standard FK constraints
- Because `chunks_vec` has no FK, explicit deletion is required on delete
- Consistency checks run at startup and manually

### Assumptions

- Target environment: a single host, a single SQLite database
- Expected scale: limited concurrency
- Trust boundary: privileges are granted only within SQLite
- External dependencies: none (SQLite is a local file)
- Items to re-evaluate if the assumptions no longer hold: multi-DB configuration, distributed execution, integration with an external index store

## Decision

### Decision Details

1. `documents` is the canonical data per document. It holds per-URL metadata and has a `url` UNIQUE constraint.
2. `chunks` is the canonical data for chunk content. It has `content`, `normalized_content`, `chunk_index`, and a `doc_id` FK (ON DELETE CASCADE).
3. `chunks_fts` is a derived full-text-search index generated from `chunks`. It is synchronized by AFTER INSERT/AFTER UPDATE/AFTER DELETE triggers.
4. `chunks_vec` is a derived vector-search index generated from `chunks`. Explicit INSERTs are performed during the ingestion pipeline, and explicit DELETEs on deletion.
5. Canonical data is not updated from derived indexes. Direct INSERT/UPDATE into `chunks_fts` is prohibited; only `/session rag-rebuild-fts` is permitted.
6. Consistency checks detect differences using `chunks` as the reference.
7. When a document is deleted, the target `chunks_vec` rows are deleted first, then `documents` (CASCADE also deletes `chunks`, and the Trigger synchronizes `chunks_fts`).
8. Normal FTS5 synchronization and manual rebuilds use the same generation rule (`COALESCE(normalized_content, content)`).
9. Even if FTS5 or the Vector Engine is replaced, the indexes can be rebuilt from `documents` and `chunks`.
10. The following operational decisions are reflected in Operations:
    - `fts_gap > 0`: rebuild FTS5
    - `fts_orphan_count > 0`: rebuild FTS5
    - `orphan_vec_count > 0`: re-ingest the target documents
    - `vec != chunks`: investigate as an embedding or synchronization failure
11. The ingestion path and the MCP deletion path use the same deletion helper or the same invariants.

### Scope

- **Target components**: `DocumentManager`, `RagMaintenanceService`, `check_rag_consistency()`
- **Target processes**: the Agent process and the ingester process
- **Target data**: the `documents` table, the `chunks` table, the `chunks_fts` virtual table, the `chunks_vec` virtual table
- **Target Environment Profile**: all environments (local/dev/production)
- **Target APIs or processing paths**: `DocumentManager.delete_existing_document()`, `DocumentManager.delete_document(url)`, `RagMaintenanceService.reconcile_url()`, `RagMaintenanceService.rebuild_fts()`

### Out of Scope

- Details of individual ingestion steps
- Selection criteria for the vector embedding model
- Details of the FTS5 tokenizer configuration
- Ranking algorithm for search results

## Rationale

### 1. Primary Reason for Adoption — Data Integrity

A clear separation between canonical and derived data ensures data consistency. It physically prevents the mistake of updating canonical data from a derived index.

### 2. Second Reason for Adoption — Operability

Defining the deletion-order invariant prevents orphan records. Because consistency checks and repair procedures are unified, operators are not left uncertain.

### 3. Third Reason for Adoption — Portability

Because the indexes can be rebuilt even if FTS5 or the Vector Engine is replaced, future technology migrations become easier.

Do not use "the current code is implemented this way" as the sole reason for adoption.

## Alternatives Considered

### Alternative A: Derived indexes as authoritative

#### Description

Make `chunks_fts` and `chunks_vec` the canonical data and `documents` and `chunks` the derived data.

#### Advantages

- Reverse lookup from the indexes is possible
- The original text might be regenerated from search results

#### Disadvantages

- The original text is lost when a search index breaks
- Complete data loss if both indexes break
- Consistency checks run in the opposite direction

#### Reason for Rejection

Rejected to prioritize Data Integrity and prevent data loss caused by search-index corruption.

#### Reconsideration Conditions

- Search indexes become a more accurate source of information than the original text
- Redundancy of both indexes is established

### Alternative B: No deletion order invariant

#### Description

Do not define a deletion order; each index cleans up independently.

#### Advantages

- Simple structure
- Few dependencies

#### Disadvantages

- Orphan records arise
- Risk of data loss
- Consistency checks become more complex

#### Reason for Rejection

Rejected to prioritize Data Integrity and prevent orphan records.

#### Reconsideration Conditions

- sqlite-vec supports FK constraints
- FTS5 supports standard DELETE

### Alternative C: Manual sync only

#### Description

Abolish automatic synchronization by triggers and manage everything manually.

#### Advantages

- Explicit control is possible
- No trigger overhead

#### Disadvantages

- Inconsistencies caused by human operational errors
- No real-time synchronization
- Increased operational burden

#### Reason for Rejection

Rejected to prioritize Operability, ensuring real-time synchronization and preventing human operational errors.

#### Reconsideration Conditions

- Trigger performance problems become serious
- Manual synchronization tools become sufficiently mature

## Consequences

### Positive Consequences

- A clear separation between canonical and derived data is ensured
- The deletion-order invariant prevents orphan records
- Consistency checks and repair procedures are unified
- Replacing FTS5 or the Vector Engine becomes easier
- The ingestion path and the MCP deletion path are unified under the same rules

### Negative Consequences

- Because `chunks_vec` has no FK, explicit deletion is required
- The consistency-check thresholds are strict (zero tolerance)
- Trigger overhead
- Cost at rebuild time

### Operational Consequences

- A consistency check runs at startup
- Repairing a mismatch requires a manual command
- Rebuild with `/session rag-rebuild-fts` or `ingester.py --force`

### Security Consequences

- Trust boundary: privileges are granted only within SQLite
- Authentication and authorization: permission decisions based on configuration files
- Secret handling: follow the principle of minimal exposure
- Fail-Closed: abort startup when a configuration file is missing
- Audit Log: record configuration loading events

If not applicable, write "Not applicable".

## Invariants

- INV-01: Canonical data is not updated from derived indexes.
- INV-02: When a document is deleted, rows are deleted in the order `chunks_vec` → `documents`.
- INV-03: Normal FTS5 synchronization and manual rebuilds use the same generation rule.
- INV-04: Consistency checks detect differences using `chunks` as the reference.
- INV-05: The ingestion path and the MCP deletion path use the same deletion helper.

## Exceptions

None

## Failure Policy

### Fail-Fast Conditions

- The consistency check finds `fts_orphan_count > 0` (risk of data loss)
- `write_mode=True` is not effective during deletion (FKs disabled)

### Fail-Open or Degraded Conditions

- In the local development environment, minor consistency mismatches are recorded as warnings

### Retry Policy

- Retry target: ingestion failures
- Retry count: `retry_policy.max_attempts` (default 3)
- Backoff: fixed interval (default 1 second)
- Errors not retried: consistency-check mismatches

### Fallback Policy

- Fallback targets: none
- Fallback destination: none
- Conditions that prohibit Fallback: consistency-check mismatches
- Where Fallback reasons are recorded: audit log

If not applicable, write "Not applicable".

## Data Ownership and Persistence

- **System of Record**: the `documents` table and the `chunks` table
- **Derived Data**: the `chunks_fts` virtual table and the `chunks_vec` virtual table
- **Ownership**: RAG team (owner of the canonical data)
- **Persistence**: SQLite file system
- **Transaction Boundary**: per document
- **Recovery Source**: canonical data (`documents` + `chunks`)
- **Deletion Rule**: `chunks_vec` → `documents` (`chunks` via CASCADE, `chunks_fts` via Trigger)

If not applicable, write "Not applicable".

## Verification

### Automated Tests

- **Test**: No orphan `chunks_vec` rows remain after deletion
  - **Verifies**: INV-02
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/test_rag_index_integrity.py::test_deletion_order_invariant` (TEST-DESIGN3-04)

- **Test**: Deleting `documents` cascades the deletion to `chunks`
  - **Verifies**: INV-02
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/test_rag_index_integrity.py::test_force_reingest_no_orphan_vectors` (TEST-DESIGN3-03)

- **Test**: The output of the FTS Trigger and of a manual rebuild match
  - **Verifies**: INV-03
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/test_rag_index_integrity.py::test_fts_rebuild_uses_cascade` (TEST-DESIGN3-01)

- **Test**: The consistency check detects Gaps and Orphans
  - **Verifies**: INV-04
  - **Type**: Regression
  - **Blocking**: Yes
  - **Implementation**: `tests/test_rag_index_integrity.py::test_consistency_check_detects_fts_gap` (TEST-DESIGN3-05)

- **Test**: `chunks_fts` is derived from `chunks` (no direct INSERTs)
  - **Verifies**: INV-01
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/test_rag_index_integrity.py::test_chunks_fts_is_derived_index` (TEST-DESIGN3-02)

### Startup Validation

- `check_rag_consistency()` runs at startup
- A warning is recorded when there is a mismatch

### Deployment Validation

- Check the consistency-check results before and after deployment
- The post-deployment consistency check passes

### Runtime Monitoring

- Health Check: consistency-check results
- Metrics: `fts_gap`, `fts_orphan_count`, `orphan_vec_count`
- Logs: consistency-check events, error events
- Alert conditions: `fts_orphan_count > 0`
- Degraded condition: `fts_gap > 0` or `orphan_vec_count > 0`

### Manual Review

- Investigation of consistency-check mismatches
- Consistency-check verification before deployment

Register any Invariant without Verification as an unverified item in an Issue.

## Implementation Notes

Briefly describe how the current implementation realizes the Decision.

See Related Documents > Implementation References for the current file/symbol list.

This chapter is not a basis for design decisions. List detailed APIs, Classes, and Functions in the Implementation References.

Do not record line numbers; reference by File Path and Symbol name.

## Known Deviations

Record any discrepancy between this ADR and the current implementation, configuration, tests, or documents.

- **Known Issue**: `sqlite-vec` lacks FK constraints — `chunks_vec` has no foreign key pointing to `chunks`. This is a known architectural limitation of `sqlite-vec` virtual tables. Consequence: Orphaned vector records can exist after document deletion if the explicit `chunks_vec` deletion step is missed. Mitigation: All deletion code paths enforce the `chunks_vec` → `documents` ordering invariant.
- **Type**: Architectural Limitation
- **Summary**: `chunks_vec` has no FK constraint
- **Impact**: An explicit deletion step is required
- **Resolution Target**: Cannot be relaxed until sqlite-vec supports FK constraints

Do not unconditionally align the ADR text with the current implementation; manage discrepancies as Known Issues.

## Review Triggers

Re-evaluate this ADR when any of the following conditions occurs.

- The operational scale or concurrency changes significantly
- The deployment changes from a single host to multiple hosts or a distributed configuration
- Security or audit requirements change
- Performance targets or resource constraints change
- An external protocol or adopted library is changed or discontinued
- Failure history shows that the assumptions or the Failure Policy are no longer valid
- The reasons for rejecting an alternative no longer hold

Add review conditions specific to this ADR.

- `sqlite-vec` supports FK constraints
- FTS5 supports standard DELETE
- A new shared configuration file becomes necessary
- Persistent storage moves to something other than files

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

### Related ADRs

- ADR-002: Per-Process Configuration Ownership and Config Isolation

### Specifications

- [RAG Data Model](../21_rag/rag_04_01_dto-models_data.md) — data model definitions
- [RAG Consistency Checks](../21_rag/rag_05_7-rag-index-consistency-checks.md) — consistency-check procedure
- [RAG MCP Internal Operations](../21_rag/rag_05_8-rag-mcp-internal-operations-direct-db-access.md) — MCP internal operations
- [DB Schema Reference](../41_db/db_02_db_architecture_and_schema-schema-reference.md) — DB schema reference
- [Ingestion Pipeline Overview](../21_rag/rag_02_01_ingestion_pipeline-overview.md) — ingestion overview
- [Ingestion Pipeline - Ingester](../21_rag/rag_02_04_ingestion_pipeline-ingester.md) — Ingester details
- [Ingestion Pipeline - Crawler](../21_rag/rag_02_02_ingestion_pipeline-crawler.md) — Crawler details
- [Ingestion Pipeline - ChunkSplitter](../21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md) — ChunkSplitter details
- [Configuration Reference](../21_rag/rag_05_1-configuration-reference.md) — configuration reference

### Operations

<!-- TODO: Document 'rag_05_6-rag-operations.md' was deleted -->

### Known Issues

- None

### Implementation References

- `scripts/rag/ingestion/document_manager.py` — `DocumentManager.delete_existing_document()`, `delete_document_chain()`
- `scripts/agent/services/rag_maintenance_service.py` — `RagMaintenanceService.reconcile_url()`, `RagMaintenanceService.rebuild_fts()`
- `scripts/db/maintenance.py` — `check_rag_consistency()`
- `scripts/shared/config_loader.py` — `ConfigLoader.restrict_to()`, `ConfigLoader.load()`
- `documents` table — `url` UNIQUE, `title`, `lang`, `fetched_at`, `etag`, `last_modified`, `chunking_strategy`
- `chunks` table — `content`, `normalized_content`, `chunk_index`, `chunk_type`, `doc_id` FK
- `chunks_fts` virtual table — FTS5 trigger synchronization
- `chunks_vec` virtual table — sqlite-vec KNN index
- Triggers — `chunks_ai`, `chunks_au`, `chunks_ad`
- Tests — `tests/test_rag_index_integrity.py` (TEST-DESIGN3-01 to 05)
- Tests — `tests/test_fts_fallback.py`

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
- [x] Migration, or the reason no migration is needed, is recorded
- [x] The relationship with existing ADRs is recorded
- [x] The ADR does not contradict related Specifications
- [ ] Discrepancies with the current implementation are registered as Known Issues
- [ ] The Owner and required Reviewers are defined
- [ ] Review Triggers are recorded
- [ ] The ADR is registered in the ADR index and the Document Guides of related areas
