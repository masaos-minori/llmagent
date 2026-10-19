---
title: "ADR Index"
area: governance
tags:
  - governance
  - adr
related:
  - governance_01_documentation-policy.md
  - governance_04_documentation-checks.md
  - adr_02_02_001_agent-workflow-engine-mandatory.md
  - adr_02_01_002_platform-config-isolation.md
  - adr_02_02_003_agent-runtime-tool-registry-routing-authority.md
  - adr_02_01_004_platform-environment-failure-handling-policy.md
  - adr_02_06_005_rag-source-derived-index-relationships.md
  - adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md
  - adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md
  - adr_02_05_008_db-sqlite-4db-separation.md
  - adr_02_06_009_rag-fts5-text-separation.md
  - adr_02_06_010_rag-fallback.md
  - adr_02_03_012_mcp-git-server-side-write-enforcement.md
  - adr_02_04_013_eventbus-authentication-authorization.md
  - adr_02_02_014_agent-control-plane-responsibility-boundaries.md
  - adr_02_07_015_docs-reference-document-class-disposition.md
  - governance_03_issue-and-uncertainty-management.md
  - governance_05_change-impact-and-dependency-graphs.md
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

| ID | Title | Status | Group | File |
|----|-------|--------|-------|------|
| ADR-001 | Mandatory Workflow Engine | Accepted | 02 agent | `10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` |
| ADR-002 | Per-Process Configuration Ownership and Config Isolation | Accepted | 01 platform | `10_adr/adr_02_01_002_platform-config-isolation.md` |
| ADR-003 | RuntimeToolRegistry as the Sole Routing Authority | Accepted | 02 agent | `10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` |
| ADR-004 | Failure Handling Policy Across Environments | Accepted | 01 platform | `10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` |
| ADR-005 | Relationship Between RAG Canonical Data and Derived Indexes | Accepted | 06 rag | `10_adr/adr_02_06_005_rag-source-derived-index-relationships.md` |
| ADR-006 | EventBus SQLite Persistence and SSE Delivery | Accepted | 04 eventbus | `10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` |
| ADR-007 | Adoption of HTTP MCP and Non-Support of stdio | Accepted | 03 mcp | `10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` |
| ADR-008 | Separating SQLite into Four Databases | Accepted | 05 db | `10_adr/adr_02_05_008_db-sqlite-4db-separation.md` |
| ADR-009 | Separating RAG FTS5 Search Text from LLM Presentation Text | Accepted | 06 rag | `10_adr/adr_02_06_009_rag-fts5-text-separation.md` |
| ADR-010 | In-Process Fallback When External RAG Execution Fails | Accepted | 06 rag | `10_adr/adr_02_06_010_rag-fallback.md` |
| ADR-012 | Git MCP Server-Side Write Enforcement | Accepted | 03 mcp | `10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md` |
| ADR-013 | EventBus Authentication and Authorization | Accepted | 04 eventbus | `10_adr/adr_02_04_013_eventbus-authentication-authorization.md` |
| ADR-014 | Responsibility Boundaries of the Agent Control Plane | Accepted | 02 agent | `10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md` |
| ADR-015 | Reference Document Class Disposition | Accepted | 07 docs | `10_adr/adr_02_07_015_docs-reference-document-class-disposition.md` |

The number ADR-011 is unassigned: no ADR file carries it, and it is not referenced as a dependency by any ADR in this list.

## ADR Dependency Graph

`A → B` means that ADR-A lists ADR-B under its Related ADRs and refers to it in its body.
ADR-015 references no other ADR.

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
ADR-012 → ADR-007
ADR-013 → ADR-002, ADR-006
ADR-014 → ADR-001
```

### Intentional Circular References

The following bidirectional references are intentional, not defects:

- ADR-001 ↔ ADR-004: ADR-004 classifies a missing or invalid workflow as a Fail-Fast failure; ADR-001 owns the mandatory workflow decision.
- ADR-001 ↔ ADR-014: ADR-014 extends the responsibility boundaries to the components other than the Workflow Engine; ADR-001 owns the Workflow Engine's mandatoriness.
- ADR-002 ↔ ADR-004: ADR-004 classifies a Config Isolation violation as a Fail-Fast failure; ADR-002 owns the isolation decision.
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
| ADR-001 INV-01 | Workflow definition mandatory; a missing or invalid workflow raises RuntimeError | Unit Test | CI | Blocking | Confirmed (`tests/agent/test_startup_workflow_preflight.py::TestComponentInitializerWorkflowPreflight::test_aborts_on_missing_workflow_definition`; `tests/agent/test_orchestrator.py::TestWorkflowLoadFailureIsFatal`, passing) |
| ADR-001 INV-08 | Stage execution is idempotent via a `{task_id}:{stage_id}:{attempt}` deterministic key; duplicate start within the same attempt is rejected by `begin_stage_if_new()` | Unit Test | CI | Blocking | Confirmed (`tests/agent/workflow/test_workflow_stage_persistence.py::test_begin_stage_if_new_idempotent`, passing) |
| ADR-001 INV-10 | A workflow definition that contains the `require_approval` key is rejected at load time (the workflow has no approval stage) | Unit Test | CI | Blocking | Confirmed (`tests/agent/workflow/test_workflow_loader.py::TestRequireApprovalKeyRejected`, passing) |
| ADR-001 INV-11 | Every tool-level approval decision is recorded as a `tool_approval` audit event with the `workflow_id` and the turn ID in `task_id` | Unit Test | CI | Blocking | Confirmed (`tests/agent/test_tool_audit.py::TestAuditApprovalInv11`, passing) |
| ADR-002 INV-01, INV-02 | Config isolation enforced between processes | Unit Test | CI | Blocking | Confirmed (`tests/shared/test_config_loader.py::TestRestrictToIsolation`; the `agent-mcp-config-models` import-linter contract now covers every Agent module because its `ignore_imports` grant was removed) |
| ADR-002 INV-01, INV-02 and ADR-004 INV-07, INV-10 | Each MCP server validates its own configuration at import, publishes the resulting Security Posture on `/health`, and refuses to bind HTTP when one of its checks is `FAILED`; the Agent aborts startup on the same posture through `check_readiness()` | Startup Validation | Startup | Deployment Blocking | Confirmed (`tests/agent/test_mcp_health_posture.py`, `tests/mcp_servers/`, passing) |
| ADR-003 INV-02 | RuntimeToolRegistry is the sole routing authority | Unit Test | CI | Blocking | Confirmed (`tests/shared/test_route_resolver.py::TestRoutingSourceIsolation`) |
| ADR-003 INV-03 | Approval and audit operation types do not classify a registered write tool as READ, and a write-flag mismatch against the static tool sets is reported at startup | Unit Test | CI | Blocking | Confirmed (`tests/agent/test_tool_policy_comprehensive.py::TestClassifyOperationType`, `tests/agent/services/test_mcp_tool_discovery.py::TestWriteClassificationFinding`, passing) |
| ADR-004 INV-01, INV-02 | The system uses a single common failure-handling policy across all environments; environment names do not weaken safety, validation, authentication, authorization, approval, routing, or data-integrity controls | Manual Review | Startup | Deployment Blocking | Manual review; no environment-conditional safety-control branching exists (Strongly implied by code — repository search of `scripts/`); no dedicated cross-cutting test |
| ADR-004 INV-07, INV-10 | Safety or integrity failures (auth, allowlist, safety-tier, secrets, Config Isolation, approval-control establishment, RuntimeToolRegistry init, duplicate tool ownership) are Fail-Fast at startup (Decision #14) or Fail-Closed at execution (Decision #15), and are never converted into partial availability | Startup Validation | Startup | Deployment Blocking | By phase — Fail-Fast at startup confirmed for Allowlist, Safety Tier, Config Isolation (strict keys), required DB connection, RuntimeToolRegistry init via the startup validation pipeline and `ProductionConfigValidator.validate()`; an allowlist or authentication failure now reaches startup as a server posture `FAILED` result through `check_readiness()` (`tests/agent/test_failure_handling_policy_cross_cutting.py`, passing); Fail-Closed at runtime confirmed for unknown/disabled Tool, ambiguous ownership, invalid args, missing approval, auth/authz, resource-scope, allowlist. The safety-tier, strict-key and `allowed_tools` checks are covered (`tests/agent/test_production_config_validator.py`, passing); no test covers every listed failure class (authentication, secrets, Config Isolation, approval-control establishment, duplicate tool ownership) as a single cross-cutting guarantee. No class permits continued partial availability |
| ADR-004 INV-08 | Required-component unavailability prevents startup | Startup Validation | Startup | Deployment Blocking | Confirmed (`tests/agent/services/test_mcp_tool_discovery.py::TestDiscoverAllUnreachableServers`, passing; the unified `required` field drives startup behavior) |
| ADR-004 INV-09 | A non-required component's availability failure permits startup continuation with partial availability; the component is disabled and its capabilities excluded from executable exposure | Startup Validation | Startup | Deployment Blocking | Confirmed (`tests/agent/services/test_mcp_tool_discovery.py::TestDiscoverAllUnreachableServers`, passing; `required=False` permits startup continuation on the discovery path; the subprocess spawn path is covered by ADR-004 Exceptions and `tests/shared/test_mcp_config.py::TestMcpServerConfigValidation::test_subprocess_non_required_rejected`) |
| ADR-004 INV-14 | Unknown component criticality must not be assumed non-required; it must be treated as an unresolved design or configuration error (ADR-004 Decision #12) | Startup Validation | Startup | Deployment Blocking | Confirmed (`tests/shared/test_mcp_config.py::TestRequiredDefault::test_required_default_true_on_direct_construction`, `tests/shared/test_mcp_config.py::TestRequiredDefault::test_required_default_true_from_toml_absent_key`, passing; an unspecified `required` defaults to true) |
| ADR-004 INV-15, INV-16 | Fallback occurs only where another Accepted ADR explicitly defines it; ADR-010 remains the sole authority for RAG fallback | Manual Review | Release review | Non-Blocking | Manual-release-review decision: automated fallback-path detector rejected because "fallback" appears as defensive default-value/best-effort patterns across production sources, so a pattern-based check yields unmanageable false positives; only ADR-010 marker uniqueness is automated (`tests/rag/test_rag_pipeline_service.py::TestFallbackMarkerLockGuard`). Manual fallback-audit retained as the controlling gate |
| ADR-005 INV-02 | `chunks_vec` deleted before `documents` | Unit Test | CI | Blocking | Confirmed (`tests/rag/ingestion/test_delete_chain.py::TestDeleteDocumentChain::test_delete_chunks_vec_before_documents`, passing) |
| ADR-006 INV-02 | No success response before event persistence | Integration Test | CI | Blocking | Confirmed (`tests/eventbus/test_eventbus_publish.py::test_publish_sqlite_write_failure_reports_failure_without_side_effects`, passing; SQLite insert and commit failures are injected into `POST /publish`, and the HTTP response, committed SQLite state, JSONL archive, and broker notification are verified together; the converse is covered by `tests/eventbus/test_eventbus_publish_contract.py::TestPublishContract::test_publish_succeeds_if_jsonl_append_fails`) |
| ADR-006 INV-05, INV-09 | EventBus offsets strictly monotonic | Unit Test | CI | Blocking | Confirmed (`tests/eventbus/test_eventbus_offsets.py::TestConsumerOffsetsTable::test_offset_does_not_regress_on_older_seq`, `tests/eventbus/test_eventbus_offsets.py::TestSqliteOffsetMonotonicity::test_older_seq_cannot_move_offset_backward`) |
| ADR-006 INV-16 | `ack_event_for_consumer()`'s per-consumer delivery-state UPSERT and offset-progression commit atomically in one SQLite transaction; a failure in either rolls back both | Unit Test | CI | Blocking | Confirmed (`tests/eventbus/test_eventbus_crash_ack.py::TestCrashBeforeAck::test_offset_write_failure_after_delivery_state`, passing) |
| ADR-007 INV-06 | No stdio transport usage | Unit Test | CI | Blocking | Confirmed (`tests/shared/test_mcp_config.py::TestMcpServerConfigValidation::test_stdio_transport_rejected`, passing) |
| ADR-007 INV-09 | MCP servers bind only to a loopback address and every MCP server, including mdq-mcp, rejects requests without a matching Bearer token | Unit Test | CI | Blocking | Confirmed (`tests/mcp_servers/test_mcp_server_base.py::TestBindAddressValidation::test_private_lan_rejected`, `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py::TestInboundAuth`, `tests/mcp_servers/shell/test_shell_server_auth.py`, `tests/mcp_servers/github/test_github_server_auth.py`, `tests/mcp_servers/file/test_file_server_auth.py`, `tests/mcp_servers/mdq/test_mdq_authentication.py::TestAuthentication`, `tests/mcp_servers/mdq/test_mdq_authentication.py::TestStartupRequiresToken`, passing) |
| ADR-007 INV-12 | mdq-mcp applies fail-closed `allowed_dirs` authorization only after successful Bearer authentication; neither replaces the other | Unit Test | CI | Blocking | Confirmed (`tests/mcp_servers/mdq/test_mdq_authentication.py::TestAuthenticationBeforeAuthorization`, `tests/mcp_servers/mdq/test_mdq_path_jail.py`, passing) |
| ADR-007 INV-11 | `McpServerHealthState`'s state names (`HEALTHY`/`DEGRADED`/`UNAVAILABLE`/`HALF_OPEN`) are not silently renamed, since callers outside `scripts/shared/mcp_health.py` compare against them by exact value | Unit Test | CI | Blocking | Confirmed (`tests/shared/test_mcp_health.py`, passing) |
| ADR-015 INV-01 | Guarded blocks of generated Reference documents are produced only by their generators and never hand-edited | Static Check | CI | Blocking | Confirmed (`tools/generate_reference_table.py --check` runs in the CI `lint` job; `tests/tools/test_generate_reference_table.py::TestCheckDrift::test_live_docs_have_no_drift`, passing) |
| ADR-008 INV-01 to INV-05 | SQLite 4DB separation maintained | Static Check | CI, Pre-deploy | Blocking | Confirmed (`tools/check_db_separation.py` runs in the CI `lint` job and the deploy pre-deploy check; `tests/tools/test_check_db_separation.py::test_live_repository_has_no_violations`, passing; it verifies table ownership per database, absence of cross-database foreign keys, distinct database paths, and absence of `ATTACH` and schema-qualified `FROM`/`JOIN`; the `DbTarget` enum constrains the four targets) |
| ADR-009 INV-07 | FTS5 rebuild rules followed | Integration Test | CI | Blocking | Confirmed (`tests/rag/test_fts_sync.py::TestFtsTriggerSync::test_fts_trigger_and_manual_rebuild_use_same_text_selection_rule`, `tests/rag/test_fts_sync.py::TestFtsTriggerSync::test_rebuild_fts_preserves_normalized_content_semantics`, `tests/agent/services/test_rag_index_integrity.py::test_rebuild_fts_uses_coalesce`) |
| ADR-009 INV-10 | `normalized_content` must not appear in LLM output | Unit Test | CI | Blocking | Confirmed (`tests/rag/test_rag_pipeline.py::TestFormatChunksDesign2::test_real_normalized_content_attribute_excluded`, passing) |
| ADR-010 INV-03 | No local fallback on normal empty RAG result | Integration Test | CI | Blocking | Confirmed (`remote_empty` → `HttpResultKind.EMPTY`; `tests/rag/test_rag_http_mode.py::test_remote_empty_does_not_trigger_in_process`, passing) |
| ADR-010 INV-04 | No local fallback on RAG 401/403 | Integration Test | CI | Blocking | Confirmed (`tests/rag/test_pipeline_http_result_kind.py::test_auth_error_fails_closed_without_in_process_fallback`, passing: `augment()` raises `RagPipelineError` on 401/403 and does not run the in-process pipeline) |
| ADR-012 INV-01, INV-02, INV-03, INV-04 | Git MCP write operations enforced server-side: safe ref/remote patterns, no forced update through the normal `git_push` path, protected-branch enforcement on the changed branch, and independence from Agent-side approval | Unit/Integration Test | CI | Blocking | Confirmed (`tests/mcp_servers/git/`, passing). INV-01 covered by the write-tool allow-list rejection suite (`test_git_service_dispatch.py`) plus the retained read-tool option-injection tests; INV-02 covered by the push refspec rejection tests (`tests/mcp_servers/git/test_git_service_dispatch.py::TestGitPushRefRejectionBeforeGit::test_rejected_before_snapshot`, `tests/mcp_servers/git/test_git_service_dispatch.py::TestWriteRefAllowlist::test_rejected_branch_forms`); INV-03 covered by the destination-based protected-branch tests (`tests/mcp_servers/git/test_repository_state.py::TestStage3DestinationProtection`, `tests/mcp_servers/git/test_git_service_dispatch.py::TestDestinationBasedProtection`) plus the existing protected-branch suite; INV-04 covered by the independence tests under `tests/mcp_servers/git/`. |
| ADR-013 INV-02, INV-07 | Every Consumer-route principal is explicitly bound to authorized `consumer_id` and topic values; shared and admin credentials have no Consumer-route bypass, and a rejected Subscribe, ACK, or NACK changes no delivery state | Integration Test | CI | Blocking | Confirmed (`tests/eventbus/test_eventbus_consumer_authorization.py::TestSharedAndAdminTokensHaveNoConsumerBypass`, `tests/eventbus/test_eventbus_consumer_authorization.py::TestConsumerPrincipalBinding`, `tests/eventbus/test_eventbus_auth.py::TestFailClosedConsumerAuthorization::test_shared_and_admin_tokens_have_no_consumer_bypass`, passing) |
| ADR-014 INV-01 | Non-WorkflowEngine components (Orchestrator, LlmTurnExecutor, ToolExecutor) do not decide persistent Task/Attempt state, stage transitions, or retries | Manual Review | Code Review | Non-Blocking | `Orchestrator.handle_turn()` delegates to `WorkflowEngineAdapter.execute_turn()` (Explicit in code — `scripts/agent/orchestrator.py`, `scripts/agent/workflow_engine_adapter.py`); no automated test |
| ADR-014 INV-02 | `LlmTurnExecutor` instance construction is centralized in the component that drives the LLM/tool-call loop; no other component holds an unused or duplicate instance | Unit Test | CI | Non-Blocking | Confirmed (`tests/agent/test_orchestrator.py::TestSingleLlmTurnExecutorOwnership::test_orchestrator_creates_single_shared_llm_turn_executor`, passing) |
| ADR-014 INV-03 | MCP Server-side technical safety checks (allowlist, path validation, sandboxing, resource limits, argument validation) are not duplicated or re-implemented in Orchestrator/ToolExecutor layers | Manual Review | Code Review | Non-Blocking | Checks live in the MCP servers (Explicit in code — `scripts/mcp_servers/tool_validators.py`, `scripts/mcp_servers/shell/shell_service.py`); no automated test |

**Note**: "Type" reflects the intended verification method, not whether a test currently exists; the Verification Status column states what exists.

### Pipeline Mapping Summary

| Pipeline Stage | Invariants Covered |
|----------------|-------------------|
| CI (pull request), confirmed | ADR-001 INV-01, INV-08, INV-10 and INV-11; ADR-002 INV-01 and INV-02; ADR-003 INV-02; ADR-004 INV-14; ADR-005 INV-02; ADR-006 INV-02, INV-05, INV-09 and INV-16; ADR-007 INV-06, INV-09, INV-11 and INV-12; ADR-013 INV-02 and INV-07; ADR-015 INV-01; ADR-009 INV-07 and INV-10; ADR-010 INV-03 and INV-04; ADR-012 INV-01, INV-02, INV-03 and INV-04; ADR-014 INV-02 |
| CI (pull request), partial or not verified | ADR-004 INV-07, INV-10 (partial) |
| Startup validation | ADR-004 INV-01, INV-02, INV-07 (partial), INV-08, INV-09, INV-10 (partial) and INV-14; ADR-002 INV-01 and INV-02 through the Security Posture contract |
| Pre-deployment validation | ADR-008 INV-01 to INV-05 (also enforced in CI) |
| Manual Review (code review) | ADR-004 INV-15 and INV-16 (release-review fallback audit); ADR-014 INV-01 and INV-03 |

## Keywords

- adr
- architecture decision record
- invariant
- verification matrix
- dependency graph
- security posture
- posture contract
- self-validation
