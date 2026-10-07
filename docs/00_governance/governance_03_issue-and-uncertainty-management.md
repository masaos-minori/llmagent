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

Open → Investigating → Deferred, or removed from this inventory once resolved or no
longer applicable to the current system.

### Review Cadence

Part 1 entries are reviewed quarterly, consistent with the cadence documented for Part 2 Needs Confirmation items and "Proposed" ADRs in `docs/00_governance/governance_01_documentation-policy.md` under `## Maintenance Rules`.

### Active Items

Active Items follow an ordering convention: entries are grouped by ID-prefix (RAG-*, DESIGN-*, AGENT-*, MCP-*, DEPLOY-*, EVENTBUS-*, SHARED-*, CI-*), each group's entries in ascending numeric order.

| ID | Title | Status | Severity | Area | Type | Source | Owner | First Found | Summary | Related |
|----|-------|--------|----------|------|------|--------|-------|-------------|---------|---------|
| DESIGN-001 | ADR-002 Agent required-keys row lists keys absent from config/agent.toml | open | Low | Governance | document-code-mismatch | `ADR-002` | Unassigned | Documentation review | Agent row names keys absent from `config/agent.toml` | `ADR-002` |
| AGENT-001 | Default workflow definition does not satisfy the documented require_approval policy | open | Medium | Agent | design-gap | `config/workflows/default.json` | Unassigned | Documentation review | Default workflow sets `require_approval` false; policy not enforced | `agent_03` |
| MCP-001 | git-mcp audit records are never emitted | open | Medium | MCP | implementation-bug | `scripts/mcp_servers/git/git_server.py` | Unassigned | Documentation review | `_audit_log()` rejects the keywords `call_tool` passes; no audit record | `mcp_04`, `ADR-012` |
| MCP-002 | git_pull and git_push schema contradicts the protected-branch validation | open | Medium | MCP | implementation-bug | `scripts/mcp_servers/git/git_tools.py` | Unassigned | Documentation review | Schema allows an empty `branch`; validation rejects it | `mcp_04` |
| MCP-003 | cicd-mcp workflow_allowlist entries do not match the workflow value the tool receives | open | Medium | MCP | implementation-bug | `config/cicd_mcp_server.toml` | Unassigned | Documentation review | Allowlist holds `owner/repo/.github/workflows/ci.yml` but requests carry a file name | `mcp_05` |
| DEPLOY-001 | LLM service start procedure is not provided by any repository script | open | Medium | Deployment | operational-gap | `deploy/setup_services.sh` | Unassigned | Documentation review | No repository script starts `embed-llm`/`agent-llm` | `deployment_01` |
| EVENTBUS-008 | Consumer-role token without a consumer_id allowlist skips consumer-identity validation | open | Medium | EventBus | design-gap | `scripts/eventbus/auth.py` | Unassigned | ADR Known Deviations review | CONSUMER token without an allowlist is unrestricted (fail-open) | `ADR-013` |
| EVENTBUS-011 | NACK on a concurrently deleted event can return a misleading 409 | open | Low | EventBus | implementation-bug | `scripts/eventbus/ack_route.py` | Unassigned | ADR Known Deviations review | Concurrent delete during NACK yields 409 instead of 404 | `ADR-006` |
| EVENTBUS-012 | Duplicate NACK from the same consumer increments the failure counters on every call | open | Medium | EventBus | implementation-bug | `scripts/eventbus/delivery_repo.py` | Unassigned | Documentation review | No idempotency guard: repeated NACKs keep incrementing counters | `eventbus_05` |
| EVENTBUS-013 | ACK and NACK do not enforce Consumer ID exclusivity (ADR-006 INV-10) | open | Medium | EventBus | design-gap | `scripts/eventbus/ack_route.py` | Unassigned | Documentation review | `/ack` and `/nack` do not enforce Consumer ID exclusivity | `ADR-006`, `eventbus_05` |

#### DESIGN-001

- **ID**: DESIGN-001
- **Title**: ADR-002 Agent required-keys row lists keys absent from config/agent.toml
- **Status**: open
- **Severity**: Low
- **Area**: Governance
- **Type**: document-code-mismatch
- **Source**: `docs/10_adr/ADR-002-config-isolation.md`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/10_adr/ADR-002-config-isolation.md`
- **Related**: None
- **Summary**: The Agent row of the per-process key table names keys that `config/agent.toml` does not contain.
- **Current Description**: The other rows of the table were corrected against their files; the Agent row was not.
- **Observed Implementation**: About a dozen listed keys appear nowhere in `config/agent.toml` (for example `title_llm_temperature`, `security_profile`).
- **Impact**: A reader cannot tell which Agent keys are required, defaulted in code, or removed.
- **Recommended Action**: Check each key against the agent configuration builders and rewrite the row.
- **Resolution Target**: The Agent row matches `config/agent.toml` and the builders.

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
- **Current Description**: agent_03_03 labels the policy operational only and notes the default does not meet it.
- **Observed Implementation**: `WorkflowLoader` treats `require_approval` as optional (false when absent); `ProductionConfigValidator` has no rule for it.
- **Impact**: A default deployment runs those stages without a workflow-level approval gate (the tool-level gate is separate).
- **Recommended Action**: Either enforce the policy (validator rule and default definition) or reduce it to a recommendation.
- **Resolution Target**: Policy, default definition and validator agree.

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
- **Current Description**: mcp_04_05 describes the audit fields; ADR-012 expects write-enforcement decisions to be audited.
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
- **Current Description**: The schema describes an empty `branch` as the current or tracking branch.
- **Observed Implementation**: `GitService._validate_protected()` rejects an empty `branch` for checkout, pull and push.
- **Impact**: `git_pull`/`git_push` calls that rely on the schema default are rejected.
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
- **Current Description**: The configuration comment says "file names (e.g. ci.yml)", but its example and the checked-in value use a full path.
- **Observed Implementation**: `_assert_allowed_workflow()` tests `workflow not in allowlist`; tests use `ci.yml`.
- **Impact**: A call with `workflow="ci.yml"` is rejected with `CicdAuthorizationError` under the checked-in configuration.
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
- **Current Description**: The deployment document says `setup_services.sh` does not start the LLM services and gives no start procedure.
- **Observed Implementation**: `setup_services.sh` only echoes the service names and queries their health endpoints; its header comment says they are agent-managed subprocesses, but the agent starts only MCP servers.
- **Impact**: An operator has no documented way to start the LLM services the agent and RAG pipeline require.
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
- **Current Description**: ADR-013 states authentication is implemented; the consumer_id allowlist is the residual gap.
- **Observed Implementation**: `_populate_token_maps()` sets `allowed_consumer_ids` only when `consumer_authorization` or `topic_authorization` is configured; `require_consumer_identity()` skips validation when it is `None`. The shared and admin tokens are unrestricted by design.
- **Impact**: A holder of an unrestricted CONSUMER token can act under any consumer_id (ACK, NACK, offsets).
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
- **Current Description**: ADR-006 records the `(-2, -2)` result for ACKed or DLQ'd events and a residual race on deletion.
- **Observed Implementation**: `ack_route.py` re-reads `acked_at`/`dlq_at` in a separate `run_with_db_lock()` call; a missing row falls into the final `else` and raises 409 "invalid NACK transition".
- **Impact**: Low: an incorrect status code for one request.
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
- **Current Description**: The ACK/NACK documentation describes an ACK-then-NACK guard but none for a repeated NACK.
- **Observed Implementation**: `nack_event()` applies its `UPDATE` whenever `acked_at IS NULL AND dlq_at IS NULL`; there is no per-consumer NACK-state check.
- **Impact**: A duplicated NACK can promote an event to the DLQ earlier than the retry limit implies.
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
- **Current Description**: The delivery-semantics document states that ACK does not detect a collision.
- **Observed Implementation**: A second concurrent `/subscribe` gets 409 from the in-process broker registry; `/ack` and `/nack` check only the principal allowlist.
- **Impact**: Two callers sharing a `consumer_id` through ACK overwrite each other's delivery state and progress.
- **Recommended Action**: Bind ACK/NACK to the active subscription, or narrow INV-10 to the subscribe path; add a test.
- **Resolution Target**: INV-10 and the ACK path agree, covered by a test.

Other Known Issue IDs are not tracked here: a resolved or no-longer-applicable item is removed from this inventory.


## Part 2: Needs Confirmation Inventory

### Purpose

A centralized inventory of all "Needs confirmation" items found across the design documentation set. It makes unconfirmed statements trackable and actionable, preventing them from being silently accepted as facts.

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

A centralized inventory of all canonical source conflicts found across the design documentation set. It makes conflicting claims trackable and actionable, preventing them from being silently accepted as facts.

### Entry Template

Each active Canonical Source Conflict entry must contain these 12 fields: ID, Decision target, Claim type, Canonical source, Conflicting source or evidence, Conflict category, Impact, Severity (`High`/`Medium`/`Low`), Blocking status (`Blocking`/`Non-blocking`), Required action, Owner, Validation evidence.

### Status Values

- **open** — Conflict acknowledged but not yet investigated
- **investigating** — Investigation underway

An item is removed from this active inventory once it is resolved (exactly one normative source remains and validation evidence confirms the conflict is closed) or no longer applies to the current system; it is not retained here with a closed-out status.

### Lifecycle

Open → Investigating, or removed from this inventory once resolved or no longer applicable to the current system.

### Resolution Rule

Canonical Source Conflict resolved only when exactly one normative source remains registered.

### Evidence-Required Rule

Evidence is required before any discrepancy is reclassified or removed; a documentation-only edit cannot close a design-vs-code conflict unless required implementation evidence exists.

### Active Items

No other active Canonical Source Conflict items remain open.

## Part 4: Configuration Drift

### Purpose

A minimal inventory of discrepancies between deployed operational values and approved operational values. Tracks configuration drift that may affect behavior without changing the approved value.

### Entry Template

Each active Configuration Drift entry must contain these 6 fields: ID, Decision target, Deployed value description, Approved operational value description, Severity, Status.

### Status Values

- **open** — Drift acknowledged but not yet investigated
- **investigating** — Investigation underway

An item is removed from this active inventory once it is resolved (deployed and approved values agree, or the approved value has been formally changed) or no longer applies to the current system; it is not retained here with a closed-out status.

### Lifecycle

Same as the Lifecycle in Part 3: Open → Investigating, or removed from this inventory once resolved or no longer applicable to the current system.

### Resolution Rule

Configuration Drift resolved only when deployed and approved values agree, or approved value is formally changed.

### Evidence-Required Rule

Evidence is required before any discrepancy is reclassified or removed.

## Resolution Rules

The following resolution criteria apply across all four parts of this document:

- Known Issue resolved only when implementation and design agree, or design is formally changed
- Configuration Drift resolved only when deployed and approved values agree, or approved value is formally changed
- Needs Confirmation removed only after evidence establishes intent and the canonical source is updated
- Canonical Source Conflict resolved only when exactly one normative source remains registered
- Documentation correction complete only when validation shows no stale statement remains

## Temporary Exception Process

Applies to any automated check finding classified `Warning` (not `Blocking`) in
`docs/00_governance/governance_04_documentation-checks.md`'s Governance Verification Matrix
— for example, `GV-017`'s removed-name reintroduction findings. A `Warning`
finding does not block merge by itself, but leaving it neither fixed nor formally
excepted is not a complete review (see `docs/00_governance/governance_04_documentation-checks.md`
`### 19. Merge Condition Validation`).

### Exception Record Fields

A temporary exception must record all three of:
- **Reason**: why the finding is not being fixed now (e.g. the flagged usage is
  intentional and pending a separate follow-up issue).
- **Owner**: who accepted the exception — a specific person, not `Team` or
  `Unassigned`.
- **Expiration Date**: the date by which the exception must be re-reviewed or the
  underlying finding fixed. An exception with no expiration date is not valid.

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
