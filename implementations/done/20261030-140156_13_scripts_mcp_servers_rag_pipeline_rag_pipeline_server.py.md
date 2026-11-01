# Implementation Procedure: `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` (RAGCORPUS001 Phase 2)

**Plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` (REQ-001, REQ-002)

## Goal
Expose the server's own corpus identity on the health and search responses (additive).
`index_generation` bump on ingestion completion is out of scope for this procedure (REQ-001
is handled by the paired `ingester.py` procedure — this server performs no ingestion).

## Scope
- Health route GET /health at `:245-250` via `make_health_response` (import `:36`);
  `_check_health_deps` `:216`; probe import block `:235`
  (`rag_pipeline_health_probe.py` — Reference Files only: `_run_probe` `:53`,
  `reset_cache` `:33`).
- Search routes POST `/rag_run_pipeline` `:182` and POST `/rag_debug_pipeline` `:199`;
  their response envelope is `RagRunResponse` (`scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py:253`),
  which gains the additive `corpus_identity` field by the paired `rag_pipeline_models.py`
  edit — this module sets that field on the returned instance after the service returns.
- `RAG_PIPELINE_SERVER_KEY` `:70`, `RAG_PIPELINE_OWN_CONFIG_FILE` `:71`; server owns its
  `rag_db_path` (`config/rag_pipeline_mcp_server.toml:13` — Reference Files row).
- `class RagPipelineMCPServer` `:304`; `_enforce_posture_gate` `:319`.

## Assumptions
- Recorded open items:
  - UNK-03 (probe cache for identity payload): RESOLVED — no cache; `_identity_payload()`
    opens a short-lived read-only connection per call. Identity is cheap and correct;
    caching is a later optimization if profiling shows the read path is hot.
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.
- `embedding_model_id` is NOT chosen by an embedder-selection step (none exists in this
  codebase); it is read back from the `rag_corpus_meta` row via
  `compute_local_identity()` (doc 01 / `identity_gate.py`). `schema_version` is the
  module constant `SCHEMA_VERSION` (`pipeline.py:60`), passed as the caller-supplied arg.

## Design decisions
- `_identity_payload()` (new, module level): opens a short-lived read-only connection to
  the server's own `rag_db_path`, calls `rag.identity_gate.compute_local_identity(db,
  schema_version=SCHEMA_VERSION)`, and returns the seven-field wire dict
  (`corpus_id`, `index_generation`, `schema_version`, `embedding_model_id`,
  `normalization_version`, `chunking_policy_version`, `verified`). A missing/unreadable
  corpus yields an unverified dict (all-empty except `schema_version`/`index_generation=0`,
  `verified=false`) — never omitted — so callers always see the shape (REQ-002). The read
  fails closed (unverified dict) rather than raising, mirroring the pipeline gate.
- Health response: `corpus_identity` attached as an additive member of the `details`
  dict assembled at `:248` before `make_health_response(...)` at `:250`; `make_health_response`
  forwards the extra dict key (existing additive pattern; not a target row).
- Search response: `corpus_identity` set on the returned `RagRunResponse` instance in both
  `/rag_run_pipeline` (`:182`) and `/rag_debug_pipeline` (`:199`) after the service returns;
  `rag_pipeline_models.py` declares the additive field (paired edit). All pre-existing
  fields unchanged (AC-5). `RagDebugResponse` inherits the field.
- No ingestion bump here (out of scope; REQ-001 handled by the paired `ingester.py`
  procedure).

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. Add `_identity_payload()` at module level (near `_rag_security_view` `:74`). Import
   `SQLiteHelper` from `db.helper` and `compute_local_identity` from `rag.identity_gate`
   lazily inside the function (avoid top-level rag/db import cost); `SCHEMA_VERSION` from
   `rag.pipeline`. Open a read-only connection, compute, close, return the wire dict.
2. Wire it into health: set `details["corpus_identity"] = _identity_payload()` in
   `health()` at `:248` before `make_health_response(...)`.
3. Wire it into search: in `/rag_run_pipeline` (`:182`) and `/rag_debug_pipeline` (`:199`),
   set `result.corpus_identity = _identity_payload()` on the returned `RagRunResponse`
   after the service call. `rag_pipeline_models.py` (paired edit) declares the field.

## Compatibility considerations
**Dependencies**: upstream: doc 01 (identity module — shared-library import convention,
**Blocks**: docs 10, 11, 16

## Security considerations
- No new security surface beyond what the Source plan records.

## Rollback considerations
- Revert this file together with its paired test rows in the same commit; the change is additive and gated by the plan's checkers.

- Health payload carries `corpus_identity`; search `RagRunResponse` carries `corpus_identity`
  (inherited by `RagDebugResponse`); all pre-existing fields unchanged; an unverified corpus
  still emits the shape with `verified=false`.
  end-to-end against a stubbed server payload).

## Completion criteria
- Health and search payloads both carry the identity; an old-format test client sees all
  pre-existing fields unchanged; generation increments only on completed ingestion.

## Out of Scope
- Everything outside the target file and the anchors recorded above; cross-plan boundaries and sequencing are recorded in the Source plan.

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-verify cited anchors before editing | Completed | — | — |  |
| 2 | UNK-03 (probe cache for identity payload): RESOLVED — no cache required; per-call read-only connection | Completed | — | 2026-10-31 |  |
| 3 | Run the Validation plan gates | Completed | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2 | UNK-03 (probe cache for identity payload): Needs Confirmation — proposed: cache with | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `20261030-140156_01_scripts_rag_corpus_identity.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- `(new)` markers applied: `_identity_payload` (Contract section).

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: `issues/20261029-104506_ragcorpus001_rag-corpus-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` — Implementation Target Files row 13
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-140156
- **Related target files**: `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`