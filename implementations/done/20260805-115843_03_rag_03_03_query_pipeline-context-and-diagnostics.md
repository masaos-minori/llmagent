# Implementation Procedure: docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md

## Goal

Deduplicate the `SearchDiagnostics` field table in §4.2 of
`docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md` by replacing it with a
cross-reference to `docs/03_rag_04_02_dto-models_result.md`, and record the confirmed
`fetch_result` staleness behavior in HTTP mode as a note in §4.3.

## Scope

- In scope: `docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md` §4.2 and §4.3 only.
- Out of scope: `docs/03_rag_04_02_dto-models_result.md`, any file under `scripts/`, any other
  documentation file.

## Assumptions

- The one-to-two-sentence cross-reference form (pointing readers to the full field list in
  `docs/03_rag_04_02_dto-models_result.md`) satisfies the deduplication intent.
- The evidence trail for `fetch_result` staleness (`scripts/rag/pipeline.py:336`, `:408-414`,
  `:470-511` and `scripts/rag/pipeline_service.py:42-171`) is accurate as given in the source
  requirement.

## Design decisions

- Keep §4.2 focused on HTTP-mode boundary/ownership semantics (the `http_result_kind`
  dual-vocabulary note) and delegate the exhaustive field/type/default listing to the DTO doc,
  per the single-source-of-truth principle (avoid implementation-reference duplication across
  docs, analogous to `skills/DESIGN.md` §Avoid implementation-reference duplication).
- Attach the staleness note directly under the `fetch_result` table row in §4.3 (not as a
  separate subsection) so the caveat is visible at the point of use.

## Alternatives considered

- Keep the full field table in §4.2 and only add the staleness note: rejected — does not
  address the stated deduplication goal and leaves two documents as competing sources of truth
  for the same field list.
- Move the staleness note into `docs/03_rag_04_02_dto-models_result.md` instead of §4.3: rejected
  — that file documents the dataclass itself, not `get_diagnostics()` output semantics; the
  staleness behavior is specific to `RagPipeline.get_diagnostics()` / HTTP augment flow described
  in §4.3.

## Implementation

### Target file

- `docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md`

### Procedure

1. In §4.2 (`SearchDiagnostics (scripts/rag/models_result.py)`), replace the field table with one
   or two sentences stating that the full field list, types, and defaults are documented in
   `docs/03_rag_04_02_dto-models_result.md`; retain the existing "境界条件 (Boundary and
   ownership)" subsection describing `http_result_kind`'s dual meaning.
2. In §4.3 (`get_diagnostics()` return value table), add a note directly beneath the
   `fetch_result` row stating that in HTTP mode `fetch_result` may hold a stale value from the
   previous in-process run, because `RagPipeline._run_http_augment()` does not call `self.run()`
   on HTTP success. Cite `scripts/rag/pipeline.py:336`, `:408-414`, `:470-511` and
   `scripts/rag/pipeline_service.py:42-171` as evidence references.
3. Proofread the section for Markdown table integrity (no broken pipes/rows) and correct
   cross-link syntax to `docs/03_rag_04_02_dto-models_result.md`.

### Method

- Direct text edit of the two target sections; no code changes, no test changes (documentation
  only).
- Verify line-number references against current `scripts/rag/pipeline.py` and
  `scripts/rag/pipeline_service.py` before finalizing, since docs are prone to line-drift as
  source files change.

### Details

- `scripts/rag/pipeline.py:302` — `RagPipeline.run()` (async); this is the in-process path that
  populates `last_fetch_result` (`TwoStageFetchResult`) around the fetch/rerank stage (observed
  near lines 335-338 in the reviewed source, consistent with plan's `:336` reference).
- `scripts/rag/pipeline.py:408-414` — inside `augment()`: when `self._cfg.rag_service_url` is
  set, delegates to `self._run_http_augment(...)` and returns its result directly, bypassing
  `self.run()`.
- `scripts/rag/pipeline.py:470-511` — `RagPipeline._run_http_augment()`: calls
  `HttpAugment.run()`, updates `self.last_search_diagnostics` via `dataclasses.replace(...)`, but
  never touches `self.last_fetch_result` — confirming that on the HTTP success path
  `last_fetch_result` retains whatever value was set by a prior in-process `run()` call (or the
  dataclass default, if none occurred).
- `scripts/rag/pipeline_service.py:42-171` — service-layer caller context establishing how
  `get_diagnostics()` is invoked relative to HTTP vs. in-process augment calls (evidence
  reference only; not re-derived here — see plan's original citation).
- Current document state (verified by direct read, not part of this procedure's own edit):
  §4.2 already contains a cross-reference sentence (not the old field table) and §4.3 already
  contains a staleness note textually matching this procedure's target content and citing the
  same four line references. See "Out of scope" below for how to handle this.

## Compatibility considerations

- Documentation-only change; no API, schema, or runtime behavior is affected.
- Existing external links into §4.2 by heading anchor are unaffected (heading text unchanged,
  only body content under it changes).

## Security considerations

- N/A — no code, credentials, or configuration surface touched.

## Rollback considerations

- Low risk: revert via `git checkout -- docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md`
  or a follow-up commit restoring the prior table, since this is a single-file prose/table edit
  with no downstream consumers other than human readers.

## Validation plan

- Manual review: confirm the `SearchDiagnostics` field table no longer appears in §4.2 and a
  cross-reference sentence to `docs/03_rag_04_02_dto-models_result.md` is present.
- Manual review: confirm the staleness note appears adjacent to the `fetch_result` row in §4.3
  and cites `scripts/rag/pipeline.py:336`, `:408-414`, `:470-511` and
  `scripts/rag/pipeline_service.py:42-171`.
- Markdown lint/preview: confirm table formatting is not broken by the edit.

## Out of scope

- Modifying `docs/03_rag_04_02_dto-models_result.md`.
- Modifying any file under `scripts/`.
- Modifying any other documentation file.
- Note for the implementer: a direct read of the current
  `docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md` (performed only to gather
  Method/Details context for this procedure document, not as part of an "already implemented"
  determination, which per workflow rules is filename-only against `implementations/` and
  `implementations/done/`) shows the target content already matches this procedure's intended
  end state. The implementer should re-verify at execution time and treat this step as a
  no-op/verification pass if the document is unchanged, rather than blindly re-applying the edit.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260803-235200_plan.md
- Source implementation procedure: N/A
- Generated at: 20260805-115843
- Related target files: docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md
