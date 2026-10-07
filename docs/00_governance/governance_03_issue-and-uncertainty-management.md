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
| RAG-001 | HTTP 401/403 from the RAG service still falls back to the in-process pipeline | open | Medium | RAG | implementation-bug |
| RAG-002 | Japanese sentences with empty normalized text are dropped with their original text | open | Low | RAG | implementation-bug |
| AGENT-001 | Default workflow definition does not satisfy the documented require_approval policy | open | Medium | Agent | design-gap |
| AGENT-002 | No regression test for ADR-014 INV-02 | open | Low | Agent | operational-gap |
| AGENT-003 | Orchestrator continues in fallback mode when the workflow fails to load | open | Medium | Agent | design-gap |
| MCP-001 | git-mcp audit records are never emitted | open | Medium | MCP | implementation-bug |
| MCP-002 | git_pull and git_push schema contradicts the protected-branch validation | open | Medium | MCP | implementation-bug |
| MCP-003 | cicd-mcp workflow_allowlist entries do not match the workflow value the tool receives | open | Medium | MCP | implementation-bug |
| DEPLOY-001 | LLM service start procedure is not provided by any repository script | open | Medium | Deployment | operational-gap |
| EVENTBUS-008 | Consumer-role token without a consumer_id allowlist skips consumer-identity validation | open | Medium | EventBus | design-gap |
| EVENTBUS-011 | NACK on a concurrently deleted event can return a misleading 409 | open | Low | EventBus | implementation-bug |
| EVENTBUS-012 | Duplicate NACK from the same consumer increments the failure counters on every call | open | Medium | EventBus | implementation-bug |
| EVENTBUS-013 | ACK and NACK do not enforce Consumer ID exclusivity (ADR-006 INV-10) | open | Medium | EventBus | design-gap |

#### AGENT-003

- **ID**: AGENT-003
- **Title**: Orchestrator continues in fallback mode when the workflow fails to load
- **Status**: open
- **Severity**: Medium
- **Area**: Agent
- **Type**: design-gap
- **Source**: `scripts/agent/orchestrator.py`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/10_adr/ADR-001-workflow-engine-mandatory.md`
- **Related**: `docs/10_adr/ADR-004-environment-failure-handling-policy.md`
- **Summary**: `Orchestrator.__init__()` catches workflow load errors and runs with a stage-less workflow.
- **Current Description**: ADR-001 and ADR-004 require startup to abort.
- **Observed Implementation**: The preflight normally aborts first; otherwise the REPL starts in fallback mode.
- **Impact**: The agent runs without workflow features.
- **Recommended Action**: Abort startup on load failure, or record the exception in the ADRs.
- **Resolution Target**: Startup aborts, or the ADRs record the exception.

#### RAG-001

- **ID**: RAG-001
- **Title**: HTTP 401/403 from the RAG service still falls back to the in-process pipeline
- **Status**: open
- **Severity**: Medium
- **Area**: RAG
- **Type**: implementation-bug
- **Source**: `scripts/rag/pipeline_service.py`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/10_adr/ADR-010-rag-fallback.md`
- **Related**: None
- **Summary**: ADR-010 forbids falling back on 401/403, but the code falls back.
- **Current Description**: Decision 6 and INV-04 say authentication failures do not fall back.
- **Observed Implementation**: `call_rag_service()` returns `None` for 401/403; `HttpAugment.run()` reports it as `in_process_fallback`; the pipeline then runs in-process. A mocked 401 confirmed this.
- **Impact**: Authentication failures are hidden behind a local result.
- **Recommended Action**: Surface `AUTH_ERROR` and skip the fallback, then test the caller-level behavior.
- **Resolution Target**: A 401/403 produces `AUTH_ERROR` with no fallback, covered by a test.

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
- **Target**: `docs/10_adr/ADR-009-rag-ft5-text-separation.md`
- **Related**: None
- **Summary**: Sentences that normalize to nothing are dropped, so `content` is lost for them.
- **Current Description**: ADR-009 INV-05 says normalization never costs original text.
- **Observed Implementation**: `_split_into_ja_sentences()` drops a pair whose normalized text is empty, together with the original sentence.
- **Impact**: Original text of such sentences is missing from the index.
- **Recommended Action**: Keep the original sentence in `content` when normalization is empty.
- **Resolution Target**: `content` keeps every original sentence, covered by a test.

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

#### MCP-001

- **ID**: MCP-001
- **Title**: git-mcp audit records are never emitted
- **Status**: open
- **Severity**: Medium
- **Area**: MCP
- **Type**: implementation-bug
- **Source**: `scripts/mcp_servers/git/git_server.py`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/22_mcp/mcp_04_05_git.md`
- **Related**: `docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md`
- **Summary**: `call_tool` passes keyword arguments that `_audit_log()` does not accept, so no audit record is written.
- **Current Description**: mcp_04_05 describes audit fields that are never written.
- **Observed Implementation**: `call_tool` passes `requested_target=`/`canonical_target=`; the `TypeError` is swallowed by `_audit_log_safe()` and only `audit_log failed` is logged. Tests mock `_audit_log`.
- **Impact**: git-mcp writes leave no audit record.
- **Recommended Action**: Align the `_audit_log()` signature with its callers and test the real function.
- **Resolution Target**: Each git-mcp call writes an audit record, covered by a test.

#### MCP-002

- **ID**: MCP-002
- **Title**: git_pull and git_push schema contradicts the protected-branch validation
- **Status**: open
- **Severity**: Medium
- **Area**: MCP
- **Type**: implementation-bug
- **Source**: `scripts/mcp_servers/git/git_tools.py`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/22_mcp/mcp_04_05_git.md`
- **Related**: `docs/22_mcp/mcp_04_05_git.md`
- **Summary**: The tool schema and the service validation disagree about an empty `branch`.
- **Current Description**: The schema and the validation disagree about an empty `branch`.
- **Observed Implementation**: `GitService._validate_protected()` rejects an empty `branch` for checkout, pull and push.
- **Impact**: Calls relying on the schema default are rejected.
- **Recommended Action**: Resolve the current branch before validation, or make `branch` required in the schema.
- **Resolution Target**: Schema, validation and mcp_04_05 agree.

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
- **Summary**: A CONSUMER-role token with no allowlist is not restricted to any consumer_id (fail-open).
- **Current Description**: ADR-013 treats the consumer_id allowlist as the residual gap.
- **Observed Implementation**: `_populate_token_maps()` sets `allowed_consumer_ids` only when `consumer_authorization` or `topic_authorization` is configured; `require_consumer_identity()` skips validation when it is `None`.
- **Impact**: An unrestricted CONSUMER token can act under any consumer_id.
- **Recommended Action**: Decide between rejecting such a token (fail-closed) and accepting the unrestricted contract, then align `auth.py` or ADR-013.
- **Resolution Target**: Implementation and ADR-013 agree for a CONSUMER token without an allowlist.

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
- **Title**: ACK and NACK do not enforce Consumer ID exclusivity (ADR-006 INV-10)
- **Status**: open
- **Severity**: Medium
- **Area**: EventBus
- **Type**: design-gap
- **Source**: `scripts/eventbus/ack_route.py`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`
- **Related**: `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`
- **Summary**: INV-10 forbids concurrent use of one `consumer_id`, but only `/subscribe` enforces it.
- **Current Description**: The delivery-semantics document states ACK does not detect a collision.
- **Observed Implementation**: A second concurrent `/subscribe` gets 409 from the in-process broker registry; `/ack` and `/nack` check only the principal allowlist.
- **Impact**: Callers sharing a `consumer_id` overwrite each other's progress.
- **Recommended Action**: Bind ACK/NACK to the active subscription, or narrow INV-10 to the subscribe path; add a test.
- **Resolution Target**: INV-10 and the ACK path agree, covered by a test.

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

Topics explicitly excluded from this document:

- Resolving individual items — resolution requires separate investigation
- Modifying source documents during extraction — this document is read-only relative to sources
- Defining new evidence labels beyond those already established
- Changing the common template itself

## Keywords

known issues
needs confirmation
inconsistencies
template
evidence labels
resolution workflow
