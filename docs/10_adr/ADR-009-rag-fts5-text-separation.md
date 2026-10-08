---
title: "ADR-009: Separating RAG FTS5 Search Text from LLM Presentation Text"
area: governance
tags:
  - rag
  - fts5
  - text-separation
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
  - ADR-005-rag-source-derived-index-relationships.md
  - ADR-004-environment-failure-handling-policy.md
---

# ADR-009: Separating RAG FTS5 Search Text from LLM Presentation Text

## Keywords

- rag
- fts5
- text separation
- chunks

## Status

Accepted

## Summary

Normalized text for search quality is separated from the readable original text presented to the LLM, and the purpose of each is fixed as an invariant. `chunks.content` is defined as the canonical source of LLM-facing text, and `chunks.normalized_content` as derived data used only for the FTS5 Index.

## Context

### Problem

Japanese BM25 search requires normalization by morphological analysis, but the context presented to the LLM must use the original readable text. Managing both texts in the same field creates a trade-off between search quality and LLM comprehensibility.

### Constraints

- `chunks_fts` is an external-content FTS5 table over `chunks` with a single indexed column, so what it indexes is decided by the text written to it, not by a separate column
- Japanese normalization (Sudachi) runs at chunking time and its result is stored in `chunks.normalized_content`
- Different tokenizer approaches are used for Japanese and for English/code
- The embedding of a chunk is computed from `content`, not from `normalized_content`

## Assumptions

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
6. A normalization failure never alters `content`: normalized text never replaces it, and a source file whose Japanese normalization fails produces no chunks.
7. The original text is not restored from `normalized_content`.
8. The FTS Trigger and manual rebuilds use the same text-selection rule.
9. Changes to the Tokenizer or normalization method do not change the original LLM-facing text.
10. Text that is not Japanese-normalized, including Markdown heading chunks, has `normalized_content = NULL` and is indexed by `content`.
11. AugmentStage outputs only `content` and does not output `normalized_content` to the LLM Context.
12. A sentence whose normalization succeeds but yields empty text keeps its original text in `content`, with `normalized_content = NULL`.

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

Keeping `content` as a separate, never-replaced field guarantees that every stored chunk carries its original text. When normalization fails for a file, the file is skipped as a whole rather than indexed with altered or partial text, so a stored chunk is never a lossy copy. Because the original text cannot be restored from `normalized_content`, `content` is always a reliable source of information.

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
- A stored chunk never loses its original text to normalization; a file whose normalization fails is skipped and must be re-chunked after the cause is fixed
- Changes to the Tokenizer or normalization method do not affect the original LLM-facing text

### Negative Consequences

- Data redundancy increases
- The normalization pipeline adds complexity
- Debugging becomes harder because FTS5 and the LLM use different text

### Operational Consequences

- `/session rag-rebuild-fts` regenerates `chunks_fts` from the stored `content` and `normalized_content`; it does not recompute normalization
- Changing the normalization method requires re-chunking the sources so that `normalized_content` is regenerated

### Security Consequences

- Trust boundary: privileges are granted only within SQLite
- Secret handling: follow the principle of minimal exposure

## Invariants

- INV-01: `chunks.content` is the only text used for the LLM Context.
- INV-02: `chunks.normalized_content` is used only for the FTS5 Index.
- INV-03: FTS5 indexes `COALESCE(normalized_content, content)`.
- INV-04: For English, code, and text not subject to normalization, `normalized_content = NULL`, falling back to `content`.
- INV-05: A normalization failure never alters `content`: normalized text never replaces it, and a source file whose Japanese normalization fails produces no chunks.
- INV-06: The original text is not restored from `normalized_content`.
- INV-07: The FTS Trigger and manual rebuilds use the same text-selection rule.
- INV-08: Changes to the Tokenizer or normalization method do not change the original LLM-facing text.
- INV-09: Text that is not Japanese-normalized, including Markdown heading chunks, has `normalized_content = NULL` and is indexed by `content`.
- INV-10: AugmentStage outputs only `content` and does not output `normalized_content` to the LLM Context.
- INV-11: A sentence whose normalized text is empty keeps its original text in `content` with `normalized_content = NULL`.

## Failure Policy

### Fail-Fast Conditions

- When Japanese normalization fails (`TokenizationError`), chunking of that source file stops and no chunk is written for it; the failure is logged and the remaining source files are still processed (Explicit in code — `scripts/rag/ingestion/chunk_japanese.py` `_normalize_ja_sentence()`, `scripts/rag/ingestion/chunk_splitter.py` `ChunkSplitter.process_all()`)
- When an FTS Trigger fails, the statement on `chunks` that fired it fails with it (SQLite trigger semantics)

### Fail-Open or Degraded Conditions

- None: ADR-004 defines a single common failure-handling policy, and no environment-specific downgrade to warnings exists

### Retry Policy

Not applicable (this ADR defines no retry policy of its own)

### Fallback Policy

Not applicable (no failure Fallback exists). The `COALESCE(normalized_content, content)` rule is a data-selection rule for chunks that have no `normalized_content`, not a Fallback for a failed normalization; a failed normalization never produces a chunk (see Fail-Fast Conditions).

## Data Ownership and Persistence

- **System of Record**: the `chunks` table (`content` + `normalized_content`)
- **Derived Data**: the `chunks_fts` virtual table
- **Ownership**: RAG team (owner of the canonical data)
- **Persistence**: SQLite file system
- **Transaction Boundary**: per chunk
- **Recovery Source**: the `chunks` table (`content` + `normalized_content`); `chunks_fts` is rebuilt from it
- **Deletion Rule**: deleting a document removes its `chunks` rows by CASCADE and the matching `chunks_fts` rows by Trigger; the deletion order is defined by ADR-005

## Verification

### Automated Tests

- **Test**: Normalized text is registered in FTS5 for Japanese
  - **Verifies**: INV-03
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/rag/test_fts_japanese.py::TestChunksAiTrigger::test_ja_normalized_content_indexed_in_fts`, `tests/rag/test_fts_japanese.py::TestChunksAiTrigger::test_trigger_uses_coalesce_order`

- **Test**: The original text is used for the LLM Context
  - **Verifies**: INV-01
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/rag/test_rag_pipeline.py::TestFormatChunksDesign2::test_content_appears_in_output`

- **Test**: For English and code, `content` is used for FTS5
  - **Verifies**: INV-04
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/rag/test_fts_fallback.py::TestCodeFtsFallback::test_code_search_returns_original_content`, `tests/rag/test_fts_japanese.py::TestChunksAiTrigger::test_ja_raw_content_fallback_when_normalized_null`

- **Test**: The Index content is the same after an FTS rebuild
  - **Verifies**: INV-07
  - **Type**: Regression
  - **Blocking**: Yes
  - **Implementation**: `tests/rag/test_fts_sync.py::TestFtsTriggerSync::test_fts_trigger_and_manual_rebuild_use_same_text_selection_rule`, `tests/rag/test_fts_sync.py::TestFtsTriggerSync::test_rebuild_fts_preserves_normalized_content_semantics`, `tests/agent/services/test_rag_index_integrity.py::test_rebuild_fts_uses_coalesce`

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
- INV-05, INV-06, INV-08, INV-09, INV-11 have no dedicated automated test

## Implementation Notes

- `ChunkSplitter` produces `(chunk_type, content, normalized_content)` triples: Japanese text is split and normalized by `ChunkJapaneseMixin`; English text, code blocks, and Markdown heading chunks (selected by `_is_markdown_source()`) get an empty `normalized_content`.
- The ingestion transaction stores an empty `normalized_content` as NULL in `chunks`; the chunk embedding is computed from `content`.
- The `chunks_ai`, `chunks_au`, and `chunks_ad` triggers and `RagMaintenanceService.rebuild_fts()` index `COALESCE(normalized_content, content)`.
- `AugmentStage` formats only `content` of each reranked hit into the RAG context block.

See Implementation References for the current file/symbol list.

This chapter is not a basis for design decisions.

## Known Deviations

- **Known Issue**: RAG-002 — tracked in governance_03 Part 1 (Japanese sentences with empty normalized text are dropped together with their original text; violates INV-11)

## Review Triggers

Re-evaluate this ADR when any of the following conditions occurs.

- The operational scale or concurrency changes significantly
- The deployment changes from a single host to multiple hosts or a distributed configuration
- Security or audit requirements change
- Performance targets or resource constraints change
- An external protocol or adopted library is changed or discontinued
- Failure history shows that the assumptions or the Failure Policy are no longer valid
- The reasons for rejecting an alternative no longer hold
- The Japanese normalization method or the Sudachi dictionary changes
- The FTS5 tokenizer or the indexed column set of `chunks_fts` changes
- The LLM context starts to use any text other than `chunks.content`

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
- **Decision Change (2026-10-08)**: The addition of Decision Details #12 and INV-11 and the narrowed data-integrity rationale were approved as a task-level approval decision (repository administrator instruction); individual reviewer names are not recorded.

This ADR's `Accepted` status uses the task-level approval decision defined by the governance document above as its acceptance evidence. No formal Approval Record with individual reviewer names and approval dates has been created.

## Related ADRs

- ADR-002: Per-Process Configuration Ownership and Config Isolation
- ADR-005: Relationship Between RAG Canonical Data and Derived Indexes
- ADR-004: Failure Handling Policy Across Environments

## Implementation References

- `scripts/rag/ingestion/chunk_splitter.py` — `ChunkSplitter._build_text_triples()`, `ChunkSplitter._is_markdown_source()`, `ChunkSplitter._build_chunk_payload()`
- `scripts/rag/ingestion/chunk_japanese.py` — `ChunkJapaneseMixin._chunk_japanese()`, `ChunkJapaneseMixin._normalize_ja_sentence()`
- `scripts/rag/ingestion/embedding.py` — `embed_and_store()` (embeds `content`)
- `scripts/rag/ingestion/transaction_commit.py` — `TransactionManager._insert_chunks_batch()`
- `scripts/rag/stages/augment.py` — `_format_chunks()`, `AugmentStage.run()`
- `scripts/agent/services/rag_maintenance_service.py` — `RagMaintenanceService.rebuild_fts()`
- `scripts/db/schema_sql.py` — `chunks_fts` and the `chunks_ai`, `chunks_au`, `chunks_ad` triggers
- `tools/check_chunks_fts_invariant.py` — direct `chunks_fts` write detection
- `chunks` table — `content`, `normalized_content`
- `chunks_fts` virtual table — FTS5 index over `COALESCE(normalized_content, content)`
- Tests — `tests/rag/test_fts_sync.py`, `tests/rag/test_fts_japanese.py`, `tests/rag/test_fts_fallback.py`, `tests/rag/test_rag_pipeline.py`, `tests/rag/test_rag_pipeline_stage.py`, `tests/rag/ingestion/test_chunk_splitter.py`, `tests/agent/services/test_rag_index_integrity.py`

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
- [ ] Each Invariant has a corresponding Verification (INV-05, INV-06, INV-08, INV-09, INV-11 have no automated test)
- [x] Automatable verification does not rely only on Manual Review
- [x] The relationship with existing ADRs is recorded
- [x] The ADR does not contradict related Specifications
- [x] Discrepancies with the current implementation are registered as Known Issues (RAG-002)
- [x] The Owner and required Reviewers are defined
- [x] Review Triggers are recorded
- [x] The ADR is registered in the ADR index and the Document Guides of related areas
