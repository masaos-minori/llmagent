# Add RAG corpus identity and severity-aware consistency enforcement

## Priority
Medium

## Summary
Give the RAG corpus a verifiable identity that is compared before a remote-to-local fallback result is accepted and recorded on every RAG result path, and make startup consistency checking act on the severity that `scripts/db/rag_consistency.py` already assigns, so canonical-data corruption stops startup or rejects execution while repairable derived-index drift enters an observable degraded state.

## Background
Source: `memo-issue.md` item M-01 (original tasks M-02 and M-03), re-verified against current source on 2026-10-29.

Corpus identity (`Documentation only` unless noted):
- ADR-010 documents the current trade-off: the external and in-process modes "read their corpus from separately configured database paths (`rag_db_path`), which are identical by configuration convention only", and "result consistency between the external RAG and the local RAG is not guaranteed" (`docs/10_adr/adr_02_06_010_rag-fallback.md:60, 77`). The alternative of a separate, synchronized corpus was rejected "to prioritize Availability and avoid the cost of corpus synchronization" (lines 126-130). ADR-010's re-evaluation triggers include "the external RAG service using a corpus other than the local one" (line 61).
- ADR-010 INV-05 states that on fallback the whole pipeline is re-executed, and INV-06 that the result source (Remote, Local, Fallback) is tracked in metrics and logs (`adr_02_06_010_rag-fallback.md:165-166`). No corpus ID, index generation, embedding-model ID, normalization version, or chunking-policy version exists in `scripts/rag/` (`rg` over `pipeline.py`, `http_augment.py`, and `pipeline_service.py` finds fallback logic but no corpus-identity symbol; `Explicit by absence search`).

Consistency severity (`Explicit in code`):
- `scripts/db/rag_consistency.py` already labels findings in their text: `[WARNING]` for an FTS gap, a vector count mismatch, and documents without chunks (lines 156-213); `[CRITICAL]` for FTS orphans, orphan vector rows, chunks without vector rows, and duplicate `chunk_index` values (lines 167-238).
- Startup validation does not act on that distinction: every consistency issue is recorded with `pipeline.add_warning("rag_consistency", ...)` (`scripts/agent/startup_validation.py:171-176`), and a timeout or an unexpected failure of the check is recorded as skipped, not fatal (lines 177-190, with a `noqa: BLE001` stating the check "must not abort startup").
- The memo's list of fatal classes (canonical-table corruption, FK inconsistency, embedding-dimension mismatch, unknown schema, unverifiable generation) is only partly represented by the existing checks; which of them `check_rag_consistency` already detects was not traced end to end.

## Problem
A fallback can silently return results from a corpus that differs from the remote one in content, embedding model, normalization, or chunking, and nothing identifies which corpus produced a result. At startup, findings the checker itself marks critical are downgraded to warnings, so a corrupted canonical corpus does not stop startup.

## Reason for Change
Corpus identity makes the accepted ADR-010 trade-off observable and lets a deployment reject or flag an incompatible fallback; severity-aware enforcement aligns startup behavior with the fail-fast policy for integrity failures (ADR-004). Priority is Medium: the corpus mismatch is a documented, accepted limitation with no incident cited, and the severity labels already exist, so the work improves guarantees rather than fixing an observed failure. It is not time-sensitive.

## Implementation Intent
Define a corpus identity (corpus ID, index generation, schema version, embedding-model ID, normalization version, chunking-policy version) stored with the local corpus metadata and exposed through the remote RAG health or response contract, compare the identities before accepting fallback results, and record the selected generation in diagnostics and logs. Define mismatch behavior as one of: reject the fallback, return an explicitly degraded result, or allow only under an approved policy, and document it. Separately, turn the existing severity labels into a structured classification (repairable or degraded versus fatal) that startup validation acts on, expose severity, affected functions, and the repair action, and keep fatal findings non-downgradable by configuration. Because corpus synchronization was explicitly rejected in ADR-010, the identity mechanism must not introduce synchronization; changing ADR-010's "consistency not guaranteed" decision needs an approval record.

## Target Files or Areas
- `scripts/rag/pipeline.py`, `scripts/rag/http_augment.py`, `scripts/rag/pipeline_service.py`
- `scripts/db/rag_consistency.py`
- `scripts/agent/startup_validation.py`, `scripts/agent/services/rag_maintenance_service.py`
- RAG pipeline MCP health endpoint (`scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`) and the RAG metadata schema (path to be confirmed)
- RAG fallback and consistency tests (names to be confirmed)
- `docs/10_adr/adr_02_06_010_rag-fallback.md` and the RAG operations documents under `docs/`

## Required Changes
- Define the corpus identity fields and expose them through local metadata and the remote RAG health or response contract.
- Compare remote and local identities before accepting fallback results, define mismatch behavior, and record the selected generation in search diagnostics and logs.
- Replace text-prefix severity with a structured classification: FTS gaps, FTS orphans, and vector orphans as repairable or degraded; canonical-table corruption, FK inconsistency, embedding-dimension mismatch, unknown schema, and unverifiable generation as fatal.
- Make startup validation act on severity (abort or reject for fatal, observable degraded state with a repair action for derived-index drift) and expose severity, affected functions, and the repair action.
- Add integration tests for generation mismatch and every consistency severity.

## Constraints
- Fail closed for canonical-data failures; fatal findings cannot be downgraded through configuration.
- Do not add a corpus synchronization protocol (rejected in ADR-010); the identity is compared, not synchronized.
- Keep the existing fallback conditions (ADR-010 INV-03 to INV-05) and the rule that authentication errors do not fall back.
- Preserve public RAG tool contracts unless the identity fields are an agreed additive extension.

## Acceptance Criteria
- Fallback never silently switches to an unidentified or incompatible corpus, and mismatch behavior is deterministic and documented.
- Every RAG result identifies the corpus generation used.
- Canonical-data integrity failures abort startup or reject execution according to policy; derived-index failures enter an observable degraded state with a repair action.
- Fatal findings cannot be downgraded through configuration.

## Testing Expectations
- Integration tests: identity match, identity mismatch with each policy, missing identity, each consistency severity at startup, and a timeout or error of the check itself.
- Unit tests for the severity classification and the identity comparison.
- `uv run pytest tests/rag tests/agent tests/db`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `uv run python tools/check_docs_consistency.py --domain rag`.

## Documentation Impact
Yes. ADR-010 and the RAG operations documents must state the identity contract, the mismatch behavior, and the severity classes with their startup consequences; document intent, boundaries, and failure behavior only (`skills/DESIGN.md` Docs content policy).

## Out of Scope
- Corpus synchronization, replication, or automatic repair of canonical corruption.
- Changes to retrieval quality, ranking, or the fallback conditions themselves.
- Unrelated refactoring or formatting-only changes.

## Dependencies
- Depends on an owner decision about ADR-010's accepted "consistency not guaranteed" trade-off (see Unresolved Questions); record the approval before implementing the identity part.
- Related: `issues/20261029-104504_adrauth001_adr-authority-model.md` (ADR-010 is the primary authority for RAG fallback) and `issues/20261029-104505_adrcov001_contract-manifests-invariant-coverage.md` (health contracts manifest). No in-flight plan targets these RAG files (checked in `plans/`).

## Unresolved Questions
- `Needs confirmation`: whether the owner wants to change ADR-010's accepted trade-off at all, or only add identity observability without rejecting fallback.
- `Needs confirmation`: where the corpus identity should be stored (RAG metadata table or a file) and how the remote service learns its own identity.
- `Needs confirmation`: which of the memo's fatal classes `check_rag_consistency` already detects (embedding-dimension mismatch, unknown schema, unverifiable generation, FK inconsistency).
- `Needs confirmation`: the policy default when identities mismatch (reject, degraded result, or approved allow).

## AI Implementation Instruction
- Read ADR-004 and ADR-010, `scripts/db/rag_consistency.py`, and `scripts/agent/startup_validation.py` before editing; reuse the existing finding classification as the starting point.
- Do not add synchronization and do not weaken fail-fast behavior; stop and report instead of choosing the mismatch policy or changing ADR-010 without an approval record.
- Deliver the identity work and the severity work as separate, reviewable steps.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261029-104506
- **Related target files**: `scripts/rag/pipeline.py`, `scripts/rag/http_augment.py`, `scripts/rag/pipeline_service.py`, `scripts/db/rag_consistency.py`, `scripts/agent/startup_validation.py`, `scripts/agent/services/rag_maintenance_service.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, `docs/10_adr/adr_02_06_010_rag-fallback.md`
