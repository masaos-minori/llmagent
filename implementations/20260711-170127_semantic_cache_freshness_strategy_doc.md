## Goal

Document, in the query-pipeline `SemanticCache`/`RagPipeline` reference doc, both the new `RagPipeline.invalidate_cache()` method and the chosen operational strategy for CLI-ingestion cache freshness (documented restart, not an invented cross-process invalidation mechanism), so operators know exactly what to do after CLI ingestion if immediate query freshness is required.

## Scope

**In-Scope:**
- `docs/03_rag_03_06_query_pipeline-helpers-and-cache-part1.md`, section `## 6. SemanticCache (scripts/rag/cache.py)` (re-confirm this is still the correct current section/file at implementation time, per the plan's own note about ongoing doc-split churn — if `SemanticCache`/`RagPipeline` coverage has moved to a successor file, target that file instead):
  - Add documentation of `RagPipeline.invalidate_cache()` (what it does, when MCP calls it).
  - Add the CLI-ingestion cache-freshness strategy paragraph (Design/Assumption 6): operational restart of the rag-pipeline-mcp service (or agent process) is required for immediate freshness after CLI ingestion; this is not automatic.

**Out-of-Scope:**
- Implementing any of the 3 alternative freshness strategies (MCP admin-invalidation endpoint, DB-persisted corpus version, MCP-service-managed ingestion) — explicitly out of scope per the plan; document only the chosen strategy and why the others were not built.
- Any code change to `scripts/rag/pipeline.py` or `scripts/rag/cache.py` (covered by the Phase 1 doc).

## Assumptions

- The doc's existing language/register is Japanese (confirmed via its `## 6. SemanticCache` header); new content should match that convention.
- `SemanticCache.invalidate()` (cache.py:102-106) and `RagPipeline.semantic_cache` (pipeline.py:114) are already documented or at least already exist in code — this task adds documentation of the *new* `invalidate_cache()` wrapper method and the freshness-strategy narrative; it does not need to re-document `SemanticCache.invalidate()`'s internals if already covered elsewhere in this doc (check first; add only what's missing).
- The exact filename may have changed since the plan was written (the plan flags "re-confirm exact filename at implementation time per this session's ongoing doc-split churn"); as of this document's creation, `docs/03_rag_03_06_query_pipeline-helpers-and-cache-part1.md` still exists and still contains the `## 6. SemanticCache` section, so it remains the correct target — re-verify with `ls docs/ | grep -i cache` immediately before making the edit, in case it moved again in the interim.

## Implementation

### Target file

`docs/03_rag_03_06_query_pipeline-helpers-and-cache-part1.md` (re-verify at implementation time; see Assumptions)

### Procedure

1. Re-run `ls docs/ | grep -iE "cache|03_rag_03_06"` immediately before editing to confirm this file (or its current successor) still covers `SemanticCache`.
2. Open the file, locate `## 6. SemanticCache (scripts/rag/cache.py)`.
3. Add a subsection (or extend an existing "usage"/"呼び出し元" subsection if one exists) documenting `RagPipeline.invalidate_cache()`: its signature, that it delegates to `SemanticCache.invalidate()`, and that the MCP `rag_pipeline` service's `fmt_delete_document()` calls it after a successful deletion.
4. Add a clearly separated subsection (e.g. "### CLI インジェスト後のキャッシュ鮮度" or matching existing heading style) containing the freshness-strategy paragraph (see Method below), stating plainly that CLI ingestion does not automatically invalidate a running MCP service's cache, and that a restart is the documented operational remedy.
5. If the doc has a `## Related Documents` section, add a cross-reference to the ingester/document-manager docs (Phase 4 part A) and to wherever `RagPipeline`'s public API is otherwise documented.
6. Update `## Keywords` if present (e.g. add `invalidate_cache`, `cache freshness`, `restart`).

### Method

Content to add, translated/phrased to match the doc's existing (Japanese) register:

**`invalidate_cache()` documentation** — cover:
- Signature: `RagPipeline.invalidate_cache(self) -> None`
- Behavior: delegates to `self.semantic_cache.invalidate()` (thread-safe, bumps generation counter, clears all entries)
- Caller: MCP `rag_pipeline` service's `fmt_delete_document()`, called only on successful deletion

**Freshness-strategy paragraph** (English source text from the plan's Design, to be phrased in the doc's own language/register):

> MCP `rag_delete_document` invalidates the calling MCP-service process's own `RagPipeline.semantic_cache` via `invalidate_cache()` — this only clears the cache **within that one process**. CLI ingestion (`uv run python -m rag.ingestion.ingester`) runs in a **separate process** with no access to the MCP service's in-memory cache; **if immediate query freshness after CLI ingestion is required, restart the rag-pipeline-mcp service (or the agent process, which restarts all subprocess-mode MCP servers) — this is an operational step, not something CLI ingestion does automatically.** Absent a restart, semantic-cache entries populated before the ingestion may return stale context for a bounded window (until the cache's own eviction/TTL — see [cache configuration] — naturally expires them).

### Details

- Make explicit that this is a deliberate design tradeoff (per the plan's Risks table), not an oversight: state that automatic cross-process invalidation was considered and rejected in favor of a documented manual step, to avoid a future reader mistakenly "fixing" this as a bug.
- Link/reference the cache configuration doc section (TTL/eviction) if one already exists in this file or a sibling doc, per the bracketed `[cache configuration]` placeholder in the paragraph — replace the placeholder with a real doc/section reference rather than leaving literal brackets in the shipped doc.
- Do not describe the 3 rejected alternative strategies in implementation detail — a brief one-clause mention of "other approaches (e.g. an admin invalidation endpoint) were considered but are not implemented" is sufficient; the plan itself only requires operators to know what to do, not a full design-alternatives writeup.

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to documentation changes:

| Check | Tool | Target |
|---|---|---|
| Docs | `uv run python tools/check_docs_consistency.py` | Passes |
