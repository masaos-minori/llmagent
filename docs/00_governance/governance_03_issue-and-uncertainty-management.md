---
title: "Issue and Uncertainty Management"
area: governance
tags:
  - governance
related:
  - 00_index.md
  - overview_00_document-guide.md
  - governance_01_documentation-policy.md
  - rag_05_01-configuration-reference.md
  - adr_02_010_rag-fallback.md
  - adr_02_005_rag-source-derived-index-relationships.md
  - adr_02_004_environment-failure-handling-policy.md
  - adr_02_003_runtime-tool-registry-routing-authority.md
  - mcp_03_01_dispatch-and-routing.md
  - agent_10_01_operations-and-observability-startup-and-health.md
  - agent_09_01_data-layer-session-db.md
  - agent_04_02_state-and-persistence-history-compression.md
  - agent_07_10_cli-and-commands-slash-commands-memory-other.md
  - adr_02_001_workflow-engine-mandatory.md
  - adr_02_002_config-isolation.md
  - agent_10_04_operations-and-observability-validation-and-troubleshooting.md
  - adr_02_007_http-mcp-adoption-and-stdio-non-support.md
  - security_01_architecture-and-trust-boundaries.md
  - mcp_02_02_startup-modes-and-health.md
  - deployment_01_deployment.md
  - adr_02_013_eventbus-authentication-authorization.md
  - adr_02_006_eventbus-sqlite-persistence-and-sse-delivery.md
  - db_03_architecture_and_schema-migration-and-scaling.md
  - adr_02_008_sqlite-4db-separation.md
  - overview_02_files.md
  - eventbus_07_configuration-and-operations.md
  - governance_05_change-impact-and-dependency-graphs.md
  - mcp_03_02_tool-registry.md
  - shared_03_04_runtime_and_execution-caching-and-reference.md
  - agent_05_llm-and-streaming.md
  - db_05_api_and_operations-protocol-and-backend.md
  - governance_04_documentation-checks.md
---

# Issue and Uncertainty Management

## Purpose

This document defines how to track currently active discrepancies between documentation and implementation (Known Issues) and currently active unverified claims, tracked as Needs Confirmation items. It ensures unconfirmed statements are trackable and actionable, preventing them from being silently accepted as facts.

## Part 1: Known Issues

### Entry Template

Each active Known Issue entry must contain these 17 fields: ID, Title, Status, Severity, Area, Type, Source, Owner, First Found, Target, Related, Summary, Current Description, Observed Implementation, Impact, Recommended Action, Resolution Target.

### Status Values

- **open** — Issue acknowledged but not yet investigated
- **investigating** — Investigation underway
- **deferred** — Resolution postponed to future work

An item is removed from this active inventory once it is resolved or no longer
applies to the current system; it is not retained here with a closed-out status.

### Type Values

document-code-mismatch, document-document-mismatch, obsolete-description, missing-documentation, ambiguous-behavior, implementation-bug (code does not match documented intent), design-gap, operational-gap.

### Unused Features

A symbol, configuration key, or statistic that production code under `scripts/` defines, validates, or exposes but never reads or calls (only tests or documents reference it) is registered as a `design-gap` when a document describes it as current behavior; closely related items share one entry.

### Severity Values

High (safety or critical functionality; immediate attention), Medium (correctness or clarity; address soon), Low (minor inconsistency; can be deferred).

### Owner Values

Unassigned, a person (`[Name]`), Team, or Repository owner.

### First Found and Related Values

`First Found` names the activity that surfaced the issue (for example, a documentation review); it is not a date. `Related` is `None` or a comma-separated list of Known Issue IDs and repository-relative document paths.

### Area Values

Overview, Deployment, RAG, MCP, Agent, EventBus, Shared/DB, Governance

### Review Cadence

Part 1 entries, Part 2 items, and "Proposed" ADRs are reviewed quarterly (`governance_01_documentation-policy.md`, Maintenance Rules).

### Active Items

Active Items follow an ordering convention: entries are grouped by ID-prefix (RAG-*, DESIGN-*, AGENT-*, MCP-*, DEPLOY-*, EVENTBUS-*, SHARED-*, CI-*), each group's entries in ascending numeric order.

| ID | Title | Status | Severity | Area | Type |
|----|-------|--------|----------|------|------|
| RAG-006 | Refiner settings in config/agent.toml are validated but never read by the Agent | open | Low | RAG | design-gap |
| RAG-007 | chunks_vec has no foreign key to chunks | open | Low | RAG | design-gap |
| AGENT-004 | A non-required subprocess MCP server aborts startup when it fails to spawn | open | Medium | Agent | design-gap |
| AGENT-005 | Approval and audit operation-type classification reads static tool-name sets before RuntimeToolRegistry | open | Medium | Agent | design-gap |
| AGENT-006 | Secret masking of MCP subprocess output recognizes only key=value forms | open | Medium | Agent | design-gap |
| AGENT-007 | A diagnostic row that fails to decrypt is returned as ciphertext with only a warning | open | Low | Agent | design-gap |
| AGENT-008 | /undo after a compressed session reload can undo fewer turns than expected | open | Low | Agent | design-gap |
| AGENT-009 | /skill messages lose the _ephemeral marker during append validation | open | Low | Agent | design-gap |
| AGENT-010 | The workflow loader requires require_approval=true although ADR-001 allows skipping approval | open | Medium | Agent | document-code-mismatch |
| AGENT-011 | The Agent startup security audit reads MCP server configuration models outside ADR-002's exceptions | open | Medium | Agent | document-code-mismatch |
| AGENT-012 | Agent statistics and health members are defined but never reached | open | Low | Agent | design-gap |
| MCP-001 | The shell, github, and file MCP servers register no Bearer-token authentication middleware | open | High | MCP | implementation-bug |
| DEPLOY-001 | LLM service start procedure is not provided by any repository script | open | Medium | Deployment | operational-gap |
| DEPLOY-002 | Production auxiliary uv run calls do not exclude the dev dependency group | open | Medium | Deployment | operational-gap |
| EVENTBUS-008 | Consumer-role token is unrestricted when the authorization mappings are empty | open | Medium | EventBus | design-gap |
| EVENTBUS-015 | Shared auth_token and admin_token grant every role | open | Medium | EventBus | design-gap |
| EVENTBUS-016 | Two EventBus DDL sources define slightly different schemas | open | Low | EventBus | design-gap |
| EVENTBUS-017 | No runtime component uses the EventBus although ADR-008 INV-07 relies on Events for cross-DB consistency | open | Medium | EventBus | design-gap |
| EVENTBUS-018 | retained_event_count is validated but never applied | open | Low | EventBus | design-gap |
| SHARED-001 | shared/security package has no importers | open | Low | Shared/DB | design-gap |
| SHARED-002 | Several shared and db helpers have no production caller | open | Low | Shared/DB | design-gap |

#### RAG-006

- **ID**: RAG-006
- **Title**: Refiner settings in config/agent.toml are validated but never read by the Agent
- **Status**: open
- **Severity**: Low
- **Area**: RAG
- **Type**: design-gap
- **Source**: `scripts/agent/config_builders.py`
- **Owner**: Repository owner
- **First Found**: Documentation review
- **Target**: `docs/21_rag/rag_05_01-configuration-reference.md`
- **Related**: `docs/10_adr/adr_02_010_rag-fallback.md`
- **Summary**: `use_refiner` and the `refiner_*` keys in `config/agent.toml` are not read by any Agent code path.
- **Current Description**: The keys appear as Agent RAG settings.
- **Observed Implementation**: Only `embed_url` is read from `AgentConfig.rag`; the rag-pipeline MCP server uses `config/rag_pipeline_mcp_server.toml`.
- **Impact**: Editing these keys has no effect on refiner behavior.
- **Recommended Action**: Remove the unused keys from `config/agent.toml` and `RAGConfig`, or wire them to a consumer.
- **Resolution Target**: Every refiner key in `config/agent.toml` has a consumer, or the keys are removed.

#### RAG-007

- **ID**: RAG-007
- **Title**: chunks_vec has no foreign key to chunks
- **Status**: open
- **Severity**: Low
- **Area**: RAG
- **Type**: design-gap
- **Source**: `scripts/db/schema_sql.py`
- **Owner**: Repository owner
- **First Found**: ADR Known Deviations review
- **Target**: `docs/10_adr/adr_02_005_rag-source-derived-index-relationships.md`
- **Related**: None
- **Summary**: The `sqlite-vec` virtual table `chunks_vec` cannot declare a foreign key to `chunks`.
- **Current Description**: ADR-005 requires derived index rows to follow their source rows.
- **Observed Implementation**: All deletion paths delete the `chunks_vec` rows explicitly before `documents`. The `chunks_vec_ad` trigger on `chunks` also removes the matching vector row, including on the `documents` cascade, as a backstop.
- **Impact**: Orphaned vector rows remain only if the trigger is missing from the schema or fails; `check_rag_consistency()` reports them.
- **Recommended Action**: Keep the ordering invariant tested, and revisit when `sqlite-vec` supports foreign keys.
- **Resolution Target**: `sqlite-vec` supports foreign keys, or the limitation is recorded as accepted.

#### AGENT-004

- **ID**: AGENT-004
- **Title**: A non-required subprocess MCP server aborts startup when it fails to spawn
- **Status**: open
- **Severity**: Medium
- **Area**: Agent
- **Type**: design-gap
- **Source**: `scripts/agent/startup_mcp_starter.py`
- **Owner**: Repository owner
- **First Found**: Documentation review
- **Target**: `docs/10_adr/adr_02_004_environment-failure-handling-policy.md`
- **Related**: None
- **Summary**: The spawn path never reads `required`, so `required=false` does not disable the server.
- **Current Description**: ADR-004 disables a non-mandatory component and continues startup.
- **Observed Implementation**: `McpServerStarter` retries once and raises a fatal error; `required` is applied only during discovery.
- **Impact**: A non-required server can still block startup.
- **Recommended Action**: Apply `required` to spawn failures, or record the exception in ADR-004.
- **Resolution Target**: Spawn failures follow `required`, or ADR-004 records the exception.

#### AGENT-005

- **ID**: AGENT-005
- **Title**: Approval and audit operation-type classification reads static tool-name sets before RuntimeToolRegistry
- **Status**: open
- **Severity**: Medium
- **Area**: Agent
- **Type**: design-gap
- **Source**: `scripts/agent/tool_policy.py`
- **Owner**: Repository owner
- **First Found**: Documentation review
- **Target**: `docs/10_adr/adr_02_003_runtime-tool-registry-routing-authority.md`
- **Related**: `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`
- **Summary**: `classify_operation_type()` reads the frozensets in `shared/tool_constants.py` first and uses `RuntimeToolRegistry` only for READ versus UNKNOWN.
- **Current Description**: ADR-003 INV-03 requires approval and auditing to reference the same `RuntimeTool` attributes as routing.
- **Observed Implementation**: The operation type does not read the `RuntimeTool` write attribute.
- **Impact**: A tool name missing from the static sets and registered as a write tool in `RuntimeToolRegistry` is classified READ for approval and audit.
- **Recommended Action**: Derive the operation type from `RuntimeTool`, or record the static-set classification as an accepted exception in ADR-003.
- **Resolution Target**: Approval and audit classification reference `RuntimeTool`, or ADR-003 records the exception.

#### AGENT-006

- **ID**: AGENT-006
- **Title**: Secret masking of MCP subprocess output recognizes only key=value forms
- **Status**: open
- **Severity**: Medium
- **Area**: Agent
- **Type**: design-gap
- **Source**: `scripts/agent/secrets_masker.py`
- **Owner**: Repository owner
- **First Found**: Documentation review
- **Target**: `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`
- **Related**: None
- **Summary**: Masking of MCP subprocess output matches only `key=value` forms.
- **Current Description**: Documented only as a chapter-level limitation in agent_10_01.
- **Observed Implementation**: `_mask_secrets()` matches `password`, `api_key`, `secret` and `token` as `key=value`; a Bearer header is not masked.
- **Impact**: Other secret shapes can reach logs and reports.
- **Recommended Action**: Extend the patterns or reuse the shared redaction registry.
- **Resolution Target**: Registered secrets in subprocess output are masked, tested.

#### AGENT-007

- **ID**: AGENT-007
- **Title**: A diagnostic row that fails to decrypt is returned as ciphertext with only a warning
- **Status**: open
- **Severity**: Low
- **Area**: Agent
- **Type**: design-gap
- **Source**: `scripts/agent/diagnostic_store.py`
- **Owner**: Repository owner
- **First Found**: Documentation review
- **Target**: `docs/23_agent/agent_09_01_data-layer-session-db.md`
- **Related**: None
- **Summary**: A failed decryption leaves the ciphertext in the returned row.
- **Current Description**: Documented only as a chapter-level limitation in agent_09_01.
- **Observed Implementation**: The loader logs a warning and keeps the Fernet token in `content`.
- **Impact**: A wrong or rotated key is not surfaced to the caller.
- **Recommended Action**: Mark the row undecryptable or raise, or record it as accepted.
- **Resolution Target**: A decryption failure is visible to the caller, or the tolerance is recorded.

#### AGENT-008

- **ID**: AGENT-008
- **Title**: /undo after a compressed session reload can undo fewer turns than expected
- **Status**: open
- **Severity**: Low
- **Area**: Agent
- **Type**: design-gap
- **Source**: `scripts/agent/services/undo_service.py`
- **Owner**: Repository owner
- **First Found**: Documentation review
- **Target**: `docs/23_agent/agent_04_02_state-and-persistence-history-compression.md`
- **Related**: None
- **Summary**: Compression replaces original messages with a summary, so fewer turns are undoable.
- **Current Description**: Documented only as a chapter-level limitation in agent_04_02.
- **Observed Implementation**: `undo_last_turn()` removes the last turn from history and DB rows and only warns when it removes a summary.
- **Impact**: Original messages cannot be recovered after compression.
- **Recommended Action**: Keep originals recoverable, or record the limitation as accepted.
- **Resolution Target**: The undo range after compression is defined and tested.

#### AGENT-009

- **ID**: AGENT-009
- **Title**: /skill messages lose the _ephemeral marker during append validation
- **Status**: open
- **Severity**: Low
- **Area**: Agent
- **Type**: design-gap
- **Source**: `scripts/agent/commands/cmd_skill.py`
- **Owner**: Repository owner
- **First Found**: Documentation review
- **Target**: `docs/23_agent/agent_07_10_cli-and-commands-slash-commands-memory-other.md`
- **Related**: None
- **Summary**: The `/skill` message carries `_ephemeral` and `_skill_ephemeral`, but only `_skill_ephemeral` survives history validation.
- **Current Description**: Documented only as a chapter-level Known Limitation in the CLI skill-command chapter.
- **Observed Implementation**: `TRUSTED_SOURCES["skill_mixin"]` authorizes only `_skill_ephemeral`, so `append_message()` removes `_ephemeral` with a warning log.
- **Impact**: The orchestrator's generic `_ephemeral` pre-turn clearing does not remove injected skill messages at the start of the next turn.
- **Recommended Action**: Authorize `_ephemeral` for the skill source, or make the pre-turn clearing also handle `_skill_ephemeral`, or record the behavior as accepted.
- **Resolution Target**: Skill messages are cleared by one defined mechanism, with a test.

#### AGENT-010

- **ID**: AGENT-010
- **Title**: The workflow loader requires require_approval=true although ADR-001 allows skipping approval
- **Status**: open
- **Severity**: Medium
- **Area**: Agent
- **Type**: document-code-mismatch
- **Source**: `docs/10_adr/adr_02_001_workflow-engine-mandatory.md`, `scripts/agent/workflow/workflow_loader.py`
- **Owner**: Repository owner
- **First Found**: Documentation review
- **Target**: `docs/10_adr/adr_02_001_workflow-engine-mandatory.md`
- **Related**: None
- **Summary**: ADR-001 allows skipping the approval stage, while the loader accepts only definitions whose `require_approval` is true.
- **Current Description**: ADR-001 allows skipping only the approval stage; the Agent chapters describe the approval gate as active for every loaded definition.
- **Observed Implementation**: `WorkflowLoader._validate()` raises `WorkflowLoadError` when `require_approval` is absent or not true.
- **Impact**: A reader of ADR-001 can expect `require_approval=false` to load; the loader rejects it at startup.
- **Recommended Action**: Decide whether the mandatory gate is the adopted decision; if so, amend ADR-001 through the ADR approval process, otherwise relax the loader.
- **Resolution Target**: ADR-001 and the loader describe the same approval-skipping rule.

#### AGENT-011

- **ID**: AGENT-011
- **Title**: The Agent startup security audit reads MCP server configuration models outside ADR-002's exceptions
- **Status**: open
- **Severity**: Medium
- **Area**: Agent
- **Type**: document-code-mismatch
- **Source**: `scripts/agent/security_audit_config.py`
- **Owner**: Repository owner
- **First Found**: Documentation review
- **Target**: `docs/10_adr/adr_02_002_config-isolation.md`
- **Related**: None
- **Summary**: The Agent startup audit loads the shell, git, github, and cicd MCP configuration models, while ADR-002 requires the Agent to read only `config/agent.toml`.
- **Current Description**: ADR-002 INV-01 and INV-02 list only EventBus as an exception to the Agent reading other configuration files.
- **Observed Implementation**: `audit_security_defaults()` reads each MCP server's configuration file for the audit.
- **Impact**: The documented configuration isolation boundary and the audit read path disagree.
- **Recommended Action**: Decide whether the read-only audit is an accepted exception and record it in ADR-002 through the ADR approval process, or move the audit into the MCP servers.
- **Resolution Target**: ADR-002 and the startup audit describe the same configuration read boundary.

#### AGENT-012

- **ID**: AGENT-012
- **Title**: Agent statistics and health members are defined but never reached
- **Status**: open
- **Severity**: Low
- **Area**: Agent
- **Type**: design-gap
- **Source**: `scripts/agent/context.py`, `scripts/agent/http_lifecycle_health_checker.py`
- **Owner**: Repository owner
- **First Found**: Documentation review
- **Target**: `docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md`, `docs/10_adr/adr_02_004_environment-failure-handling-policy.md`
- **Related**: None
- **Summary**: `stat_semantic_cache_hits` is never incremented and `HealthChecker.startup_poll()` is called only by tests.
- **Current Description**: agent_10_04 documents the semantic-cache counter as only reset and displayed; ADR-004 lists `startup_poll()` among its implementation references.
- **Observed Implementation**: The counter is reset, persisted, and displayed but no code increments it; `startup_poll()` has no caller under `scripts/`.
- **Impact**: The counter is always 0 and the startup poll does not run in production.
- **Recommended Action**: Wire both into the runtime, or remove them and align the documents.
- **Resolution Target**: Each member is reached by runtime code or removed.

#### MCP-001

- **ID**: MCP-001
- **Title**: The shell, github, and file MCP servers register no Bearer-token authentication middleware
- **Status**: open
- **Severity**: High
- **Area**: MCP
- **Type**: implementation-bug
- **Source**: `scripts/mcp_servers/server.py`, `scripts/mcp_servers/{shell,github,file}/`
- **Owner**: Repository owner
- **First Found**: Documentation review
- **Target**: `docs/10_adr/adr_02_007_http-mcp-adoption-and-stdio-non-support.md`, `docs/91_security/security_01_architecture-and-trust-boundaries.md`, `docs/22_mcp/mcp_02_02_startup-modes-and-health.md`
- **Related**: None
- **Summary**: The shell, github, and file servers never call `attach_auth_middleware()`.
- **Current Description**: ADR-007 INV-09 requires every MCP server to reject a non-matching Bearer token, except the documented exceptions.
- **Observed Implementation**: Only the cicd, git, rag-pipeline, web-search, and mdq servers call `attach_auth_middleware()`. Requests without a token return 200 on `/v1/tools` for the others, while git returns 401.
- **Impact**: The documented authentication boundary does not hold for these servers (loopback-only bind limits exposure).
- **Recommended Action**: Register the middleware in these servers, or record an ADR-007 exception through the ADR approval process.
- **Resolution Target**: Every MCP server verifies the Bearer token, or ADR-007 lists the exceptions.

#### DEPLOY-001

- **ID**: DEPLOY-001
- **Title**: LLM service start procedure is not provided by any repository script
- **Status**: open
- **Severity**: Medium
- **Area**: Deployment
- **Type**: operational-gap
- **Source**: `deploy/setup_services.sh`
- **Owner**: Repository owner
- **First Found**: Documentation review
- **Target**: `docs/90_deployment/deployment_01_deployment.md`
- **Related**: None
- **Summary**: No repository script, unit file or configuration starts `embed-llm` and `agent-llm`.
- **Current Description**: The deployment document gives no start procedure for the LLM services.
- **Observed Implementation**: `setup_services.sh` only echoes the service names and queries their health endpoints; its header comment says they are agent-managed subprocesses, but the agent starts only MCP servers.
- **Impact**: An operator has no documented way to start the LLM services.
- **Recommended Action**: Decide where the procedure lives, document it, and correct the script header comment.
- **Resolution Target**: The deployment document describes how both LLM services are started.

#### DEPLOY-002

- **ID**: DEPLOY-002
- **Title**: Production auxiliary uv run calls do not exclude the dev dependency group
- **Status**: open
- **Severity**: Medium
- **Area**: Deployment
- **Type**: operational-gap
- **Source**: `deploy/deploy.sh`
- **Owner**: Repository owner
- **First Found**: Documentation review
- **Target**: `docs/90_deployment/deployment_01_deployment.md`
- **Related**: `DEPLOY-001`
- **Summary**: The deployment scripts call `uv run` for auxiliary steps without excluding the `dev` group.
- **Current Description**: deployment_01 section 1.2: the agent and MCP servers start from compiled binaries, `uv run` remains for auxiliary steps, and no script excludes the dev group.
- **Observed Implementation**: The deploy scripts call `uv run` with `UV_SYSTEM_CERTS=true` only; `pyproject.toml` has a `dev` group.
- **Impact**: An auxiliary `uv run` step can install development dependencies in production.
- **Recommended Action**: Exclude the dev group in the production scripts, or document a separate production sync.
- **Resolution Target**: Production excludes the dev group, or the production sync is documented.

#### EVENTBUS-008

- **ID**: EVENTBUS-008
- **Title**: Consumer-role token is unrestricted when the authorization mappings are empty
- **Status**: open
- **Severity**: Medium
- **Area**: EventBus
- **Type**: design-gap
- **Source**: `scripts/eventbus/auth.py`
- **Owner**: Repository owner
- **First Found**: ADR Known Deviations review
- **Target**: `docs/10_adr/adr_02_013_eventbus-authentication-authorization.md`
- **Related**: `docs/10_adr/adr_02_006_eventbus-sqlite-persistence-and-sse-delivery.md`
- **Summary**: A CONSUMER token whose `consumer_authorization` and `topic_authorization` mappings are both empty is not restricted to any consumer_id, and `auth_token` and `admin_token` are never restricted.
- **Current Description**: ADR-013 INV-02 forbids acting as another `consumer_id`.
- **Observed Implementation**: A `consumer_token` without `consumer_authorization` is rejected at startup. With empty `consumer_authorization` and `topic_authorization` mappings, the CONSUMER token gets `allowed_consumer_ids=None` (unrestricted), as do `auth_token` and `admin_token`.
- **Impact**: An unrestricted principal can use any `consumer_id`.
- **Recommended Action**: Deny all consumers when both mappings are empty, or reject an empty `consumer_authorization` at startup when `consumer_token` is configured.
- **Resolution Target**: Every CONSUMER token has a non-empty allowlist or is denied, covered by a test.

#### EVENTBUS-015

- **ID**: EVENTBUS-015
- **Title**: Shared auth_token and admin_token grant every role
- **Status**: open
- **Severity**: Medium
- **Area**: EventBus
- **Type**: design-gap
- **Source**: `scripts/eventbus/auth.py`
- **Owner**: Repository owner
- **First Found**: Documentation review
- **Target**: `docs/10_adr/adr_02_013_eventbus-authentication-authorization.md`
- **Related**: `EVENTBUS-008`
- **Summary**: The mandatory shared token and the admin token map to every role, so per-role separation holds only for callers that hold per-role tokens.
- **Current Description**: ADR-013 defines five roles, each granted a fixed set of routes.
- **Observed Implementation**: The principal map assigns every role to `auth_token` and to `admin_token`.
- **Impact**: A publisher or consumer process given `auth_token` can call operator and admin routes.
- **Recommended Action**: Keep these tokens operator-only and enforce that no publisher or consumer process receives them (for example by a deployment check against ADR-013 INV-07), or make per-role tokens sufficient so the every-role tokens are not needed.
- **Resolution Target**: ADR-013 and the deployment practice agree, or per-role tokens suffice.

#### EVENTBUS-016

- **ID**: EVENTBUS-016
- **Title**: Two EventBus DDL sources define slightly different schemas
- **Status**: open
- **Severity**: Low
- **Area**: EventBus
- **Type**: design-gap
- **Source**: `scripts/db/schema_sql.py`
- **Owner**: Repository owner
- **First Found**: Documentation review
- **Target**: `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`
- **Related**: None
- **Summary**: `eventbus.sqlite` can be created from two DDL sources that are not identical.
- **Current Description**: The database documents name both `build_eventbus_schema_sql()` (used by `create_schema()`) and `scripts/eventbus/schema.sql` (used by the EventBus service when the `events` table is missing) as DDL sources.
- **Observed Implementation**: The two differ in the `published_at` default and in one `consumer_delivery` index, which only `schema.sql` creates.
- **Impact**: A database bootstrapped by `create_schema()` can differ from one created by the service at first startup.
- **Recommended Action**: Make one source canonical and generate or load the other from it, or add a test that asserts the two stay equivalent.
- **Resolution Target**: Both bootstrap paths produce the same schema.

#### EVENTBUS-017

- **ID**: EVENTBUS-017
- **Title**: No runtime component uses the EventBus although ADR-008 INV-07 relies on Events for cross-DB consistency
- **Status**: open
- **Severity**: Medium
- **Area**: EventBus
- **Type**: design-gap
- **Source**: `scripts/agent/eventbus_client.py`, `scripts/agent/eventbus_subscriber.py`, `scripts/agent/eventbus_topic_admin_client.py`
- **Owner**: Repository owner
- **First Found**: Documentation review
- **Target**: `docs/10_adr/adr_02_008_sqlite-4db-separation.md`, `docs/01_overview/overview_02_files.md`
- **Related**: None
- **Summary**: ADR-008 Decision 8 and INV-07 guarantee cross-DB consistency by Events, but nothing at runtime publishes to or subscribes from the EventBus.
- **Current Description**: governance_05 states that no runtime component calls the EventBus; the three client modules under `scripts/agent/` are imported only by their unit tests.
- **Observed Implementation**: The EventBus service runs standalone; no Agent, RAG, or MCP code imports the client, subscriber, or topic-admin classes.
- **Impact**: The consistency mechanism named by INV-07 has no runtime path, so cross-DB consistency rests on idempotent processing and state reconciliation alone.
- **Recommended Action**: Wire a producer and consumer into the runtime, or amend ADR-008 through the ADR approval process and remove the unused client modules.
- **Resolution Target**: INV-07 names only mechanisms that run, or the EventBus has a runtime user.

#### EVENTBUS-018

- **ID**: EVENTBUS-018
- **Title**: retained_event_count is validated but never applied
- **Status**: open
- **Severity**: Low
- **Area**: EventBus
- **Type**: design-gap
- **Source**: `scripts/eventbus/config.py`
- **Owner**: Repository owner
- **First Found**: Documentation review
- **Target**: `docs/24_eventbus/eventbus_07_configuration-and-operations.md`
- **Related**: `EVENTBUS-017`
- **Summary**: The EventBus configuration accepts and validates `retained_event_count` but no code uses it to limit or prune events.
- **Current Description**: eventbus_07 documents the key as validated at startup but not consumed by any runtime path.
- **Observed Implementation**: Only `config.py` references the key (default, minimum check, known-key list); no retention logic reads it.
- **Impact**: Operators can set the value expecting event retention to change, and nothing happens.
- **Recommended Action**: Implement retention using the key, or remove it from the accepted configuration.
- **Resolution Target**: The key controls retention, or it is no longer accepted.

#### SHARED-001

- **ID**: SHARED-001
- **Title**: shared/security package has no importers
- **Status**: open
- **Severity**: Low
- **Area**: Shared/DB
- **Type**: design-gap
- **Source**: `scripts/shared/security/__init__.py`
- **Owner**: Repository owner
- **First Found**: Documentation review
- **Target**: `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`
- **Related**: None
- **Summary**: `HighRiskToolPolicy`, `SecurityMode`, and `AuditLogger` are defined but no module under `scripts/` or `tests/` imports them.
- **Current Description**: Documented only as a note in the Runtime Dependency Graph chapter.
- **Observed Implementation**: The package exports its names from `__init__.py` and nothing imports the package.
- **Impact**: No runtime path uses these classes, so any behavior they define does not take effect.
- **Recommended Action**: Wire the package into the runtime and add it to the dependency graph, or remove it and align the security documents.
- **Resolution Target**: The package is either imported by runtime code or removed.

#### SHARED-002

- **ID**: SHARED-002
- **Title**: Several shared and db helpers have no production caller
- **Status**: open
- **Severity**: Low
- **Area**: Shared/DB
- **Type**: design-gap
- **Source**: `scripts/shared/tool_routing_validation.py`, `scripts/shared/tool_executor_helpers.py`, `scripts/shared/tool_cache.py`, `scripts/shared/llm_client.py`, `scripts/db/store_impl.py`
- **Owner**: Repository owner
- **First Found**: Documentation review
- **Target**: `docs/22_mcp/mcp_03_02_tool-registry.md`, `docs/40_shared/shared_03_04_runtime_and_execution-caching-and-reference.md`, `docs/23_agent/agent_05_llm-and-streaming.md`, `docs/41_db/db_05_api_and_operations-protocol-and-backend.md`
- **Related**: `SHARED-001`
- **Summary**: `validate_all_routing()`, `is_side_effect()`, `ToolResultCache`, `LLMClient.call()`, and `SQLiteSessionStore` are called or instantiated only by tests.
- **Current Description**: The listed documents describe these as available helpers; some state that they are unused.
- **Observed Implementation**: No module under `scripts/` calls or instantiates them; session persistence goes through other classes.
- **Impact**: Behavior they define does not take effect, and the documents can read as if it did.
- **Recommended Action**: Wire each into the runtime, or remove it and align the documents.
- **Resolution Target**: Each helper has a runtime caller or is removed.

Other Known Issue IDs are not tracked here: a resolved or no-longer-applicable item is removed from this inventory.

## Part 2: Needs Confirmation Inventory

### Purpose

An inventory of active "Needs confirmation" items, so unconfirmed statements are tracked rather than silently accepted as facts.

### Inventory Entry Fields

Each entry must contain these fifteen fields: ID, Source File, Section, Line Number, Question, Evidence, Impact, Required Action, Status, Assigned To, Last Reviewed, Priority, Related NC, Resolution Target, Blocking.

### Status Values

- **open** — Acknowledged but not investigated
- **investigating** — Underway
- **deferred** — Postponed

As in Part 1, a resolved or inapplicable item is removed, not kept closed-out.

### Priority Values

- **High** — Must resolve before next release
- **Medium** — Resolve within sprint
- **Low** — Nice-to-have

### Extraction Process

Search `docs/` for "Needs confirmation", populate fields from context, add sequential ID, never modify source documents.

### Active Items

Each active item is listed with all fifteen Inventory Entry Fields above.

No active Needs Confirmation items remain.

## Part 3: Canonical Source Conflict

### Purpose

An inventory of active canonical source conflicts, so conflicting claims are tracked rather than silently accepted.

### Entry Template

Each active Canonical Source Conflict entry must contain these 12 fields: ID, Decision target, Claim type, Canonical source, Conflicting source or evidence, Conflict category, Impact, Severity (`High`/`Medium`/`Low`), Blocking status (`Blocking`/`Non-blocking`), Required action, Owner, Validation evidence.

### Status Values

- **open** — Conflict acknowledged but not yet investigated
- **investigating** — Investigation underway

An item is removed from this active inventory once it is resolved (exactly one normative source remains and validation evidence confirms the conflict is closed) or no longer applies to the current system; it is not retained here with a closed-out status.

### Active Items

No active Canonical Source Conflict items remain.

## Part 4: Configuration Drift

### Purpose

An inventory of discrepancies between deployed and approved operational values.

### Entry Template

Each active Configuration Drift entry must contain these 6 fields: ID, Decision target, Deployed value description, Approved operational value description, Severity, Status.

### Status Values

- **open** — Drift acknowledged but not yet investigated
- **investigating** — Investigation underway

An item is removed from this active inventory once it is resolved (deployed and approved values agree, or the approved value has been formally changed) or no longer applies to the current system; it is not retained here with a closed-out status.

### Active Items

No active Configuration Drift items remain.

## Resolution Rules

The following resolution criteria apply across all four parts of this document:

- Known Issue resolved only when implementation and design agree, or design is formally changed
- Configuration Drift resolved only when deployed and approved values agree, or approved value is formally changed
- Needs Confirmation removed only after evidence establishes intent and the canonical source is updated
- Canonical Source Conflict resolved only when exactly one normative source remains registered
- Documentation correction complete only when validation shows no stale statement remains
- Evidence is required before any discrepancy is reclassified or removed; a documentation-only edit cannot close a design-vs-code conflict without implementation evidence

## Temporary Exception Process

Applies to any automated check finding classified `Warning` (not `Blocking`) in
`docs/00_governance/governance_04_documentation-checks.md`'s Governance Verification Matrix
— for example, `GV-017`'s removed-name reintroduction findings. A `Warning`
finding does not block merge by itself, but leaving it neither fixed nor formally
excepted is not a complete review (see `docs/00_governance/governance_04_documentation-checks.md`
`### 19. Merge Condition Validation`).

### Exception Record Fields

A temporary exception records a **Reason** (why the finding is not fixed now), an **Owner** (the person who accepted it; not `Team` or `Unassigned`) and an **Expiration Date** (when it must be re-reviewed or fixed; an exception without one is not valid).

### Recording an Exception

Record the exception inline, next to the flagged line, as:

`<!-- exception: {rule-id} — {reason} — {owner} — expires {YYYY-MM-DD} -->`

An exception past its expiration date is treated as an unexplained finding (see
`docs/00_governance/governance_04_documentation-checks.md`
`### 19. Merge Condition Validation`) — not as still-covered.

## Non-Goals

Excluded topics:

- Resolving individual items — resolution requires separate investigation
- Modifying source documents during extraction — this document is read-only relative to sources
- Defining new evidence labels beyond those already established
- Changing the common template itself

## Keywords

- known issues
- needs confirmation
- inconsistencies
- template
- evidence labels
- resolution workflow
