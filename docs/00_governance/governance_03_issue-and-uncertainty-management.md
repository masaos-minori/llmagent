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

Active Items follow an ordering convention: entries are grouped by ID-prefix (RAG-*, DESIGN-*, EVENTBUS-*, SHARED-*, CI-*), each group's entries in ascending numeric order.

| ID | Title | Status | Severity | Area | Type | Source | Owner | First Found | Summary | Related |
|----|-------|--------|----------|------|------|--------|-------|-------------|---------|---------|
| EVENTBUS-008 | Consumer-role token without a consumer_id allowlist skips consumer-identity validation | open | Medium | EventBus | design-gap | `scripts/eventbus/auth.py` | Unassigned | ADR Known Deviations review | A CONSUMER-role token with no `consumer_authorization`/`topic_authorization` configured is not restricted to any consumer_id (fail-open) | `docs/10_adr/ADR-013-eventbus-authentication-authorization.md` |
| EVENTBUS-011 | NACK on a concurrently deleted event can return a misleading 409 | open | Low | EventBus | implementation-bug | `scripts/eventbus/ack_route.py` | Unassigned | ADR Known Deviations review | `_nack_and_promote()` and the follow-up state lookup run under separate DB-lock acquisitions, so an event deleted in between yields 409 instead of 404 | `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` |
| EVENTBUS-012 | Duplicate NACK from the same consumer increments the failure counters on every call | open | Medium | EventBus | implementation-bug | `scripts/eventbus/delivery_repo.py` | Unassigned | Documentation review | `nack_event()` has no idempotency guard for repeated NACKs of the same event by the same consumer, so repeated calls can drive the event toward DLQ promotion | `docs/24_eventbus/eventbus_06_dlq_offsets_and_delivery_semantics.md` |

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
- **Summary**: Bearer-token authentication and role-based authorization are implemented, but consumer-identity validation is fail-open for a token that has no consumer_id allowlist.
- **Current Description**: The ADR set states that the EventBus authentication model is implemented (public bind is rejected by `EventBusConfig.__post_init__()`; Bearer-token authentication and role checks are attached in `scripts/eventbus/app.py`). The residual gap recorded under ADR-013 is the consumer_id allowlist: when no allowlist applies to the calling token, the consumer_id supplied by the caller is accepted as-is.
- **Observed Implementation**: In `scripts/eventbus/auth.py`, `_populate_token_maps()` sets `allowed_consumer_ids` only on the CONSUMER-role token, and only when `consumer_authorization` or `topic_authorization` is configured; otherwise it is `None`. `require_consumer_identity()` raises 403 only when `allowed_consumer_ids is not None` and the consumer_id is absent from it, so `None` skips validation. The shared `auth_token` and `admin_token` are unrestricted by design.
- **Impact**: A holder of an unrestricted CONSUMER token can act under any consumer_id (ACK, NACK, offset operations), which weakens per-consumer isolation within the same-host trust boundary.
- **Recommended Action**: Decide whether a CONSUMER-role token with no allowlist should be rejected (fail-closed) or whether the unrestricted behavior is the accepted contract; then align `scripts/eventbus/auth.py` or ADR-013 accordingly.
- **Resolution Target**: Implementation and ADR-013 agree on the behavior for a CONSUMER-role token without an allowlist.

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
- **Summary**: When an event is deleted between the NACK call and the follow-up state lookup, the route raises 409 "invalid NACK transition" instead of 404.
- **Current Description**: ADR-006 records that `nack_event()` returns `(-2, -2)` for events already ACKed or DLQ'd and that the route converts this to HTTP 409, with a residual race when the event is deleted between the NACK call and the status check.
- **Observed Implementation**: `nack_event()` in `scripts/eventbus/delivery_repo.py` returns `(-2, -2)` only when the row still exists. In `scripts/eventbus/ack_route.py`, the `failure_count == -2` branch re-reads `acked_at`/`dlq_at` in a separate `run_with_db_lock()` call; if the row is gone, the final `else` raises 409 "invalid NACK transition" rather than 404.
- **Impact**: Low. Events are deleted only in rare cases; the effect is an incorrect status code for one request.
- **Recommended Action**: Treat a missing row in the follow-up lookup as 404 (event not found), or perform the NACK and the state lookup under one lock acquisition.
- **Resolution Target**: A NACK on an event deleted concurrently returns 404, covered by a test.

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
- **Target**: `docs/24_eventbus/eventbus_06_dlq_offsets_and_delivery_semantics.md`
- **Related**: None
- **Summary**: A NACK of an event that is neither ACKed nor in the DLQ always increments `delivery_failure_count` and `cycle_failure_count`, even when the same consumer already NACKed it.
- **Current Description**: The ACK/NACK documentation describes an ACK-then-NACK guard (HTTP 409) but no equivalent guard for a repeated NACK.
- **Observed Implementation**: `nack_event()` in `scripts/eventbus/delivery_repo.py` applies its `UPDATE` whenever `acked_at IS NULL AND dlq_at IS NULL` (plus the per-consumer ACK guard when `consumer_id` is given). No per-consumer NACK-state check exists, so each call increments the counters.
- **Impact**: A retried or duplicated NACK request can inflate the failure count and promote an event to the DLQ earlier than the configured retry limit implies.
- **Recommended Action**: Decide whether NACK must be idempotent per consumer; if so, add a per-consumer guard in `nack_event()` and align the ACK/NACK documentation.
- **Resolution Target**: Repeated NACKs from the same consumer for the same delivery attempt do not change the counters again, covered by a test.

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

An item is removed from this active inventory once it is resolved (deployed and approved values agree, or the approved value has been formally changed) or no longer applies to the current system; it is not retained here with a closed-out status.

### Lifecycle

Same as the Lifecycle in Part 3: Open → Investigating, or removed from this inventory once resolved or no longer applicable to the current system.

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

## Keywords

known issues
needs confirmation
inconsistencies
template
evidence labels
resolution workflow
