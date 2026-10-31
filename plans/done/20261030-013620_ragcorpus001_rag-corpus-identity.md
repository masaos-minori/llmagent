## Goal
- Give the RAG corpus a verifiable identity (corpus ID, index generation, schema version, embedding-model ID, normalization version, chunking-policy version) that is compared before a remote-to-local fallback result is accepted and recorded on every RAG result path, and make startup consistency checking act on a structured severity classification so canonical-data corruption is fatal while repairable derived-index drift enters an observable degraded state.

## Priority
Medium

## Scope
- **In-Scope**:
  - Corpus identity definition, storage in the RAG database, computation from local DB + config, and exposure through the remote RAG health/response contract.
  - Identity comparison before accepting a remote-to-local fallback result; mismatch behavior (reject by default, explicitly degraded under an approved config allowance); recording of the selected corpus generation in diagnostics and logs.
  - Structured severity classification of `check_rag_consistency` findings (repairable/degraded vs fatal) with detection extensions for the fatal classes the checker currently lacks; startup validation acting on severity via the existing `pipeline.add_fatal`/`add_warning` mechanism.
  - ADR-010 trade-off amendment with an approval record (owner-approved 2026-10-29: identity observability and a fallback identity gate; corpus synchronization remains out of scope).
- **Out-of-Scope**:
  - Corpus synchronization, replication, or automatic repair of canonical corruption (ADR-010 Out of Scope line 94 preserved).
  - Changes to retrieval quality, ranking, or the existing fallback conditions themselves (ADR-010 INV-03 to INV-05 preserved; auth errors still do not fall back).
  - Unrelated refactoring or formatting-only changes.
- **Dependencies**:
  - `scripts/db/schema_sql.py` is shared with Frozen Plan `plans/20261029-214108_dbmig001_forward-only-db-migrations.md` (forward-only migration ledger) and Frozen Plan `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md` (Phase 4 DDL). Sequenced landing order: dbmig001 first (it builds the migration-registration framework); this Plan's `rag_corpus_meta` DDL registers through that framework afterwards; then toolexec001 or this Plan in either order with rebase. Recorded per `check_plan_target_overlaps.py` sequencing convention.
  - `docs/10_adr/adr_02_06_010_rag-fallback.md` amendment follows the ADR-authority placement reconciliation of `plans/20261029-214650_adrauth001_adr-authority-model.md` (adrauth001 defines where approval records and authority statements live; land adrauth001 first for the approval-record format).
  - `issues/20261029-104504_adrauth001_adr-authority-model.md` cited by the issue is now archived at `issues/done/` (issue citation is stale; relationship unchanged).

## Background
Source: `issues/20261029-104506_ragcorpus001_rag-corpus-identity.md`, adversarially re-verified against current source on 2026-10-30. Verified findings:

- ADR-010 documents the trade-off verbatim: "read their corpus from separately configured database paths (`rag_db_path`), which are identical by configuration convention only" (`docs/10_adr/adr_02_06_010_rag-fallback.md:60`) and "result consistency between the external RAG and the local RAG is not guaranteed" (`:77`, repeated in INV-09 `:169`). Rejection of the synchronized-corpus alternative is at `:126-131` ("to prioritize Availability and avoid the cost of corpus synchronization", `:130`).
- Correction: the re-evaluation trigger "the external RAG service using a corpus other than the local one" is in the Assumptions section "Items to re-evaluate if the assumptions no longer hold" (`:61`), not the Review Triggers section (`:252-265`).
- INV-05 (full pipeline re-execution on fallback) `:165`, INV-06 (result source tracked) `:166`; a Verification table with real test names (e.g. `test_in_process_fallback_sets_result_source_fallback`) exists at `:206-218`.
- No corpus ID, index generation, embedding-model ID, normalization version, or chunking-policy version exists in `scripts/rag/pipeline.py`, `scripts/rag/http_augment.py`, `scripts/rag/pipeline_service.py` (confirmed by absence search). Nuance: `schema_version` exists as ingestion-artifact metadata (`scripts/rag/ingestion/pipeline_utils.py` `IngestedChunk.schema_version`, `scripts/rag/ingestion/chunk_splitter.py:288`, `file_routing.py:105`) — it is not a corpus identity and is not persisted as such.
- `scripts/db/rag_consistency.py` severity is text-prefix only: `[WARNING]` FTS gap `:162`, vector count mismatch `:202`, documents without chunks `:213`; `[CRITICAL]` FTS orphan `:175`, orphan vector rows `:189`, chunks without vector rows `:224`, duplicate `chunk_index` `:238`. Issue omission corrected: a `[WARNING] URL-level inconsistency` finding also exists at `:248` and must be classified too. `RagConsistencyReport` (`scripts/db/models.py:75`) carries counts only, no severity field.
- Startup validation (`scripts/agent/startup_validation.py`): every consistency issue is downgraded — `pipeline.add_warning("rag_consistency", ...)` at `:174-176` (issue cited `:171-176`; `:171` is the `add_ok` branch); `TimeoutError` → `add_skipped` `:177-181`; unexpected `Exception` → `add_skipped` `:182-188` with `# noqa: BLE001` "non-critical maintenance check must not abort startup". `_classify_rag_failure` (`:31`) categorizes the exception but never escalates to fatal. The pipeline already supports `pipeline.add_fatal(...)` (used by routing_drift `:59`, readiness `:85/:99/:103`, mcp_tool_discovery `:127/:132`), so severity-aware behavior needs no new pipeline primitive.
- Detection-gap answer to the issue's open question: `scripts/db/rag_consistency.py` + `scripts/db/rag_consistency_queries.py` have no embedding-dimension check, no FK/foreign-key integrity check, no unknown-schema check, and no generation verification (absence search confirms). They detect only FTS/vector/chunk count relations, orphans, duplicates, URL-level mismatches, and documents-without-chunks.
- Config convention confirmed on both sides: `config/agent.toml:7 rag_db_path` and `config/rag_pipeline_mcp_server.toml:13 rag_db_path`. `docs/21_rag/rag_01_system_overview.md:180` states the paths are "same path by convention, not by an enforced invariant … silently diverge, undetected by any current automated check".
- No in-flight plan currently targets the RAG files (plans/ scan confirms); the only cross-plan collision is `scripts/db/schema_sql.py` (see Dependencies).

## Problem
A fallback can silently return results from a corpus that differs from the remote one in content, embedding model, normalization, or chunking, and nothing identifies which corpus produced a result (`docs/21_rag/rag_01_system_overview.md:180`: divergence is "undetected by any current automated check"). At startup, findings the checker itself marks `[CRITICAL]` are downgraded to warnings (`scripts/agent/startup_validation.py:174-176`), and a failed or timed-out check is recorded as skipped (`:177-188`), so a corrupted canonical corpus does not stop startup.

## Reason for Change
Corpus identity makes the accepted ADR-010 trade-off observable and lets a deployment reject or flag an incompatible fallback; severity-aware enforcement aligns startup behavior with the fail-fast policy for integrity failures (ADR-004 `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`). Priority Medium: the corpus mismatch is a documented, accepted limitation with no incident cited; the severity labels already exist as text, so the work improves guarantees rather than fixing an observed failure. Owner approved amending ADR-010's trade-off (observability + fallback gate, no synchronization) on 2026-10-29.

## Implementation Intent
Two independent deliverables, landed as separate reviewable phases per the issue's AI instruction:
1. Severity stream: replace text-prefix severity in `scripts/db/rag_consistency.py` with a structured classification attached to `RagConsistencyReport`, extend detection to the missing fatal classes (embedding-dimension mismatch, FK inconsistency, unknown schema, unverifiable generation), and make `scripts/agent/startup_validation.py` route fatal findings through the existing `pipeline.add_fatal` and repairable findings through `add_warning` with an explicit repair action.
2. Identity stream: define a corpus identity computed from the local RAG DB (meta table) plus config, expose it through the rag_pipeline MCP server health/response contract, compare remote vs local identity before accepting a fallback in `scripts/rag/pipeline.py`, record the selected generation in diagnostics/logs, and amend ADR-010 with the approval record. No synchronization protocol is introduced; identities are compared, never reconciled.

## Requirements
- `REQ-001`: Corpus identity fields defined: `corpus_id` (stable UUID generated at first schema creation), `index_generation` (monotonic integer bumped on each completed ingestion/rebuild), `schema_version`, `embedding_model_id`, `normalization_version`, `chunking_policy_version`; stored in a single-row `rag_corpus_meta` table in the RAG database.
- `REQ-002`: The remote RAG service computes and exposes its own identity from its own database/config through the health and search response contract (additive fields; existing fields preserved).
- `REQ-003`: Before a remote-to-local fallback result is accepted, the remote identity (from the response or health record) is compared with the local identity; a mismatch is handled per policy: reject (default) or explicitly degraded result; a missing identity on either side is treated as unverifiable and rejected for fallback acceptance.
- `REQ-004`: Every RAG result records the corpus generation used (diagnostics + logs), consistent with ADR-010 INV-06 result-source tracking.
- `REQ-005`: Structured severity classification replaces text prefixes: degraded/repairable = FTS gap, FTS orphan, vector count mismatch, orphan vector rows, chunks without vector rows, URL-level inconsistency, documents without chunks; fatal = duplicate `chunk_index` (canonical corruption), FK inconsistency (new check), embedding-dimension mismatch (new check), unknown schema (new check), unverifiable corpus generation (new check).
- `REQ-006`: Startup validation acts on severity: fatal findings call `pipeline.add_fatal` (startup aborts per ADR-004 Fail-Fast); degraded findings call `pipeline.add_warning` with the repair action named in the message. Fatal findings cannot be downgraded through configuration.
- `REQ-007`: A failed or timed-out consistency check marks the corpus as identity-unverified: the check itself stays non-fatal at startup (Availability trade-off), but the fallback gate refuses to accept fallback results while the local identity is unverifiable (fail-closed at the point of use).
- `REQ-008`: ADR-010 amended with the trade-off change and an approval record; mismatch behavior, identity contract, and severity classes documented in the RAG operations docs.
- `REQ-009`: Existing fallback conditions (ADR-010 INV-03 to INV-05) and the auth-error-no-fallback rule preserved; public RAG tool contracts extended only additively.
- `REQ-010`: The `rag_corpus_meta` DDL lands only through the dbmig001 forward-only migration ledger framework (no direct schema bypass), sequenced after dbmig001.

## Implementation Target Files
**Freeze status**: Frozen (Step 8 Implementation Target Files Validation passed on
2026-10-30: every row exists-or-is-new-with-evidence, is linked to a Plan requirement,
and is `Verified` against `HEAD c5a8285dd` — severity anchors `rag_consistency.py:162-248`
(incl. the corrected `:248` URL-level WARNING), the startup downgrade block
`startup_validation.py:160-188`, the existing `add_fatal` primitive (`:59/:85/:99`), the
fallback wiring `pipeline.py:128/:156/:245`, `CallRagResult` `:27`, `ResultSource`
`:21/:109`, and all doc anchors re-confirmed by direct read; `check_workitem_structure.py`
reports no findings; cross-plan pairs reported by `check_plan_target_overlaps.py` are
recorded sequenced in Dependencies.)

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

**Amendment (ragcorpus001, 2026-10-31):** the `index_generation` bump was mis-attributed to `rag_pipeline_server.py`, which performs no ingestion. The bump is relocated to `scripts/rag/ingestion/ingester.py::ingest_all()` — the sole ingestion completion point (`ingest_all()` `:142-200` opens the rag DB in write mode `:159-164` and returns the post-ingestion report at `:200`); `bump_index_generation()` is best-effort and leaves the previous generation in force on failure. Row 88's reason was corrected to identity exposure only, and the `ingester.py` row above was added with repository evidence and a REQ-001 link. The four Step 8 checks were re-run against `HEAD 18fa384c8`; the section remains Frozen.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/rag/corpus_identity.py | new | corpus identity dataclass, compute-from-DB+config, meta-table read/write, version constants for normalization/chunking policy | REQ-001, REQ-003, REQ-007 | new file; no corpus-identity symbol exists in `scripts/rag/` (absence search 2026-10-30) | tests/rag/test_corpus_identity.py | Verified |
| scripts/db/schema_sql.py | modify | add `rag_corpus_meta` single-row DDL next to the existing `chunks` DDL (`:38`) | REQ-001 | exists; `CREATE TABLE IF NOT EXISTS chunks` at `:38`; shared with Frozen dbmig001/toolexec001 plans (sequenced in Dependencies) | tests/db/test_rag_consistency.py | Verified |
| scripts/db/rag_consistency.py | modify | structured severity classification replacing `[WARNING]`/`[CRITICAL]` text prefixes; attach severity + repair action to findings | REQ-005, REQ-006 | exists; severity text prefixes at `:162`, `:175`, `:189`, `:202`, `:213`, `:224`, `:238`, `:248` | tests/db/test_rag_consistency.py | Verified |
| scripts/db/rag_consistency_queries.py | modify | new fatal-class detection queries: FK consistency (chunks→documents), embedding-dimension check, schema-recognition check | REQ-005 | exists; no dimension/FK/schema checks today (absence search 2026-10-30) | tests/db/test_rag_consistency.py | Verified |
| scripts/db/models.py | modify | `RagConsistencyReport` (`:75`): add structured severity/fatal-count fields so severity survives to callers without text parsing | REQ-005, REQ-006 | exists; report is counts-only `scripts/db/models.py:75-95` | tests/db/test_rag_consistency.py | Verified |
| scripts/agent/services/rag_maintenance_service.py | modify | `consistency()` (`:46`) exposes severity and repair actions in `RagConsistencyResult`; add corpus-meta ensure/read used by startup and the gate | REQ-005, REQ-006, REQ-007 | exists; `consistency()` `scripts/agent/services/rag_maintenance_service.py:46-54` | tests/agent/test_startup.py | Verified |
| scripts/agent/startup_validation.py | modify | severity-aware routing: fatal → `pipeline.add_fatal` (primitive exists, `:59/:85/:99`), degraded → `add_warning` with repair action; unverified-check state recorded | REQ-006, REQ-007 | exists; RAG block `:160-188` downgrades everything to warning/skipped | tests/agent/test_startup.py, tests/agent/test_startup_severity_classification.py | Verified |
| scripts/rag/pipeline.py | modify | fallback gate: compare remote vs local identity before accepting fallback (`augment` `:197`, HTTP mode dispatch `:216-245`); record selected generation | REQ-003, REQ-004, REQ-009 | exists; stage status `Literal["success","fallback","failure"]` `:128/:156`, `run_http_augment` call `:245` | tests/rag/test_rag_http_mode.py | Verified |
| scripts/rag/augment.py | modify | `run_http_augment` (`:69`) passes remote identity through to the gate | REQ-003 | exists; `scripts/rag/augment.py:69` | tests/rag/test_rag_http_mode.py | Verified |
| scripts/rag/http_augment.py | modify | parse identity fields from the remote response/health payload (`run` `:100`) | REQ-002, REQ-003 | exists; `scripts/rag/http_augment.py:100` | tests/rag/test_rag_http_mode.py | Verified |
| scripts/rag/pipeline_service.py | modify | `CallRagResult` (`:27`): additive identity fields for the delegation outcome | REQ-002, REQ-003 | exists; `CallRagResult` `scripts/rag/pipeline_service.py:27-39` | tests/rag/test_rag_pipeline_service.py | Verified |
| scripts/rag/models_result.py | modify | result/diagnostics model (`ResultSource` `:21`, `result_source` `:109`): additive corpus-generation field | REQ-004 | exists; `scripts/rag/models_result.py:21,109` | tests/rag/test_pipeline_http_result_kind.py | Verified |
| scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py | modify | expose server-side identity on health and search response (additive) | REQ-001, REQ-002 | exists; server process owns its own `rag_db_path` (`config/rag_pipeline_mcp_server.toml:13`) | tests/rag/test_rag_http_mode.py | Verified |
| scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py | modify | `RagRunResponse` (`:253`): additive `corpus_identity` wire field so the search response carries the server identity; `RagDebugResponse` inherits it | REQ-002 | exists; `RagRunResponse` `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py:253-263`; Pydantic v2 `BaseModel` — an undefined field cannot be serialized, so the field must be declared | tests/rag/test_rag_http_mode.py | Verified |
| scripts/rag/ingestion/ingester.py | modify | bump `index_generation` after a completed `ingest_all()` run (best-effort; a failure leaves the previous generation in force) | REQ-001 | exists; `ingest_all()` `scripts/rag/ingestion/ingester.py:142-200` opens the rag DB in write mode (`:159-164`) and returns the post-ingestion consistency report at `:200` | tests/rag/test_ingester_index_generation.py (new) | Verified |
| config/agent.toml | modify | new RAG identity policy key (`rag_identity_mismatch_policy`, default `reject`; `degraded` only by explicit approval); no change to `rag_db_path` (`:7`) | REQ-003, REQ-006 | exists; `config/agent.toml:7` is the convention-side path | tests/rag/test_rag_http_mode.py | Verified |
| tests/rag/test_corpus_identity.py | new | unit tests: identity computation, meta-table round-trip, missing/unverifiable identity | REQ-001, REQ-007 | new file | — | Verified |
| tests/rag/test_rag_http_mode.py | modify | integration matrix: identity match, mismatch × policy (reject/degraded), missing identity on either side, auth-error no-fallback regression | REQ-003, REQ-009 | exists; HTTP-mode fallback tests live here (churn 30d = 2) | — | Verified |
| tests/rag/test_rag_pipeline_service.py | modify | `CallRagResult` identity-field contract tests | REQ-002 | exists | — | Verified |
| tests/rag/test_pipeline_http_result_kind.py | modify | recorded generation on each result kind | REQ-004 | exists | — | Verified |
| tests/db/test_rag_consistency.py | modify | severity unit tests for every degraded class and every fatal class incl. new checks | REQ-005, REQ-006 | exists | — | Verified |
| tests/agent/test_startup.py | modify | startup behavior per severity: fatal aborts, degraded warns with repair action, timeout marks unverified (not fatal) | REQ-006, REQ-007 | exists | — | Verified |
| tests/agent/test_startup_severity_classification.py | modify | extend severity-classification coverage to the RAG findings stream | REQ-005, REQ-006 | exists | — | Verified |
| docs/10_adr/adr_02_06_010_rag-fallback.md | modify | trade-off amendment: identity contract + fallback gate as new invariants, Approval Record entry; Out of Scope synchronization line (`:94`) and Alternative C rejection (`:126-131`) preserved | REQ-008 | exists; `:60/:77/:94/:126-131/:165-169` anchors verified 2026-10-30 | check_adr_structure/preservation via docs gates | Verified |
| docs/21_rag/rag_01_system_overview.md | modify | replace the "undetected divergence" statement (`:180`) with the identity-comparison contract and mismatch behavior | REQ-008 | exists; `:180` verified | docs consistency checkers | Verified |
| docs/21_rag/rag_05_07-rag-index-consistency-checks.md | modify | severity classes, new fatal checks, startup consequences and repair actions | REQ-008 | exists; startup-warning description at `:22-28` must be updated | docs consistency checkers | Verified |
| docs/21_rag/rag_05_01-configuration-reference.md | modify | document `rag_identity_mismatch_policy` key | REQ-008 | exists; config-reference doc (`:93` covers RAG config surface) | docs consistency checkers | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md | ADR-004 Fail-Fast criteria and Fail-Fast list (`:76-85`) ground the fatal-severity routing | REQ-006, `scripts/agent/startup_validation.py` |
| scripts/mcp_servers/rag_pipeline/rag_pipeline_health_probe.py | current health-probe shape (`_run_probe` `:53`) the identity fields must extend additively | REQ-002, `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` |
| scripts/rag/diagnostics.py | diagnostics surface where the selected generation is recorded | REQ-004, `scripts/rag/models_result.py` |
| scripts/rag/ingestion/pipeline_utils.py | `IngestedChunk` metadata incl. `schema_version` (`:238` region) — reuse, do not duplicate, version semantics | REQ-001, `scripts/rag/corpus_identity.py` |
| scripts/db/create_schema.py | schema creation path where `corpus_id` generation must hook in | REQ-001, `scripts/db/schema_sql.py` |
| config/rag_pipeline_mcp_server.toml | server-side `rag_db_path` (`:13`); identity is computed from the server's own DB | REQ-002, `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` |
| scripts/rag/stages/augment.py | augment/refiner stage wiring around the fallback decision point | REQ-003, `scripts/rag/pipeline.py` |
| docs/21_rag/rag_05_05-constraints-reference.md | existing RAG constraint statements (`:29-30`) the identity contract must not contradict | REQ-008, docs rows |

## Acceptance Criteria
- AC-1 (REQ-003, REQ-007): Fallback never silently switches to an unidentified or incompatible corpus; mismatch behavior is deterministic (reject default) and documented.
- AC-2 (REQ-004): Every RAG result identifies the corpus generation used (diagnostics and logs).
- AC-3 (REQ-006): Canonical-data integrity failures abort startup via `add_fatal`; derived-index failures produce an observable degraded state with a named repair action.
- AC-4 (REQ-006): No configuration can downgrade a fatal finding.
- AC-5 (REQ-002, REQ-009): Remote identity is exposed additively; all pre-existing request/response fields and fallback conditions (incl. auth-error no-fallback) are unchanged.
- AC-6 (REQ-008): ADR-010 carries the amendment and approval record; RAG operations docs state the identity contract, mismatch behavior, and severity classes with startup consequences.

## Tests
- Unit (REQ-001, REQ-003, REQ-007): `tests/rag/test_corpus_identity.py` — identity computation, meta-table round-trip, missing/unverifiable identity handling.
- Unit (REQ-005, REQ-006): `tests/db/test_rag_consistency.py` — every degraded class, every fatal class incl. the three new checks; `tests/agent/test_startup_severity_classification.py` extended.
- Integration (REQ-003, REQ-009): `tests/rag/test_rag_http_mode.py` — identity match, mismatch × each policy, missing identity on either side, timeout/unverified state blocks fallback, auth-error no-fallback regression.
- Integration (REQ-002, REQ-004): `tests/rag/test_rag_pipeline_service.py`, `tests/rag/test_pipeline_http_result_kind.py` — additive contract fields and recorded generation per result kind.
- Startup (REQ-006, REQ-007): `tests/agent/test_startup.py` — fatal aborts startup, degraded warns with repair action, check failure marks unverified without aborting.
- Suite commands: `uv run pytest tests/rag tests/agent tests/db`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `uv run python tools/check_docs_consistency.py --domain rag`.

## Documentation Impact
Yes. Per `docs/00_index.md` task-scope mapping (RAG + ADR rows): ADR-010 amendment with approval record (REQ-008), `docs/21_rag/rag_01_system_overview.md` identity contract replacing the undetected-divergence statement (REQ-008), `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` severity classes and startup consequences (REQ-005/REQ-006), `docs/21_rag/rag_05_01-configuration-reference.md` for the new policy key (REQ-003). Intent, boundaries, and failure behavior only (`skills/DESIGN.md` Docs content policy).

## Assumptions
- `corpus_id` is generated once at first RAG schema creation and never regenerated; a DB restored from a copy carries its meta table along.
- `embedding_model_id` is read from configuration (the embedder selection), not inferred from vector contents; `normalization_version` and `chunking_policy_version` are module-level version constants bumped by policy when those behaviors change.
- The remote RAG service learns its identity from its own database and config (same schema convention); no new cross-process registration channel is built.
- Mismatch policy default `reject` is the fail-closed interpretation of the owner-approved amendment; `degraded` is only reachable through explicit `config/agent.toml` approval.
- `index_generation` bump is best-effort at ingestion completion; a crash mid-ingestion leaves the previous generation recorded (identity reflects published state only).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether `degraded` acceptance should ever be allowed in production or reserved for staging | No operational precedent on record | Default `reject`; owner confirms before enabling `degraded` in any deployment | False |
| UNK-02 | Maximum acceptable startup time for the extended consistency checks (new fatal checks add queries to the existing 30s timeout window at `scripts/agent/startup_validation.py:164-170`) | No query-cost measurement for FK/dimension checks on production corpus size | Measure during Phase 1; adjust check ordering or timeout if needed | False |
| UNK-03 | Whether the health endpoint identity payload should be cached by the probe (`reset_cache` exists at `rag_pipeline_health_probe.py:33`) | No staleness requirement stated | Assumption: cache identity with the same TTL as current probe cache; revisit if staleness causes false rejections | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here is a subset of `Implementation Target Files`' rows.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/db/schema_sql.py | add `rag_corpus_meta` DDL | RAG DB schema; shared target with dbmig001/toolexec001 | 11 | 4 | No (no new service); DB init path affected |
| scripts/agent/startup_validation.py | severity-aware routing incl. new fatal path | startup gate for the agent service | 6 | 2 | Service restart required on deploy |
| scripts/rag/pipeline.py | fallback identity gate | every HTTP-mode RAG request path | 2 | 4 | No |
| scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py | identity exposure + generation bump | rag_pipeline MCP server contract | 5 | 3 | rag_pipeline service restart |
| config/agent.toml | new policy key | agent config surface | 9 | 3 | Config sync on deploy |
| scripts/db/rag_consistency.py | structured severity | consistency-check consumers | 5 | 2 | No |
| scripts/db/rag_consistency_queries.py | new fatal checks | startup check duration | 1 | 1 | No |
| scripts/rag/http_augment.py | identity parsing | HTTP fallback path | 3 | 3 | No |
| scripts/rag/pipeline_service.py | additive result fields | delegation contract | 1 | 4 | No |
| scripts/rag/models_result.py | additive generation field | result/diagnostics contract | 0 | 4 | No |
| scripts/rag/augment.py | identity passthrough | augment wiring | 1 | 2 | No |
| scripts/db/models.py | report severity fields | db models consumers | 0 | 3 | No |
| scripts/agent/services/rag_maintenance_service.py | severity + meta access | maintenance API | 0 | 3 | No |
| scripts/rag/corpus_identity.py | new module | new surface only | 0 | new (2 owners planned) | No |
| tests/agent/test_startup.py | severity behavior tests | startup test surface | 7 | 2 | No |
| tests/rag/test_rag_http_mode.py | fallback matrix | RAG HTTP test surface | 2 | 2 | No |

## Design
- Severity model (Phase 1). `RagConsistencyReport` gains a structured severity classification (per-finding severity enum + repair-action string) computed in `scripts/db/rag_consistency.py`; the `[WARNING]`/`[CRITICAL]` text prefixes remain only inside the human-readable message body. Classification is fixed in code, not configuration (AC-4). New fatal checks (FK consistency chunks→documents, embedding dimension vs configured dimension, unknown schema shape, corpus-meta presence) are added to `scripts/db/rag_consistency_queries.py`. `scripts/agent/startup_validation.py` routes: any fatal → `pipeline.add_fatal("rag_consistency", ...)` (existing primitive; aborts per ADR-004); degraded-only → `pipeline.add_warning` with the repair action; check timeout/exception → warning "identity-unverified" (not fatal) — fail-closed is enforced at the fallback gate instead (REQ-007), keeping the documented Availability trade-off.
- Identity model (Phase 2). `rag_corpus_meta` single-row table (corpus_id TEXT, index_generation INTEGER, embedding_model_id TEXT, normalization_version TEXT, chunking_policy_version TEXT, updated_at) created through the dbmig001 migration framework in `scripts/db/schema_sql.py`. `scripts/rag/corpus_identity.py` computes the effective identity = meta row + current `schema_version` + `rag_db_path` presence; missing/corrupt meta → identity-unverified. The rag_pipeline server exposes identity in its health payload and as an additive field on search responses; `scripts/rag/corpus_identity.py` is imported by the server process (shared library convention, same as `dispatch_tool`).
- Fallback gate (Phase 3). In `scripts/rag/pipeline.py`, when the HTTP path returns a fallback-triggering outcome, the gate compares remote identity (carried in `CallRagResult`/response via `scripts/rag/http_augment.py`, `scripts/rag/pipeline_service.py`, `scripts/rag/augment.py`) against local identity before executing the local re-run (INV-05 preserved: the pipeline still fully re-executes locally; the gate decides whether the local result is labeled `fallback` or the request is rejected). Policy from `config/agent.toml`: `reject` (default) → return failure outcome with reason `identity_mismatch`; `degraded` → return the local result but mark it degraded in `scripts/rag/models_result.py` and log. Auth-error path untouched (no fallback, no gate involvement). Every accepted result records `corpus_generation` in diagnostics (`REQ-004`, extending INV-06's result-source tracking).
- ADR amendment (Phase 4). ADR-010 Decision/Invariants amended: identity comparison before fallback acceptance becomes an invariant; "consistency not guaranteed" reworded to "consistency is verified by identity comparison; mismatch behavior is policy-defined"; Approval Record extended with the 2026-10-29 owner decision. Out-of-Scope synchronization and Alternative C rejection text preserved verbatim. Follows the approval-record placement conventions adrauth001 establishes (`plans/20261029-214650_adrauth001_adr-authority-model.md`).

## Implementation steps
1. **Phase 1: Severity classification (independent of ADR change)**
   - [ ] Add severity fields to `RagConsistencyReport` (REQ-005; `scripts/db/models.py`)
   - [ ] Replace text-prefix severity with structured classification + repair actions in `check_rag_consistency` (REQ-005; `scripts/db/rag_consistency.py`)
   - [ ] Add fatal-class detection queries: FK consistency, embedding dimension, unknown schema (REQ-005; `scripts/db/rag_consistency_queries.py`)
   - [ ] Expose severity and repair actions through `RagConsistencyResult` (REQ-006; `scripts/agent/services/rag_maintenance_service.py`)
   - [ ] Route severity in startup: fatal → `add_fatal`, degraded → `add_warning` w/ repair action, check failure → unverified warning (REQ-006, REQ-007; `scripts/agent/startup_validation.py`)
   - [ ] Unit/startup tests for every severity class (REQ-005, REQ-006; `tests/db/test_rag_consistency.py`, `tests/agent/test_startup.py`, `tests/agent/test_startup_severity_classification.py`)
2. **Phase 2: Corpus identity storage and exposure**
   - [ ] `rag_corpus_meta` DDL registered through the dbmig001 migration framework (REQ-001; `scripts/db/schema_sql.py`)
   - [ ] Implement identity module: compute, ensure-meta-at-startup, version constants (REQ-001; `scripts/rag/corpus_identity.py`)
   - [ ] `corpus_id` generation hook at schema creation (REQ-001; `scripts/db/create_schema.py` behavior consumed; implementation via `scripts/rag/corpus_identity.py` + `scripts/agent/services/rag_maintenance_service.py`)
   - [ ] Server identity exposure on health + search response; `index_generation` bump at ingestion completion (REQ-002; `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`)
   - [ ] Identity unit tests (REQ-001, REQ-007; `tests/rag/test_corpus_identity.py`)
3. **Phase 3: Fallback identity gate and generation recording**
   - [ ] Additive identity fields on `CallRagResult` (REQ-002; `scripts/rag/pipeline_service.py`)
   - [ ] Parse remote identity (REQ-002, REQ-003; `scripts/rag/http_augment.py`) and pass through augment wiring (REQ-003; `scripts/rag/augment.py`)
   - [ ] Implement gate in the fallback decision path with policy lookup `rag_identity_mismatch_policy` (REQ-003; `scripts/rag/pipeline.py`, `config/agent.toml`)
   - [ ] Record selected generation in result/diagnostics (REQ-004; `scripts/rag/models_result.py`)
   - [ ] Integration matrix tests incl. auth-error regression (REQ-003, REQ-009; `tests/rag/test_rag_http_mode.py`, `tests/rag/test_rag_pipeline_service.py`, `tests/rag/test_pipeline_http_result_kind.py`)
4. **Phase 4: ADR amendment and documentation**
   - [ ] Amend ADR-010 with approval record (REQ-008; `docs/10_adr/adr_02_06_010_rag-fallback.md`)
   - [ ] Update RAG operations docs: identity contract, severity classes, policy key (REQ-008; `docs/21_rag/rag_01_system_overview.md`, `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`, `docs/21_rag/rag_05_01-configuration-reference.md`)
5. **Phase 5: Deployment & verification**
   - [ ] Full validation sequence: `uv run pytest tests/rag tests/agent tests/db`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `uv run python tools/check_docs_consistency.py --domain rag`, `ruff`/`bandit` per `rules/toolchain.md` (all REQs; deploy.sh unchanged — verify deployed files current per `skills/deploy`)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/db/rag_consistency.py + queries | Unit, per severity class incl. new fatal checks | `uv run pytest tests/db/test_rag_consistency.py` | Every finding carries structured severity; fatal classes detected |
| scripts/agent/startup_validation.py | Integration via startup test harness | `uv run pytest tests/agent/test_startup.py tests/agent/test_startup_severity_classification.py` | Fatal aborts startup; degraded warns with repair action; check failure = unverified, not fatal |
| scripts/rag/pipeline.py + http chain | Integration matrix (match/mismatch×policy/missing/timeout) | `uv run pytest tests/rag/test_rag_http_mode.py tests/rag/test_rag_pipeline_service.py tests/rag/test_pipeline_http_result_kind.py` | No silent mismatched fallback; generation recorded; auth-error behavior unchanged |
| scripts/rag/corpus_identity.py | Unit | `uv run pytest tests/rag/test_corpus_identity.py` | Stable identity across restarts; unverified state on corrupt meta |
| docs/10_adr/adr_02_06_010_rag-fallback.md + docs/21_rag/* | Docs checkers | `uv run python tools/check_docs_consistency.py --domain rag`, `check_adr_structure.py`, `check_adr_preservation.py` | Amendment preserved; no stale doc claims left |
| scripts/db/schema_sql.py | Migration registration test | `uv run pytest tests/db` (equivalence tests per dbmig001 framework) | `rag_corpus_meta` created only through the forward-only ledger |

## Risks
- **Risk**: shared `scripts/db/schema_sql.py` edits collide with dbmig001/toolexec001 → **Mitigation**: sequenced landing (dbmig001 first; this Plan registers through its framework); overlap recorded in both plans' Dependencies.
- **Risk**: new fatal checks abort startup on corpora that today pass with silent drift → **Mitigation**: Phase 1 lands severity detection first with the severity map reviewed against a production corpus snapshot before enabling the fatal path; ADR-004 already classifies integrity failures as Fail-Fast.
- **Risk**: identity gate rejects fallback on an old remote server that predates identity exposure → **Mitigation**: missing remote identity is treated as unverifiable → default policy rejects fallback acceptance with an explicit, logged reason (fail-closed by design); rolling upgrade documented in the ADR amendment.
- **Risk**: `index_generation` bump fails mid-ingestion leaving stale generation → **Mitigation**: bump happens only after a completed ingestion; failures leave the previous generation in force and mark the corpus unverified for gate purposes.
- **Risk**: severity reclassification changes test expectations broadly (`tests/agent/test_startup.py` churn 7/30d) → **Mitigation**: Phase 1 is self-contained and lands before any identity work.

## Execution Status
| Phase | Status | Procedure Docs |
|---|---|---|
| Phase 1 | procedure generated | 20261030-140156_03, _04, _05, _06, _07 (checker/queries/report/maintenance/startup), _19, _20, _21 (tests) |
| Phase 2 | procedure generated | 20261030-140156_01 (corpus_identity), _02 (schema), _13 (server exposure), _15 (identity tests) |
| Phase 3 | procedure generated | 20261030-140156_08, _09, _10, _11, _12 (gate + plumbing), _14 (policy key), _16, _17, _18 (tests) |
| Phase 4 | procedure generated | 20261030-140156_22 (ADR-010), _23, _24, _25 (RAG docs) |
| Phase 5 | validation only, no target file | — (deployment/verification gates run at implementation time) |

## Blocker Log
| Item | Detail | Status |
|---|---|---|
| UNK-01 policy default | `degraded` acceptance in production is unconfirmed; default `reject` everywhere until the owner confirms (docs 14, 25) | open — Needs Confirmation before implementation |
| UNK-02 check duration | Query cost of the new fatal checks against the 30s startup window is unmeasured; measure during Phase 1 implementation (docs 04, 07) | open — measure at implementation |
| UNK-03 identity cache | Health-probe identity caching assumes the current probe-cache TTL (`rag_pipeline_health_probe.py` :33/:53); revisit if staleness causes false rejections (doc 13) | open — assumption recorded |
| Frozen-table gap (doc 12) | Recording the generation on results may reach `to_dict` in `scripts/rag/diagnostics.py`, a file not in the frozen table; raise and register before editing it | open — Needs Confirmation before implementation |
| schema_sql.py sequencing | Doc 02 must land after the dbmig001 implementation lands (REQ-010: registration through its forward-only migration ledger); do not edit `schema_sql.py` from this plan first | recorded in doc 02 |

## Work Items Created
| Item ID | Target File | Phase |
|---|---|---|
| 20261030-140156_01_scripts_rag_corpus_identity.py.md | scripts/rag/corpus_identity.py | Phase 2 |
| 20261030-140156_02_scripts_db_schema_sql.py.md | scripts/db/schema_sql.py | Phase 2 |
| 20261030-140156_03_scripts_db_rag_consistency.py.md | scripts/db/rag_consistency.py | Phase 1 |
| 20261030-140156_04_scripts_db_rag_consistency_queries.py.md | scripts/db/rag_consistency_queries.py | Phase 1 |
| 20261030-140156_05_scripts_db_models.py.md | scripts/db/models.py | Phase 1 |
| 20261030-140156_06_scripts_agent_services_rag_maintenance_service.py.md | scripts/agent/services/rag_maintenance_service.py | Phase 1 |
| 20261030-140156_07_scripts_agent_startup_validation.py.md | scripts/agent/startup_validation.py | Phase 1 |
| 20261030-140156_08_scripts_rag_pipeline.py.md | scripts/rag/pipeline.py | Phase 3 |
| 20261030-140156_09_scripts_rag_augment.py.md | scripts/rag/augment.py | Phase 3 |
| 20261030-140156_10_scripts_rag_http_augment.py.md | scripts/rag/http_augment.py | Phase 3 |
| 20261030-140156_11_scripts_rag_pipeline_service.py.md | scripts/rag/pipeline_service.py | Phase 3 |
| 20261030-140156_12_scripts_rag_models_result.py.md | scripts/rag/models_result.py | Phase 3 |
| 20261030-140156_13_scripts_mcp_servers_rag_pipeline_rag_pipeline_server.py.md | scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py | Phase 2 |
| 20261030-140156_14_config_agent.toml.md | config/agent.toml | Phase 3 |
| 20261030-140156_15_tests_rag_test_corpus_identity.py.md | tests/rag/test_corpus_identity.py | Phase 2 |
| 20261030-140156_16_tests_rag_test_rag_http_mode.py.md | tests/rag/test_rag_http_mode.py | Phase 3 |
| 20261030-140156_17_tests_rag_test_rag_pipeline_service.py.md | tests/rag/test_rag_pipeline_service.py | Phase 3 |
| 20261030-140156_18_tests_rag_test_pipeline_http_result_kind.py.md | tests/rag/test_pipeline_http_result_kind.py | Phase 3 |
| 20261030-140156_19_tests_db_test_rag_consistency.py.md | tests/db/test_rag_consistency.py | Phase 1 |
| 20261030-140156_20_tests_agent_test_startup.py.md | tests/agent/test_startup.py | Phase 1 |
| 20261030-140156_21_tests_agent_test_startup_severity_classification.py.md | tests/agent/test_startup_severity_classification.py | Phase 1 |
| 20261030-140156_22_docs_10_adr_adr_02_06_010_rag-fallback.md | docs/10_adr/adr_02_06_010_rag-fallback.md | Phase 4 |
| 20261030-140156_23_docs_21_rag_rag_01_system_overview.md | docs/21_rag/rag_01_system_overview.md | Phase 4 |
| 20261030-140156_24_docs_21_rag_rag_05_07-rag-index-consistency-checks.md | docs/21_rag/rag_05_07-rag-index-consistency-checks.md | Phase 4 |
| 20261030-140156_25_docs_21_rag_rag_05_01-configuration-reference.md | docs/21_rag/rag_05_01-configuration-reference.md | Phase 4 |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261029-104506_ragcorpus001_rag-corpus-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261030-013620
- **Related target files**: `scripts/rag/corpus_identity.py`, `scripts/db/schema_sql.py`, `scripts/db/rag_consistency.py`, `scripts/db/rag_consistency_queries.py`, `scripts/db/models.py`, `scripts/agent/services/rag_maintenance_service.py`, `scripts/agent/startup_validation.py`, `scripts/rag/pipeline.py`, `scripts/rag/augment.py`, `scripts/rag/http_augment.py`, `scripts/rag/pipeline_service.py`, `scripts/rag/models_result.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, `config/agent.toml`, `tests/rag/test_corpus_identity.py`, `tests/rag/test_rag_http_mode.py`, `tests/rag/test_rag_pipeline_service.py`, `tests/rag/test_pipeline_http_result_kind.py`, `tests/db/test_rag_consistency.py`, `tests/agent/test_startup.py`, `tests/agent/test_startup_severity_classification.py`, `docs/10_adr/adr_02_06_010_rag-fallback.md`, `docs/21_rag/rag_01_system_overview.md`, `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`, `docs/21_rag/rag_05_01-configuration-reference.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes; owner decision 2026-10-29 | `scripts/rag/corpus_identity.py`, `scripts/db/schema_sql.py` | Phase 2 | AC-2 | `tests/rag/test_corpus_identity.py` | Confirmed by owner decision |
| REQ-002 | Required Changes | `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, `scripts/rag/pipeline_service.py` | Phase 2-3 | AC-5 | `tests/rag/test_rag_pipeline_service.py` | Explicit in issue |
| REQ-003 | Required Changes; Constraints | `scripts/rag/pipeline.py`, `scripts/rag/http_augment.py`, `scripts/rag/augment.py`, `config/agent.toml` | Phase 3 | AC-1 | `tests/rag/test_rag_http_mode.py` | Explicit in issue |
| REQ-004 | Required Changes; ADR-010 INV-06 (`:166`) | `scripts/rag/models_result.py` | Phase 3 | AC-2 | `tests/rag/test_pipeline_http_result_kind.py` | Explicit in issue |
| REQ-005 | Required Changes; severity anchors `:162-:248` incl. corrected `:248` URL-level WARNING | `scripts/db/rag_consistency.py`, `scripts/db/rag_consistency_queries.py`, `scripts/db/models.py` | Phase 1 | AC-3 | `tests/db/test_rag_consistency.py` | Explicit in issue + verified 2026-10-30 |
| REQ-006 | Required Changes; `startup_validation.py:174-188` downgrades; `add_fatal` primitive exists `:59/:85` | `scripts/agent/startup_validation.py`, `scripts/agent/services/rag_maintenance_service.py` | Phase 1 | AC-3, AC-4 | `tests/agent/test_startup.py`, `tests/agent/test_startup_severity_classification.py` | Explicit in issue + verified 2026-10-30 |
| REQ-007 | Problem (timeout/skip gap, `:177-188`) | `scripts/agent/startup_validation.py`, `scripts/rag/pipeline.py` | Phase 1, 3 | AC-1 | `tests/rag/test_rag_http_mode.py` | Derived from confirmed evidence |
| REQ-008 | Documentation Impact; owner approval 2026-10-29 | `docs/10_adr/adr_02_06_010_rag-fallback.md`, `docs/21_rag/rag_01_system_overview.md`, `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`, `docs/21_rag/rag_05_01-configuration-reference.md` | Phase 4 | AC-6 | docs checkers | Confirmed by owner decision |
| REQ-009 | Constraints | `scripts/rag/pipeline.py`, `tests/rag/test_rag_http_mode.py` | Phase 3 | AC-5 | auth-error no-fallback regression | Explicit in issue |
| REQ-010 | Dependencies (dbmig001 sequencing, schema_sql.py overlap) | `scripts/db/schema_sql.py` | Phase 2 | AC-3 | `tests/db` migration equivalence tests | Derived from confirmed evidence |
