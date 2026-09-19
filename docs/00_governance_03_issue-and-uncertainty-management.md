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

Part 1 entries are reviewed quarterly, consistent with the cadence documented for Part 2 Needs Confirmation items and "Proposed" ADRs in `docs/00_governance_01_documentation-policy.md` line 521.

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

Active Items follow an ordering convention: entries are grouped by ID-prefix (RAG-*, DESIGN-*, EVENTBUS-*, SHARED-*, CI-*), each group's entries in ascending numeric order.

#### RAG-003

RAG-003 ("Unresolved usage status of `RegisteredDocument` DTO") was resolved and removed from this active inventory 2026-09-14. Confirmed by direct code inspection while drafting `issues/done/20260914-105211_ragsvc02_unused-dto-and-config-dataclasses.md`: `grep -n "^class " scripts/rag/models_data.py` lists `EmbeddingResponse`, `ChunkDocument`, `CrawlDocument`, `ChunkRecord`, `PreparedChunk`, `TwoStageFetchResult` — no `RegisteredDocument` class exists anywhere in this file, and a repository-wide `grep -rn "class RegisteredDocument" scripts/` finds no definition anywhere. The class this entry's "unresolved usage status" question was about no longer exists — the entry's underlying question (required future component vs. removable dead code) is moot, since removal has already happened by some other change. Its absence from the active list is the correct, policy-compliant state — do not create a `#### RAG-003` heading.

#### RAG-004

RAG-004 ("Unresolved usage status of `models_config.py` configuration dataclasses") was resolved and removed from this active inventory 2026-09-14. Confirmed by direct code inspection while drafting `issues/done/20260914-105211_ragsvc02_unused-dto-and-config-dataclasses.md`: `grep -n "^class " scripts/rag/models_config.py` lists only `RagConfigImpl` — none of `MqeConfig`, `FusionConfig`, `RerankConfig`, `SearchConfig`, `ChunkSplitterConfig`, `IngesterConfig`, or `PipelineConfig` exist anywhere in this file, and a repository-wide `grep -rn "class {Name}" scripts/` for each of the seven finds no definition anywhere. The classes this entry's "unresolved usage status" question was about no longer exist — the entry's underlying question is moot, since removal has already happened by some other change. Its absence from the active list is the correct, policy-compliant state — do not create a `#### RAG-004` heading.

**RAG-005**: Resolved. sqlite-vec lacks FK constraints — `chunks_vec` has no foreign key pointing to `chunks`; mitigation enforced via deletion ordering (`chunks_vec` deleted before `documents`) confirmed in `scripts/rag/ingestion/document_manager.py::delete_document_chain()` (confirmed: lines 19-35). This limitation is documented in `docs/adr/ADR-005-rag-source-derived-index-relationships.md`'s Known Deviations section (lines 342-350). Its absence from the active list is the correct, policy-compliant state — do not create a `#### RAG-005` heading.

#### RAG-006

- **ID**: RAG-006
- **Title**: Missing operational guidance for rag-src/registered/ file lifecycle
- **Status**: open
- **Severity**: Low
- **Area**: RAG
- **Type**: operational-gap
- **Source**: `scripts/rag/ingestion/file_routing.py`, `scripts/rag/ingestion/ingester.py`
- **Owner**: Team
- **First Found**: 2026-09-13
- **Target**: `docs/03_rag_02_01_ingestion_pipeline-overview.md`, `docs/03_rag_02_04_ingestion_pipeline-ingester.md`
- **Related**: NC-026 — unresolved; no corresponding `#### NC-026` heading exists in Part 2 and no removal-placeholder paragraph naming NC-026 was found during this Plan's systematic scan.
- **Summary**: What is the retention/deletion policy for chunk files moved to `rag-src/registered/` after successful ingestion? Who deletes them, when, and under what trigger?
- **Current Description**: After successful ingestion, chunk files are routed to `rag-src/registered/` via `FileRouter`. The File Lifecycle table in the ingestion pipeline overview documents creation but not deletion of these files. No deletion logic exists in `scripts/rag/ingestion/ingester.py` or `file_routing.py`.
- **Observed Implementation**: `FileRouter.__init__` creates `self._registered_dir = registered_dir / path.name`; `FileRouter.route()` writes successful chunks to `dest = self._registered_dir / path.name`. No corresponding cleanup or deletion call anywhere in either file.
- **Impact**: `rag-src/registered/` may grow unbounded over time; files may be deleted ad hoc without traceability if this gap is not tracked with appropriate visibility.
- **Recommended Action**: Owner review required to define the retention period, deletion trigger, and deletion ownership for `rag-src/registered/` files. Until defined, this directory's growth should be monitored.
- **Resolution Target**: Next RAG architecture review

**Removal-placeholder-reference policy**: A `Related`/`Target` field may cite a removed entry's ID only when a removal-placeholder paragraph exists for that ID; without such a placeholder, the citation is treated as a dangling reference (Warning severity if the placeholder exists but no heading, Blocking if neither exists).

DESIGN-1 ("External RAG and local RAG corpus difference not documented") was resolved and removed from this active inventory 2026-09-14. Both documentation updates required by the source Issue (`issues/20260914-112416_ragsvc04_execution-mode-shared-corpus-doc.md`) are complete: (1) a shared-corpus note was added to `docs/03_rag_01_system_overview.md` stating that external/local RAG modes share one corpus by configuration convention (not an enforced invariant), citing both `config/agent.toml` and `config/rag_pipeline_mcp_server.toml`; (2) `docs/adr/ADR-010-rag-fallback.md`'s "Data Ownership and Persistence" `System of Record` line was reworded to describe one shared `rag.sqlite` file accessed via two execution paths, not two independent systems of record. Its absence from the active list is the correct, policy-compliant state — do not create a `#### DESIGN-1` heading.

#### DESIGN-2

- **ID**: DESIGN-2
- **Title**: No test guarantees application code never directly operates `chunks_fts`
- **Status**: open
- **Severity**: Medium
- **Area**: RAG
- **Type**: operational-gap
- **Source**: `scripts/rag/`
- **Owner**: Team
- **First Found**: 2026-08-22
- **Target**: `tests/` directory
- **Related**: ADR-009
- **Summary**: ADR-009 establishes that application code must never directly operate on the `chunks_fts` table — all FTS operations must go through the FTS wrapper. No test enforces this invariant.
- **Current Description**: The FTS wrapper provides a controlled interface for full-text search, but there is no test that verifies application code respects this boundary.
- **Observed Implementation**: Zero direct-write bypasses of ADR-005's rebuild-path restriction found. All non-wrapper, non-schema hits on `chunks_fts` outside `scripts/mcp_servers/mdq/` belong to the sanctioned `/session rag-rebuild-fts` path (invoked via `scripts/agent/commands/cmd_session.py`). Read-only `SELECT`/`bm25`/consistency-check queries against `chunks_fts` appear in `scripts/rag/repository.py` and `scripts/db/rag_consistency.py`. MDQ's `chunks_fts` references target a separate database (`/opt/llm/db/mdq.sqlite`, confirmed: `scripts/mcp_servers/mdq/mdq_service.py` line 67) and are out of ADR-009's RAG-boundary scope.
- **Impact**: Without enforcement, new code could inadvertently operate on `chunks_fts` directly, breaking the abstraction boundary established by the ADR.
- **Recommended Action**: Add a lint rule or test that scans for direct `chunks_fts` references outside the FTS wrapper, or add integration tests that verify all FTS operations go through the wrapper.
- **Resolution Target**: Next RAG architecture review

**EVENTBUS-001**: Resolved. Collision detection via `ValueError` on duplicate offsets was implemented in `scripts/eventbus/db.py::migrate_legacy_offsets()` (confirmed: lines 578-656). Legacy migration only — the live ACK path is unaffected. Its absence from the active list is the correct, policy-compliant state — do not create a `#### EVENTBUS-001` heading.

**EVENTBUS-002**: Resolved. Resolution confirmed by `docs/eventbus/03_replay_operations.md` (JSON response schema `{total, limit, offset, items}` confirmed: lines 44-66). Its absence from the active list is the correct, policy-compliant state — do not create a `#### EVENTBUS-002` heading.

#### EVENTBUS-005

- **ID**: EVENTBUS-005
- **Title**: Agent Cannot Publish to Event Bus
- **Status**: deferred
- **Severity**: Low
- **Area**: EventBus
- **Type**: design-gap
- **Source**: Agent/EventBus integration layer
- **Owner**: @eventbus-dev
- **First Found**: 2026-09-03
- **Target**: N/A: no current target document
- **Related**: EVENTBUS-006, EVENTBUS-007
- **Summary**: Agent integration is intentionally unimplemented; the Agent cannot publish events to Event Bus.
- **Current Description**: Intentional deferral — Agent integration is not currently prioritized; this is not a defect.
- **Observed Implementation**: Explicit in code — no Agent publish path exists in the Event Bus client.
- **Impact**: Limits Agent-driven workflows that would otherwise publish events. Workaround: direct MCP tool calls from the Agent.
- **Recommended Action**: Implement Agent → Event Bus publish when this integration is prioritized.
- **Resolution Target**: Next EventBus architecture review

#### EVENTBUS-006

- **ID**: EVENTBUS-006
- **Title**: Agent Cannot Subscribe to Event Bus SSE Streams
- **Status**: deferred
- **Severity**: Low
- **Area**: EventBus
- **Type**: design-gap
- **Source**: Agent/EventBus integration layer
- **Owner**: @eventbus-dev
- **First Found**: 2026-09-03
- **Target**: N/A: no current target document
- **Related**: EVENTBUS-005, EVENTBUS-007
- **Summary**: Agent integration is intentionally unimplemented; the Agent cannot subscribe to Event Bus SSE streams.
- **Current Description**: Intentional deferral — Agent integration is not currently prioritized; this is not a defect.
- **Observed Implementation**: Explicit in code — no Agent SSE client exists in the Event Bus client.
- **Impact**: Limits real-time Agent workflows. Workaround: the Agent polls via `/replay` or uses MCP tools.
- **Recommended Action**: Implement Agent SSE subscribe when this integration is prioritized.
- **Resolution Target**: Next EventBus architecture review

#### EVENTBUS-007

- **ID**: EVENTBUS-007
- **Title**: Agent Cannot Manage Event Bus Topics
- **Status**: deferred
- **Severity**: Low
- **Area**: EventBus
- **Type**: design-gap
- **Source**: Agent/EventBus integration layer
- **Owner**: @eventbus-dev
- **First Found**: 2026-09-03
- **Target**: N/A: no current target document
- **Related**: EVENTBUS-005, EVENTBUS-006
- **Summary**: Agent integration is intentionally unimplemented; the Agent cannot manage Event Bus topics.
- **Current Description**: Intentional deferral — Agent integration is not currently prioritized; this is not a defect.
- **Observed Implementation**: Explicit in code — no Agent topic-management path exists in the Event Bus client.
- **Impact**: Limits administrative workflows. Workaround: direct MCP tool calls for topic management.
- **Recommended Action**: Implement Agent topic management when this integration is prioritized.
- **Resolution Target**: Next EventBus architecture review

#### EVENTBUS-008

EVENTBUS-008 ("No Production Authentication Model for Event Bus HTTP API") was resolved 2026-09-14 and removed from this active inventory. Confirmed by direct code inspection: `scripts/eventbus/app.py` calls `attach_auth_middleware(app)`, and every route requires `Depends(require_role(...))`; the ACK/NACK/subscribe endpoints additionally require `Depends(require_consumer_identity)`, which validates the caller's bearer token and, when configured, a `consumer_id` allowlist. The entry's original claim ("no authentication middleware is implemented") no longer matches the code. Its absence from the active list is the correct, policy-compliant state — do not create a `#### EVENTBUS-008` heading. A narrower residual gap found during this same review — a token with no configured `consumer_id` allowlist entry has consumer-identity validation skipped (fail-open) — is tracked separately in `issues/20260914-102317_eventbus03_consumer-topic-authorization-ack-nack.md`, not under this entry.

#### SHARED-001

SHARED-001 was fully resolved this cycle; its content was transferred to SHARED-002 and SHARED-003, both since independently resolved and removed from this active inventory in turn. Its absence from the active list is the correct, policy-compliant state — do not create a `#### SHARED-001` heading.

#### CI-001

CI-001 ("EventBus process reads configuration directly instead of using ConfigLoader") was resolved and removed from this active inventory 2026-09-15. Confirmed by code inspection: `scripts/eventbus/config.py` now uses `ConfigLoader.load()` instead of direct `tomllib.load()`, preserving all EventBus-specific validation logic in `__post_init__` and `load_config()`. The migration was verified by tests confirming all existing validation error cases produce equivalent errors through the ConfigLoader path. Its absence from the active list is the correct, policy-compliant state — do not create a `#### CI-001` heading.

**CI-003**: Resolved. Resolution confirmed by `tests/agent/services/test_config_reload.py::test_apply_config_dict_exercises_real_registry_and_no_discovery_call` (confirmed: line 480). Re-evaluate if `mcpagent04` support is added. With the introduction of `llm_visibility_base` as an immutable discovery-time visibility field (REQ-001), the config reload path must also respect this field — a new Known Issue has been filed under REQ-001 to track this discrepancy. Its absence from the active list is the correct, policy-compliant state — do not create a `#### CI-003` heading.

CI-002 ("former-ADR-011 INV-01/INV-02 production/local recovery distinction — stale reference") was resolved and removed from this active inventory 2026-09-09. Confirmed by direct code inspection while drafting issues/done/20260909-192919_ci002_remove_placeholder.md: investigated against all three tracked ADR-011 revisions and current ADR-008 text, and the cited INV-01/INV-02 pair was found to have never existed; recover_corruption()'s lack of a production/local distinction was confirmed as correct, intended behavior, not a gap; removed 2026-09-09 with no further action required. Its absence from the active list is the correct, policy-compliant state — do not create a #### CI-002 heading.

#### CI-004

CI-004 ("ADR-010 INV-02 — in-process fallback potentially triggered on non-transport errors") was resolved and removed from this active inventory 2026-09-14. This entry's own premise did not match `ADR-010`'s actual text: confirmed by direct reading of `docs/adr/ADR-010-rag-fallback.md`, no invariant states fallback should occur "ONLY on transport errors" — `ADR-010`'s actual INV-02 is "HTTP呼び出しは`timeout=10.0`で各試行を制御する" (unrelated to fallback-trigger classification). The governing Decision Details are #4 ("HTTPエラー（401, 403, 4xx, 5xx）と空結果（""）を区別する") and #6 ("技術的失敗（タイムアウト、接続エラー、HTTPエラー）のみをフォールバック条件とする"), restated as INV-04 — both explicitly classify HTTP errors (4xx included) as a technical failure that *should* trigger fallback, not an exception to it. `scripts/rag/pipeline_service.py::call_rag_service()`'s 4xx-triggers-fallback behavior is exactly this intended design, and is locked in by existing tests (`tests/rag/test_rag_pipeline_service.py::test_4xx_returns_none_no_retry`, `::test_4xx_calls_set_fallback_reason`) that assert 4xx-triggers-fallback as the correct outcome, not a bug. Its absence from the active list is the correct, policy-compliant state — do not create a `#### CI-004` heading.

A narrower, genuine discrepancy was found during this same re-verification and is *not* covered by the above: `ADR-010` Decision #9 ("解析エラーはログに記録し、空結果として扱う" — a parse error should be logged and treated as an empty result, i.e. `""`, not a fallback trigger) does not match `call_rag_service()`'s actual `ValueError` handling, which returns `None` (triggering fallback) rather than `""` — also locked in by an existing test (`tests/rag/test_rag_pipeline_service.py::test_json_parse_error_calls_set_fallback_reason`). Whether this reflects an intentional, undocumented refinement of Decision #9, or an actual deviation from it, was not resolved during this correction pass and is out of scope for closing CI-004 — file a new, narrowly-scoped Known Issue or Needs Confirmation entry for this specific Decision #9 vs. `ValueError`-handling question if it is to be tracked.

#### CI-005

CI-005 ("ADR-004 INV-03 — fail-closed for missing config not implemented") was resolved and removed from this active inventory 2026-09-14. Confirmed by direct code inspection: this entry's `Source` field cited a non-existent `scripts/shared/config_loader.py::load_config()` — the actual `load_config()` (`scripts/agent/config_builders.py`) calls `ConfigLoader().load_all()`, whose `strict` parameter already defaults to `True` (`scripts/shared/config_loader.py`), and `_REQUIRED_CONFIG_FILES` includes `agent.toml`. `ConfigMissingError` is a `ValueError` subclass, so it is caught by `load_config()`'s own exception handler and re-raised as `ConfigLoadError` — a missing required config file already fails closed. Its absence from the active list is the correct, policy-compliant state — do not create a `#### CI-005` heading. `ConfigLoader.load_all()`'s docstring previously contradicted its actual `strict: bool = True` default ("If False (default), missing files are skipped") — corrected 2026-09-14.

**EventBus-specific verification (REQ-006)**: Verified by configuration test confirming `ConfigMissingError` is raised when a required config file is missing. The EventBus `load_config()` function (`scripts/eventbus/config.py`) validates required keys via `_REQUIRED_CONFIG_KEYS` and raises `ValueError` for missing keys — consistent with the fail-closed behavior described in CI-005.

#### CI-006

CI-006 ("ADR-004 Decision Details #4 — local safety-related fail-closed behavior not verified") was resolved and removed from this active inventory 2026-09-14 — not by verifying the local-mode behavior it asked about, but because the premise no longer applies: `docs/adr/ADR-004-environment-failure-handling-policy.md`'s own 2026-09-04 revision record states `SecurityProfile.LOCAL` was fully abolished and production-grade validation made unconditional for every normal startup. Confirmed by direct code inspection: `scripts/shared/mcp_config.py`'s `SecurityProfile` enum now defines only `PRODUCTION`, and `security_profile: SecurityProfile = SecurityProfile.PRODUCTION` is the sole default in `scripts/agent/config_dataclasses.py` — there is no local/production branch left in which safety checks could fail open. Its absence from the active list is the correct, policy-compliant state — do not create a `#### CI-006` heading.

#### CI-007

- **ID**: CI-007
- **Title**: ADR-009 INV-09 — FTS5 rebuild rules not verified
- **Status**: open
- **Severity**: Low
- **Area**: RAG
- **Type**: ambiguous-behavior
- **Source**: `scripts/rag/`
- **Owner**: @data-eng
- **First Found**: 2026-09-03
- **Target**: `docs/adr/ADR-009-rag-ft5-text-separation.md`
- **Related**: ADR-009, DESIGN-2
- **Summary**: ADR-009 defines specific FTS5 rebuild rules that must be followed.
- **Current Description**: These rules have not been validated against the actual implementation.
- **Observed Implementation**: Not verified.
- **Impact**: Incorrect FTS5 rebuild could lead to inconsistent search results.
- **Recommended Action**: Validate FTS5 rebuild logic against documented rules.
- **Resolution Target**: Next RAG architecture review

#### CI-008

- **ID**: CI-008
- **Title**: ADR-001 INV-01 — workflow definition required, verified but needs test coverage
- **Status**: open
- **Severity**: Medium
- **Area**: Agent
- **Type**: operational-gap
- **Source**: Agent Workflow Engine initialization path
- **Owner**: TODO(owner) — cross-area initiative, no single RACI role fits (see batching note)
- **First Found**: 2026-09-03
- **Target**: `docs/adr/ADR-001-workflow-engine-mandatory.md`
- **Related**: ADR-001
- **Summary**: ADR-001 states that workflow definitions are mandatory and missing workflows raise `RuntimeError`.
- **Current Description**: This has been verified via code inspection (`RuntimeError` raised on missing workflow during initialization), but there is no automated test covering this invariant.
- **Observed Implementation**: Verified by code inspection only.
- **Impact**: Without test coverage, regression of this invariant cannot be caught automatically.
- **Recommended Action**: Add a unit test for the workflow-definition requirement.
- **Resolution Target**: ADR-invariant test suite initiative — tracked as one cross-area effort, see batching note below

#### CI-009

- **ID**: CI-009
- **Title**: ADR-002 INV-01 — config isolation, verified but needs test coverage
- **Status**: open
- **Severity**: Medium
- **Area**: Shared/DB
- **Type**: operational-gap
- **Source**: `scripts/shared/config_loader.py::restrict_to()`
- **Owner**: TODO(owner) — cross-area initiative, no single RACI role fits (see batching note)
- **First Found**: 2026-09-03
- **Target**: `docs/adr/ADR-002-config-isolation.md`
- **Related**: ADR-002, CI-001
- **Summary**: ADR-002 states that config isolation must be enforced.
- **Current Description**: This has been verified via code inspection (`restrict_to()` enforcement confirmed in `config_loader.py`), but there is no automated test covering this invariant.
- **Observed Implementation**: Verified by code inspection only.
- **Impact**: Without test coverage, regression of this invariant cannot be caught automatically.
- **Recommended Action**: Add a unit test for config isolation enforcement.
- **Resolution Target**: ADR-invariant test suite initiative — tracked as one cross-area effort, see batching note below

#### CI-010

- **ID**: CI-010
- **Title**: ADR-003 INV-01 — RuntimeToolRegistry routing authority, verified but needs test coverage
- **Status**: open
- **Severity**: Medium
- **Area**: MCP
- **Type**: operational-gap
- **Source**: `scripts/shared/route_resolver.py::resolve()`
- **Owner**: TODO(owner) — cross-area initiative, no single RACI role fits (see batching note)
- **First Found**: 2026-09-03
- **Target**: `docs/adr/ADR-003-runtime-tool-registry-routing-authority.md`
- **Related**: ADR-003, CI-003, CI-015
- **Summary**: ADR-003 states that `RuntimeToolRegistry` is the sole routing authority.
- **Current Description**: This has been verified via code inspection (`resolve()` only looks up in `_runtime_registry`, never falls back to `ToolRegistry`), but there is no automated test covering this invariant.
- **Observed Implementation**: Verified by code inspection only.
- **Impact**: Without test coverage, regression of this invariant cannot be caught automatically.
- **Recommended Action**: Add a unit test for routing-authority enforcement.
- **Resolution Target**: ADR-invariant test suite initiative — tracked as one cross-area effort, see batching note below

#### CI-011

- **ID**: CI-011
- **Title**: ADR-005 INV-02 — RAG deletion order, verified but needs test coverage
- **Status**: open
- **Severity**: Medium
- **Area**: RAG
- **Type**: operational-gap
- **Source**: `scripts/db/rag_consistency.py` / RAG deletion path
- **Owner**: TODO(owner) — cross-area initiative, no single RACI role fits (see batching note)
- **First Found**: 2026-09-03
- **Target**: `docs/adr/ADR-005-rag-source-derived-index-relationships.md`
- **Related**: ADR-005, RAG-005
- **Summary**: ADR-005 states that `chunks_vec` must be deleted before `documents`.
- **Current Description**: This has been verified via code inspection (implementation matches the invariant), but there is no automated test covering this invariant.
- **Observed Implementation**: Verified by code inspection only.
- **Impact**: Without test coverage, regression of this invariant cannot be caught automatically.
- **Recommended Action**: Add a unit test for deletion-order enforcement.
- **Resolution Target**: ADR-invariant test suite initiative — tracked as one cross-area effort, see batching note below

#### CI-012

- **ID**: CI-012
- **Title**: ADR-006 INV-01 — EventBus offset monotonicity, verified but needs test coverage
- **Status**: open
- **Severity**: Medium
- **Area**: EventBus
- **Type**: operational-gap
- **Source**: `scripts/eventbus/offsets.py::write_offset()`
- **Owner**: TODO(owner) — cross-area initiative, no single RACI role fits (see batching note)
- **First Found**: 2026-09-03
- **Target**: `docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`
- **Related**: ADR-006, EVENTBUS-001
- **Summary**: ADR-006 states that EventBus offsets must be monotonically increasing.
- **Current Description**: This has been verified via code inspection (`seq > current` enforcement confirmed in `write_offset()`), but there is no automated test covering this invariant.
- **Observed Implementation**: Verified by code inspection only.
- **Impact**: Without test coverage, regression of this invariant cannot be caught automatically.
- **Recommended Action**: Add a unit test for offset-monotonicity enforcement.
- **Resolution Target**: ADR-invariant test suite initiative — tracked as one cross-area effort, see batching note below

#### CI-013

- **ID**: CI-013
- **Title**: ADR-007 INV-01 — stdio transport prohibition, verified but needs test coverage
- **Status**: open
- **Severity**: Medium
- **Area**: MCP
- **Type**: operational-gap
- **Source**: `scripts/mcp_servers/`
- **Owner**: TODO(owner) — cross-area initiative, no single RACI role fits (see batching note)
- **First Found**: 2026-09-03
- **Target**: `docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md`
- **Related**: ADR-007
- **Summary**: ADR-007 states that stdio transport is prohibited.
- **Current Description**: This has been verified via code inspection (no actual stdio transport code exists in `scripts/`, only conceptual comments), but there is no automated test covering this invariant.
- **Observed Implementation**: Verified by code inspection only.
- **Impact**: Without test coverage, regression of this invariant cannot be caught automatically.
- **Recommended Action**: Add a unit test for stdio-transport prohibition.
- **Resolution Target**: ADR-invariant test suite initiative — tracked as one cross-area effort, see batching note below

#### CI-014

- **ID**: CI-014
- **Title**: ADR-009 INV-01 — `normalized_content` LLM-output prohibition, verified but needs test coverage
- **Status**: open
- **Severity**: Medium
- **Area**: RAG
- **Type**: operational-gap
- **Source**: `_format_chunks()`
- **Owner**: TODO(owner) — cross-area initiative, no single RACI role fits (see batching note)
- **First Found**: 2026-09-15
- **Target**: `docs/adr/ADR-009-rag-ft5-text-separation.md`
- **Related**: ADR-009, CI-007
- **Summary**: ADR-009 states that `normalized_content` must not appear in LLM output.
- **Current Description**: This has been verified via code inspection (`_format_chunks()` uses `c.content`, not `c.normalized_content`), but there is no automated test covering this invariant.
- **Observed Implementation**: Verified by code inspection only.
- **Impact**: Without test coverage, regression of this invariant cannot be caught automatically.
- **Recommended Action**: Add a unit test for the `normalized_content` prohibition.
- **Resolution Target**: ADR-invariant test suite initiative — tracked as one cross-area effort, see batching note below

#### CI-015

- **ID**: CI-015
- **Title**: ADR-003 INV-01 — duplicate tool ownership fails agent startup, verified but needs test coverage
- **Status**: open
- **Severity**: Medium
- **Area**: MCP
- **Type**: operational-gap
- **Source**: `scripts/agent/services/mcp_tool_discovery.py`
- **Owner**: TODO(owner) — cross-area initiative, no single RACI role fits (see batching note)
- **First Found**: 2026-09-03
- **Target**: `docs/adr/ADR-003-runtime-tool-registry-routing-authority.md`
- **Related**: ADR-003, CI-003, CI-010
- **Summary**: ADR-003 (formerly also stated in ADR-013 INV-05, merged 2026-08-31) states that duplicate tool names produce a FATAL outcome.
- **Current Description**: This has been verified via code inspection (duplicate tool name produces a FATAL outcome, confirmed in `mcp_tool_discovery.py`), but there is no automated test covering this invariant.
- **Observed Implementation**: Verified by code inspection only.
- **Impact**: Without test coverage, regression of this invariant cannot be caught automatically.
- **Recommended Action**: Add a unit test for duplicate-tool detection.
- **Resolution Target**: ADR-invariant test suite initiative — tracked as one cross-area effort, see batching note below

#### CI-016

- **ID**: CI-016
- **Title**: ADR-004 Decision #12/INV-14 — undefined component criticality treatment relies on a safe default, verified but needs test coverage
- **Status**: open
- **Severity**: Medium
- **Area**: Agent
- **Type**: operational-gap
- **Source**: `scripts/shared/mcp_config.py` (`required: bool = True` default), `scripts/agent/services/mcp_tool_discovery.py`
- **Owner**: TODO(owner) — cross-area initiative, no single RACI role fits (see batching note)
- **First Found**: 2026-09-15
- **Target**: `docs/adr/ADR-004-environment-failure-handling-policy.md`
- **Related**: ADR-004
- **Summary**: ADR-004 Decision #12/INV-14 requires that undefined or undeterminable component criticality never be assumed non-required and be treated as an unresolved design/config error.
- **Current Description**: `McpServerConfig.required` defaults to `True` (`scripts/shared/mcp_config.py:95`), so an unspecified criticality is never silently treated as non-required. However, no automated test verifies this default-required safety net, and no distinct code path flags "criticality was never explicitly configured" as its own design/config error per Decision #12's literal wording — ADR-004's own Completion Checklist and Manual Review notes still list INV-14 as unverified/Manual-Review-only.
- **Observed Implementation**: Verified by code inspection only (default value inspection); no automated test.
- **Impact**: Without test coverage, a future change to the default value (e.g. `required: bool = False`) would silently violate INV-14 with no automated check to catch the regression.
- **Recommended Action**: Add a unit test asserting `McpServerConfig.required` defaults to `True` when unspecified, and/or a test asserting undefined-criticality components are never routed as non-required.
- **Resolution Target**: ADR-invariant test suite initiative — tracked as one cross-area effort, see batching note below

Note on CI-008 through CI-016 batching: These nine structurally identical "ADR invariant verified by code inspection, no automated test" entries are treated as one initiative. Their Area fields span Agent (CI-008, CI-016), Shared/DB (CI-009), MCP (CI-010, CI-013, CI-015), RAG (CI-011, CI-014), and EventBus (CI-012) — no single existing RACI role is accountable for a cross-area ADR-invariant-test-suite initiative. This Plan flags the decision for human determination: create a new cross-cutting role vs. revert to per-area ownership.

#### CI-017

- **ID**: CI-017
- **Title**: `docs/03_rag_04_04_dto-models_config.md`'s documented DTOs no longer exist — `scripts/rag/models_config.py` replaced by `RagConfigImpl`
- **Status**: open
- **Severity**: Medium
- **Area**: RAG
- **Type**: document-code-mismatch
- **Source**: `scripts/rag/models_config.py`, `scripts/shared/types.py::RagConfig`
- **Owner**: Unassigned
- **First Found**: 2026-09-20
- **Target**: `docs/03_rag_04_04_dto-models_config.md`
- **Related**: N/A
- **Summary**: The 7 dataclasses documented in `docs/03_rag_04_04_dto-models_config.md` (`MqeConfig`, `FusionConfig`, `RerankConfig`, `SearchConfig`, `ChunkSplitterConfig`, `IngesterConfig`, `PipelineConfig`) no longer exist in `scripts/rag/models_config.py`, which now defines only `RagConfigImpl`.
- **Current Description**: The doc's main body still describes the 7 legacy per-stage config dataclasses as the runtime config contract.
- **Observed Implementation**: `scripts/rag/models_config.py` defines only `RagConfigImpl` (a flat dataclass), actively used by `scripts/rag/pipeline.py` and 5 test files, implementing the `RagConfig` Protocol (`scripts/shared/types.py`), whose docstring no longer claims these files are "DTOs for the ingestion TOML format".
- **Impact**: A reader of this doc would look for config classes that no longer exist and miss the actual runtime contract (`RagConfigImpl`/`RagConfig` Protocol).
- **Recommended Action**: Rewrite `docs/03_rag_04_04_dto-models_config.md`'s main body to document `RagConfigImpl` and the `RagConfig` Protocol instead of the removed per-stage dataclasses.
- **Resolution Target**: Next RAG documentation pass covering `scripts/rag/models_config.py`

#### CI-018

- **ID**: CI-018
- **Title**: RAG exception hierarchy fragmented across `exceptions.py`/`llm_prompts.py`/`pipeline.py` with no recorded rationale
- **Status**: open
- **Severity**: Low
- **Area**: RAG
- **Type**: design-gap
- **Source**: `scripts/rag/exceptions.py`, `scripts/rag/llm_prompts.py::RagRerankError`, `scripts/rag/pipeline.py::RagPipelineError`
- **Owner**: Unassigned
- **First Found**: 2026-09-19
- **Target**: `docs/03_rag_05_4-error-handling-reference.md`
- **Related**: N/A
- **Summary**: `RagRerankError` and `RagPipelineError` are defined outside `scripts/rag/exceptions.py` and inherit from `RuntimeError` rather than the `RagLayerError` base class used by the other 7 rag-layer exceptions, with no ADR or design document recording a rationale for the split.
- **Current Description**: The exception hierarchy is not unified under a single base class across the rag layer.
- **Observed Implementation**: Confirmed via 3 independent refactoring commits: `5ac7b757 refactor(rag): Phase 1-3 — backward-compat removal, foundation files, dataclass migration` introduced `RagLayerError` and its 6 subclasses; `2ff62348 refactor(rag): split llm.py (413→42+260+245 lines) into prompts + client` introduced `RagRerankError`/`RagExpansionError` (`RuntimeError`-based); `c0477811 refactor(rag): pipeline/stages fail-fast — remove expand_queries_safe, except Exception fallbacks, add RagPipelineError` introduced `RagPipelineError` (`RuntimeError`-based). No ADR or design document records a rationale for keeping them separate.
- **Impact**: Future unification would require touching every `except` clause across `scripts/rag/` that currently catches `RagRerankError`/`RagPipelineError`/`RagExpansionError`/`RuntimeError` by name — a cross-cutting change; until then, a caller could catch the wrong exception type or miss one to a base-class catch.
- **Recommended Action**: Decide whether to unify `RagRerankError`/`RagPipelineError`/`RagExpansionError` under `RagLayerError` in a dedicated cross-cutting refactor, or document the split as an accepted permanent exception via ADR.
- **Resolution Target**: Next RAG exception-hierarchy refactor or ADR decision

#### REQ-001

- **ID**: REQ-001
- **Title**: Immutable discovery-time visibility field (`llm_visibility_base`) not enforced during config reload
- **Status**: open
- **Severity**: High
- **Area**: Agent
- **Type**: document-code-mismatch
- **Source**: `scripts/shared/runtime_tool.py`, `scripts/shared/runtime_tool_registry.py::apply_policy()`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `docs/00_governance_03_issue-and-uncertainty-management.md`
- **Related**: CI-003
- **Summary**: `llm_visibility_base` is defined as an immutable discovery-time visibility field on `RuntimeTool` (confirmed: 11 matches across `scripts/`), but the config reload path via `apply_policy()` does not enforce immutability of this field — a tool hidden from the LLM at discovery time could be unhidden via config reload.
- **Current Description**: `llm_visibility_base` exists on `RuntimeTool` (lines 53, 72, 76-77, 96, 111, 128-129, 148 in `runtime_tool.py`). The `apply_policy()` formula uses this field as the immutable base (confirmed: `scripts/shared/runtime_tool_registry.py` lines 166-167). However, no enforcement prevents config reload from overriding this field.
- **Observed Implementation**: `apply_policy()` reads `llm_visibility_base` as the starting point for visibility computation, but the config reload path can modify tool visibility without respecting this constraint.
- **Impact**: A tool hidden from the LLM at discovery time could become visible again through config reload, violating the security boundary established by REQ-001.
- **Recommended Action**: Enforce immutability of `llm_visibility_base` in the config reload path; add tests to verify this invariant.

#### REQ-002

- **ID**: REQ-002
- **Title**: Atomic registry swap invariant not verified during config reload
- **Status**: open
- **Severity**: Medium
- **Area**: Agent
- **Type**: design-gap
- **Source**: `scripts/shared/runtime_tool_registry.py`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `docs/00_governance_03_issue-and-uncertainty-management.md`
- **Related**: N/A
- **Summary**: Config reload swaps the tool registry, but there is no guarantee that the swap is atomic — intermediate states where some tools use the old registry and others use the new one could cause inconsistent routing decisions.
- **Current Description**: The registry swap mechanism during config reload does not provide atomicity guarantees. If the swap fails partway through, some tools may route through the old registry while others route through the new one.
- **Observed Implementation**: Not verified.
- **Impact**: Inconsistent routing decisions during partial registry swaps could lead to unauthorized tool access or incorrect fallback behavior.
- **Recommended Action**: Implement atomic registry swap (e.g., using a two-phase commit pattern) and add tests to verify this invariant.

#### REQ-003

- **ID**: REQ-003
- **Title**: Preflight gate additions not validated against all execution paths
- **Status**: open
- **Severity**: Medium
- **Area**: Agent
- **Type**: missing-documentation
- **Source**: `scripts/agent/tool_policy.py::check_preflight()`, `scripts/agent/repository_gateway.py`, `scripts/agent/commands/cmd_mdq.py`, `scripts/agent/commands/cmd_context.py`, `scripts/agent/tool_approval.py`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `docs/00_governance_03_issue-and-uncertainty-management.md`
- **Related**: N/A
- **Summary**: `check_preflight()` calls have been added to `_cmd_diff()` (line 114), `_execute_mdq()` (line 67), and other locations (9 total matches across `scripts/`), but there is no documentation or test coverage verifying that all execution paths are gated.
- **Current Description**: Preflight gates exist in multiple locations, but it is unclear whether all execution paths are covered. The scope of the preflight gate additions needs to be documented and tested.
- **Observed Implementation**: Confirmed: `check_preflight()` appears in 9 locations across `scripts/` — `repository_gateway.py` (lines 7, 24, 114), `cmd_mdq.py` (line 67), `cmd_context.py` (lines 35, 206), `tool_policy.py` (line 318), `tool_approval.py` (lines 31, 148).
- **Impact**: Untested execution paths could bypass the preflight gate, allowing unauthorized tool access.
- **Recommended Action**: Document the full set of execution paths covered by preflight gates and add tests to verify each path.

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
- **Question**: Should `_classify_error()` be extended to actually classify a case as `INVALID_FORMAT`, or should the enum value and its dispatch branch be removed as dead?
- **Evidence**: The structured six-state `DbCondition` classification is implemented (`scripts/db/recovery.py`), but `INVALID_FORMAT` is defined and dispatched-on without any code path that produces it — the branch is currently unreachable.
- **Impact**: Implementing wrong classification model would require rework; leaving unconfirmed risks divergent interpretations
- **Required Action**: Owner review of the classification model defined in ADR-008 (Decision Details #14, merged from former ADR-011) before implementation begins
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-06
- **Priority**: Medium
- **Related NC**: None
- **Resolution Target**: Confirm whether `_classify_error()` should be extended to produce `INVALID_FORMAT` cases, or whether the enum value and its dispatch branch should be removed as dead code.
- **Blocking**: No

#### NC-022

NC-022 ("Are `RAG → EventBus`, `MCP → EventBus`, and `Agent → EventBus` unimplemented design intent, or a documentation error?") was resolved by owner review 2026-09-14: confirmed as intended future integrations (design intent), not a documentation error — the edges are retained in `docs/00_governance_01_documentation-policy.md`'s Software Runtime Dependency Graph under a new "Planned (design intent, not yet implemented)" category rather than "Needs Confirmation." Removed from this active inventory. Its absence from the active list is the correct, policy-compliant state — do not create a `#### NC-022` heading.

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

NC-030 ("Should `adr` and `security` be permanent `area` enum values, or folded into an existing area?") was resolved by owner review 2026-09-14: folded into `governance` rather than kept as independent values. All 12 `docs/adr/*.md` files and both `docs/00_security_*.md` files had their `area:` front matter migrated from `adr`/`security` to `governance`; `00_governance_02_documentation-metadata.md`'s `area` enum was updated to the original 8 values accordingly. Removed from this active inventory. Its absence from the active list is the correct, policy-compliant state — do not create a `#### NC-030` heading.

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

#### NC-033

- **Source File**: `03_rag_02_03_ingestion_pipeline-chunksplitter.md`
- **Section**: lang Field Validation
- **Line Number**: ~194
- **Question**: Is `lang` field enforcement against `LanguageCode` values intended?
- **Evidence**: The document states: "any non-empty string accepted; the en/ja value set (LanguageCode) is convention only — not enforced at parse time (Needs confirmation: whether enforcement is intended)"
- **Impact**: If lang-field enforcement is actually intended but not implemented, downstream language-handling code could behave incorrectly without anyone flagging it as an open question
- **Required Action**: Owner confirmation or investigation of scripts/rag/ validation logic for the lang field
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-14
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next ChunkSplitter specification review
- **Blocking**: No

#### NC-034

- **Source File**: `chunk_splitter.py` / `config/chunk_splitter.toml`
- **Section**: min_chunk / max_chunk / chunk_overlap constants
- **Line Number**: ~70-71, 168-169, 185-186
- **Question**: Why is the minimum chunk size 40 characters, maximum chunk size 500 characters, and overlap 50 characters? What is the historical reason for these specific values?
- **Evidence**: No rationale comment in `chunk_splitter.py` or `config/chunk_splitter.toml`; no ADR or governance entry found. `_min_chunk` (line 70), `_max_chunk` (line 71), and `_chunk_overlap` (line 74) enforce the constraint boundaries documented in `docs/03_rag_05_1-configuration-reference.md` line 39, but no explanation exists for why 40/500/50 were chosen over any other values.
- **Impact**: Operators cannot understand why sub-40-char chunks are discarded as noise, why sections exceeding 500 chars are split further, or why overlap is set to 50 characters
- **Required Action**: Owner confirmation of the historical reason for these specific values; if resolved, update the chunksplitter documentation accordingly
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-14
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next ChunkSplitter specification review
- **Blocking**: No

#### NC-035

- **Source File**: `crawler.py` / `config/crawler.toml`
- **Section**: max_depth / max_pages operational limits
- **Line Number**: ~61, 66
- **Question**: Why is the crawl depth limited to 3 hops from the start URL, and why is the maximum pages per site limited to 200? What is the historical reason for these specific operational values?
- **Evidence**: No rationale comment in `crawler.py` or `config/crawler.toml`; no ADR or governance entry found. `_max_depth` (line 61) and `_max_pages` (line 66) read from `config/crawler.toml` and stop BFS traversal at the limit, but no explanation exists for why 3 and 200 were chosen over any other values.
- **Impact**: Operators cannot understand why crawlers stop after 3 hops or 200 pages per site; new developers may not realize these are operational limits rather than technical constraints
- **Required Action**: Owner confirmation of the historical reason for these specific operational values; if resolved, update the crawler documentation accordingly
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-14
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next crawler operations review
- **Blocking**: No

#### NC-036

- **Source File**: `scripts/rag/pipeline_service.py::call_rag_service()` / `ADR-010-rag-fallback.md`
- **Section**: Decision #9 vs. actual behavior
- **Line Number**: Decision #9 (line 69), `call_rag_service()` ValueError handling
- **Question**: Is the parse-error-triggers-fallback behavior an intentional refinement of Decision #9 or an unintended deviation?
- **Evidence**: ADR-010 Decision #9 states "解析エラーはログに記録し、空結果として扱う" (parse errors should be logged and treated as an empty result); however, `call_rag_service()` returns `None` on parse error, triggering fallback. The test `test_json_parse_error_calls_set_fallback_reason` confirms this behavior is actively defended by a passing test.
- **Impact**: An undocumented ADR deviation actively defended by a passing test — operators may assume parse errors are handled per ADR when they actually trigger fallback
- **Required Action**: Owner/architect judgment required: (1) If intentional, amend ADR-010 via ADR Change Protocol + RACI approval from `@data-eng`; (2) If unintended, fix `call_rag_service()` to treat parse errors as empty results per Decision #9
- **Status**: open
- **Assigned To**: @data-eng
- **Last Reviewed**: 2026-09-16
- **Priority**: High
- **Related NC**: None
- **Resolution Target**: Next RAG architecture review
- **Blocking**: No

#### NC-037

- **Source File**: `docs/adr/ADR-004-environment-failure-handling-policy.md`
- **Section**: Implementation Notes (MCP server retry policy)
- **Line Number**: ~450 (pre-reclassification; now a cross-reference to this entry)
- **Question**: Is the current single fixed-delay retry (`HEALTH_CHECK_RETRY_DELAY_SEC`) on MCP server unreachability an intentional simplicity choice, or is a configurable-attempt-count general Retry Policy still pending implementation?
- **Evidence**: Neither this ADR's `## Rationale` nor its `## Known Deviations` sections state or acknowledge this design choice either way.
- **Impact**: A future implementer might either leave the fixed retry alone (if intentional) or build unneeded complexity (if a general policy was never actually planned) without knowing which is correct.
- **Required Action**: Owner/architect confirmation of whether a configurable Retry Policy was ever intended for MCP server health checks.
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-19
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next Agent/MCP health-check design review
- **Blocking**: No

#### NC-038

- **Source File**: `docs/adr/ADR-015-reference-document-class-disposition.md`
- **Section**: Implementation Notes (Memory Reference-class migration candidates)
- **Line Number**: ~113 (pre-reclassification; now a cross-reference to this entry)
- **Question**: Which of the 6 candidate `docs/05_agent_12_*.md` chapter files (or how many) is/are the correct target for Memory-layer Reference-class migration under Option B?
- **Evidence**: `plans/done/20260919-105034_plan.md`'s own Unknowns table (`UNK-01`) and Execution Status (Step 4, still `In Progress`) confirm this is genuinely unresolved — `generate_memory_reference_table()` has not yet been added.
- **Impact**: The Memory Reference-class migration (Steps 2/3 of that Plan already completed for Agent/EventBus) cannot proceed until the target document(s) are confirmed.
- **Required Action**: Confirm target document(s) for `generate_memory_reference_table()`, per `plans/done/20260919-105034_plan.md` Step 4.
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-19
- **Priority**: Medium
- **Related NC**: None
- **Resolution Target**: Completion of `plans/done/20260919-105034_plan.md` Step 4
- **Blocking**: No

#### NC-039

- **Source File**: `docs/03_rag_05_3-logging.md`
- **Section**: Implementation Notes (JSON-lines structured logging)
- **Line Number**: ~33 (pre-reclassification; now a cross-reference to this entry)
- **Question**: Is it deliberate that `crawler.py`, `chunk_splitter.py`, and `ingester.py` never set `structured_log=True` (staying on text format), or was JSON-lines output intended for these scripts and never enabled?
- **Evidence**: Neither this doc nor `shared/logger.py` states whether JSON-lines was intended for these 3 scripts.
- **Impact**: Context fields (`turn_id`, `session_id`, `rag_query_id`, `workflow_id`, `task_id`) passed via `extra={...}` are silently dropped from these scripts' text-format output; if JSON logging was intended, this is a lost-observability gap, not a documented decision.
- **Required Action**: Owner confirmation of whether these 3 ingestion scripts should adopt `structured_log=True`.
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-19
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next RAG ingestion logging review
- **Blocking**: No

No other active items beyond NC-021 through NC-039 above.

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
