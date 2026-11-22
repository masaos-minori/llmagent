# Plan: Replace the shared dedup configuration file with process-owned typed settings

## Goal
- Remove `config/mcp_dedup.toml` as a config file that no process owns. Each MCP server process gets its dedup store settings only from its own `config/{server}_mcp_server.toml` `[dedup]` section, injected at bootstrap as an immutable typed config; the dedup modules perform no config discovery and keep no module cache. Agent call policy is read only from `config/agent.toml`. The store-behavior fingerprint already written at first init is compared on every reopen, so a process whose validated parameters differ from the store's does not start.

## Priority
Medium

## Scope
- **In-Scope**:
  - Rename the store config type to `DedupStoreConfig` (no `retry_class` field) and inject it per process; no filesystem discovery and no cache in the dedup modules.
  - `[dedup]` sections in all ten `config/*_mcp_server.toml` files with identical shared-store values (all ten processes can dispatch through the one shared store), isolated by `ConfigLoader.restrict_to()` and strictly validated plus range-checked by `load_dedup_section()` at injection.
  - Agent-side call-policy ownership in `config/agent.toml`: `pending_timeout_minutes` stays the authoritative stale-pending timeout; approval-grant expiry moves from the `tool_approval` module constant `_GRANT_TTL_SECONDS` to an `AgentConfig` field with the same default value (no lifetime change).
  - Removal of the `[retry_class]` mirror and its loader validation; the declared `retry_policy` tool metadata (already the classification authority) becomes the only retry-class read path in the dispatcher.
  - Reopen-time fingerprint enforcement in the dedup store with a new refusal state `identity_mismatch`.
  - Removal of `config/mcp_dedup.toml`, its deploy copy, and every reference in `deploy/init_db.sh`, `scripts/shared/execution_snapshot.py`, `tools/check_db_separation.py`, and tests.
  - Documentation updates for the ownership map and the new refusal state.
- **Out-of-Scope**:
  - Call-state control API, `control_api` DDL, `MCP_CONTROL_API_TOKEN`, and control endpoints (issue mcpdl004 backlog item; a separate work item).
  - Retention/capacity monitor settings and the history cap (issue mcpdl005 backlog item).
  - RAG-side and other database config ownership changes owned by the config-ownership-split plan (issue agentcfg004).
  - Any change to `retry_policy` metadata content or to approval-grant lifetime semantics (only the config ownership of the horizon moves; the default value stays 300.0).
  - Splitting the single shared store `mcp_dedup.sqlite` into per-server databases; the store stays shared and the fingerprint comparison enforces cross-server parameter agreement.
- **Dependencies**:
  - Depends on the already-implemented store-identity-continuity work (issue mcpdl002) for the fingerprint inputs (`store_meta` identity rows, `config_fingerprint`, typed `DedupStoreError(state)` refusal model) and the already-implemented runtime-tool-metadata work (issue agentcfg003) that made `retry_policy` declarations the classification authority (issue mcpdl003 Out-of-Scope items are those two issues' scopes).
  - **Depends on**: `plans/done/20261121-140444_agentcfg004_config-ownership-split.md` | phase all | both edit `config/agent.toml` and `scripts/agent/production_config_validator.py`, and that plan freezes which config keys `AgentConfig` owns; its 32 procedures are generated but not yet applied, so this plan's implementation lands after it and re-verifies `tests/agent/test_http_lifecycle_env_allowlist_integration.py`, whose allowlist currently lists `mcp_dedup.toml` as read-by-agent.
  - Ordering note (recorded by id, not a wait): the open mcpdd001 (dedup-keyless-config-gate) and mcpai006 (github-write-retry-policy) issues state that they are implemented after this plan, so their settings land in the typed store config and classification constants; their future plans must be generated after this plan lands (mcpdd001's range-bound gap is already closed by the implemented mcpdl002 loader bounds).

## Background
- `config/mcp_dedup.toml` predates the per-server config model. Its `[dedup]` section is read by every server process through the lazy singleton `scripts/mcp_servers/dispatch.py::_dedup_context()` (line 171), which calls `scripts/shared/mcp_dedup_config.py::load_dedup_config()` — path-discovery loader with a module-level cache. Its `[retry_class]` section is a load-validated mirror of `scripts/shared/tool_constants.py` `RETRYABLE_TOOLS` and feeds `dispatch.py`'s retry decisions (line 329) even though each tool's declared `retry_policy` metadata is already the owner.
- Agent-side call policy already lives in `config/agent.toml`: top-level `pending_timeout_minutes` (line 30) feeds `AgentConfig` (line 378) → `WorkflowEngine`, and approval-grant expiry is the `scripts/agent/tool_approval.py` constant `_GRANT_TTL_SECONDS = 300.0` (line 51). The shared file duplicates these semantics as a second source with no owner.
- The issue's unresolved question ("which MCP processes read `config/mcp_dedup.toml` today") is resolved by source reading: every process that dispatches through `dispatch_tool()` (all ten MCP servers) reaches `_dedup_context()`; `deploy/init_db.sh` (line 128) and `scripts/shared/execution_snapshot.py` (lines 148-156) also read it; `scripts/agent/production_config_validator.py` does not (only a comment at line 170).

## Problem
- A server process opens the dedup store with parameters discovered from a shared file rather than injected from its own validated transport config; `load_dedup_config()` resolves the path relative to the repo root or cwd (unpredictable under production launchers with relative config paths) and caches the result for the process lifetime.
- `scripts/shared/mcp_dedup.py::_first_initialization` writes `config_fingerprint` into `store_meta`, but `_classify_existing` never compares it on reopen, so the shared store can be reopened under a different validated parameter set, breaking frozen-store continuity.
- The loader validates a `retry_class` map that duplicates the `retry_policy` metadata authority, keeping the shared file in the dependency graph of dispatcher retry semantics and of the `RETRYABLE_TOOLS` drift test.

## Reason for Change
- ADR-002 config isolation and the ADR-008 / db_08 config-ownership boundary require each config surface to have one owner and forbid a config file that is a second source of a runtime authority; the shared file is exactly that. The issue also orders this work before the open keyless-config-gate (mcpdd001) and github-write-retry-policy (mcpai006) issues so their settings land in the typed configuration instead of the removed file.

## Implementation Intent
- Keep store behavior unchanged: no new store-semantics keys, no DDL, no migration. Move ownership only: per-server `[dedup]` table → typed immutable config injected once at server bootstrap; Agent call policy stays in `config/agent.toml` with the approval-grant horizon promoted from a module constant to a config field with identical default. Delete the discovery loader, the cache, and the `[retry_class]` validation; replace the dispatcher's mirror-based retry lookup with the registry metadata lookup. Activate the already-stored fingerprint as a reopen gate. Remove the file and every operational reference last, gated by a production fingerprint check.

## Requirements
- `REQ-001`: Each MCP process reads only its own `config/{server}_mcp_server.toml` `[dedup]` section for store settings, parsed into an immutable typed `DedupStoreConfig` and injected at bootstrap (`DedupStoreConfig`, injected `open_dedup_store()`), enforced through the existing `own_config_file` + `ConfigLoader.restrict_to()` bootstrap.
- `REQ-002`: The Agent reads call policy only from `config/agent.toml`: `pending_timeout_minutes` remains the only stale-pending timeout read by `WorkflowEngine`/`tool_call_state_ops`, and approval-grant lifetime becomes an `AgentConfig` field defaulting to the current constant value. The issue's `[mcp_call]` key set (logical-id format, write-idempotency requirement, reconciliation enablement, mandatory state recording) maps to existing Agent-side code defaults and the agentcfg004 ownership map; no new keys beyond the grant horizon are invented (UNK-01).
- `REQ-003`: The dedup modules perform no directory discovery, no TOML reading, and keep no module-level cache: remove `load_dedup_config()` discovery, `_default_config_path()`, `_DEDUP_CONFIG_CACHE`, and `clear_dedup_config_cache()`; the replacement `load_dedup_section()` is a pure function over an already-loaded mapping.
- `REQ-004`: `config/mcp_dedup.toml` is removed from the repository, from the deploy copy list, and from every runtime and tool reference; it is not kept as an alias (Current-Specification-Only).
- `REQ-005`: The `[retry_class]` mirror and its loader validation are removed; `retry_policy` tool metadata is the sole retry-class authority, with the unknown-tool fallback kept as non-retryable through the existing inline default (`retry_policy_is_retryable(None)` is False; no named fallback constant exists in current source — corrected 2026-11-22, the prior `DEFAULT_RETRY_CLASS` name was unfounded) and `RETRYABLE_TOOLS` kept as reference/drift data.
- `REQ-006`: Strict validation: reject invalid types, booleans used as integers, unknown fields, unsafe paths (`db_path` outside the dedup database directory contract), and a missing `[dedup]` section; startup fails fast with a file-and-key-specific `ConfigParseError`/`ConfigMissingError` (typed errors of `shared.config_errors` carrying `dedup.<key>`-prefixed messages, as the current loader does — corrected 2026-11-22: no `DedupConfigError` type exists in current source) before any store opens.
- `REQ-007`: Fingerprint only shared-store behavior (the existing `config_fingerprint` over validated store parameters): a reopen whose injected fingerprint differs from the stored `store_meta.config_fingerprint` raises `DedupStoreError("identity_mismatch")` before any query; process-local settings outside the fingerprinted set may differ (in this design all ten sections carry identical shared-store values).
- `REQ-008`: Store behavior is unchanged: the four existing refusal states (`lost`, `replaced`, `legacy_or_unverified`, `schema_mismatch`), overlay-only degradation, pending-claim, replay, lease-reconciliation, and audit payload semantics are preserved for every non-mismatch path.
- `REQ-009`: Tests cover process config isolation, strict parser and unknown-field validation, missing section, cross-process fingerprint mismatch, and deployment reference validation; ruff, mypy, import-linter, and the full suite run.
- `REQ-010`: Documentation records the configuration ownership of the dedup settings and the removed file.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
| --- | --- | --- | --- | --- | --- | --- |
| scripts/shared/mcp_dedup_config.py | Loader/validation split; typed config contract | Discovery, cache, and `retry_class` validation live here | REQ-003, REQ-005, REQ-006; AC-002 | `_DEDUP_CONFIG_CACHE` (line 42), `_default_config_path()`, `_validated_retry_class()` in current source |`tests/shared/test_mcp_dedup.py`| Verified |
| scripts/shared/mcp_dedup.py | Injected-config store; reopen fingerprint gate | `open_dedup_store()` currently falls back to the discovery loader; `_classify_existing` skips the fingerprint check | REQ-001, REQ-007, REQ-008; AC-002, AC-004 | `open_dedup_store` (line 411); fingerprint written at `_first_initialization`, never compared (Step 2 read) |`tests/shared/test_mcp_dedup_identity.py`| Verified |
| scripts/mcp_servers/dispatch.py | Inject-only dedup context; metadata-first retry class | Lazy `load_dedup_config()` fallback and `retry_class(name, config)` mirror lookup live here | REQ-003, REQ-005, REQ-008; AC-002, AC-004 | `_dedup_context()` (lines 171-200), `retry_class(name, config)` call sites (lines 327, 525, 544; corrected 2026-11-22 from the earlier single "line 329" citation) |`tests/mcp_servers/test_mcp_dispatch.py`| Verified |
| scripts/mcp_servers/server.py | Bootstrap injection point | Own-config bootstrap (`own_config_file`, `ConfigLoader.restrict_to()`) is where `[dedup]` is read and injected | REQ-001, REQ-006; AC-002 | `own_config_file` (line 282), `restrict_to` (lines 340-348) |`tests/mcp_servers/test_server_idempotency_boundary.py`| Verified |
| scripts/agent/config_dataclasses.py | Agent call-policy field | Approval-grant horizon moves from module constant to `AgentConfig` | REQ-002; AC-005 | `pending_timeout_minutes` (line 378) |`tests/agent/test_config_dataclasses.py`| Verified |
| scripts/agent/config_builders.py | Agent config builder | Builder must read the new Agent-side key | REQ-002; AC-005 | `pending_timeout_minutes` read (lines 145-146) |`tests/agent/test_config_builders.py`| Verified |
| scripts/agent/production_config_validator.py | Production key validation | Key tables must cover the new Agent key and per-server `[dedup]` tables | REQ-006; AC-006 | valid-keys site (line 173); no `mcp_dedup.toml` read (line 170 comment only) |`tests/agent/test_production_config_validator.py`| Verified |
| scripts/agent/tool_approval.py | Grant expiry source | `_GRANT_TTL_SECONDS` (line 51) becomes the fallback default for the config-sourced horizon | REQ-002; AC-005 | `_issue_grant` (lines 239-254) |`tests/agent/test_tool_approval_paths.py`| Verified |
| scripts/agent/workflow/workflow_engine.py | Comment/framing only | Docstrings reference the dispatcher `[dedup]` TOML framing being removed | REQ-002; AC-005 | lines 35-37, 142 in current source |`tests/agent/workflow/test_workflow_engine.py`| Verified |
| scripts/agent/workflow/tool_call_state_ops.py | Docstring only | States the timeout comes from the dispatcher-side config | REQ-002; AC-005 | line 142 in current source |`tests/agent/workflow/test_stale_recovery_lease.py`| Verified |
| scripts/shared/execution_snapshot.py | Snapshot dedup component | `_dedup_component` reads `config/mcp_dedup.toml` directly | REQ-003, REQ-004; AC-003 | lines 148-156 (`load_dedup_config(cfg_dir / "mcp_dedup.toml")`) |`tests/shared/test_execution_snapshot.py`| Verified |
| config/agent.toml | Agent call-policy ownership | Add the approval-grant horizon key; update header comment that references the dispatcher `[dedup]` section | REQ-002; AC-005 | `pending_timeout_minutes = 10` (line 30) and header comment |`tests/agent/test_config_builders.py`| Verified |
| config/cicd_mcp_server.toml | Per-server store settings | Add `[dedup]` section | REQ-001; AC-002 | current file (no `[dedup]` today) |`tests/mcp_servers/cicd/test_cicd_server_endpoints.py`| Verified |
| config/file_delete_mcp_server.toml | Per-server store settings | Add `[dedup]` section | REQ-001; AC-002 | current file (no `[dedup]` today) |`tests/mcp_servers/file/`| Verified |
| config/file_read_mcp_server.toml | Per-server store settings | Add `[dedup]` section (uniform contract: the read server also registers the idempotency middleware and can reach `_dedup_context()`; uniformity avoids an exemption branch in the bootstrap) | REQ-001; AC-002 | `scripts/mcp_servers/server.py` middleware applies to all servers (lines 156-201) |`tests/mcp_servers/file/`| Verified |
| config/file_write_mcp_server.toml | Per-server store settings | Add `[dedup]` section | REQ-001; AC-002 | current file (no `[dedup]` today) |`tests/mcp_servers/file/`| Verified |
| config/git_mcp_server.toml | Per-server store settings | Add `[dedup]` section | REQ-001; AC-002 | current file (no `[dedup]` today) |`tests/mcp_servers/git/`| Verified |
| config/github_mcp_server.toml | Per-server store settings | Add `[dedup]` section | REQ-001; AC-002 | current file (no `[dedup]` today) |`tests/mcp_servers/github/test_github_server_endpoints.py`| Verified |
| config/mdq_mcp_server.toml | Per-server store settings | Add `[dedup]` section | REQ-001; AC-002 | current file (no `[dedup]` today) |`tests/mcp_servers/mdq/`| Verified |
| config/rag_pipeline_mcp_server.toml | Per-server store settings | Add `[dedup]` section | REQ-001; AC-002 | current file (no `[dedup]` today) |`tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py`| Verified |
| config/shell_mcp_server.toml | Per-server store settings | Add `[dedup]` section | REQ-001; AC-002 | current file (no `[dedup]` today) |`tests/mcp_servers/shell/test_shell_server_endpoints.py`| Verified |
| config/web_search_mcp_server.toml | Per-server store settings | Add `[dedup]` section (`search_web` is dispatched through the store as `non_retryable`) | REQ-001; AC-002 | `[retry_class]` entry `search_web = "non_retryable"` in config/mcp_dedup.toml |`tests/mcp_servers/web_search/`| Verified |
| config/mcp_dedup.toml | Removal | The file being eliminated (delete at Phase 4 only) | REQ-004; AC-003 | whole file; `[dedup]` + `[retry_class]` sections |`tests/tools/test_check_db_separation.py`| Verified |
| deploy/deploy.sh | Deployment reference removal | Step-2 config copy list includes `mcp_dedup.toml` | REQ-004; AC-003 | line 154 |`tests/deploy/test_init_db_schema_gate.py`| Verified |
| deploy/init_db.sh | Validation-call removal | Calls `load_dedup_config()` for the shared file (python heredoc at lines 108-175, imports at line 125, call at line 128); no `clear_dedup_config_cache()` call exists in the script (corrected 2026-11-22) | REQ-003, REQ-004; AC-003 | lines 108-175 |`tests/deploy/test_init_db_schema_gate.py`| Verified |
| tools/check_db_separation.py | Store-path registration update | Registers `("mcp_dedup.toml", "db_path")` and reads the file for the separation check | REQ-004; AC-003 | lines 17, 127, 226-227 |`tests/tools/test_check_db_separation.py`| Verified |
| tests/shared/test_mcp_dedup.py | Retarget loader tests | Tests exercise the removed discovery/cache/retry-class validation paths | REQ-003, REQ-005, REQ-006, REQ-009; AC-006 | consumer scan (`direct:tests`) |`—`| Verified |
| tests/shared/test_mcp_dedup_identity.py | Identity regression extension | Add fingerprint-drift reopen refusal and identical-config continuity cases | REQ-007, REQ-009; AC-004 | existing identity-state tests (Step 2 read) |`—`| Verified |
| tests/shared/test_mcp_dedup_concurrency.py | Fixture update | Uses cache-clear/discovery fixtures | REQ-003; AC-002 | consumer scan (`direct:tests`) |`—`| Verified |
| tests/shared/test_execution_snapshot.py | Fixture update | Exercises the `mcp_dedup.toml` fallback path | REQ-003; AC-003 | consumer scan (`direct:tests`) |`—`| Verified |
| tests/shared/test_tool_constants.py | Drift-test retarget | `RETRYABLE_TOOLS` drift check currently compares against the TOML mirror | REQ-005; AC-006 | agentcfg003 verification note in tools/_agentcfg003_content_shared.py line 241 |`—`| Verified |
| tests/mcp_servers/test_mcp_dispatch.py | Dispatcher fixtures and degradation cases | Replaces dedup globals fixtures; overlay-only degradation assertions must survive | REQ-003, REQ-005, REQ-008, REQ-009 | imports of `DedupConfig`/`DedupStore` (lines 334, 374, 569) |`—`| Verified |
| tests/mcp_servers/test_server_idempotency_boundary.py | Bootstrap-injection case | Exercises the idempotency boundary at server construction | REQ-001, REQ-009 | current test file |`—`| Verified |
| tests/mcp_servers/conftest.py | Fixture rewrite | Imports `DedupConfig` and clears the config cache (line 46) | REQ-003; AC-002 | line 46 |`—`| Verified |
| tests/mcp_servers/test_config_isolation_fail_closed.py | Fail-fast extension | Add missing/invalid `[dedup]`, boolean-as-integer, unsafe-path cases | REQ-006, REQ-009; AC-006 | current test file |`—`| Verified |
| tests/mcp_servers/test_config_isolation_import.py | Isolation extension | Assert servers no longer reach the removed loader paths | REQ-001, REQ-003, REQ-009; AC-002 | current test file |`—`| Verified |
| tests/agent/test_config_dataclasses.py | New field coverage | `approval_grant_ttl_seconds` field | REQ-002; AC-005 | current test file |`—`| Verified |
| tests/agent/test_config_builders.py | Builder coverage | Reads the new Agent-side key | REQ-002; AC-005 | current test file |`—`| Verified |
| tests/agent/test_production_config_validator.py | Validator coverage | Unknown-key rejection for the new Agent key and per-server `[dedup]` tables | REQ-006; AC-006 | current test file |`—`| Verified |
| tests/agent/test_tool_approval_paths.py | Grant-lifetime equality | Grant expiry sourced from `AgentConfig` with identical default lifetime | REQ-002; AC-005 | current test file |`—`| Verified |
| tests/agent/test_http_lifecycle_env_allowlist_integration.py | Allowlist update | Allowlist currently lists `mcp_dedup.toml` as read-by-agent | REQ-004; AC-003 | current test file (allowlist expectations) |`—`| Verified |
| tests/agent/workflow/test_stale_recovery_lease.py | Regression run/adjustment | Timeout wiring must stay Agent-side only | REQ-002; AC-005 | current test file |`—`| Verified |
| tests/agent/workflow/test_workflow_engine.py | Regression run/adjustment | Comment-driven expectations for the framing removal | REQ-002; AC-005 | current test file |`—`| Verified |
| tests/tools/test_check_db_separation.py | Separation-test fixture update | Exercises the removed file's registration | REQ-004; AC-003 | consumer scan (`direct:tests`) |`—`| Verified |
| tests/deploy/test_init_db_schema_gate.py | Deploy-gate update | init_db must no longer validate the removed file | REQ-004; AC-003 | current test file |`—`| Verified |
| tests/db/test_schema_validation_per_database.py | Regression run/adjustment | Imports `DedupStore`/`DedupStoreError` and canonical DDL (lines 42-43) | REQ-008 | scan `patch-or-import` candidates |`—`| Verified |
| docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md | Ownership map and refusal state | Documents the shared file and store degradation table | REQ-010; AC-007 | names `mcp_dedup.toml` (scan `direct:docs`) |`N/A: docs checker only`| Verified |
| docs/41_db/db_08_active_databases.md | Ownership row replacement | Active-database/config table carries the `mcp_dedup.toml` row | REQ-010; AC-007 | names `mcp_dedup.toml` (scan `direct:docs`) |`N/A: docs checker only`| Verified |
| docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md | Refusal-state enumeration | Enumerates the four start states that gain `identity_mismatch` | REQ-007, REQ-010; AC-004, AC-007 | line 68 state list in current source |`N/A: docs checker only`| Verified |
| docs/22_mcp/mcp_03_03_transport-and-health.md | Mention update | Names `config/mcp_dedup.toml` | REQ-010; AC-007 | scan `direct:docs` |`N/A: docs checker only`| Verified |
| docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md | Mention update | Names `config/mcp_dedup.toml` | REQ-010; AC-007 | scan `direct:docs` |`N/A: docs checker only`| Verified |
| docs/23_agent/agent_10_05_operations-and-observability-monitoring.md | Refusal-state enumeration | Degraded-dedup row lists the four start states (line 30) | REQ-007, REQ-010; AC-004, AC-007 | line 30 state list in current source |`N/A: docs checker only`| Verified |
| docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md | Path-mention update only | Names `mcp_dedup.toml`; no Status/approval change (issue Constraint) | REQ-010; AC-007 | scan `direct:docs` |`N/A: docs checker only`| Verified |
| docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md | Path-mention update only | Names `config/mcp_dedup.toml` `[retry_class]` mirror | REQ-005, REQ-010; AC-006, AC-007 | scan `direct:docs` |`N/A: docs checker only`| Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/shared/config_loader.py | `ConfigLoader.restrict_to()` own-file isolation used by the injection point; unknown-key and range validation of the `[dedup]` table comes from `load_dedup_section()` itself (porting `load_dedup_config`'s current checks at lines 174-183); `ConfigLoader` has no `reject_unknown_keys` member (corrected 2026-11-22) | scripts/mcp_servers/server.py; REQ-001, REQ-006 |
| scripts/shared/runtime_tool_registry.py | `get(tool_name)` metadata lookup for the retry-class switch | scripts/mcp_servers/dispatch.py; REQ-005 |
| scripts/shared/tool_metadata.py | `retry_policy_is_retryable()` helper contract | scripts/mcp_servers/dispatch.py; REQ-005 |
| scripts/shared/tool_constants.py | `RETRYABLE_TOOLS` reference data and the inline non-retryable default for unknown tools stay unchanged | REQ-005, REQ-008 |
| scripts/agent/shared/models.py | `ApprovalGrant` model (`issued_at`/`expires_at` contract) stays unchanged | scripts/agent/tool_approval.py; REQ-002 |
| scripts/shared/mcp_config.py | Issue target list; confirmed NOT a reader of `mcp_dedup.toml` (Agent transport config only) — not affected | REQ-001 (verification record) |
| scripts/agent/orchestrator.py | Consumer of `AgentConfig.pending_timeout_minutes` (line 143) — unchanged wiring must be verified | REQ-002 |
| rules/persisted-schema-change.md | Scratch-database recipe and checklist items recorded in Design | REQ-007, REQ-009 |
| docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md | Fail-open/fail-closed policy semantics that must not change; mentions `mcp_dedup.sqlite`, not the TOML — not affected | REQ-008 |
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | Records the observed degradation behavior (line 149); text stays accurate after this plan — not affected | REQ-008 |
| docs/41_db/db_01_architecture_and_schema-overview-and-config.md | Describes the disposable-store contract (line 36); no state enumeration, no TOML name — not affected | REQ-008 |
| docs/22_mcp/mcp_06_01_configuration-file-inventory.md | Config-file inventory that must be checked for the removed file; grep shows no `mcp_dedup` mention — not affected | REQ-004 |
| tools/_agentcfg003_content_shared.py | Contains agentcfg003-era verification claims about the `[retry_class]` mirror (lines 207-241); one-shot content embedded in already-generated procedures — not edited here | REQ-005 (verification record) |

## Acceptance Criteria
- [ ] AC-001 (REQ-002): The Agent reads call policy only from `config/agent.toml`; no Agent-side module reads any dedup TOML (grep gate).
- [ ] AC-002 (REQ-001, REQ-003): Each MCP process reads only its own TOML; `mcp_dedup.py`/`mcp_dedup_config.py` do no configuration discovery and keep no cache; the store opens only through an injected `DedupStoreConfig`.
- [ ] AC-003 (REQ-004): `mcp_dedup.toml` is neither read, copied by deploy, nor mounted: `rg -n "mcp_dedup\.toml|load_dedup_config|clear_dedup_config_cache|_DEDUP_CONFIG_CACHE|_validated_retry_class" scripts/ config/ deploy/ tools/` returns zero hits after Phase 4; no service units or volume mounts reference it (this repository ships none — Step 2 inspection finding).
- [ ] AC-004 (REQ-007): A shared-store semantic difference fails startup: reopen with a drifted validated set raises `DedupStoreError("identity_mismatch")` before any query, and the dispatcher degrades to overlay-only with the existing `error_type="dedup_store_error"` / `dedup_state="store_error"` payload (corrected 2026-11-22: no `store_refused` payload exists in current source).
- [ ] AC-005 (REQ-002): `pending_timeout_minutes` remains top-level in `agent.toml` and the only stale-pending timeout read by the workflow modules; every approval grant's lifetime equals today's `_GRANT_TTL_SECONDS` default.
- [ ] AC-006 (REQ-005, REQ-006): `[retry_class]` is gone from config files, loader validation, and the store config type; unknown keys, booleans-as-integers, unsafe `db_path` values, and a missing `[dedup]` section each fail startup with a file-and-key-specific error before any store opens.
- [ ] AC-007 (REQ-010): The documentation rows listed in Implementation Target Files are updated; no ADR Status change or approval statement is written (issue Constraint).

## Tests
- REQ-001/REQ-003: injected-config fixtures replace discovery/cache fixtures in `tests/mcp_servers/conftest.py`, `tests/mcp_servers/test_mcp_dispatch.py`, `tests/shared/test_mcp_dedup_concurrency.py`; `tests/mcp_servers/test_config_isolation_import.py` asserts servers no longer import the removed loader paths.
- REQ-006: new strict-parser cases in `tests/mcp_servers/test_config_isolation_fail_closed.py` and `tests/shared/test_mcp_dedup.py`: unknown key inside `[dedup]`, `lease_seconds = 0/7200`, `retention_days = 0/366`, `max_attempts = 0/11`, boolean literal where an integer is expected, `db_path` outside the dedup database directory, and a missing `[dedup]` table for a dispatching server.
- REQ-007: cross-process fingerprint mismatch regression in `tests/shared/test_mcp_dedup_identity.py` (init under config A, reopen under drifted config B → `identity_mismatch`, no rows written; reopen under A again → continuity success), plus the scratch-database check in Validation plan.
- REQ-008: unchanged behavior-lock run of the Regression baseline (see Validation plan) covering in-progress suppression, replay, lease reconciliation, and the existing degradation-path assertions (measured 2026-11-22: 33 `store_error` occurrences across 3 test files, 11 `dedup_store_error`/`dedup_unreplayable` occurrences in 1 file, 24 refused-at-open/start-state occurrences across 5 files — corrected from the earlier unverified "160 `store_refused`" count, which does not exist in current source).
- REQ-002/REQ-004: `tests/agent/test_http_lifecycle_env_allowlist_integration.py` allowlist drops `mcp_dedup.toml`; `tests/agent/test_tool_approval_paths.py` asserts grant-lifetime equality with the old constant.
- REQ-009: ruff, mypy, `lint-imports`, and the full test suite per `rules/toolchain.md` (`tools/run_validation_gates.py --full`).

## Documentation Impact
Yes (`REQ-007`, `REQ-010`): configuration ownership of the dedup settings, the removed file, and the new refusal state. Target docs identified via `docs/00_index.md` "Document References by Task" (rows "DB layer spec", "TransportType / StartupMode enums (mcp_config.py)" area, "Agent REPL flow / tool execution", "Agent startup / verification / troubleshooting") and the Step 3 consumer scan: the MCP dedup/executionsnapshot DB spec page, the active-databases page, the DB migration-and-scaling page, the MCP transport-and-health page, the Agent tool-execution page, the Agent observability page, and the two ADR pages named as rows in Implementation Target Files (path-mention only there). English only (`skills/DESIGN.md` Output language).

## Assumptions
- All ten dispatching MCP servers get a `[dedup]` section (including `file_read`): the shared `server.py` middleware and `dispatch_tool()` path can reach the store from any server, so a uniform contract avoids a write-capable exemption branch; the issue's "missing section for a write-capable server" gate is satisfied for all servers (`Confirmed by repository evidence`).
- The `[mcp_call]` key list in the issue (logical-id format, write-idempotency requirement, reconciliation enablement, mandatory state recording) is already implemented as Agent-side code behavior or `agent.toml` keys, so this plan adds only the approval-grant horizon key and records the rest as UNK-01 (`Needs confirmation` at procedure time).
- The current production deploy ships no systemd units, containers, or mounts for the dedup file (Step 2 inspection: `deploy/` has no unit files; servers launch via `agent.toml` `[mcp_servers.*]` commands) — AC-003's mount clause is satisfied by absence (`Confirmed by repository evidence`).
- mcpdd001 and mcpai006 settings will go into the typed `DedupStoreConfig` and classification constants, per their own issue texts (`Explicit in issue`, Dependencies section).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether any of the issue's `[mcp_call]` items needs a new `agent.toml` key beyond the grant horizon | No `approval_grant`-style or logical-id-format config exists in current Agent code; mapping is inferred | Decide at Phase 2 procedure time against the applied agentcfg004 ownership map; if a key is required it is added to the `AgentConfig` rows already listed, not a new file | False |
| UNK-02 | Name and accepted range of the approval-grant horizon key | No existing key to mirror | Proposed `approval_grant_ttl_seconds`, float range `60..3600`, default `300.0`; confirm in the Phase 2 procedure | False |
| UNK-03 | Whether every deployed production store's stored fingerprint matches the to-be-injected `[dedup]` values | No production store on this host (`/opt/llm/db/mcp_dedup.sqlite` absent; no services running) | Mandatory scratch-copy fingerprint check per host before Phase 4 (rules/persisted-schema-change.md recipe); on mismatch adjust `[dedup]` sections, never the store | False |
| UNK-04 | Whether per-server value divergence (e.g. `lease_seconds`) is ever intended once each server owns its section | No product decision recorded | Phase 2 copies identical values; the fingerprint gate fails closed on accidental divergence; intentional divergence requires a future store-split decision outside this plan | False |

Verification results (2026-11-22, adversarial verification): the earlier init_db.sh unknown is resolved — `deploy/init_db.sh` lines 108-175 drive dedup init through a python heredoc calling `load_dedup_config()` with no arguments (line 128, `LLMAGENT_CONFIG_DIR` honored) then `open_dedup_store(config)` and a verification gate (identity row, `PRAGMA user_version=1`, `.mcp_dedup_installed` marker), so Phase 4 must make that step resolve a designated per-server `[dedup]` section (or keep a dedicated owner file); which section owns the init remains an implementation decision. The earlier env-allowlist unknown is resolved — `tests/agent/test_http_lifecycle_env_allowlist_integration.py` references `mcp_dedup.toml` in the `_SUBPROCESS_REACHABLE_CONFIGS` frozenset (line 56) with a comment (lines 46-47) stating it is read by every subprocess server through the dispatch dedup-store loader, not in an env-var pattern list; after Phase 4 removes the shared file, the entry must be replaced by the per-server `*_mcp_server.toml` coverage (already implied by `_SUBPROCESS_REACHABLE_PATTERNS`).

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/mcp_servers/dispatch.py | inject-only context, metadata-first retry | all ten MCP servers' call path | 7 | 3 | Indirect: deploy copies configs the dispatcher consumes |
| scripts/shared/mcp_dedup.py | injected store, fingerprint reopen gate | every dedup store open | 9 | 2 | Indirect (store open happens via init_db.sh today) |
| scripts/shared/mcp_dedup_config.py | loader/validation split | all dedup config reads | 2 | 1 | Direct: init_db.sh calls this loader today |
| scripts/mcp_servers/server.py | bootstrap injection | all ten server processes' startup | 11 | 3 | None |
| scripts/agent/production_config_validator.py | key-table extension | production config gate | 13 | 2 | Direct: deploy invokes the validator |
| scripts/agent/config_dataclasses.py | new Agent field | Agent config surface shared with agentcfg004 | 11 | 4 | None |
| config/agent.toml | new Agent key | Agent startup config; agentcfg004 overlap | 17 | 3 | Direct: copied by deploy.sh step 2 |
| config/mcp_dedup.toml | removal | deploy copy list, init_db.sh, tools/check_db_separation.py | 5 | 2 | Direct: copied by deploy.sh (line 154) today |
| deploy/deploy.sh | copy-list edit | production config deploy | 2 | 2 | Direct |
| deploy/init_db.sh | validation-call removal | database init gate | 8 | 2 | Direct |
| tests/mcp_servers/conftest.py | fixture rewrite | all MCP server tests | 3 | 2 | None |
| tools/check_db_separation.py | path-registration edit | CI separation check | 1 | 2 | None |

## Design
- Config ownership map after the change: each server's `[dedup]` table owns store parameters (`db_path`, `retention_days`, `pending_timeout_minutes`, `lease_seconds`, `max_attempts` — the current five, no new semantics keys); `config/agent.toml` owns Agent call policy (top-level `pending_timeout_minutes`, new grant-horizon key); `retry_policy` tool metadata owns retry classification. Explicit deployment contract: every `[dedup]` value is written out even when equal to the code default (issue Constraint).
- Injection flow: `scripts/mcp_servers/server.py` bootstrap (after `ConfigLoader.restrict_to(self.own_config_file)`, lines 340-348) → `load_dedup_section(loaded mapping)` → `dispatch.configure_dedup(store_config)` (new eager setter reusing the existing replaceable module globals `_dedup_store`/`_dedup_config`, preserving the test pattern at `scripts/mcp_servers/dispatch.py` lines 160-200) → `open_dedup_store(config)`. `_dedup_context()` keeps its overlay-only degradation contract: an unconfigured process sets `_dedup_disabled` with a `not_configured` start state in the audit log, reusing the existing degradation payload path (`error_type="dedup_store_error"`, `dedup_state="store_error"` — corrected 2026-11-22: no `store_refused` payload exists in current source).
- Shared-store fingerprint gate: `_classify_existing` compares stored `store_meta.config_fingerprint` with `config_fingerprint(injected)` and raises `DedupStoreError("identity_mismatch")`; the four existing states and their operator runbook (archive + `resolve_store` new generation, db_08) are unchanged; recovery for `identity_mismatch` is config correction, never store mutation. Fingerprint inputs stay exactly the current validated-parameter set (issue: "fingerprint only shared-store behavior").
- Retry-class switch: `dispatch.py` `retry_class(name, config)` call sites (lines 327, 525, 544) become a `RuntimeToolRegistry.get(name).retry_policy` lookup through `retry_policy_is_retryable()`; unknown/unregistered tools keep the non-retryable default because `get()` raises `KeyError` (caught at the call site, as today at lines 545-546) and `retry_policy_is_retryable(None)` is False — identical semantics to the mirror's "unknown tools default to non_retryable" rule; no new named fallback constant is introduced (`DEFAULT_RETRY_CLASS` does not exist in current source — corrected 2026-11-22). `RETRYABLE_TOOLS` stays reference data with its drift test retargeted from the TOML mirror to the declarations only (REQ-005).
- Persisted-schema-change checklist outcome: no DDL, no schema version, no migration registry change (items 1-5, 7-9 do not apply; the agentcfg004-owned `mcp_dedup` migration registry slots v21..v24 are untouched). Item 6 (fingerprint) applies: the reopen check compares the stored content fingerprint directly; verification uses the scratch-database recipe, never databases under `/opt/llm/`.
- Consumer-scan candidate disposition (`tools/scan_change_consumers.py --seed load_dedup_config --seed clear_dedup_config_cache --seed DedupConfig --seed retry_class --seed _DEDUP_CONFIG_CACHE --seed _config_fingerprint --seed _validated_retry_class --seed mcp_dedup.toml`, 2026-11-21):
  - `direct:scripts` (82): target rows (mcp_dedup_config, mcp_dedup, dispatch, server, execution_snapshot, config_dataclasses, config_builders, production_config_validator, tool_approval, workflow_engine, tool_call_state_ops); remaining candidates `not affected: scripts/shared/mcp_config.py`, `scripts/agent/orchestrator.py`, `scripts/agent/context.py` — verified non-readers of the dedup TOML (Reference Files).
  - `direct:tests` (130) + `patch-or-import` (23): the 16 test rows above; remaining candidates `not affected: references to the tool-metadata `retry_policy` symbol or refusal-state strings, not dedup config`.
  - `direct:tools` (10) + `inventory` (4): `tools/check_db_separation.py` target row (registration tuple line 127, direct read lines 226-227); `tools/_agentcfg003_content_shared.py` `not affected: one-shot content module of already-generated agentcfg003 procedures` (Reference Files).
  - `adr-test-citation` (11): `not affected: ADR citation of workflow retry tests (tests/agent/test_repl_health.py, tests/agent/workflow/test_workflow_engine.py); no dedup-config reads` — test_workflow_engine stays a row only for its comment expectations.
  - `direct:docs` (14): the 8 doc rows above; `docs/00_governance/governance_03...`, `docs/10_adr/adr_02_01_004...`, `docs/41_db/db_01...` `not affected` (Reference Files).
  - `testmon` (8): already listed target test files.
- Predictable-fallout check: module size gate — measured 2026-11-22: `scripts/mcp_servers/dispatch.py` is 24,185 B against the 24,576 B gate (391 B headroom; corrected 2026-11-22, the earlier "insertions only in config/test files" reasoning was wrong because Phases 2-3 insert into `dispatch.py` and `server.py`), so its retry-plumbing removal (Phase 2) and `configure_dedup()` setter (Phase 3) must keep it under the gate or a baseline/split decision is needed at implementation time; all other code targets have ample headroom (`server.py` 17,612 B, `mcp_dedup.py` 20,074 B, `mcp_dedup_config.py` 7,589 B); pinned counts — the degradation-path test occurrences (33 `store_error` across 3 files, 11 `dedup_store_error`/`dedup_unreplayable` in 1 file, 24 start-state/refused-at-open across 5 files, measured 2026-11-22) and refusal-state enumerations are kept valid by preserving the four legacy states; tool inventory — `tools/check_db_separation.py` DB_PATH_REGISTRATIONS row added; generated docs blocks — measured 2026-11-22: zero generated reference docs mention `mcp_dedup.toml` (the only doc mentions are the operational `rules/env.md` config reference and `rules/tool-gates.md`, corrected from the earlier "3 generated reference docs" claim); `tools/TOOL_DESCRIPTIONS.md` has no `mcp_dedup` entry (grep evidence: zero hits) so the tool-behavior edit needs no description change beyond the checker runs.

## Implementation steps
1. **Phase 1: Config-module separation and store-config contract**
   - [ ] Remove discovery (`_default_config_path`), the cache (`_DEDUP_CONFIG_CACHE`, `clear_dedup_config_cache`), and `_validated_retry_class` from `scripts/shared/mcp_dedup_config.py`; add `DedupStoreConfig` (no `retry_class` field) and pure `load_dedup_section(mapping)` (REQ-003, REQ-005, REQ-006).
   - [ ] `scripts/shared/mcp_dedup.py`: `open_dedup_store()` requires an injected `DedupStoreConfig`; `retry_class()` facade becomes a deprecated `RETRYABLE_TOOLS` reference lookup (REQ-001, REQ-005).
   - [ ] `scripts/mcp_servers/dispatch.py`: add eager `configure_dedup(store_config)`; keep a transitional `mcp_dedup.toml`-based bootstrap call so the suite stays green until Phase 2 replaces it (REQ-003).
   - [ ] Retarget `tests/shared/test_mcp_dedup.py`, `tests/shared/test_mcp_dedup_concurrency.py`, `tests/mcp_servers/conftest.py`, `tests/mcp_servers/test_mcp_dispatch.py` fixtures to injected configs (REQ-009).
2. **Phase 2: Bootstrap injection and ownership**
   - [ ] `scripts/mcp_servers/server.py`: after the `restrict_to()` bootstrap, load the own config file, run `load_dedup_section()`, and call `dispatch.configure_dedup()` before serving; fail fast on invalid/missing `[dedup]` (REQ-001, REQ-006).
   - [ ] Add identical `[dedup]` tables (explicit values, `db_path = "/opt/llm/db/mcp_dedup.sqlite"`) to the ten `config/*_mcp_server.toml` rows; drop the transitional call from `scripts/mcp_servers/dispatch.py` (REQ-001, REQ-003).
   - [ ] Agent-side: `scripts/agent/config_dataclasses.py`, `scripts/agent/config_builders.py`, `scripts/agent/production_config_validator.py`, `scripts/agent/tool_approval.py`, `config/agent.toml` — grant-horizon key with validator range; `_issue_grant` reads it (REQ-002).
   - [ ] `scripts/shared/execution_snapshot.py`: `_dedup_component` reads only `agent.toml` (REQ-003).
   - [ ] Update `tests/mcp_servers/test_config_isolation_fail_closed.py`, `tests/mcp_servers/test_config_isolation_import.py`, `tests/agent/test_config_dataclasses.py`, `tests/agent/test_config_builders.py`, `tests/agent/test_production_config_validator.py`, `tests/agent/test_tool_approval_paths.py`, `tests/shared/test_execution_snapshot.py`, `tests/agent/test_http_lifecycle_env_allowlist_integration.py` (REQ-009); re-verify against the applied agentcfg004 ownership map before proceeding.
3. **Phase 3: Store-identity enforcement and retry-class removal**
   - [ ] `scripts/shared/mcp_dedup.py`: `_classify_existing` raises `DedupStoreError("identity_mismatch")` on stored-vs-injected fingerprint mismatch before any query (REQ-007).
   - [ ] `scripts/mcp_servers/dispatch.py`: switch retry decisions to registry `retry_policy` metadata (unknown/unregistered tools default to non-retryable via `retry_policy_is_retryable(None)` == False and the `KeyError` catch at the call site); delete the `retry_class()` facade and all `DedupConfig` retry plumbing (REQ-005, REQ-008).
   - [ ] Update `scripts/agent/workflow/workflow_engine.py` and `scripts/agent/workflow/tool_call_state_ops.py` framing comments (REQ-002).
   - [ ] Extend `tests/shared/test_mcp_dedup_identity.py` (drift → refusal, identical → continuity), retarget `tests/shared/test_tool_constants.py` drift check, run `tests/db/test_schema_validation_per_database.py`, `tests/agent/workflow/test_stale_recovery_lease.py`, `tests/agent/workflow/test_workflow_engine.py` (REQ-009).
4. **Phase 4: Removal of the shared file and operational references**
   - [ ] Confirm the Phase-2 production checklist for `[dedup]` coverage (UNK-03 scratch-copy fingerprint check) is signed off for the deployment hosts.
   - [ ] Delete `config/mcp_dedup.toml`; drop the copy entry from `deploy/deploy.sh` (line 154) and the validation call from `deploy/init_db.sh` (line 128) (REQ-004).
   - [ ] Update `tools/check_db_separation.py` registrations to the per-server `[dedup]` `db_path` entries (REQ-004, REQ-010 see Documentation Impact checker note); update `tests/tools/test_check_db_separation.py`, `tests/deploy/test_init_db_schema_gate.py`, `tests/agent/test_http_lifecycle_env_allowlist_integration.py` fixtures (REQ-009).
   - [ ] Run the deployment validation/scripts check: `rg` grep gate (AC-003), `tools/check_db_separation.py`, `uv run pytest tests/tools/test_check_db_separation.py tests/deploy/ -q`, full `uv run pytest -q` (REQ-009).
5. **Phase 5: Documentation**
   - [ ] Update the eight doc rows (ownership map, `[dedup]` contract, `identity_mismatch` state and its config-correction recovery note, `[retry_class]` removal note; path-mention only in the two ADR rows — no Status change, no approval statements) (REQ-007, REQ-010).
   - [ ] Run `uv run python tools/check_docs_links.py` and `uv run python tools/check_docs_consumption.py`, plus the `tools/` checker for the `tools/check_db_separation.py` edit per `routing.md` Tools mapping (REQ-009, REQ-010).

### Release units
**Unit**: dedup-config-isolation-core | **Phases**: 1, 2, 4 | **Reason**: Phase 1 removes the discovery loader that `deploy/init_db.sh`, `scripts/shared/execution_snapshot.py`, and test fixtures still call, so no member phase passes the full gate alone until Phase 2's injection and Phase 4's reference removal land in the same delivery. Phase 3 and Phase 5 validate alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/shared/mcp_dedup_config.py | Unit: strict parser bounds, booleans-as-integers, unknown keys, unsafe paths, missing table | `uv run pytest tests/shared/test_mcp_dedup.py -q` | Every listed invalid input raises `ConfigParseError`/`ConfigMissingError` naming file and key |
| scripts/shared/mcp_dedup.py + store | Integration on scratch database | scratch-database recipe in `rules/persisted-schema-change.md` | drifted reopen → `identity_mismatch`; identical reopen → continuity; four legacy states unchanged |
| scripts/mcp_servers/server.py + dispatch | Integration: server bootstrap injection, unconfigured degradation | `uv run pytest tests/mcp_servers/ -q` | Store opens only via injected config; unconfigured dispatcher → overlay-only with the `dedup_state="store_error"` payload and null `call_id` |
| scripts/agent/* (config_dataclasses, config_builders, production_config_validator, tool_approval) | Unit | `uv run pytest tests/agent/test_config_dataclasses.py tests/agent/test_config_builders.py tests/agent/test_production_config_validator.py tests/agent/test_tool_approval_paths.py -q` | New key parsed/validated; grant lifetime equals 300.0 default; unknown keys rejected with file and key |
| deploy/deploy.sh, deploy/init_db.sh | Deploy-script check | `uv run pytest tests/deploy/test_init_db_schema_gate.py -q` + manual `bash -n` | No reference to the removed file; init gate green |
| tools/check_db_separation.py | Tool unit | `uv run pytest tests/tools/test_check_db_separation.py -q` and `uv run python tools/check_db_separation.py` | Per-server registrations resolve; zero violations on the live repository |
| whole diff | Full gate | `uv run python tools/run_validation_gates.py --full` (ruff, mypy, import-linter, full pytest with coverage, diff-cover) | All gates green; import contracts unchanged |
| docs rows | Docs checkers | `uv run python tools/check_docs_links.py`, `uv run python tools/check_docs_consumption.py` | No broken links or stale claims |

## Risks
- **Risk**: Phase 4 deploys before every production `*_mcp_server.toml` has a fingerprint-matching `[dedup]` section, so servers refuse the store and run overlay-only (dedup lost, call safety intact) → **Mitigation**: Phase 4 checklist gate (UNK-03 scratch-copy fingerprint check per host) and `ConfigParseError` messages naming the server file.
- **Risk**: The unapplied agentcfg004 procedures conflict with this plan on `config/agent.toml` and `scripts/agent/production_config_validator.py` → **Mitigation**: declared `Depends on` ordering; re-verify the allowlist test and validator key tables against the applied ownership map at Phase 2 (Phase 2 step 5 explicitly re-checks).
- **Risk**: The new fingerprint gate turns previously-tolerated config drift into startup refusals → **Mitigation**: intentional (frozen-store continuity); recovery note (adjust `[dedup]`, never the store) documented in the db_03_07 row; four legacy states and their runbook unchanged.
- **Risk**: Eager `configure_dedup()` changes dispatcher startup and breaks fixtures that replace the module globals (the 44 `store_error`/`dedup_store_error` degradation assertions measured 2026-11-22) → **Mitigation**: keep the replaceable-globals pattern (Design); Phase 1 updates `tests/mcp_servers/conftest.py` and `tests/mcp_servers/test_mcp_dispatch.py` in the same unit.
- **Risk**: Broad test surface references removed names (scan: 39 `load_dedup_config`, 25 `retry_class` candidates) → **Mitigation**: per-phase `tools/scan_change_consumers.py` run as the edit checklist; `not affected` dispositions recorded in Design.
- **Risk**: Uniform `[dedup]` on all ten servers masks a future need for per-server store semantics → **Mitigation**: UNK-04 recorded; divergence requires a store-split decision outside this plan; today divergence fails closed as `identity_mismatch`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Config-module separation and store-config contract | Pending | — | — | |
| 2 | Phase 2: Bootstrap injection and ownership | Pending | — | — | Requires agentcfg004 applied first |
| 3 | Phase 3: Store-identity enforcement and retry-class removal | Pending | — | — | |
| 4 | Phase 4: Removal of the shared file and operational references | Pending | — | — | Gated by the production `[dedup]` checklist |
| 5 | Phase 5: Documentation | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2 | Implementation cannot start until the agentcfg004 procedures are applied (shared `config/agent.toml` / validator surface) | No | — |
| 4 | Production hosts' `[dedup]` fingerprint verification (UNK-03) must be signed off before removal | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261122-192909_* (44 procedure documents) | 1 | Implementation procedure document | Created | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261120-115842_mcpdl003_dedup-config-isolation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261121-172154
- **Related target files**: scripts/shared/mcp_dedup_config.py, scripts/shared/mcp_dedup.py, scripts/mcp_servers/dispatch.py, scripts/mcp_servers/server.py, scripts/agent/config_dataclasses.py, scripts/agent/config_builders.py, scripts/agent/production_config_validator.py, scripts/agent/tool_approval.py, scripts/agent/workflow/workflow_engine.py, scripts/agent/workflow/tool_call_state_ops.py, scripts/shared/execution_snapshot.py, config/agent.toml, config/cicd_mcp_server.toml, config/file_delete_mcp_server.toml, config/file_read_mcp_server.toml, config/file_write_mcp_server.toml, config/git_mcp_server.toml, config/github_mcp_server.toml, config/mdq_mcp_server.toml, config/rag_pipeline_mcp_server.toml, config/shell_mcp_server.toml, config/web_search_mcp_server.toml, config/mcp_dedup.toml, deploy/deploy.sh, deploy/init_db.sh, tools/check_db_separation.py, tests/shared/test_mcp_dedup.py, tests/shared/test_mcp_dedup_identity.py, tests/shared/test_mcp_dedup_concurrency.py, tests/shared/test_execution_snapshot.py, tests/shared/test_tool_constants.py, tests/mcp_servers/test_mcp_dispatch.py, tests/mcp_servers/test_server_idempotency_boundary.py, tests/mcp_servers/conftest.py, tests/mcp_servers/test_config_isolation_fail_closed.py, tests/mcp_servers/test_config_isolation_import.py, tests/agent/test_config_dataclasses.py, tests/agent/test_config_builders.py, tests/agent/test_production_config_validator.py, tests/agent/test_tool_approval_paths.py, tests/agent/test_http_lifecycle_env_allowlist_integration.py, tests/agent/workflow/test_stale_recovery_lease.py, tests/agent/workflow/test_workflow_engine.py, tests/tools/test_check_db_separation.py, tests/deploy/test_init_db_schema_gate.py, tests/db/test_schema_validation_per_database.py, docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md, docs/41_db/db_08_active_databases.md, docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md, docs/22_mcp/mcp_03_03_transport-and-health.md, docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md, docs/23_agent/agent_10_05_operations-and-observability-monitoring.md, docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md, docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes bullet 2; Acceptance Criteria | scripts/mcp_servers/server.py | Phase 2 | AC-002 | tests/mcp_servers/test_server_idempotency_boundary.py | Explicit in issue |
| REQ-001 | Required Changes bullet 2 ("inject it at bootstrap") | scripts/shared/mcp_dedup.py | Phase 1 | AC-002 | tests/shared/test_mcp_dedup_identity.py | Explicit in issue |
| REQ-001 | Resolved Open Question: all ten servers dispatch through the store | scripts/mcp_servers/dispatch.py | Phase 1-2 | AC-002 | tests/mcp_servers/test_mcp_dispatch.py | Confirmed by repository evidence |
| REQ-001 | Target Files "every `config/mcp_*.toml`" | config/cicd_mcp_server.toml | Phase 2 | AC-002 | tests/mcp_servers/cicd/test_cicd_server_endpoints.py | Explicit in issue |
| REQ-001 | Same | config/file_delete_mcp_server.toml | Phase 2 | AC-002 | tests/mcp_servers/file/ | Explicit in issue |
| REQ-001 | Design: uniform contract incl. read server | config/file_read_mcp_server.toml | Phase 2 | AC-002 | tests/mcp_servers/file/ | Derived from confirmed evidence |
| REQ-001 | Target Files "every `config/mcp_*.toml`" | config/file_write_mcp_server.toml | Phase 2 | AC-002 | tests/mcp_servers/file/ | Explicit in issue |
| REQ-001 | Same | config/git_mcp_server.toml | Phase 2 | AC-002 | tests/mcp_servers/git/ | Explicit in issue |
| REQ-001 | Same | config/github_mcp_server.toml | Phase 2 | AC-002 | tests/mcp_servers/github/test_github_server_endpoints.py | Explicit in issue |
| REQ-001 | Same | config/mdq_mcp_server.toml | Phase 2 | AC-002 | tests/mcp_servers/mdq/ | Explicit in issue |
| REQ-001 | Same | config/rag_pipeline_mcp_server.toml | Phase 2 | AC-002 | tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py | Explicit in issue |
| REQ-001 | Same | config/shell_mcp_server.toml | Phase 2 | AC-002 | tests/mcp_servers/shell/test_shell_server_endpoints.py | Explicit in issue |
| REQ-001 | Same | config/web_search_mcp_server.toml | Phase 2 | AC-002 | tests/mcp_servers/web_search/ | Explicit in issue |
| REQ-002 | Required Changes bullet 1; Acceptance Criteria | scripts/agent/config_dataclasses.py | Phase 2 | AC-005 | tests/agent/test_config_dataclasses.py | Explicit in issue |
| REQ-002 | Same | scripts/agent/config_builders.py | Phase 2 | AC-005 | tests/agent/test_config_builders.py | Explicit in issue |
| REQ-002 | Same | scripts/agent/tool_approval.py | Phase 2 | AC-005 | tests/agent/test_tool_approval_paths.py | Explicit in issue |
| REQ-002 | Same | config/agent.toml | Phase 2 | AC-005 | tests/agent/test_config_builders.py | Explicit in issue |
| REQ-002 | Current framing references the dispatcher TOML | scripts/agent/workflow/workflow_engine.py | Phase 3 | AC-005 | tests/agent/workflow/test_workflow_engine.py | Confirmed by repository evidence |
| REQ-002 | Same | scripts/agent/workflow/tool_call_state_ops.py | Phase 3 | AC-005 | tests/agent/workflow/test_stale_recovery_lease.py | Confirmed by repository evidence |
| REQ-002 | UNK-01/UNK-02 mapping decision | scripts/agent/production_config_validator.py | Phase 2 | AC-006 | tests/agent/test_production_config_validator.py | Needs confirmation |
| REQ-003 | Required Changes bullet 4; Issue Evidence (`_DEDUP_CONFIG_CACHE`) | scripts/shared/mcp_dedup_config.py | Phase 1 | AC-002 | tests/shared/test_mcp_dedup.py | Explicit in issue |
| REQ-003 | Issue Evidence ("loads it lazily on first use") | scripts/mcp_servers/dispatch.py | Phase 1-2 | AC-002 | tests/mcp_servers/test_mcp_dispatch.py | Explicit in issue |
| REQ-003 | Reader found in Step 2 inspection (resolved Open Question) | scripts/shared/execution_snapshot.py | Phase 2 | AC-003 | tests/shared/test_execution_snapshot.py | Confirmed by repository evidence |
| REQ-003 | Fixture consumers of the cache-clear API | tests/mcp_servers/conftest.py | Phase 1 | AC-002 | — | Confirmed by repository evidence |
| REQ-004 | Required Changes bullet 4; Acceptance Criteria | config/mcp_dedup.toml | Phase 4 | AC-003 | tests/tools/test_check_db_separation.py | Explicit in issue |
| REQ-004 | Issue Evidence (deploy.sh line 154) | deploy/deploy.sh | Phase 4 | AC-003 | tests/deploy/test_init_db_schema_gate.py | Explicit in issue |
| REQ-004 | Reader found in Step 2 inspection | deploy/init_db.sh | Phase 4 | AC-003 | tests/deploy/test_init_db_schema_gate.py | Confirmed by repository evidence |
| REQ-004 | Consumer scan `inventory` candidates | tools/check_db_separation.py | Phase 4 | AC-003 | tests/tools/test_check_db_separation.py | Confirmed by repository evidence |
| REQ-004 | Allowlist currently lists the file | tests/agent/test_http_lifecycle_env_allowlist_integration.py | Phase 2, 4 | AC-003 | same file | Confirmed by repository evidence |
| REQ-005 | Required Changes bullet 5 | scripts/shared/mcp_dedup_config.py | Phase 1 | AC-006 | tests/shared/test_mcp_dedup.py | Explicit in issue |
| REQ-005 | Same | scripts/mcp_servers/dispatch.py | Phase 3 | AC-006 | tests/mcp_servers/test_mcp_dispatch.py | Explicit in issue |
| REQ-005 | Drift test currently compares against the mirror | tests/shared/test_tool_constants.py | Phase 3 | AC-006 | same file | Confirmed by repository evidence |
| REQ-005 | ADR mention of the mirror | docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md | Phase 5 | AC-007 | docs checkers | Confirmed by repository evidence |
| REQ-006 | Required Changes bullet 3 | scripts/shared/mcp_dedup_config.py | Phase 1 | AC-006 | tests/shared/test_mcp_dedup.py | Explicit in issue |
| REQ-006 | `ConfigLoader.restrict_to()` enforcement (bullet 4) | scripts/mcp_servers/server.py | Phase 2 | AC-006 | tests/mcp_servers/test_config_isolation_fail_closed.py | Explicit in issue |
| REQ-006 | Production validator key tables (Target Files list) | scripts/agent/production_config_validator.py | Phase 2 | AC-006 | tests/agent/test_production_config_validator.py | Explicit in issue |
| REQ-007 | Required Changes bullet 6; mcpdl002 fingerprint inputs | scripts/shared/mcp_dedup.py | Phase 3 | AC-004 | tests/shared/test_mcp_dedup_identity.py; Validation plan scratch-database row | Explicit in issue |
| REQ-007 | State enumeration in docs | docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md | Phase 5 | AC-004, AC-007 | docs checkers | Confirmed by repository evidence |
| REQ-007 | Same | docs/23_agent/agent_10_05_operations-and-observability-monitoring.md | Phase 5 | AC-004, AC-007 | docs checkers | Confirmed by repository evidence |
| REQ-008 | AI Implementation Instruction ("Keep store behavior unchanged") | scripts/shared/mcp_dedup.py | Phase 1-3 | AC-004 | tests/shared/test_mcp_dedup_concurrency.py | Explicit in issue |
| REQ-008 | Same | scripts/mcp_servers/dispatch.py | Phase 1-3 | AC-004 | tests/mcp_servers/test_mcp_dispatch.py | Explicit in issue |
| REQ-008 | Store-schema regression | tests/db/test_schema_validation_per_database.py | Phase 3 | AC-004 | same file | Derived from confirmed evidence |
| REQ-009 | Testing Expectations | tests/mcp_servers/test_config_isolation_import.py | Phase 2 | AC-002, AC-006 | same file | Explicit in issue |
| REQ-009 | Same | tests/mcp_servers/test_config_isolation_fail_closed.py | Phase 2 | AC-006 | same file | Explicit in issue |
| REQ-009 | Same | tests/shared/test_execution_snapshot.py | Phase 2 | AC-003 | same file | Explicit in issue |
| REQ-009 | Same | tests/agent/test_config_dataclasses.py | Phase 2 | AC-005 | same file | Explicit in issue |
| REQ-009 | Same | tests/agent/test_config_builders.py | Phase 2 | AC-005 | same file | Explicit in issue |
| REQ-009 | Same | tests/agent/test_production_config_validator.py | Phase 2 | AC-006 | same file | Explicit in issue |
| REQ-009 | Same | tests/agent/test_tool_approval_paths.py | Phase 2 | AC-005 | same file | Explicit in issue |
| REQ-009 | Same | tests/agent/workflow/test_stale_recovery_lease.py | Phase 3 | AC-005 | same file | Explicit in issue |
| REQ-009 | Same | tests/agent/workflow/test_workflow_engine.py | Phase 3 | AC-005 | same file | Explicit in issue |
| REQ-009 | Same | tests/tools/test_check_db_separation.py | Phase 4 | AC-003 | same file | Explicit in issue |
| REQ-009 | Same | tests/deploy/test_init_db_schema_gate.py | Phase 4 | AC-003 | same file | Explicit in issue |
| REQ-009 | Same | tests/shared/test_mcp_dedup.py | Phase 1 | AC-006 | same file | Explicit in issue |
| REQ-009 | Same | tests/shared/test_mcp_dedup_identity.py | Phase 1, 3 | AC-004 | same file | Explicit in issue |
| REQ-009 | Same | tests/shared/test_mcp_dedup_concurrency.py | Phase 1 | AC-002 | same file | Explicit in issue |
| REQ-009 | Same | tests/mcp_servers/test_mcp_dispatch.py | Phase 1-3 | AC-002, AC-004 | same file | Explicit in issue |
| REQ-009 | Same | tests/mcp_servers/test_server_idempotency_boundary.py | Phase 2 | AC-002 | same file | Explicit in issue |
| REQ-009 | Same | tests/mcp_servers/conftest.py | Phase 1 | AC-002 | — | Explicit in issue |
| REQ-010 | Documentation Impact | docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md | Phase 5 | AC-007 | docs checkers | Explicit in issue |
| REQ-010 | Same | docs/41_db/db_08_active_databases.md | Phase 5 | AC-007 | docs checkers | Explicit in issue |
| REQ-010 | Same | docs/22_mcp/mcp_03_03_transport-and-health.md | Phase 5 | AC-007 | docs checkers | Explicit in issue |
| REQ-010 | Same | docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md | Phase 5 | AC-007 | docs checkers | Explicit in issue |
| REQ-010 | Same | docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md | Phase 5 | AC-007 | docs checkers | Explicit in issue |
