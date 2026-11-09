## Goal
Pin the new `_build_fts_query` contract at unit level (`REQ-001`: terms joined with OR; `REQ-002`: Unicode tokens for the non-Japanese branch; `REQ-003`: tokens stay double-quoted, operator-like words stay literal, the 20-token cap stays; `REQ-005`: tests written first and failing on HEAD).

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies only `tests/rag/test_rag_repository.py`. The integration tests and the two join-form assertion updates are in `tests/rag/test_fts_japanese.py` (next procedure); production code is changed by the `repository.py` procedure.

## Assumptions
- Execution order: Plan Phase 1, first. The new tests fail on the current HEAD for the changed behavior (AND join, ASCII-only token pattern).
- Overlap judgment (Plan Assumptions): `plans/20261108-165114_ragrev006_rrf-merge-drops-signals.md` also adds tests to this file (merge and signal tests); the tests here are limited to `TestBuildFtsQuery` and do not touch its `RagScorer` or `fts_search` result tests (compatible, no required order).
- Existing `TestBuildFtsQuery` and `TestBuildFtsQueryLogging` assertions use `in`, counts of quote characters, single tokens, or log text, so they pass unchanged under the OR join and are not edited.
- Why this row is not a companion of the `repository.py` document: the test design (fixtures, expected strings) is a decision of its own and the Plan orders tests before code.

## Design decisions
- Assert exact strings for short queries (the OR join is the contract) and structural checks (`split(" OR ")`) for the cap and operator-like cases.
- Cover ASCII equivalence explicitly (an underscore still splits tokens), so the Unicode pattern cannot silently change ASCII tokenization.

## Alternatives considered
N/A: test-only row.

## Implementation
### Target file
`tests/rag/test_rag_repository.py`

### Procedure
1. Add six tests to `TestBuildFtsQuery`: `test_terms_joined_with_or` (new), `test_single_token_has_no_or` (new), `test_non_ascii_queries_yield_tokens` (new) (new, parametrized over accented Latin, Cyrillic, and Hangul), `test_operator_like_words_stay_quoted_literals` (new), `test_token_cap_holds_with_or_join` (new), and `test_underscore_still_splits_ascii_tokens` (new).
2. Do not edit any existing test in this file.

### Method
- `test_terms_joined_with_or` (new): `_build_fts_query("alpha beta gamma") == '"alpha" OR "beta" OR "gamma"'` (AC-1 at unit level).
- `test_single_token_has_no_or` (new): `_build_fts_query("alpha") == '"alpha"'`.
- `test_non_ascii_queries_yield_tokens` (new): for `"café résumé"`, `"привет мир"`, and `"안녕하세요 세계"` the result is non-empty and equals the quoted tokens joined with ` OR ` (AC-2).
- `test_operator_like_words_stay_quoted_literals` (new): `_build_fts_query('a AND b OR NOT NEAR').split(" OR ")` equals `['"a"', '"AND"', '"b"', '"OR"', '"NOT"', '"NEAR"']`, proving the user's operator words are quoted literals and the only unquoted `OR` is the join (AC-3).
- `test_token_cap_holds_with_or_join` (new): for 100 distinct words the result splits into exactly 20 quoted tokens (the existing cap) (AC-3).
- `test_underscore_still_splits_ascii_tokens` (new): `_build_fts_query("foo_bar") == '"foo" OR "bar"'`.

### Details
- Use only the module-level import already present (`_build_fts_query`); no database or fixture is needed.
- Keep distinct, recognizable tokens so a wrong split cannot pass by accident.

## Compatibility considerations
N/A: test-only.

## Security considerations
N/A: pure string tests; the operator-like case documents that user-supplied operator words are neutralized by quoting.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Before the production change: `uv run pytest tests/rag/test_rag_repository.py -q -k "BuildFtsQuery"`; the new tests must fail on HEAD (record the failing assertions); the existing ones pass.
- After `repository.py` is changed: the same command is green, then `uv run pytest tests/rag -q`.
- `uv run ruff check tests/rag/test_rag_repository.py`.

## Completion criteria
- Six new tests exist, fail on the pre-change HEAD, and pass after the `repository.py` procedure; no existing test in the file was edited.

## Out of Scope
- `scripts/rag/repository.py`, `tests/rag/test_fts_japanese.py`, the docs, ragrev006's merge and signal tests, and the memory-module FTS builder.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the six `_build_fts_query` unit tests | Pending | — | — | |
| 2 | Run them on the pre-change HEAD and record that they fail (AC-5) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (OR join), `REQ-002` (Unicode tokens), `REQ-003` (quoting and cap), `REQ-005` (tests first)
- **Source issue**: issues/20261108-131008_ragrev005_fts-query-and-semantics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-164946_ragrev005_fts-query-and-semantics.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-121825
- **Related target files**: `tests/rag/test_rag_repository.py`
