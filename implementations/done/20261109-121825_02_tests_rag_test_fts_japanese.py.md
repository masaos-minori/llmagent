## Goal
Update the two exact-string `_build_fts_query` assertions that encode the AND join, and add real-FTS5 integration tests for recall, Unicode queries, and operator-like text (`REQ-001`, `REQ-002`, `REQ-003`, `REQ-005`), written before the production change.

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies only `tests/rag/test_fts_japanese.py`.

## Assumptions
- Execution order: Plan Phase 1, after `tests/rag/test_rag_repository.py` and before `scripts/rag/repository.py`.
- The two assertions in `TestBuildFtsQuery` (`test_build_fts_query_ja_extracts_nouns_verbs_adjectives`, `test_build_fts_query_en_uses_ascii_extraction`) compare the exact AND-joined strings and fail under the OR join; this was found by adversarial verification and is recorded in the Plan. They are edited, not deleted; the token sets they assert are unchanged. `test_build_fts_query_escapes_fts_metacharacters` (single token) needs no change.
- Why this row is not a companion of the `repository.py` document: the integration fixtures are a design decision of their own and the Plan orders tests before code.
- Hangul and Cyrillic matching depends on `unicode61` as built into the local SQLite. If a case does not match on this build, report it as a `Plan Gap` instead of weakening the assertion (Plan Assumptions).

## Design decisions
- Reuse the file's `db` fixture, `_FakeSQLiteHelper`, `_insert_doc`, `_insert_chunk`, and `_fts_rowids` helpers and call the module-level `fts_search(query, top_k=..., db=db)`, so the tests run the real schema and the real query builder.
- The AND-versus-OR comparison runs the old AND form directly through `_fts_rowids` and the new behavior through `fts_search`, on one fixture corpus.

## Alternatives considered
N/A: test-only row.

## Implementation
### Target file
`tests/rag/test_fts_japanese.py`

### Procedure
1. In `TestBuildFtsQuery`, change the expected strings to the OR form: `'"食べ物" OR "美味しい"'` and `'"hello" OR "world" OR "123"'`.
2. Add a class `TestFtsRecallAndUnicode` (new) with four tests: `test_long_query_matches_subset_ranked_by_bm25` (new), `test_accented_query_hits_indexed_chunk` (new), `test_cyrillic_and_hangul_queries_hit_indexed_chunks` (new), and `test_operator_like_text_is_literal_in_real_fts5` (new).

### Method
- `test_long_query_matches_subset_ranked_by_bm25` (new): insert three chunks of similar length on one document: A contains six of ten query words, B contains two, C contains none; assert `fts_search(ten_word_query, top_k=5, db=db)` returns A then B and not C (AC-1), and assert the AND form of the same ten words run through `_fts_rowids` returns `[]` (the fixture comparison).
- `test_accented_query_hits_indexed_chunk` (new): content `"Café résumé guide"`, query `"café résumé"`, assert one hit (AC-2).
- `test_cyrillic_and_hangul_queries_hit_indexed_chunks` (new): one chunk each for `"Привет мир"` and `"안녕하세요 세계"`, query with the same words, assert one hit per query (AC-2).
- `test_operator_like_text_is_literal_in_real_fts5` (new): a chunk containing `"alpha"`; query `"alpha AND beta OR NOT NEAR"`; assert no `sqlite3.OperationalError` is raised and the chunk is returned (the OR join makes the single matching token enough) (AC-3).

### Details
- Keep chunk contents of comparable length so the BM25 length normalization does not decide the order; choose the six-versus-two matched-word split with distinct words.
- Do not patch `_build_fts_tokens_ja` in the new tests; the non-Japanese branch does not use it.
- Do not touch the trigger and lifecycle tests.

## Compatibility considerations
N/A: test-only; the two edited assertions follow the new contract and are the only existing tests whose expected values change.

## Security considerations
N/A: in-memory databases and dummy text; the operator-like test runs hostile-looking text through the real engine and expects no syntax error.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Before the production change: `uv run pytest tests/rag/test_fts_japanese.py -q`; the two edited assertions and the four new tests fail on HEAD (record the failures).
- After `repository.py` is changed: the same command is green; then `uv run pytest tests/rag -q`.
- `uv run ruff check tests/rag/test_fts_japanese.py`.

## Completion criteria
- The two assertions use the OR form; the four new tests exist, fail on the pre-change HEAD, and pass after the `repository.py` procedure.
- No other existing test in the file changed.

## Out of Scope
- `scripts/rag/repository.py`, `tests/rag/test_rag_repository.py`, the docs, and real-corpus recall measurement (Plan UNK-01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the two join-form assertions and add the four integration tests | Completed | 20261109-152648 | 20261109-152818 |  |
| 2 | Run them on the pre-change HEAD and record that they fail (AC-5) | Completed | — | 20261109-152818 | AC-5: 7 fail on HEAD — 2 edited join assertions (space vs OR) + long-query/accented/Cyrillic/Hangul/operator integration tests (ASCII-only regex drops Unicode -> empty; AND join needs all terms); existing tests pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261109-152818 | ruff format/check clean; full-suite green run deferred to repository.py procedure (03) |

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
- **Requirement ID**: `REQ-001` (OR recall), `REQ-002` (Unicode queries), `REQ-003` (operator-like text), `REQ-005` (real-schema tests)
- **Source issue**: issues/20261108-131008_ragrev005_fts-query-and-semantics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-164946_ragrev005_fts-query-and-semantics.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-121825
- **Related target files**: `tests/rag/test_fts_japanese.py`