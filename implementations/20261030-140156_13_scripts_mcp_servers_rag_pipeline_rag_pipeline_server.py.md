# Implementation Procedure: `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` (RAGCORPUS001 Phase 2)

**Plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` (REQ-001, REQ-002)

## Goal
Expose the server's own corpus identity on the health and search responses (additive)
and bump `index_generation` when an ingestion completes.

## Scope
- Health route GET /health at `:245-250` via `make_health_response` (import `:36`);
  `_check_health_deps` `:216`; probe import block `:235`
  (`rag_pipeline_health_probe.py` — Reference Files only: `_run_probe` `:53`,
  `reset_cache` `:33`).
- `RAG_PIPELINE_SERVER_KEY` `:70`, `RAG_PIPELINE_OWN_CONFIG_FILE` `:71`; server owns its
  `rag_db_path` (`config/rag_pipeline_mcp_server.toml:13` — Reference Files row).
- `class RagPipelineMCPServer` `:304`; `_enforce_posture_gate` `:319`.

## Assumptions
- Recorded open items (Needs Confirmation):
  - UNK-03 (probe cache for identity payload): Needs Confirmation — proposed: cache with
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions
- `_identity_payload()` (new): calls `rag.corpus_identity.compute_identity` (doc 01)
  against the server's own DB and config (`embedding_model_id` from the server's
  embedder selection — Assumptions `:149`) and returns the six identity fields as a
  JSON object; unverifiable meta → the object is still emitted with
  `"verified": false` (never omitted).
- Health response: identity attached as an additive `corpus_identity` member of the
  payload assembled at `:245-250` — extend through the existing `make_health_response`
  kwargs/additional-members pattern; `mcp_servers/health_response.py` is not a target
  row, so use whatever additive mechanism it already offers (record at implementation).
- Search response: additive `corpus_identity` member on the search tool result envelope;
  all pre-existing fields unchanged (AC-5).
- Ingestion completion hook: after the existing ingestion routine finishes a full run,
  call `bump_index_generation` (doc 01); on failure leave the previous generation and
  log (Assumptions `:151`, Risk `:228`).
- UNK-03 (probe cache for identity payload): Needs Confirmation — proposed: cache with
  the same TTL as the current probe cache; confirm before landing.

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. Add `_identity_payload()` near `_check_health_deps` `:216`.
2. Wire it into health (`:245`) and search response assembly.
3. Add the post-ingestion bump at the ingestion completion point in this module's
   ingestion tool handler.

## Compatibility considerations
**Dependencies**: upstream: doc 01 (identity module — shared-library import convention,
**Blocks**: docs 10, 11, 16

## Security considerations
- No new security surface beyond what the Source plan records.

## Rollback considerations
- Revert this file together with its paired test rows in the same commit; the change is additive and gated by the plan's checkers.

## Validation plan
- `uv run pytest tests/rag/test_rag_http_mode.py` (doc 16 exercises the contract
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
| 1 | Re-verify cited anchors before editing | Pending | — | — | |
| 2 | Apply the Implementation procedure | Pending | — | — | |
| 3 | Run the Validation plan gates | Pending | — | — | |

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
