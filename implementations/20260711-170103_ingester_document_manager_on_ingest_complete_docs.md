## Goal

Document the existing, already-correct `on_ingest_complete` callback plumbing between `RagIngester.ingest_all()` and `DocumentManager.check_consistency()` in the two ingestion-pipeline reference docs, so readers understand exactly when the callback fires (and does not fire), and that CLI `main()` does not pass one today.

## Scope

**In-Scope:**
- `docs/03_rag_02_04_ingestion_pipeline-ingester-part1.md` — section `## 4. RagIngester (scripts/rag/ingestion/ingester.py)`: add the `on_ingest_complete` parameter description, the empty-`chunk_files`-short-circuit fact, and the CLI `main()` no-callback fact.
- `docs/03_rag_02_05_ingestion_pipeline-document-manager.md` — section `## 4.10 DocumentManager (scripts/rag/ingestion/document_manager.py)`: add the `check_consistency()` callback-invocation facts (invoked after a successful run including when issues are present; not invoked if the consistency check itself raises).

**Out-of-Scope:**
- `scripts/rag/ingestion/ingester.py` / `scripts/rag/ingestion/document_manager.py` — no code change; the behavior described is already correct and confirmed by direct read (plan's Assumption 5). This is documentation-only.
- Any other section of either doc.

## Assumptions

- Both docs are already written in Japanese prose (confirmed by reading their existing `##` section headers); new content should match the existing document's language and formatting conventions rather than introducing English prose into an otherwise-Japanese doc. `rules/coding.md`'s "English only" rule governs code comments/log output, not existing narrative documentation — follow the surrounding doc's established language.
- The 5 facts below are drawn directly from the plan's Assumption 5, itself confirmed by direct code reads; no new investigation is needed, only faithful transcription into doc prose.
- No code snippet needs to be pasted into the docs beyond short illustrative signatures (e.g. the `on_ingest_complete` parameter), consistent with existing doc style (check a couple of existing subsections in each file for whether they use short code spans vs. full code blocks, and match that style).

## Implementation

### Target file

`docs/03_rag_02_04_ingestion_pipeline-ingester-part1.md` and `docs/03_rag_02_05_ingestion_pipeline-document-manager.md`

### Procedure

1. Open `docs/03_rag_02_04_ingestion_pipeline-ingester-part1.md`, locate `## 4. RagIngester` and its `### 4.2 動作の詳細` (behavior detail) subsection.
2. Add prose covering facts 1, 3, and 5 (below) to this section — the `on_ingest_complete` parameter's existence/purpose, the empty-chunk-files short-circuit, and the CLI's current no-callback behavior.
3. Open `docs/03_rag_02_05_ingestion_pipeline-document-manager.md`, locate `## 4.10 DocumentManager`.
4. Add prose covering facts 2 and 4 (below) — that `check_consistency()` invokes the callback after a successful run (issues do not suppress it), and that it does not invoke the callback if the consistency check itself raises.
5. Keep additions scoped to the existing subsections; do not restructure the docs or add new top-level `##` sections unless the existing section has no natural home for this content (in which case add a minimal new `###` subsection, matching heading depth conventions already used in the file).
6. Update each doc's `## Keywords` section if it exists and does not yet include relevant terms (e.g. `on_ingest_complete`, `check_consistency`) — check existing keyword list style before adding.

### Method

Five explicit statements to add (verbatim facts from the plan, translate/phrase to match each doc's existing language):

1. `RagIngester.ingest_all(force, on_ingest_complete=None)` accepts an optional callback, forwarded to `DocumentManager.check_consistency()`. *(→ ingester doc)*
2. `check_consistency()` invokes the callback after a successful consistency-check run — including when the report contains issues (issues alone do not suppress the callback). *(→ document-manager doc)*
3. If `chunk_dir` has no `*.json` files, `ingest_all()` returns `None` immediately; the callback is never invoked. *(→ ingester doc)*
4. If the consistency check itself raises, `check_consistency()` returns `None`; the callback is never invoked. *(→ document-manager doc)*
5. CLI `main()` (`scripts/rag/ingestion/ingester.py`) calls `ingest_all(args.force)` with no callback — the CLI path never invokes `on_ingest_complete` today; it exists for callers (e.g. a future MCP-driven ingestion path) that need a post-ingestion hook. *(→ ingester doc)*

### Details

- Facts 1, 3, 5 belong in the ingester doc (they describe `ingest_all()`'s own control flow and its CLI caller); facts 2, 4 belong in the document-manager doc (they describe `check_consistency()`'s internal behavior).
- Do not imply any of this is new behavior — phrase as documenting existing, current behavior (e.g. "現在の実装では…", matching whatever tense/register the surrounding doc already uses).
- Cross-reference: consider adding a short pointer from the ingester doc's callback description to the document-manager doc's `check_consistency()` section (and vice versa), if the existing docs already use `## Related Documents`-style or inline cross-references elsewhere — match that pattern rather than inventing a new cross-reference style.
- Do not add anything about `RagPipeline.invalidate_cache()` or the MCP-side cache invalidation here — that belongs in the separate cache/pipeline doc (see the other Phase 4 implementation doc for `docs/03_rag_03_06_query_pipeline-helpers-and-cache-part1.md`).

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to documentation changes:

| Check | Tool | Target |
|---|---|---|
| Docs | `uv run python tools/check_docs_consistency.py` | Passes |
