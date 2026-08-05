# Implementation Procedure: 03_rag_03_06_query_pipeline-helpers-and-cache-part2.md

## Goal

Ensure `docs/03_rag_03_06_query_pipeline-helpers-and-cache-part2.md` §7 (`RagRepository`,
Japanese-FTS5 tokenization, `RagScorer`, `RagLLM`) describes behavior in concise prose plus
source-file pointers, instead of verbatim SQL/method tables, per
`plans/20260803-235800_plan.md` Phase 3.

## Scope

- In scope: `docs/03_rag_03_06_query_pipeline-helpers-and-cache-part2.md`, sections
  `### 7.1 RagRepository`, `### 7.2 RagScorer`, `### 7.3 RagLLM` (lines 30-79 as currently
  read).
- Out of scope: `docs/03_rag_03_06_query_pipeline-helpers-and-cache-part1.md` (separate
  implementation-procedure document, same plan); `### 7.4 PipelineRunResult` (not listed in
  the plan's scope); any change to `scripts/rag/repository.py` or `scripts/rag/llm_client.py`.

## Assumptions

- Fact (verified by reading the current file, 2026-08-05): most of §7.1 is already prose —
  the SQL-query table and the `RagRepository` public-method table described in the plan are
  no longer present as raw tables (a prior, unrelated commit —
  `1883c8ec docs: update documentation and requirement plans` — appears to have applied an
  equivalent change). §7.2 (`RagScorer`) and §7.3 (`RagLLM`) are likewise already prose.
- Fact: one raw Markdown table remains at lines 41-44 — the "日本語FTS5のトークン化" /
  `tokenize_pos_filter` method table (`| メソッド | シグネチャ | 説明 |`). This is the one
  concrete remaining conversion target for this item.
- Assumption: converting this single remaining table is sufficient to satisfy Phase 3's
  "Convert Japanese-FTS5 tokenization table (§7.1) to prose" step; the other three
  Phase-3 bullets (RagRepository SQL/method table, RagScorer table, RagLLM tables) are
  already satisfied and need only a verification pass, not a rewrite.
- Assumption: the code pointers (`scripts/rag/repository.py`, `scripts/rag/llm_client.py`)
  and line numbers cited below are accurate as of this writing; re-grep before editing since
  source line numbers drift.

## Design decisions

- Prefer prose + pointer over an exhaustive method/SQL table, consistent with
  `rules/coding.md` documentation conventions and the plan's stated goal.
- For the remaining `tokenize_pos_filter` table, fold its single row into the existing
  "Sudachiの遅延ロード" prose paragraph immediately above it, rather than leaving a
  one-row table — a one-row table adds no value over a sentence.
- Keep the module-level wrapper bullet list (`vector_search`, `fts_search`,
  `fetch_full_document`, `deduplicate_chunks`, `cosine_sim`) as-is — the plan explicitly
  allows keeping "module-level wrapper list if short," and it already reads as prose
  bullets, not a table.

## Alternatives considered

- Remove the `tokenize_pos_filter` row without folding it into prose — rejected, the
  signature and RuntimeError-on-failure behavior is useful context not otherwise stated in
  the surrounding paragraphs.
- Merge §7.1/7.2/7.3 across both files into one consolidated helper-class doc — rejected,
  out of scope (file split is a pre-existing structural decision).

## Implementation

### Target file

`docs/03_rag_03_06_query_pipeline-helpers-and-cache-part2.md`

### Procedure

1. Re-run `grep -n "class RagRepository\|class RagScorer\|def tokenize_pos_filter\|def vector_search\|def fts_search\|def rrf_merge" scripts/rag/repository.py` and `grep -n "class RagLLM\|def expand_queries\|def cross_encoder_rerank\|def summarize_tool_result\|def refine_context" scripts/rag/llm_client.py` to confirm names/line numbers have not drifted.
2. Read `docs/03_rag_03_06_query_pipeline-helpers-and-cache-part2.md` lines 28-80 and confirm the table at lines 41-44 (`tokenize_pos_filter`) is still the only remaining raw table; confirm §7.1's SQL/method content, §7.2, and §7.3 remain prose as recorded under "Assumptions."
3. Replace the `tokenize_pos_filter` table (lines 41-44) with a prose sentence appended to (or merged with) the "Sudachiの遅延ロード" paragraph, stating: `tokenize_pos_filter(text, keep_pos)` returns `normalized_form()` for tokens whose `part_of_speech()[0]` is in `keep_pos`, and raises `RuntimeError` on tokenization failure — with a pointer to `scripts/rag/repository.py`.
4. If §7.1 SQL/method content, §7.2, or §7.3 have regressed to raw tables (e.g., from a merge/revert), replace them with prose + pointer per the plan's Phase 3 bullets; otherwise make no further edit there.
5. Do not touch `### 7.4 PipelineRunResult` — it is out of scope for this plan.

### Method

- Locate section boundaries with `grep -n "^### 7\.\|^## Related Documents" docs/03_rag_03_06_query_pipeline-helpers-and-cache-part2.md`.
- Edit only within `### 7.1`-`### 7.3`; leave `### 7.4` and the `## Related Documents` /
  `## Keywords` sections untouched.

### Details

- `RagRepository` (class, `scripts/rag/repository.py:103`): owns SQL for
  `vector_search` (143, sqlite-vec KNN) and `fts_search` (166, FTS5 BM25; raises
  `sqlite3.OperationalError` on FTS syntax errors, already documented in prose at line 50 of
  the doc). Module-level wrapper functions `vector_search`/`fts_search` at repository.py:226/231
  delegate to the class.
- `_SudachiTokenizer` / `tokenize_pos_filter` (`scripts/rag/repository.py:58`): lazily loads
  Sudachi (`_ensure_loaded`, line 44) with `dictionary(dict="core")` and
  `Tokenizer.SplitMode.C` (lines 54/56) on first use; `tokenize_pos_filter` filters tokens by
  `part_of_speech()[0] in keep_pos` and raises `RuntimeError` on failure (lines 58-67).
- `RagScorer.rrf_merge` (static method, `scripts/rag/repository.py:200`): merges ranked
  lists via `score(d) = Σ 1/(rrf_k + rank_i(d))`, returns descending by score (line 203/211)
  — already covered by existing prose at doc line 61.
- `RagLLM` (`scripts/rag/llm_client.py:94`): `expand_queries` (127, async), `cross_encoder_rerank`
  (149, async), `summarize_tool_result` (192, async), `refine_context` (215, async); module-level
  `get_embedding` (250) and `summarize_tool_result` (265) — already covered by existing prose
  at doc lines 77-79.

## Compatibility considerations

- Documentation-only change; no API, schema, or config compatibility impact.
- No effect on cross-links to `03_rag_03_06_query_pipeline-helpers-and-cache-part1.md`.

## Security considerations

N/A — documentation prose change, no code or secret-handling impact.

## Rollback considerations

- Single-file Markdown edit; revert via `git checkout -- docs/03_rag_03_06_query_pipeline-helpers-and-cache-part2.md` or a follow-up commit reverting the specific hunk.
- No migration or data-state rollback needed.

## Validation plan

- Manual review: confirm no Markdown table (`| ... | ... |`) remains under `### 7.1` in
  `docs/03_rag_03_06_query_pipeline-helpers-and-cache-part2.md` (specifically, the
  `tokenize_pos_filter` table at lines 41-44 is gone).
- Manual review: confirm `scripts/rag/repository.py` and `scripts/rag/llm_client.py`
  pointers remain present and unbroken after the edit
  (`grep -n "scripts/rag/repository.py\|scripts/rag/llm_client.py" docs/03_rag_03_06_query_pipeline-helpers-and-cache-part2.md`).
- No automated test suite covers documentation prose; this is a manual/documentation-review
  gate only (per `rules/toolchain.md`, no code changes are introduced by this item).

## Out of scope

- Any change to `docs/03_rag_03_06_query_pipeline-helpers-and-cache-part1.md` (separate
  implementation-procedure document, same plan).
- `### 7.4 PipelineRunResult` — not listed in the plan's scope.
- Any change to `scripts/rag/repository.py` or `scripts/rag/llm_client.py`.
- Moving `plans/20260803-235800_plan.md` to `plans/done/` — handled as a separate workflow
  step (Step 4), not part of this document.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260803-235800_plan.md
- Source implementation procedure: N/A
- Generated at: 20260805-120218
- Related target files: 03_rag_03_06_query_pipeline-helpers-and-cache-part2.md
