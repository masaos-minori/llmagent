# Implementation Procedure: `scripts/rag/pipeline_service.py` (RAGCORPUS001 Phase 3)

**Plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` (REQ-002, REQ-003)

## Goal
Extend the delegation outcome `CallRagResult` with additive identity fields so the
pipeline gate can compare remote identity without re-parsing HTTP payloads.

## Scope
- `class CallRagResult` `:27-39`; `_MAX_ATTEMPTS` `:20`, `_REQUEST_TIMEOUT_SECONDS`
  `:21`; `_set_fallback_reason` `:53`, `_set_fetch_result` `:61`.

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions
- `CallRagResult` gains `remote_identity` (new): `CorpusIdentity | None`, defaulted
  `None`. Populated wherever this module already parses a remote response body (same
  wire fields as doc 10). The shared parse helper `parse_remote_identity(body)` lives
  in the leaf module `scripts/rag/corpus_identity.py` (imports only `db.helper`; no
  runtime import cycle with `pipeline_service`/`http_augment`) and is imported here at
  the `rag.*` top-level layer.
- All pre-existing fields and their semantics unchanged (REQ-009); retry/logging paths
  (`_log_retry` `:42`) untouched.

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. Add the defaulted field to the dataclass.
2. At each success-decoding site of the delegation call, attach the parsed identity;
   failure/timeout outcomes keep `None`.

## Compatibility considerations
**Dependencies**: upstream: doc 10 (identity parsed from responses)
**Blocks**: docs 08, 17

## Security considerations
- No new security surface beyond what the Source plan records.

## Rollback considerations
- Revert this file together with its paired test rows in the same commit; the change is additive and gated by the plan's checkers.

## Validation plan
- `uv run pytest tests/rag/test_rag_pipeline_service.py` (doc 17).

## Completion criteria
- Gate can source identity from `CallRagResult` alone; old constructions without the
  kwarg remain valid.

## Out of Scope
- Everything outside the target file and the anchors recorded above; cross-plan boundaries and sequencing are recorded in the Source plan.

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-verify cited anchors before editing | Completed | 20261031-115014 | 20261031-115014 | stale_detector clean; anchors re-verified against HEAD |
| 2 | Apply the Implementation procedure | Completed | 20261031-115014 | 20261031-115014 | CallRagResult.remote_identity added (defaulted None); call_rag_service parses body on success/empty sites; auth_error/transient keep None |
| 3 | Run the Validation plan gates | Completed | 20261031-115014 | 20261031-115014 | ruff(0)/mypy(0)/pytest 25 passed; parse_remote_identity pure helper in leaf corpus_identity.py |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `20261030-140156_10_scripts_rag_http_augment.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- `(new)` markers applied: `remote_identity` (Contract section).

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002, REQ-003
- **Source issue**: `issues/20261029-104506_ragcorpus001_rag-corpus-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` — Implementation Target Files row 11
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-140156
- **Related target files**: `scripts/rag/pipeline_service.py`