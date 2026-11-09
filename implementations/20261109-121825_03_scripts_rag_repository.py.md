## Goal
Make the BM25 query recall-oriented and script-neutral in `_build_fts_query` (`REQ-001`..`REQ-004`): join the quoted tokens with `OR` so BM25 ranks partial matches, and tokenize the non-Japanese branch with a Unicode-aware pattern, without weakening quoting or the token cap.

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies only `scripts/rag/repository.py`, function `_build_fts_query` (and its docstring). `RagRepository`, `_SQL_FTS`, and the signal handling of `rrf_merge` / `_dedup_hits` / `vector_search` / `fts_search` are not touched.

## Assumptions
- Execution order: Plan Phase 2, after both test procedures (Phase 1).
- Overlap judgment (Plan Assumptions): `plans/20261108-165114_ragrev006_rrf-merge-drops-signals.md` also edits this file (merge, dedup, and the hit construction inside `vector_search` / `fts_search`). The functions are disjoint from `_build_fts_query`; compatible with no required order. Both Plans shift line numbers, so this procedure cites symbols only.
- `unicode61` tokenizes letters and digits of any script as word runs and treats punctuation, including the underscore, as separators, so tokens extracted with `[^\W_]+` correspond to what the index sees; on ASCII the pattern equals the current `[a-zA-Z0-9]+`.
- The OR rule is a retrieval-behavior change (Plan UNK-01, non-blocking): real-corpus recall is an owner-side check after implementation.

## Design decisions
- Join with `" OR "` for both the Japanese and the non-Japanese branches: `ORDER BY bm25(chunks_fts)` in `_SQL_FTS` already ranks by matched-term count and rarity, so widening the match set keeps ordering meaningful. FTS5 has no native minimum-should-match, so none is attempted.
- Change nothing else in the function: token source for Japanese (`_build_fts_tokens_ja`), quote stripping, the `_MAX_FTS_TOKENS` cap, the info log fields, and the empty-query returns stay as they are (`REQ-003`, `REQ-004`).

## Alternatives considered
- Keep AND and only fix tokenization: rejected, the recall collapse for long paraphrases remains.
- A minimum-should-match threshold or a configurable rule: rejected (no FTS5 primitive; speculative).

## Implementation
### Target file
`scripts/rag/repository.py`

### Procedure
1. In the non-Japanese branch of `_build_fts_query`, replace the token pattern `[a-zA-Z0-9]+` with `[^\W_]+`.
2. Change the final join of the quoted tokens from a space to `" OR "`.
3. Update the function docstring: tokens are double-quoted so `AND`/`OR`/`NOT`/`NEAR` in user text are literals, and the quoted tokens are joined with `OR` so a chunk matching a subset of terms is returned and ranked by BM25.

### Method
- The pattern is applied to `text` exactly where `re.findall` is called today; `has_japanese` routing is unchanged, so Hangul, Cyrillic, and accented Latin reach the Unicode branch while kana and CJK ideographs keep the Sudachi path.
- `" OR ".join(f'"{t}"' for t in sanitized)` keeps every token quoted; the only unquoted operator in the output is the join.

### Details
- Do not change `_MAX_FTS_TOKENS`, the sanitizing step (removing `"` and whitespace, dropping empty tokens), the logging of `original`, `used`, and `truncated`, or the `if not tokens` / `if not sanitized` early returns.
- Do not change `fts_search`, `_SQL_FTS`, or the module-level `fts_search` wrapper.
- Keep the module within the size gate: `uv run python tools/check_module_size.py`.

## Compatibility considerations
- `fts_search` now returns chunks that match any query term (previously all terms), ranked by BM25, and non-ASCII Latin, Cyrillic, and Hangul queries now produce lexical hits instead of an empty query. The query-builder signature, `fts_search` signature, and the schema are unchanged; no reindex is needed (query side only). Two existing exact-string tests are updated by the test procedure; every other existing test is unmodified.

## Security considerations
- Every token stays double-quoted with embedded quotes removed, so user text cannot inject FTS5 syntax; the `OR` keyword comes only from the join constant. The operator-like integration test runs hostile text through the real FTS5 engine.

## Rollback considerations
N/A: revert the commit (the OR rule lives in one function; no data or index change).

## Validation plan
- `uv run pytest tests/rag/test_rag_repository.py tests/rag/test_fts_japanese.py tests/rag/test_fts_fallback.py -q`, then `uv run pytest tests/rag -q`.
- `uv run ruff check scripts/rag/repository.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run radon cc scripts/rag/repository.py -s` (`_build_fts_query` stays B), `uv run python tools/check_module_size.py`.

## Completion criteria
- A multi-word query returns chunks matching any word, best BM25 first; accented, Cyrillic, and Hangul queries return a non-empty query and hits; operator-like text raises no FTS5 syntax error; the 20-token cap and the Japanese path are unchanged.
- All new and updated tests pass; the complexity grade of `_build_fts_query` is not worse than before.

## Out of Scope
- Replacing FTS5 or Sudachi, index-side tokenization, the memory module's `scripts/agent/memory/fts_query.py` (Plan UNK-02), the token cap, a configurable rule, ragrev006's signal changes, and deployment (a user decision after commit and push).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Change the token pattern, the join, and the docstring of `_build_fts_query` | Pending | — | — | |
| 2 | Run the new and updated tests, then `tests/rag` | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) and `radon cc` | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (OR join), `REQ-002` (Unicode tokens), `REQ-003` (quoting and cap kept), `REQ-004` (Japanese path and empty query unchanged)
- **Source issue**: issues/20261108-131008_ragrev005_fts-query-and-semantics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-164946_ragrev005_fts-query-and-semantics.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-121825
- **Related target files**: `scripts/rag/repository.py`
