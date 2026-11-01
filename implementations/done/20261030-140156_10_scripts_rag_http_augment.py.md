# Implementation Procedure: `scripts/rag/http_augment.py` (RAGCORPUS001 Phase 3)

**Plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` (REQ-002, REQ-003)

## Goal
Carry the remote corpus identity (parsed once by `call_rag_service` in doc 11) onto
`HttpAugmentResult` as a copy, so the pipeline gate can compare remote vs local identity
without re-parsing HTTP payloads.

## Scope
- `_map_http_result_kind` `:39`; `class HttpAugmentResult` `:51` (init `:54`);
  `class HttpAugment` `:70`; `get_status` `:92`; `async def run(query, history_context)`
  `:100`; properties `stage_result` `:168`, `http_result_kind` `:173`.

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions
- `HttpAugmentResult` gains a `remote_identity` field (new): `CorpusIdentity | None`,
  defaulted `None`. Populated by copying `CallRagResult.remote_identity` (already parsed
  once by `call_rag_service` in doc 11) — no re-parse here (single parse site, Option B).
  A copied `None` (missing/malformed remote identity) stays `None` (unverifiable), never a
  zero-filled fake identity.
- `run` `:100` copies `outcome.remote_identity` into the result; existing result-kind
  mapping (`:39`) and status/kind parsing unchanged.
- Health-payload shape precedent: `scripts/mcp_servers/rag_pipeline/rag_pipeline_health_probe.py`
  `_run_probe` `:53` — read it (Reference Files only); identity caching decision
  (UNK-03: cache with the same TTL as the probe cache) is recorded as Needs Confirmation
  and lands server-side in doc 13, not here.

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. Extend `HttpAugmentResult.__init__` `:54` with the defaulted `remote_identity=None`
   and store it as `self.remote_identity`.
2. In `run` `:100`, pass `remote_identity=outcome.remote_identity` to the
   `HttpAugmentResult` constructor (copy of the doc 11 parse result).

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
| 1 | Re-verify cited anchors before editing | Completed | 20261031-115014 | 20261031-115014 | stale_detector clean; anchors verified |
| 2 | Apply the Implementation procedure | Completed | 20261031-115014 | 20261031-115014 | HttpAugmentResult.remote_identity added (copied from CallRagResult.remote_identity, single parse site per Option B) |
| 3 | Run the Validation plan gates | Completed | 20261031-115014 | 20261031-115014 | ruff(0)/mypy(0)/bandit(M=pre-existing B107)/pytest 4 passed |

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