# Unify the RAG diagnostics model so one class and one output shape remain

## Priority
Medium

## Summary
Merge the two `SearchDiagnostics` classes, make the diagnostics output come from one model only (no keys appended afterwards), and remove the re-export, the duplicated or hidden values, and the phase comments in the RAG diagnostics code.

## Background
- Source: `memo-issue.md` item H-02 (consolidated version), re-checked against current source on 2026-11-10. The HTTP and remote parts of the memo are already gone after `plans/done/20261110-092546_adrrev003_rag-http-delegation.md`; the remaining parts are below.
- `Explicit in code`:
  - `scripts/rag/diagnostics.py` defines `SearchDiagnostics` (embed and FTS counters plus `degraded`) and `PipelineDiagnostics`; both `to_dict()` docstrings say they produce "the exact same dict shape as the current get_diagnostics()", and the `PipelineDiagnostics` docstring says it mirrors the old dict keys exactly.
  - `scripts/rag/models_result.py` defines a second, different `SearchDiagnostics` (adds `fallback_reason` and `corpus_generation`); `scripts/rag/stages/search.py` and `scripts/rag/augment.py` use this one, while `RagPipeline` uses the one in `diagnostics.py`.
  - `models_result.py` re-exports `PipelineDiagnostics` under a `noqa: F401` "re-exported for consumers" comment, and types `RagSearchResult.hits` as `list[Any]` with a comment "typed after Phase 3-1".
  - `RagPipeline.get_diagnostics()` appends `corpus_generation` after `PipelineDiagnostics.to_dict()` returns, with a comment saying this keeps the frozen contract in `tests/rag/test_diagnostics.py` byte-for-byte stable, and reads `_last_corpus_generation` through a `getattr` default.
  - `PipelineDiagnostics` stores `rrf_k`, but `to_dict()` never outputs it; `hit_counts.merged` repeats the hit count already reported under `fetch_result`.
  - `PipelineDiagnostics.to_dict()` still outputs `fallback_count` and `fallback_reasons`, derived from stage results whose status is `fallback`.
- Refuted memo claims: `http_result_kind`, `remote_status_code`, `remote_latency_ms`, `result_source`, and `identity_degraded` no longer appear in `scripts/rag/`; "(new)" markers were not found; `fallback_count` and `fallback_reasons` cannot be removed as dead HTTP fields because the rerank, MQE, and refiner stages can still record a fallback (`Strongly implied by code`: those stage modules contain fallback handling).
- `Explicit in code`: `get_diagnostics()` has no caller in `scripts/` other than its definition; the memo's Agent `/rag diag` consumer was not found. Tests under `tests/rag/` call it.

## Problem
- The output shape is frozen to preserve an old dict and a test, not by design; every new field (`corpus_generation`) has to be bolted on after the model builds the dict.
- Two classes named `SearchDiagnostics` in two modules make a wrong import type-check against a different structure.
- A stored field that is never output (`rrf_k`) and a value reported twice (`hit_counts.merged`) look like separate information; a re-export keeps an old import path alive; phase comments become false once merged.

## Reason for Change
- The current-only policy (`compatrm001`) forbids re-exports and shape-preservation layers. The identity decision issue in the same batch (`issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md`) decides whether `corpus_generation` stays, so the model has to be settled together with it. No external deadline.

## Implementation Intent
- One diagnostics model, defined in one module, with one documented output shape that contains only fields production fills, each value once.
- `get_diagnostics()` builds its result from the model only.
- Keep the stage-level fallback reporting (`fallback_count`, `fallback_reasons`, `refiner_*`) because those stages can still fall back.

## Target Files or Areas
- `scripts/rag/diagnostics.py`, `scripts/rag/models_result.py`, `scripts/rag/pipeline.py`
- `scripts/rag/stages/search.py`, `scripts/rag/augment.py` (users of the second class)
- `tests/rag/test_diagnostics.py` and the tests that reference `SearchDiagnostics` or `get_diagnostics()` (for example `tests/rag/test_fusion_mode_diagnostics.py`, `tests/rag/test_pipeline_refiner_fallback_counters.py`, `tests/rag/test_augment_refiner.py`, `tests/rag/test_rag_stages.py`)
- `docs/21_rag/` documents that describe the diagnostics output shape (location `Unknown`; find with a search for `get_diagnostics` and `fusion_mode`)

## Required Changes
- Merge the two `SearchDiagnostics` classes into one in one module and update every importer.
- Remove `corpus_generation` from the diagnostics (the identity issue is decided as Option B, remove), including the post-hoc append and the `getattr` default in `get_diagnostics()`.
- Either output `rrf_k` or remove the stored field; report the merged hit count once.
- Remove the `PipelineDiagnostics` re-export and import it from `rag.diagnostics` everywhere.
- Remove the "exact same dict shape" / "mirrors ... exactly" wording and the "Phase 3-1" comment; give `RagSearchResult.hits` its final element type.
- Update the tests and the documented output shape to the new shape.

## Constraints
- The output shape is a public contract for tests and any external reader of `get_diagnostics()`; a changed shape must be intended and documented.
- Do not add compatibility keys or aliases to keep the old shape (`compatrm001`).
- `scripts/rag/models_result.py` and `scripts/rag/pipeline.py` are also edited by `issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md` (and by the identity issue); keep edits non-overlapping.

## Acceptance Criteria
- Exactly one class named `SearchDiagnostics` exists under `scripts/rag/`.
- `get_diagnostics()` returns the model's own `to_dict()` result with no key added afterwards and no `getattr` default.
- Every stored field of the diagnostics model appears in `to_dict()` (or is removed), and no value is reported twice.
- `rg -n "re-exported|Phase 3-1|exact same dict shape" scripts/rag/` returns nothing.
- Tests pass with expectations updated to the new shape; the documented output shape matches.

## Testing Expectations
- Update `tests/rag/test_diagnostics.py` and the affected tests; add a test that `get_diagnostics()` before any `augment()` call returns the model's zero values, replacing the `__new__`-based construction.
- Run `rules/toolchain.md` validation (ruff, mypy with `--no-namespace-packages`, import-linter, pytest on `tests/rag/`) and `uv run python tools/check_docs_consistency.py --domain rag` if docs change.

## Documentation Impact
- Documentation must be updated: describe the output shape and the meaning of the fallback and refiner counters at the level of intent and failure behavior, without copying a field table that duplicates the source (`skills/DESIGN.md` Avoid implementation-reference duplication).
- Run the `docs/` checkers listed in `routing.md`.

## Out of Scope
- The decision whether the corpus identity remains (`issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md`).
- Removing the remote delegation leftovers (`issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md`).
- Changing how stages decide to fall back.

## Dependencies
- Depends on `issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md` for the `corpus_generation` decision (apply that decision first, or settle the field together).
- Coordinate with `issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md` (same `scripts/rag/` modules, no shared lines).
- Related, already implemented: `plans/done/20261110-092546_adrrev003_rag-http-delegation.md`.

## Unresolved Questions
- `Needs confirmation`: whether any consumer outside `scripts/` and `tests/` (for example an operator script or the rag-pipeline MCP server response) reads the `get_diagnostics()` keys; none was found in `scripts/`.
- `Needs confirmation`: whether `rrf_k` should be output or removed (either satisfies the acceptance criteria; maintainer preference).
- `Needs confirmation`: which documents describe the output shape (search required).

## AI Implementation Instruction
- Change only the diagnostics model, its importers, its tests, and the documents that describe its output shape.
- Do not remove the stage-level fallback counters.
- Stop and report if the identity decision is not yet made and `corpus_generation` cannot be settled.
- Keep comments and log text in English.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261110-170709
- **Related target files**: `scripts/rag/diagnostics.py`, `scripts/rag/models_result.py`, `scripts/rag/pipeline.py`, `scripts/rag/stages/search.py`, `scripts/rag/augment.py`, `tests/rag/test_diagnostics.py`
