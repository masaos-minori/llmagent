## Goal

Make merged hits keep both retrieval signals regardless of list order: `RagScorer.rrf_merge` and `_dedup_hits` combine per-chunk `distance` and `bm25_score` across all lists (minimum of each), and `vector_search` / `fts_search` set only the signal they produce, so an absent signal stays `None` (`REQ-001`..`REQ-006`: signal combination, absent marker, unchanged ranking).

## Scope
**Release unit**: ragrev006-core

- In scope: `rrf_merge`, `_dedup_hits`, the hit construction in `vector_search` and `fts_search`, and one new private combining helper, all in `scripts/rag/repository.py`.
- Out of scope: the RRF score formula, `rrf_k`, ordering, fusion strategy, rerank, `rag_min_score`.

## Assumptions

- Re-verified this cycle (after the ragrev005 repository procedure landed): `rrf_merge` (L231) writes `meta[cid] = item` at `scripts/rag/repository.py:241`; `_dedup_hits` keeps only the first occurrence (`repository.py:336-355`); `vector_search` sets `distance=float(r["distance"] or 0.0)` (L181) and `fts_search` sets `bm25_score=float(r["bm25_score"] or 0.0)` (L212).
- Minimum is the combination rule (smaller L2 distance and more negative BM25 are better); this is a design decision recorded in the Plan, not an Issue statement.
- Requires `..._01_scripts_shared_types.py.md` first: the `None` defaults on `RawHit` are what lets the search functions omit the other signal.
- Overlap with `plans/20261108-164946_ragrev005_fts-query-and-semantics.md` (procedure `implementations/20261109-121825_03_scripts_rag_repository.py.md`): compatible. That procedure edits `_build_fts_query`; this one edits `rrf_merge`, `_dedup_hits`, and the two search methods. Line numbers cited here may shift if that procedure runs first; locate code by symbol name.
- `fts_search` and `vector_search` keep `distance` / `bm25_score` as `None` when a row value is SQL NULL instead of falling back to `0.0`.

## Design decisions

- One small module-private helper `_min_signal` (new) returns the smaller of two optional floats, treating `None` as absent; both merge functions use it, which keeps each function at complexity grade A.
- `rrf_merge` keeps `meta[cid] = item` for `content` / `url` / `title` (same chunk, same text) and tracks the two signals in separate per-chunk dicts, so the score accumulation and the sort are untouched (`REQ-005`).

## Alternatives considered

- Per-chunk signal flags: rejected (more state, same ambiguity risk).
- Taking the first or last list's signal: rejected (the order dependence is the defect).

## Implementation
### Target file
`scripts/rag/repository.py`

### Procedure
1. Add `_min_signal(a: float | None, b: float | None) -> float | None` (new) near `_dedup_hits`: return `b` if `a is None`, `a` if `b is None`, otherwise `min(a, b)`.
2. In `rrf_merge`, add `distances: dict[int, float | None]` and `bm25s: dict[int, float | None]`; inside the existing loop update both with `_min_signal(distances.get(cid), item.distance)` and the same for `bm25_score`; build each `MergedHit` with `distance=distances[cid]` and `bm25_score=bm25s[cid]`. Leave `scores`, `meta`, the sort, and `rrf_score` unchanged.
3. In `_dedup_hits`, keep first-occurrence order but, for a chunk already seen, update the stored `MergedHit`'s `distance` and `bm25_score` through `_min_signal` (new) (store hits in a `dict[int, MergedHit]` and return `list(...values())`).
4. In `vector_search`, build `RawHit` with `distance=float(r["distance"]) if r["distance"] is not None else None` and no `bm25_score`; in `fts_search`, build `RawHit` with `bm25_score` likewise and no `distance`.

### Method
- `_min_signal` (new) is a pure function; no mutation of input hits (`RawHit` instances are never changed, only the new `MergedHit`).
- `_dedup_hits` sets `rrf_score=0.0` exactly as today.

### Details
- The `use_rrf=False` path in `scripts/rag/stages/fusion.py` calls `_dedup_hits` and `use_rrf=True` calls `rrf_merge`; neither call site changes (Reference File).
- Mixed-type input lists (`list[list[RawHit]] | list[list[RagHit]]`) keep their current annotations; `MergedHit` and `RankedHit` inputs carry the same two fields.
- After editing, run `uv run python tools/check_module_size.py` (the file must not grow past its recorded size gate) and `uv run radon cc scripts/rag/repository.py -s -n C` (no new grade C).

## Compatibility considerations

- Signature and return types of `rrf_merge`, `_dedup_hits`, `vector_search`, `fts_search` are unchanged; only field values for absent signals change from `0.0` to `None`.
- The fused `rrf_score` values and output order are identical for the same inputs (`REQ-005`).
- Consumers: `_apply_rerank_scores` copies the fields and `_hit_to_dict` serializes them; both tolerate `None`.

## Security considerations

N/A: in-memory merge logic over already-parameterized query results; no new input, SQL, or trust boundary.

## Rollback considerations

N/A: revert the commit (ships with the types procedure in Release unit `ragrev006-core`).

## Validation plan

- `uv run pytest tests/rag/test_rag_repository.py tests/rag/test_fts_fallback.py -q` (new tests from `..._03_tests_rag_test_rag_repository.py.md` fail on HEAD, pass after).
- `uv run pytest tests/rag tests/mcp_servers/rag_pipeline tests/agent/test_rag_get_cfg.py -q`
- `uv run ruff check scripts/rag/repository.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit scripts/rag/repository.py`.
- `uv run python tools/check_module_size.py` and `uv run python tools/check_docstrings.py`.

## Completion criteria

- Vector-plus-FTS merges keep both signals in either list order; a signal absent from every list is `None`.
- Across several lists of one kind, merged `distance` and `bm25_score` are the minimums.
- `_dedup_hits` returns the same combined signals.
- `rrf_score` and ordering match the pre-change snapshot; mypy, ruff, lint-imports, and the regression suites pass.

## Out of Scope

- `scripts/shared/types.py`, tests, and docs (separate procedures).
- Changes to `_build_fts_query` (ragrev005) and to rerank or the MCP service.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_min_signal` (new) and update `rrf_merge` and `_dedup_hits` | Completed | 20261109-163321 | 20261109-163438 | _min_signal added above _dedup_hits; rrf_merge per-chunk distances/bm25s dicts; _dedup_hits stores dict[int, MergedHit] and combines on re-encounter; scores/meta/sort/rrf_score untouched |
| 2 | Make `vector_search` / `fts_search` set only their own signal | Completed | — | 20261109-163438 | vector_search/fts_search: own signal via 'float(...) if ... is not None else None', other signal omitted (None by default); fetch_full_document untouched (no signals, correct) |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the Plan's regression suites | Completed | 20261109-163438 | 20261109-164557 | targeted pytest 77 passed; ruff check/format clean after one format pass; mypy clean; lint-imports 6 kept; bandit clean; check_module_size ALL OK; check_docstrings no new violations; radon: no grade C+; Plan regression suites deferred to unit-end full run unit-end run: Plan regression suites green (full suite 12055 passed, diff-cover 100%) |

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
- **Requirement ID**: `REQ-001`..`REQ-005` (signal combination, absent marker, unchanged ranking), `REQ-006` (consumers handle `None`)
- **Source issue**: issues/20261108-131010_ragrev006_rrf-merge-drops-signals.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-165114_ragrev006_rrf-merge-drops-signals.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-133509
- **Related target files**: `scripts/rag/repository.py`