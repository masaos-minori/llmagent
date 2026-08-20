# Needs Confirmation Inventory

This document provides a centralized inventory of all "Needs confirmation" items found across the design documentation set. It makes unconfirmed statements trackable and actionable, preventing them from being silently accepted as facts.

## Inventory Entry Fields

Each entry must contain the following fifteen fields:

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
12. **Priority** — Classification of urgency: High (must resolve before next release), Medium (resolve within sprint), Low (nice-to-have)
13. **Related NC** — Other NC items that share the same root cause or dependency
14. **Resolution Target** — Date or milestone by which this item should be resolved
15. **Blocking** — Whether this item blocks other work (Yes/No)

## Status Values

- **open** — Item acknowledged but not yet investigated
- **investigating** — Investigation underway
- **resolved** — Item resolved through code change or documentation update
- **deferred** — Resolution postponed to future work
- **wontfix** — Item will not be addressed

### Priority values

- **High** — Must resolve before next release
- **Medium** — Should resolve within a sprint
- **Low** — Desired but not mandatory

## Extraction Process

To extract "Needs confirmation" items from source documents:

1. Search all Markdown files under `docs/` for the phrase "Needs confirmation"
2. For each match, identify the surrounding context (section, paragraph)
3. Populate all eleven required fields based on the context
4. Add the entry to this document with a sequential ID
5. Never modify the source documents during extraction

## Inventory Items

No active (open/investigating/deferred) items as of 2026-08-20 — all 17 originally tracked items have been resolved; see Archived (Resolved) Items below.

## Archived (Resolved) Items

### NC-001

- **Source File**: `05_agent_05_llm-and-streaming.md`
- **Section**: §Error Classification
- **Line Number**: ~176
- **Question**: Are `UTF8_PARTIAL_DECODE_ERROR` and `PREMATURE_EOF` distinct error types?
- **Evidence**: Both appear in error classification without clear distinction
- **Impact**: Incorrect error handling could cause silent failures
- **Required Action**: Verify error type definitions in LLMClient implementation
- **Resolution**: Confirmed distinct — `PREMATURE_EOF` is raised when SSE stream ends before expected content-length in `scripts/shared/llm_sse_stream.py:90`. `UTF8_PARTIAL_DECODE_ERROR` handles JSON decode errors separately.
- **Status**: resolved
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-07-29

### NC-002

- **Source File**: `03_rag_04_04_dto-models_config.md`
- **Section**: §ResultSource field definition
- **Line Number**: ~92
- **Question**: Is the unused ResultSource definition intentional for future migration or deletion oversight?
- **Evidence**: Field exists but has no current usage path in codebase
- **Impact**: Dead code may cause confusion; potential memory overhead
- **Required Action**: Confirm with original author or check git history
- **Resolution**: Obsolete — `ResultSource` enum is actively used in `SearchDiagnostics.result_source` (`scripts/rag/models_result.py:102`). Referenced doc file no longer contains this section.
- **Status**: resolved
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-07-29

### NC-003

- **Source File**: `03_rag_02_06_ingestion_pipeline-supporting-components.md`
- **Section**: §ETagManager behavior
- **Line Number**: ~42
- **Question**: Does ETagManager correctly handle existing document re-fetching?
- **Evidence**: DocumentManager passes fixed value `0` instead of `existing_doc_id` for ETag updates
- **Impact**: Existing document ETag updates may not function as intended
- **Required Action**: Trace ETag update flow through DocumentManager
- **Resolution**: Fixed — `_update_etag()` in `document_manager.py` now accepts `doc_id: int` parameter and passes it to `ETagManager(self._db, doc_id)`. `handle_existing_document()` threads `existing_doc_id` through.
- **Status**: resolved
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-07-29
- **Priority**: High
- **Resolution Target**: N/A (resolved)
- **Blocking**: No

### NC-004

- **Source File**: `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- **Section**: §knn_search method
- **Line Number**: ~66
- **Question**: Is the distance metric cosine or L2 — cannot determine from this module alone
- **Evidence**: Code comment says "Negate distance" but does not specify metric type
- **Impact**: Distance metric affects search quality and ranking
- **Required Action**: Check memories_vec table definition for metric specification
- **Resolution**: Confirmed L2/Euclidean — added explicit `distance_metric=L2` clause to both `memories_vec` and `chunks_vec` vec0 DDL in `schema_sql.py`. Retriever comment updated to name L2 and note magnitude sensitivity.
- **Status**: resolved
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-07-29

### NC-005

- **Source File**: `03_rag_04_03_dto-models_audit.md`
- **Section**: §DTO purpose analysis
- **Line Number**: ~40
- **Question**: Are AuditLogRecord/ApprovalDecision dead code or forward-looking definitions?
- **Evidence**: Zero callers found via repo-wide grep; classes were never imported from `scripts/` or `tests/`
- **Impact**: Dead code creates maintenance burden
- **Required Action**: Resolved — confirmed zero production callers via full-repo grep and git history back to initial commit. Both classes removed from `scripts/rag/models_audit.py`. See implementations/done/20260728-174511_models_audit.py.md.
- **Status**: resolved
- **Assigned To**: N/A — resolved
- **Last Reviewed**: 2026-07-29

### NC-006

- **Source File**: `03_rag_03_06_query_pipeline-helpers-and-cache.md`
- **Section**: §result_source field analysis
- **Line Number**: ~120
- **Question**: Is result_source field intended for future use or should it be removed?
- **Evidence**: No code path sets PipelineRunResult.result_source; only SearchDiagnostics uses dataclasses.replace()
- **Impact**: Dead field may confuse developers; potential hidden functionality
- **Required Action**: Check git history for original intent; verify no plugin sets this field
- **Resolution**: Removed `result_source` field from `PipelineRunResult` in `scripts/rag/types.py`. Field was confirmed dead — no construction site passes `result_source=` argument, no reader exists. See implementation `implementations/20260728-174511_types.py.md`.
- **Status**: resolved
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-07-29

### NC-007

- **Source File**: `05_agent_04_03_state-and-persistence-platform-databases.md`
- **Section**: §Archive memory operation
- **Line Number**: ~54
- **Question**: What is the read path for archived memory?
- **Evidence**: Archive operation exists but read path details unclear
- **Impact**: Archived data may be inaccessible after write
- **Required Action**: Trace archive write and find corresponding read path
- **Resolution**: Read path confirmed — `JsonlMemoryStore.read_all()` returns all entries; `read_active()` filters by retention policy per source type. See `scripts/agent/memory/jsonl_store.py:72-111`.
- **Status**: resolved
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-07-29

### NC-008

- **Source File**: `05_agent_04_03_state-and-persistence-platform-databases.md`
- **Section**: §request_approval workflow_id parameter
- **Line Number**: ~109-110
- **Question**: How is workflow_id used in multi-workflow scenario?
- **Evidence**: Parameter appears to distinguish multiple workflows but purpose unclear
- **Impact**: Multi-workflow routing may fail silently
- **Required Action**: Trace workflow_id usage in request_approval call chain
- **Resolution**: `workflow_id` is stored in `approvals` table and returned in query results, but current code does NOT filter/route by it. It serves only as a tracking field. No active filtering logic uses this column.
- **Status**: resolved
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-07-29
- **Priority**: High
- **Resolution Target**: N/A (resolved)
- **Blocking**: No

### NC-009

- **Source File**: `03_rag_04_05_dto-types.md`
- **Section**: §RagPipelineConfig.run field
- **Line Number**: ~48
- **Question**: Who explicitly sets the run field?
- **Evidence**: Field exists but setting mechanism unknown
- **Impact**: Run field may never be set, causing incorrect pipeline state
- **Required Action**: Search codebase for explicit run field assignment
- **Resolution**: The `run` field no longer exists on `RagPipelineConfig`. This NC is obsolete — the field was removed in a prior implementation cycle.
- **Status**: resolved
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-07-29

### NC-010

- **Source File**: `03_rag_05_7-rag-index-consistency-checks.md`
- **Section**: §gen_rag_reference.py auto-update target
- **Line Number**: ~98
- **Question**: Should gen_rag_reference.py OPS_DOC constant be updated to split files?
- **Evidence**: Same issue as NC-010; tool outputs to non-existent file
- **Impact**: Auto-generated content becomes stale; manual tracking required
- **Required Action**: Determine if tool should be updated or if manual process is acceptable
- **Resolution**: Resolved — OPS_DOC removed from `tools/gen_rag_reference.py`; CLI-help-only write path established via `CLI_HELP_DOC`. Config-table generation kept only under `--dry-run`. See implementation `implementations/20260728-175500_gen_rag_reference.py.md`.
- **Status**: resolved
- **Assigned To**: N/A — resolved
- **Last Reviewed**: 2026-07-29
- **Priority**: Medium
- **Resolution Target**: Current sprint
- **Blocking**: No
- **Related NC**: NC-010

### NC-011

- **Source File**: `03_rag_02_04_ingestion_pipeline-ingester.md`
- **Section**: §docstring accuracy
- **Line Number**: ~49
- **Question**: Is the docstring reference to common.toml::embedding_dims intentional legacy text?
- **Evidence**: Docstring references non-existent common.toml; actual config comes from ingester.toml
- **Impact**: Misleading documentation may cause incorrect assumptions
- **Required Action**: Resolved — confirmed outdated; see docs/03_rag_02_04_ingestion_pipeline-ingester.md §4.4 (~line 51): common.toml does not exist, actual config source is config/ingester.toml.
- **Status**: resolved
- **Assigned To**: N/A — resolved
- **Last Reviewed**: 2026-07-29

### NC-012

- **Source File**: `05_agent_10_05_operations-and-observability-monitoring.md`
- **Section**: §DiagnosticStore loop_guard_hint method
- **Line Number**: ~92
- **Question**: Is loop_guard_hint kind name ever generated in practice?
- **Evidence**: Method defined but no caller found in scripts/agent/ tree
- **Impact**: Dead method may indicate incomplete feature or unnecessary code
- **Required Action**: Resolved — `save_loop_guard_hint` method removed (confirmed zero production callers). `guard_hint` confirmed as the sole loop-guard kind. See implementations/done/20260728-175009_diagnostic_store.py.md.
- **Status**: resolved
- **Assigned To**: N/A — resolved
- **Last Reviewed**: 2026-07-22

### NC-013

- **Source File**: `05_agent_10_05_operations-and-observability-monitoring.md`
- **Section**: §DiagnosticStore fetch_by_kind / fetch_all methods
- **Line Number**: ~93
- **Question**: Are fetch_by_kind/fetch_all methods intended for CLI/API use?
- **Evidence**: Methods defined but no callers found in scripts/agent/ tree
- **Impact**: Dead methods add maintenance burden; missing API breaks expected functionality
- **Required Action**: Resolved — both methods removed (confirmed zero production callers). See implementations/done/20260728-180000_diagnostic_store.py.md.
- **Status**: resolved
- **Assigned To**: N/A — resolved
- **Last Reviewed**: 2026-07-22

### NC-014

- **Source File**: `03_rag_05_7-rag-index-consistency-checks.md`
- **Section**: §gen_rag_reference.py auto-update target
- **Line Number**: ~98
- **Question**: Should gen_rag_reference.py OPS_DOC constant be updated to split files?
- **Evidence**: Same issue as NC-010; tool outputs to non-existent file
- **Impact**: Same as NC-010
- **Required Action**: Resolved — NC-014 shares root cause with NC-010; resolved by sibling plan `implementations/20260728-175500_gen_rag_reference.py.md` (CLI-help-only write path). See also `plans/20260727-152003_plan.md`.
- **Status**: resolved
- **Assigned To**: N/A — resolved
- **Last Reviewed**: 2026-07-29
- **Priority**: Medium
- **Resolution Target**: Current sprint
- **Blocking**: No
- **Related NC**: NC-010

### NC-015

- **Source File**: `05_agent_12_02_memory-gate-data-model-search.md`
- **Section**: §Threshold/retention functions
- **Line Number**: ~98
- **Question**: Where are RETENTION_DAYS and duplicate threshold functions used?
- **Evidence**: Functions referenced but usages unclear
- **Impact**: Unused functions add complexity; missing usage breaks deduplication
- **Required Action**: Resolved — DEDUP_THRESHOLDS actively consumed by `_get_dedup_threshold()` (ingestion.py:178-184) during memory ingestion; RETENTION_DAYS only referenced by `JsonlMemoryStore.read_active()` (jsonl_store.py:91-111) which has zero callers repo-wide — dead code. See docs/05_agent_12_02_memory-gate-data-model-search.md §Implementation Notes.
- **Status**: resolved
- **Assigned To**: N/A — resolved
- **Last Reviewed**: 2026-07-22

### NC-016

- **Source File**: `90_shared_03_04_runtime_and_execution-caching-and-reference.md`
- **Section**: §on_usage callback type
- **Line Number**: ~82
- **Question**: What is the actual shape of the on_usage callback?
- **Evidence**: Type declared as object | None; usage context unclear from this module alone
- **Impact**: Callback signature mismatch could cause runtime errors
- **Required Action**: Resolved — confirmed `Callable[[int, int], None] | None`, invoked as `on_usage(prompt_tokens, completion_tokens)` from `shared.llm_sse_helpers.LlmSseHelpers.parse_usage()`. See docs/90_shared_03_04_runtime_and_execution-caching-and-reference.md §18.
- **Status**: resolved
- **Assigned To**: N/A — resolved
- **Last Reviewed**: 2026-07-22

### NC-017

- **Source File**: `05_agent_09_01_data-layer-session-db.md`
- **Section**: §SQLiteSessionStore callers
- **Line Number**: ~115
- **Question**: Who calls SQLiteSessionStore directly?
- **Evidence**: AgentSession uses SQLiteHelper directly, bypassing SQLiteSessionStore
- **Impact**: Dead class adds confusion; potential missed abstraction opportunity
- **Required Action**: Resolved — confirmed zero production callers via full-repo grep and git history back to initial commit. Sole caller is tests/test_db_store_impl.py::TestSQLiteSessionStore (protocol-conformance test scaffolding). See implementations/20260728-182000_nc017_docs.md.
- **Status**: resolved
- **Assigned To**: N/A — resolved
- **Last Reviewed**: 2026-07-29

### NC-018

- **Source File**: `05_agent_03_03_turn-processing-flow-workflow-engine.md`
- **Section**: §Approval Gate
- **Line Number**: ~97
- **Question**: What is the production default policy for `WorkflowDef.require_approval`, and does the documented "expire" lifecycle state actually work?
- **Evidence**: `config/workflows/default.json` ships `require_approval: false` with no per-environment override mechanism; `WorkflowEngine._gate_approval()` did not check `expires_at` prior to this resolution
- **Impact**: Ambiguous production guidance could leave post-execution approval gates disabled in environments that need them; an approval record could remain "pending" forever past its TTL
- **Required Action**: Resolved — a per-operation-category approval-requirement table and local-dev exception policy are now documented in `05_agent_03_03_turn-processing-flow-workflow-engine.md` §Approval Gate; `is_expired()` was added to `agent/workflow/approval_ops.py` and `WorkflowEngine._gate_approval()` now re-requests approval when a pending record has expired, tested by `test_expired_pending_approval_is_re_requested`.
- **Status**: resolved
- **Assigned To**: N/A — resolved
- **Last Reviewed**: 2026-08-20

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
- [Terminology Glossary](00_governance_09_terminology-glossary.md)
