# Implementation: RAG configuration docs — document max_size=0/negative semantics + generation's role

## Goal

Document the newly-defined `semantic_cache_max_size=0` ("capacity zero, cache holds no
entries") and negative-value (rejected by `RagConfigValidator`) semantics, and clarify
that `CacheEntry.generation` is observability-only (not used for stale-entry filtering at
lookup time). Re-confirm no dangling reference to a non-existent `tests/test_rag_cache*.py`
exists in the docs (Assumption 7 of the plan) now that the real file has been created.

## Scope

**In:**
- `docs/03_rag_05_1-configuration-reference.md` — the `semantic_cache_max_size` config
  reference row (current line 110) gains a note on the `0`/negative edge cases
- `docs/03_rag_03_06_query_pipeline-helpers-and-cache-part1.md` — the `SemanticCache`
  method/property reference table (`prune`, `generation` rows, current lines 43 and 46)
  gains: (a) `prune()`'s `max_size <= 0` behavior, (b) `generation`'s observability-only
  role
- Re-run `grep -rln "test_rag_cache" docs/` to confirm no dangling reference needs removal

**Out:**
- No change to any other row/section of either doc
- No change to any source or test file — this doc only describes documentation edits

## Assumptions

1. Per the plan's research, the two doc files most likely to need this update are
   `docs/03_rag_05_1-configuration-reference.md` (has the `semantic_cache_max_size`
   config-reference row) and
   `docs/03_rag_03_06_query_pipeline-helpers-and-cache-part1.md` (has the `SemanticCache`
   method/property table including `prune` and `generation`) — confirmed by direct read:
   both files exist today and both contain the exact rows described above.
2. `grep -rln "test_rag_cache" docs/` at planning time found no existing reference — this
   remains true at implementation time unless other in-flight work introduced one; the
   grep must be re-run as a final check, not assumed still-clean.
3. Documentation is in Japanese (matching the existing surrounding text in both target
   files) — this is a docs-only file, not `scripts/` source, so `rules/coding.md`'s
   "comments and log output: English only" rule does not apply to prose in `docs/`.

## Implementation

### Target file

- `docs/03_rag_05_1-configuration-reference.md`
- `docs/03_rag_03_06_query_pipeline-helpers-and-cache-part1.md`

### Procedure

1. In `docs/03_rag_05_1-configuration-reference.md`, locate the `semantic_cache_max_size`
   row (line 110: `| \`semantic_cache_max_size\` | SemanticCacheの容量 |`). Extend the
   description to state: `0` is a valid, deliberate "capacity zero" configuration (the
   cache immediately prunes every entry — effectively disabled via capacity, independent
   of the separate `use_semantic_cache` on/off flag); negative values are rejected as a
   configuration error by `RagConfigValidator`.
2. In `docs/03_rag_03_06_query_pipeline-helpers-and-cache-part1.md`:
   - Update the `prune` row (line 43) to note the `max_size <= 0` special case: the cache
     is emptied unconditionally (not just pruned down to `max_size` entries), rather than
     only describing the `len ≤ max_size` FIFO case.
   - Update the `generation` row (line 46) or add a short note beneath the table
     clarifying that `generation` is observability-only today: it is stamped onto each
     `CacheEntry` at `put()` time and incremented by `invalidate()`, but is never read or
     compared elsewhere — staleness-freedom after `invalidate()` is achieved by physically
     clearing `_entries`, not by generation-based filtering at lookup time.
3. Run `grep -rln "test_rag_cache" docs/` after the above edits. If it returns any file,
   inspect and remove the dangling reference (expected: no output, confirming
   Assumption 7 / Assumption 2 above still hold — the concern is moot since
   `tests/test_rag_cache.py` now exists for real).
4. Do not touch any other section of either file.

### Method

Two small prose/table-cell edits (Japanese text, matching each file's existing style and
terminology) plus one verification grep. No code blocks change in either doc beyond
what's already shown as reference material (the `cache = SemanticCache(...)` example line
is unaffected).

### Details

- Keep both edits terse and consistent with each file's existing table-row style (a single
  additional sentence per row is sufficient — do not restructure the tables).
- Cross-reference between the two docs is not required; each stands on its own as a
  reference table entry.
- If a third doc is found via the `grep` step in Procedure #3 to reference
  `test_rag_cache*.py` incorrectly (e.g. claiming it doesn't exist, or describing stale
  test names), remove/correct that reference as part of this same phase.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Docs consistency | `uv run python tools/check_docs_consistency.py` | Passes |
| Dangling reference check | `grep -rln "test_rag_cache" docs/` | Either no output, or only correct references to the real `tests/test_rag_cache.py` (no claims that it doesn't exist) |
| Manual review | Re-read both edited rows in context | Wording matches the codebase's actual, implemented behavior (Assumption 2 and Assumption 6 of the plan) — no aspirational or inaccurate claims |
