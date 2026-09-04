---
title: "Issue and Uncertainty Management"
area: governance
tags:
  - governance
related:
  - 00_index.md
  - 01_overview.md
---

# Issue and Uncertainty Management

## Purpose

This document defines how to track currently active discrepancies between documentation and implementation (Known Issues) and currently active unverified claims (Needs Confirmation). It ensures unconfirmed statements are trackable and actionable, preventing them from being silently accepted as facts.

## Part 1: Known Issues

### Entry Template

Each active Known Issue entry must contain these 16 fields: ID, Title, Status, Severity, Area, Type, Source, Owner, First Found, Target, Related, Summary, Current Description, Observed Implementation, Impact, Recommended Action.

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

### Consolidation Note

The area-specific `03_rag_90_inconsistencies_and_known_issues.md`,
`04_mcp_90_inconsistencies_and_known_issues.md`,
`05_agent_90_inconsistencies_and_known_issues.md`,
`06_eventbus_90_inconsistencies_and_known_issues.md`, and
`90_shared_90_inconsistencies_and_known_issues.md` files were consolidated into this
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

- **Agent 5-Tier Scheme (historical, superseded by this consolidation):** `05_agent_90`'s design intent
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

#### RAG-003

- **ID**: RAG-003
- **Title**: Unresolved usage status of `RegisteredDocument` DTO
- **Status**: open
- **Severity**: Low
- **Area**: RAG
- **Type**: design-gap
- **Source**: `scripts/rag/models_data.py`
- **Owner**: Team
- **First Found**: 2026-08-02
- **Target**: `docs/03_rag_04_01_dto-models_data.md`
- **Related**: RAG-004
- **Summary**: `RegisteredDocument` in `scripts/rag/models_data.py` appears to be unused throughout the codebase.
- **Current Description**: It is defined in `scripts/rag/models_data.py`, but grep shows zero external references. Its role as either a forward-looking placeholder or dead code is unconfirmed.
- **Observed Implementation**: Definition exists as the `RegisteredDocument` class, but no imports or instantiations found in any other `.py` files.
- **Impact**: Potential accumulation of dead code or confusion regarding intended data structures.
- **Recommended Action**: Confirm with design/implementation owner whether this is a required future component or removable dead code.

#### RAG-004

- **ID**: RAG-004
- **Title**: Unresolved usage status of `models_config.py` configuration dataclasses
- **Status**: open
- **Severity**: Low
- **Area**: RAG
- **Type**: design-gap
- **Source**: `scripts/rag/models_config.py`
- **Owner**: Team
- **First Found**: 2026-08-02
- **Target**: `docs/03_rag_04_04_dto-models_config.md`
- **Related**: RAG-003
- **Summary**: Several dataclasses in `scripts/rag/models_config.py` appear to be unused.
- **Current Description**: `MqeConfig`, `FusionConfig`, `RerankConfig`, `SearchConfig`, `ChunkSplitterConfig`, `IngesterConfig`, and `PipelineConfig` are defined in `scripts/rag/models_config.py` but do not appear to be imported or instantiated elsewhere. Configuration is currently handled via raw `dict` access from TOML files.
- **Observed Implementation**: Grep confirms no imports or instantiations of these classes outside `scripts/rag/models_config.py`.
- **Impact**: Potential accumulation of dead code or confusion regarding the intended configuration mechanism.
- **Recommended Action**: Confirm with design/implementation owner whether these are intentional placeholders for a future validation layer or removable dead code.

#### RAG-005

- **ID**: RAG-005
- **Title**: sqlite-vec does not enforce foreign key constraints on embedding vectors
- **Status**: open
- **Severity**: Low
- **Area**: RAG
- **Type**: operational-gap
- **Source**: `scripts/rag/`
- **Owner**: Team
- **First Found**: 2026-08-22
- **Target**: `docs/adr/ADR-005-rag-source-derived-index-relationships.md`
- **Related**: ADR-005
- **Summary**: sqlite-vec does not enforce foreign key constraints on embedding vectors stored in the `chunks_fts` table. This means orphaned vectors can exist even when their source documents are deleted.
- **Current Description**: When a document is deleted, its embeddings remain in the vector index because sqlite-vec has no FK enforcement mechanism.
- **Observed Implementation**: Deletion of a document removes rows from the primary table but leaves orphaned entries in the vector index until a manual cleanup step runs.
- **Impact**: Vector index grows over time with orphaned entries, increasing memory usage and potentially degrading search performance.
- **Recommended Action**: Accept this limitation and implement periodic cleanup of orphaned vectors, or migrate to a vector store that supports FK constraints. (Note: this is a known, accepted architectural limitation mitigated by deletion ordering, not an active defect being worked.)

#### RAG-006

- **ID**: RAG-006
- **Title**: Documentation described `read_json_file()`'s lenient fallback behavior as a current production reader
- **Status**: resolved
- **Severity**: Medium
- **Area**: RAG
- **Type**: obsolete-description
- **Source**: `scripts/rag/ingestion/pipeline_utils.py`
- **Owner**: Team
- **First Found**: 2026-09-02
- **Target**: `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`
- **Related**: N/A: no related active Known Issue
- **Summary**: `docs/03_rag_02_08_ingestion_pipeline-shared.md` documented `read_json_file()`'s lenient fallback behavior (`lang` default `"en"`, `chunk_index` default `0`, empty-string fallbacks) as a currently-relevant reader, even though the strict-reader migration (`read_crawl_json()`/`read_chunk_json()`, both raising `ChunkFormatError` on missing/invalid fields) had already superseded it in code.
- **Current Description**: `read_json_file()` remains in `scripts/rag/ingestion/pipeline_utils.py` (removal was out of scope for this resolution) but is confirmed unused by any current pipeline code path. The `docs/03_rag_*.md` Specification set now states `read_crawl_json()`/`read_chunk_json()` as the canonical readers, documents the `ChunkFormatError` failure mode, classifies every crawl/chunk field as Required/Nullable/Conditional in one canonical table (this document's Target), and marks `read_json_file()`'s description as historical in `docs/03_rag_02_08_ingestion_pipeline-shared.md`.
- **Observed Implementation**: Verified by test — `tests/rag/ingestion/test_pipeline_utils_strict.py` exercises `read_crawl_json()`/`read_chunk_json()`'s `ChunkFormatError` conditions; no test exercises `read_json_file()` as a production path.
- **Impact**: Prior to resolution, new artifact producers or future implementers reading the Specification set risked reintroducing lenient-fallback assumptions no longer valid against the strict readers.
- **Recommended Action**: Resolved — canonical-reader statements, the `ChunkFormatError` failure mode, and a single canonical Required/Nullable/Conditional field-contract table were added across the `docs/03_rag_*.md` Specification set, and `read_json_file()`'s description was relocated to a clearly marked historical section. (Action already taken via `plans/20260903-085152_plan.md`; entry retained per this template pending removal at next review, matching the `SHARED-002` precedent in this document.)

#### RAG-007

- **ID**: RAG-007
- **Title**: Documentation did not reflect Null Fill Mode's removal from `ETagManager`
- **Status**: resolved
- **Severity**: Medium
- **Area**: RAG
- **Type**: obsolete-description
- **Source**: `scripts/rag/ingestion/etag_manager.py`
- **Owner**: Team
- **First Found**: 2026-09-02
- **Target**: `docs/03_rag_02_06_ingestion_pipeline-supporting-components.md`
- **Related**: N/A: no related active Known Issue
- **Summary**: `issues/done/20260828_01_remove-fetched-at-null-fill-and-mandatory-contract.md` removed `_update_null_fill()` and made `fetched_at` mandatory on `ChunkDocument`/`ETagManager.update()`/`DocumentManager.handle_existing_document()`, but that change's Documentation Impact was limited to docstrings — the `docs/03_rag_*.md` Specification set was not updated to reflect Null Fill Mode's removal, `fetched_at`'s mandatory status, or several ETagManager freshness-comparison edge cases (invalid timestamps, equal timestamps, missing stored timestamp) newly relevant once the fallback path was gone.
- **Current Description**: `scripts/rag/ingestion/` no longer contains any `_update_null_fill`, `null_fill`, or `COALESCE` reference (confirmed via repository-wide search). The `docs/03_rag_*.md` Specification set now states Freshness Mode as `ETagManager`'s only update mode, documents `fetched_at` as a required field on `ChunkDocument`, and documents the invalid-incoming-timestamp, invalid-stored-timestamp, equal-timestamp, and missing-stored-timestamp outcomes in this document's Target above.
- **Observed Implementation**: Explicit in code — `scripts/rag/ingestion/etag_manager.py`'s `ETagManager` has a single update path (`_update_with_freshness()`), gated by `_is_stale_update()`; `ChunkDocument.fetched_at`, `ETagManager.update()`'s `new_fetched_at`, and `DocumentManager.handle_existing_document()`'s `fetched_at` are all typed `str`, not `str | None`.
- **Impact**: Prior to resolution, a reader of the Specification set could believe missing-`fetched_at` fallback handling (Null Fill Mode) still existed, or could be unaware of the freshness-comparison edge cases introduced by its removal.
- **Recommended Action**: Resolved — the `docs/03_rag_*.md` Specification set was updated to document `fetched_at` as required, Freshness Mode as the only update mode, and the invalid-timestamp/equal-timestamp/missing-stored-timestamp edge cases, cross-linked from the ingester and document-manager documents rather than duplicated. (Action already taken via `plans/done/20260903-085718_plan.md`; entry retained per this template pending removal at next review, matching the `SHARED-002`/`RAG-006` precedent in this document.)

#### DESIGN-1

- **ID**: DESIGN-1
- **Title**: External RAG and local RAG corpus difference not documented
- **Status**: open
- **Severity**: Medium
- **Area**: RAG
- **Type**: missing-documentation
- **Source**: `scripts/rag/`
- **Owner**: Team
- **First Found**: 2026-08-22
- **Target**: `docs/03_rag_01_system_overview.md`
- **Related**: ADR-010
- **Summary**: External RAG and local RAG use different corpora (different data sources), but this architectural difference is not documented anywhere. Users cannot determine which corpus is being queried without inspecting the code.
- **Current Description**: Two separate RAG implementations exist — one for external search and one for local search — each operating on different data stores.
- **Observed Implementation**: External RAG uses a vector store connected to an external API endpoint; local RAG uses SQLite with the sqlite-vec extension storing embeddings derived from ingested documents.
- **Impact**: Operators may assume both RAG systems query the same knowledge base, leading to incorrect expectations about result consistency.
- **Recommended Action**: Document the corpus difference in the RAG system overview and add a note to the ADR explaining why two corpora were chosen.

#### DESIGN-2

- **ID**: DESIGN-2
- **Title**: No test guarantees application code never directly operates `chunks_fts`
- **Status**: open
- **Severity**: Medium
- **Area**: RAG
- **Type**: missing-documentation
- **Source**: `scripts/rag/`
- **Owner**: Team
- **First Found**: 2026-08-22
- **Target**: `tests/` directory
- **Related**: ADR-009
- **Summary**: ADR-009 establishes that application code must never directly operate on the `chunks_fts` table — all FTS operations must go through the FTS wrapper. No test enforces this invariant.
- **Current Description**: The FTS wrapper provides a controlled interface for full-text search, but there is no test that verifies application code respects this boundary.
- **Observed Implementation**: Grep for direct SQL references to `chunks_fts` outside the FTS wrapper module shows that some code paths may bypass the wrapper.
- **Impact**: Without enforcement, new code could inadvertently operate on `chunks_fts` directly, breaking the abstraction boundary established by the ADR.
- **Recommended Action**: Add a lint rule or test that scans for direct `chunks_fts` references outside the FTS wrapper, or add integration tests that verify all FTS operations go through the wrapper.

#### EVENTBUS-001

- **ID**: EVENTBUS-001
- **Title**: Consumer ID Collision Detection
- **Status**: open
- **Severity**: High
- **Area**: EventBus
- **Type**: design-gap
- **Source**: `scripts/eventbus/offsets.py::write_offset()` (`_sanitize_consumer_id`)
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `06_eventbus_04_dlq_offsets_and_delivery_semantics.md`
- **Related**: EVENTBUS-003, EVENTBUS-008
- **Summary**: Multiple distinct `consumer_id`s may sanitize to the same filename, leading to silent overwriting of offsets.
- **Current Description**: Sanitization process (`_sanitize_consumer_id`) is lossy (e.g., `user.1` -> `user_1`), so one consumer can inadvertently overwrite another consumer's progress if IDs collide after sanitization.
- **Observed Implementation**: Current implementation uses simple replacement which causes collisions for `user.1` vs. `user_1`.
- **Impact**: One consumer can inadvertently overwrite another consumer's progress if IDs collide after sanitization, affecting data integrity and consumer isolation.
- **Recommended Action**: Implement collision detection using mapping files (e.g., `{sanitized_id}.map`). Workaround until implemented: ensure unique `consumer_id`s that do not result in identical sanitized strings.

#### EVENTBUS-002

- **ID**: EVENTBUS-002
- **Title**: `/replay?format=json` Pagination Format Undocumented
- **Status**: open
- **Severity**: Low
- **Area**: EventBus
- **Type**: missing-documentation
- **Source**: `scripts/eventbus/` replay endpoint
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `06_eventbus_02_operations.md`, `06_eventbus_06_reference-api.md`
- **Related**: EVENTBUS-001
- **Summary**: `/replay?format=json` returns `{total, limit, offset, items}`, but this pagination response format is not documented in the API reference.
- **Current Description**: Behavior is correct — the endpoint returns paginated JSON — but the format is undocumented, so clients may not know to expect a paginated response structure.
- **Observed Implementation**: Explicit in code — the replay endpoint returns paginated JSON; documentation lacks a format specification.
- **Impact**: Clients may not know to expect paginated response structure. Workaround: clients can infer the shape from the response body.
- **Recommended Action**: Add the pagination format to `06_eventbus_02_operations.md` and `06_eventbus_06_reference-api.md`.

#### EVENTBUS-003

- **ID**: EVENTBUS-003
- **Title**: Dual Path for DLQ Promotion Undocumented
- **Status**: open
- **Severity**: Medium
- **Area**: EventBus
- **Type**: missing-documentation
- **Source**: `nack_event()` in `ack_route.py`; `promote_single()` in `dlq.py`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `06_eventbus_02_operations.md`
- **Related**: EVENTBUS-004
- **Summary**: DLQ promotion occurs via two paths — inline nack escalation and a background sweep — but only one path was documented.
- **Current Description**: Two independent code paths promote to DLQ (inline in the nack handler, plus a background sweep); both must be documented.
- **Observed Implementation**: Explicit in code — `nack_event()` calls `promote_single()` inline; `dlq.py` also has a background sweep calling `promote_single()`.
- **Impact**: Operators may not understand all DLQ entry origins. No workaround — documentation only.
- **Recommended Action**: Document both paths in `06_eventbus_02_operations.md`.

#### EVENTBUS-004

- **ID**: EVENTBUS-004
- **Title**: `promote_to_dlq()` Dead Code
- **Status**: open
- **Severity**: Low
- **Area**: EventBus
- **Type**: obsolete-description
- **Source**: `scripts/eventbus/dlq.py::promote_to_dlq()`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `scripts/eventbus/dlq.py`
- **Related**: EVENTBUS-003
- **Summary**: `promote_to_dlq()` is never called; only `sweep_orphans()`/`promote_single()` are valid paths.
- **Current Description**: Function was added but never wired into any call path; superseded by `promote_single()`.
- **Observed Implementation**: Explicit in code — grep shows zero callers of `promote_to_dlq()` in `scripts/`.
- **Impact**: Dead code increases maintenance surface and potential confusion during audits. Code is inert; no runtime impact.
- **Recommended Action**: Remove `promote_to_dlq()` or add a deprecation marker with a migration note.

#### EVENTBUS-005

- **ID**: EVENTBUS-005
- **Title**: Agent Cannot Publish to Event Bus
- **Status**: deferred
- **Severity**: Low
- **Area**: EventBus
- **Type**: design-gap
- **Source**: Agent/EventBus integration layer
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: N/A: no current target document
- **Related**: EVENTBUS-006, EVENTBUS-007
- **Summary**: Agent integration is intentionally unimplemented; the Agent cannot publish events to Event Bus.
- **Current Description**: Intentional deferral — Agent integration is not currently prioritized; this is not a defect.
- **Observed Implementation**: Explicit in code — no Agent publish path exists in the Event Bus client.
- **Impact**: Limits Agent-driven workflows that would otherwise publish events. Workaround: direct MCP tool calls from the Agent.
- **Recommended Action**: Implement Agent → Event Bus publish when this integration is prioritized.

#### EVENTBUS-006

- **ID**: EVENTBUS-006
- **Title**: Agent Cannot Subscribe to Event Bus SSE Streams
- **Status**: deferred
- **Severity**: Low
- **Area**: EventBus
- **Type**: design-gap
- **Source**: Agent/EventBus integration layer
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: N/A: no current target document
- **Related**: EVENTBUS-005, EVENTBUS-007
- **Summary**: Agent integration is intentionally unimplemented; the Agent cannot subscribe to Event Bus SSE streams.
- **Current Description**: Intentional deferral — Agent integration is not currently prioritized; this is not a defect.
- **Observed Implementation**: Explicit in code — no Agent SSE client exists in the Event Bus client.
- **Impact**: Limits real-time Agent workflows. Workaround: the Agent polls via `/replay` or uses MCP tools.
- **Recommended Action**: Implement Agent SSE subscribe when this integration is prioritized.

#### EVENTBUS-007

- **ID**: EVENTBUS-007
- **Title**: Agent Cannot Manage Event Bus Topics
- **Status**: deferred
- **Severity**: Low
- **Area**: EventBus
- **Type**: design-gap
- **Source**: Agent/EventBus integration layer
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: N/A: no current target document
- **Related**: EVENTBUS-005, EVENTBUS-006
- **Summary**: Agent integration is intentionally unimplemented; the Agent cannot manage Event Bus topics.
- **Current Description**: Intentional deferral — Agent integration is not currently prioritized; this is not a defect.
- **Observed Implementation**: Explicit in code — no Agent topic-management path exists in the Event Bus client.
- **Impact**: Limits administrative workflows. Workaround: direct MCP tool calls for topic management.
- **Recommended Action**: Implement Agent topic management when this integration is prioritized.

#### EVENTBUS-008

- **ID**: EVENTBUS-008
- **Title**: No Production Authentication Model for Event Bus HTTP API
- **Status**: open
- **Severity**: High
- **Area**: EventBus
- **Type**: operational-gap
- **Source**: `scripts/eventbus/config.py`; Event Bus route handlers (`ack_route.py`, `subscribe_route.py`, `publish_route.py`)
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: N/A: no current target document
- **Related**: EVENTBUS-001
- **Summary**: The Event Bus HTTP API (`/publish`, `/subscribe`, `/events/{event_id}/ack`, `/nack`, `/health`, `/dlq`, `/replay`) lacks production-grade authentication/authorization; the only control is unconditional loopback-only binding.
- **Current Description (updated 2026-09-04)**: No authentication middleware is implemented. `allow_public_bind` (the former escape hatch allowing a non-loopback bind) was removed entirely by `plans/done/20260903-091921_plan.md` ("loopbackonly") — `EventBusConfig.__post_init__()` (`scripts/eventbus/config.py`) now raises `ValueError` unconditionally for any host other than `127.0.0.1`/`::1`, with no configuration override possible.
- **Observed Implementation**: Explicit in code — no auth middleware exists; `scripts/eventbus/config.py`'s `_is_public_host()` check is now a fail-fast `ValueError` in `__post_init__()`, not a togglable gate.
- **Impact**: The Event Bus HTTP API remains reachable without authentication to any process on the same host (or via SSH tunnel), since loopback-only binding is the sole control and cannot be relaxed. This is a narrower residual risk than before `allow_public_bind`'s removal (public exposure is no longer possible via configuration), but same-host/tunneled access still has no authentication layer.
- **Recommended Action**: Implement static bearer-token validation in the Event Bus process; add auth middleware to route handlers.

#### SHARED-002

- **ID**: SHARED-002
- **Title**: Backup restoration was not validated, not atomic, and not re-verified after restore
- **Status**: resolved
- **Severity**: High
- **Area**: Shared/DB
- **Type**: design-gap
- **Source**: `scripts/db/recovery.py::_restore_from_backup()`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `90_shared_05_04_db_api_and_operations-recovery-and-reference.md` section 9.5 Safe restoration sequence
- **Related**: SHARED-003
- **Summary**: `_restore_from_backup()` restored from a backup file whose own integrity was never checked (only `Path.exists()` was verified), copied directly onto the live target path via `shutil.copy2()` instead of through a temporary file with an atomic rename, and did not reopen or re-run an integrity check on the restored database before reporting `success=True`.
- **Current Description**: A corrupted backup could be restored unconditionally; a failure mid-copy could leave the target database partially written; a restore that produced a still-broken database was reported as successful.
- **Observed Implementation**: Backup validation and atomic temp-file staging were already implemented; the missing post-restore re-verification was added, returning `action="restore_verify_failed"` on failure (Verified by test).
- **Impact**: A corrupted backup could be restored unconditionally; a failure mid-copy could leave the target database partially written.
- **Recommended Action**: Resolved — validate the backup independently before use, restore through a temporary file with an atomic replace, and re-run integrity verification against the restored file before returning success. (Action already taken; entry retained per this template pending removal at next review, since this document, not the deleted area file, is now the system of record.)

#### SHARED-003

- **ID**: SHARED-003
- **Title**: `workflow.sqlite` and `eventbus.sqlite` have no physical-corruption recovery path
- **Status**: deferred
- **Severity**: High
- **Area**: Shared/DB
- **Type**: design-gap
- **Source**: `scripts/db/recovery.py::recover_corruption()`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `90_shared_05_04_db_api_and_operations-recovery-and-reference.md` section 9.7 Persistence-domain policy
- **Related**: SHARED-002, ADR-008
- **Summary**: `recover_corruption()` only supports `target='rag'` or `target='session'`. Neither `workflow.sqlite` (task/approval state) nor `eventbus.sqlite` (event delivery state) has corruption-recovery or backup-rotation coverage.
- **Current Description**: Unsupported `target` values are now rejected (`action="unsupported_target"`), fixing a prior mismatched-display-path bug where a `target="workflow"`/`"eventbus"` call integrity-checked `session_db_path` and could VACUUM the real file unchecked. ADR-008 Decision Details #20 (merged from former ADR-011 Requirement #6) makes `no_recovery_allowed` for `workflow`/`eventbus` the accepted policy (manual operator recovery only, no automatic restoration) rather than a bug.
- **Observed Implementation**: `target` validation now rejects unsupported values explicitly (Verified by test).
- **Impact**: Physical corruption of workflow or event-delivery state has no automatic recovery procedure; the only observed startup behavior for a broken session/workflow store is a fatal `RuntimeError` that stops the agent. This is accepted policy, not a gap, for the automatic-recovery question — the remaining gap is operational: no documented step-by-step operator recovery runbook exists for these two domains.
- **Recommended Action**: Write the operator recovery runbook for `workflow.sqlite`/`eventbus.sqlite` (target-validation fix and policy decision are both already complete).

#### CI-001

- **ID**: CI-001
- **Title**: EventBus process reads configuration directly instead of using ConfigLoader
- **Status**: open
- **Severity**: High
- **Area**: EventBus
- **Type**: document-code-mismatch
- **Source**: `scripts/eventbus/config.py`; `scripts/shared/config_loader.py`
- **Owner**: Unassigned
- **First Found**: 2026-08-22
- **Target**: `02_config_isolation_02_01_config-loader-design.md`
- **Related**: ADR-002
- **Summary**: ADR-002 requires that all processes load configuration via ConfigLoader to ensure process-level config isolation. EventBus reads its own TOML configuration directly without going through ConfigLoader, violating this invariant.
- **Current Description**: EventBus's `config.py` loads TOML files directly using `tomllib.load()` or similar, bypassing ConfigLoader entirely.
- **Observed Implementation**: `scripts/eventbus/config.py` opens TOML files and parses them independently; `scripts/shared/config_loader.py` is never imported or used by the EventBus module.
- **Impact**: EventBus operates with a configuration loading path that differs from other processes, potentially leading to inconsistent config handling across the system.
- **Recommended Action**: Refactor EventBus configuration loading to use ConfigLoader, ensuring consistent config access across all processes.

#### CI-002

- **ID**: CI-002
- **Title**: former-ADR-011 INV-01/INV-02 production/local recovery distinction — stale reference
- **Status**: resolved
- **Severity**: N/A
- **Area**: Shared/DB
- **Type**: obsolete-description
- **Source**: `scripts/db/recovery.py::recover_corruption()`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `docs/adr/ADR-008-sqlite-4db-separation.md`
- **Related**: ADR-008
- **Summary**: `recover_corruption()` does NOT distinguish between production and local environments — confirmed to be the correct, intended current behavior, not a gap.
- **Current Description**: This entry's original wording cited an "INV-01 (production MUST NOT auto-recover without explicit operator confirmation)" / "INV-02 (local MAY auto-recover)" pair that was investigated against all three tracked ADR-011 revisions and the current ADR-008 text: no such invariant pair was ever present.
- **Observed Implementation**: No production/local recovery gap exists; the entry described a citation that never corresponded to real ADR content.
- **Impact**: None — retained as a historical record of the investigation.
- **Recommended Action**: None required.

#### CI-003

- **ID**: CI-003
- **Title**: ADR-003 Decision Details #14 — reload-updates-only-policy-fields claim not verified
- **Status**: open
- **Severity**: Medium
- **Area**: MCP
- **Type**: ambiguous-behavior
- **Source**: `scripts/shared/runtime_tool_registry.py::apply_policy()`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `docs/adr/ADR-003-runtime-tool-registry-routing-authority.md`
- **Related**: ADR-003
- **Summary**: ADR-003 (formerly ADR-013 Decision Details #6, merged 2026-08-31) states that reload operations update only policy-derived fields and do NOT rediscover tools.
- **Current Description**: The implementation appears correct based on code inspection of `apply_policy()`, but this has NOT been validated against the actual reload flow. `requires_approval` (unread by any approval code) was removed from `RuntimeTool`/`apply_policy()`; the former ADR-013's mentions of it are now stale and were not carried into ADR-003.
- **Observed Implementation**: Code inspection of `apply_policy()` in `runtime_tool_registry.py` appears correct; not traced end-to-end.
- **Impact**: If reload also rediscovered tools, it would violate the stated invariant that policy changes don't alter tool availability.
- **Recommended Action**: Trace the full reload execution path to confirm only policy fields are updated.

#### CI-004

- **ID**: CI-004
- **Title**: ADR-010 INV-02 — in-process fallback potentially triggered on non-transport errors
- **Status**: open
- **Severity**: Medium
- **Area**: RAG
- **Type**: document-code-mismatch
- **Source**: `scripts/rag/http_augment.py`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `docs/adr/ADR-010-rag-fallback.md`
- **Related**: ADR-010
- **Summary**: ADR-010 states that in-process fallback should occur ONLY on transport errors (connection refused, timeout, etc.).
- **Current Description**: The implementation in `http_augment.py` triggers immediate fallback on 4xx errors and parse errors (`ValueError`), which are NOT transport errors — normal HTTP responses (e.g. 404, 400) trigger in-process fallback rather than being handled as valid HTTP responses.
- **Observed Implementation**: Confirmed by code inspection of `http_augment.py`'s fallback trigger conditions.
- **Impact**: Normal HTTP error responses cause unnecessary in-process fallback, potentially masking real transport failures and increasing latency.
- **Recommended Action**: Review `http_augment.py` to distinguish transport errors from application-level HTTP errors.

#### CI-005

- **ID**: CI-005
- **Title**: ADR-004 INV-03 — fail-closed for missing config not implemented
- **Status**: open
- **Severity**: High
- **Area**: Shared/DB
- **Type**: implementation-bug
- **Source**: `scripts/shared/config_loader.py::load_config()`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `docs/adr/ADR-004-environment-failure-handling-policy.md`
- **Related**: ADR-004
- **Summary**: ADR-004 states that missing configuration should fail closed (stop the process) in ALL modes.
- **Current Description**: `load_config()` calls `ConfigLoader().load_all()` WITHOUT `strict=True`, so missing config files silently skip in all modes. The `ConfigMissingError` class exists but is never raised because strict loading is never enabled.
- **Observed Implementation**: Confirmed by code inspection — `strict=True` is never passed to `load_all()`.
- **Impact**: Missing critical configuration silently fails open across all environments, including production.
- **Recommended Action**: Pass `strict=True` to `load_all()` or add explicit validation after config loading.

#### CI-006

- **ID**: CI-006
- **Title**: ADR-004 Decision Details #4 — local safety-related fail-closed behavior not verified
- **Status**: open
- **Severity**: Medium
- **Area**: Shared/DB
- **Type**: ambiguous-behavior
- **Source**: `check_readiness()`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `docs/adr/ADR-004-environment-failure-handling-policy.md`
- **Related**: ADR-004
- **Summary**: ADR-004 states that local safety-related checks (like permission checks) should fail closed even though general health checks fail open.
- **Current Description**: The implementation in `check_readiness()` distinguishes between production/local modes, but it is unclear whether safety-related checks specifically fail closed in local mode.
- **Observed Implementation**: Not fully traced; distinguishing logic exists but has not been verified against this specific invariant.
- **Impact**: Safety checks might incorrectly pass in local mode, allowing unsafe operations.
- **Recommended Action**: Verify that safety-related checks in `check_readiness()` enforce fail-closed behavior in local mode.

#### CI-007

- **ID**: CI-007
- **Title**: ADR-009 INV-09 — FTS5 rebuild rules not verified
- **Status**: open
- **Severity**: Low
- **Area**: RAG
- **Type**: ambiguous-behavior
- **Source**: `scripts/rag/`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `docs/adr/ADR-009-rag-ft5-text-separation.md`
- **Related**: ADR-009, DESIGN-2
- **Summary**: ADR-009 defines specific FTS5 rebuild rules that must be followed.
- **Current Description**: These rules have not been validated against the actual implementation.
- **Observed Implementation**: Not verified.
- **Impact**: Incorrect FTS5 rebuild could lead to inconsistent search results.
- **Recommended Action**: Validate FTS5 rebuild logic against documented rules.

#### CI-008

- **ID**: CI-008
- **Title**: ADR-001 INV-01 — workflow definition required, verified but needs test coverage
- **Status**: open
- **Severity**: Medium
- **Area**: Agent
- **Type**: operational-gap
- **Source**: Agent Workflow Engine initialization path
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `docs/adr/ADR-001-workflow-engine-mandatory.md`
- **Related**: ADR-001
- **Summary**: ADR-001 states that workflow definitions are mandatory and missing workflows raise `RuntimeError`.
- **Current Description**: This has been verified via code inspection (`RuntimeError` raised on missing workflow during initialization), but there is no automated test covering this invariant.
- **Observed Implementation**: Verified by code inspection only.
- **Impact**: Without test coverage, regression of this invariant cannot be caught automatically.
- **Recommended Action**: Add a unit test for the workflow-definition requirement.

#### CI-009

- **ID**: CI-009
- **Title**: ADR-002 INV-01 — config isolation, verified but needs test coverage
- **Status**: open
- **Severity**: Medium
- **Area**: Shared/DB
- **Type**: operational-gap
- **Source**: `scripts/shared/config_loader.py::restrict_to()`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `docs/adr/ADR-002-config-isolation.md`
- **Related**: ADR-002, CI-001
- **Summary**: ADR-002 states that config isolation must be enforced.
- **Current Description**: This has been verified via code inspection (`restrict_to()` enforcement confirmed in `config_loader.py`), but there is no automated test covering this invariant.
- **Observed Implementation**: Verified by code inspection only.
- **Impact**: Without test coverage, regression of this invariant cannot be caught automatically.
- **Recommended Action**: Add a unit test for config isolation enforcement.

#### CI-010

- **ID**: CI-010
- **Title**: ADR-003 INV-01 — RuntimeToolRegistry routing authority, verified but needs test coverage
- **Status**: open
- **Severity**: Medium
- **Area**: MCP
- **Type**: operational-gap
- **Source**: `scripts/shared/route_resolver.py::resolve()`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `docs/adr/ADR-003-runtime-tool-registry-routing-authority.md`
- **Related**: ADR-003, CI-003, CI-015
- **Summary**: ADR-003 states that `RuntimeToolRegistry` is the sole routing authority.
- **Current Description**: This has been verified via code inspection (`resolve()` only looks up in `_runtime_registry`, never falls back to `ToolRegistry`), but there is no automated test covering this invariant.
- **Observed Implementation**: Verified by code inspection only.
- **Impact**: Without test coverage, regression of this invariant cannot be caught automatically.
- **Recommended Action**: Add a unit test for routing-authority enforcement.

#### CI-011

- **ID**: CI-011
- **Title**: ADR-005 INV-02 — RAG deletion order, verified but needs test coverage
- **Status**: open
- **Severity**: Medium
- **Area**: RAG
- **Type**: operational-gap
- **Source**: `scripts/db/rag_consistency.py` / RAG deletion path
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `docs/adr/ADR-005-rag-source-derived-index-relationships.md`
- **Related**: ADR-005, RAG-005
- **Summary**: ADR-005 states that `chunks_vec` must be deleted before `documents`.
- **Current Description**: This has been verified via code inspection (implementation matches the invariant), but there is no automated test covering this invariant.
- **Observed Implementation**: Verified by code inspection only.
- **Impact**: Without test coverage, regression of this invariant cannot be caught automatically.
- **Recommended Action**: Add a unit test for deletion-order enforcement.

#### CI-012

- **ID**: CI-012
- **Title**: ADR-006 INV-01 — EventBus offset monotonicity, verified but needs test coverage
- **Status**: open
- **Severity**: Medium
- **Area**: EventBus
- **Type**: operational-gap
- **Source**: `scripts/eventbus/offsets.py::write_offset()`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`
- **Related**: ADR-006, EVENTBUS-001
- **Summary**: ADR-006 states that EventBus offsets must be monotonically increasing.
- **Current Description**: This has been verified via code inspection (`seq > current` enforcement confirmed in `write_offset()`), but there is no automated test covering this invariant.
- **Observed Implementation**: Verified by code inspection only.
- **Impact**: Without test coverage, regression of this invariant cannot be caught automatically.
- **Recommended Action**: Add a unit test for offset-monotonicity enforcement.

#### CI-013

- **ID**: CI-013
- **Title**: ADR-007 INV-01 — stdio transport prohibition, verified but needs test coverage
- **Status**: open
- **Severity**: Medium
- **Area**: MCP
- **Type**: operational-gap
- **Source**: `scripts/mcp_servers/`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md`
- **Related**: ADR-007
- **Summary**: ADR-007 states that stdio transport is prohibited.
- **Current Description**: This has been verified via code inspection (no actual stdio transport code exists in `scripts/`, only conceptual comments), but there is no automated test covering this invariant.
- **Observed Implementation**: Verified by code inspection only.
- **Impact**: Without test coverage, regression of this invariant cannot be caught automatically.
- **Recommended Action**: Add a unit test for stdio-transport prohibition.

#### CI-014

- **ID**: CI-014
- **Title**: ADR-009 INV-01 — `normalized_content` LLM-output prohibition, verified but needs test coverage
- **Status**: open
- **Severity**: Medium
- **Area**: RAG
- **Type**: operational-gap
- **Source**: `_format_chunks()`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `docs/adr/ADR-009-rag-ft5-text-separation.md`
- **Related**: ADR-009, CI-007
- **Summary**: ADR-009 states that `normalized_content` must not appear in LLM output.
- **Current Description**: This has been verified via code inspection (`_format_chunks()` uses `c.content`, not `c.normalized_content`), but there is no automated test covering this invariant.
- **Observed Implementation**: Verified by code inspection only.
- **Impact**: Without test coverage, regression of this invariant cannot be caught automatically.
- **Recommended Action**: Add a unit test for the `normalized_content` prohibition.

#### CI-015

- **ID**: CI-015
- **Title**: ADR-003 INV-01 — duplicate tool ownership fails agent startup, verified but needs test coverage
- **Status**: open
- **Severity**: Medium
- **Area**: MCP
- **Type**: operational-gap
- **Source**: `scripts/agent/services/mcp_tool_discovery.py`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `docs/adr/ADR-003-runtime-tool-registry-routing-authority.md`
- **Related**: ADR-003, CI-003, CI-010
- **Summary**: ADR-003 (formerly also stated in ADR-013 INV-05, merged 2026-08-31) states that duplicate tool names produce a FATAL outcome.
- **Current Description**: This has been verified via code inspection (duplicate tool name produces a FATAL outcome, confirmed in `mcp_tool_discovery.py`), but there is no automated test covering this invariant.
- **Observed Implementation**: Verified by code inspection only.
- **Impact**: Without test coverage, regression of this invariant cannot be caught automatically.
- **Recommended Action**: Add a unit test for duplicate-tool detection.

No other active Known Issues beyond RAG-003, RAG-004, RAG-005, DESIGN-1, DESIGN-2,
EVENTBUS-001 through EVENTBUS-008, SHARED-002, SHARED-003, and CI-001 through
CI-015 above.

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

#### NC-021

- **Source File**: `90_shared_05_04_db_api_and_operations-recovery-and-reference.md`
- **Section**: 9.3 Integrity-result model (target design)
- **Line Number**: ~39
- **Question**: Is the target structured integrity-result classification (healthy / confirmed corruption / lock contention / permission / invalid format / unknown) the classification model the owner intends to implement?
- **Evidence**: `_run_integrity_check()` currently returns only pass/fail-ish result plus free-form exception string; no structured classification exists
- **Impact**: Implementing wrong classification model would require rework; leaving unconfirmed risks divergent interpretations
- **Required Action**: Owner review of the classification model defined in ADR-008 (Decision Details #14, merged from former ADR-011) before implementation begins
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-08-21
- **Priority**: Medium
- **Related NC**: None
- **Resolution Target**: The prerequisite structured-classification implementation is already in place (`DbCondition`/`_classify_error()` in `scripts/db/recovery.py`); this item now tracks confirming the classification model matches the owner's intent
- **Blocking**: No

#### NC-022

- **Source File**: `00_governance_01_documentation-policy.md`
- **Section**: Software Runtime Dependency Graph
- **Line Number**: ~306
- **Question**: Are `RAG → EventBus`, `MCP → EventBus`, and `Agent → EventBus`
  unimplemented design intent, or a documentation error that should be removed from
  the graph entirely?
- **Evidence**: `grep -rl "eventbus" scripts/agent/ scripts/mcp_servers/ scripts/rag/`
  returns 0 matches — none of Agent, MCP, or RAG source imports or HTTP-publishes to
  EventBus, despite these three edges being asserted in the previous (pre-correction)
  Area Dependency Graph
- **Impact**: If unimplemented, the corrected graph's marking of these edges as
  Needs Confirmation (rather than confirmed fact) is the right interim state; if a
  documentation error, the edges should eventually be removed once confirmed absent
- **Required Action**: Owner review of whether Agent/MCP/RAG are intended to
  eventually publish to EventBus, or whether these edges should be removed once
  confirmed absent
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-03
- **Priority**: Medium
- **Related NC**: None
- **Resolution Target**: Next EventBus integration review, or next Software Runtime
  Dependency Graph review, whichever comes first
- **Blocking**: No

#### NC-023

- **Source File**: `00_governance_01_documentation-policy.md`
- **Section**: Software Runtime Dependency Graph
- **Line Number**: ~306
- **Question**: Are `scripts/rag/` and `scripts/mcp_servers/rag_pipeline/` the same
  RAG implementation (one wrapping the other) or two independent implementations?
- **Evidence**: Not investigated by `plans/done/20260902-191512_plan.md` (explicitly
  Out-of-Scope there); the Software Runtime Dependency Graph's RAG node's exact
  relationship to the MCP node's `rag_pipeline` server is undetermined as a result
- **Impact**: Without resolving this, the Runtime Graph's RAG node scope is
  ambiguous, and any future edge involving RAG cannot be confirmed as
  direct-vs-indirect
- **Required Action**: Owner or RAG-area-lead investigation comparing
  `scripts/rag/` and `scripts/mcp_servers/rag_pipeline/`'s actual code and
  responsibilities
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-03
- **Priority**: Medium
- **Related NC**: None
- **Resolution Target**: Next RAG architecture review
- **Blocking**: No

#### NC-024

- **Source File**: `00_governance_01_documentation-policy.md`
- **Section**: Software Runtime Dependency Graph / Governance Applicability Matrix
- **Line Number**: ~306
- **Question**: Should the Security governance area be treated as a runtime
  component (added as a node to the Software Runtime Dependency Graph) rather than
  governance-only?
- **Evidence**: No `scripts/security/` or equivalent runtime package was found by a
  quick `find` during this Plan's investigation, but this was not exhaustively
  confirmed
- **Impact**: If Security has a runtime component not yet reflected as a graph
  node, the Runtime Graph's node set (Agent, MCP, RAG, EventBus, Shared/DB) would be
  incomplete
- **Required Action**: Owner confirmation of whether a Security runtime component
  exists anywhere in the repository; if so, add it to the Software Runtime
  Dependency Graph's node set
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-03
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next governance area-scope review
- **Blocking**: No

#### NC-025

- **Source File**: `00_governance_01_documentation-policy.md`
- **Section**: Change Impact Rule
- **Line Number**: ~198
- **Question**: Is a Configuration Ownership Map or API Consumer Map needed for the
  Change Impact Rule's configuration/API-change categories, beyond the existing
  Canonical Source Precedence matrix?
- **Evidence**: The Change Impact Rule directs configuration/API changes to the
  existing Canonical Source Precedence matrix (Decision Target Canonical Source
  Matrix) rather than a dedicated map; no such map exists anywhere in the repository
- **Impact**: Without a dedicated map, configuration/API change-impact scoping
  relies on the same general-purpose matrix used for all decision types, which may
  be too coarse for large configuration surfaces
- **Required Action**: Owner review of whether configuration/API change volume
  justifies building a dedicated Configuration Ownership Map or API Consumer Map
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-03
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next governance tooling review
- **Blocking**: No

#### NC-026

- **Source File**: `03_rag_02_04_ingestion_pipeline-ingester.md`
- **Section**: 4a. RagIngester (`scripts/rag/ingestion/ingester.py`) — Class Overview
- **Line Number**: ~37
- **Question**: What is the retention/deletion policy for chunk files moved to `rag-src/registered/` after successful ingestion? Who deletes them, when, and under what trigger?
- **Evidence**: The document states only that "Processed chunks are moved to `rag-src/registered/`" (also stated in `03_rag_01_system_overview.md`); no retention period, deletion trigger, or deletion owner is documented anywhere in the RAG Specification set (confirmed by repository-wide search)
- **Impact**: Without a documented policy, `rag-src/registered/` may grow unbounded, or files may be deleted ad hoc without a way to trace ingestion history
- **Required Action**: Owner review to define retention period, deletion trigger, and deletion ownership; document the decision in the ingester Specification
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-03
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next RAG operations documentation pass
- **Blocking**: No

#### NC-027

- **Source File**: `03_rag_02_03_ingestion_pipeline-chunksplitter.md`
- **Section**: 3. ChunkSplitter (`scripts/rag/ingestion/chunk_splitter.py`) — Module-level Constants
- **Line Number**: ~40
- **Question**: What is the rationale for `MIN_HEADING_LINES_FOR_MARKDOWN = 2` (the minimum heading-line count threshold used to decide Markdown heading-based chunking)?
- **Evidence**: The document already carries an inline marker: "the rationale for `MIN_HEADING_LINES_FOR_MARKDOWN = 2` is unconfirmed (Needs Confirmation)"; the constant is defined in `scripts/rag/ingestion/chunk_splitter.py` with no rationale comment
- **Impact**: Changing this value without knowing its rationale risks unintended changes to heading-based chunk splitting, e.g. short Markdown sections being split incorrectly
- **Required Action**: Owner confirmation, or investigate how this value was originally derived (test cases, empirical validation)
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-03
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next ChunkSplitter specification review
- **Blocking**: No

#### NC-028

- **Source File**: `03_rag_02_08_ingestion_pipeline-shared.md`
- **Section**: FTS5 Query Token Limit
- **Line Number**: ~132
- **Question**: What is the rationale for the FTS5 query token limit of 20 (`_MAX_FTS_TOKENS` in `scripts/rag/repository.py`)? Is it based on measurement or load testing?
- **Evidence**: The document already carries an inline marker: "There is currently no documented rationale within the project for this specific value (20) based on measurement or load testing. As it appears to be a heuristic setting, it should be re-validated during performance tuning."
- **Impact**: An unvalidated limit risks silently truncating long queries (reducing search precision) if too low, or query explosion if raised without validation
- **Required Action**: Re-validate this value against measurement or load testing during RAG query performance tuning
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-03
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next RAG query performance tuning pass
- **Blocking**: No

#### NC-029

- **Source File**: `03_rag_02_09_ingestion_pipeline-shared-utilities.md`
- **Section**: Constants
- **Line Number**: ~47
- **Question**: What is the rationale for `MIN_TEXT_LENGTH_FOR_DETECTION = 100` (the minimum text length required for language detection)?
- **Evidence**: The document already carries an inline marker: "the rationale for `MIN_TEXT_LENGTH_FOR_DETECTION = 100` is unconfirmed (Needs Confirmation)"; the constant is defined in `scripts/rag/utils.py` with no rationale comment
- **Impact**: Changing this threshold without knowing its rationale risks unintended effects on language-detection accuracy for short texts
- **Required Action**: Owner confirmation, or validate against the language-detection library's own empirical guidance
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-03
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next language-detection logic review
- **Blocking**: No

#### NC-030

- **Source File**: `00_governance_02_documentation-metadata.md`
- **Section**: Existing Metadata Fields (`area` enum)
- **Line Number**: ~22
- **Question**: Should `adr` and `security` be permanent `area` enum values, or
  folded into an existing area (e.g. `overview`)?
- **Evidence**: 11 real documents use `area: adr`, 2 use `area: security`, yet
  neither was part of the original 8-value enum; no stated design rationale
  was found for the omission
- **Impact**: If folded into another area instead, 13 documents' `area:`
  values would need migration; if kept permanent, no migration is needed but
  the enum grows to 10 values
- **Required Action**: Owner review of whether `adr` and `security` warrant
  their own top-level area, given their real, non-trivial adoption
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-03
- **Priority**: Medium
- **Related NC**: None
- **Resolution Target**: Next governance area-taxonomy review
- **Blocking**: No

#### NC-031

- **Source File**: `00_governance_02_documentation-metadata.md`
- **Section**: Existing Metadata Fields (`related`)
- **Line Number**: ~24
- **Question**: Is the front-matter `related` field and the `## Related
  Documents` body-section heading an intentional duality (front matter for
  tooling, body section for human readers), or an unintentional drift where
  one should be removed?
- **Evidence**: Both exist in active use across the document set; no design
  rationale was found in `docs/00_governance_01_documentation-policy.md` or
  `docs/00_governance_02_documentation-metadata.md` explaining why both exist
- **Impact**: If unintentional drift, maintaining two parallel
  related-documents lists risks them diverging (one updated, the other left
  stale)
- **Required Action**: Owner decision on whether both should be kept (and if
  so, whether one should generate the other), or one should be deprecated
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-03
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next governance metadata review
- **Blocking**: No

#### NC-032

- **Source File**: `schemas/doc_front_matter.json`
- **Section**: `additionalProperties` (top-level schema property)
- **Line Number**: ~6
- **Question**: Should `schemas/doc_front_matter.json` set
  `additionalProperties: false` (strict, matching `schemas/event_envelope.json`'s
  own convention) or remain permissive (`true`) to allow forward-compatible,
  area-specific extension fields?
- **Evidence**: `schemas/event_envelope.json` itself uses
  `additionalProperties: false`; however, this repository's actual `docs/*.md`
  front matter already carries area-specific extra keys in active use in some
  files (e.g. `source:` seen in several RAG documents)
- **Impact**: If later set to `false` without first auditing which documents
  carry extension keys, `docmeta03`'s CI enforcement would immediately fail on
  every file using one
- **Required Action**: Owner decision, informed by a survey of which documents
  currently use non-required front-matter keys, before `docmeta03`'s
  CI-enforcement implementation begins
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-03
- **Priority**: Medium
- **Related NC**: None
- **Resolution Target**: Before `docmeta03`'s CI-enforcement implementation
  begins
- **Blocking**: No

No other active items beyond NC-021 through NC-032 above.

## Temporary Exception Process

Applies to any automated check finding classified `Warning` (not `Blocking`) in
`docs/00_governance_04_documentation-checks.md`'s Governance Verification Matrix
— for example, `GV-020`'s removed-name reintroduction findings. A `Warning`
finding does not block merge by itself, but leaving it neither fixed nor formally
excepted is not a complete review (see `docs/00_governance_04_documentation-checks.md`
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
`docs/00_governance_04_documentation-checks.md`
`### 13. Merge Condition Validation`) — not as still-covered.

## Non-Goals

Topics explicitly excluded from this document:

- Resolving individual items — resolution requires separate investigation
- Modifying source documents during extraction — this document is read-only relative to sources
- Defining new evidence labels beyond those already established
- Changing the common template itself

## Related Documents

Cross-cutting documentation rules and policies:

- [Documentation Policy](00_governance_01_documentation-policy.md)
- [Documentation Metadata](00_governance_02_documentation-metadata.md)
- [Documentation Checks](00_governance_04_documentation-checks.md)

## Keywords

known issues
needs confirmation
inconsistencies
template
evidence labels
resolution workflow
