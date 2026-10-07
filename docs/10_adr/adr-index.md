---
title: "ADR Index"
area: governance
tags:
  - governance
  - adr
related:
  - governance_01_documentation-policy.md
  - governance_04_documentation-checks.md
---

# ADR Index

## Purpose

Canonical list of all Architecture Decision Records (ADRs): current status,
dependency relationships, and invariant verification status. ADR status
definitions, ID format rules, and section header conventions are defined once in
`governance_01_documentation-policy.md` — not repeated here.

## Known Deviations

This index records no deviations of its own. Open deviations are recorded in the `## Known Deviations` section of the individual ADR that owns them (for example ADR-006).

## ADR List

| ID | Title | Status | File |
|----|-------|--------|------|
| ADR-001 | Mandatory Workflow Engine | Accepted | `10_adr/ADR-001-workflow-engine-mandatory.md` |
| ADR-002 | Per-Process Configuration Ownership and Config Isolation | Accepted | `10_adr/ADR-002-config-isolation.md` |
| ADR-003 | RuntimeToolRegistry as the Sole Routing Authority | Accepted | `10_adr/ADR-003-runtime-tool-registry-routing-authority.md` |
| ADR-004 | Failure Handling Policy Across Environments | Accepted | `10_adr/ADR-004-environment-failure-handling-policy.md` |
| ADR-005 | Relationship Between RAG Canonical Data and Derived Indexes | Accepted | `10_adr/ADR-005-rag-source-derived-index-relationships.md` |
| ADR-006 | EventBus SQLite Persistence and SSE Delivery | Accepted | `10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` |
| ADR-007 | Adoption of HTTP MCP and Non-Support of stdio | Accepted | `10_adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` |
| ADR-008 | Separating SQLite into Four Databases | Accepted | `10_adr/ADR-008-sqlite-4db-separation.md` |
| ADR-009 | Separating RAG FTS5 Search Text from LLM Presentation Text | Accepted | `10_adr/ADR-009-rag-ft5-text-separation.md` |
| ADR-010 | In-Process Fallback When External RAG Execution Fails | Accepted | `10_adr/ADR-010-rag-fallback.md` |
| ADR-012 | Git MCP Server-Side Write Enforcement | Accepted | `10_adr/ADR-012-git-mcp-server-side-write-enforcement.md` |
| ADR-013 | EventBus Authentication and Authorization | Accepted | `10_adr/ADR-013-eventbus-authentication-authorization.md` |
| ADR-014 | Responsibility Boundaries of the Agent Control Plane | Accepted | `10_adr/ADR-014-agent-control-plane-responsibility-boundaries.md` |
| ADR-015 | Reference Document Class Disposition | Accepted | `10_adr/ADR-015-reference-document-class-disposition.md` |

## ADR Dependency Graph

`A → B` means that ADR-A lists ADR-B under its Related ADRs and refers to it in its body.
ADR-012 and ADR-015 reference no other ADR.

```text
ADR-001 → ADR-004, ADR-014
ADR-002 → ADR-001, ADR-004
ADR-003 → ADR-001, ADR-002, ADR-004
ADR-004 → ADR-001, ADR-002, ADR-003, ADR-010
ADR-005 → ADR-002, ADR-004
ADR-006 → ADR-002, ADR-004, ADR-013
ADR-007 → ADR-002, ADR-004
ADR-008 → ADR-002, ADR-004, ADR-005, ADR-006, ADR-013
ADR-009 → ADR-002, ADR-004, ADR-005
ADR-010 → ADR-002, ADR-004, ADR-005
ADR-013 → ADR-002, ADR-006
ADR-014 → ADR-001
```

### Intentional Circular References

The following bidirectional references are intentional, not defects:

- ADR-003 ↔ ADR-004: ADR-004 defines the failure-classification contract; ADR-003 remains the authority for RuntimeToolRegistry, Tool ownership, and Routing.
- ADR-004 ↔ ADR-010: ADR-004 defines the failure-classification contract; ADR-010 is the sole Fallback it permits.
- ADR-006 ↔ ADR-013: ADR-013 owns EventBus authentication and authorization; ADR-006 owns persistence and SSE delivery.

Each pair splits ownership by topic, so neither ADR's decision depends on the other's
being changed first. The prohibition on circular dependencies in
`governance_05_change-impact-and-dependency-graphs.md` applies to the area nodes of that
graph (Agent, MCP, RAG, EventBus, Shared/DB), not to this ADR reference graph.

## ADR Invariant Verification Matrix

This matrix lists the invariants that need automated verification at CI or startup, plus selected others, and records how each is verified, where it runs and what happens if it fails. It is not exhaustive: every ADR's own `## Verification` section covers all of that ADR's invariants. Rows are identified by the ADR-local invariant ID (`ADR-NNN INV-NN`); there is no global numbering.

A row whose Verification Status is "Not verified" is Non-Blocking, because a gate cannot be enforced without a verification.

| Invariant | Statement | Type | Timing | Gate | Verification Status |
|-----------|-----------|------|--------|------|---------------------|
| ADR-001 INV-01 | Workflow definition mandatory; missing workflow raises RuntimeError | Unit Test | CI | Blocking | Confirmed (`tests/agent/test_startup_workflow_preflight.py::test_aborts_on_missing_workflow_definition`, passing) |
| ADR-001 INV-08 | Stage execution is idempotent via a `{task_id}:{stage_id}:{attempt}` deterministic key; duplicate start within the same attempt is rejected by `begin_stage_if_new()` | Unit Test | CI | Blocking | Confirmed (`tests/agent/workflow/test_workflow_stage_persistence.py::test_begin_stage_if_new_idempotent`, passing) |
| ADR-002 INV-01, INV-02 | Config isolation enforced between environments | Unit Test | CI | Blocking | Confirmed (`tests/shared/test_config_loader.py::TestRestrictToIsolation`) |
| ADR-003 INV-02 | RuntimeToolRegistry is the sole routing authority | Unit Test | CI | Blocking | Confirmed (`tests/shared/test_route_resolver.py::TestRoutingSourceIsolation`) |
| ADR-004 INV-01, INV-02 | The system uses a single common failure-handling policy across all environments; environment names do not weaken safety, validation, authentication, authorization, approval, routing, or data-integrity controls | Manual Review | Startup | Deployment Blocking | Manual review; no environment-conditional safety-control branching exists (confirmed by repository search); no dedicated cross-cutting test |
| ADR-004 INV-07, INV-10 | Safety or integrity failures (auth, allowlist, safety-tier, secrets, Config Isolation, approval-control establishment, RuntimeToolRegistry init, duplicate tool ownership) are Fail-Fast at startup (Decision #14) or Fail-Closed at execution (Decision #15), and are never converted into partial availability | Startup Validation | Startup | Deployment Blocking | Confirmed in code structure (`scripts/agent/startup.py` routes these checks through unconditional FATAL paths); no cross-cutting test |
| ADR-004 INV-08 | Required-component unavailability prevents startup | Startup Validation | Startup | Deployment Blocking | Confirmed (`tests/agent/services/test_mcp_tool_discovery.py::TestDiscoverAllUnreachableServers`, passing; the unified `required` field drives startup behavior) |
| ADR-004 INV-09 | A non-required component's availability failure permits startup continuation with partial availability; the component is disabled and its capabilities excluded from executable exposure | Startup Validation | Startup | Deployment Blocking | Confirmed (`tests/agent/services/test_mcp_tool_discovery.py::TestDiscoverAllUnreachableServers`, passing; `required=False` permits startup continuation) |
| ADR-004 INV-14 | Unknown component criticality must not be assumed non-required; it must be treated as an unresolved design or configuration error (ADR-004 Decision #12) | Startup Validation | Startup | Deployment Blocking | Confirmed by structure (ADR-004 Decision #12 prohibits assuming non-required when criticality is unknown; the unified `required` field enforces this) |
| ADR-004 INV-15, INV-16 | Fallback occurs only where another Accepted ADR explicitly defines it; ADR-010 remains the sole authority for RAG fallback | Integration Test | CI | Blocking | Confirmed — structural/code-inspection based verification sufficient; no dedicated test needed per ADR-004 Verification section |
| ADR-005 INV-02 | `chunks_vec` deleted before `documents` | Unit Test | CI | Blocking | Confirmed (`tests/rag/ingestion/test_delete_chain.py::TestDeleteDocumentChain::test_delete_chunks_vec_before_documents`, passing) |
| ADR-006 INV-02 | No success response before event persistence | Integration Test | CI | Non-Blocking | Not verified: no test injects a SQLite write failure on `POST /publish` (only `tests/eventbus/test_eventbus_publish_contract.py::TestPublishContract::test_publish_succeeds_if_jsonl_append_fails` covers the converse) |
| ADR-006 INV-05, INV-09 | EventBus offsets strictly monotonic | Unit Test | CI | Blocking | Confirmed (`tests/eventbus/test_eventbus_offsets.py::TestConsumerOffsetsTable::test_offset_does_not_regress_on_older_seq`, `tests/eventbus/test_eventbus_offsets.py::TestSqliteOffsetMonotonicity::test_older_seq_cannot_move_offset_backward`) |
| ADR-006 INV-16 | `ack_event_for_consumer()`'s per-consumer delivery-state UPSERT and offset-progression commit atomically in one SQLite transaction; a failure in either rolls back both | Unit Test | CI | Blocking | Confirmed (`tests/eventbus/test_eventbus_crash_ack.py::TestCrashBeforeAck::test_offset_write_failure_after_delivery_state`, passing) |
| ADR-007 INV-06 | No stdio transport usage | Unit Test | CI | Blocking | Confirmed (`tests/shared/test_mcp_config.py::TestMcpServerConfigValidation::test_stdio_transport_rejected`, passing) |
| ADR-007 INV-11 | `McpServerHealthState`'s state names (`HEALTHY`/`DEGRADED`/`UNAVAILABLE`/`HALF_OPEN`) are not silently renamed, since callers outside `scripts/shared/mcp_health.py` compare against them by exact value | Unit Test | CI | Blocking | Confirmed (`tests/shared/test_mcp_health.py`, passing) |
| ADR-008 INV-01 to INV-05 | SQLite 4DB separation maintained | Operational Procedure | Pre-deploy | Deployment Blocking | Confirmed (`DbTarget` enum); needs operational procedure |
| ADR-009 INV-07 | FTS5 rebuild rules followed | Integration Test | CI | Blocking | Confirmed (`tests/rag/test_fts_sync.py::TestFtsTriggerSync::test_fts_trigger_and_manual_rebuild_use_same_text_selection_rule`, `tests/rag/test_fts_sync.py::TestFtsTriggerSync::test_rebuild_fts_preserves_normalized_content_semantics`, `tests/agent/services/test_rag_index_integrity.py::test_rebuild_fts_uses_coalesce`) |
| ADR-009 INV-10 | `normalized_content` must not appear in LLM output | Unit Test | CI | Blocking | Confirmed (`tests/rag/test_rag_pipeline.py::TestFormatChunksDesign2::test_real_normalized_content_attribute_excluded`, passing) |
| ADR-010 INV-03 | No local fallback on normal empty RAG result | Integration Test | CI | Blocking | Confirmed (`remote_empty` → `HttpResultKind.EMPTY`; `tests/rag/test_rag_http_mode.py::test_remote_empty_does_not_trigger_in_process`, passing) |
| ADR-010 INV-04 | No local fallback on RAG 401/403 | Integration Test | CI | Non-Blocking | Not verified at caller level: `tests/rag/test_rag_pipeline_service.py` shows `call_rag_service()` returns no result for 401/403, but the caller falls back (RAG-001 in `governance_03_issue-and-uncertainty-management.md`) |
| ADR-012 INV-01 to INV-04 | Git MCP write operations enforced server-side | Unit/Integration Test | CI | Blocking | Confirmed (`tests/mcp_servers/git/`, passing, covering INV-01 through INV-04) |
| ADR-014 INV-01 | Non-WorkflowEngine components (Orchestrator, LlmTurnExecutor, ToolExecutor) do not decide persistent Task/Attempt state, stage transitions, retries, or approval | Manual Review | Code Review | Non-Blocking | Confirmed by code inspection (`Orchestrator.handle_turn()` delegates to `WorkflowEngineAdapter.execute_turn()`); no automated test |
| ADR-014 INV-02 | `LlmTurnExecutor` instance construction is centralized in the component that drives the LLM/tool-call loop; no other component holds an unused or duplicate instance | Unit Test | CI | Non-Blocking | Not verified: no regression test (AGENT-002 in `governance_03_issue-and-uncertainty-management.md`); code inspection of `Orchestrator.__init__` in `scripts/agent/orchestrator.py` |
| ADR-014 INV-03 | MCP Server-side technical safety checks (allowlist, path validation, sandboxing, resource limits, argument validation) are not duplicated or re-implemented in Orchestrator/ToolExecutor layers | Manual Review | Code Review | Non-Blocking | Confirmed by code inspection (`scripts/mcp_servers/tool_validators.py`, `scripts/mcp_servers/shell/shell_service.py`); no automated test |

**Note**: "Type" reflects the intended verification method, not whether a test currently exists; the Verification Status column states what exists.

### Pipeline Mapping Summary

| Pipeline Stage | Invariants Covered |
|----------------|-------------------|
| CI (pull request) | ADR-001 INV-01, ADR-001 INV-08, ADR-002 INV-01 and INV-02, ADR-003 INV-02, ADR-005 INV-02, ADR-006 INV-02, INV-05, INV-09 and INV-16, ADR-007 INV-06 and INV-11, ADR-009 INV-07 and INV-10, ADR-010 INV-03 and INV-04, ADR-012 INV-01 to INV-04, ADR-004 INV-15 and INV-16 |
| Startup validation | ADR-004 INV-01, INV-02, INV-07, INV-08, INV-09, INV-10 and INV-14 |
| Pre-deployment validation | ADR-008 INV-01 to INV-05 |
| Operations (runtime monitoring) | ADR-012 INV-01 to INV-04 |
| Manual Review (code review) | ADR-014 INV-01, INV-02 and INV-03 |

## Keywords

- adr
- architecture decision record
- invariant
- verification matrix
- dependency graph
