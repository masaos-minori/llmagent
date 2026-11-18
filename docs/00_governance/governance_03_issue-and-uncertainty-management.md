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

#### MCP-001

- **ID:** MCP-001
- **Title:** ADR-004 overlay-only fail-open exception has no maintainer approval reference
- **Status**: open
- **Severity:** Medium
- **Area:** MCP
- **Type:** missing-documentation
- **Source:** `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` `## Exceptions`, retryable fail-open bullet
- **Owner:** Repository owner
- **First Found:** adrchk011 ADR approval governance re-verification
- **Target:** `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`
- **Related:** None
- **Summary:** For a retryable tool whose dedup store is unavailable, lost, or recreated, the shared MCP dispatcher proceeds overlay-only with a `store_error` marker instead of failing closed, and the ADR records no maintainer approval for this exception.
- **Current Description:** ADR-004 `## Exceptions` states a rationale and leaves the approval to a maintainer; the exception was added after the task-level approvals in `### Approval Record`, so none covers it.
- **Observed Implementation:** `scripts/mcp_servers/dispatch.py` degrades to the overlay when the durable store is unavailable, as the ADR describes.
- **Impact:** A relaxation of fail-closed handling stands without an approval record.
- **Recommended Action:** The maintainer states the approval and the ADR records it, or the exception is removed; no approval is written here.
- **Resolution Target:** maintainer approval in the ADR-004 `### Approval Record`, or removal of the exception

#### MCP-002

- **ID:** MCP-002
- **Title:** ADR-004 post-open warning-only exception has no maintainer approval reference
- **Status**: open
- **Severity:** Medium
- **Area:** MCP
- **Type:** missing-documentation
- **Source:** `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` `## Exceptions`, post-open write-failure bullet
- **Owner:** Repository owner
- **First Found:** adrchk011 ADR approval governance re-verification
- **Target:** `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`
- **Related:** MCP-001
- **Summary:** For a retryable tool, a failed dedup store write after a successful open is warning-only instead of fail-closed, and the ADR records no maintainer approval for this exception.
- **Current Description:** ADR-004 `## Exceptions` states a rationale and leaves the approval to a maintainer; the exception was added after the task-level approvals in `### Approval Record`, so none covers it.
- **Observed Implementation:** `scripts/shared/mcp_dedup.py` `_write()` and `scripts/mcp_servers/dispatch.py` `_store_op` degrade a failed write to the overlay, as the ADR describes.
- **Impact:** A relaxation of fail-closed handling stands without an approval record.
- **Recommended Action:** The maintainer states the approval and the ADR records it, or the exception is removed; no approval is written here.
- **Resolution Target:** maintainer approval in the ADR-004 `### Approval Record`, or removal of the exception

#### SHARED-001

- **ID:** SHARED-001
- **Title:** Dry Run switches a rollback-journal-mode target database to WAL mode on open
- **Status**: open
- **Severity:** Low
- **Area:** Shared/DB
- **Type:** implementation-bug
- **Source:** `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` Automated Tests INV-16 row and `tests/db/test_db_recovery.py` rollback-journal clause
- **Owner:** Repository owner
- **First Found:** adrrev009 ADR-008 recovery alignment review
- **Target:** `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`
- **Related:** `plans/20261110-233648_adrrev009_adr008-recovery-align.md`
- **Summary:** The Dry Run path opens the target DB connection to classify its condition, which converts a rollback-journal-mode database to WAL mode; ADR-008 documents Dry Run as taking no action on the target DB, which does not cover this journal-mode switch.
- **Current Description:** ADR-008 Automated Tests INV-16 states "a rollback-journal file is switched to WAL when opened and is not covered" while the ADR's `## Known Deviations` reads "Not applicable", so the deviation is neither recorded nor resolved.
- **Observed Implementation:** `scripts/db/recovery.py` Dry Run path opens the target connection for classification; SQLite rewrites a rollback-journal-mode file to WAL mode on open.
- **Impact:** A rollback-journal-mode database is silently converted to WAL mode during a Dry Run. Operational impact is low because WAL is the production mode, but it contradicts the documented "no action on the target DB" claim and is currently unrecorded.
- **Recommended Action:** Maintainer decides either (a) fix Dry Run so it does not alter the target's journal mode (for example a read-only classification that avoids the conversion), or (b) accept the switch and record it as an explicit Known Deviation in ADR-008. Recorded here pending that decision; no code fix or approval is fabricated.
- **Resolution Target:** maintainer decision recorded in ADR-008 `## Known Deviations` or a Dry Run code fix

#### SHARED-002

- **ID:** SHARED-002
- **Title:** `memories_vec` is classified as both system of record and derived/rebuildable in ADR-008
- **Status**: open
- **Severity:** Medium
- **Area:** Shared/DB
- **Type:** document-document-mismatch
- **Source:** `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` Recovery Policy Matrix rows "System of record" and "Derived or rebuildable data"
- **Owner:** Repository owner
- **First Found:** adrrev009 ADR-008 recovery alignment review
- **Target:** `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`
- **Related:** `plans/20261110-233648_adrrev009_adr008-recovery-align.md`
- **Summary:** The session.sqlite column of ADR-008's Recovery Policy Matrix lists `memories_vec` under "System of record" and again under "Derived or rebuildable data (from memories)", classifying one store two mutually exclusive ways.
- **Current Description:** Line 92 lists `sessions, messages, memories, memories_vec` as the system of record and line 93 lists `memories_vec (from memories)` as derived/rebuildable data for the same store in the same table.
- **Observed Implementation:** No component treats `memories_vec` as a canonical store independent of `memories`; it is rebuilt from `memories`, which supports the derived classification, but the matrix still lists it as a system of record.
- **Impact:** An operator cannot determine the recovery policy for `memories_vec`; a store cannot be both canonical and derived, so the matrix is internally contradictory.
- **Recommended Action:** Maintainer decides the correct classification (system of record versus derived/rebuildable) and edits the matrix accordingly. Recorded here pending that decision; the classification is not resolved by this Plan.
- **Resolution Target:** maintainer decision reflected in the ADR-008 Recovery Policy Matrix

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

### Blocking Values

- **An NC id** — The Needs Confirmation item that this entry blocks
- **None** — Assessed; this entry blocks no other item
- **Empty** — Not yet assessed for blocking

The Part 3 `Blocking` / `Non-blocking` vocabulary does not apply to this field.

### Extraction Process

Search `docs/` for "Needs confirmation", populate fields from context, add sequential ID, never modify source documents.

### Active Items

#### NC-001

- **ID:** NC-001
- **Source File:** `adr_02_01_004_platform-environment-failure-handling-policy.md`
- **Section:** Decision > Group 1 (Registered exception, empty `path_denylist`)
- **Line Number:** 67
- **Question:** Why is an empty `path_denylist` on the GitHub server permitted as the only empty-safety-list relaxation when every other boundary control is fail-closed?
- **Evidence:** The ADR-004 Group 1 exception record (PENDING placeholder); `config/github_mcp_server.toml` ships `path_denylist = []`; config build accepts it while `allowed_root` and `protected_branches` are rejected when empty.
- **Impact:** A maintainer-declared exception without a written rationale weakens the ADR's auditability; the exception stands until the rationale is supplied or the exception is removed.
- **Required Action:** The maintainer writes the rationale into the ADR-004 Group 1 exception record; the implementer does not write it. Remove the inline marker only when the rationale text is supplied.
- **Status:** open
- **Assigned To:** maintainer
- **Last Reviewed:** 2026-11-10
- **Priority:** High
- **Related NC:** None
- **Resolution Target:** rationale text in the ADR-004 Group 1 exception record
- **Blocking:** None

#### NC-002

- **ID:** NC-002
- **Source File:** `adr_02_01_004_platform-environment-failure-handling-policy.md`
- **Section:** Decision > Group 2 (item 7, RAG derived-index results)
- **Line Number:** 73
- **Question:** Can every function that the RAG derived-index results affect be safely disabled while the RAG search path stays available, as Decision Group 2 item 8 requires for continuing startup after an availability failure?
- **Evidence:** The startup check reports Degraded findings, a failed check, and a timed-out check as warnings and startup continues; the RAG search path is not disabled on those results.
- **Impact:** The conditions of item 8 are not shown to hold for the classification of these results as availability failures.
- **Required Action:** The maintainer writes the justification into ADR-004 Decision Group 2 item 7 or reverses the classification; the implementer does not write it. Remove the inline marker only when the justification text is supplied.
- **Status:** open
- **Assigned To:** maintainer
- **Last Reviewed:** 2026-11-18
- **Priority:** High
- **Related NC:** None
- **Resolution Target:** justification text in ADR-004 Decision Group 2 item 7
- **Blocking:** None

## Part 3: Canonical Source Conflict

### Purpose

An inventory of active canonical source conflicts, so conflicting claims are tracked rather than silently accepted.

### Entry Template

Each active Canonical Source Conflict entry must contain these 13 fields: ID, Decision target, Claim type, Canonical source, Conflicting source or evidence, Conflict category, Impact, Severity (`High`/`Medium`/`Low`), Blocking status (`Blocking`/`Non-blocking`), Required action, Owner, Validation evidence, Status.

### Status Values

- **open** — Conflict acknowledged but not yet investigated
- **investigating** — Investigation underway

An item is removed from this active inventory once it is resolved (exactly one normative source remains and validation evidence confirms the conflict is closed) or no longer applies to the current system; it is not retained here with a closed-out status.

### Active Items

#### CSC-001

- **ID:** CSC-001
- **Decision target:** Acceptance of a RAG fallback result under an unverifiable corpus identity
- **Claim type:** Present-behavior claim retained in a Withdrawn ADR
- **Canonical source:** `docs/10_adr/adr_02_06_010_rag-fallback.md` `## Status` (`Withdrawn`) and its withdrawal note ("The text below remains as the record of the withdrawn decision")
- **Conflicting source or evidence:** The same ADR's Decision item 11 and the failure-outcome table row `Identity unverifiable (either identity absent)` still state the identity-comparison and unverifiable-handling contract in the present tense
- **Conflict category:** Internal contradiction in one canonical source: withdrawn status vs surviving normative wording
- **Impact:** Readers of the normative sections can take the withdrawn fallback's identity handling as current behavior although the corpus-identity handling no longer exists
- **Severity:** High
- **Blocking status:** Blocking
- **Required action:** The corpus-identity modules are gone: no `corpus_identity.py` exists under `scripts/rag/` and no `scripts/` or `tests/` file references it. The surviving present-tense wording in ADR-010 (Decision item 11 and the failure-outcome table row) is still to be moved to the withdrawn record or removed, a maintainer decision
- **Owner:** Repository owner
- **Validation evidence:** `rg corpus_identity scripts/ tests/` lists no file
- **Status**: open

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

## Part 5: ADR Approval Ledger

### Purpose

A register of ADR decision-text changes that are written into an ADR but still await the maintainer's approval, so pending approvals are tracked and cited instead of being treated as approved.

### Entry Fields

Each entry MUST contain these six fields: ID, ADR, Decision, Approver, Date, Scope.

### Rules

- An entry ID is `AAL-NNN` (three digits, ascending). An ADR's `Current Decision Approval (pending)` bullet MUST cite its entry ID, and every cited ID MUST have an entry here (`tools/check_adr_structure.py`).
- Approver and Date stay `Not recorded` until the maintainer states them. An implementer MUST NOT write approval text or an entry for a past approval.
- An entry is removed once its approval is recorded in the ADR's `### Approval Record` or the pending change is reverted.

### Active Items

#### AAL-001

- **ID:** AAL-001
- **ADR:** ADR-001
- **Decision:** INV-02 verification row set to Non-Blocking
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** INV-02 verification row

#### AAL-002

- **ID:** AAL-002
- **ADR:** ADR-004
- **Decision:** Decision Group 10 amendment (fallback prohibited without exception)
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** Decision Group 10

#### AAL-003

- **ID:** AAL-003
- **ADR:** ADR-004
- **Decision:** INV-14 verification text citing the startup-abort and registry tests
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** INV-14 verification text

#### AAL-004

- **ID:** AAL-004
- **ADR:** ADR-005
- **Decision:** Decision 10 remediation, Decision 11 helper sentence, startup-check bullet reword
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** Decisions 10 and 11, Fail-Open or Degraded Conditions

#### AAL-005

- **ID:** AAL-005
- **ADR:** ADR-005
- **Decision:** Decision 8 and the `rebuild_fts()` note reference ADR-009
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** Decision 8, Implementation Notes

#### AAL-006

- **ID:** AAL-006
- **ADR:** ADR-006
- **Decision:** `dlq_outbox` promotion record added to Scope and Data Ownership
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** Scope, Data Ownership

#### AAL-007

- **ID:** AAL-007
- **ADR:** ADR-006
- **Decision:** Replay Contract (`/replay` Operator-only, `/subscribe` start order)
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** Replay Contract

#### AAL-008

- **ID:** AAL-008
- **ADR:** ADR-006
- **Decision:** INV-13 wording, INV-04, INV-06, and INV-07 verification re-mapping, requeue error text
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** INV-04, INV-06, INV-07, INV-13

#### AAL-009

- **ID:** AAL-009
- **ADR:** ADR-006
- **Decision:** ADR-008 added to related ADRs; INV-15 states ADR-006 owns loopback binding
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** Front matter `related`, Related ADRs, INV-15

#### AAL-010

- **ID:** AAL-010
- **ADR:** ADR-008
- **Decision:** `dlq_outbox` named among the `eventbus.sqlite` contents
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** Decision Detail 4

#### AAL-011

- **ID:** AAL-011
- **ADR:** ADR-008
- **Decision:** `rag-pipeline-mcp` appended to the Target components
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** Target components

#### AAL-012

- **ID:** AAL-012
- **ADR:** ADR-009
- **Decision:** INV-09 folded into INV-04; Failure Conditions relabel and reword
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** INV-04, INV-09, Failure Conditions

#### AAL-013

- **ID:** AAL-013
- **ADR:** ADR-010
- **Decision:** Withdrawal of the fallback decision
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** Status, Withdrawal Approval Record

#### AAL-014

- **ID:** AAL-014
- **ADR:** ADR-012
- **Decision:** Safe exception (`dry_run`) and Detached HEAD policy
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** Decision Detail 5

#### AAL-015

- **ID:** AAL-015
- **ADR:** ADR-012
- **Decision:** Stages 1 to 3 (path validation, write guard, authorization)
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** Decision Detail 9

#### AAL-016

- **ID:** AAL-016
- **ADR:** ADR-014
- **Decision:** INV-02 names the Orchestrator as the single creator of the turn executor
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** INV-02

#### AAL-017

- **ID:** AAL-017
- **ADR:** ADR-015
- **Decision:** Manifest status correction; `agent_08_04` added to the generated-document list
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** Manifest status, generated-document list

#### AAL-018

- **ID:** AAL-018
- **ADR:** ADR-016
- **Decision:** Index section renamed to ADR Dependency Graph; pair count updated
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** Decision Detail 6, Implementation Notes, Summary, Problem

#### AAL-019

- **ID:** AAL-019
- **ADR:** ADR-004
- **Decision:** RAG derived-index results classified as availability failures
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** Decision Group 2 item 7

#### AAL-020

- **ID:** AAL-020
- **ADR:** ADR-005
- **Decision:** The startup classification of the consistency check results is owned by ADR-004
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** Fail-Open or Degraded Conditions

#### AAL-021

- **ID:** AAL-021
- **ADR:** ADR-003
- **Decision:** Drift validation aborts startup (severity wording of Decision Detail #15 corrected)
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** Decision Detail #15

#### AAL-022

- **ID:** AAL-022
- **ADR:** ADR-003
- **Decision:** Security Posture exclusion from RuntimeToolRegistry and its startup consequence
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** Decision Detail #16

#### AAL-023

- **ID:** AAL-023
- **ADR:** ADR-003
- **Decision:** Dynamic health hints are advisory error metadata
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** Decision Detail #17

#### AAL-024

- **ID:** AAL-024
- **ADR:** ADR-008
- **Decision:** Scope widened to six databases (title, Summary, Scope, Recovery Policy Matrix)
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** Title, Summary, Scope, Recovery Policy Matrix

#### AAL-025

- **ID:** AAL-025
- **ADR:** ADR-008
- **Decision:** Schema-mismatch rule: every database is archived and recreated, with per-database preconditions
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** Decision Detail 22

#### AAL-026

- **ID:** AAL-026
- **ADR:** ADR-008
- **Decision:** Retention rule per database; EventBus events, consumer_delivery, and dlq_outbox growth is an accepted risk
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** Decision Detail 23, INV-09

#### AAL-027

- **ID:** AAL-027
- **ADR:** ADR-008
- **Decision:** Memory canonical store: memories and memory_links canonical, memories_fts and memories_vec derived, JSONL append-only archive
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** Decision Detail 24, Recovery Policy Matrix

#### AAL-028

- **ID:** AAL-028
- **ADR:** ADR-008
- **Decision:** INV-04 names the dlq_outbox durable promotion record
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** INV-04

#### AAL-029

- **ID:** AAL-029
- **ADR:** ADR-006
- **Decision:** No-loss statements hold under the ADR-008 schema-mismatch rule; EventBus retention is an accepted risk
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** Decision Detail 9, INV-07, Data Ownership

#### AAL-030

- **ID:** AAL-030
- **ADR:** ADR-002
- **Decision:** INV-04 amendment proposal: config files carry no MCP-server-owned settings; the only MCP-specific value given to the Agent is each enabled server's connection token supplied through ADR-017's environment-variable mechanism, and an enabled server resolving to an empty token aborts startup per ADR-017
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** INV-04

## Resolution Rules

The following resolution criteria apply across the parts of this document:

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
`### 20. Merge Condition Validation`).

### Exception Record Fields

A temporary exception records a **Reason** (why the finding is not fixed now), an **Owner** (the person who accepted it; not `Team` or `Unassigned`) and an **Expiration Date** (when it must be re-reviewed or fixed; an exception without one is not valid).

### Recording an Exception

Record the exception inline, next to the flagged line, as:

`<!-- exception: {rule-id} — {reason} — {owner} — expires {YYYY-MM-DD} -->`

An exception past its expiration date is treated as an unexplained finding (see
`docs/00_governance/governance_04_documentation-checks.md`
`### 20. Merge Condition Validation`) — not as still-covered.

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
