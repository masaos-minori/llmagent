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
| AGENT-006 | Secret masking of MCP subprocess output recognizes only key=value forms | open | Medium | Agent | design-gap |
| AGENT-008 | /undo after a compressed session reload can undo fewer turns than expected | open | Low | Agent | design-gap |
| AGENT-009 | /skill messages lose the _ephemeral marker during append validation | open | Low | Agent | design-gap |
| MCP-001 | The shell, github, and file MCP servers register no Bearer-token authentication middleware | open | High | MCP | implementation-bug |
| EVENTBUS-008 | Consumer-role token is unrestricted when the authorization mappings are empty | open | Medium | EventBus | design-gap |
| EVENTBUS-017 | No runtime component uses the EventBus although ADR-008 INV-07 relies on Events for cross-DB consistency | open | Medium | EventBus | design-gap |

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
- **Resolution Target**: The undo range after compression is defined and tested, or the limitation is recorded as accepted.

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
- **Resolution Target**: Skill messages are cleared by one defined mechanism, with a test, or the behavior is recorded as accepted.

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
