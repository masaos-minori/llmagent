# Chunking documentation states max_chunk behavior the code does not implement

## Priority
Medium

## Summary
The chunk-splitter document states that text exceeding `max_chunk` is split, but the Japanese and English
paths keep oversized sentences whole, and neither the `chunk_overlap` upper bound nor what English
`content` actually contains is documented.

## Background
- `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` states: "chunks smaller than `min_chunk` are
  discarded as noise, and text exceeding `max_chunk` is split" and "`chunk_overlap` prepends that many
  trailing characters of the previous chunk to the next".
- `ChunkJapaneseMixin._split_into_ja_sentences` never splits a sentence, and `_merge_ja_sentence_pairs`
  emits the oversized buffer as-is. `ChunkEnglishMixin._split_sentences_en` states in its own docstring
  "Oversized sentences are kept as-is". Only the code path (`chunk_utils.merge_text_items` with
  `_split_overlong`) enforces `max_chunk`.
- Reproduced at head `6bdced7bb`: with `max_chunk=100` and `chunk_overlap=150`, chunk lengths reach 226,
  while the document presents overlap as a pure addition with no bound.
- The same table describes English as "chunks smaller than `min_chunk` after stopword removal are
  discarded" without stating that the stored text is the stopword-removed text (see issues/20261119-112014_ragcrv002_english-content-stopword-loss.md).
- `docs/21_rag/rag_05_04-error-handling-reference.md` was checked and matches the code (tokenization error →
  file aborted, ERROR, continue), so it needs no change here.
- The chunk-size constants' rationale was already closed as "no rationale found" in
  `issues/done/20260927-211412_nc034_confirm-rationale-for-chunk-size-bounds.md`; that wording must not be
  re-opened or rewritten.

## Problem
The document describes one uniform size guarantee. The implementation enforces it only for code chunks, so
readers cannot predict the size of the text chunks they will get, and cannot reason about what
`chunk_overlap` can do to chunk size.

## Reason for Change
Documentation accuracy is the contract other skills rely on, and a doc that overstates a guarantee hides
the defect fixed by issues/20261119-112013_ragcrv001_ja-empty-chunk-loop.md.

## Implementation Intent
Describe the size rules per chunking path — what each path enforces, what it deliberately does not, and the
bounds on `chunk_overlap` — and align the wording with whichever behavior the filed fixes land.

## Target Files or Areas
- `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`
- `docs/21_rag/rag_05_01-configuration-reference.md`

## Required Changes
- Replace the single "text exceeding max_chunk is split" sentence with a per-path statement.
- State the `chunk_overlap` bound relative to `max_chunk`, matching the validation introduced by
  issues/20261119-112015_ragcrv003_chunk-config-validation.md.
- State what English `content` and `normalized_content` contain, matching issues/20261119-112014_ragcrv002_english-content-stopword-loss.md.
- Keep the existing `Needs Confirmation` / "no rationale" wording for the tuning constants unchanged.

## Constraints
- Documentation-only: no code or config value changes in this issue.
- Must not contradict `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md` invariants.
- Follow `docs/` English-language rule and the repository documentation checkers.

## Acceptance Criteria
- The document's per-path statements match the current implementation for Japanese, English, Markdown, and code.
- `chunk_overlap` limits are stated with the enforced bound.
- Applicable documentation checkers pass.

## Testing Expectations
- Documentation consistency check with the applicable checker listed in `routing.md`, plus a manual
  cross-read of the four chunking paths.
- No code test required; behavior is unchanged.

## Documentation Impact
This issue is the documentation change: per-path size guarantees, overlap bounds, and the English stored-text
statement.

## Out of Scope
- Changing any chunking behavior.
- Re-opening the tuning-constants rationale decision.

## Dependencies
- Depends on the outcomes of issues/20261119-112013_ragcrv001_ja-empty-chunk-loop.md, issues/20261119-112014_ragcrv002_english-content-stopword-loss.md, issues/20261119-112015_ragcrv003_chunk-config-validation.md; the final wording
  must describe the post-fix behavior.

## Unresolved Questions
- N/A: none

## AI Implementation Instruction
Verify every statement against the current source before writing it. Do not restate the tuning-constant
rationale; cite the existing decision.

## Traceability
- **Workflow phase**: `python-code-review` (finding `F-010`)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-112022
- **Related target files**: `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`, `docs/21_rag/rag_05_01-configuration-reference.md`
