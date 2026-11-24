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

#### MCP-003

- **ID:** MCP-003
- **Title:** component-mandatoriness registry `failure_category` is uniformly `safety-integrity` while ADR-004 Decision Group 2 item 7 lists MCP server unavailability among availability failures
- **Status**: open
- **Severity:** Medium
- **Area:** MCP
- **Type:** design-gap
- **Source:** `registry/component_mandatoriness.yaml` `failure_category` lines of the 10 entries and ADR-004 Decision Group 2 item 7
- **Owner:** Repository owner
- **First Found:** adrchk020 mandatoriness registry posture re-verification
- **Target:** `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`
- **Related:** AAL-019, `registry/component_mandatoriness.yaml`
- **Summary:** All 10 registry entries carry `failure_category: safety-integrity`, while ADR-004 Decision Group 2 item 7 lists unavailability of an MCP server among availability failures; whether the field should follow item 7 has no recorded decision.
- **Current Description:** ADR-004 Decision Group 7 records the repository owner instruction of 2026-11-10 (option B) that every registry component is classified `required`, and the registry rationale cites it; item 10's criteria decide only a non-mandatory classification (item 12 forbids assuming one). The `failure_category` values were not part of that instruction.
- **Observed Implementation:** every server is classified `required` with `startup_consequence: abort_startup` and `failure_category: safety-integrity`; the startup outcome is abort either way (item 8), so the field affects classification wording, not behavior. Item 7's own classification of RAG derived-index results awaits approval as AAL-019.
- **Impact:** the category of an MCP server's unavailability may be read two ways (safety/integrity versus availability) with no recorded decision; no startup behavior depends on it.
- **Recommended Action:** the maintainer states whether `failure_category` stays uniform `safety-integrity` or follows ADR-004 Group 2 item 7 (`docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md:73`); recorded pending that decision, no value changes here and no approval is written.
- **Resolution Target:** maintainer decision on `failure_category` recorded in the registry via an approved change

#### MCP-004

- **ID:** MCP-004
- **Title:** component-mandatoriness registry authority/placement reconciliation has no ledger entry
- **Status**: open
- **Severity:** Low
- **Area:** MCP
- **Type:** design-gap
- **Source:** the former header note in `registry/component_mandatoriness.yaml` (line 6, "Authority/placement reconciliation pending adrauth001 (U-1)")
- **Owner:** Repository owner
- **First Found:** adrchk020 mandatoriness registry posture re-verification
- **Target:** `docs/00_governance/governance_01_documentation-policy.md`
- **Related:** MCP-003, `config/documentation_canonical_sources.toml`
- **Summary:** The registry is registered under claim type `security-policy` in `config/documentation_canonical_sources.toml`, while the governance_01 `security-policy` row names only Accepted security ADRs as its canonical source kind; the choice of how to reconcile them has no recorded decision.
- **Current Description:** the registry home is fixed by ADR-004 item 13 and `config/documentation_canonical_sources.toml:66-71` registers `registry/component_mandatoriness.yaml` as the source for `mcp.component-mandatoriness`.
- **Observed Implementation:** the governance_01 `### Resolution Matrix` is a table by claim type with no owner column and no per-decision-target rows, so no owner list exists to approve; `tools/check_canonical_source_registry.py` accepts the current registration.
- **Impact:** the registry's authority is described differently by the canonical-source registry and the policy matrix; no checker or runtime behavior depends on the difference.
- **Recommended Action:** the maintainer chooses between naming the registry in the governance_01 `security-policy` canonical source kind and changing the registry's `claim_type` in `config/documentation_canonical_sources.toml`; recorded pending that decision, no approval is written here.
- **Resolution Target:** the chosen reconciliation recorded in `governance_01_documentation-policy.md` or `config/documentation_canonical_sources.toml`

#### MCP-005

- **ID:** MCP-005
- **Title:** git_add/git_commit HEAD-destination protected-branch check is mandated by no Invariant
- **Status**: open
- **Severity:** Medium
- **Area:** MCP
- **Type:** design-gap
- **Source:** adrchk021 ADR editorial defect re-verification, ADR-012 `## Known Deviations` gap scan
- **Owner:** Repository owner
- **First Found:** adrchk021 ADR editorial defect re-verification
- **Target:** `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`
- **Related:** None
- **Summary:** `verify_authorization()` evaluates the protected-branch decision against the operation destination and protects the current HEAD for `git_add`/`git_commit`, but no Invariant mandates this; regression tests for those two tools now exist (`TestHeadDestinationProtection` in `tests/mcp_servers/git/test_repository_state.py`).
- **Current Description:** ADR-012 INV-03 names only `git_checkout`/`git_pull`/`git_push`; the Scope section describes the destination-based protection without an Invariant obligation for `git_add`/`git_commit`.
- **Observed Implementation:** `scripts/mcp_servers/git/repository_state.py` `verify_authorization()` treats the current HEAD as the destination for `git_add`/`git_commit` and rejects it when it is a configured protected branch; `TestHeadDestinationProtection` pins the protected HEAD rejection, the allowed cases, and the detached HEAD denial, and the dirty-worktree reachability tests stay in `tests/mcp_servers/git/test_git_security_compliance.py`.
- **Impact:** A safety-relevant enforcement runs with no Invariant mandate; a regression now fails a test, but the check is not part of the Invariant set.
- **Recommended Action:** the owner decides whether to add an Invariant for the HEAD-destination check (pending amendment via the ADR Approval Ledger, with its index row and citation count handled in a separate Plan) or record it as out of scope. No approval is written here.
- **Resolution Target:** maintainer decision recorded in ADR-012 (Invariant plus pending amendment, or explicit out-of-scope statement)

#### EVENTBUS-001

- **ID:** EVENTBUS-001
- **Title:** EventBus still appends events.jsonl although ADR-006 no longer permits it
- **Status**: open
- **Severity:** Medium
- **Area:** EventBus
- **Type:** document-code-mismatch
- **Source:** `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`
- **Owner:** Repository owner
- **First Found:** adrdoc001 ADR-006 and ADR-008 amendment
- **Target:** `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`
- **Related:** AAL-040
- **Summary:** ADR-006 states that the EventBus creates no events.jsonl (INV-18), but the publish route still appends it.
- **Current Description:** ADR-006 Decision Detail 15 and INV-18 make eventbus.sqlite the sole source of truth and prohibit events.jsonl.
- **Observed Implementation:** `scripts/eventbus/publish_route.py` appends to events.jsonl after the SQLite commit and increments eventbus_jsonl_append_failure_total.
- **Impact:** The file is an incomplete replica that can be mistaken for a backup or recovery source.
- **Recommended Action:** Remove the JSONL append and its metric through an implementation issue, then remove this entry.
- **Resolution Target:** implementation removes the JSONL append and the ADR-006 INV-18 test exists

#### EVENTBUS-002

- **ID:** EVENTBUS-002
- **Title:** EventBus retention, replay floor, capacity signals, and the retention-participant registry are not implemented
- **Status**: open
- **Severity:** High
- **Area:** EventBus
- **Type:** document-code-mismatch
- **Source:** `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`
- **Owner:** Repository owner
- **First Found:** adrdoc001 ADR-006 and ADR-008 amendment
- **Target:** `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`
- **Related:** AAL-041
- **Summary:** ADR-006 defines state-aware retention, HTTP 410 replay expiration, and capacity and readiness rules (INV-19 to INV-22) that no code implements, and the retention-participant registry model is not approved.
- **Current Description:** ADR-006 Decision Details 18 to 20 and the Replay Contract define the retention and replay-floor rules.
- **Observed Implementation:** No retention task, purge, capacity signal, retention configuration, replay-floor check, or HTTP 410 response exists under `scripts/eventbus/`; events, consumer_delivery, and dlq_outbox rows are never deleted.
- **Impact:** Storage grows without bound and a purged position cannot be detected until the rules are implemented.
- **Recommended Action:** Maintainer approves the registry model, then implementation issues add the retention task, replay floor, capacity signals, and tests.
- **Resolution Target:** retention, replay floor, and readiness behavior are implemented and INV-19 to INV-22 are verified

#### SHARED-003

- **ID:** SHARED-003
- **Title:** Agent memory code still implements the old Semantic/Episodic model and memory JSONL
- **Status**: open
- **Severity:** Medium
- **Area:** Shared/DB
- **Type:** document-code-mismatch
- **Source:** `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`
- **Owner:** Repository owner
- **First Found:** adrdoc001 ADR-006 and ADR-008 amendment
- **Target:** `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`
- **Related:** ADR-008 Approval Record (approved 2026-11-24; previously AAL-039)
- **Summary:** ADR-008 no longer permits Semantic Memory, memory JSONL, pin state, manual memory writes, or /memory data (INV-20 to INV-22), but the Agent code still implements them.
- **Current Description:** ADR-008 Decision Detail 24 defines Repository Context and Episodic Memory as the only memory model.
- **Observed Implementation:** `scripts/agent/memory/` and the session schema still contain the old memory model, the JSONL store, and the /memory command.
- **Impact:** Operators can rely on memory JSONL as a recovery source that the ADR no longer recognizes.
- **Recommended Action:** Implementation issues replace the memory model and remove the JSONL and /memory paths, then this entry is removed.
- **Resolution Target:** code matches Decision Detail 24 and INV-20 to INV-22 are verified

#### SHARED-004

- **ID:** SHARED-004
- **Title:** ADR-008 lifecycle policies left undecided for Episodic Memory and for capacity monitoring
- **Status**: open
- **Severity:** Medium
- **Area:** Shared/DB
- **Type:** document-code-mismatch
- **Source:** `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`
- **Owner:** Repository owner
- **First Found:** adrdoc001 ADR-006 and ADR-008 amendment
- **Target:** `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`
- **Related:** ADR-008 Approval Record (approved 2026-11-24; previously AAL-039)
- **Summary:** The Episodic Memory retention policy, its Session DB schema-mismatch handling, and capacity monitoring for stores other than eventbus.sqlite are not decided.
- **Current Description:** ADR-008 Decision Details 22 and 23 and the Recovery Policy Matrix record these cells as undecided.
- **Observed Implementation:** No policy or signal exists for the affected cells.
- **Impact:** An operator cannot tell how Episodic Memory is retained or how its schema mismatch is handled.
- **Recommended Action:** Maintainer decides each policy and the ADR-008 matrix is updated; then this entry is removed.
- **Resolution Target:** each undecided matrix cell has an approved policy

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

#### NC-003

- **ID:** NC-003
- **Source File:** `adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`
- **Section:** Decision > item 14 (EventBus producers and consumers)
- **Line Number:** 86
- **Question:** Which component defines the EventBus producers and consumers, and when is the integration planned?
- **Evidence:** ADR-006 Decision item 14 and the ADR-013 Caller model status both state that the producer and consumer model is not yet defined and that no producer or consumer is named.
- **Impact:** Until resolved, no producer or consumer is named, and the first publisher or consumer client of any kind activates ADR-013 `Review Triggers` item 1.
- **Required Action:** The maintainer decides the defining component and the integration timing; the implementer does not write either.
- **Status:** open
- **Assigned To:** maintainer
- **Last Reviewed:** 2026-11-20
- **Priority:** Medium
- **Related NC:** None
- **Resolution Target:** the decision recorded in ADR-006 Decision item 14
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
- **Scope:** Status, Withdrawal Approval Record, historical marking of the corpus-identity passages (Decision Details 11 and 14, the two identity rows of the failure-outcome table, INV-09, one Negative Consequence, one Review Trigger)

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
- **Decision:** No-loss statements hold under the ADR-008 schema-mismatch rule
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** Decision Detail 9, INV-07

#### AAL-030

- **ID:** AAL-030
- **ADR:** ADR-002
- **Decision:** INV-04 amendment proposal: config files carry no MCP-server-owned settings; the only MCP-specific value given to the Agent is each enabled server's connection token supplied through ADR-017's environment-variable mechanism, and an enabled server resolving to an empty token aborts startup per ADR-017
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** INV-04

#### AAL-032

- **ID:** AAL-032
- **ADR:** ADR-002
- **Decision:** INV-04 verification row set to Non-Blocking
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** INV-04 verification row

#### AAL-037

- **ID:** AAL-037
- **ADR:** ADR-006
- **Decision:** Stating the start position of the At-Least-Once delivery guarantee as a start position the Consumer itself selected (`since_seq` greater than zero or a `Last-Event-ID` header)
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** Decision Detail 9 and INV-07 delivery-guarantee text

#### AAL-038

- **ID:** AAL-038
- **ADR:** ADR-015
- **Decision:** Attributing the `tools/generate_adr_authority.py` guard blocks cited by ADR-015's Scope to ADR-016 (Decision 6 and INV-03) instead of extending ADR-015 INV-01
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** ADR-015 Decision Scope attribution sentence, Related ADRs entry, and the Approval Record pending bullet

#### AAL-040

- **ID:** AAL-040
- **ADR:** ADR-006
- **Decision:** Removal of EventBus events.jsonl; eventbus.sqlite is the sole source of truth
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** Decision Details 15 to 17, INV-17, INV-18, INV-21

#### AAL-041

- **ID:** AAL-041
- **ADR:** ADR-006
- **Decision:** EventBus state-aware retention, replay expiration (HTTP 410 replay_position_expired), and capacity and readiness rules
- **Approver:** Not recorded
- **Date:** Not recorded
- **Scope:** Decision Details 18 to 20, Replay Contract, INV-19, INV-20, INV-22

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
