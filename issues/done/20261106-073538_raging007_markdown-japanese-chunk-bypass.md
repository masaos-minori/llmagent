# Route Markdown documents through language-aware chunking for text regions

## Priority
Medium

## Summary
`ChunkSplitter` selects heading-based Markdown chunking from the source URL alone
(`_is_markdown_source`), and its oversized-section fallback is always `_chunk_english`.
A Japanese document whose URL ends in `.md` / `.markdown` / `.mdx` is therefore never
processed by the Japanese chunker: no Sudachi sentence segmentation, no
`normalized_content`, and English sentence heuristics applied to Japanese text.

### Verification (issue-to-plan cycle 20261106-103229)
- Confirmed line-by-line at HEAD `bdb9bed66`: the markdown check precedes the `lang` check in
  `_build_text_triples` (`chunk_splitter.py:224-229` — correction: the issue names the method
  `_split_text`; the actual method is `_build_text_triples`); `_is_markdown_source` keys on URL
  suffix plus the `md_index_enable` heading-density heuristic (`:139-158`); oversized sections
  fall back to `_chunk_english` (`:174-176`); sections below `min_chunk` are dropped
  (`:171-173`); Markdown triples carry empty `normalized_content` (`("text", c, "")`, `:225`).
- New finding: Markdown sources also record `chunking_strategy="heading"` in every chunk
  payload (`:121`), which is part of the ingester's 9-field group signature and the
  `documents` row — the fix must keep this value unchanged so group validation is unaffected.
- Unresolved question resolved: empty `normalized_content` does **not** corrupt storage —
  `transaction_commit.py:104` stores `normalized_content or None` (NULL), and the FTS5 triggers
  index `COALESCE(normalized_content, content)` (`scripts/db/schema_sql.py:78-90`), so Japanese
  Markdown chunks are indexed by raw text. What degrades is **Japanese query recall**: the
  query path tokenizes Japanese queries into Sudachi `normalized_form` tokens designed to match
  normalized-content index text (`scripts/rag/repository.py:76-90`); against raw-text Markdown
  chunks only surface-form matches hit, so inflected-form queries miss. Chosen output shape:
  non-empty normalized pairs, same as the Japanese text path.
- Test status confirmed: `TestIsMarkdownSource` (`tests/rag/ingestion/test_chunk_splitter.py:42-70`)
  pins URL-suffix detection; Markdown chunking coverage exists only for the English payload
  (`_CRAWL_WITH_MD_HEADINGS`, `:441-452`, used at `:533`); Japanese tests (`:636-663`) use a
  non-`.md` URL — no Japanese-Markdown behavior is tested today.
- Dependency confirmed: the Japanese path crash fix is planned in
  `plans/20261106-093438_raging001_japanese-chunk-merge-crash.md` (created in this batch).

## Problem
- `scripts/rag/ingestion/chunk_splitter.py` `_split_text`: `if self._is_markdown_source(
  data): return [("text", c, "") for c in self._chunk_markdown_by_heading(content)]` —
  chosen before any `lang` check; the `lang == "ja"` branch (which calls
  `_chunk_japanese`) is only reached for non-Markdown sources.
- `_is_markdown_source` keys on the URL suffix (`.md`, `.markdown`, `.mdx`), plus a
  heading-density heuristic when `md_index_enable` is set — never on `lang`.
- `_chunk_markdown_by_heading` splits at heading boundaries; sections exceeding
  `md_snippet_max_chars` fall back to `_chunk_english`, so Japanese sections get English
  paragraph/sentence rules; sections below `min_chunk` are dropped.
- Markdown chunks are emitted with an empty `normalized_content` (`("text", c, "")`),
  unlike the Japanese path which produces `(orig, norm)` pairs consumed downstream.

## Background
The chunking paths grew per format: `_chunk_english` and `_chunk_japanese` (language
paths) and heading-based Markdown snippet chunking (format path). The format decision
short-circuits the language decision. No test asserts Japanese behavior for Markdown
sources, so the divergence is untested. Related crash fix: the Japanese path itself is
tracked by `20261106-073538_raging001_japanese-chunk-merge-crash.md`.

## Reason for Change
Inconsistent indexing quality for Markdown sources in a bilingual (en/ja) corpus: the
same document content yields different chunk boundaries and normalization behavior
depending only on the URL suffix.

## Implementation Intent
Make language selection primary and format secondary: for Markdown sources, extract
heading sections, then segment oversized or in-section text with `_chunk_japanese` when
`lang == "ja"` (and `_chunk_english` otherwise), reusing the shared buffer helpers so
overlap and min/max rules apply uniformly, and emit proper `normalized_content` pairs for
Japanese sections.

## Target Files or Areas
- `scripts/rag/ingestion/chunk_splitter.py`
- `tests/rag/ingestion/test_chunk_splitter.py`

## Required Changes
- Make `_split_text` consult `lang` for Markdown sources, delegating oversized sections
  to the language-appropriate chunker.
- Produce normalized pairs for Japanese Markdown chunks consistent with the Japanese text
  path.
- Add tests: a Japanese `.md` URL chunks via the Japanese path (segmentation and
  normalization applied); English Markdown heading behavior is characterized before any
  change.

## Constraints
- Heading-boundary splitting itself stays (it is the Markdown feature); only the
  intra-section language handling changes.
- Characterize current English Markdown chunk output with tests before changing shared
  code.
- Sections below `min_chunk` keep their current drop behavior unless a test shows a
  regression.

## Acceptance Criteria
- For a Japanese `.md` input with oversized sections, produced chunks follow Japanese
  chunking semantics (verified by test) and carry non-empty `normalized_content` where
  the Japanese text path would.
- English Markdown chunking output is unchanged (characterization test).
- `uv run pytest tests/rag/ingestion` passes.

## Testing Expectations
- Characterization test for current English `.md` heading chunking.
- New tests for Japanese `.md` chunking (oversized section fallback and normalization).
- Full ingestion test suite.

## Documentation Impact
If RAG docs describe Markdown indexing, note that Markdown text now follows
language-aware chunking.

## Out of Scope
- Markdown structure-aware splitting beyond headings (tables, code fences).
- Language detection for chunking (chunkers still use the payload `lang` field).

## Dependencies
- Sequence after `20261106-073538_raging001_japanese-chunk-merge-crash.md`: routing
  Markdown into the Japanese path depends on that path being fixed.

## Unresolved Questions
- Whether empty `normalized_content` for Markdown chunks currently degrades FTS/query
  behavior in storage — Needs confirmation against the persistence layer before choosing
  the normalization output shape.
  Resolved in `plans/20261106-103229_raging007_markdown-japanese-chunk-bypass.md`: storage is
  safe (FTS5 triggers COALESCE NULL normalized_content to raw content), but Japanese query
  recall degrades because query tokens are Sudachi normalized forms; chosen output shape =
  non-empty normalized pairs consistent with the Japanese text path.

## AI Implementation Instruction
Fix the Japanese chunker crash first if working in sequence; keep
`_chunk_markdown_by_heading` responsible for heading-section extraction and delegate
intra-section segmentation to the language chunkers.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-073538
- **Related target files**: `scripts/rag/ingestion/chunk_splitter.py`, `tests/rag/ingestion/test_chunk_splitter.py`
