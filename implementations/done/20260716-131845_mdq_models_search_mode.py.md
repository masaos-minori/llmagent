# Implementation: scripts/mcp_servers/mdq/models.py (restrict `SearchDocsRequest.mode` to `Literal["bm25"]`; remove `EmbeddingResult`)

Source plan: `plans/20260716-131500_plan.md`

## Goal

`SearchDocsRequest.mode` only accepts `"bm25"` (rejecting any other value
with a `pydantic.ValidationError` automatically), and the unused
`EmbeddingResult` TypedDict is removed — closing the config/schema surface
for the never-implemented hybrid search mode.

## Scope

**In:**
- `SearchDocsRequest.mode` (`scripts/mcp_servers/mdq/models.py:96`): change
  `mode: str | None = "bm25"` → `mode: Literal["bm25"] | None = "bm25"`.
- Remove `EmbeddingResult` (`scripts/mcp_servers/mdq/models.py:237-240`).
- Add `Literal` to the file's `typing` import if not already present.

**Out:**
- Any other field on `SearchDocsRequest` (`query`, `limit`, `path_prefix`,
  `tag_filter`, `heading_prefix`, `max_results_limit`,
  `max_total_result_chars`).
- `SearchResultResult`/`SearchResultItem` — unrelated, unchanged.
- `MdqConsistencyError` and any other exception class — unchanged.

## Assumptions

1. `Literal["bm25"]` (not `Literal["bm25", "grep"]`) is the correct
   restriction per the source plan's Assumption 4 / Unknowns table: no
   `mode="grep"` branch has ever existed in `search.py` — any non-`"hybrid"`
   value already silently falls through to the default FTS5 path today, and
   `grep_docs` is a fully separate, already-implemented tool for
   regex search. Introducing a `mode="grep"` alias would be new
   functionality, not cleanup, and is explicitly out of scope.
2. `EmbeddingResult` (a `TypedDict` at `models.py:237-240`) has zero
   importers anywhere in `scripts/` or `tests/` — verified via
   `rg -n "from mcp_servers.mdq.mdq_models import"` across the repo (this is
   a distinct class from the unrelated `agent.memory.types.EmbeddingResult`
   dataclass used elsewhere in the codebase; do not confuse the two).
3. This change must land in the same commit as `tools.py`'s description
   update (companion doc) and `search.py`'s hybrid-branch removal
   (companion doc) — otherwise the schema description still advertises
   `"grep"`/hybrid modes that the model now rejects, or `search.py`'s
   `mode == "hybrid"` branch becomes dead but not yet removed.

## Implementation

### Target file

`scripts/mcp_servers/mdq/models.py`

### Procedure

1. Open `scripts/mcp_servers/mdq/models.py`.
2. Check the top-of-file `typing` import block for `Literal`; if absent,
   add it (e.g. `from typing import Literal` or extend an existing
   `from typing import ...` line, matching the file's existing import
   style).
3. Locate line 96:
   ```python
   mode: str | None = "bm25"
   ```
   Change to:
   ```python
   mode: Literal["bm25"] | None = "bm25"
   ```
4. Locate and delete `EmbeddingResult` (current lines 237-240):
   ```python
   class EmbeddingResult(TypedDict):
       chunk_id: str
       embedding_score: float
       rank: int
   ```
5. If `TypedDict` has no other users in the file after this deletion,
   remove its import too — check via
   `grep -n "TypedDict" scripts/mcp_servers/mdq/models.py` (do not remove
   the import if `SearchResultResult`/`SearchResultItem` or any other
   class still uses `TypedDict`).

### Method

One field-type narrowing edit (`str` → `Literal["bm25"]`) and one class
deletion — no new validation code, since pydantic's `Literal` type enforces
rejection of unsupported values automatically at parse time.

### Details

- Do not add a custom `@field_validator`/`@validator` for `mode` — the
  `Literal` type annotation alone satisfies "reject unsupported modes with
  a validation error" per the source plan's Design section.
- Keep `mode`'s default (`"bm25"`) and optionality (`| None`) unchanged —
  only the allowed non-`None` value set narrows.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Type narrowed | `grep -n "mode: Literal" scripts/mcp_servers/mdq/models.py` | 1 match |
| `EmbeddingResult` removed | `grep -n "class EmbeddingResult" scripts/mcp_servers/mdq/models.py` | 0 matches |
| Rejects invalid mode | `PYTHONPATH=scripts uv run python -c "from mcp_servers.mdq.mdq_models import SearchDocsRequest; SearchDocsRequest(query='x', mode='hybrid')"` | raises `pydantic.ValidationError` |
| Accepts valid mode | `PYTHONPATH=scripts uv run python -c "from mcp_servers.mdq.mdq_models import SearchDocsRequest; print(SearchDocsRequest(query='x', mode='bm25').mode)"` | prints `bm25` |
| Lint | `uv run ruff check scripts/mcp_servers/mdq/models.py` | 0 errors |
| Type check | `uv run mypy scripts/mcp_servers/mdq/models.py` | no new errors |
| Targeted tests | `uv run pytest tests/test_mdq_search_modes.py -v` (once companion new-test doc lands) | all pass |
