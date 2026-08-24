---
title: "Issue and Uncertainty Management"
area: governance
tags:
  - governance
related:
  - 00_index.md
  - 01_overview.md
---

# Issue and Uncertainty Management

## Purpose

This document defines how to track discrepancies between documentation and implementation (Known Issues), manage unverified claims (Needs Confirmation), and migrate existing entries to standardized formats. It ensures unconfirmed statements are trackable and actionable, preventing them from being silently accepted as facts.

## Part 1: Known Issues

### Entry Template

Each Known Issue entry must contain these 17 fields: ID, Title, Status, Severity, Area, Type, Source, Owner, First Found, Target, Related, Summary, Current Description, Observed Implementation, Impact, Recommended Action, Resolution Notes.

### Status Values

- **open** — Issue acknowledged but not yet investigated
- **investigating** — Investigation underway
- **fixed** — Issue resolved
- **deferred** — Resolution postponed to future work
- **deprecated** — Issue no longer relevant (obsolete feature)
- **wontfix** — Issue will not be addressed

### Type Values

- **document-code-mismatch** — Documentation contradicts code behavior
- **document-document-mismatch** — Two documents contradict each other
- **obsolete-description** — Description refers to removed/deprecated feature
- **missing-documentation** — Feature exists without documentation
- **ambiguous-behavior** — Behavior unclear due to insufficient specification
- **implementation-bug** — Code does not match documented intent
- **design-gap** — Missing design consideration
- **operational-gap** — Missing operational guidance

### Severity Values

- **High** — Requires immediate attention; affects safety or critical functionality
- **Medium** — Should be addressed soon; affects correctness or clarity
- **Low** — Can be deferred; minor inconsistency or formatting issue

### Owner Values

- **Unassigned** — No owner assigned
- **[Name]** — Assigned to specific person
- **Team** — Assigned to team decision

### Area Values

Overview, Deployment, RAG, MCP, Agent, EventBus, Shared/DB, Governance

### Lifecycle

Open → Investigating → Fixed/Deferred/Wontfix; Deprecated when underlying feature removed.

## Part 2: Needs Confirmation Inventory

### Purpose

A centralized inventory of all "Needs confirmation" items found across the design documentation set. It makes unconfirmed statements trackable and actionable, preventing them from being silently accepted as facts.

### Inventory Entry Fields

Each entry must contain these fifteen fields: ID, Source File, Section, Line Number, Question, Evidence, Impact, Required Action, Status, Assigned To, Last Reviewed, Priority, Related NC, Resolution Target, Blocking.

### Status Values

- **open** — Acknowledged but not investigated
- **investigating** — Underway
- **resolved** — Resolved through code or docs update
- **deferred** — Postponed
- **wontfix** — Will not address

### Priority Values

- **High** — Must resolve before next release
- **Medium** — Resolve within sprint
- **Low** — Nice-to-have

### Extraction Process

Search `docs/` for "Needs confirmation", populate fields from context, add sequential ID, never modify source documents.

### Active Items

#### NC-019

- **Source File**: `04_mcp_04_05_git.md`
- **Section**: Implementation Notes (also referenced from Write protection policy)
- **Line Number**: ~92
- **Question**: Is absence of command-specific guards distinguishing `git_checkout`/`git_pull`/`git_push` from other write tools an intentional design decision or missing security feature?
- **Evidence**: All five write tools share one common guard path (`allowed_repo_paths` + `read_only`) with no per-command validation; confirmed exploitable gap (forced checkout/push)
- **Impact**: If unintentional, leaves confirmed exploitable gap unresolved; if intentional, design intent should be documented rather than left implicit
- **Required Action**: Decision from tool owner on whether ADR-012's target guards (protected-branch, ref/remote validation, Force-Push rejection) should be implemented
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-08-21
- **Priority**: High
- **Related NC**: NC-020
- **Resolution Target**: Owner decision, then implementation per ADR-012
- **Blocking**: No — tracked in parallel with Known Issue MCP-003

#### NC-020

- **Source File**: `04_mcp_04_05_git.md`
- **Section**: Write protection policy → Audit
- **Line Number**: ~147
- **Question**: Does Git MCP audit call site's `target` field actually end up empty for every call?
- **Evidence**: Code inspection only — no live audit log line captured to confirm field is empty in practice
- **Impact**: If confirmed, Git MCP audit entries carry no repository identity, weakening audit trail for High-Severity write surface
- **Required Action**: Capture actual audit log line for git-mcp call and check whether `target` is empty; fix key to `repo_path` if confirmed
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-08-21
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next investigation of Git MCP audit logging
- **Blocking**: No

#### NC-021

- **Source File**: `90_shared_05_04_db_api_and_operations-recovery-and-reference.md`
- **Section**: 9.3 Integrity-result model (target design)
- **Line Number**: ~39
- **Question**: Is the target structured integrity-result classification (healthy / confirmed corruption / lock contention / permission / invalid format / unknown) the classification model the owner intends to implement?
- **Evidence**: `_run_integrity_check()` currently returns only pass/fail-ish result plus free-form exception string; no structured classification exists
- **Impact**: Implementing wrong classification model would require rework; leaving unconfirmed risks divergent interpretations
- **Required Action**: Owner review of proposed model in ADR-011 before implementation begins
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-08-21
- **Priority**: Medium
- **Related NC**: None
- **Resolution Target**: Before implementing Known Issue SHARED-001/SHARED-002 fixes
- **Blocking**: No

No other active (open/investigating/deferred) items beyond NC-019 through NC-021 above — all 17 previously tracked items have been resolved; see Archived (Resolved) Items below.

### Archived (Resolved) Items

| ID | Source File | Section | Resolution Summary |
|----|-------------|---------|-------------------|
| NC-001 | `05_agent_05_llm-and-streaming.md` | Error Classification | Confirmed distinct — `PREMATURE_EOF` raised when SSE stream ends before expected content-length; `UTF8_PARTIAL_DECODE_ERROR` handles JSON decode errors separately |
| NC-002 | `03_rag_04_04_dto-models_config.md` | ResultSource field | Obsolete — `ResultSource` enum actively used in `SearchDiagnostics.result_source`; referenced doc file no longer contains this section |
| NC-003 | `03_rag_02_06_ingestion_pipeline-supporting-components.md` | ETagManager behavior | Fixed — `_update_etag()` now accepts `doc_id` parameter; `handle_existing_document()` threads `existing_doc_id` through |
| NC-004 | `05_agent_12_04_memory-module-ref-retrieval-and-injection.md` | knn_search method | Confirmed L2/Euclidean — added explicit `distance_metric=L2` clause to vec0 DDL |
| NC-005 | `03_rag_04_03_dto-models_audit.md` | DTO purpose analysis | Removed — confirmed zero production callers; both classes removed from `scripts/rag/models_audit.py` |
| NC-006 | `03_rag_03_06_query_pipeline-helpers-and-cache.md` | result_source field | Removed `result_source` field from `PipelineRunResult` — confirmed dead |
| NC-007 | `05_agent_04_03_state-and-persistence-platform-databases.md` | Archive memory operation | Read path confirmed — `JsonlMemoryStore.read_all()` returns all entries; `read_active()` filters by retention policy |
| NC-008 | `05_agent_04_03_state-and-persistence-platform-databases.md` | request_approval workflow_id | `workflow_id` stored in `approvals` table but current code does NOT filter/route by it — serves only as tracking field |
| NC-009 | `03_rag_04_05_dto-types.md` | RagPipelineConfig.run field | Obsolete — `run` field no longer exists on `RagPipelineConfig` |
| NC-010 | `03_rag_05_7-rag-index-consistency-checks.md` | gen_rag_reference.py auto-update | OPS_DOC removed from `tools/gen_rag_reference.py`; CLI-help-only write path established |
| NC-011 | `03_rag_02_04_ingestion_pipeline-ingester.md` | docstring accuracy | Resolved — confirmed outdated; actual config source is config/ingester.toml |
| NC-012 | `05_agent_10_05_operations-and-observability-monitoring.md` | DiagnosticStore loop_guard_hint | Method removed — confirmed zero production callers |
| NC-013 | `05_agent_10_05_operations-and-observability-monitoring.md` | DiagnosticStore fetch_by_kind/fetch_all | Both methods removed — confirmed zero production callers |
| NC-014 | `03_rag_05_7-rag-index-consistency-checks.md` | gen_rag_reference.py auto-update | Shared root cause with NC-010; resolved by sibling plan |
| NC-015 | `05_agent_12_02_memory-gate-data-model-search.md` | Threshold/retention functions | DEDUP_THRESHOLDS consumed by `_get_dedup_threshold()`; RETENTION_DAYS dead code |
| NC-016 | `90_shared_03_04_runtime_and_execution-caching-and-reference.md` | on_usage callback type | Confirmed `Callable[[int, int], None] / None` — invoked as `on_usage(prompt_tokens, completion_tokens)` |
| NC-017 | `05_agent_09_01_data-layer-session-db.md` | SQLiteSessionStore callers | Zero production callers via full-repo grep; sole caller is tests/test_db_store_impl.py |
| NC-018 | `05_agent_03_03_turn-processing-flow-workflow-engine.md` | Approval Gate | `is_expired()` added to `approval_ops.py`; `_gate_approval()` now re-requests expired pending approval |

## Part 3: Known Issues Migration Plan

### Purpose

This document defines the migration plan for transitioning existing Known Issues / Inconsistencies documents across all areas to the new common template defined in Part 1 above. It ensures a controlled, gradual transition that preserves existing IDs and history.

### Scope

**Included**: Planning the migration of five area Known Issues documents to use the common template format. Recording current formats as baseline. Defining priority criteria and suggested order.

**Excluded**: Actually modifying any existing Known Issues documents during this planning phase. Creating follow-up issues for each area migration.

### Target Files

Five areas' Known Issues documents to investigate:

- `docs/03_rag_90_inconsistencies_and_known_issues.md`
- `docs/04_mcp_90_inconsistencies_and_known_issues.md`
- `docs/05_agent_90_inconsistencies_and_known_issues.md`
- `docs/06_eventbus_90_inconsistencies_and_known_issues.md`
- `docs/90_shared_90_inconsistencies_and_known_issues.md`

### Current Format Summary

#### RAG (`03_rag_90`)

- Entry count: 2 (both migrated to ADRs)
- Severity classification: None
- Type classification: Uses "Confirmed Design Decision" type
- Status classification: None
- Unique conventions: Japanese section headers; "Invariants (non-negotiable)" sub-section; implementation verification notes

#### MCP (`04_mcp_90`)

- Entry count: 2
- Severity classification: None
- Type classification: English types ("Implementation bug", "Unimplemented", etc.)
- Status classification: None
- Unique conventions: "Current behavior" instead of "Statement A/B"; includes "Affected config" field

#### Agent (`05_agent_90`)

- Entry count: 3
- Severity classification: None
- Type classification: English types ("Document inconsistency", "Implementation bug", etc.)
- Status classification: None
- Unique conventions: Standard Statement A/B format; "Notes for AI reference" field

#### EventBus (`06_eventbus_90`)

- Entry count: 6 across multiple sections
- Severity classification: None
- Type classification: None — uses section-based grouping instead
- Status classification: None
- Unique conventions: Table-based format with "Item / Safe Interpretation / Recommended Action" columns

#### Shared/DB (`90_shared_90`)

- Entry count: 1
- Severity classification: None
- Type classification: Japanese types ("Document Inconsistency", "Implementation Bug", etc.)
- Status classification: None
- Unique conventions: Includes "Evidence" field referencing specific test files

### Migration Policy

- Migrate one area at a time via separate follow-up issues
- Preserve all existing entry IDs during migration
- Do not resolve or change the substance of existing entries during migration
- Add missing metadata fields (severity, status, owner) based on best available information
- Mark migrated entries with a migration note indicating the date and source template
- Review each migrated entry for accuracy before closing the migration issue

### Priority Criteria

1. **Entry count** — Areas with more entries benefit more from standardization
2. **Format divergence** — Areas whose format differs most from the target template have higher migration value
3. **Language consistency** — Areas using non-English headers/types should be prioritized for alignment
4. **Cross-references** — Areas frequently referenced by other documents need consistent formatting
5. **Active maintenance** — Areas with recent changes require stable format for ongoing work
6. **Business impact** — Areas affecting critical operations should have standardized tracking

### Suggested Migration Order

Based on priority criteria above:

1. **Agent** — High entry count (3), uses English types but inconsistent with target template, frequently referenced
2. **MCP** — Medium entry count (2), uses English types but different field names, cross-area dependencies
3. **RAG** — Low entry count (2), uses Japanese headers creating language inconsistency, complex invariant tracking needs
4. **EventBus** — Highest format divergence (table-based), medium entry count (6), lower cross-reference frequency
5. **Shared/DB** — Lowest entry count (1), uses Japanese types, limited cross-references

### Risks

- **Lost historical context**: Preserve original content in migration notes before removing it
- **ID conflicts**: Map old IDs to new ones explicitly during migration
- **Scope creep**: Define strict acceptance criteria for each migration issue

### Acceptance Criteria for Future Migration

Each future migration issue must verify:

- All existing entries from the source document appear in the migrated version
- All existing entry IDs are preserved or explicitly mapped to new IDs
- No entry content was changed beyond adding required metadata fields
- Cross-links to related governance documents are present
- The migrated document passes consistency checks against the common template definition

## Non-Goals

Topics explicitly excluded from this document:

- Resolving individual items — resolution requires separate investigation
- Modifying source documents during extraction — this document is read-only relative to sources
- Defining new evidence labels beyond those already established
- Changing the common template itself
- Migrating non-Known-Issues documents

## Related Documents

Cross-cutting documentation rules and policies:

- [Documentation Policy](00_governance_12_documentation-policy.md)
- [Documentation Metadata](00_governance_13_documentation-metadata.md)
- [Documentation Checks](00_governance_15_documentation-checks.md)

## Keywords

known issues
needs confirmation
migration plan
inconsistencies
template
evidence labels
resolution workflow
