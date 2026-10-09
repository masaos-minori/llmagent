---
title: "Issue and Uncertainty Management"
area: governance
tags:
  - governance
related:
  - 00_index.md
  - overview_00_document-guide.md
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

### Severity Values

High (safety or critical functionality; immediate attention), Medium (correctness or clarity; address soon), Low (minor inconsistency; can be deferred).

### Owner Values

Unassigned, a specific person (`[Name]`), or Team.

### Area Values

Overview, Deployment, RAG, MCP, Agent, EventBus, Shared/DB, Governance

### Review Cadence

Part 1 entries are reviewed quarterly, as are Part 2 items and "Proposed" ADRs (`governance_01_documentation-policy.md`, Maintenance Rules).

### Active Items

Active Items follow an ordering convention: entries are grouped by ID-prefix (RAG-*, DESIGN-*, AGENT-*, MCP-*, DEPLOY-*, EVENTBUS-*, SHARED-*, CI-*), each group's entries in ascending numeric order.

| ID | Title | Status | Severity | Area | Type |
|----|-------|--------|----------|------|------|
| RAG-002 | Japanese sentences with empty normalized text are dropped with their original text | open | Low | RAG | implementation-bug |
| RAG-006 | Refiner settings in config/agent.toml are validated but never read by the Agent | open | Low | RAG | design-gap |
| AGENT-001 | Default workflow definition does not satisfy the documented require_approval policy | open | Medium | Agent | design-gap |
| AGENT-002 | No regression test for ADR-014 INV-02 | open | Low | Agent | operational-gap |
| AGENT-004 | A non-required subprocess MCP server aborts startup when it fails to spawn | open | Medium | Agent | design-gap |
| AGENT-005 | Approval and audit operation-type classification reads static tool-name sets before RuntimeToolRegistry | open | Medium | Agent | design-gap |
| AGENT-006 | Secret masking of MCP subprocess output recognizes only key=value forms | open | Medium | Agent | design-gap |
| AGENT-007 | A diagnostic row that fails to decrypt is returned as ciphertext with only a warning | open | Low | Agent | design-gap |
| AGENT-008 | /undo after a compressed session reload can undo fewer turns than expected | open | Low | Agent | design-gap |
| MCP-003 | cicd-mcp workflow_allowlist entries do not match the workflow value the tool receives | open | Medium | MCP | implementation-bug |
| DEPLOY-001 | LLM service start procedure is not provided by any repository script | open | Medium | Deployment | operational-gap |
| DEPLOY-002 | Production uv run does not exclude the dev dependency group | open | Medium | Deployment | operational-gap |
| EVENTBUS-008 | Consumer-role token without a consumer_id allowlist skips consumer-identity validation | open | Medium | EventBus | design-gap |
| EVENTBUS-011 | NACK on a concurrently deleted event can return a misleading 409 | open | Low | EventBus | implementation-bug |
| EVENTBUS-012 | Duplicate NACK from the same consumer increments the failure counters on every call | open | Medium | EventBus | implementation-bug |
| EVENTBUS-013 | ACK and NACK are not bound to the active subscription of a consumer_id | open | Medium | EventBus | design-gap |
| EVENTBUS-014 | `events.acked_at` is never written but is still read | open | Low | EventBus | implementation-bug |
| EVENTBUS-015 | Shared auth_token and admin_token grant every role | open | Medium | EventBus | design-gap |

#### RAG-002

- **ID**: RAG-002
- **Title**: Japanese sentences with empty normalized text are dropped with their original text
- **Status**: open
- **Severity**: Low
- **Area**: RAG
- **Type**: implementation-bug
- **Source**: `scripts/rag/ingestion/chunk_japanese.py`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/10_adr/ADR-009-rag-fts5-text-separation.md`
- **Related**: None
- **Summary**: Sentences that normalize to nothing are dropped, so `content` is lost for them.
- **Current Description**: ADR-009 INV-11 says a sentence whose normalized text is empty keeps its original text in `content`.
- **Observed Implementation**: `_split_into_ja_sentences()` drops a pair whose normalized text is empty, together with the original sentence.
- **Impact**: Original text of such sentences is missing from the index.
- **Recommended Action**: Keep the original sentence in `content` when normalization is empty.
- **Resolution Target**: `content` keeps every original sentence, covered by a test.

#### RAG-006

- **ID**: RAG-006
- **Title**: Refiner settings in config/agent.toml are validated but never read by the Agent
- **Status**: open
- **Severity**: Low
- **Area**: RAG
- **Type**: design-gap
- **Source**: `scripts/agent/config_builders.py`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/21_rag/rag_05_01-configuration-reference.md`
- **Related**: `docs/10_adr/ADR-010-rag-fallback.md`
- **Summary**: `use_refiner` and the `refiner_*` keys in `config/agent.toml` are not read by any Agent code path.
- **Current Description**: The keys appear as Agent RAG settings.
- **Observed Implementation**: Only `embed_url` is read from `AgentConfig.rag`; the rag-pipeline MCP server uses `config/rag_pipeline_mcp_server.toml`.
- **Impact**: Editing these keys has no effect on refiner behavior.
- **Recommended Action**: Remove the unused keys from `config/agent.toml` and `RAGConfig`, or wire them to a consumer.
- **Resolution Target**: Every refiner key in `config/agent.toml` has a consumer, or the keys are removed.

#### AGENT-001

- **ID**: AGENT-001
- **Title**: Default workflow definition does not satisfy the documented require_approval policy
- **Status**: open
- **Severity**: Medium
- **Area**: Agent
- **Type**: design-gap
- **Source**: `config/workflows/default.json`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`
- **Related**: `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`
- **Summary**: The documented policy requires workflow-level approval for some categories, but the bundled default sets `require_approval` to false and no code enforces the policy.
- **Current Description**: agent_03_03 labels the policy operational only.
- **Observed Implementation**: `WorkflowLoader` treats `require_approval` as optional (false when absent); `ProductionConfigValidator` has no rule for it.
- **Impact**: A default deployment has no workflow-level approval gate (the tool-level gate is separate).
- **Recommended Action**: Either enforce the policy (validator rule and default definition) or reduce it to a recommendation.
- **Resolution Target**: Policy, default definition and validator agree.

#### AGENT-002

- **ID**: AGENT-002
- **Title**: No regression test for ADR-014 INV-02
- **Status**: open
- **Severity**: Low
- **Area**: Agent
- **Type**: operational-gap
- **Source**: `scripts/agent/orchestrator.py`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/10_adr/ADR-014-agent-control-plane-responsibility-boundaries.md`
- **Related**: None
- **Summary**: ADR-014 INV-02 (only the component that drives the LLM/tool-call loop creates `LlmTurnExecutor`) has no automated test.
- **Current Description**: ADR-014 lists the test as not yet written.
- **Observed Implementation**: `Orchestrator.__init__` creates only `_llm_executor` and passes it to the workflow adapter; no test asserts this.
- **Impact**: A regression could go unnoticed.
- **Recommended Action**: Add a unit test that `Orchestrator` constructs exactly one `LlmTurnExecutor`.
- **Resolution Target**: A test covers ADR-014 INV-02.

#### AGENT-004

- **ID**: AGENT-004
- **Title**: A non-required subprocess MCP server aborts startup when it fails to spawn
- **Status**: open
- **Severity**: Medium
- **Area**: Agent
- **Type**: design-gap
- **Source**: `scripts/agent/startup_mcp_starter.py`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/10_adr/ADR-004-environment-failure-handling-policy.md`
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
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md`
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
- **Owner**: Unassigned
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
- **Owner**: Unassigned
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
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/23_agent/agent_04_02_state-and-persistence-history-compression.md`
- **Related**: None
- **Summary**: Compression replaces original messages with a summary, so fewer turns are undoable.
- **Current Description**: Documented only as a chapter-level limitation in agent_04_02.
- **Observed Implementation**: `undo_last_turn()` removes the last turn from history and DB rows and only warns when it removes a summary.
- **Impact**: Original messages cannot be recovered after compression.
- **Recommended Action**: Keep originals recoverable, or record the limitation as accepted.
- **Resolution Target**: The undo range after compression is defined and tested.

#### MCP-003

- **ID**: MCP-003
- **Title**: cicd-mcp workflow_allowlist entries do not match the workflow value the tool receives
- **Status**: open
- **Severity**: Medium
- **Area**: MCP
- **Type**: implementation-bug
- **Source**: `config/cicd_mcp_server.toml`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/22_mcp/mcp_05_01_access-control-and-allowlists.md`
- **Related**: `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`
- **Summary**: The checked-in allowlist uses a full-path form, but `trigger_workflow` compares the request's `workflow` value by exact match and its schema describes a file name or workflow ID.
- **Current Description**: Configuration comment, example and checked-in value use different forms.
- **Observed Implementation**: `_assert_allowed_workflow()` tests `workflow not in allowlist`; tests use `ci.yml`.
- **Impact**: `workflow="ci.yml"` is rejected under the checked-in configuration.
- **Recommended Action**: Decide the accepted form (file name or full path), then align the guard or normalization, the configuration value and comment, and the documentation.
- **Resolution Target**: The allowlist form, the guard, the tool schema and the documentation agree.

#### DEPLOY-001

- **ID**: DEPLOY-001
- **Title**: LLM service start procedure is not provided by any repository script
- **Status**: open
- **Severity**: Medium
- **Area**: Deployment
- **Type**: operational-gap
- **Source**: `deploy/setup_services.sh`
- **Owner**: Unassigned
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
- **Title**: Production uv run does not exclude the dev dependency group
- **Status**: open
- **Severity**: Medium
- **Area**: Deployment
- **Type**: operational-gap
- **Source**: `deploy/deploy.sh`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/90_deployment/deployment_01_deployment.md`
- **Related**: `DEPLOY-001`
- **Summary**: The deployment scripts call `uv run` without excluding the `dev` dependency group.
- **Current Description**: deployment_01 section 1.2 states that no script passes such a flag.
- **Observed Implementation**: The deploy scripts call `uv run` with `UV_SYSTEM_CERTS=true` only; `pyproject.toml` has a `dev` group.
- **Impact**: Development dependencies can be installed in production.
- **Recommended Action**: Exclude the dev group in the production scripts, or document a separate production sync.
- **Resolution Target**: Production excludes the dev group, or the production sync is documented.

#### EVENTBUS-008

- **ID**: EVENTBUS-008
- **Title**: Consumer-role token without a consumer_id allowlist skips consumer-identity validation
- **Status**: open
- **Severity**: Medium
- **Area**: EventBus
- **Type**: design-gap
- **Source**: `scripts/eventbus/auth.py`
- **Owner**: Unassigned
- **First Found**: ADR Known Deviations review
- **Target**: `docs/10_adr/ADR-013-eventbus-authentication-authorization.md`
- **Related**: `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/ADR-008-sqlite-4db-separation.md`
- **Summary**: A principal without a consumer_id allowlist is not restricted to any consumer_id.
- **Current Description**: ADR-013 INV-02 forbids acting as another `consumer_id`.
- **Observed Implementation**: A `consumer_token` without `consumer_authorization` is rejected at startup. With empty `consumer_authorization` and `topic_authorization` mappings, the CONSUMER token gets `allowed_consumer_ids=None` (unrestricted), as do `auth_token` and `admin_token`.
- **Impact**: An unrestricted principal can use any `consumer_id`.
- **Recommended Action**: Deny all consumers on an empty mapping, or reject it at startup.
- **Resolution Target**: Every CONSUMER token has a non-empty allowlist or is denied, covered by a test.

#### EVENTBUS-011

- **ID**: EVENTBUS-011
- **Title**: NACK on a concurrently deleted event can return a misleading 409
- **Status**: open
- **Severity**: Low
- **Area**: EventBus
- **Type**: implementation-bug
- **Source**: `scripts/eventbus/ack_route.py`
- **Owner**: Unassigned
- **First Found**: ADR Known Deviations review
- **Target**: `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`
- **Related**: None
- **Summary**: An event deleted between the NACK call and the follow-up lookup yields 409 instead of 404.
- **Current Description**: ADR-006 records the `(-2, -2)` result and a residual deletion race.
- **Observed Implementation**: `ack_route.py` re-reads `acked_at`/`dlq_at` in a separate `run_with_db_lock()` call; a missing row falls into the final `else` and raises 409 "invalid NACK transition".
- **Impact**: Low: one request returns the wrong status code.
- **Recommended Action**: Treat a missing row as 404, or run the NACK and the lookup under one lock acquisition.
- **Resolution Target**: A NACK on a concurrently deleted event returns 404, covered by a test.

#### EVENTBUS-012

- **ID**: EVENTBUS-012
- **Title**: Duplicate NACK from the same consumer increments the failure counters on every call
- **Status**: open
- **Severity**: Medium
- **Area**: EventBus
- **Type**: implementation-bug
- **Source**: `scripts/eventbus/delivery_repo.py`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`
- **Related**: None
- **Summary**: A NACK of an event that is neither ACKed nor in the DLQ always increments `delivery_failure_count` and `cycle_failure_count`.
- **Current Description**: No guard exists for a repeated NACK, unlike ACK-then-NACK.
- **Observed Implementation**: `nack_event()` applies its `UPDATE` whenever `acked_at IS NULL AND dlq_at IS NULL`; there is no per-consumer NACK-state check.
- **Impact**: A duplicated NACK can promote an event to the DLQ early.
- **Recommended Action**: Decide whether NACK must be idempotent per consumer; if so add a guard and align the documentation.
- **Resolution Target**: Repeated NACKs for the same delivery attempt do not change the counters again, covered by a test.

#### EVENTBUS-013

- **ID**: EVENTBUS-013
- **Title**: ACK and NACK are not bound to the active subscription of a consumer_id
- **Status**: open
- **Severity**: Medium
- **Area**: EventBus
- **Type**: design-gap
- **Source**: `scripts/eventbus/ack_route.py`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`
- **Related**: `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`
- **Summary**: ACK and NACK check token binding but not the active subscription of the `consumer_id`.
- **Current Description**: ADR-006 INV-10 allows one active `/subscribe` connection per consumer ID and binds ACK and NACK to the caller's token.
- **Observed Implementation**: `/ack` and `/nack` reject a `consumer_id` outside the caller's allowlist. Only `/subscribe` gets 409 from the broker registry for a second connection.
- **Impact**: Callers sharing a token and `consumer_id` overwrite each other's progress.
- **Recommended Action**: Bind ACK and NACK to the active subscription, or record token-only binding as accepted in ADR-006; add a test.
- **Resolution Target**: ADR-006 INV-10 and ACK/NACK behavior agree, covered by a test.

#### EVENTBUS-014

- **ID**: EVENTBUS-014
- **Title**: `events.acked_at` is never written but is still read
- **Status**: open
- **Severity**: Low
- **Area**: EventBus
- **Type**: implementation-bug
- **Source**: `scripts/eventbus/delivery_repo.py`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`
- **Related**: `EVENTBUS-012`
- **Summary**: The ACK route writes only per-consumer state, yet NACK and a 409 branch test `events.acked_at`.
- **Current Description**: The delivery-semantics document defines ACKed per consumer.
- **Observed Implementation**: `ack_event_for_consumer()` writes `consumer_delivery` and `consumer_offsets`; `ack_event()`, the only writer of `events.acked_at`, has no caller.
- **Impact**: The event-level ACK guard in NACK never triggers.
- **Recommended Action**: Remove the dead helper, column and checks, or write the column on ACK.
- **Resolution Target**: No code reads `events.acked_at` without a writer.

#### EVENTBUS-015

- **ID**: EVENTBUS-015
- **Title**: Shared auth_token and admin_token grant every role
- **Status**: open
- **Severity**: Medium
- **Area**: EventBus
- **Type**: design-gap
- **Source**: `scripts/eventbus/auth.py`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/10_adr/ADR-013-eventbus-authentication-authorization.md`
- **Related**: `EVENTBUS-008`
- **Summary**: The mandatory shared token and the admin token map to every role, so per-role separation holds only for callers that hold per-role tokens.
- **Current Description**: ADR-013 defines five roles, each granted a fixed set of routes.
- **Observed Implementation**: The principal map assigns every role to `auth_token` and to `admin_token`.
- **Impact**: A publisher or consumer process given `auth_token` can call operator and admin routes.
- **Recommended Action**: Keep these tokens operator-only and enforce that no publisher or consumer process receives them (for example by a deployment check against ADR-013 INV-07), or make per-role tokens sufficient so the every-role tokens are not needed.
- **Resolution Target**: ADR-013 and the deployment practice agree, or per-role tokens suffice.

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

An item is removed from the Active Items list below once it is resolved through a
code or docs update, or once it no longer applies to the current system; it is not
retained here with a closed-out status.

### Priority Values

- **High** — Must resolve before next release
- **Medium** — Resolve within sprint
- **Low** — Nice-to-have

### Extraction Process

Search `docs/` for "Needs confirmation", populate fields from context, add sequential ID, never modify source documents.

### Active Items

| Item ID | Title | Category | Priority | Evidence | Required Decision |
|---------|-------|----------|----------|----------|-------------------|

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

No other active Canonical Source Conflict items remain open.

## Part 4: Configuration Drift

### Purpose

An inventory of discrepancies between deployed and approved operational values.

### Entry Template

Each active Configuration Drift entry must contain these 6 fields: ID, Decision target, Deployed value description, Approved operational value description, Severity, Status.

### Status Values

- **open** — Drift acknowledged but not yet investigated
- **investigating** — Investigation underway

An item is removed from this active inventory once it is resolved (deployed and approved values agree, or the approved value has been formally changed) or no longer applies to the current system; it is not retained here with a closed-out status.

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
