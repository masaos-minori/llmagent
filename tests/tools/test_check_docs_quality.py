#!/usr/bin/env python3
"""Tests for tools.check_docs_quality — alphabetic-suffix duplicate headings + content similarity."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

from tools.check_docs_quality import (
    _compute_section_similarity,
    check_content_similarity,
    check_duplicate_heading_numbers,
)

# Baseline snapshot of within-file content-similarity pairs (updated 2026-09-23 after
# a large fast-forwarded batch of docs/ADR reconciliation edits shifted the set —
# this drift is expected per issues/done/20260920-175221_docqtest01's own design: a
# set-based snapshot tolerates the count changing while making exactly which
# file:section pairs changed explicit and diffable).
# Regenerate by running: uv run python -m tools.check_docs_quality
#   | grep 'between sections' > /tmp/pairs.txt
# Then extract pairs from /tmp/pairs.txt and update this constant.
EXPECTED_WITHIN_FILE_PAIRS: frozenset[str] = frozenset(
    [
        # 00_governance/00_governance_01_documentation-policy.md
        "00_governance/00_governance_01_documentation-policy.md:'Agent' <-> 'EventBus'",
        "00_governance/00_governance_01_documentation-policy.md:'Agent' <-> 'Shared/DB'",
        "00_governance/00_governance_01_documentation-policy.md:'EventBus' <-> 'Shared/DB'",
        "00_governance/00_governance_01_documentation-policy.md:'MCP' <-> 'Agent'",
        "00_governance/00_governance_01_documentation-policy.md:'MCP' <-> 'EventBus'",
        "00_governance/00_governance_01_documentation-policy.md:'MCP' <-> 'Shared/DB'",
        "00_governance/00_governance_01_documentation-policy.md:'RAG' <-> 'Agent'",
        "00_governance/00_governance_01_documentation-policy.md:'RAG' <-> 'EventBus'",
        "00_governance/00_governance_01_documentation-policy.md:'RAG' <-> 'MCP'",
        "00_governance/00_governance_01_documentation-policy.md:'RAG' <-> 'Shared/DB'",
        # 00_governance/00_governance_03_issue-and-uncertainty-management.md
        "00_governance/00_governance_03_issue-and-uncertainty-management.md:'CI-009' <-> 'CI-012'",
        "00_governance/00_governance_03_issue-and-uncertainty-management.md:'Lifecycle' <-> 'Lifecycle'",
        # 03_rag_02_01_ingestion_pipeline-overview.md
        "03_rag_02_01_ingestion_pipeline-overview.md:'Batch split unprocessed files' <-> 'Regenerate existing chunks'",
        "03_rag_02_01_ingestion_pipeline-overview.md:'Embed and save to DB' <-> 'Force re-registration'",
        "03_rag_02_01_ingestion_pipeline-overview.md:'Step 1: Crawling' <-> 'Step 2: Chunk Splitting'",
        "03_rag_02_01_ingestion_pipeline-overview.md:'Step 1: Crawling' <-> 'Step 3: Embedding and Storage'",
        "03_rag_02_01_ingestion_pipeline-overview.md:'Step 2: Chunk Splitting' <-> 'Step 3: Embedding and Storage'",
        # 03_rag_02_03_ingestion_pipeline-chunksplitter.md
        "03_rag_02_03_ingestion_pipeline-chunksplitter.md:'Keywords' <-> 'Keywords'",
        "03_rag_02_03_ingestion_pipeline-chunksplitter.md:'RAG Ingestion Pipeline' <-> 'RAG Ingestion Pipeline'",
        # 03_rag_02_04_ingestion_pipeline-ingester.md
        "03_rag_02_04_ingestion_pipeline-ingester.md:'4.2 Detailed Behavior' <-> '4.2 Detailed Behavior'",
        "03_rag_02_04_ingestion_pipeline-ingester.md:'4.2.1 Immutable Deletion Order' <-> '4.2.1 Immutable Deletion Order'",
        "03_rag_02_04_ingestion_pipeline-ingester.md:'4.3 CLI Arguments' <-> '4.3 CLI Arguments'",
        "03_rag_02_04_ingestion_pipeline-ingester.md:'4.4 Embedding API' <-> '4.4 Embedding API'",
        "03_rag_02_04_ingestion_pipeline-ingester.md:'4.5 Database Updates' <-> '4.5 Database Updates'",
        "03_rag_02_04_ingestion_pipeline-ingester.md:'4.6 Error Handling' <-> '4.6 Error Handling'",
        "03_rag_02_04_ingestion_pipeline-ingester.md:'4.7 Logging' <-> '4.7 Logging'",
        "03_rag_02_04_ingestion_pipeline-ingester.md:'Keywords' <-> 'Keywords'",
        "03_rag_02_04_ingestion_pipeline-ingester.md:'RAG Ingestion Pipeline' <-> 'RAG Ingestion Pipeline'",
        # 03_rag_03_02_query_pipeline-rag-pipeline-class.md
        "03_rag_03_02_query_pipeline-rag-pipeline-class.md:'Keywords' <-> 'Keywords'",
        # 03_rag_03_06_query_pipeline-helpers-and-cache.md
        "03_rag_03_06_query_pipeline-helpers-and-cache.md:'RAG Query Pipeline' <-> 'RAG Query Pipeline Implementation Details'",
        # 03_rag_05_2-execution-guide.md
        "03_rag_05_2-execution-guide.md:'2.1 Prerequisites' <-> '2.2 Step 1: Crawling'",
        "03_rag_05_2-execution-guide.md:'2.1 Prerequisites' <-> '2.3 Step 2: Chunk Splitting'",
        "03_rag_05_2-execution-guide.md:'2.1 Prerequisites' <-> '2.4 Embedding and Storage'",
        "03_rag_05_2-execution-guide.md:'2.2 Step 1: Crawling' <-> '2.3 Step 2: Chunk Splitting'",
        "03_rag_05_2-execution-guide.md:'2.2 Step 1: Crawling' <-> '2.4 Embedding and Storage'",
        "03_rag_05_2-execution-guide.md:'2.3 Step 2: Chunk Splitting' <-> '2.4 Embedding and Storage'",
        "03_rag_05_2-execution-guide.md:'Batch split unprocessed files' <-> 'Regenerate existing chunks'",
        "03_rag_05_2-execution-guide.md:'Embed and save to DB' <-> 'Force re-registration'",
        # 04_mcp_05_01_access-control-and-allowlists.md
        "04_mcp_05_01_access-control-and-allowlists.md:'`allow_force_push`' <-> 'Workflow Allowlist (cicd-mcp)'",
        "04_mcp_05_01_access-control-and-allowlists.md:'`allow_force_push`' <-> '`require_pr_review`'",
        "04_mcp_05_01_access-control-and-allowlists.md:'`allowed_dirs` (File Servers)' <-> 'Workflow Allowlist (cicd-mcp)'",
        "04_mcp_05_01_access-control-and-allowlists.md:'`allowed_dirs` (File Servers)' <-> '`allow_force_push`'",
        "04_mcp_05_01_access-control-and-allowlists.md:'`allowed_dirs` (File Servers)' <-> '`allowed_repo_paths` (git-mcp)'",
        "04_mcp_05_01_access-control-and-allowlists.md:'`allowed_dirs` (File Servers)' <-> '`path_denylist`'",
        "04_mcp_05_01_access-control-and-allowlists.md:'`allowed_dirs` (File Servers)' <-> '`protected_branches`'",
        "04_mcp_05_01_access-control-and-allowlists.md:'`allowed_dirs` (File Servers)' <-> '`require_pr_review`'",
        "04_mcp_05_01_access-control-and-allowlists.md:'`allowed_repo_paths` (git-mcp)' <-> 'Workflow Allowlist (cicd-mcp)'",
        "04_mcp_05_01_access-control-and-allowlists.md:'`allowed_repo_paths` (git-mcp)' <-> '`allow_force_push`'",
        "04_mcp_05_01_access-control-and-allowlists.md:'`allowed_repo_paths` (git-mcp)' <-> '`path_denylist`'",
        "04_mcp_05_01_access-control-and-allowlists.md:'`allowed_repo_paths` (git-mcp)' <-> '`protected_branches`'",
        "04_mcp_05_01_access-control-and-allowlists.md:'`allowed_repo_paths` (git-mcp)' <-> '`require_pr_review`'",
        "04_mcp_05_01_access-control-and-allowlists.md:'`path_denylist`' <-> 'Workflow Allowlist (cicd-mcp)'",
        "04_mcp_05_01_access-control-and-allowlists.md:'`path_denylist`' <-> '`allow_force_push`'",
        "04_mcp_05_01_access-control-and-allowlists.md:'`path_denylist`' <-> '`require_pr_review`'",
        "04_mcp_05_01_access-control-and-allowlists.md:'`protected_branches`' <-> 'Workflow Allowlist (cicd-mcp)'",
        "04_mcp_05_01_access-control-and-allowlists.md:'`protected_branches`' <-> '`allow_force_push`'",
        "04_mcp_05_01_access-control-and-allowlists.md:'`protected_branches`' <-> '`path_denylist`'",
        "04_mcp_05_01_access-control-and-allowlists.md:'`protected_branches`' <-> '`require_pr_review`'",
        "04_mcp_05_01_access-control-and-allowlists.md:'`require_pr_review`' <-> 'Workflow Allowlist (cicd-mcp)'",
        # 04_mcp_06_07_reading-audit-logs.md
        "04_mcp_06_07_reading-audit-logs.md:'View all audit events (MCP server + agent-side)' <-> 'View raw agent-side audit events (JSON-lines format)'",
        # 04_mcp_06_13_watchdog-health-reasons-scheduling.md
        "04_mcp_06_13_watchdog-health-reasons-scheduling.md:'Keywords' <-> 'Keywords'",
        # 05_agent_02_runtime-architecture.md
        "05_agent_02_runtime-architecture.md:'Keywords' <-> 'Keywords'",
        "05_agent_02_runtime-architecture.md:'Known Limitations' <-> 'Known Limitations'",
        "05_agent_02_runtime-architecture.md:'Related Documents' <-> 'Agent Runtime Architecture (Part 2)'",
        # 05_agent_07_02_cli-and-commands-cliview.md
        "05_agent_07_02_cli-and-commands-cliview.md:'Operational Notes' <-> 'Known Limitations'",
        # 05_agent_07_03_cli-and-commands-command-registry.md
        "05_agent_07_03_cli-and-commands-command-registry.md:'Key Constraints' <-> 'Operational Notes'",
        # 05_agent_07_06_cli-and-commands-hot-reload.md
        "05_agent_07_06_cli-and-commands-hot-reload.md:'Key Constraints' <-> 'Known Limitations'",
        # 05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md
        "05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md:'Key Constraints' <-> 'Known Limitations'",
        "05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md:'Key Constraints' <-> 'Operational Notes'",
        "05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md:'Operational Notes' <-> 'Known Limitations'",
        # 05_agent_07_09_cli-and-commands-slash-commands-context-db.md
        "05_agent_07_09_cli-and-commands-slash-commands-context-db.md:'Key Constraints' <-> 'Known Limitations'",
        "05_agent_07_09_cli-and-commands-slash-commands-context-db.md:'Key Constraints' <-> 'Operational Notes'",
        "05_agent_07_09_cli-and-commands-slash-commands-context-db.md:'Operational Notes' <-> 'Known Limitations'",
        # 05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md
        "05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md:'Key Constraints' <-> 'Operational Notes'",
        # 05_agent_07_11_cli-and-commands-slash-commands-memory-other.md
        "05_agent_07_11_cli-and-commands-slash-commands-memory-other.md:'Key Constraints' <-> 'Operational Notes'",
        # 05_agent_08_01_configuration-loading-agent-config.md
        "05_agent_08_01_configuration-loading-agent-config.md:'Key Constraints' <-> 'Known Limitations'",
        "05_agent_08_01_configuration-loading-agent-config.md:'Key Constraints' <-> 'Operational Notes'",
        "05_agent_08_01_configuration-loading-agent-config.md:'Operational Notes' <-> 'Known Limitations'",
        # 05_agent_08_02_configuration-llm-rag.md
        "05_agent_08_02_configuration-llm-rag.md:'Operational Notes' <-> 'Known Limitations'",
        # 05_agent_08_03_configuration-tools-memory.md
        "05_agent_08_03_configuration-tools-memory.md:'Operational Notes' <-> 'Known Limitations'",
        # 05_agent_09_02_data-layer-access-patterns.md
        "05_agent_09_02_data-layer-access-patterns.md:'Operational Notes' <-> 'Known Limitations'",
        # 05_agent_09_03_data-layer-indexing-boundaries.md
        "05_agent_09_03_data-layer-indexing-boundaries.md:'Operational Notes' <-> 'Known Limitations'",
        # 05_agent_12_01_memory-overview-and-modes.md
        "05_agent_12_01_memory-overview-and-modes.md:'Keywords' <-> 'Memory Layer — Overview and Modes (Part 2)'",
        # 05_agent_12_02_memory-gate-data-model-search.md
        "05_agent_12_02_memory-gate-data-model-search.md:'Memory Layer — Activation Gate, Data Model, and Search (Part 1)' <-> 'Memory Layer — Module Reference'",
        # 05_agent_13_reference-api.md
        "05_agent_13_reference-api.md:'Design Intent' <-> 'Design Intent'",
        "05_agent_13_reference-api.md:'Key Constraints' <-> 'Key Constraints'",
        "05_agent_13_reference-api.md:'Keywords' <-> 'Related Documents'",
        "05_agent_13_reference-api.md:'Operational Notes' <-> 'Operational Notes'",
        "05_agent_13_reference-api.md:'Related Docs' <-> 'Related Docs'",
        "05_agent_13_reference-api.md:'Responsibility Boundary' <-> 'Responsibility Boundary'",
        # 06_eventbus_03_persistence_schema_and_replay.md
        "06_eventbus_03_persistence_schema_and_replay.md:'Declared Role: Replica' <-> 'Declared Role: Replica'",
        "06_eventbus_03_persistence_schema_and_replay.md:'Idempotency Contract' <-> 'Idempotency Contract'",
        "06_eventbus_03_persistence_schema_and_replay.md:'Keywords' <-> 'Related Documents'",
        # 06_eventbus_04_dlq_offsets_and_delivery_semantics.md
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'ACK Error Responses' <-> 'ACK Error Responses'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'ACK Postconditions' <-> 'ACK Postconditions'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'ACK Preconditions' <-> 'ACK Preconditions'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'ACK Preconditions' <-> 'NACK Preconditions'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'ACK followed by NACK' <-> 'ACK followed by NACK'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'Background Loop Promotion' <-> 'Background Loop Promotion'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'Cleanup Procedure' <-> 'Cleanup Procedure'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'Consumer Identity' <-> 'Consumer Identity'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'Consumer Offset Precedence' <-> 'Consumer Offset Precedence'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'Duplicate NACK Behavior' <-> 'Duplicate NACK Behavior'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'Explicit Ack-only Offset' <-> 'Monotonicity Guarantee'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'Inline Promotion Path' <-> 'Inline Promotion Path'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'Inline Promotion Path' <-> 'Promotion Path'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'JSONL Archive Retention' <-> 'JSONL Archive Retention'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'Last-Event-ID Precedence' <-> 'Last-Event-ID Precedence'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'Monotonicity Guarantee' <-> 'Explicit Ack-only Offset'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'Monotonicity Guarantee' <-> 'Monotonicity Guarantee'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'NACK Error Responses' <-> 'NACK Error Responses'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'NACK Postconditions' <-> 'NACK Postconditions'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'NACK Preconditions' <-> 'ACK Preconditions'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'NACK Preconditions' <-> 'NACK Preconditions'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'NACK followed by ACK' <-> 'NACK followed by ACK'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'Per-Topic Ordering' <-> 'Per-Topic Ordering'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'Promotion Path' <-> 'Inline Promotion Path'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'Queue Overflow Behavior' <-> 'Queue Overflow Behavior'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'Requeue Semantics' <-> 'Requeue Semantics'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'Resume Behavior' <-> 'Resume Behavior'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'Seq-Based Ordering' <-> 'Seq-Based Ordering'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'Slow Consumer Detection' <-> 'Slow Consumer Detection'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'TTL Policy' <-> 'TTL Policy'",
        "06_eventbus_04_dlq_offsets_and_delivery_semantics.md:'since_seq Precedence' <-> 'since_seq Precedence'",
        # adr/ADR-001-workflow-engine-mandatory.md
        "adr/ADR-001-workflow-engine-mandatory.md:'3. 第3の採用理由 — Operability' <-> 'Description'",
        "adr/ADR-001-workflow-engine-mandatory.md:'Problem' <-> '3. 第3の採用理由 — Operability'",
        "adr/ADR-001-workflow-engine-mandatory.md:'Problem' <-> 'Description'",
        # adr/ADR-002-config-isolation.md
        "adr/ADR-002-config-isolation.md:'1. 最重要の採用理由 — Security' <-> 'Disadvantages'",
        "adr/ADR-002-config-isolation.md:'1. 最重要の採用理由 — Security' <-> 'Reconsideration Conditions'",
        "adr/ADR-002-config-isolation.md:'Constraints' <-> '1. 最重要の採用理由 — Security'",
        "adr/ADR-002-config-isolation.md:'Constraints' <-> 'Disadvantages'",
        "adr/ADR-002-config-isolation.md:'Constraints' <-> 'Reconsideration Conditions'",
        "adr/ADR-002-config-isolation.md:'Disadvantages' <-> 'Disadvantages'",
        "adr/ADR-002-config-isolation.md:'Disadvantages' <-> 'Reconsideration Conditions'",
        "adr/ADR-002-config-isolation.md:'Problem' <-> 'Implementation References'",
        "adr/ADR-002-config-isolation.md:'Reconsideration Conditions' <-> 'Disadvantages'",
        # adr/ADR-003-runtime-tool-registry-routing-authority.md
        "adr/ADR-003-runtime-tool-registry-routing-authority.md:'3. 第3の採用理由 — Operability' <-> 'Startup Validation'",
        "adr/ADR-003-runtime-tool-registry-routing-authority.md:'Advantages' <-> 'Description'",
        "adr/ADR-003-runtime-tool-registry-routing-authority.md:'Advantages' <-> 'Reconsideration Conditions'",
        "adr/ADR-003-runtime-tool-registry-routing-authority.md:'Description' <-> 'Advantages'",
        "adr/ADR-003-runtime-tool-registry-routing-authority.md:'Description' <-> 'Description'",
        "adr/ADR-003-runtime-tool-registry-routing-authority.md:'Description' <-> 'Reconsideration Conditions'",
        "adr/ADR-003-runtime-tool-registry-routing-authority.md:'Reconsideration Conditions' <-> 'Description'",
        "adr/ADR-003-runtime-tool-registry-routing-authority.md:'Reconsideration Conditions' <-> 'Reconsideration Conditions'",
        # adr/ADR-004-environment-failure-handling-policy.md
        "adr/ADR-004-environment-failure-handling-policy.md:'Description' <-> 'Reason for Rejection'",
        "adr/ADR-004-environment-failure-handling-policy.md:'Problem' <-> '3. 第3の採用理由 — Predictability'",
        "adr/ADR-004-environment-failure-handling-policy.md:'Reconsideration Conditions' <-> 'Reason for Rejection'",
        # adr/ADR-005-rag-source-derived-index-relationships.md
        "adr/ADR-005-rag-source-derived-index-relationships.md:'Negative Consequences' <-> 'Fail-Fast Conditions'",
        "adr/ADR-005-rag-source-derived-index-relationships.md:'Reason for Rejection' <-> 'Reason for Rejection'",
        # adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md
        "adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md:'Advantages' <-> 'Reconsideration Conditions'",
        # adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md
        "adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md:'Advantages' <-> 'Operational Consequences'",
        "adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md:'Description' <-> 'Reconsideration Conditions'",
        # adr/ADR-008-sqlite-4db-separation.md
        "adr/ADR-008-sqlite-4db-separation.md:'Advantages' <-> 'Reconsideration Conditions'",
        "adr/ADR-008-sqlite-4db-separation.md:'Description' <-> 'Advantages'",
        "adr/ADR-008-sqlite-4db-separation.md:'Description' <-> 'Description'",
        "adr/ADR-008-sqlite-4db-separation.md:'Description' <-> 'Operational Consequences'",
        "adr/ADR-008-sqlite-4db-separation.md:'Description' <-> 'Reconsideration Conditions'",
        "adr/ADR-008-sqlite-4db-separation.md:'Reconsideration Conditions' <-> 'Description'",
        "adr/ADR-008-sqlite-4db-separation.md:'Reconsideration Conditions' <-> 'Operational Consequences'",
        # adr/ADR-009-rag-ft5-text-separation.md
        "adr/ADR-009-rag-ft5-text-separation.md:'2. 第2の採用理由 — LLM Usability' <-> 'Disadvantages'",
        "adr/ADR-009-rag-ft5-text-separation.md:'2. 第2の採用理由 — LLM Usability' <-> 'Reconsideration Conditions'",
        "adr/ADR-009-rag-ft5-text-separation.md:'Description' <-> 'Description'",
        "adr/ADR-009-rag-ft5-text-separation.md:'Description' <-> 'Negative Consequences'",
        "adr/ADR-009-rag-ft5-text-separation.md:'Disadvantages' <-> 'Reconsideration Conditions'",
        # adr/ADR-010-rag-fallback.md
        "adr/ADR-010-rag-fallback.md:'1. 最重要の採用理由 — Availability' <-> 'Description'",
        "adr/ADR-010-rag-fallback.md:'1. 最重要の採用理由 — Availability' <-> 'Fail-Fast Conditions'",
        "adr/ADR-010-rag-fallback.md:'1. 最重要の採用理由 — Availability' <-> 'Positive Consequences'",
        "adr/ADR-010-rag-fallback.md:'Description' <-> 'Description'",
        "adr/ADR-010-rag-fallback.md:'Description' <-> 'Fail-Fast Conditions'",
        "adr/ADR-010-rag-fallback.md:'Description' <-> 'Positive Consequences'",
        "adr/ADR-010-rag-fallback.md:'Positive Consequences' <-> 'Fail-Fast Conditions'",
        "adr/ADR-010-rag-fallback.md:'Problem' <-> '1. 最重要の採用理由 — Availability'",
        "adr/ADR-010-rag-fallback.md:'Problem' <-> 'Description'",
        "adr/ADR-010-rag-fallback.md:'Problem' <-> 'Fail-Fast Conditions'",
        "adr/ADR-010-rag-fallback.md:'Problem' <-> 'Positive Consequences'",
        "adr/ADR-010-rag-fallback.md:'Reason for Rejection' <-> 'Reason for Rejection'",
        # adr/ADR-014-agent-control-plane-responsibility-boundaries.md
        "adr/ADR-014-agent-control-plane-responsibility-boundaries.md:'1. 最重要の採用理由 — Maintainability' <-> 'Negative Consequences'",
        "adr/ADR-014-agent-control-plane-responsibility-boundaries.md:'Disadvantages' <-> 'Startup Validation'",
        # 41_db/active_databases.md
        "41_db/active_databases.md:'Keywords' <-> 'Related Documents'",
        "41_db/active_databases.md:'rag.sqlite' <-> 'session.sqlite'",
        # eventbus/ack-nack-endpoints.md
        "eventbus/ack-nack-endpoints.md:'Bad Request Responses' <-> 'Bad Request Responses'",
        "eventbus/ack-nack-endpoints.md:'Forbidden Response' <-> 'Forbidden Response'",
        "eventbus/ack-nack-endpoints.md:'Not Found Response' <-> 'Not Found Response'",
        "eventbus/ack-nack-endpoints.md:'Related Documents' <-> 'Keywords'",
        "eventbus/ack-nack-endpoints.md:'Success Response' <-> 'Success Response'",
        # eventbus/dlq-endpoint.md
        "eventbus/dlq-endpoint.md:'Related Documents' <-> 'Keywords'",
        "eventbus/dlq-endpoint.md:'Success Response' <-> 'Success Response'",
        # eventbus/health-endpoint.md
        "eventbus/health-endpoint.md:'Related Documents' <-> 'Keywords'",
        # eventbus/replay-endpoint.md
        "eventbus/replay-endpoint.md:'Related Documents' <-> 'Keywords'",
    ]
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
_DOCS_DIR = _ROOT_DIR / "docs"
_KNOWN_DEFECT_PATH = (
    _DOCS_DIR
    / "40_shared"
    / "90_shared_02_02_types_and_protocols-tool-and-execution-dto.md"
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
_DOCS_DIR = _ROOT_DIR / "docs"
_KNOWN_DEFECT_PATH = (
    _DOCS_DIR
    / "40_shared"
    / "90_shared_02_02_types_and_protocols-tool-and-execution-dto.md"
)


def _make_doc_file(
    content: str, path: Path | None = None, tmp_name: str = ".tmp_test_doc.md"
) -> object:
    """Construct an object that behaves like DocFile for check functions."""

    class FakeDocFile:
        def __init__(self, content: str, path: Path | None = None) -> None:
            self.lines = content.splitlines()
            if path is not None:
                self.path = path
                self.rel_path = str(path.relative_to(_ROOT_DIR / "docs"))
            else:
                tmp = _ROOT_DIR / tmp_name
                tmp.write_text(content, encoding="utf-8")
                self.path = tmp
                self.rel_path = tmp_name

    return FakeDocFile(content, path)


# ---------------------------------------------------------------------------
# Tests for _compute_section_similarity
# ---------------------------------------------------------------------------


class TestComputeSectionSimilarity:
    def test_identical_sections(self):
        text = "hello world foo bar baz"
        assert _compute_section_similarity(text, text) is True

    def test_no_overlap(self):
        assert _compute_section_similarity("hello world", "foo bar baz") is False

    def test_partial_overlap_below_threshold(self):
        # Only 1 word overlap out of ~6 unique words → Jaccard ≈ 0.14 < 0.85
        assert (
            _compute_section_similarity(
                "hello world foo bar",
                "hello baz qux quux",
            )
            is False
        )

    def test_custom_threshold(self):
        # With threshold=0.1, partial overlap should pass
        assert (
            _compute_section_similarity(
                "hello world foo bar",
                "hello baz qux quux",
                threshold=0.1,
            )
            is True
        )

    def test_empty_body_returns_false(self):
        assert _compute_section_similarity("", "some text") is False
        assert _compute_section_similarity("some text", "") is False

    def test_code_blocks_are_stripped(self):
        text_with_code = "before ```code\nprint('hello')\n```\nafter"
        text_without_code = "before after"
        result = _compute_section_similarity(text_with_code, text_without_code)
        assert result is True


# ---------------------------------------------------------------------------
# Tests for alphabetic-suffix duplicate-heading detection
# ---------------------------------------------------------------------------


class TestAlphabeticSuffixDuplicateHeading:
    def test_true_positive_same_base_number(self):
        """Two headings with same base number and same level → expect Issue."""
        content = "# Title\n\n## 7a. First section\n\nSome text.\n\n## 7b. Second section\n\nMore text."
        doc = _make_doc_file(content)
        issues = check_duplicate_heading_numbers(_DOCS_DIR, [doc])
        assert len(issues) == 1
        assert "7a" in str(issues[0].message) or "7b" in str(issues[0].message)

    def test_true_positive_known_defect_case(self):
        """The known ## 7c. duplicate in docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md → expect Issue."""
        if not _KNOWN_DEFECT_PATH.exists():
            pytest.skip(f"Test file not found: {_KNOWN_DEFECT_PATH}")
        content = _KNOWN_DEFECT_PATH.read_text(encoding="utf-8")
        doc = _make_doc_file(content, path=_KNOWN_DEFECT_PATH)
        issues = check_duplicate_heading_numbers(_DOCS_DIR, [doc])
        assert len(issues) >= 1
        assert any("7c" in str(issue.message) for issue in issues)

    def test_false_positive_different_base_numbers(self):
        """Different base numbers at same level → no Issue."""
        content = "# Title\n\n## 7a. First section\n\nText A.\n\n## 8b. Second section\n\nText B."
        doc = _make_doc_file(content)
        issues = check_duplicate_heading_numbers(_DOCS_DIR, [doc])
        assert len(issues) == 0

    def test_false_positive_numeric_subsections(self):
        """Numeric subsections like 2.1, 2.2 → no Issue."""
        content = "# Title\n\n## 2.1 First subsection\n\nText A.\n\n## 2.2 Second subsection\n\nText B."
        doc = _make_doc_file(content)
        issues = check_duplicate_heading_numbers(_DOCS_DIR, [doc])
        assert len(issues) == 0

    def test_false_positive_different_levels(self):
        """Same heading number at different levels → no Issue."""
        content = "# Title\n\n## 7a. Level 2 section\n\nText A.\n\n####### 7a. Level 7 section\n\nText B."
        doc = _make_doc_file(content)
        issues = check_duplicate_heading_numbers(_DOCS_DIR, [doc])
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# Tests for content-similarity check
# ---------------------------------------------------------------------------


class TestContentSimilarity:
    def test_true_positive_overlapping_sections(self):
        """Two sections with heavily overlapping body text → expect Issue."""
        common_text = (
            "This is boilerplate content that appears in many documents. "
            "It describes the purpose and scope of the section."
        )
        content = f"# Title\n\n## Section One\n\n{common_text}\n\n## Section Two\n\n{common_text}"
        doc = _make_doc_file(content)
        issues = check_content_similarity(_DOCS_DIR, [doc])
        assert len(issues) >= 1
        assert any("similarity" in issue.message.lower() for issue in issues)

    def test_false_positive_templated_distinct_sections(self):
        """Two templated-but-distinct sections → no Issue."""
        verification_a = (
            "Verification: This item has been verified against the current source code."
        )
        verification_b = "Verification: This item has been validated against the latest documentation updates."
        content = f"# Title\n\n## Verification A\n\n{verification_a}\n\n## Verification B\n\n{verification_b}"
        doc = _make_doc_file(content)
        issues = check_content_similarity(_DOCS_DIR, [doc])
        assert len(issues) == 0

    def test_false_positive_short_unique_sections(self):
        """Short sections with minimal overlap → no Issue."""
        content = "# Title\n\n## Short A\n\nA.\n\n## Short B\n\nB."
        doc = _make_doc_file(content)
        issues = check_content_similarity(_DOCS_DIR, [doc])
        assert len(issues) == 0

    def test_content_similarity_across_multiple_sections(self):
        """Three sections where two share heavy overlap → expect one Issue."""
        shared = "Shared content between sections one and three."
        content = f"# Title\n\n## Section One\n\n{shared}\n\n## Section Two\n\nUnique content here.\n\n## Section Three\n\n{shared}"
        doc = _make_doc_file(content)
        issues = check_content_similarity(_DOCS_DIR, [doc])
        assert len(issues) >= 1


class TestContentSimilarityCrossFile:
    def test_true_positive_cross_file_overlap(self):
        """Two different documents sharing a near-duplicate section body → expect cross-file Issue."""
        common_text = (
            "This is boilerplate content that appears in many documents. "
            "It describes the purpose and scope of the section."
        )
        content_a = f"# Title A\n\n## Section One\n\n{common_text}"
        content_b = f"# Title B\n\n## Section Two\n\n{common_text}"
        doc_a = _make_doc_file(content_a, tmp_name=".tmp_test_doc_a.md")
        doc_b = _make_doc_file(content_b, tmp_name=".tmp_test_doc_b.md")
        try:
            issues = check_content_similarity(_DOCS_DIR, [doc_a, doc_b])
            assert len(issues) >= 1
            assert any(
                doc_a.rel_path in issue.message and doc_b.rel_path in issue.message
                for issue in issues
            )
        finally:
            (_ROOT_DIR / ".tmp_test_doc_a.md").unlink(missing_ok=True)
            (_ROOT_DIR / ".tmp_test_doc_b.md").unlink(missing_ok=True)

    def test_false_positive_cross_file_unrelated(self):
        """Two different documents with unrelated content → no cross-file Issue."""
        content_a = (
            "# Title A\n\n## Section One\n\nCompletely unrelated discussion of widgets."
        )
        content_b = (
            "# Title B\n\n## Section Two\n\nA totally different discussion of gadgets."
        )
        doc_a = _make_doc_file(content_a, tmp_name=".tmp_test_doc_a.md")
        doc_b = _make_doc_file(content_b, tmp_name=".tmp_test_doc_b.md")
        try:
            issues = check_content_similarity(_DOCS_DIR, [doc_a, doc_b])
            assert issues == []
        finally:
            (_ROOT_DIR / ".tmp_test_doc_a.md").unlink(missing_ok=True)
            (_ROOT_DIR / ".tmp_test_doc_b.md").unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


class TestIntegrationKnownDefect:
    def test_run_checker_against_known_duplicate(self):
        """Run checker against the known defect file → expect '7c' in output."""
        if not _KNOWN_DEFECT_PATH.exists():
            pytest.skip(f"Test file not found: {_KNOWN_DEFECT_PATH}")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.check_docs_quality",
                "--only",
                "duplicate_heading_numbers",
                str(_KNOWN_DEFECT_PATH),
            ],
            capture_output=True,
            text=True,
            cwd=str(_ROOT_DIR),
        )

        # Warnings don't trigger non-zero exit; check output content instead
        assert "7c" in result.stdout or "7c" in result.stderr


class TestRegressionFullDocsTree:
    def test_no_new_false_positives_on_full_docs_tree(self):
        """Run checker against full docs/ tree → confirm no false-positive noise on numeric subsections."""
        if not _DOCS_DIR.exists():
            pytest.skip(f"Docs directory not found: {_DOCS_DIR}")

        result = subprocess.run(
            [sys.executable, "-m", "tools.check_docs_quality"],
            capture_output=True,
            text=True,
            cwd=str(_ROOT_DIR),
        )

        lines = result.stdout.split("\n") + result.stderr.split("\n")
        for line in lines:
            if ".1" in line or ".2" in line or ".3" in line:
                assert "duplicate" not in line.lower(), (
                    f"False positive on numeric subsection: {line}"
                )

    def test_cross_file_duplication_detected_on_full_docs_tree(self):
        """Run the extended checker against the full docs/ tree → confirm the
        within-file finding count is unchanged and the known governance_01/
        governance_04 duplication is now detected cross-file."""
        if not _DOCS_DIR.exists():
            pytest.skip(f"Docs directory not found: {_DOCS_DIR}")

        result = subprocess.run(
            [sys.executable, "-m", "tools.check_docs_quality"],
            capture_output=True,
            text=True,
            cwd=str(_ROOT_DIR),
        )
        output = result.stdout + result.stderr

        current_pairs: set[str] = set()
        for line in output.split("\n"):
            m = re.search(
                r"\[WARNING\] ([^:]+):\d+ — Content similarity detected between "
                r"sections '([^']+)' and '([^']+)'",
                line,
            )
            if m:
                file_path = m.group(1)
                section_a = m.group(2)
                section_b = m.group(3)
                current_pairs.add(
                    f"{file_path}:{repr(section_a)} <-> {repr(section_b)}"
                )

        assert current_pairs == EXPECTED_WITHIN_FILE_PAIRS, (
            f"Within-file content-similarity pairs changed:\n"
            f"Added: {current_pairs - EXPECTED_WITHIN_FILE_PAIRS}\n"
            f"Removed: {EXPECTED_WITHIN_FILE_PAIRS - current_pairs}"
        )

        assert (
            "00_governance_01_documentation-policy.md" in output
            and "00_governance_04_documentation-checks.md" in output
        ), (
            "Expected a cross-file finding between the known governance_01/governance_04 duplication"
        )
