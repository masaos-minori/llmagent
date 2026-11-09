## Goal
- Make the BM25 leg recall-oriented and script-neutral: combine query terms so a chunk matching a subset ranks by BM25 instead of being excluded, and tokenize non-Japanese text with a Unicode-aware pattern so accented, Cyrillic, and Hangul queries no longer produce an empty FTS query, without weakening FTS5 metacharacter quoting or the token cap.

## Priority
Medium

## Scope
- **In-Scope**:
  - `_build_fts_query` in `scripts/rag/repository.py`: term-combination rule (proposed: OR across quoted tokens, BM25-ranked by the existing `ORDER BY bm25(...)`) and a Unicode word-token pattern for the non-Japanese branch.
  - Unit tests for `_build_fts_query` and an integration test against an in-memory FTS5 table with the real schema (long query, accented query, Hangul/Cyrillic query, operator-like query).
  - A small deterministic fixture-corpus comparison (AND vs chosen rule) kept as a test, plus the doc update for the matching rule and tokenization boundary.
- **Out-of-Scope**:
  - Replacing FTS5 or Sudachi, index-side tokenization, the separate memory-module builder `scripts/agent/memory/fts_query.py`, raising or removing the token cap, a configurable rule.
- **Dependencies**: Related, no required order: the ragrev004 work (the search stage; no shared code file, both edit different parts of the RAG docs).

## Background
Review finding F-007. `_build_fts_query` (`scripts/rag/repository.py:87-120`) returns `" ".join(f'"{t}"' ...)`; FTS5 evaluates space-separated terms as an implicit AND, so every term must occur in one chunk. For text with no kana or CJK ideographs the token source is `re.findall(r"[a-zA-Z0-9]+", text)` (L93), so Hangul, Cyrillic, and accented words yield an empty query and `fts_search` returns `[]` silently (L198-201). The index uses `tokenize = 'unicode61'` (`scripts/db/schema_sql.py:67`), which tokenizes all Unicode word characters, so the query side is the narrower half. Existing tests (`tests/rag/test_rag_repository.py:473-520`, `tests/rag/test_fts_japanese.py`) cover quoting, the cap, and Japanese; none covers recall semantics or non-ASCII Latin. Found by adversarial verification at procedure time: `tests/rag/test_fts_japanese.py::TestBuildFtsQuery` asserts the exact AND-joined strings `'"食べ物" "美味しい"'` (Japanese tokens) and `'"hello" "world" "123"'` (English), so the OR join breaks those two tests; the other existing assertions use `in`, counts, or a single token and are unaffected (`tests/rag/test_rag_repository.py::TestBuildFtsQuery`, `TestBuildFtsQueryLogging`, the `fts_search` integration tests including the multi-word `test_english_multi_word_query` in `tests/rag/test_fts_fallback.py`, which assert at least one hit). The doc claims differ from code in two places (checked in Step 3): `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md:46` says an empty query is `'""'` while the code returns `""` and short-circuits, and says truncation is silent while the code logs it.

## Problem
BM25 recall collapses as the query grows, and non-ASCII Latin, Cyrillic, and Hangul queries get no lexical results at all, silently.

## Reason for Change
The hybrid design relies on BM25 to complement the vector leg; an over-strict query makes that leg dead weight for exactly the long paraphrases MQE generates.

## Implementation Intent
Prefer OR across quoted tokens because `ORDER BY bm25(chunks_fts)` already ranks chunks by how many and how rare the matched terms are, so widening the match set is safe for ordering; FTS5 has no native minimum-should-match, so a threshold would need custom ranking and is not planned. Replace `[a-zA-Z0-9]+` with a Unicode word pattern for the non-Japanese branch. Use the pattern `[^\W_]+` for the non-Japanese branch: it equals `[a-zA-Z0-9]+` on ASCII (an underscore still splits tokens, as `unicode61` does), so ASCII tokenization and the token cap are unchanged. Keep per-token quote stripping, wrapping every token in double quotes (so `AND`/`OR`/`NOT`/`NEAR` become literals), and the 20-token cap. The OR-versus-AND decision is validated on a deterministic fixture corpus in the tests and recorded in the doc; real-corpus recall remains an owner-side check (Unknowns).

## Requirements
- `REQ-001`: Terms are combined with `OR`; a ten-word query returns chunks that contain any subset of the words, ranked by BM25.
- `REQ-002`: The non-Japanese branch tokenizes Unicode word characters; a Latin-with-accents, Cyrillic, or Hangul query yields a non-empty FTS query.
- `REQ-003`: Every token stays double-quoted with embedded quotes removed; `AND`/`OR`/`NOT`/`NEAR` in the user text act as literals, never operators; the 20-token cap and its info log stay.
- `REQ-004`: Japanese tokenization (Sudachi POS filter) and the empty-query short-circuit are unchanged; only the join of the resulting tokens changes (the OR join applies to both branches).
- `REQ-005`: Tests cover long, accented, Hangul/Cyrillic, and operator-like queries at `_build_fts_query` and against an in-memory FTS5 table using the real schema, including an AND-versus-OR fixture comparison.
- `REQ-006`: The RAG docs state the matching rule, the tokenization boundary, and correct the two doc/code mismatches (empty query value, truncation logging).

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tests/rag/test_rag_repository.py` | Modify | Unit tests for rule, Unicode tokens, operator-like text, cap | `REQ-001`..`REQ-003`, `REQ-005` / AC-1..AC-3, AC-5 | `TestBuildFtsQuery` at L473-520 (checked in Step 3) | self | Verified |
| `tests/rag/test_fts_japanese.py` | Modify | Update the two exact-string assertions of `TestBuildFtsQuery` (Japanese and English) from the AND join to the OR join; add in-memory FTS5 integration with the real schema (L26-83): long, accented, Hangul/Cyrillic, AND-vs-OR fixture | `REQ-001`, `REQ-002`, `REQ-005` / AC-1, AC-2, AC-5 | File builds the real schema with `unicode61` (checked in Step 3) | self | Verified |
| `scripts/rag/repository.py` | Modify | OR join and Unicode token pattern in `_build_fts_query` (L87-120) | `REQ-001`..`REQ-004` / AC-1..AC-4 | Join at L120, ASCII regex at L93, `_SQL_FTS` L139-147 orders by `bm25` (checked in Step 3) | `tests/rag/test_rag_repository.py`, `tests/rag/test_fts_japanese.py` | Verified |
| `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md` | Modify | Matching rule, tokenization boundary, and the two corrections in the "Japanese FTS5 Tokenization" paragraph (L46) | `REQ-006` / AC-6 | L46 states `[a-zA-Z0-9]+`, `'""'`, silent truncation (checked in Step 3) | docs gates | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/db/schema_sql.py` | `chunks_fts` DDL, `unicode61` tokenizer, trigger input `COALESCE(normalized_content, content)` | `REQ-002` |
| `scripts/rag/stages/search.py` | Only production caller of `fts_search` (via `RagRepository`) | `REQ-001` |
| `scripts/agent/memory/fts_query.py` | Separate builder with the same shape; explicitly out of scope, recorded for the owner | Scope |
| `docs/21_rag/rag_03_04_query_pipeline-search-stages.md` | States BM25 usage; edited by the ragrev004 Plan, not here | `REQ-006` |

## Acceptance Criteria
- AC-1 (`REQ-001`): a ten-word query against the fixture corpus returns chunks containing a subset of the words, best BM25 first; the AND variant returns none for the same fixture.
- AC-2 (`REQ-002`): `_build_fts_query("café résumé")`, a Cyrillic query, and a Hangul query each return a non-empty string.
- AC-3 (`REQ-003`): `_build_fts_query('a AND b OR NOT NEAR')` yields only quoted tokens; running it through FTS5 raises no syntax error; 100 words yield at most 20 tokens.
- AC-4 (`REQ-004`): the existing Japanese and empty-query tests pass unmodified, except the two exact-string `TestBuildFtsQuery` assertions in `tests/rag/test_fts_japanese.py`, which are updated to the OR form in Phase 1 (same tokens, joined with ` OR `).
- AC-5 (`REQ-005`): the new tests fail on HEAD where they target the changed behavior.
- AC-6 (`REQ-006`): the doc names the OR rule, the Unicode boundary, the real empty-query value, and the logged truncation; docs checkers pass.

## Tests
- `REQ-001`: unit (joined with ` OR `) and fixture-corpus integration (AND returns nothing, OR returns ranked subset).
- `REQ-002`: parametrized accented, Cyrillic, Hangul queries (unit and in-memory FTS5 hit).
- `REQ-003`: operator-like text through the real FTS5 engine.
- `REQ-004`: existing tests unmodified apart from the two join-form assertions named in AC-4.
- `REQ-005`: the above on the real schema.

## Documentation Impact
Yes (`REQ-006`): `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md` (located via `docs/00_index.md` RAG rows), intent and failure behavior only. Run `check_docs_quality`, `check_docs_structure`, `check_docs_content_policy`, `check_docs_consistency --domain rag`, `check_docs_japanese`.

## Assumptions
- Overlap judgment (Step 2, `tools/check_plan_target_overlaps.py`): `plans/20261108-165114_ragrev006_rrf-merge-drops-signals.md` shares `scripts/rag/repository.py` and `tests/rag/test_rag_repository.py`; it changes `rrf_merge`, `_dedup_hits`, and the signal assignment inside `vector_search` / `fts_search`, while this Plan changes only `_build_fts_query` and its tests; the designs are compatible with no required order (ragrev006 lists no dependency on this Plan). Both edit `repository.py`, so line numbers shift: the procedures cite symbols. `plans/20261108-164823_ragrev004_search-bm25-coupling.md` touches `scripts/rag/stages/search.py` and a different doc; compatible.
- OR with BM25 ordering is the proposed default; it is a retrieval-behavior change and the owner may prefer to confirm it before implementation (UNK-01). RRF fusion consumes the ranked list, so a larger FTS candidate set changes fusion inputs only through ranking.
- `unicode61` tokenizes Hangul and Cyrillic as word runs, so Unicode query tokens can match the index (the standard `unicode61` behavior; the in-memory integration test proves it for the tested scripts).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Recall and noise of OR on the real corpus, notably for Japanese `normalized_content` | No measurement on the production corpus | Owner-side offline comparison after implementation; fixture test covers only the rule | False |
| UNK-02 | Whether the memory module's separate `build_fts_query` should get the same change | Owner intent | Separate Issue if wanted (Out-of-Scope here) | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/repository.py` | Modify | Medium (all lexical retrieval; `radon`: `_build_fts_query` B (9)) | 1 | N/A | not applicable (rsynced) |
| `tests/rag/test_rag_repository.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_fts_japanese.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Path B (more than 3 target files). Architecture: the change is confined to a leaf helper of `rag/repository.py`; `lint-imports` shows 6 contracts kept at plan time and no import changes are planned. Dependency graph: `_build_fts_query` has one production caller (`RagRepository.fts_search`, `repository.py:198`), reached through `scripts/rag/stages/search.py`; tests import it directly (`tests/rag/test_rag_repository.py`, `tests/rag/test_fts_japanese.py`). Historical: `repository.py` 1 commit in 30 days. Operational: no DB schema or index change (query side only), so no reindex is needed.

Alternatives: (a) keep AND and only fix tokens, rejected (recall collapse remains); (b) minimum-should-match, rejected (no FTS5 primitive; custom ranking out of scope); (c) a configurable rule, rejected (speculative). Chosen: OR plus Unicode tokens.

Persisted schema check (`rules/persisted-schema-change.md`): not applicable, no DDL, version, or migration change.

Validation baseline: `vulture`/`bandit` pre-existing findings recorded in `plans/20261108-164302_ragrev001_mqe-malformed-response-abort.md` (source unchanged); `diff-cover`: none at plan time, 90 percent at implementation.

## Implementation steps
1. **Phase 1: Tests first**
   - [ ] Unit tests for rule, Unicode, operator-like, cap (`REQ-001`..`REQ-003`, `REQ-005`; `tests/rag/test_rag_repository.py`)
   - [ ] In-memory FTS5 integration and the AND-versus-OR fixture (`REQ-001`, `REQ-002`, `REQ-005`; `tests/rag/test_fts_japanese.py`)
2. **Phase 2: Query construction**
   - [ ] OR join and Unicode token pattern (`REQ-001`..`REQ-004`; `scripts/rag/repository.py`)
3. **Phase 3: Documentation**
   - [ ] Matching rule, tokenization boundary, and two corrections (`REQ-006`; `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md`)
4. **Phase 4: Deployment & Verification**
   - [ ] `uv run pytest tests/rag -q`, lint/type gates, docs gates; deploy hand-off to `skills/deploy/SKILL.md` after commit and push, at the user's decision (all requirements; `scripts/rag/repository.py`)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/repository.py` | Unit and in-memory FTS5 integration | `uv run pytest tests/rag/test_rag_repository.py tests/rag/test_fts_japanese.py -q` | new tests fail on HEAD, pass after |
| whole RAG | Regression | `uv run pytest tests/rag -q` | green |
| touched code | Static | `uv run ruff check`, `uv run mypy`, `PYTHONPATH=scripts uv run lint-imports` | clean |
| docs | Docs gates | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag`, `check_docs_japanese.py` | no findings |

## Risks
- **Risk**: OR raises noise for Japanese `normalized_content` and changes production ranking → **Mitigation**: BM25 ordering contains it; UNK-01 owner-side measurement; the rule lives in one function and is revertable alone.
- **Risk**: a Unicode pattern admits tokens that `unicode61` splits differently (for example punctuation-joined words) → **Mitigation**: tokens are quoted phrases, so `unicode61` re-tokenizes them consistently; integration test on the real schema.
- **Risk**: weakening escaping → **Mitigation**: quote handling is unchanged and AC-3 runs operator-like text through the real FTS5 engine.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: tests first | In Progress | — | — |  |
| 2 | Phase 2: query construction | In Progress | — | — |  |
| 3 | Phase 3: documentation | In Progress | — | — |  |
| 4 | Phase 4: deployment and verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261109-121825_01_tests_rag_test_rag_repository.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261109-121825_02_tests_rag_test_fts_japanese.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261109-121825_03_scripts_rag_repository.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261109-121825_04_docs_21_rag_rag_03_06_query_pipeline-helpers-and-cache.md.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261108-131008_ragrev005_fts-query-and-semantics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261108-164946
- **Related target files**: `scripts/rag/repository.py`, `tests/rag/test_rag_repository.py`, `tests/rag/test_fts_japanese.py`, `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Implementation Intent; `repository.py:120` | `scripts/rag/repository.py` | Phase 2 | AC-1 | fixture integration test | Confirmed by repository evidence |
| REQ-001 | Testing Expectations | `tests/rag/test_rag_repository.py` | Phase 1 | AC-1 | unit join test | Explicit in issue |
| REQ-001 | Testing Expectations | `tests/rag/test_fts_japanese.py` | Phase 1 | AC-1 | AND-vs-OR fixture | Explicit in issue |
| REQ-002 | Required Changes 2; `repository.py:93` | `scripts/rag/repository.py` | Phase 2 | AC-2 | Unicode query tests | Confirmed by repository evidence |
| REQ-002 | Testing Expectations | `tests/rag/test_rag_repository.py` | Phase 1 | AC-2 | Unicode query tests | Explicit in issue |
| REQ-002 | Testing Expectations | `tests/rag/test_fts_japanese.py` | Phase 1 | AC-2 | in-memory hit test | Explicit in issue |
| REQ-003 | Required Changes 3; Constraints | `scripts/rag/repository.py` | Phase 2 | AC-3 | operator-like query test | Explicit in issue |
| REQ-003 | Testing Expectations | `tests/rag/test_rag_repository.py` | Phase 1 | AC-3 | operator-like query test | Explicit in issue |
| REQ-004 | Constraints | `scripts/rag/repository.py` | Phase 2 | AC-4 | existing Japanese tests | Derived from confirmed evidence |
| REQ-005 | Testing Expectations | `tests/rag/test_rag_repository.py` | Phase 1 | AC-5 | new tests fail on HEAD | Explicit in issue |
| REQ-005 | Testing Expectations | `tests/rag/test_fts_japanese.py` | Phase 1 | AC-5 | new tests fail on HEAD | Explicit in issue |
| REQ-006 | Required Changes 1; Documentation Impact; doc L46 | `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md` | Phase 3 | AC-6 | docs gates | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261109-121825 -->