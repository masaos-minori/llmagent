# Implementation Procedure: 03_rag_03_06_query_pipeline-helpers-and-cache-part1.md

## Goal

Ensure `docs/03_rag_03_06_query_pipeline-helpers-and-cache-part1.md` §6 (`SemanticCache`)
describes behavior in concise prose plus a source-file pointer, instead of a verbatim
method-signature table, per `plans/20260803-235800_plan.md` Phase 2.

## Scope

- In scope: `docs/03_rag_03_06_query_pipeline-helpers-and-cache-part1.md`, section
  `## 6. SemanticCache (scripts/rag/cache.py)` (lines 29-56 as currently read).
- Out of scope: `docs/03_rag_03_06_query_pipeline-helpers-and-cache-part2.md` (covered by a
  separate implementation-procedure document for the same plan); any change to
  `scripts/rag/cache.py` or other source files; any change to `result_source` notes.

## Assumptions

- Fact (verified by reading the current file, 2026-08-05): §6 no longer contains a raw
  Markdown method table — it already reads as a prose paragraph (line 39) describing
  `lookup()`/`put()`, FIFO `prune()` eviction, `size`, and `invalidate()` incrementing
  `generation`, plus a "テストで確認されている挙動" note (line 41) referencing
  `tests/test_rag_quality_regression.py::test_semantic_cache_generation_invalidation`.
- Assumption: this prose already satisfies the plan's Phase 2 intent (a prior, unrelated
  commit — `1883c8ec docs: update documentation and requirement plans` — appears to have
  applied an equivalent change). This procedure therefore also covers a verification pass,
  not only a from-scratch rewrite, so the next executor does not need to guess.
- Assumption: the code pointer `scripts/rag/cache.py:31` (class `SemanticCache`) and the
  test path referenced in the doc are still accurate as of this writing; the executor should
  re-grep before editing since source line numbers drift.

## Design decisions

- Prefer prose + pointer over an exhaustive method table, consistent with `rules/coding.md`
  documentation conventions and the plan's stated goal of reducing maintenance burden.
- Keep the existing "テストで確認されている挙動" (test-verified behavior) callout intact —
  it is evidence-labeled and should not be diluted into unlabeled prose.
- Do not restate every constructor parameter (`max_size`, `threshold`) in prose beyond what
  is needed to orient a reader; point to `scripts/rag/cache.py` for exact defaults.

## Alternatives considered

- Delete the code sample (lines 33-37) entirely and rely on prose only — rejected, the
  minimal import/instantiation snippet is low-maintenance and orients readers faster than
  prose alone.
- Merge §6 into part 2's helper-class section — rejected, out of scope (file split is a
  pre-existing structural decision, not part of this plan).

## Implementation

### Target file

`docs/03_rag_03_06_query_pipeline-helpers-and-cache-part1.md`

### Procedure

1. Re-run `grep -n "class SemanticCache\|def lookup\|def put\|def prune\|def invalidate\|generation" scripts/rag/cache.py` to confirm method names/line numbers have not drifted since this procedure was written.
2. Read `docs/03_rag_03_06_query_pipeline-helpers-and-cache-part1.md` lines 29-56 and confirm whether the table already described under "Assumptions" above is still absent (i.e., still prose).
3. If a raw method table has reappeared (e.g., from a merge/revert), replace it with a prose paragraph covering: `CacheService` protocol conformance, `lookup()`/`put()`, FIFO `prune()` eviction, `size` property, and `invalidate()` semantics (atomic clear + `generation` increment), followed by a pointer to `scripts/rag/cache.py`.
4. If the file already matches the target state, make no edit — record "no change needed" when this procedure is executed.
5. Preserve the "テストで確認されている挙動" note and its test-path reference unchanged.

### Method

- Locate section boundaries with `grep -n "^## 6\.\|^## Related Documents" docs/03_rag_03_06_query_pipeline-helpers-and-cache-part1.md`.
- Edit only within the located line range; do not touch `### RagPipeline.invalidate_cache()` or the CLI cache-freshness subsection, which are already prose and out of this item's scope.

### Details

- `SemanticCache` (class, `scripts/rag/cache.py:34`) implements the `CacheService` protocol
  (`lookup()`/`put()` declared at lines 23/27). Relevant methods observed via grep:
  `lookup` (46), `put` (70), `prune` (94), `size` property (106), `invalidate` (111),
  `generation` property (118) which returns `self._generation` under a lock.
- The doc's code sample imports `from rag.cache import SemanticCache` and instantiates
  `SemanticCache(max_size=100, threshold=0.92)` — keep this snippet as-is unless the
  constructor signature has changed (re-grep to confirm before editing).

## Compatibility considerations

- Documentation-only change; no API, schema, or config compatibility impact.
- No effect on `03_rag_03_06_query_pipeline-helpers-and-cache-part2.md`'s cross-links to
  this file (front-matter `related`/`source` fields are unaffected by prose-only edits).

## Security considerations

N/A — documentation prose change, no code or secret-handling impact.

## Rollback considerations

- Single-file Markdown edit; revert via `git checkout -- docs/03_rag_03_06_query_pipeline-helpers-and-cache-part1.md` or a follow-up commit reverting the specific hunk.
- No migration or data-state rollback needed.

## Validation plan

- Manual review: confirm no Markdown table (`| ... | ... |`) remains under `## 6.` in
  `docs/03_rag_03_06_query_pipeline-helpers-and-cache-part1.md`.
- Manual review: confirm the `scripts/rag/cache.py` pointer and the
  `tests/test_rag_quality_regression.py::test_semantic_cache_generation_invalidation`
  reference are both present and unbroken (`grep -n "scripts/rag/cache.py\|test_rag_quality_regression" docs/03_rag_03_06_query_pipeline-helpers-and-cache-part1.md`).
- No automated test suite covers documentation prose; this is a manual/documentation-review
  gate only (per `rules/toolchain.md`, no code changes are introduced by this item).

## Out of scope

- Any change to `docs/03_rag_03_06_query_pipeline-helpers-and-cache-part2.md` (separate
  implementation-procedure document, same plan).
- Any change to `scripts/rag/cache.py` or other source files.
- Moving `plans/20260803-235800_plan.md` to `plans/done/` — handled as a separate workflow
  step (Step 4), not part of this document.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260803-235800_plan.md
- Source implementation procedure: N/A
- Generated at: 20260805-120117
- Related target files: 03_rag_03_06_query_pipeline-helpers-and-cache-part1.md
