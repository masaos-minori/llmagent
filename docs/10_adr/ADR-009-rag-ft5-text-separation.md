---
title: "ADR-009: Separating RAG FTS5 Search Text from LLM Presentation Text"
area: governance
tags:
  - rag
  - fts5
  - text-separation
decision_scope:
  - rag
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
supersedes: []
superseded_by: null
---

# ADR-009: Separating RAG FTS5 Search Text from LLM Presentation Text

## Keywords

rag
fts5
text separation
chunks

## Status

Accepted

## Summary

Normalized text for search quality is separated from the readable original text presented to the LLM, and the purpose of each is fixed as an invariant. `chunks.content` is defined as the canonical source of LLM-facing text, and `chunks.normalized_content` as derived data used only for the FTS5 Index. DESIGN-2 is transferred to this ADR.

## Context

### Problem

Japanese BM25 search requires normalization by morphological analysis, but the context presented to the LLM must use the original readable text. Managing both texts in the same field creates a trade-off between search quality and LLM comprehensibility.

### Constraints

- Multiple tables coexist in a single SQLite database
- `chunks_fts` is an FTS5 virtual table and does not support standard FK constraints
- Because the sqlite-vec extension is used, some standard FK constraints are restricted
- Different tokenizer approaches are used for Japanese and for English/code

### Assumptions

- Target environment: a single host, a single SQLite database
- Expected scale: limited concurrency
- Trust boundary: privileges are granted only within SQLite
- External dependencies: none (SQLite is a local file)
- Items to re-evaluate if the assumptions no longer hold: multi-DB configuration, distributed execution, integration with an external index store

## Decision

### Decision Details

1. `chunks.content` is the original readable text and the only text used for the LLM Context.
2. `chunks.normalized_content` is text normalized for search and is used only for the FTS5 Index.
3. FTS5 indexes `COALESCE(normalized_content, content)`.
4. Japanese text can use values normalized by Sudachi or similar tools.
5. For English, code, and text not subject to normalization, `normalized_content = NULL`, falling back to `content`.
6. `content` is kept even when normalization fails.
7. The original text is not restored from `normalized_content`.
8. The FTS Trigger and manual rebuilds use the same text-selection rule.
9. Changes to the Tokenizer or normalization method do not change the original LLM-facing text.
10. Document the behavior for cases where Japanese normalization is not performed, such as Markdown heading chunks.
11. AugmentStage outputs only `content` and does not output `normalized_content` to the LLM Context.

### Scope

- **Target components**: `ChunkJapaneseMixin`, `AugmentStage`, `RagRepository`, `RagMaintenanceService`
- **Target processes**: the Agent process and the ingester process
- **Target data**: the `chunks` table, the `chunks_fts` virtual table
- **Target Environment Profile**: production (the only supported execution mode; ADR-004 applies one failure-handling policy to every environment)
- **Target APIs or processing paths**: `AugmentStage.run()`, `_format_chunks()` (`scripts/rag/stages/augment.py`), `RagMaintenanceService.rebuild_fts()`

### Out of Scope

- Detailed configuration of individual Tokenizers
- Selection criteria for Sudachi dictionaries
- Selection criteria for the vector embedding model
- Details of the FTS5 tokenizer configuration
- Ranking algorithm for search results

## Rationale

### 1. Primary Reason for Adoption — Search Quality

Japanese BM25 search requires normalization by morphological analysis, and search accuracy drops if the original text is used as is. Indexing the normalized text in FTS5 improves search quality.

### 2. Second Reason for Adoption — LLM Usability

The context presented to the LLM must use the original readable text. Presenting normalized text to the LLM loses meaning and reduces the LLM's comprehension.

### 3. Third Reason for Adoption — Data Integrity

Keeping `content` even when normalization fails prevents data loss. Because the original text cannot be restored from `normalized_content`, `content` is always a reliable source of information.

Do not use "the current code is implemented this way" as the sole reason for adoption.

## Alternatives Considered

### Alternative A: Single Text Field

#### Description

Keep only `content` and use the same text for both FTS5 and the LLM.

#### Advantages

- Simple structure
- No data redundancy

#### Disadvantages

- Lower Japanese search accuracy
- A trade-off between normalization and readability

#### Reason for Rejection

Rejected to prioritize Search Quality and LLM Usability and satisfy both requirements.

#### Reconsideration Conditions

- Japanese search is no longer needed
- Normalization becomes unnecessary

### Alternative B: Normalize Both Fields

#### Description

Normalize `content` as well and use the same normalized text for FTS5 and the LLM.

#### Advantages

- Simple structure
- Data consistency is ensured

#### Disadvantages

- Lower LLM comprehension
- The original readable text is lost

#### Reason for Rejection

Rejected to prioritize LLM Usability and preserve LLM comprehension.

#### Reconsideration Conditions

- The LLM can understand normalized text
- The original readable text is no longer needed

### Alternative C: No COALESCE Fallback

#### Description

Skip FTS5 search when `normalized_content` is NULL.

#### Advantages

- Simple implementation
- No errors occur

#### Disadvantages

- English/code cannot be searched
- Search quality becomes uneven

#### Reason for Rejection

Rejected to prioritize Search Quality and enable search in all languages.

#### Reconsideration Conditions

- English/code search is no longer needed
- Normalization becomes mandatory

## Consequences

### Positive Consequences

- Japanese search accuracy improves
- The quality of context presented to the LLM improves
- Data loss on normalization failure is prevented
- Changes to the Tokenizer or normalization method do not affect the original LLM-facing text

### Negative Consequences

- Data redundancy increases
- The normalization pipeline adds complexity
- Debugging becomes harder because FTS5 and the LLM use different text

### Operational Consequences

- A consistency check runs at startup
- Repairing a mismatch requires a manual command
- Rebuild with `/session rag-rebuild-fts` or `ingester.py --force`

If not applicable, write "Not applicable".

### Security Consequences

- Trust boundary: privileges are granted only within SQLite
- Secret handling: follow the principle of minimal exposure

If not applicable, write "Not applicable".

## Invariants

- INV-01: `chunks.content` is the only text used for the LLM Context.
- INV-02: `chunks.normalized_content` is used only for the FTS5 Index.
- INV-03: FTS5 indexes `COALESCE(normalized_content, content)`.
- INV-04: For English, code, and text not subject to normalization, `normalized_content = NULL`, falling back to `content`.
- INV-05: `content` is kept even when normalization fails.
- INV-06: The original text is not restored from `normalized_content`.
- INV-07: The FTS Trigger and manual rebuilds use the same text-selection rule.
- INV-08: Changes to the Tokenizer or normalization method do not change the original LLM-facing text.
- INV-09: The behavior for cases where Japanese normalization is not performed, such as Markdown heading chunks, is documented.
- INV-10: AugmentStage outputs only `content` and does not output `normalized_content` to the LLM Context.

Behavior for INV-09: Markdown heading chunks (and other text not subject to Japanese normalization,
determined by the `_is_markdown_source()` branch) get `normalized_content = NULL` at ingestion
(`scripts/rag/ingestion/chunk_splitter.py::_build_text_triples()`). By the same
`COALESCE(normalized_content, content)` rule as the English and code chunks defined by INV-04, FTS5
falls back to `content`.

## Exceptions

None

## Failure Policy

### Fail-Fast Conditions

- When normalization fails (an error generating `normalized_content`)
- When FTS Trigger synchronization fails

### Fail-Open or Degraded Conditions

- None: ADR-004 defines a single common failure-handling policy, and no environment-specific downgrade to warnings exists

### Retry Policy

Not applicable (this ADR defines no retry policy of its own)

If not applicable, write "Not applicable".

### Fallback Policy

- Fallback target: normalization failure
- Fallback destination: fall back to `content`
- Conditions that prohibit Fallback: consistency-check mismatches
- Where Fallback reasons are recorded: audit log

If not applicable, write "Not applicable".

## Data Ownership and Persistence

- **System of Record**: the `chunks` table (`content` + `normalized_content`)
- **Derived Data**: the `chunks_fts` virtual table
- **Ownership**: RAG team (owner of the canonical data)
- **Persistence**: SQLite file system
- **Transaction Boundary**: per chunk
- **Recovery Source**: canonical data (`content` + `normalized_content`)
- **Deletion Rule**: `chunks_vec` → `documents` (`chunks` via CASCADE, `chunks_fts` via Trigger)

If not applicable, write "Not applicable".

## Verification

### Automated Tests

- **Test**: Normalized text is registered in FTS5 for Japanese
  - **Verifies**: INV-03
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/rag/test_fts_fallback.py::TestEnglishFtsFallback`

- **Test**: The original text is used for the LLM Context
  - **Verifies**: INV-01
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/rag/test_rag_pipeline.py::TestFormatChunksDesign2::test_content_appears_in_output`

- **Test**: For English and code, `content` is used for FTS5
  - **Verifies**: INV-04
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/rag/test_fts_fallback.py::TestCodeFtsFallback::test_code_search_returns_original_content`

- **Test**: The Index content is the same after an FTS rebuild
  - **Verifies**: INV-07
  - **Type**: Regression
  - **Blocking**: Yes
  - **Implementation**: `tests/rag/test_fts_sync.py::test_fts_trigger_and_manual_rebuild_use_same_text_selection_rule`

- **Test**: `normalized_content` does not leak into the RAG Context Block
  - **Verifies**: INV-02
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/rag/test_rag_pipeline.py::TestFormatChunksDesign2::test_normalized_content_does_not_appear`

- **Test**: AugmentStage outputs only `content`
  - **Verifies**: INV-10
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/rag/test_rag_pipeline_stage.py::TestAugmentStage::test_augment_stage_content_only_invariant`

### Startup Validation

- `check_rag_consistency()` runs at startup
- A warning is recorded when there is a mismatch

### Deployment Validation

- Check the consistency-check results before and after deployment
- The post-deployment consistency check passes

### Runtime Monitoring

- Health Check: consistency-check results
- Metrics: `fts_gap`, `fts_orphan_count`
- Logs: consistency-check events, error events
- Alert conditions: `fts_orphan_count > 0`
- Degraded condition: `fts_gap > 0`

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


- **Whitelist**: 
  - `scripts/agent/services/rag_maintenance_service.py::rebuild_fts()` — sanctioned `/session rag-rebuild-fts` command path
  - `scripts/db/schema_sql.py` — schema initialization SQL (executed once during setup, not runtime)
- **Excluded**: `scripts/mcp_servers/mdq/` — targets a separate mdq database, out of ADR-009 scope
- **Enforcement**: `tools/check_chunks_fts_invariant.py` detects direct INSERT/UPDATE (integrated into CI)
  - Whitelist: `scripts/agent/services/rag_maintenance_service.py::rebuild_fts()` (AST function-context detection), `scripts/db/schema_sql.py` (INSERTs inside CREATE TRIGGER blocks are excluded because they are not runtime writes), `scripts/mcp_servers/mdq/` (targets a separate DB)

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

- sqlite-vec supports FK constraints
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
- ADR-005: Relationship Between RAG Canonical Data and Derived Indexes
- ADR-004: Failure Handling Policy Across Environments

### Specifications

- [RAG Data Model](../21_rag/rag_04_dto-models-types.md) — data model definitions
- [RAG Consistency Checks](../21_rag/rag_05_07-rag-index-consistency-checks.md) — consistency-check procedure
- [RAG MCP Internal Operations](../21_rag/rag_05_08-rag-mcp-internal-operations-direct-db-access.md) — MCP internal operations
- [DB Schema Reference](../41_db/db_02_architecture_and_schema-schema-reference.md) — DB schema reference
- [Ingestion Pipeline Overview](../21_rag/rag_02_01_ingestion_pipeline-overview.md) — ingestion overview
- [Ingestion Pipeline - Ingester](../21_rag/rag_02_04_ingestion_pipeline-ingester.md) — Ingester details
- [Ingestion Pipeline - Crawler](../21_rag/rag_02_02_ingestion_pipeline-crawler.md) — Crawler details
- [Ingestion Pipeline - ChunkSplitter](../21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md) — ChunkSplitter details
- [Configuration Reference](../21_rag/rag_05_01-configuration-reference.md) — configuration reference

### Known Issues

- None

### Implementation References

- `scripts/rag/ingestion/document_manager.py` — `DocumentManager.delete_existing_document()`, `delete_document_chain()`
- `scripts/agent/services/rag_maintenance_service.py` — `RagMaintenanceService.reconcile_url()`, `RagMaintenanceService.rebuild_fts()`
- `scripts/db/rag_consistency.py` — `check_rag_consistency()`
- `scripts/shared/config_loader.py` — `ConfigLoader.restrict_to()`, `ConfigLoader.load()`
- `documents` table — `url` UNIQUE, `title`, `lang`, `fetched_at`, `etag`, `last_modified`, `chunking_strategy`
- `chunks` table — `content`, `normalized_content`, `chunk_index`, `chunk_type`, `doc_id` FK
- `chunks_fts` virtual table — FTS5 trigger synchronization
- `chunks_vec` virtual table — sqlite-vec KNN index
- Triggers — `chunks_ai`, `chunks_au`, `chunks_ad`, `chunks_vec_ad`
- Tests — `tests/agent/services/test_rag_index_integrity.py` (TEST-DESIGN3-01 to 05)
- Tests — `tests/rag/test_fts_fallback.py`

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
- [x] The Owner and required Reviewers are defined
- [x] Review Triggers are recorded
- [ ] The ADR is registered in the ADR index and the Document Guides of related areas
