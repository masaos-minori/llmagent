# Implementation Procedure: `scripts/rag/http_augment.py` (RAGCORPUS001 Phase 3)

**Plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` (REQ-002, REQ-003)

## Goal
Parse the additive identity fields from the remote search response (and health payload
where used) into a structured `CorpusIdentity`-shaped value on `HttpAugmentResult`.

## Scope
- `_map_http_result_kind` `:39`; `class HttpAugmentResult` `:51` (init `:54`);
  `class HttpAugment` `:70`; `get_status` `:92`; `async def run(query, history_context)`
  `:100`; properties `stage_result` `:168`, `http_result_kind` `:173`.

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions
- `HttpAugmentResult` gains a `remote_identity` field (new): `CorpusIdentity | None`.
  Parsed from the additive response fields (`corpus_id`, `index_generation`,
  `schema_version`, `embedding_model_id`, `normalization_version`,
  `chunking_policy_version` — exact wire names fixed by doc 13; keep them identical to
  the server payload keys). Absent or malformed payload → `None` (unverifiable), never a
  zero-filled fake identity.
- `run` `:100` parses once per response; existing result-kind mapping (`:39`) unchanged.
- Health-payload shape precedent: `scripts/mcp_servers/rag_pipeline/rag_pipeline_health_probe.py`
  `_run_probe` `:53` — read it (Reference Files only); identity caching decision
  (UNK-03: cache with the same TTL as the probe cache) is recorded as Needs Confirmation
  and lands server-side in doc 13, not here.

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. Extend `HttpAugmentResult.__init__` `:54` with the defaulted `remote_identity=None`.
2. In `run` `:100`, extract and build the identity after the existing status/kind
   parsing; wrap extraction in a try/except that yields `None` on any schema surprise.

## Compatibility considerations
**Dependencies**:
- Upstream: doc 13 (server exposes identity in search response/health payloads)
**Blocks**: docs 09, 11, 16

## Security considerations
- No new security surface beyond what the Source plan records.

## Rollback considerations
- Revert this file together with its paired test rows in the same commit; the change is additive and gated by the plan's checkers.

## Validation plan
- `uv run pytest tests/rag/test_rag_http_mode.py` (doc 16: match, mismatch, missing).

## Completion criteria
- Remote identity available to the gate; malformed/missing identity is `None`; all
  existing response fields still parsed.

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
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `20261030-140156_13_scripts_mcp_servers_rag_pipeline_rag_pipeline_server.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- `(new)` markers applied: `remote_identity` (Contract section).

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002, REQ-003
- **Source issue**: `issues/20261029-104506_ragcorpus001_rag-corpus-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` — Implementation Target Files row 10
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-140156
- **Related target files**: `scripts/rag/http_augment.py`
