# FTS query requires every token and drops queries without ASCII or Japanese words

## Priority
Medium

## Summary
`_build_fts_query` joins up to 20 quoted tokens with spaces, which FTS5 evaluates as an AND of all terms, and it keeps only `[a-zA-Z0-9]+` runs for non-Japanese text, so long natural-language queries rarely match and accented, Cyrillic or Hangul queries produce an empty query.

## Background
Review finding F-007. Evidence (Explicit in code; behavior of FTS5 implicit AND is Strongly implied, not yet measured on the real corpus): `scripts/rag/repository.py` `_build_fts_query` returns `" ".join(f'"{t}"' ...)`; the token source is `re.findall(r"[a-zA-Z0-9]+", text)` for text without kana or CJK ideographs. The archived `issues/done/20260913-163623_bugs002_fts_query_truncation_silent_drop.md` addressed truncation logging only. MQE paraphrases and long questions regularly contain more than a few terms.

## Problem
Recall of the BM25 leg collapses as the query grows (every term must occur in one chunk), and non-ASCII Latin-script queries get no lexical results at all, silently.

## Reason for Change
The hybrid design relies on BM25 to complement the vector leg; an over-strict query turns that leg into dead weight for exactly the queries MQE generates.

## Implementation Intent
Choose and document a recall-oriented matching rule (for example OR across terms with BM25 ranking, or a minimum-should-match threshold) and a token rule that handles all word characters, then measure it on a small fixed query set before adopting it.

## Target Files or Areas
- `scripts/rag/repository.py` (`_build_fts_query`, `RagRepository.fts_search`)
- `tests/rag/test_rag_repository.py` or the existing repository tests under `tests/rag/`

## Required Changes
- Decide the term-combination rule and record the decision (intent and boundary) in the RAG documentation.
- Use a Unicode-aware token pattern for non-Japanese text.
- Keep the quoting that neutralizes FTS5 operators.
- Add tests for a long query, an accented query and an operator-like query.

## Constraints
- Do not weaken the escaping of FTS5 metacharacters.
- Keep the maximum token cap.

## Acceptance Criteria
- A query of ten ordinary words returns chunks that contain a subset of the words (per the chosen rule).
- A non-ASCII Latin-script query yields a non-empty FTS query.
- Quoting still prevents `AND`/`OR`/`NOT`/`NEAR` from acting as operators.

## Testing Expectations
- Unit tests for `_build_fts_query` and an integration test against an in-memory FTS5 table.
- A small offline recall comparison recorded in the PR description.
- ruff and mypy on touched files.

## Documentation Impact
Document the matching rule and the tokenization boundary in the RAG search-stage description (intent and failure behavior only).

## Out of Scope
- Replacing FTS5 or the Sudachi tokenizer.
- Changing the index-side tokenization.

## Dependencies
Related, no required order: `issues/20261108-131007_ragrev004_search-bm25-coupling.md` (BM25 leg coupling in the search stage).

## Unresolved Questions
Whether the index-side `normalized_content` tokens make an OR rule noisy for Japanese is `Needs confirmation` and needs the recall measurement.

## AI Implementation Instruction
Keep the change minimal and confined to the Target Files or Areas. Do not rewrite unrelated files, keep public behavior unchanged unless Required Changes says otherwise, and do not implement items listed under Out of Scope. Add the tests named in Testing Expectations before or with the fix. If a requirement is unclear, stop and report the open question instead of guessing.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261108-131008
- **Related target files**: `scripts/rag/repository.py`, `tests/rag/test_rag_repository.py`
