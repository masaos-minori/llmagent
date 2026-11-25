# Introduce explicit RAG pipeline outcomes and canonical stage diagnostics

## Priority
High

## Summary
Separate empty, degraded, and failed searches with explicit pipeline outcomes and one immutable result per stage, so a backend outage can no longer read as "No relevant documents found".

## Background
Verified against master on 2026-11-25 (source: `memo-issue.md` H-04):
- Confirmed: `fmt_run_pipeline` returns "(No relevant documents found in the knowledge base.)" for any empty `augmented_text` (`scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py:222`), and the search stage returns `[], True` on a leg failure (`scripts/rag/stages/search.py:58-83`).
- Confirmed: the fallback reason is one shared slot, `ctx._fallback_reason` (`scripts/rag/stage.py:51`), overwritten by `mqe` and `rerank` (`stages/mqe.py:43-53`, `stages/rerank.py:59-69`).
- Confirmed: `PipelineStageName` has no `REFINER` member (`scripts/rag/enums.py:11-17`), and the Refiner result is appended to `AugmentRefiner.last_stage_results` with the literal name `"Refiner"` (`scripts/rag/augment.py:105-111`).
- Partly confirmed: `AugmentStage.get_status` returns `fallback` for no reranked results and `success` otherwise (`scripts/rag/stages/augment.py:43-48`), so it is not unconditional, but it never reflects the actual formatting outcome.
- Confirmed in part: `fts_errors` counts one per failed retrieval leg and there is no `vector_errors` (`stages/search.py:41,99-122`); the module docstring says so deliberately.
- Not verified: the claim that a DB-open failure becomes an empty result in every path.

## Problem
Normal zero-hit searches, supported degradation, and real failures are not distinguishable by callers or monitoring, and stage diagnostics lose information when two stages degrade in one run.

## Reason for Change
Operators and the Agent need to tell an outage from "no hits"; error text built by the formatter cannot be used for monitoring.

## Implementation Intent
Define outcomes `success`, `empty`, `degraded`, `failure` and per-stage results with canonical statuses (`success`, `degraded`, `skipped`, `disabled`, `failure`) held in one immutable collection that includes the Refiner and Augment stages. Derive service and MCP errors from the structured outcome; keep presentation text out of the decision.

## Target Files or Areas
- `scripts/rag/stage.py`, `stage_lifecycle.py`, `enums.py`, `pipeline.py`, `diagnostics.py`, `augment.py`, `models_result.py`
- `scripts/rag/stages/search.py`, `mqe.py`, `fusion.py`, `rerank.py`, `augment.py`
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py`, `rag_pipeline_server.py`
- `tests/rag/`, `tests/mcp_servers/rag_pipeline/`

## Required Changes
- Outcome model: `empty` only when at least one retrieval leg succeeded with zero hits; `degraded` when a supported fallback leaves usable results; `failure` when all legs fail or a non-recoverable stage fails; later dependent stages recorded as `skipped`.
- Replace the shared fallback slot with one immutable result per stage; configured disablement is `disabled`, not degradation.
- Add `vector_errors`; keep `fts_errors` FTS-specific; record attempted, succeeded, failed, and hit count per leg.
- Add `REFINER` to the stage enum and put Refiner and Augment results in the same collection with their real status.
- Convert domain exceptions to `RagPipelineServiceError` at the service boundary; MCP failures return `is_error=true`.

## Constraints
- Keep the documented empty-result text for real zero-hit searches.
- Keep the existing safe fallbacks (MQE, rerank) for degradation.
- Do not change public tool names or input schemas.

## Acceptance Criteria
- Zero-hit search returns the documented empty result; single-leg failure with usable results is `degraded`; all legs failing is an MCP error; DB-open and unexpected stage errors never become empty results.
- MQE and rerank degradation reasons are both retained in one run; disabled stages do not increment degradation counters.
- Vector and FTS errors are observable separately; Augment status reflects its real outcome.

## Testing Expectations
Stage-level and service-level tests for each outcome, combined degradation, and disabled stages; MCP endpoint tests for `is_error`; whole-suite run and changed-path gates.

## Documentation Impact
Update the RAG pipeline and diagnostics documents for the outcome and stage status vocabulary.

## Out of Scope
- Rerank validation and context boundaries (issues/20261125-093150_ragrem005_rag-rerank-context-trust.md).

## Dependencies
- Depends on issues/20261125-093146_ragrem001_rag-runtime-tool-contracts.md.
- Blocks issues/20261125-093150_ragrem005_rag-rerank-context-trust.md.

## Unresolved Questions
- `不明`: whether existing consumers parse `fallback_reasons` or the `"Refiner"` stage name (needs a consumer scan before renaming).
- `不明`: whether the Agent maps the empty-result text to behavior.

## AI Implementation Instruction
Run `tools/scan_change_consumers.py --seed` for the changed symbols before editing; keep changes inside the listed RAG modules; do not weaken existing fallbacks.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261125-093149
- **Related target files**: `scripts/rag/stage.py`, `scripts/rag/stages/search.py`, `scripts/rag/pipeline.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py`
