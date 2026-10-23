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

#### EVENTBUS-019

- **ID**: EVENTBUS-019
- **Title**: DLQ requeue is not transactional and reads shared SQLite state outside the global lock
- **Status**: open
- **Severity**: High
- **Area**: EventBus
- **Type**: implementation-bug
- **Source**: `scripts/eventbus/dlq_repo.py`, `scripts/eventbus/dlq_route.py`
- **Owner**: Repository owner
- **First Found**: Documentation review (design-vs-code check)
- **Target**: `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`
- **Related**: `issues/20261023-154325_eventbus001_dlq-requeue-transactional.md`, `docs/24_eventbus/eventbus_03_dlq_operations.md`
- **Summary**: A failed requeue can leave an uncommitted `dlq_requeue_count` update on the shared connection, and the route queries SQLite outside the global lock.
- **Current Description**: ADR-006 INV-08 requires the count and history of Requeue to be persisted, and INV-16 requires related state changes to commit or roll back together.
- **Observed Implementation**: `redeliver_event()` updates `dlq_requeue_count` and inserts the redelivery row but commits only on success and never rolls back. The shared connection uses implicit transactions, so a later request can commit the leftover update. `dlq_requeue()` reads `new_seq` and reclassifies 404/409 with `db.execute(...)` after the locked section, and `dlq_list()` takes the lock twice (count, then page). The default timestamp is interpolated into SQL through an f-string.
- **Impact**: A committed requeue count can exist without its redelivery row; the response can describe a different state than the repository operation; DLQ pagination totals can disagree with the page.
- **Recommended Action**: Move the whole transition into one repository transaction under one lock acquisition with explicit rollback, return a typed result, and read the DLQ count and page in one snapshot.
- **Resolution Target**: The requeue state transition is atomic, no SQLite access remains in the route, and negative and concurrency tests cover the failure paths.

#### EVENTBUS-020

- **ID**: EVENTBUS-020
- **Title**: The EventBus config loader drops the authorization mappings and accepts duplicate token values
- **Status**: open
- **Severity**: High
- **Area**: EventBus
- **Type**: implementation-bug
- **Source**: `scripts/eventbus/config.py`, `scripts/eventbus/auth.py`
- **Owner**: Repository owner
- **First Found**: Documentation review (design-vs-code check)
- **Target**: `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`
- **Related**: `issues/20261023-154326_eventbus002_config-authorization-token-roles.md`
- **Summary**: `load_config()` does not pass `consumer_authorization` and `topic_authorization` to `EventBusConfig`, and equal token values are not rejected.
- **Current Description**: ADR-013 requires a Consumer process to use a `consumer_token` with explicit `consumer_authorization` and `topic_authorization` mappings, and the shared `auth_token` never holds the Consumer role.
- **Observed Implementation**: Both keys are known and validated in `EventBusConfig.__post_init__` but `load_config()` builds the object without them, so a TOML mapping is lost and a configured `consumer_token` fails startup with a missing-mapping error. `_populate_token_maps()` unions roles when a per-role token equals an existing map key, so a `consumer_token` equal to `auth_token` yields the control-plane roles plus Consumer. The shipped `config/eventbus.toml` sets no per-role token, so the defect is latent until one is configured.
- **Impact**: A valid Consumer configuration cannot start from a file; ambiguous duplicate tokens can create a principal that the ADR forbids.
- **Recommended Action**: Pass the validated mappings through the loader, reject any duplicate non-empty token value before the principal map is built, and test through the file-loading path.
- **Resolution Target**: A TOML mapping reaches the Consumer principal, and duplicate token values are rejected at load.

#### EVENTBUS-021

- **ID**: EVENTBUS-021
- **Title**: EventBus schema shape is not validated when `user_version` matches, and deployment does not verify EventBus readiness
- **Status**: open
- **Severity**: High
- **Area**: EventBus
- **Type**: implementation-bug
- **Source**: `scripts/eventbus/schema.py`, `scripts/db/create_schema.py`, `deploy/init_db.sh`, `deploy/setup_services.sh`
- **Owner**: Repository owner
- **First Found**: Documentation review (design-vs-code check)
- **Target**: `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`
- **Related**: `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `docs/90_deployment/deployment_01_deployment.md`, `issues/20261023-154326_eventbus003_startup-gate-schema-health.md`
- **Summary**: A correctly stamped but malformed EventBus database starts, and the deployment scripts report success without checking EventBus tables, process or health.
- **Current Description**: The deployment guide states that `init_db.sh` verifies all mandatory EventBus tables and aborts when any is missing, and that the EventBus service refuses a different table shape; ADR-004 requires fail-closed startup on schema inconsistency.
- **Observed Implementation**: `_init_schema()` returns when `PRAGMA user_version` equals the expected value; the column comparison runs only for an unstamped database. `scripts/db/create_schema.py` compares only the version and runs idempotent `CREATE ... IF NOT EXISTS` DDL. `deploy/init_db.sh` verifies the Workflow tables only and prints `.tables` for EventBus. `deploy/setup_services.sh` starts the process in the background, prints one health response if available, and prints `started` without checking process liveness or health.
- **Impact**: A database with a missing table or changed column can pass startup and fail on the first request that touches it; a crashed or degraded EventBus is reported as started.
- **Recommended Action**: Validate table shape against one shared fingerprint in both the runtime and the deployment path, and add bounded process and readiness polling to `setup_services.sh`; correct the deployment guide to the verified behavior in the same change.
- **Resolution Target**: A stamped but malformed database is rejected by both paths, and deployment reports EventBus started only after a verified readiness check.

#### EVENTBUS-022

- **ID**: EVENTBUS-022
- **Title**: EventBus shutdown closes the shared SQLite connection even when the database lock was not acquired
- **Status**: open
- **Severity**: High
- **Area**: EventBus
- **Type**: implementation-bug
- **Source**: `scripts/eventbus/app.py`, `tests/eventbus/test_eventbus_shutdown.py`
- **Owner**: Repository owner
- **First Found**: Documentation review (design-vs-code check)
- **Target**: `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`
- **Related**: `issues/20261023-154326_eventbus004_shutdown-safe-during-sweep.md`
- **Summary**: After the lock-acquisition timeout the lifespan still closes the connection a background sweep may be using.
- **Current Description**: ADR-006 treats SQLite as the canonical store (INV-01), which requires the connection to be released only when no other worker uses it.
- **Observed Implementation**: The lifespan waits up to 5.0 seconds for the global lock and then calls `db.close()` in a `finally` even when the lock was not acquired; `test_shutdown_logs_warning_when_lock_timeout_exceeded` requires that behavior, and `test_eventbus_app_isolation.py` replaces the DLQ loop with a no-op to avoid the crash. A worker thread still queued on the lock can run SQL on the closed connection.
- **Impact**: A shutdown during a long sweep can crash inside SQLite or interrupt an active transaction.
- **Recommended Action**: Track the worker, stop new sweeps at shutdown, and close the connection only when exclusive ownership is proven; choose a documented bounded-shutdown policy.
- **Resolution Target**: The connection is never closed while another worker may use it, and the tests assert that invariant.

#### EVENTBUS-023

- **ID**: EVENTBUS-023
- **Title**: A repeated NACK request is counted again because the route generates a new attempt identifier per request
- **Status**: open
- **Severity**: High
- **Area**: EventBus
- **Type**: implementation-bug
- **Source**: `scripts/eventbus/ack_route.py`, `scripts/eventbus/delivery_repo.py`
- **Owner**: Repository owner
- **First Found**: Documentation review (design-vs-code check)
- **Target**: `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`
- **Related**: `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`, `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`, `issues/20261023-154326_eventbus005_nack-idempotency-retries.md`
- **Summary**: The documented no-op for a duplicate NACK of the same delivery attempt cannot occur over HTTP.
- **Current Description**: A NACK that repeats the stored `consumer_last_nack_attempt` is a no-op and does not increment the consumer's failure count.
- **Observed Implementation**: `ack_route.py` generates a new random UUID as the attempt identifier on every request, so the stored value never matches a retry. The repository stores one key per consumer and event, and no delivery-attempt identifier is exposed to clients.
- **Impact**: Client or proxy retries double-count failures and promote events to the DLQ earlier than `max_retry` allows.
- **Recommended Action**: Define the delivery-attempt identity and a caller-supplied idempotency key, pass it unchanged to the repository, and decide the retention window.
- **Resolution Target**: A retry of the same delivery attempt does not increment the failure count, and the contract is identical in the API, documents and tests.

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
