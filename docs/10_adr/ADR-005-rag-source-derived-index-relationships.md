---
title: "ADR-005: Relationship Between RAG Canonical Data and Derived Indexes"
area: governance
tags:
  - rag
  - index
  - canonical-source
related:
  - ADR-002-config-isolation.md
  - rag_04_dto-models-types.md
  - rag_05_07-rag-index-consistency-checks.md
  - rag_05_08-rag-mcp-internal-operations-direct-db-access.md
  - db_02_architecture_and_schema-schema-reference.md
  - rag_02_01_ingestion_pipeline-overview.md
  - rag_02_04_ingestion_pipeline-ingester.md
  - rag_02_02_ingestion_pipeline-crawler.md
  - rag_02_03_ingestion_pipeline-chunksplitter.md
  - rag_05_01-configuration-reference.md
  - ADR-004-environment-failure-handling-policy.md
---

# ADR-005: Relationship Between RAG Canonical Data and Derived Indexes

## Keywords

- rag
- source data
- derived index
- chunks
- fts

## Status

Accepted

## Summary

`documents` and `chunks` are defined as the canonical data for document and chunk content, and `chunks_fts` and `chunks_vec` as rebuildable derived indexes, making the criteria for consistency checks, deletion order, and recovery unambiguous.

## Context

### Problem

The RAG infrastructure has four data stores, `documents`, `chunks`, `chunks_fts`, and `chunks_vec`, each with a different role. There is a risk of mistakenly updating canonical data from a derived index, and of orphan records arising from an inconsistent deletion order. A design guarantee is also needed that the data can be rebuilt even if FTS5 or the Vector Engine is replaced.

### Constraints

- Multiple tables coexist in a single SQLite database
- `chunks_fts` is an FTS5 virtual table and does not support standard FK constraints
- `chunks_vec` is a sqlite-vec extension and does not support standard FK constraints
- Because `chunks_vec` has no FK, explicit deletion is required on delete
- Consistency checks run at startup and manually

## Assumptions

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
5. Canonical data is not updated from derived indexes. Direct INSERT/UPDATE into `chunks_fts` is prohibited outside the schema triggers and the `RagMaintenanceService` maintenance operations (rebuild through `/session rag-rebuild-fts`, per-URL reconciliation). (Explicit in code — `tools/check_chunks_fts_invariant.py` sanctioned paths)
6. Consistency checks detect differences using `chunks` as the reference.
7. When a document is deleted, the target `chunks_vec` rows are deleted first, then `documents` (CASCADE also deletes `chunks`, and the Trigger synchronizes `chunks_fts`).
8. Normal FTS5 synchronization and manual rebuilds use the same generation rule (`COALESCE(normalized_content, content)`).
9. Even if FTS5 or the Vector Engine is replaced, the indexes can be rebuilt from `documents` and `chunks`.
10. The following operational decisions are reflected in Operations:
    - `fts_gap > 0`: rebuild FTS5
    - `fts_orphan_count > 0`: rebuild FTS5
    - `orphan_vec_count > 0`: re-ingest the target documents
    - `vec != chunks`: investigate as an embedding or synchronization failure
11. The ingestion path (`delete_document_chain()`) and the MCP deletion path (`DocumentManager.delete_document()` of the rag_pipeline MCP server) apply the same deletion order (`chunks_vec` before `documents`). The MCP path issues the same statements itself rather than calling the shared helper.

### Scope

- **Target components**: `DocumentManager` (ingestion), `DocumentManager` (rag_pipeline MCP server), `RagMaintenanceService`, `check_rag_consistency()`
- **Target processes**: the Agent process and the ingester process
- **Target data**: the `documents` table, the `chunks` table, the `chunks_fts` virtual table, the `chunks_vec` virtual table
- **Target Environment Profile**: production (the only supported execution mode; ADR-004 applies one failure-handling policy to every environment)
- **Target APIs or processing paths**: `DocumentManager.delete_existing_document()`, `delete_document_chain()`, rag_pipeline `DocumentManager.delete_document()`, `RagMaintenanceService.reconcile_url()`, `RagMaintenanceService.rebuild_fts()`

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
- Secret handling: follow the principle of minimal exposure

## Invariants

- INV-01: Canonical data is not updated from derived indexes.
- INV-02: When a document is deleted, rows are deleted in the order `chunks_vec` → `documents`.
- INV-03: Normal FTS5 synchronization and manual rebuilds use the same generation rule.
- INV-04: Consistency checks detect differences using `chunks` as the reference.
- INV-05: The ingestion path and the MCP deletion path use the same deletion order (`chunks_vec` before `documents`).

## Failure Policy

### Fail-Fast Conditions

- Document deletion requires a `write_mode=True` connection: foreign keys are enforced only in write mode, and without them the `documents` delete does not cascade to `chunks` (Explicit in code — `scripts/db/helper.py` `SQLiteHelper.open()`)

### Fail-Open or Degraded Conditions

- The startup consistency check records each mismatch as a warning and does not abort startup; a timeout or an unexpected failure of the check skips it (Explicit in code — `scripts/agent/startup_validation.py`)
- The post-ingestion consistency check logs each issue as a warning and does not fail the ingestion run (Explicit in code — `scripts/rag/ingestion/document_manager.py` `DocumentManager.check_consistency()`)

### Retry Policy

Not applicable (this ADR defines no retry policy of its own)

### Fallback Policy

Not applicable (no Fallback exists: a mismatch is reported and repaired through the manual commands, never masked by switching to another index or data source)

## Data Ownership and Persistence

- **System of Record**: the `documents` table and the `chunks` table
- **Derived Data**: the `chunks_fts` virtual table and the `chunks_vec` virtual table
- **Ownership**: RAG team (owner of the canonical data)
- **Persistence**: SQLite file system
- **Transaction Boundary**: per document
- **Recovery Source**: canonical data (`documents` + `chunks`)
- **Deletion Rule**: `chunks_vec` → `documents` (`chunks` via CASCADE, `chunks_fts` via Trigger)

## Verification

### Automated Tests

- **Test**: No orphan `chunks_vec` rows remain after deletion
  - **Verifies**: INV-02
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/agent/services/test_rag_index_integrity.py::test_delete_document_chain_no_orphan_vec` (TEST-DESIGN3-03)

- **Test**: Deleting `documents` cascades the deletion to `chunks`
  - **Verifies**: INV-02
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/agent/services/test_rag_index_integrity.py::test_canonical_deletion_leaves_no_orphans_and_cascades_chunks` (TEST-DESIGN3-04)

- **Test**: The output of the FTS Trigger and of a manual rebuild match
  - **Verifies**: INV-03
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/rag/test_fts_sync.py::TestFtsTriggerSync::test_fts_trigger_and_manual_rebuild_use_same_text_selection_rule`

- **Test**: The consistency check detects Gaps and Orphans
  - **Verifies**: INV-04
  - **Type**: Regression
  - **Blocking**: Yes
  - **Implementation**: `tests/agent/services/test_rag_index_integrity.py::test_consistency_check_detects_fts_gap` (TEST-DESIGN3-05)

- **Test**: The MCP deletion path removes `chunks_vec` and cascades to `chunks`
  - **Verifies**: INV-05
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/mcp_servers/rag_pipeline/test_document_manager.py::TestDeleteDocument::test_cascades_to_chunks_and_removes_chunks_vec`

- **Test**: The deletion helper deletes `chunks_vec` before `documents`
  - **Verifies**: INV-02
  - **Type**: Unit
  - **Blocking**: Yes
  - **Implementation**: `tests/rag/ingestion/test_delete_chain.py::TestDeleteDocumentChain::test_delete_chunks_vec_before_documents`

- **Test**: A direct `chunks_fts` INSERT/UPDATE outside the sanctioned paths is detected
  - **Verifies**: INV-01
  - **Type**: Lint regression
  - **Blocking**: Yes
  - **Implementation**: `tests/test_chunks_fts_invariant_lint.py::test_violation_detected`

- **Test**: `chunks_fts` is derived from `chunks` (no direct INSERTs)
  - **Verifies**: INV-01
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/agent/services/test_rag_index_integrity.py::test_chunks_fts_is_trigger_synced` (TEST-DESIGN3-02)

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

## Implementation Notes

- Schema triggers on `chunks` keep `chunks_fts` synchronized and clean `chunks_vec` as a backstop for direct `chunks` deletes; `chunks_vec` rows are written explicitly by the ingestion pipeline.
- `delete_document_chain()` deletes the `chunks_vec` rows of a document, then the `documents` row; the cascade removes `chunks`. The rag_pipeline MCP server's `DocumentManager.delete_document()` issues the same two statements in the same order.
- `RagMaintenanceService.rebuild_fts()` regenerates `chunks_fts` with `COALESCE(normalized_content, content)`, the same rule as the triggers.
- `check_rag_consistency()` computes the counts and mismatches from `chunks`; the startup check and `/session rag-consistency` report them.

See Implementation References for the current file/symbol list.

This chapter is not a basis for design decisions.

## Known Deviations

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
- `sqlite-vec` supports FK constraints
- FTS5 supports standard DELETE
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

## Related ADRs

- ADR-002: Per-Process Configuration Ownership and Config Isolation
- ADR-004: Failure Handling Policy Across Environments

## Implementation References

- `scripts/rag/ingestion/document_manager.py` — `DocumentManager.delete_existing_document()`, `delete_document_chain()`
- `scripts/agent/services/rag_maintenance_service.py` — `RagMaintenanceService.reconcile_url()`, `RagMaintenanceService.rebuild_fts()`
- `scripts/db/rag_consistency.py` — `check_rag_consistency()`
- `scripts/mcp_servers/rag_pipeline/document_manager.py` — `DocumentManager.delete_document()`
- `scripts/db/schema_sql.py` — RAG schema and triggers
- `tools/check_chunks_fts_invariant.py` — direct `chunks_fts` write detection
- `documents` table — `url` UNIQUE, `title`, `lang`, `fetched_at`, `etag`, `last_modified`, `chunking_strategy`
- `chunks` table — `content`, `normalized_content`, `chunk_index`, `chunk_type`, `doc_id` FK
- `chunks_fts` virtual table — FTS5 trigger synchronization
- `chunks_vec` virtual table — sqlite-vec KNN index
- Triggers — `chunks_ai`, `chunks_au`, `chunks_ad`, `chunks_vec_ad`
- Tests — `tests/agent/services/test_rag_index_integrity.py` (TEST-DESIGN3-01 to 05)
- Tests — `tests/rag/ingestion/test_delete_chain.py`, `tests/rag/test_fts_sync.py`, `tests/mcp_servers/rag_pipeline/test_document_manager.py`, `tests/test_chunks_fts_invariant_lint.py`

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
