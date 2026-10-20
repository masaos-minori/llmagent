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
  - adr_02_06_010_rag-fallback.md
  - adr_02_06_005_rag-source-derived-index-relationships.md
  - adr_02_01_004_platform-environment-failure-handling-policy.md
  - adr_02_02_003_agent-runtime-tool-registry-routing-authority.md
  - mcp_03_01_dispatch-and-routing.md
  - agent_10_01_operations-and-observability-startup-and-health.md
  - agent_09_01_data-layer-session-db.md
  - agent_04_02_state-and-persistence-history-compression.md
  - agent_07_10_cli-and-commands-slash-commands-memory-other.md
  - adr_02_02_001_agent-workflow-engine-mandatory.md
  - adr_02_01_002_platform-config-isolation.md
  - agent_10_04_operations-and-observability-validation-and-troubleshooting.md
  - adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md
  - security_01_architecture-and-trust-boundaries.md
  - mcp_02_02_startup-modes-and-health.md
  - deployment_01_deployment.md
  - adr_02_04_013_eventbus-authentication-authorization.md
  - adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md
  - db_03_architecture_and_schema-migration-and-scaling.md
  - adr_02_05_008_db-sqlite-4db-separation.md
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

#### NC-041
- **ID:** NC-041
- **Source File:** `agent_08_04_configuration-mcp-approval-obs.md`
- **Section:** Component Criticality Classification, classification table, `github` row
- **Line Number:** 61
- **Question:** Whether `config/agent.toml` setting `[mcp_servers.github]` to `required = false` with `startup_mode = "none"` is an approved reclassification under ADR-004 Decision Group 3 item 13, or a deviation from the approved classification (`github` = required)
- **Evidence:** `config/agent.toml` `[mcp_servers.github]` sets `startup_mode = "none"` and `required = false` (commit `4e2442a75`, "disable the github MCP server until GITHUB_TOKEN is provisioned"); the classification table records `github` as required; ADR-004 Decision Group 3 item 13 states the `required` field in `config/agent.toml` must match the table and that configuration alone cannot weaken a mandatory component; no owner decision or table update accompanies the configuration change
- **Impact:** Until resolved, the classification table and the deployed configuration disagree for `github`, and it is unknown whether the Fail-Closed handling of a disabled `github-mcp` has been assessed against Decision Group 3 item 10
- **Required Action:** Record an owner decision: either update the classification table for `github` (with the item 10 assessment) or restore `required = true` when `GITHUB_TOKEN` is provisioned
- **Status:** open
- **Assigned To:** Unknown
- **Last Reviewed:** 2026-10-20
- **Priority:** Medium
- **Related NC:** None
- **Resolution Target:** Owner decision on the `github` classification; classification table and `config/agent.toml` agree
- **Blocking:**

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
