# Route Markdown documents through language-aware chunking

## Priority
Medium

## Summary
`ChunkSplitter._split_text` bypasses the language-specific chunkers when the source file
has a `.md` suffix: `_split_markdown` splits only on code fences and paragraph boundaries,
with no Japanese sentence segmentation and no `chunk_overlap` support. A Japanese `.md`
document is chunked by a different, weaker algorithm than the same text arriving as HTML,
and can contain chunks below `min_chunk` that the Japanese path would never emit.

## Problem
- In `scripts/rag/ingestion/chunk_splitter.py`, `_split_text` calls `_split_markdown`
  whenever `ext == ".md"`, regardless of `lang`.
- `_split_markdown` only merges paragraphs up to `max_chunk` and has no overlap handling
  at all, so `chunk_overlap = 50` (`config/chunk_splitter.toml`) silently does not apply
  to Markdown sources.
- `lang == "ja"` is only consulted in the non-Markdown branch; the Japanese morphological
  path (Sudachi sentence splitting, stop-word normalization, overlap) never runs for `.md`.
- The Markdown path emits any non-empty leftover buffer, including segments shorter than
  `min_chunk`, violating the min/max contract the other paths enforce.
- Crawler-produced `.json` sources and `--input` files go through the language-aware
  paths; the divergence applies specifically to `.md` inputs (`md_index_enable` workflow).

## Background
The three chunking paths grew separately: `_chunk_english` (paragraph/sentence),
`_chunk_japanese` (Sudachi), `_split_markdown` (fence/paragraph). The `.md` branch was a
format-first decision made before language handling existed for chunkers; no test asserts
Japanese behavior for Markdown inputs, so the divergence is untested.

## Reason for Change
Inconsistent indexing quality for Markdown sources in a bilingual (en/ja) corpus: the same
document content yields different chunk boundaries, overlap guarantees, and minimum-length
behavior depending only on file suffix.

## Implementation Intent
Make language selection primary and format a secondary concern: for `.md` sources, extract
code fences, then send each text region through `_chunk_japanese` or `_chunk_english`
according to `lang` (reusing `merge_text_items`/`start_next_buf` so overlap and
min/max rules apply uniformly).

## Target Files or Areas
- `scripts/rag/ingestion/chunk_splitter.py`
- `tests/rag/ingestion/test_chunk_splitter.py`

## Required Changes
- Rework `_split_text`/`_split_markdown` so Markdown text regions go through the
  language-aware chunkers.
- Enforce `min_chunk` filtering on Markdown-derived chunks consistent with the other
  paths.
- Add tests: a Japanese `.md` document is chunked with the Japanese path (overlap applied,
  no sub-`min_chunk` text chunks); an English `.md` document keeps its current fence/code
  behavior.

## Constraints
- Code chunks from fences keep their current special handling (including empty
  `chunk_type == "code"` placeholders for missing blocks).
- Existing English Markdown chunking results should not regress; characterize current
  output before changing it.
- Do not change `.json` (crawler) or non-Markdown paths.

## Acceptance Criteria
- For a Japanese `.md` input longer than `max_chunk`, produced chunks follow the Japanese
  chunking semantics (sentence boundaries, overlap, min/max) — verified by test.
- Markdown code-block chunk behavior is unchanged.
- `uv run pytest tests/rag/ingestion` passes.

## Testing Expectations
- Characterization test capturing current English `.md` chunking before the change.
- New tests for Japanese `.md` chunking with `chunk_overlap > 0` and a sub-`min_chunk`
  tail.
- Full ingestion test suite.

## Documentation Impact
If the RAG docs describe Markdown indexing, note that Markdown text now follows
language-aware chunking.

## Out of Scope
- Markdown structure-aware splitting (headers, tables).
- Language detection for chunking (chunkers still use the payload `lang` field).

## Dependencies
- Consider sequencing after `20261106-073538_raging001_japanese-chunk-merge-crash.md`:
  routing Markdown into the Japanese path depends on that path being fixed.

## Unresolved Questions
- Whether any production `.md` sources are already indexed with sub-`min_chunk` chunks
  that would need a rebuild after this change.

## AI Implementation Instruction
Fix the Japanese chunker crash first if working in sequence; keep `_split_markdown`
responsible only for fence/region extraction and delegate text segmentation to the
language chunkers.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-073538
- **Related target files**: `scripts/rag/ingestion/chunk_splitter.py`, `tests/rag/ingestion/test_chunk_splitter.py`
