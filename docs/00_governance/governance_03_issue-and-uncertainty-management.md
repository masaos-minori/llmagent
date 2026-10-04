---
title: "Issue and Uncertainty Management"
area: governance
tags:
  - governance
related:
  - ../00_index.md
  - ../01_overview/overview_00_document-guide.md
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

### Consolidation Note

The area-specific `~~rag_90_inconsistencies_and_known_issues~~ (deleted).md`,
`~~mcp_90_inconsistencies_and_known_issues~~ (deleted).md`,
`~~agent_90_inconsistencies_and_known_issues~~ (deleted).md`,
`~~eventbus_90_inconsistencies_and_known_issues~~ (deleted).md`, and
`~~shared_90_inconsistencies_and_known_issues~~ (deleted).md` files were consolidated into this
section on 2026-09-03 and deleted; this document is now the single system of record
for Known Issues across all areas. Existing IDs were preserved as-is (`RAG-*`,
`EVENTBUS-*`, `SHARED-*`, `CI-*`, `DESIGN-*`); one previously untitled RAG entry was
assigned a new ID (`RAG-005`) since the 16-field template requires one. EventBus
entries used a distinct 18-field format with no direct equivalent for `Component`,
`Workaround`, or the `*-Justification` fields — these were folded into `Source`,
`Recommended Action`, and `Current Description`/`Resolution Notes` respectively, per
this template. `CI-*` entries (originally filed under Shared/DB regardless of actual
subject) were re-assigned to the Area their cited ADR/Decision actually concerns,
since several concern RAG, MCP, or Agent behavior rather than Shared/DB.

Two non-Known-Issue notes from the deleted files, with no active items depending on
them, are preserved here rather than lost:

- **Agent 5-Tier Scheme (historical, superseded by this consolidation):** `agent_90`'s design intent
  had, for Agent-area entries only, used a 5-tier classification (Design Decision /
  Implementation Bug / Documentation Gap / Needs Confirmation / Operational
  Observation) as a documented exception to this document's common template,
  reasoning that the common Status/Type fields conflate "accepted design choice"
  with "acknowledged bug awaiting fix." At the time of this consolidation the
  Agent-area file had zero open entries. This consolidation ends that exception —
  all areas, including Agent, now use only this document's common template — since
  a per-area exception has no purpose once there is only one canonical inventory.
- **EventBus schema/implementation note (informational, no issue):** `06_eventbus_90` recorded that
  `acked_at`, `delivery_failure_count`, `dlq_requeue_count`, and `dlq_at` are all
  documented in the schema and all in active use, with no discrepancy — retained
  here only because the source file no longer exists to hold it.

### Active Items

Active Items follow an ordering convention: entries are grouped by ID-prefix (RAG-*, DESIGN-*, EVENTBUS-*, SHARED-*, CI-*), each group's entries in ascending numeric order.

| ID | Title | Status | Severity | Area | Type | Source | Owner | First Found | Summary | Related |
|----|-------|--------|----------|------|------|--------|-------|-------------|---------|---------|

No active Known Issue items remain.


**Removal-placeholder-reference policy**: A `Related`/`Target` field may cite a removed entry's ID only when a removal-placeholder paragraph exists for that ID; without such a placeholder, the citation is treated as a dangling reference (Warning severity if the placeholder exists but no heading, Blocking if neither exists).


**EventBus-specific verification (REQ-006)**: Verified by configuration test confirming `ConfigMissingError` is raised when a required config file is missing. The EventBus `load_config()` function (`scripts/eventbus/config.py`) validates required keys via `_REQUIRED_CONFIG_KEYS` and raises `ValueError` for missing keys — consistent with the fail-closed behavior described in CI-005.

Note on CI-014 batching: These "ADR invariant verified by code inspection, no automated test" entries formed one cross-cutting initiative of originally nine members. All nine have since been removed once test coverage was added (CI-008, CI-009, CI-010, CI-011, CI-012, CI-013, CI-014, CI-015, and CI-016); no active members remain. Their Area fields spanned Agent, Shared/DB, MCP, RAG, and EventBus, so no single existing RACI role was accountable for the cross-area ADR-invariant-test-suite initiative. This finding is recorded here; the cross-cutting-role vs. per-area-ownership decision stays open for any future similar initiative.

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
- **resolved** — Exactly one normative source remains; validation evidence confirms the conflict is closed

An item is removed from this active inventory once it is resolved or no longer applies to the current system; it is not retained here with a closed-out status.

### Lifecycle

Open → Investigating → Resolved, or removed from this inventory once resolved or no longer applicable to the current system.

### Resolution Rule

Canonical Source Conflict resolved only when exactly one normative source remains registered.

### Evidence-Required Rule

Evidence is required before any discrepancy is reclassified or removed; a documentation-only edit cannot close a design-vs-code conflict unless required implementation evidence exists.

### Current-Specification-Only Policy Reference

Resolved-item handling for Canonical Source Conflict follows the existing Current-Specification-Only Policy: resolved entries are removed from the active inventory, not retained with a closed-out status.

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
- **resolved** — Deployed and approved values agree, or the approved value has been formally changed

An item is removed from this active inventory once it is resolved or no longer applies to the current system; it is not retained here with a closed-out status.

### Lifecycle

Open → Investigating → Resolved, or removed from this inventory once resolved or no longer applicable to the current system.

### Resolution Rule

Configuration Drift resolved only when deployed and approved values agree, or approved value is formally changed.

### Evidence-Required Rule

Evidence is required before any discrepancy is reclassified or removed.

### Current-Specification-Only Policy Reference

Resolved-item handling for Configuration Drift follows the existing Current-Specification-Only Policy: resolved entries are removed from the active inventory, not retained with a closed-out status.

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
— for example, `GV-020`'s removed-name reintroduction findings. A `Warning`
finding does not block merge by itself, but leaving it neither fixed nor formally
excepted is not a complete review (see `docs/00_governance/governance_04_documentation-checks.md`
`### 13. Merge Condition Validation`).

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

For example: `<!-- exception: GV-020 — read_json_file mention is a historical
comparison, not a current-spec claim — @agent-lead — expires 2026-12-01 -->`

An exception past its expiration date is treated as an unexplained finding (see
`docs/00_governance/governance_04_documentation-checks.md`
`### 13. Merge Condition Validation`) — not as still-covered.

## Non-Goals

Topics explicitly excluded from this document:

- Resolving individual items — resolution requires separate investigation
- Modifying source documents during extraction — this document is read-only relative to sources
- Defining new evidence labels beyond those already established
- Changing the common template itself

## Related Documents

Cross-cutting documentation rules and policies:

- [Documentation Overview](../00_index.md)
- [System Overview Index](../01_overview/overview_00_document-guide.md)

## Keywords

known issues
needs confirmation
inconsistencies
template
evidence labels
resolution workflow
