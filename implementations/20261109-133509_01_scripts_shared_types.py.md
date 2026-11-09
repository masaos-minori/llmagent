## Goal

Make `distance` and `bm25_score` on the three RAG hit dataclasses (`RawHit`, `MergedHit`, `RankedHit`) explicitly optional with a `None` default, so an absent retrieval signal is distinguishable from a real `0.0` (`REQ-006`: optional signal fields with `None` default).

## Scope
**Release unit**: ragrev006-core

- In scope: the six field declarations in `scripts/shared/types.py` (two per dataclass) and the `RawHit` / `MergedHit` / `RankedHit` docstrings if they need one clause about the marker.
- Plan: `plans/20261108-165114_ragrev006_rrf-merge-drops-signals.md` (Plan step 2, first bullet).

## Assumptions

- The current declarations are `distance: float = 0.0` and `bm25_score: float = 0.0` at `scripts/shared/types.py:132-133`, `144-145`, `157-158` (re-verified at generation time).
- Production readers of the two fields are `_apply_rerank_scores` in `scripts/rag/llm_prompts.py:213-214` (copy only) and `dataclasses.asdict` in `_hit_to_dict` of `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py` (serialization only); `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py:201-202` already types both `float | None`. No production code under `scripts/` compares or formats them (`rg "\.distance|\.bm25_score" scripts/` outside `repository.py` shows only the memory retriever, which uses its own types).
- `tests/rag/test_rag_repository.py` is also the Related Test of row 2 (`scripts/rag/repository.py`), so it keeps its own procedure (`..._03_tests_rag_test_rag_repository.py.md`) instead of being a companion here.
- This change must land together with `..._02_scripts_rag_repository.py.md`; the `None` defaults are only meaningful once `vector_search` / `fts_search` stop filling the other signal (Release unit `ragrev006-core`).

## Design decisions

- Use `float | None = None` on all three dataclasses (no flag field, no NaN); this matches the existing MCP response TypedDict.
- Keep field order and the other defaults unchanged so every existing keyword or positional construction stays valid.

## Alternatives considered

- A separate per-signal presence flag field: rejected (more state, same ambiguity risk).
- A NaN marker: rejected (breaks equality and sorting, serializes badly).

## Implementation
### Target file
`scripts/shared/types.py`

### Procedure
1. In `RawHit`, `MergedHit`, and `RankedHit`, change `distance: float = 0.0` to `distance: float | None = None` and `bm25_score: float = 0.0` to `bm25_score: float | None = None`.
2. Add one short clause to each class docstring only where it helps: `None` means the signal was not produced by any list.

### Method
- Edit the six declarations in place; do not reorder fields.
- `RankedHit.rerank_score` already uses `float | None = None`; follow that spelling.

### Details
- After the edit, run `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`; the expected new findings are limited to `scripts/rag/repository.py` assignments handled by the sibling procedure. Any finding in `scripts/rag/llm_prompts.py` means a consumer assumed a non-`None` float and must be reported as a Plan Gap (that file is a Reference File, not a target).
- Blast radius (`rules/toolchain.md` Impact-radius check): run `rg -l "RawHit|MergedHit|RankedHit" tests/ | wc -l` before editing and record the count; keyword construction is unaffected by this change.

## Compatibility considerations

- Constructors: keyword and positional calls keep working because only the defaults and annotations change.
- Behavior: code that read the old `0.0` default now sees `None`; the in-repo readers only copy or serialize. External JSON clients of the MCP response may previously have seen `0.0` and now see `null` (Plan UNK-01: the MCP schema already permits `null`; report it at implementation).

## Security considerations

N/A: in-memory dataclass annotations only; no trust boundary or input handling changes.

## Rollback considerations

N/A: revert the commit (the sibling repository procedure ships in the same Release unit and is reverted with it).

## Validation plan

- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`
- `uv run ruff check scripts/shared/types.py` and `uv run ruff format --check scripts/shared/types.py`
- `PYTHONPATH=scripts uv run lint-imports`
- `uv run pytest tests/rag tests/mcp_servers/rag_pipeline tests/agent/test_rag_get_cfg.py -q`

## Completion criteria

- All three dataclasses declare both fields as `float | None = None`.
- mypy, ruff, and lint-imports are clean for the file.
- The regression suites above pass, with only intended `0.0`-assumption adjustments (made in the tests procedure).

## Out of Scope

- Merge and search logic (`scripts/rag/repository.py`), tests, and documentation (separate procedures).
- Any change to `rrf_score`, `rerank_score`, or `rag_min_score`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Change the six field declarations in `scripts/shared/types.py` | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`): ruff, mypy, lint-imports, regression suites | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (optional signal fields defaulting to `None`)
- **Source issue**: issues/20261108-131010_ragrev006_rrf-merge-drops-signals.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-165114_ragrev006_rrf-merge-drops-signals.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-133509
- **Related target files**: `scripts/shared/types.py`
