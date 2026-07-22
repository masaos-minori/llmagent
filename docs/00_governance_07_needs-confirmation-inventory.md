## Purpose

This document provides a centralized inventory of all "Needs confirmation" items found across the design documentation set. It makes unconfirmed statements trackable and actionable, preventing them from being silently accepted as facts.

## Inventory Entry Fields

Each entry must contain the following eleven fields:

1. **ID** — Unique identifier in format `NC-{NNN}` (e.g., NC-001)
2. **Source File** — Markdown file containing the item
3. **Section** — Section or subsection where the item appears
4. **Line Number** — Approximate line number in the source file
5. **Question** — What needs to be confirmed
6. **Evidence** — What evidence exists for the current statement
7. **Impact** — Consequences if the statement is wrong
8. **Required Action** — What needs to happen to resolve this item
9. **Status** — Current lifecycle state of the item
10. **Assigned To** — Person responsible for resolution
11. **Last Reviewed** — Date last reviewed

## Status Values

- **open** — Item acknowledged but not yet investigated
- **investigating** — Investigation underway
- **resolved** — Item resolved through code change or documentation update
- **deferred** — Resolution postponed to future work
- **wontfix** — Item will not be addressed

## Extraction Process

To extract "Needs confirmation" items from source documents:

1. Search all Markdown files under `docs/` for the phrase "Needs confirmation"
2. For each match, identify the surrounding context (section, paragraph)
3. Populate all eleven required fields based on the context
4. Add the entry to this document with a sequential ID
5. Never modify the source documents during extraction

## Inventory Items

### NC-001

- **Source File**: `05_agent_05_llm-and-streaming-part1.md`
- **Section**: §Error Classification
- **Line Number**: ~176
- **Question**: Are `UTF8_PARTIAL_DECODE_ERROR` and `PREMATURE_EOF` distinct error types?
- **Evidence**: Both appear in error classification without clear distinction
- **Impact**: Incorrect error handling could cause silent failures
- **Required Action**: Verify error type definitions in LLMClient implementation
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-07-22

### NC-002

- **Source File**: `03_rag_04_04_dto-models_config.md`
- **Section**: §ResultSource field definition
- **Line Number**: ~92
- **Question**: Is the unused ResultSource definition intentional for future migration or deletion oversight?
- **Evidence**: Field exists but has no current usage path in codebase
- **Impact**: Dead code may cause confusion; potential memory overhead
- **Required Action**: Confirm with original author or check git history
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-07-22

### NC-003

- **Source File**: `03_rag_02_06_ingestion_pipeline-supporting-components.md`
- **Section**: §ETagManager behavior
- **Line Number**: ~42
- **Question**: Does ETagManager correctly handle existing document re-fetching?
- **Evidence**: DocumentManager passes fixed value `0` instead of `existing_doc_id` for ETag updates
- **Impact**: Existing document ETag updates may not function as intended
- **Required Action**: Trace ETag update flow through DocumentManager
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-07-22

### NC-004

- **Source File**: `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- **Section**: §knn_search method
- **Line Number**: ~66
- **Question**: Is the distance metric cosine or L2 — cannot determine from this module alone
- **Evidence**: Code comment says "Negate distance" but does not specify metric type
- **Impact**: Distance metric affects search quality and ranking
- **Required Action**: Check memories_vec table definition for metric specification
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-07-22

### NC-005

- **Source File**: `03_rag_04_03_dto-models_audit.md`
- **Section**: §DTO purpose analysis
- **Line Number**: ~40
- **Question**: Are RagAuditRequest/RagAuditResponse dead code or forward-looking definitions?
- **Evidence**: DTOs exist but are not used by any current audit/approval workflow
- **Impact**: Dead code creates maintenance burden; missing code causes broken workflows
- **Required Action**: Check git history for intent; verify no pending feature uses these
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-07-22

### NC-006

- **Source File**: `03_rag_03_06_query_pipeline-helpers-and-cache-part2.md`
- **Section**: §result_source field analysis
- **Line Number**: ~120
- **Question**: Is result_source field intended for future use or should it be removed?
- **Evidence**: No code path sets PipelineRunResult.result_source; only SearchDiagnostics uses dataclasses.replace()
- **Impact**: Dead field may confuse developers; potential hidden functionality
- **Required Action**: Check git history for original intent; verify no plugin sets this field
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-07-22

### NC-007

- **Source File**: `05_agent_04_03_state-and-persistence-platform-databases.md`
- **Section**: §Archive memory operation
- **Line Number**: ~54
- **Question**: What is the read path for archived memory?
- **Evidence**: Archive operation exists but read path details unclear
- **Impact**: Archived data may be inaccessible after write
- **Required Action**: Trace archive write and find corresponding read path
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-07-22

### NC-008

- **Source File**: `05_agent_04_03_state-and-persistence-platform-databases.md`
- **Section**: §request_approval workflow_id parameter
- **Line Number**: ~109-110
- **Question**: How is workflow_id used in multi-workflow scenario?
- **Evidence**: Parameter appears to distinguish multiple workflows but purpose unclear
- **Impact**: Multi-workflow routing may fail silently
- **Required Action**: Trace workflow_id usage in request_approval call chain
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-07-22

### NC-009

- **Source File**: `03_rag_04_05_dto-types.md`
- **Section**: §RagPipelineConfig.run field
- **Line Number**: ~48
- **Question**: Who explicitly sets the run field?
- **Evidence**: Field exists but setting mechanism unknown
- **Impact**: Run field may never be set, causing incorrect pipeline state
- **Required Action**: Search codebase for explicit run field assignment
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-07-22

### NC-010

- **Source File**: `03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md`
- **Section**: §gen_rag_reference.py output target
- **Line Number**: ~86
- **Question**: Should gen_rag_reference.py OPS_DOC constant be updated to point to split files?
- **Evidence**: Tool outputs to non-existent docs/03_rag_05_configuration_and_operations.md
- **Impact**: Auto-generated content becomes stale; manual tracking required
- **Required Action**: Determine if tool should be updated or if manual process is acceptable
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-07-22

### NC-011

- **Source File**: `03_rag_02_04_ingestion_pipeline-ingester-part2.md`
- **Section**: §docstring accuracy
- **Line Number**: ~49
- **Question**: Is the docstring reference to common.toml::embedding_dims intentional legacy text?
- **Evidence**: Docstring references non-existent common.toml; actual config comes from ingester.toml
- **Impact**: Misleading documentation may cause incorrect assumptions
- **Required Action**: Confirm with original author that docstring is outdated
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-07-22

### NC-012

- **Source File**: `05_agent_10_05_operations-and-observability-monitoring.md`
- **Section**: §DiagnosticStore loop_guard_hint method
- **Line Number**: ~92
- **Question**: Is loop_guard_hint kind name ever generated in practice?
- **Evidence**: Method defined but no caller found in scripts/agent/ tree
- **Impact**: Dead method may indicate incomplete feature or unnecessary code
- **Required Action**: Search entire codebase including tests for loop_guard_hint usage
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-07-22

### NC-013

- **Source File**: `05_agent_10_05_operations-and-observability-monitoring.md`
- **Section**: §DiagnosticStore fetch_by_kind / fetch_all methods
- **Line Number**: ~93
- **Question**: Are fetch_by_kind/fetch_all methods intended for CLI/API use?
- **Evidence**: Methods defined but no callers found in scripts/agent/ tree
- **Impact**: Dead methods add maintenance burden; missing API breaks expected functionality
- **Required Action**: Check if any CLI commands or external APIs expect these methods
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-07-22

### NC-014

- **Source File**: `03_rag_05_7-rag-index-consistency-checks.md`
- **Section**: §gen_rag_reference.py auto-update target
- **Line Number**: ~98
- **Question**: Should gen_rag_reference.py OPS_DOC constant be updated to split files?
- **Evidence**: Same issue as NC-010; tool outputs to non-existent file
- **Impact**: Same as NC-010
- **Required Action**: Same as NC-010 — resolve at root cause level
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-07-22

### NC-015

- **Source File**: `05_agent_12_02_memory-gate-data-model-search-part1.md`
- **Section**: §Threshold/retention functions
- **Line Number**: ~98
- **Question**: Where are RETENTION_DAYS and duplicate threshold functions used?
- **Evidence**: Functions referenced but usages unclear
- **Impact**: Unused functions add complexity; missing usage breaks deduplication
- **Required Action**: Trace function call chains to find consumers
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-07-22

### NC-016

- **Source File**: `90_shared_03_04_runtime_and_execution-caching-and-reference-part2.md`
- **Section**: §on_usage callback type
- **Line Number**: ~82
- **Question**: What is the actual shape of the on_usage callback?
- **Evidence**: Type declared as object | None; usage context unclear from this module alone
- **Impact**: Callback signature mismatch could cause runtime errors
- **Required Action**: Find actual callback invocation site to determine signature
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-07-22

### NC-017

- **Source File**: `05_agent_09_01_data-layer-session-db.md`
- **Section**: §SQLiteSessionStore callers
- **Line Number**: ~115
- **Question**: Who calls SQLiteSessionStore directly?
- **Evidence**: AgentSession uses SQLiteHelper directly, bypassing SQLiteSessionStore
- **Impact**: Dead class adds confusion; potential missed abstraction opportunity
- **Required Action**: Verify no test or external code uses SQLiteSessionStore
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-07-22

## Non-Goals

Topics explicitly excluded from this document:

- Resolving individual items — resolution requires separate investigation
- Modifying source documents during extraction — this document is read-only relative to sources
- Defining new evidence labels beyond those already established

## Related Governance Documents

Cross-cutting documentation rules and policies:

- [Documentation Governance](00_governance_01_documentation-governance.md)
- [Canonical Source Rule](00_governance_02_canonical-source-rule.md)
- [Evidence Labels](00_governance_03_evidence-labels.md)
- [Known Issues Template](00_governance_04_known-issues-template.md)
- [Deprecated Items](00_governance_05_deprecated-items.md)
- [AI Reading Metadata](00_governance_06_ai-reading-metadata.md)
