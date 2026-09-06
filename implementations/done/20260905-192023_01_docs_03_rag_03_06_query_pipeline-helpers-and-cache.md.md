## Goal
Replace `docs/03_rag_03_06_query_pipeline-helpers-and-cache.md`'s "## 6. SemanticCache"
section (class description, code sample, `RagPipeline.invalidate_cache()`
sub-section, "Cache Freshness After CLI Ingestion" sub-section) with a no-cache
retrieval-freshness description, and remove the `semantic-cache` front-matter tag and
Keywords entry (`REQ-001`).

## Scope
- **In-Scope**: replace lines 31-57 (the "## 6. SemanticCache (`scripts/rag/cache.py`)"
  heading through the end of the "### Cache Freshness After CLI Ingestion"
  sub-section) with a new section describing the current no-cache retrieval-freshness
  guarantee; remove the `semantic-cache` entry from the front-matter `tags:` list
  (line 5) and from the "## Keywords" section (line 75).
- **Out-of-Scope**: the document's other sections (`## Related Documents`, "##
  7a. Helper Classes" and its `RagRepository`/`RagScorer`/`RagLLM`/`PipelineRunResult`
  subsections) — confirmed unrelated by reading the full file; `related`/`source`
  front-matter fields — confirmed this document's own filename/inbound-link scope
  question is deferred (Plan Unknowns `UNK-01`: keep the filename unchanged, per this
  Plan's own default resolution).

## Assumptions
- `scripts/rag/cache.py` (`semcacherm`'s procedure document `02`) and
  `RagPipeline.invalidate_cache()` (`semcacherm`'s procedure document `01`) have
  landed before this document's edit — this document describes the *current* (post-
  removal) design, so it must not be written before the removal it describes is
  actually true.
- `tests/rag/test_rag_pipeline_no_cache_freshness.py` (`semcacherm`'s procedure
  document `20`) exists and passes by the time this edit lands — this Plan's `REQ-005`
  names it as the regression-test evidence for the freshness guarantee this section
  now describes; if it is missing or insufficient at implementation time, that is a
  separate Requirement (`REQ-005`) this document does not itself resolve (see Out of
  Scope).

## Design decisions
(per `skills/DESIGN.md` Output language / `skills/python-documentation` conventions,
and this Plan's own Design section)
- Replace, not delete, the numbered section — per this Plan's Design section, "an
  empty section or a bare deletion note would leave the query-pipeline helpers
  document incomplete, since this section is one of the document's numbered
  top-level sections (`## 6.`)." The new section keeps the same `## 6.` numbering and
  heading level so the document's overall section sequence (`## 6.` → "## 7a.") is
  undisturbed.
- State the freshness guarantee precisely as "retrieval from the currently visible
  committed local RAG database state" (per the originating issue's own wording,
  quoted in this Plan's Design section) rather than a vaguer "always up to date"
  claim — this is the exact phrase this Plan's `AC-6` requires.
- Do not restate `scripts/rag/pipeline.py`'s implementation detail beyond what a
  reader needs (per `skills/DESIGN.md` Avoid implementation-reference duplication) —
  name `SearchStage`/`augment()` as the mechanism, without exhaustive method
  signatures.

## Alternatives considered
- Deleting the section entirely and renumbering subsequent sections — rejected: the
  document's other numbered sections ("## 7a.", "### 7.1" etc.) would require
  renumbering, and any inbound cross-reference to "## 6." (from this document's own
  `Related Documents` list or another document) would break; replacing content while
  keeping the heading number is the minimal, safe change.

## Implementation
### Target file
`docs/03_rag_03_06_query_pipeline-helpers-and-cache.md`

### Procedure
1. Remove `semantic-cache` from the front-matter `tags:` list (line 5), leaving
   `rag-repository`, `rag-scorer`, `rag-llm` unchanged.
2. Replace lines 31-57 (the full "## 6. SemanticCache" section through "### Cache
   Freshness After CLI Ingestion") with a new "## 6. Retrieval Freshness" section
   stating: local RAG executes the full retrieval pipeline (`SearchStage`, via
   `RagPipeline.augment()`) for every query, including repeated identical queries;
   no query-result cache exists; committed document additions, updates, and
   deletions are reflected in the very next query with no cache-invalidation action
   or service/process restart required; this guarantee is verified by
   `tests/rag/test_rag_pipeline_no_cache_freshness.py`.
3. Remove `semantic-cache` from the "## Keywords" section (line 75), leaving
   `rag-repository`, `rag-scorer`, `rag-llm`, `rag` unchanged.

### Method
Direct `Edit`: one front-matter line removal, one section-body replacement, one
Keywords line removal.

### Details
- The replacement section must not describe `SemanticCache`, `CacheService`,
  `invalidate_cache()`, FIFO eviction, cache TTL, or a cache `generation` counter as
  current behavior — per this Plan's `AC-3`.
- The replacement section must not state that a service restart or cache-invalidation
  action is required for freshness (the *opposite* of the removed section's "Cache
  Freshness After CLI Ingestion" sub-section) — per `AC-5`.
- Confirm after editing: `rg -in "semanticcache|cacheservice|invalidate_cache|fifo|cache
  generation" docs/03_rag_03_06_query_pipeline-helpers-and-cache.md` returns zero
  matches; `rg -n "semantic-cache"
  docs/03_rag_03_06_query_pipeline-helpers-and-cache.md` (front-matter/Keywords)
  returns zero matches.
- Per `skills/DESIGN.md` Output language, write the new section in English regardless
  of chat language.

## Compatibility considerations
- Other documents' `Related Documents` lists that reference this file by name
  continue to resolve (the file is not renamed or deleted, per Unknowns `UNK-01`'s
  default resolution) — only this one section's content changes.

## Security considerations
N/A: documentation-only change; no secrets or credentials are involved.

## Rollback considerations
- Revert via `git checkout` on this single file; no other file's correctness depends
  on this document's content (documentation only, no code consumer).

## Validation plan
- `uv run python tools/check_docs_quality.py` — no new findings.
- `uv run python tools/check_docs_structure.py
  docs/03_rag_03_06_query_pipeline-helpers-and-cache.md` — passes (heading structure,
  Front Matter, internal link reachability).
- `uv run python tools/check_docs_consistency.py --domain rag` — passes.
- `uv run python tools/check_docs_japanese.py` — no new findings (English-only
  content).

## Completion criteria
- The "## 6." section states the no-cache retrieval-freshness guarantee using the
  exact "currently visible committed local RAG database state" phrasing (Plan
  `AC-1`, `AC-3`, `AC-5`, `AC-6`).
- No `semantic-cache` tag/keyword remains in this document's front-matter or Keywords
  section (Plan `AC-8`).
- All four documentation checkers listed in Validation plan pass.

## Out of scope
- `REQ-005`'s confirmation that `tests/rag/test_rag_pipeline_no_cache_freshness.py`
  exists and is sufficient (a separate Requirement, verified procedurally, not a
  file-level edit this document performs).
- Renaming this file (Plan Unknowns `UNK-01`, deferred).
- Every other section of this document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Done |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A: documentation-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | Done |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | This document's Implementation IS the documentation update |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Depends on `semcacherm`/`semcacheconfig` implementations landing first | Yes | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (replace the SemanticCache section with a no-cache description; remove the front-matter tag/keyword)
- **Source issue**: issues/20260902-150341_semcachedocs_replace_semanticcache_tests_and_docs_with_no_cache_design.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141629_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-192023
- **Related target files**: docs/03_rag_03_06_query_pipeline-helpers-and-cache.md
