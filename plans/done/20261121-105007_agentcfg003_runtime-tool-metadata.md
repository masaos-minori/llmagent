## Goal
- Make the per-tool runtime metadata carried by `RuntimeTool` the single authority for side-effect,
  retry, reconciliation, idempotency, capability and resource-key classification, so that no Agent
  decision is derived from a tool-name set or from a per-tool configuration map. Static constants
  keep only the drift-detection role.

## Priority
Medium

## Scope
- **In-Scope**:
  - Typed field definitions with closed value sets in the `shared` leaf layer (no import of `agent`).
  - Required runtime metadata on `RuntimeTool`; absence fails closed and no risk-lowering default is
    added. `agent_safety_tier` becomes a declared value, not a default.
  - The MCP per-tool field set extended to the new required fields; producers declare them.
  - Migration of the Agent and shared consumers from config maps and static name sets to declared
    metadata.
  - Removal of `tool_safety_tiers`, `approval_risk_rules`, `approval_dry_run_tools` and
    `approval_resource_keys` from `config/agent.toml`, the config dataclass, the section builders,
    the field registry and the ownership manifest. `approval_protected_paths`,
    `approval_high_risk_branches`, `approval_github_allowed_repos` and `plan_blocked_tools` stay as
    operational exceptions.
  - Priority inversion in `classify_operation_type()`: declared metadata is the authority, static
    sets report drift only. `RETRYABLE_TOOLS` ownership moves from an Agent constant to the declared
    per-tool policy.
  - Contract tests for the typed vocabulary, the fail-closed validation and the authority inversion.
  - Documentation and ADR updates required by the contract change.
- **Out-of-Scope**:
  - The call-state API, result storage and secure replay owned by the MCP two-layer defense issues.
  - Preview Policy decision rules (what is shown before execution); this Plan defines capability
    flags only.
  - Per-server internal write-protection gates inside MCP servers that use their own tool lists
    (see `scripts/mcp_servers/git/git_service.py` and `scripts/mcp_servers/git/git_server.py`).
  - Migration of test files that only use the removed config maps as fixtures (recorded as a
      follow-up work item).
  - The MCP schema-version number for the extended field set, which is a decision recorded under
      Unknowns.
- **Dependencies**: `N/A: none` for implementation order. The related work items are noted by id:
  `agentcfg001` (plan-mode and mode classification), `agentcfg002` (tool catalog and registry),
  `mcpai005` (Preview Policy), `mcpdl003` (dedup configuration isolation), `mcpdl004` (call-state
  and reconciliation contract).
  - **Gate decision**: work item `mcpdl006` (two-layer failure verification) | phase all | The reconciliation field values and the replay boundary are defined by that work item; this Plan only carries the typed field and its closed values. Owner decision 2026-11-21: the gate is lifted, implementation proceeds with this Plan's closed value sets.

## Background
Runtime behaviour is decided today from three sources that can disagree: per-tool configuration maps
in `config/agent.toml`, static tool-name sets in `scripts/shared/tool_constants.py`, and the metadata
declared by each MCP server through `/v1/tools`. ADR-003 makes `RuntimeToolRegistry` the sole routing
authority and limits static definitions to tests, expected values and documentation generation, but the
approval, audit and retry decisions still read configuration maps and static sets. The issue
`issues/20261120-114211_agentcfg003_runtime-tool-metadata.md` removes that duplication.

## Problem
- `agent/tool_policy.py` reads `tool_safety_tiers`, `approval_risk_rules` and
  `approval_resource_keys`; `agent/tool_approval.py` reads `approval_dry_run_tools` and its own
  `_KNOWN_DRY_RUN_CAPABLE_TOOLS` set; `agent/tool_runner.py` and `shared/mcp_dedup.py` derive the
  retry class from `RETRYABLE_TOOLS`. A tool that is not in a map or a set is classified by a
  fallback, so the decision is an inference from a name rather than a declared contract.
- `agent/tool_policy.py::classify_operation_type()` consults the static sets before the registry, so
  a declared value cannot win.
- `RuntimeTool.agent_safety_tier` has a default (`WRITE_DANGEROUS`), so a missing declaration is
  silently accepted.
- `approval_resource_keys` is a single global key list, so a path argument and a branch argument
  cannot be classified differently for the same tool.

## Reason for Change
The runtime metadata is already carried by `RuntimeTool` for four fields, and the schema validation
already rejects tools missing them. Extending that contract to the remaining vocabulary removes the
last name-based inferences, and it is the point at which the drift checks can become honest
comparisons instead of decision inputs. Doing it after the tool-catalog and plan-mode work would keep
two sources for the same concept.

## Implementation Intent
Define the vocabulary as typed fields with closed value sets in the `shared` leaf layer, require the
producers to declare them, and make every consumer read the declared value. Keep the existing generic
execution shape: only the values change from names and maps to typed fields. Static sets stay as
reference data for drift detection and for tests, and no compatibility reader is introduced for the
removed maps.

## Requirements
- `REQ-001`: Define the typed vocabulary (side-effect class, retry policy, reconciliation policy,
  idempotency requirement, preview capability flag, resource-key kind) as closed value sets in the
  `shared` leaf layer. No per-tool constant is introduced for policy vocabulary.
- `REQ-002`: Required runtime metadata: a tool entry missing any required field is rejected at
  registration, and no default that lowers risk is applied. `agent_safety_tier` is a required
  argument, not a default.
- `REQ-003`: Extend the MCP per-tool required field set so that every producer declares the new
  fields; the `MCP_TOOL_SCHEMA_VERSION` envelope stays, and the field-set version is recorded in one
  place rather than as a per-tool literal.
- `REQ-004`: Agent and shared consumers read declared metadata instead of configuration maps or
  static tool-name sets.
- `REQ-005`: `config/agent.toml` keeps only operational exceptions (protected paths, high-risk
  branches, allowed repos, raise-only exceptions). Remove `tool_safety_tiers`,
  `approval_risk_rules`, `approval_dry_run_tools` and `approval_resource_keys` from the config file,
  the dataclass, the section builders, the field registry and the ownership manifest.
- `REQ-006`: Plan-mode blocking is derived from the declared tier (a non-`READ_ONLY` tool fails
  closed). `plan_blocked_tools` stays only as a documented exception denylist; no new metadata field
  is added for it.
- `REQ-007`: Static constants become drift detection only: `classify_operation_type()` reads declared
  metadata first, and `RETRYABLE_TOOLS` ownership moves to the declared `retry_policy`. Drift
  findings report disagreement; they do not change a decision.
- `REQ-008`: Resource-key classification is typed per key (`path`, `branch`, `repo`), so path
  escalation and branch escalation read declared kinds instead of hardcoded tool names.
- `REQ-009`: Preview capability flags are declared per tool; the Agent does not infer execution mode
  or capability from tool names. The decision rules stay with the Preview Policy issue.
- `REQ-010`: Idempotency and reconciliation boundary: this Plan defines the typed fields only; the
  call-state contract and the reconcilers stay with the MCP two-layer defense issues.
- `REQ-011`: No compatibility reader for the removed maps; each concept has one source.
- `REQ-012`: Documentation and ADR updates. A change to an ADR decision or invariant requires a
  maintainer approval record in the same change; this Plan records the requirement and does not
  simulate the approval.
- `REQ-013`: Contract tests for the vocabulary, the fail-closed validation, the authority inversion
  and the removed config fields.

## Implementation Target Files
**Freeze status**: Frozen (issue-to-plan Step 8 Implementation Target Files Validation
passed on 2026-11-21: every row exists or is declared as a creation, every row is `Verified`,
and every row is linked to a Requirement or Acceptance criterion. Run
`uv run python tools/audit_plan_target_paths.py` and `uv run python tools/check_plan_target_overlaps.py`
to re-check).
Amended 2026-11-21 (scope): added scripts/mcp_servers/models.py — McpTool TypedDict carries the extended per-tool required field set; resource_scope_keys value type becomes the key-to-kind mapping
Amended 2026-11-21 (fallout): added scripts/agent/constants.py — Remove the default constants for the removed maps (dead definitions once the fields and builders are removed); the declared metadata is the only source

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/shared/tool_metadata.py` | Create (new) | Typed vocabulary module, `shared` leaf, closed value sets; cannot import `agent` (import-linter keeps `shared` a leaf) | REQ-001 / AC-01 | Consumer scan `RuntimeTool` seed; `scripts/shared/runtime_tool.py` is the only current owner of `AgentSafetyTier` | `tests/shared/test_tool_metadata.py` | Verified |
| `scripts/shared/runtime_tool.py` | Extend | Add the typed fields; remove the `agent_safety_tier` default | REQ-002 / AC-02 | `scripts/shared/runtime_tool.py` `AgentSafetyTier` default `WRITE_DANGEROUS`; `build_runtime_tool()` requires four schema-2.0 fields | `tests/shared/test_runtime_tool.py`, `tests/shared/runtime_tool_factory.py` | Verified |
| `scripts/shared/resource_scope.py` | Extend | `validate_tool_schema_v2()` validates the new required fields and the typed key kinds | REQ-002, REQ-008 / AC-02, AC-07 | `validate_tool_schema_v2()` is the enforcement point named by `docs/22_mcp/mcp_06_11_new-tool-registration-procedure.md` | `tests/shared/test_resource_scope.py` | Verified |
| `scripts/shared/runtime_tool_registry.py` | Narrow | `apply_policy()` stops applying a configuration-derived tier | REQ-004, REQ-005 / AC-04 | `apply_policy()` documented as the policy-application path (ADR-003 Decision 9) | `tests/shared/test_runtime_tool_registry.py` | Verified |
| `scripts/shared/tool_constants.py` | Narrow | Sets become reference data for drift detection only; `RETRYABLE_TOOLS` ownership moved | REQ-007 / AC-04, AC-10 | `scripts/shared/tool_constants.py:183` `RETRYABLE_TOOLS`; line 220 note on not conflating dimensions | `tests/shared/test_tool_constants.py` | Verified |
| `scripts/shared/mcp_dedup.py` | Change | Retry classification comes from the caller-supplied declared policy, not from a static set | REQ-007, REQ-010 / AC-09 | `scripts/shared/mcp_dedup.py:29,169-173` cross-check against `config/mcp_dedup.toml [retry_class]` | `tests/shared/test_mcp_dedup.py` | Verified |
| `scripts/shared/tool_routing_validation.py` | Change | Tier checks become drift reports, not decision inputs | REQ-007 / AC-10 | `check_tool_safety_tiers()`, `check_unknown_tool_safety_tiers()` called from `agent/services/routing_drift.py` | `tests/shared/test_tool_routing_validation.py` | Verified |
| `scripts/mcp_servers/server.py` | Extend | Per-tool required field set extended; envelope version unchanged | REQ-003 / AC-03 | `TOOL_SCHEMA_V2_FIELDS`, `MCP_TOOL_SCHEMA_VERSION` | `tests/mcp_servers/test_tool_schema_contract.py` | Verified |
| `scripts/mcp_servers/cicd/cicd_tools.py` | Extend | Declare the new fields for its 6 tool entries | REQ-003 / AC-03 | Consumer scan, `*tools*.py` producer set | `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py` | Verified |
| `scripts/mcp_servers/file/read_tools.py` | Extend | Declare the new fields for its 9 tool entries | REQ-003 / AC-03 | Consumer scan, producer set | `tests/mcp_servers/file/test_tool_server_layer_consistency.py` | Verified |
| `scripts/mcp_servers/file/write_tools.py` | Extend | Declare the new fields for its 4 tool entries | REQ-003 / AC-03 | Consumer scan, producer set | `tests/mcp_servers/file/test_tool_server_layer_consistency.py` | Verified |
| `scripts/mcp_servers/file/delete_tools.py` | Extend | Declare the new fields for its 2 tool entries | REQ-003 / AC-03 | Consumer scan, producer set | `tests/mcp_servers/file/test_tool_server_layer_consistency.py` | Verified |
| `scripts/mcp_servers/git/git_tools.py` | Extend | Declare the new fields for its 10 tool entries | REQ-003 / AC-03 | Consumer scan, producer set | `tests/mcp_servers/git/test_tools_endpoint.py` | Verified |
| `scripts/mcp_servers/github/tools_file.py` | Extend | Declare the new fields for its 7 tool entries | REQ-003 / AC-03 | Consumer scan, producer set | `tests/mcp_servers/github/test_tools_endpoint.py` | Verified |
| `scripts/mcp_servers/github/tools_issues.py` | Extend | Declare the new fields for its 7 tool entries | REQ-003 / AC-03 | Consumer scan, producer set | `tests/mcp_servers/github/test_tools_endpoint.py` | Verified |
| `scripts/mcp_servers/github/tools_pull_requests.py` | Extend | Declare the new fields for its 8 tool entries | REQ-003 / AC-03 | Consumer scan, producer set | `tests/mcp_servers/github/test_tools_endpoint.py` | Verified |
| `scripts/mcp_servers/github/tools_repository.py` | Extend | Declare the new fields for its 8 tool entries | REQ-003 / AC-03 | Consumer scan, producer set | `tests/mcp_servers/github/test_tools_endpoint.py` | Verified |
| `scripts/mcp_servers/mdq/mdq_tools.py` | Extend | Declare the new fields for its 7 tool entries | REQ-003 / AC-03 | Consumer scan, producer set | `tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py` | Verified |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_tools.py` | Extend | Declare the new fields for its 4 tool entries | REQ-003 / AC-03 | Consumer scan, producer set | `tests/mcp_servers/rag_pipeline/test_tool_server_layer_consistency.py` | Verified |
| `scripts/mcp_servers/shell/shell_tools.py` | Extend | Declare the new fields for its 1 tool entry | REQ-003 / AC-03 | Consumer scan, producer set | `tests/mcp_servers/shell/test_tool_server_layer_consistency.py` | Verified |
| `scripts/mcp_servers/web_search/web_search_tools.py` | Extend | Declare the new fields for its 2 tool entries | REQ-003 / AC-03 | Consumer scan, producer set | `tests/mcp_servers/web_search/test_tool_server_layer_consistency.py` | Verified |
| `scripts/agent/tool_policy.py` | Change | Read declared metadata for tier, risk and key kinds; `classify_operation_type()` priority inverted | REQ-004, REQ-006, REQ-007, REQ-008 / AC-04, AC-06, AC-07 | Reads removed maps at lines 89, 173, 185, 190, 361, 424, 426, 458-459 | `tests/agent/test_tool_policy.py`, `tests/agent/test_tool_policy_comprehensive.py` | Verified |
| `scripts/agent/tool_approval.py` | Change | Read the declared capability flag; remove `_KNOWN_DRY_RUN_CAPABLE_TOOLS` | REQ-004, REQ-009 / AC-04, AC-08 | `_KNOWN_DRY_RUN_CAPABLE_TOOLS` at line 69; `approval_dry_run_tools` read at line 107 | `tests/agent/test_tool_approval_preflight.py` | Verified |
| `scripts/agent/tool_audit.py` | Change | Operation type and resource keys read declared metadata | REQ-004, REQ-008 / AC-04, AC-07 | `approval_resource_keys` reads at lines 68, 76 | `tests/agent/test_tool_audit.py` | Verified |
| `scripts/agent/tool_runner.py` | Change | `classify_retry_class()` reads the declared `retry_policy` | REQ-004, REQ-007 / AC-04, AC-09 | `tool_runner.py:171-177` names `RETRYABLE_TOOLS` as the single source of truth | `tests/agent/test_tool_runner.py` | Verified |
| `scripts/agent/production_config_validator.py` | Narrow | Tier-map checks removed; the fail-closed check moves to declared metadata | REQ-004, REQ-011 / AC-04, AC-05 | `_check_unknown_tool_safety_tiers()` line 72, called at 253 | `tests/agent/test_production_config_validator.py` | Verified |
| `scripts/agent/startup_validation.py` | Change | Startup failure text and the tier check path follow the removed maps | REQ-002, REQ-007 / AC-02, AC-10 | `startup_validation.py:177` message; broad catch around `check_tool_safety_tiers` | `tests/agent/shared/test_startup_validation_pipeline.py` | Verified |
| `scripts/agent/services/config_validators.py` | Narrow | Remove `validate_tool_safety_tiers` and its value check | REQ-005, REQ-011 / AC-05 | `config_validators.py:261-268` | `tests/agent/test_config_builders.py` | Verified |
| `scripts/agent/services/config_field_registry.py` | Narrow | Remove the four removed config fields from the registry | REQ-005, REQ-011 / AC-05 | `config_field_registry.py:94,95,97,110,146-149` | `tests/agent/services/test_config_reload.py` | Verified |
| `scripts/agent/config_dataclasses.py` | Narrow | Remove the four map fields from the approval section | REQ-005, REQ-006, REQ-008 / AC-05, AC-06 | `config_dataclasses.py:293,297,302` field definitions | `tests/agent/test_config_dataclasses.py` | Verified |
| `scripts/agent/config_section_builders.py` | Narrow | Remove the builders and `_validate_dry_run_tools` | REQ-005, REQ-009, REQ-011 / AC-05 | `_validate_dry_run_tools()` at line 93, called at 300 | `tests/agent/test_config_builders.py` | Verified |
| `config/agent.toml` | Change | Remove the four map sections; keep the operational exceptions | REQ-005, REQ-006 / AC-05, AC-06 | `config/agent.toml` lines 109, 117, 201, 225, 251, 272, 289; `plan_blocked_tools` at 97 | `tests/agent/test_config_builders.py` | Verified |
| `registry/manifests/config_ownership.yaml` | Change | Remove the ownership entries for the removed fields | REQ-005, REQ-011 / AC-05 | `registry/manifests/config_ownership.yaml:10,26,30,33,110,146,149` | `uv run python tools/check_config_ownership.py` | Verified |
| `scripts/agent/services/mcp_status.py` | Change | Server risk level derived from declared tiers, not from the config map | REQ-004 / AC-04 | `mcp_status.py:63,319` | `tests/agent/services/test_agent_mcp_status.py` | Verified |
| `scripts/agent/services/config_service_sync.py` | Change | Tier mapping type and source change | REQ-004 / AC-04 | `config_service_sync.py:78` | `tests/agent/services/test_config_reload.py` | Verified |
| `scripts/agent/commands/cmd_config_display.py` | Narrow | Remove the display lines for the removed maps | REQ-005 / AC-05 | `cmd_config_display.py:97,118-119` | `tests/agent/commands/test_agent_cmd_config.py` | Verified |
| `scripts/agent/services/routing_drift.py` | Change | Tier drift becomes a report against declared metadata | REQ-007 / AC-10 | `routing_drift.py:17,22-23` | `tests/agent/services/test_routing_drift.py` | Verified |
| `scripts/agent/services/mcp_tool_discovery.py` | Change | Write-classification drift compares declarations against the reference sets only | REQ-007 / AC-10 | `mcp_tool_discovery.py:204` ADR-003 INV-03 report | `tests/agent/services/test_mcp_tool_discovery_posture_gate.py` | Verified |
| `scripts/agent/services/mcp_tool_discovery_registry.py` | Change | Build tools with the extended required field set | REQ-002, REQ-003 / AC-02, AC-03 | `build_runtime_tool()` call path | `tests/shared/test_runtime_tool_registry.py` | Verified |
| `tests/shared/test_tool_metadata.py` | Create (new) | Contract tests for the typed vocabulary and closed value sets | REQ-001, REQ-013 / T-01 | New module has no test yet | this file | Verified |
| `tests/shared/test_runtime_tool.py` | Change | Assert required fields and no risk-lowering default | REQ-002, REQ-013 / T-02 | Existing safe-default assertions | this file | Verified |
| `tests/shared/runtime_tool_factory.py` | Change | Shared fixture must supply the new required fields | REQ-002, REQ-013 / T-02 | Used by the contract test files listed above | this file | Verified |
| `tests/shared/test_runtime_tool_registry.py` | Change | Assert no configuration-derived tier after `apply_policy()` | REQ-002, REQ-004, REQ-013 / T-02 | Fixture helpers build `RuntimeTool` instances | this file | Verified |
| `tests/shared/test_resource_scope.py` | Change | Assert typed key kinds and rejection of a missing field | REQ-002, REQ-008, REQ-013 / T-02, T-06 | Existing scope-resolution fixture | this file | Verified |
| `tests/shared/test_tool_safety_tiers.py` | Change | Assert drift reporting only, with no decision effect | REQ-007, REQ-013 / T-09 | 20 direct references to the removed map | this file | Verified |
| `tests/shared/test_tool_constants.py` | Change | Assert the reference role and cross-source consistency without ownership | REQ-007, REQ-013 / T-09 | Lines 103, 117, 127 assert ownership of `RETRYABLE_TOOLS` | this file | Verified |
| `tests/mcp_servers/test_tool_schema_contract.py` | Change | Assert the extended per-tool field set for every producer | REQ-003, REQ-013 / T-03 | Imports the reference sets and `get_all_mcp_tool_names()` | this file | Verified |
| `tests/agent/test_tool_policy.py` | Change | Contract tests for metadata authority and plan-mode derivation | REQ-004, REQ-006, REQ-008, REQ-013 / T-04, T-06 | 71 direct references | this file | Verified |
| `tests/agent/test_tool_policy_comprehensive.py` | Change | Assert the inverted priority in `classify_operation_type()` | REQ-007, REQ-013 / T-04, T-09 | Cited by `docs/10_adr/adr_01_index.md` for the tier rule | this file | Verified |
| `tests/agent/test_tool_approval_preflight.py` | Change | Capability-flag path replaces the config map and the local set | REQ-004, REQ-009, REQ-013 / T-04, T-07 | 26 direct references | this file | Verified |
| `tests/agent/test_tool_approval_risk.py` | Change | Risk levels read from declared metadata | REQ-004, REQ-013 / T-04 | 14 direct references | this file | Verified |
| `tests/agent/test_agent_repl_tool_exec.py` | Change | Contract assertions on tier behaviour must move to declared metadata | REQ-004, REQ-013 / T-04 | 26 direct references | this file | Verified |
| `tests/agent/test_tool_audit.py` | Change | Operation-type and key-kind assertions | REQ-004, REQ-008, REQ-013 / T-04, T-06 | 9 direct references; cited by `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | this file | Verified |
| `tests/agent/test_tool_runner.py` | Change | Retry class from declared policy | REQ-004, REQ-007, REQ-010, REQ-013 / T-04, T-08 | Lines 2534-2555 assert membership of `RETRYABLE_TOOLS` | this file | Verified |
| `tests/agent/test_production_config_validator.py` | Change | Remove the tier-map validation cases; add the fail-closed metadata cases | REQ-002, REQ-005, REQ-011, REQ-013 / T-02, T-05 | 25 direct references | this file | Verified |
| `tests/agent/_config_test_defaults.py` | Change | Shared fixture helper defines the removed maps | REQ-005, REQ-013 / T-05 | 5 direct references; used by the contract tests above | this file | Verified |
| `tests/agent/test_config_builders.py` | Change | Remove builder and validator cases for the removed fields | REQ-005, REQ-009, REQ-013 / T-05 | 18 direct references | this file | Verified |
| `tests/agent/test_config_dataclasses.py` | Change | Remove the field-level assertions for the removed maps | REQ-005, REQ-013 / T-05 | 9 direct references | this file | Verified |
| `tests/agent/services/test_config_reload.py` | Change | Hot-reload contract for the removed fields is dropped | REQ-005, REQ-011, REQ-013 / T-05 | 19 direct references, including the field list at 1167-1168 | this file | Verified |
| `tests/agent/commands/test_agent_cmd_config.py` | Change | Display assertions for the removed maps | REQ-005, REQ-013 / T-05 | 4 direct assertions on the removed map | this file | Verified |
| `tests/agent/shared/test_startup_validation_pipeline.py` | Change | Pipeline stage names and fixtures for the tier check | REQ-007, REQ-013 / T-09 | Lines 310, 322 | this file | Verified |
| `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` | Change | Remove the config-map priority statement and the local capability set | REQ-012 / AC-11 | Lines 46, 50, 52, 54, 101, 112, 125, 131-132 | `uv run python tools/check_docs_structure.py docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` | Verified |
| `docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md` | Change | Canonical level source moves from the config map to declared metadata | REQ-012 / AC-11 | Named by `docs/00_index.md` for the tool-execution-and-approval task | `uv run python tools/check_docs_structure.py docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md` | Verified |
| `docs/23_agent/agent_08_03_configuration-tools-memory.md` | Change | Removed config keys | REQ-012 / AC-11 | Documented field set includes the removed maps | `uv run python tools/check_docs_structure.py docs/23_agent/agent_08_03_configuration-tools-memory.md` | Verified |
| `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` | Change | Removed config keys and the precedence statement | REQ-012 / AC-11 | Lines 83, 91, 98, 102, 130 | `uv run python tools/check_docs_structure.py docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` | Verified |
| `docs/91_security/security_02_high-risk-tool-common-policy.md` | Change | Fail-closed table row for the removed maps | REQ-012 / AC-11 | Line 158 | `uv run python tools/check_docs_structure.py docs/91_security/security_02_high-risk-tool-common-policy.md` | Verified |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Change | Decision and invariant change, with the maintainer approval record | REQ-012 / AC-11 | Decisions 2, 5, 8, 9, 14 | `uv run python tools/check_adr_reference.py` | Verified |
| `scripts/mcp_servers/models.py` | Extend | McpTool TypedDict carries the extended per-tool required field set; resource_scope_keys value type becomes the key-to-kind mapping | REQ-003 / N/A: none cites REQ-003 | McpTool TypedDict declares the four current required keys; every producer TOOL_LIST literal is typed as list[McpTool], so the extended field set cannot be declared without this file | tests/mcp_servers/test_tool_schema_contract.py | Verified |
| `scripts/agent/constants.py` | Narrow | Remove the default constants for the removed maps (dead definitions once the fields and builders are removed); the declared metadata is the only source | REQ-011 / N/A: none cites REQ-011 | scripts/agent/constants.py defines _DEFAULT_APPROVAL_RISK_RULES, _DEFAULT_RESOURCE_KEYS, _DEFAULT_DRY_RUN_TOOLS; they are read only by config_section_builders.py and config_dataclasses.py, and no test references them | N/A: no test asserts these constants | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/tool_arg_validator.py` | Confirms the schema-2.0 argument contract and `allow_extra_fields`; no behavior change is expected | REQ-002 |
| `scripts/agent/repository_gateway.py` | Consumer of `check_preflight()` and `classify_operation_type()`; confirms the call signature stays stable | REQ-004, REQ-007 |
| `scripts/mcp_servers/dispatch.py` | Its use of `ALL_SIDE_EFFECTING_TOOLS` is the boundary with the dedup configuration issues; this Plan does not change it | REQ-010, UNK-05 |
| `scripts/mcp_servers/git/git_service.py`, `scripts/mcp_servers/git/git_server.py` | Per-server write-protection gate; read to confirm it is out of scope | REQ-007, UNK-05 |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Decisions 2, 5, 8, 9 and 14 are the current authority statements this Plan changes | REQ-012 |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Fail-closed startup consequence for a missing tier; the wording this Plan must not restate | REQ-002, REQ-012 |
| `docs/10_adr/adr_02_07_016_adr-authority-model.md` | Records where an ADR decision change and its approval record must be written | REQ-012 |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Current ADR credited by `tool_runner.py` for the retry ownership that this Plan moves | REQ-007, UNK-03 |
| `docs/22_mcp/mcp_06_11_new-tool-registration-procedure.md` | Names the required field set and the enforcement point this Plan extends | REQ-003 |
| `docs/40_shared/shared_02_02_types_and_protocols-tool-and-execution-dto.md` | `ToolExecutionContext` has no execution-mode or capability fields; confirms the boundary with the call-state issues | REQ-009, REQ-010, UNK-04 |
| `docs/22_mcp/mcp_03_06_tool-runtime-availability-metadata.md` | Current runtime availability metadata; no capability flags are defined there today | REQ-009 |
| `config/mcp_dedup.toml` | `[retry_class]` mirror that the drift check compares with the declared policy | REQ-007, REQ-010 |
| `deploy/deploy.sh` | Confirms `config/agent.toml` and `registry/` are copied as-is, so deployment needs no script change | REQ-005, AC-05 |

## Acceptance Criteria
- `AC-01` (REQ-001): the typed vocabulary lives in the `shared` leaf layer and imports nothing from
  `agent`; `uv run python tools/check_import_layers.py` and `PYTHONPATH=scripts uv run lint-imports`
  pass.
- `AC-02` (REQ-002): a tool entry missing any required field is rejected and excluded from the
  registry; no default that lowers risk remains in `build_runtime_tool()`.
- `AC-03` (REQ-003): every producer file declares the extended field set for every tool entry, and
  the field-set version appears in one place.
- `AC-04` (REQ-004, REQ-007): no Agent decision reads a per-tool configuration map or a static
  tool-name set; the only remaining reads are drift comparisons.
- `AC-05` (REQ-005, REQ-011): the four removed keys are absent from `config/agent.toml`, the
  dataclass, the builders, the field registry and the ownership manifest, and no compatibility reader
  exists.
- `AC-06` (REQ-006): plan-mode blocking comes from the declared tier; `plan_blocked_tools` is
  documented as an exception denylist and its current entries stay redundant by design.
- `AC-07` (REQ-008): path and branch escalation resolve from the declared key kind.
- `AC-08` (REQ-009): capability flags come from the declared flag; `_KNOWN_DRY_RUN_CAPABLE_TOOLS` is
  gone.
- `AC-09` (REQ-007, REQ-010): `mcp_dedup` and `tool_runner` use the declared retry policy; the
  `[retry_class]` mirror stays as a drift comparison only.
- `AC-10` (REQ-007): a drift finding reports disagreement between a declaration and the reference
  data and changes no decision.
- `AC-11` (REQ-012): the documentation and ADR changes carry the maintainer approval record for the
  decision change, and the doc checkers pass.
- `AC-12` (REQ-013): the contract tests pass, and the full suite passes against the recorded baseline
  (1 known pre-existing failure, 13182 passed, 5 skipped).

## Tests
- `T-01` (REQ-001): `tests/shared/test_tool_metadata.py` — closed value sets, no per-tool constants,
  no import of `agent`.
- `T-02` (REQ-002): `tests/shared/test_runtime_tool.py`, `tests/shared/test_runtime_tool_factory.py`,
  `tests/shared/test_runtime_tool_registry.py`, `tests/shared/test_resource_scope.py` — a missing
  required field is rejected; `agent_safety_tier` has no default.
- `T-03` (REQ-003): `tests/mcp_servers/test_tool_schema_contract.py` — every producer entry declares
  the extended field set; the envelope version is unchanged.
- `T-04` (REQ-004): `tests/agent/test_tool_policy.py`, `tests/agent/test_tool_policy_comprehensive.py`,
  `tests/agent/test_tool_approval_preflight.py`, `tests/agent/test_tool_approval_risk.py`,
  `tests/agent/test_tool_audit.py`, `tests/agent/test_agent_repl_tool_exec.py`,
  `tests/agent/test_tool_runner.py`, `tests/agent/services/test_agent_mcp_status.py` — decisions read
  declared metadata.
- `T-05` (REQ-005): `tests/agent/test_config_builders.py`, `tests/agent/test_config_dataclasses.py`,
  `tests/agent/services/test_config_reload.py`, `tests/agent/test_production_config_validator.py`,
  `tests/agent/commands/test_agent_cmd_config.py`, `tests/agent/_config_test_defaults.py` — the
  removed fields are absent and rejected as unknown keys.
- `T-06` (REQ-008): `tests/shared/test_resource_scope.py`, `tests/agent/test_tool_audit.py`,
  `tests/agent/test_tool_policy.py` — typed key kinds for path and branch escalation.
- `T-07` (REQ-009): `tests/agent/test_tool_approval_preflight.py` — declared capability flag only.
- `T-08` (REQ-007, REQ-010): `tests/agent/test_tool_runner.py`, `tests/shared/test_tool_constants.py` —
  retry policy from the declared value.
- `T-09` (REQ-007): `tests/shared/test_tool_safety_tiers.py`, `tests/shared/test_tool_constants.py`,
  `tests/agent/test_tool_policy_comprehensive.py`, `tests/agent/shared/test_startup_validation_pipeline.py` —
  drift reports do not change a decision.
- `T-10` (REQ-013): full suite and the validation gates; test files that only use the removed maps as
  fixtures are covered by the follow-up test-audit work item, not by this Plan.

## Documentation Impact
Yes, docs must be updated for `REQ-012` (and `REQ-007`, which changes what the docs state as the
authority). Target docs named through `docs/00_index.md`'s "Document References by Task" table for the
tool-execution-and-approval task, the configuration task, the high-risk tool common-policy task, and
the ADR authority task:
- `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` (classification priority,
  `_KNOWN_DRY_RUN_CAPABLE_TOOLS`, dry-run map).
- `docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md` (canonical level source).
- `docs/23_agent/agent_08_03_configuration-tools-memory.md` and
  `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` (removed config keys).
- `docs/91_security/security_02_high-risk-tool-common-policy.md` (fail-closed table for the removed
  maps).
- `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` (the decision change
  and its approval record).
A secondary sweep of the MCP reference docs that state the current priority order
(`docs/22_mcp/mcp_01_tool_ownership_matrix.md`, `mcp_03_01`, `mcp_03_02`, `mcp_05_03`,
`mcp_06_01`, `mcp_06_11`, `mcp_06_12`, `mcp_06_13`, `docs/41_db/db_03_07*`,
`docs/40_shared/shared_02_02*`) is recorded as a follow-up doc work item under Risks; run the doc
checkers after any of these edits.

## Assumptions
- The `shared` package remains an import-linter leaf, so the typed vocabulary cannot import `agent`;
  producers in `scripts/mcp_servers/` and consumers in `scripts/agent/` both read it from `shared`.
- Every MCP tool entry is served through the `/v1/tools` schema-2.0 path, so a single field-set
  extension is enough for all producers.
- `policy_version` is carried as the field-set version recorded in one place, not as a per-tool
  literal; a per-tool literal would recreate the drift problem the issue removes.
- The full suite baseline (1 known pre-existing failure in `tests/agent/test_agent_session.py`) is not
  caused by this change and is not fixed by it.
- Test files that only use the removed maps as fixtures are out of this Plan's scope by the owner's
  decision; the contract-test scope is the set listed in Implementation Target Files.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Which MCP schema version identifier the extended per-tool field set carries | The issue states the version must be decided; the current envelope is `MCP_TOOL_SCHEMA_VERSION` 2.0 and the per-tool field set has no version identifier of its own | Decided: `2.1` (owner decision 2026-11-21); recorded in `scripts/shared/tool_metadata.py` and the ADR change | False |
| UNK-02 | The names of the typed preview capability fields that the call-state contract will use | The preview contract is not planned yet (`mcpai005`); `ToolExecutionContext` has no capability fields | Decide in the preview work item; this Plan defines only the declared capability flag and keeps the decision rules out of scope | False |
| UNK-03 | `RETRYABLE_TOOLS` ownership move needs a maintainer approval record for the ADR text that credits it | `tool_runner.py` names ADR-008 as the source of the current ownership; no ADR records it as an Agent canonical set | Maintainer approval given 2026-11-21; the record is written in the ADR change (procedure 67), per `docs/10_adr/adr_02_07_016_adr-authority-model.md` | False |
| UNK-04 | Removing the configuration-derived tier changes the reload semantics stated by ADR-003 Decision 14 | No approval record exists for the change to a Decision/invariant statement | Maintainer approval given 2026-11-21; the record is added in the ADR change (procedure 67) | False |
| UNK-05 | Whether the MCP servers' own tool-name sets (used for their internal write-protection gate) are in scope of the constants demotion | The issue names `shared/tool_constants.py`; `git_service.py` uses `GIT_READ_TOOLS` as a runtime decision inside the server | Decide with the MCP owner; this Plan treats the per-server gate as out of scope and records it here | False |
| UNK-06 | Whether the `[retry_class]` mirror in `config/mcp_dedup.toml` stays as drift reference or is removed by the dedup configuration issue | The dedup configuration issue is open and unplanned; `mcpdl003` | That issue decides the file's removal; this Plan keeps the mirror as a drift comparison only | False |
| UNK-07 | `agentcfg001` and `agentcfg002` plan rows are not marked `Completed`, but the code evidence shows their scope landed | Execution Status of those plans | Confirm with the owner; treated as landed for this analysis, so no implementation dependency is recorded | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here is a subset of `Implementation Target Files`' rows. Bus Factor is the
top author's share of commits per file (per-file `git log --format='%an'`; `git-fame` is not
installed). Values are from the measurement run on the current working tree.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `config/agent.toml` | Remove four map sections | Config consumers, startup validation, docs | 17 | 49/84 | Copies `config/agent.toml` to the deployed config directory; the deployed copy must be re-copied, no script change |
| `scripts/agent/tool_policy.py` | Authority inversion, remove map reads | Approval, plan mode, audit callers | 9 | 17/34 | rsync of `scripts/`, no change needed |
| `scripts/agent/tool_approval.py` | Capability flag, remove local set | Approval prompts, preflight path | 6 | 19/37 | rsync, no change needed |
| `scripts/agent/tool_audit.py` | Declared key kinds | Audit records, risk escalation | 8 | 27/41 | rsync, no change needed |
| `scripts/agent/tool_runner.py` | Declared retry policy | Dedup writes, retry behavior | 16 | 42/84 | rsync, no change needed |
| `scripts/agent/production_config_validator.py` | Remove tier-map checks | Startup validation, hot reload | 12 | 8/14 | rsync, no change needed |
| `scripts/shared/runtime_tool.py` | Required typed fields | Every producer and consumer of the contract | 1 | 6/10 | rsync, no change needed |
| `scripts/shared/runtime_tool_registry.py` | Remove configuration-derived tier application | Routing and policy application | 5 | 13/23 | rsync, no change needed |
| `scripts/shared/tool_constants.py` | Sets become reference data | Drift checks, consistency tests | 5 | 17/36 | rsync, no change needed |
| `scripts/shared/mcp_dedup.py` | Retry from declared policy | Dedup state machine, `[retry_class]` mirror | 7 | 5/7 | rsync, no change needed |
| `scripts/shared/resource_scope.py` | Extended field-set validation | Tool registration, schema validation | 1 | 2/3 | rsync, no change needed |
| `scripts/mcp_servers/server.py` | Per-tool required field set | All MCP servers, `/v1/tools` responses | 10 | 20/34 | rsync, no change needed |
| `scripts/agent/config_dataclasses.py` | Remove four fields | Config build, hot reload, display | 10 | 38/69 | rsync, no change needed |
| `scripts/agent/config_section_builders.py` | Remove builders and validator | Config build path | 6 | 4/7 | rsync, no change needed |
| `scripts/agent/services/config_field_registry.py` | Remove field entries | Hot-reload field set | 4 | 6/10 | rsync, no change needed |
| `registry/manifests/config_ownership.yaml` | Remove ownership entries | Ownership checker, config docs | 6 | 4/6 | `registry/` is rsynced to the deployed directory; no script change |
| `scripts/agent/services/mcp_status.py` | Server risk from declared tiers | `/mcp` status display | 4 | 17/36 | rsync, no change needed |
| `scripts/agent/startup_validation.py` | Tier check path | Startup failure handling | 16 | 15/25 | rsync, no change needed |
| `scripts/mcp_servers/models.py` | Modify | Not assessed (amendment 2026-11-21) | N/A | N/A | Not assessed (amendment 2026-11-21) |
| `scripts/agent/constants.py` | Modify | Not assessed (amendment 2026-11-21) | N/A | N/A | Not assessed (amendment 2026-11-21) |

## Design
### Contract shape
- New module `scripts/shared/tool_metadata.py` holds the typed vocabulary: `SideEffectClass`
  (`read_only`, `local_write`, `external_write`), `RetryPolicy` (`never`, `safe_read_retry`,
  `same_logical_call_only`, `reconcile_then_retry`), `ReconciliationPolicy` (`not_required`,
  `local_state`, `external_state`), `ResourceKeyKind` (`path`, `branch`, `repo`), the capability flag
  values, and the single field-set version constant. It imports nothing from `agent`.
- `RuntimeTool` gains `side_effect_class`, `retry_policy`, `reconciliation_policy`,
  `idempotency_required`, `preview_capability`, and `policy_version`; `resource_scope_keys` becomes a
  mapping of key name to `ResourceKeyKind`. All new fields are required at build time; absence fails
  closed at registration. `agent_safety_tier` becomes a required argument with no default.
- `build_runtime_tool()` keeps its shape; only the required argument set grows. The existing four
  schema-2.0 fields are unchanged, which keeps the producers' declaration style.
- No default value is added for any new field. A tool that cannot declare a value is rejected, which
  is the current behavior for the schema-2.0 fields.

### Authority and drift
- `classify_operation_type()` reads the declared metadata first. The static sets in
  `scripts/shared/tool_constants.py` are reference data for drift detection and for tests only; they
  are no longer decision inputs. This is the priority inversion the issue asks for.
- `RETRYABLE_TOOLS` ownership moves to the declared `retry_policy`. `shared/mcp_dedup.py` receives the
  classification from the caller and keeps the `[retry_class]` comparison as a drift check.
- `plan_blocked_tools` needs no new field: plan-mode blocking is derived from the tier, and the config
  list remains as an exception denylist. Its current entries are redundant by design; that is recorded
  as `DT-03 Option A` in the existing docs, so the exception is documented rather than removed.
- The config keeps only operational exceptions: protected paths, high-risk branches, allowed repos, and
  raise-only exceptions. A value that can be derived from a declared field is not kept in config.

### Boundaries
- `shared` stays a leaf; the vocabulary module cannot import `agent`, so the classification values are
  defined in `shared` and read by both sides.
- Preview Policy: this Plan defines the capability flag only; the rules that decide what is shown
  before execution stay with the preview work item.
- Reconciliation: this Plan defines the typed field and its closed values; the call-state API, the
  reconcilers and result replay stay with the MCP two-layer defense issues. The reconciliation coupling
  is in `scripts/shared/mcp_dedup.py`, not in `scripts/db/recovery.py` (the issue's wording about
  `db/recovery.py` is not current code).
- Per-server tool lists used inside an MCP server for its own write-protection gate stay as they are;
  the demotion applies to the Agent-side policy vocabulary.

### Consumer scan disposition (`tools/scan_change_consumers.py`, saved at `/tmp/opencode/scans.txt`)
- Production candidates are dispositioned as target rows or reference rows in the tables above; the
  seeds were `RuntimeTool`, `RETRYABLE_TOOLS`, `approval_dry_run_tools`,
  `_KNOWN_DRY_RUN_CAPABLE_TOOLS`, `tool_safety_tiers`, `plan_blocked_tools`,
  `approval_resource_keys`.
- `scripts/agent/tool_arg_validator.py`: reference row; comment-only reference, no behavior change.
- `scripts/agent/repository_gateway.py`: reference row; it calls the policy functions through their
  existing signatures.
- `scripts/mcp_servers/dispatch.py`, `scripts/mcp_servers/git/git_service.py`,
  `scripts/mcp_servers/git/git_server.py`: reference rows; out of scope per the boundary decision and
  UNK-05.
- `scripts/shared/runtime_tool_registry.py`, `scripts/shared/resource_scope.py`,
  `scripts/shared/tool_constants.py`, `scripts/shared/mcp_dedup.py`,
  `scripts/shared/tool_routing_validation.py`, `scripts/agent/*`, `scripts/mcp_servers/*`: target rows.
- Test candidates that assert on the removed maps or on the contract are target rows.
- Test candidates that only build fixtures with the removed maps are `not affected` in this Plan's
  scope by the owner's decision, except `tests/shared/runtime_tool_factory.py` and
  `tests/agent/_config_test_defaults.py`, which are shared helpers the contract tests use. They are
  handled by the follow-up test-audit work item.
- Test candidates that compare producer declarations with the reference sets
  (`tests/mcp_servers/**/test_*_layer_consistency.py`, `tests/shared/test_rag_tools_consistency.py`,
  `tests/shared/test_tool_registry*.py`) are `not affected: they are the drift-detection role the Plan
  keeps`, unless a listed contract-test file overlaps them.
- `docs/` candidates are dispositioned in Documentation Impact.

## Implementation steps

1. **Phase 1: Decision gate**
   - [ ] Record the field-set version decision and the ADR decision/invariant change, with the
     maintainer approval record requirement stated in the change (REQ-012;
     `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`).
2. **Phase 2: Typed vocabulary and contract validation**
   - [ ] Create the typed vocabulary module with closed value sets and the single version constant
     (REQ-001; `scripts/shared/tool_metadata.py`).
   - [ ] Add the typed fields to `RuntimeTool` and remove the tier default (REQ-002;
     `scripts/shared/runtime_tool.py`).
   - [ ] Extend the field-set validation and the typed key kinds (REQ-002, REQ-008;
     `scripts/shared/resource_scope.py`).
3. **Phase 3: Producer declarations**
   - [ ] Extend the per-tool required field set in the schema contract (REQ-003;
     `scripts/mcp_servers/server.py`).
   - [ ] Declare the new fields in each tool-definition file (REQ-003; every row in Implementation
     Target Files under `scripts/mcp_servers/*_tools.py` and the `scripts/mcp_servers/github` and
     `scripts/mcp_servers/rag_pipeline` tool files listed there).
   - [ ] Extend (REQ-003; `scripts/mcp_servers/models.py`) — amendment 2026-11-21
4. **Phase 4: Consumer migration**
   - [ ] Read declared metadata in the Agent policy, approval, audit and runner paths
     (REQ-004, REQ-008, REQ-009; `scripts/agent/tool_policy.py`, `scripts/agent/tool_approval.py`,
     `scripts/agent/tool_audit.py`, `scripts/agent/tool_runner.py`).
   - [ ] Move the retry classification to the declared policy (REQ-007, REQ-010;
     `scripts/shared/mcp_dedup.py`).
   - [ ] Demote the static sets to reference data and invert the classification priority
     (REQ-007; `scripts/shared/tool_constants.py`, `scripts/shared/tool_routing_validation.py`,
     `scripts/agent/services/routing_drift.py`, `scripts/agent/services/mcp_tool_discovery.py`,
     `scripts/agent/startup_validation.py`).
   - [ ] Remove the configuration-derived tier application (REQ-004, REQ-005;
     `scripts/shared/runtime_tool_registry.py`).
   - [ ] Migrate the remaining config-map readers (REQ-004; `scripts/agent/services/mcp_status.py`,
     `scripts/agent/services/config_service_sync.py`,
     `scripts/agent/commands/cmd_config_display.py`, `scripts/agent/services/mcp_tool_discovery_registry.py`).
5. **Phase 5: Configuration layer**
   - [ ] Remove the four map fields and their builders, validators and registry entries (REQ-005,
     REQ-011; `scripts/agent/config_dataclasses.py`, `scripts/agent/config_section_builders.py`,
     `scripts/agent/services/config_field_registry.py`, `scripts/agent/services/config_validators.py`,
     `registry/manifests/config_ownership.yaml`, `config/agent.toml`).
   - [ ] Narrow (REQ-011; `scripts/agent/constants.py`) — amendment 2026-11-21
6. **Phase 6: Tests**
   - [ ] Contract tests for the vocabulary, required fields and fail-closed validation (REQ-001,
     REQ-002, REQ-013; `tests/shared/test_tool_metadata.py`, `tests/shared/test_runtime_tool.py`,
     `tests/shared/runtime_tool_factory.py`, `tests/shared/test_runtime_tool_registry.py`,
     `tests/shared/test_resource_scope.py`).
   - [ ] Authority and drift tests (REQ-004, REQ-007, REQ-008, REQ-009;
     `tests/agent/test_tool_policy.py`, `tests/agent/test_tool_policy_comprehensive.py`,
     `tests/agent/test_tool_approval_preflight.py`, `tests/agent/test_tool_approval_risk.py`,
     `tests/agent/test_tool_audit.py`, `tests/agent/test_agent_repl_tool_exec.py`,
     `tests/agent/test_tool_runner.py`, `tests/shared/test_tool_safety_tiers.py`,
     `tests/shared/test_tool_constants.py`, `tests/mcp_servers/test_tool_schema_contract.py`,
     `tests/agent/shared/test_startup_validation_pipeline.py`).
   - [ ] Configuration-layer tests (REQ-005, REQ-011, REQ-013;
     `tests/agent/test_config_builders.py`, `tests/agent/test_config_dataclasses.py`,
     `tests/agent/services/test_config_reload.py`, `tests/agent/test_production_config_validator.py`,
     `tests/agent/commands/test_agent_cmd_config.py`, `tests/agent/_config_test_defaults.py`).
7. **Phase 7: Deployment and verification**
   - [ ] Run the full validation gates: `uv run ruff check scripts/`,
     `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`,
     `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml`,
     `uv run pytest -n logical -m "not repo_scan"`, then `uv run diff-cover` at the 90% gate
     (REQ-013, AC-12; every target row).
   - [ ] Confirm the deployed config is current: `config/agent.toml` and `registry/` are copied as-is
     by `deploy/deploy.sh`, so only the re-copy is needed; no script change (REQ-005;
     `deploy/deploy.sh` read as a reference, `config/agent.toml`, `registry/manifests/config_ownership.yaml`).
   - [ ] Run the doc checkers after the documentation edits: `uv run python tools/check_docs_quality.py`
     and `uv run python tools/check_docs_structure.py` on the changed docs, plus
     `uv run python tools/check_adr_reference.py` and `uv run python tools/check_adr_invariant_matrix.py`
     for the ADR change (REQ-012; the docs rows in Implementation Target Files).

### Release units
**Unit**: contract-and-producers | **Phases**: 2, 3, 4 | **Reason**: consumers read fields that do not exist until the vocabulary lands and producers are rejected by the extended validation until the contract lands, so no phase in this group passes validation alone.
**Unit**: config-removal-and-tests | **Phases**: 5, 6 | **Reason**: the contract tests assert the removed fields are absent, so the config layer and the tests cannot be validated separately.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/tool_metadata.py` | Unit | `uv run pytest tests/shared/test_tool_metadata.py -v` | Closed value sets, no `agent` import |
| `scripts/shared/tool_metadata.py`, `scripts/shared/runtime_tool.py`, `scripts/shared/resource_scope.py` | Import-layer and type check | `PYTHONPATH=scripts uv run lint-imports`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` | `shared` stays a leaf; no untyped value |
| `scripts/mcp_servers/server.py` and the tool-definition files | Contract test over all producers | `uv run pytest tests/mcp_servers/test_tool_schema_contract.py -v` | Every tool entry declares the extended field set; none is defaulted |
| `scripts/agent/tool_policy.py`, `scripts/agent/tool_approval.py`, `scripts/agent/tool_audit.py`, `scripts/agent/tool_runner.py` | Unit plus impact-based run | `uv run pytest tests/agent/test_tool_policy.py tests/agent/test_tool_policy_comprehensive.py tests/agent/test_tool_approval_preflight.py tests/agent/test_tool_audit.py tests/agent/test_tool_runner.py -v` | Decisions come from declared metadata; drift findings change nothing |
| `config/agent.toml` | Config-build test | `uv run pytest tests/agent/test_config_builders.py tests/agent/test_config_dataclasses.py tests/agent/services/test_config_reload.py tests/agent/test_production_config_validator.py -v` | Removed keys are absent and rejected; operational exceptions still work |
| `registry/manifests/config_ownership.yaml` | Ownership checker | `uv run python tools/check_config_ownership.py` | No entry for a removed field |
| Every target row | Full suite and coverage gate | `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan"`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | No new failure beyond the recorded baseline |

## Risks
- **Risk**: 35 test files reference the removed config maps, and only the ~21 with direct assertions or
  shared fixtures are in scope → **Mitigation**: the remaining fixture-only files are recorded as the
  follow-up test-audit work item; the full-suite run shows whether any of them fails before the
  migration, and a failure there is reported rather than silently fixed here.
- **Risk**: removing a config field changes the hot-reload field set and the startup validation
  behavior, and existing deployed configurations may still contain the sections → **Mitigation**: the
  config-build path rejects the removed keys as unknown, so a stale deployed `config/agent.toml` fails
  at startup with a named key; the deployment step re-copies `config/agent.toml` and no compatibility
  reader is added.
- **Risk**: the ADR decision/invariant change needs a maintainer approval record → **Mitigation**: the
  approval record is added in the same change; this Plan records the requirement and does not assume
  the approval, and Phase 1 stops if the approval is not given.
- **Risk**: `scripts/agent/tool_policy.py` (584 lines) and `scripts/shared/resource_scope.py` grow when
  the authority is inverted → **Mitigation**: the typed vocabulary lives in a separate module so the
  dataclass stays small; `uv run python tools/check_module_size.py` is part of the gates, and the
  baseline has no entry for these files (limit 24576 bytes each).
- **Risk**: the field-set version decision (UNK-01) may require a producer-visible version number,
  which could break the current `/v1/tools` contract tests → **Mitigation**: the envelope version stays
  unchanged; only the required field set grows, and the version is recorded in one place.
- **Risk**: the boundary with the preview and call-state issues is not planned yet, so the capability
  flag names may change → **Mitigation**: this Plan defines only the flag and the closed values; the
  decision rules and the call-state fields stay out of scope.
- **Risk**: `docs/` statements about the classification priority are spread across several MCP reference
  docs → **Mitigation**: the primary docs are target rows; the secondary sweep is a follow-up doc work
  item, and the doc checkers are run for any changed doc.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: decision gate and ADR approval record | Completed | — | 20261121-203335 | Maintainer approval recorded 2026-11-21 (UNK-03, UNK-04 resolved); the ADR procedure was generated in this pass (20261121-115519) |
| 2 | Phase 2: typed vocabulary and field-set validation | Completed | — | 20261121-203335 | 3 procedure documents generated (pass 20261121-115519); field-set version decided as `2.1` (UNK-01, owner decision 2026-11-21) |
| 3 | Phase 3: producer declarations | Completed | — | 20261121-203335 | 13 tool-definition files plus the schema contract 15 procedure documents generated (pass 20261121-115519) |
| 4 | Phase 4: consumer migration and constants demotion | Completed | — | 20261121-203335 | Release unit: contract-and-producers 16 procedure documents generated (pass 20261121-115519); field names undecided (UNK-02, UNK-05, UNK-06) |
| 5 | Phase 5: configuration layer removal | Completed | — | 20261121-203335 | Release unit: config-removal-and-tests 7 procedure documents generated (pass 20261121-115519) |
| 6 | Phase 6: contract tests | Completed | — | 20261121-203335 | Fixture-only test files are out of scope (see Risks) 9 procedure documents generated (pass 20261121-115519); fixture-only test files stay with the test-audit follow-up |
| 7 | Phase 7: validation gates, deployment check, doc checkers | Completed | — | 20261121-203335 | Baseline: 1 known pre-existing failure, 13182 passed, 5 skipped |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | ADR decision/invariant change requires a maintainer approval record (UNK-03, UNK-04) | Yes | 2026-11-21 |
| 3 | Field-set version number for the extended per-tool contract is not decided (UNK-01) | Yes | 2026-11-21 |
| 4 | Per-server tool-list scope and the preview/call-state field names are undecided (UNK-02, UNK-05, UNK-06) | No | — |
| 7 | Full-suite baseline contains one known pre-existing failure not caused by this change | N/A: not a blocker for this Plan's scope | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| test-audit follow-up: migrate the test files that use the removed config maps only as fixtures (~14 files) | 6 | Test | Pending | QA | N/A: not scheduled |
| doc sweep: MCP reference docs that state the current classification priority | 7 | Doc Change | Pending | Docs | N/A: not scheduled |
| ADR approval record for the constants-to-drift-only and `RETRYABLE_TOOLS` ownership change | 1 | Code Change | Completed | Maintainer | 20261121-202456 (procedure 20261121-115519_67: amendment record in ADR-003 `Approval`, Decision Details #5 and #18) |
| implementations/20261121-115519_01_scripts_shared_tool_metadata.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261121-115519_02_scripts_shared_runtime_tool.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261121-115519_03_scripts_shared_resource_scope.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261121-115519_04_scripts_shared_runtime_tool_registry.py.md | 4 | Procedure | Completed | — | — |
| implementations/20261121-115519_05_scripts_shared_tool_constants.py.md | 4 | Procedure | Completed | — | — |
| implementations/20261121-115519_06_scripts_shared_mcp_dedup.py.md | 4 | Procedure | Completed | — | — |
| implementations/20261121-115519_07_scripts_shared_tool_routing_validation.py.md | 4 | Procedure | Completed | — | — |
| implementations/20261121-115519_08_scripts_mcp_servers_server.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-115519_09_scripts_mcp_servers_cicd_cicd_tools.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-115519_10_scripts_mcp_servers_file_read_tools.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-115519_11_scripts_mcp_servers_file_write_tools.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-115519_12_scripts_mcp_servers_file_delete_tools.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-115519_13_scripts_mcp_servers_git_git_tools.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-115519_14_scripts_mcp_servers_github_tools_file.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-115519_15_scripts_mcp_servers_github_tools_issues.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-115519_16_scripts_mcp_servers_github_tools_pull_requests.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-115519_17_scripts_mcp_servers_github_tools_repository.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-115519_18_scripts_mcp_servers_mdq_mdq_tools.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-115519_19_scripts_mcp_servers_rag_pipeline_rag_pipeline_tools.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-115519_20_scripts_mcp_servers_shell_shell_tools.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-115519_21_scripts_mcp_servers_web_search_web_search_tools.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-115519_22_scripts_agent_tool_policy.py.md | 4 | Procedure | Completed | — | — |
| implementations/20261121-115519_23_scripts_agent_tool_approval.py.md | 4 | Procedure | Completed | — | — |
| implementations/20261121-115519_24_scripts_agent_tool_audit.py.md | 4 | Procedure | Completed | — | — |
| implementations/20261121-115519_25_scripts_agent_tool_runner.py.md | 4 | Procedure | Completed | — | — |
| implementations/20261121-115519_26_scripts_agent_production_config_validator.py.md | 4 | Procedure | Completed | — | — |
| implementations/20261121-115519_27_scripts_agent_startup_validation.py.md | 4 | Procedure | Completed | — | — |
| implementations/20261121-115519_28_scripts_agent_services_config_validators.py.md | 5 | Procedure | Completed | — | — |
| implementations/20261121-115519_29_scripts_agent_services_config_field_registry.py.md | 5 | Procedure | Completed | — | — |
| implementations/20261121-115519_30_scripts_agent_config_dataclasses.py.md | 5 | Procedure | Completed | — | — |
| implementations/20261121-115519_31_scripts_agent_config_section_builders.py.md | 5 | Procedure | Completed | — | — |
| implementations/20261121-115519_32_config_agent.toml.md | 5 | Procedure | Completed | — | — |
| implementations/20261121-115519_33_registry_manifests_config_ownership.yaml.md | 5 | Procedure | Completed | — | — |
| implementations/20261121-115519_34_scripts_agent_services_mcp_status.py.md | 4 | Procedure | Completed | — | — |
| implementations/20261121-115519_35_scripts_agent_services_config_service_sync.py.md | 4 | Procedure | Completed | — | — |
| implementations/20261121-115519_36_scripts_agent_commands_cmd_config_display.py.md | 4 | Procedure | Completed | — | — |
| implementations/20261121-115519_37_scripts_agent_services_routing_drift.py.md | 4 | Procedure | Completed | — | — |
| implementations/20261121-115519_38_scripts_agent_services_mcp_tool_discovery.py.md | 4 | Procedure | Completed | — | — |
| implementations/20261121-115519_39_scripts_agent_services_mcp_tool_discovery_registry.py.md | 4 | Procedure | Completed | — | — |
| implementations/20261121-115519_43_tests_shared_test_runtime_tool_registry.py.md | 6 | Procedure | Completed | — | — |
| implementations/20261121-115519_45_tests_shared_test_tool_safety_tiers.py.md | 6 | Procedure | Completed | — | — |
| implementations/20261121-115519_47_tests_mcp_servers_test_tool_schema_contract.py.md | 6 | Procedure | Completed | — | — |
| implementations/20261121-115519_49_tests_agent_test_tool_policy_comprehensive.py.md | 6 | Procedure | Completed | — | — |
| implementations/20261121-115519_51_tests_agent_test_tool_approval_risk.py.md | 6 | Procedure | Completed | — | — |
| implementations/20261121-115519_52_tests_agent_test_agent_repl_tool_exec.py.md | 6 | Procedure | Completed | — | — |
| implementations/20261121-115519_56_tests_agent__config_test_defaults.py.md | 6 | Procedure | Completed | — | — |
| implementations/20261121-115519_57_tests_agent_test_config_builders.py.md | 6 | Procedure | Completed | — | — |
| implementations/20261121-115519_59_tests_agent_services_test_config_reload.py.md | 6 | Procedure | Completed | — | — |
| implementations/20261121-115519_62_docs_23_agent_agent_06_02_tool-execution-and-approval-approval.md.md | 7 | Procedure | Completed | — | — |
| implementations/20261121-115519_63_docs_23_agent_agent_06_04_tool-execution-and-approval-canonical.md.md | 7 | Procedure | Completed | — | — |
| implementations/20261121-115519_64_docs_23_agent_agent_08_03_configuration-tools-memory.md.md | 7 | Procedure | Completed | — | — |
| implementations/20261121-115519_65_docs_23_agent_agent_08_04_configuration-mcp-approval-obs.md.md | 7 | Procedure | Completed | — | — |
| implementations/20261121-115519_66_docs_91_security_security_02_high-risk-tool-common-policy.md.md | 7 | Procedure | Completed | — | — |
| implementations/20261121-115519_67_docs_10_adr_adr_02_02_003_agent-runtime-tool-registry-routing-authority.md.md | 1 | Procedure | Completed | — | — |
| implementations/20261121-115519_68_scripts_mcp_servers_models.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261121-115519_69_scripts_agent_constants.py.md | 5 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261121-105007
- **Related target files**: `scripts/shared/tool_metadata.py`, `scripts/shared/runtime_tool.py`, `scripts/shared/resource_scope.py`, `scripts/shared/runtime_tool_registry.py`, `scripts/shared/tool_constants.py`, `scripts/shared/mcp_dedup.py`, `scripts/shared/tool_routing_validation.py`, `scripts/mcp_servers/server.py`, `scripts/mcp_servers/cicd/cicd_tools.py`, `scripts/mcp_servers/file/read_tools.py`, `scripts/mcp_servers/file/write_tools.py`, `scripts/mcp_servers/file/delete_tools.py`, `scripts/mcp_servers/git/git_tools.py`, `scripts/mcp_servers/github/tools_file.py`, `scripts/mcp_servers/github/tools_issues.py`, `scripts/mcp_servers/github/tools_pull_requests.py`, `scripts/mcp_servers/github/tools_repository.py`, `scripts/mcp_servers/mdq/mdq_tools.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_tools.py`, `scripts/mcp_servers/shell/shell_tools.py`, `scripts/mcp_servers/web_search/web_search_tools.py`, `scripts/agent/tool_policy.py`, `scripts/agent/tool_approval.py`, `scripts/agent/tool_audit.py`, `scripts/agent/tool_runner.py`, `scripts/agent/production_config_validator.py`, `scripts/agent/startup_validation.py`, `scripts/agent/services/config_validators.py`, `scripts/agent/services/config_field_registry.py`, `scripts/agent/config_dataclasses.py`, `scripts/agent/config_section_builders.py`, `config/agent.toml`, `registry/manifests/config_ownership.yaml`, `scripts/agent/services/mcp_status.py`, `scripts/agent/services/config_service_sync.py`, `scripts/agent/commands/cmd_config_display.py`, `scripts/agent/services/routing_drift.py`, `scripts/agent/services/mcp_tool_discovery.py`, `scripts/agent/services/mcp_tool_discovery_registry.py`, `tests/shared/test_tool_metadata.py`, `tests/shared/test_runtime_tool.py`, `tests/shared/runtime_tool_factory.py`, `tests/shared/test_runtime_tool_registry.py`, `tests/shared/test_resource_scope.py`, `tests/shared/test_tool_safety_tiers.py`, `tests/shared/test_tool_constants.py`, `tests/mcp_servers/test_tool_schema_contract.py`, `tests/agent/test_tool_policy.py`, `tests/agent/test_tool_policy_comprehensive.py`, `tests/agent/test_tool_approval_preflight.py`, `tests/agent/test_tool_approval_risk.py`, `tests/agent/test_agent_repl_tool_exec.py`, `tests/agent/test_tool_audit.py`, `tests/agent/test_tool_runner.py`, `tests/agent/test_production_config_validator.py`, `tests/agent/_config_test_defaults.py`, `tests/agent/test_config_builders.py`, `tests/agent/test_config_dataclasses.py`, `tests/agent/services/test_config_reload.py`, `tests/agent/commands/test_agent_cmd_config.py`, `tests/agent/shared/test_startup_validation_pipeline.py`, `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`, `docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md`, `docs/23_agent/agent_08_03_configuration-tools-memory.md`, `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`, `docs/91_security/security_02_high-risk-tool-common-policy.md`, `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`, `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`, `docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md`, `docs/23_agent/agent_08_03_configuration-tools-memory.md`, `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`, `docs/91_security/security_02_high-risk-tool-common-policy.md`, `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`, `scripts/mcp_servers/models.py`, `scripts/agent/constants.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue: "Move the current static constants to typed fields on RuntimeTool" | `scripts/shared/tool_metadata.py` | Phase 2 | AC-01 | T-01 | Explicit in issue |
| REQ-001 | Issue: closed values, no new shared constant | `tests/shared/test_tool_metadata.py` | Phase 6 | AC-01 | T-01 | Derived from confirmed evidence |
| REQ-002 | Issue: "When required runtime metadata is absent, the Agent must fail closed" | `scripts/shared/runtime_tool.py` | Phase 2 | AC-02 | T-02 | Explicit in issue |
| REQ-002 | Issue: the tier must be declared, not defaulted; `build_runtime_tool()` requires the schema-2.0 fields | `scripts/shared/resource_scope.py` | Phase 2 | AC-02 | T-02 | Confirmed by repository evidence |
| REQ-002 | Issue: no default that lowers risk | `tests/shared/test_runtime_tool.py` | Phase 6 | AC-02 | T-02 | Derived from confirmed evidence |
| REQ-002 | Shared fixture must supply the required fields | `tests/shared/runtime_tool_factory.py` | Phase 6 | AC-02 | T-02 | Confirmed by repository evidence |
| REQ-002 | Registration path builds tools with the required field set | `scripts/agent/services/mcp_tool_discovery_registry.py` | Phase 4 | AC-02, AC-03 | T-02 | Confirmed by repository evidence |
| REQ-002 | Fail-closed startup text for a missing declared value | `scripts/agent/startup_validation.py` | Phase 4 | AC-02, AC-10 | T-09 | Confirmed by repository evidence |
| REQ-003 | Issue: the MCP contract must declare per-tool capabilities | `scripts/mcp_servers/server.py` | Phase 3 | AC-03 | T-03 | Explicit in issue |
| REQ-003 | Producer declarations | `scripts/mcp_servers/cicd/cicd_tools.py` | Phase 3 | AC-03 | T-03 | Confirmed by repository evidence |
| REQ-003 | Producer declarations | `scripts/mcp_servers/file/read_tools.py` | Phase 3 | AC-03 | T-03 | Confirmed by repository evidence |
| REQ-003 | Producer declarations | `scripts/mcp_servers/file/write_tools.py` | Phase 3 | AC-03 | T-03 | Confirmed by repository evidence |
| REQ-003 | Producer declarations | `scripts/mcp_servers/file/delete_tools.py` | Phase 3 | AC-03 | T-03 | Confirmed by repository evidence |
| REQ-003 | Producer declarations | `scripts/mcp_servers/git/git_tools.py` | Phase 3 | AC-03 | T-03 | Confirmed by repository evidence |
| REQ-003 | Producer declarations | `scripts/mcp_servers/github/tools_file.py` | Phase 3 | AC-03 | T-03 | Confirmed by repository evidence |
| REQ-003 | Producer declarations | `scripts/mcp_servers/github/tools_issues.py` | Phase 3 | AC-03 | T-03 | Confirmed by repository evidence |
| REQ-003 | Producer declarations | `scripts/mcp_servers/github/tools_pull_requests.py` | Phase 3 | AC-03 | T-03 | Confirmed by repository evidence |
| REQ-003 | Producer declarations | `scripts/mcp_servers/github/tools_repository.py` | Phase 3 | AC-03 | T-03 | Confirmed by repository evidence |
| REQ-003 | Producer declarations | `scripts/mcp_servers/mdq/mdq_tools.py` | Phase 3 | AC-03 | T-03 | Confirmed by repository evidence |
| REQ-003 | Producer declarations | `scripts/mcp_servers/rag_pipeline/rag_pipeline_tools.py` | Phase 3 | AC-03 | T-03 | Confirmed by repository evidence |
| REQ-003 | Producer declarations | `scripts/mcp_servers/shell/shell_tools.py` | Phase 3 | AC-03 | T-03 | Confirmed by repository evidence |
| REQ-003 | Producer declarations | `scripts/mcp_servers/web_search/web_search_tools.py` | Phase 3 | AC-03 | T-03 | Confirmed by repository evidence |
| REQ-003 | Field-set contract test over every producer | `tests/mcp_servers/test_tool_schema_contract.py` | Phase 6 | AC-03 | T-03 | Confirmed by repository evidence |
| REQ-004 | Issue: consumers must read declared metadata | `scripts/agent/tool_policy.py` | Phase 4 | AC-04 | T-04 | Confirmed by repository evidence |
| REQ-004 | Issue: no inference from tool names | `scripts/agent/tool_approval.py` | Phase 4 | AC-04, AC-08 | T-04, T-07 | Confirmed by repository evidence |
| REQ-004 | Issue: audit must use the canonical vocabulary | `scripts/agent/tool_audit.py` | Phase 4 | AC-04, AC-07 | T-04, T-06 | Confirmed by repository evidence |
| REQ-004 | Issue: retry classification from metadata | `scripts/agent/tool_runner.py` | Phase 4 | AC-04, AC-09 | T-04, T-08 | Confirmed by repository evidence |
| REQ-004 | Tier-derived status display | `scripts/agent/services/mcp_status.py` | Phase 4 | AC-04 | T-04 | Confirmed by repository evidence |
| REQ-004 | Tier mapping source | `scripts/agent/services/config_service_sync.py` | Phase 4 | AC-04 | T-04 | Confirmed by repository evidence |
| REQ-004 | Policy application must not override from config | `scripts/shared/runtime_tool_registry.py` | Phase 4 | AC-04 | T-02 | Confirmed by repository evidence |
| REQ-005 | Issue: config keeps only operational exceptions | `config/agent.toml` | Phase 5 | AC-05 | T-05 | Explicit in issue |
| REQ-005 | Field definitions for the removed maps | `scripts/agent/config_dataclasses.py` | Phase 5 | AC-05 | T-05 | Confirmed by repository evidence |
| REQ-005 | Builders and `_validate_dry_run_tools` for the removed maps | `scripts/agent/config_section_builders.py` | Phase 5 | AC-05 | T-05 | Confirmed by repository evidence |
| REQ-005 | Field registry entries for the removed fields | `scripts/agent/services/config_field_registry.py` | Phase 5 | AC-05 | T-05 | Confirmed by repository evidence |
| REQ-005 | Ownership manifest entries | `registry/manifests/config_ownership.yaml` | Phase 5 | AC-05 | `uv run python tools/check_config_ownership.py` | Confirmed by repository evidence |
| REQ-005 | Display of the removed maps | `scripts/agent/commands/cmd_config_display.py` | Phase 4 | AC-05 | T-05 | Confirmed by repository evidence |
| REQ-006 | Issue: `plan_blocked_tools` documented as an exception rule | `scripts/agent/tool_policy.py` | Phase 4 | AC-06 | T-04 | Derived from confirmed evidence |
| REQ-006 | Exception denylist stays in config | `config/agent.toml` | Phase 5 | AC-06 | T-05 | Derived from confirmed evidence |
| REQ-007 | Issue: static constants become drift detection only | `scripts/shared/tool_constants.py` | Phase 4 | AC-04, AC-10 | T-09 | Explicit in issue |
| REQ-007 | Priority inversion in `classify_operation_type()` | `scripts/agent/tool_policy.py` | Phase 4 | AC-04, AC-10 | T-04, T-09 | Confirmed by repository evidence |
| REQ-007 | `RETRYABLE_TOOLS` ownership moved | `scripts/shared/mcp_dedup.py` | Phase 4 | AC-09 | T-08 | Confirmed by repository evidence |
| REQ-007 | Drift checks without decision effect | `scripts/shared/tool_routing_validation.py` | Phase 4 | AC-10 | T-09 | Confirmed by repository evidence |
| REQ-007 | Drift report path | `scripts/agent/services/routing_drift.py` | Phase 4 | AC-10 | T-09 | Confirmed by repository evidence |
| REQ-007 | Write-classification drift against reference data | `scripts/agent/services/mcp_tool_discovery.py` | Phase 4 | AC-10 | T-09 | Confirmed by repository evidence |
| REQ-008 | Issue: typed resource-key classification | `scripts/shared/resource_scope.py` | Phase 2 | AC-07 | T-06 | Explicit in issue |
| REQ-008 | Key-kind consumers | `tests/shared/test_resource_scope.py` | Phase 6 | AC-07 | T-06 | Derived from confirmed evidence |
| REQ-009 | Issue: typed preview capability flags | `scripts/agent/tool_approval.py` | Phase 4 | AC-08 | T-07 | Explicit in issue |
| REQ-009 | Capability-flag test | `tests/agent/test_tool_approval_preflight.py` | Phase 6 | AC-08 | T-07 | Derived from confirmed evidence |
| REQ-010 | Issue: idempotency and reconciliation boundary | `scripts/shared/mcp_dedup.py` | Phase 4 | AC-09 | T-08 | Explicit in issue |
| REQ-010 | Typed field vocabulary for the boundary | `scripts/shared/tool_metadata.py` | Phase 2 | AC-09 | T-01 | Derived from confirmed evidence |
| REQ-011 | Issue: no compatibility reader for removed maps | `scripts/agent/production_config_validator.py` | Phase 4 | AC-05 | T-05 | Explicit in issue |
| REQ-011 | Single source per concept | `tests/agent/test_production_config_validator.py` | Phase 6 | AC-05 | T-05 | Derived from confirmed evidence |
| REQ-012 | Issue: ADR decision/invariant change needs an approval record | `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Phase 1, Phase 7 | AC-11 | `uv run python tools/check_adr_reference.py` | Explicit in issue |
| REQ-012 | Approval-priority statement | `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` | Phase 7 | AC-11 | `uv run python tools/check_docs_structure.py` | Confirmed by repository evidence |
| REQ-012 | Canonical level source | `docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md` | Phase 7 | AC-11 | `uv run python tools/check_docs_structure.py` | Confirmed by repository evidence |
| REQ-012 | Config-key documentation | `docs/23_agent/agent_08_03_configuration-tools-memory.md` | Phase 7 | AC-11 | `uv run python tools/check_docs_structure.py` | Confirmed by repository evidence |
| REQ-012 | Config-key documentation | `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` | Phase 7 | AC-11 | `uv run python tools/check_docs_structure.py` | Confirmed by repository evidence |
| REQ-012 | Fail-closed table | `docs/91_security/security_02_high-risk-tool-common-policy.md` | Phase 7 | AC-11 | `uv run python tools/check_docs_structure.py` | Confirmed by repository evidence |
| REQ-013 | Contract tests, grouped by area T-01..T-10 | `tests/shared/test_tool_metadata.py` | Phase 6 | AC-12 | T-01 | Derived from confirmed evidence |
| REQ-013 | Authority tests | `tests/agent/test_tool_policy.py` | Phase 6 | AC-12 | T-04 | Derived from confirmed evidence |
| REQ-013 | Priority-inversion test | `tests/agent/test_tool_policy_comprehensive.py` | Phase 6 | AC-12 | T-04, T-09 | Derived from confirmed evidence |
| REQ-013 | Preflight capability test | `tests/agent/test_tool_approval_risk.py` | Phase 6 | AC-12 | T-04 | Derived from confirmed evidence |
| REQ-013 | REPL execution tier test | `tests/agent/test_agent_repl_tool_exec.py` | Phase 6 | AC-12 | T-04 | Derived from confirmed evidence |
| REQ-013 | Audit key-kind test | `tests/agent/test_tool_audit.py` | Phase 6 | AC-12 | T-04, T-06 | Derived from confirmed evidence |
| REQ-013 | Retry-class test | `tests/agent/test_tool_runner.py` | Phase 6 | AC-12 | T-04, T-08 | Derived from confirmed evidence |
| REQ-013 | Tier drift test | `tests/shared/test_tool_safety_tiers.py` | Phase 6 | AC-12 | T-09 | Derived from confirmed evidence |
| REQ-013 | Reference-role test | `tests/shared/test_tool_constants.py` | Phase 6 | AC-12 | T-08, T-09 | Derived from confirmed evidence |
| REQ-013 | Registry policy test | `tests/shared/test_runtime_tool_registry.py` | Phase 6 | AC-12 | T-02 | Derived from confirmed evidence |
| REQ-013 | Config-build test group | `tests/agent/test_config_builders.py` | Phase 6 | AC-12 | T-05 | Derived from confirmed evidence |
| REQ-013 | Dataclass test group | `tests/agent/test_config_dataclasses.py` | Phase 6 | AC-12 | T-05 | Derived from confirmed evidence |
| REQ-013 | Hot-reload test group | `tests/agent/services/test_config_reload.py` | Phase 6 | AC-12 | T-05 | Derived from confirmed evidence |
| REQ-013 | Display test group | `tests/agent/commands/test_agent_cmd_config.py` | Phase 6 | AC-12 | T-05 | Derived from confirmed evidence |
| REQ-013 | Startup pipeline test group | `tests/agent/shared/test_startup_validation_pipeline.py` | Phase 6 | AC-12 | T-09 | Derived from confirmed evidence |
| REQ-013 | Shared fixture helper | `tests/agent/_config_test_defaults.py` | Phase 6 | AC-12 | T-05 | Derived from confirmed evidence |
| REQ-003 | Amendment 2026-11-21: McpTool TypedDict carries the extended per-tool required field set; resource_scope_keys value type becomes the key-to-kind mapping | scripts/mcp_servers/models.py | Phase 3 | N/A: none cites REQ-003 | tests/mcp_servers/test_tool_schema_contract.py | Confirmed by repository evidence |
| REQ-011 | Amendment 2026-11-21: Remove the default constants for the removed maps (dead definitions once the fields and builders are removed); the declared metadata is the only source | scripts/agent/constants.py | Phase 5 | N/A: none cites REQ-011 | N/A: no test asserts these constants | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261121-115519 -->
