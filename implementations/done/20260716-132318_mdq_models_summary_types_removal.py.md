# Implementation: scripts/mcp_servers/mdq/models.py (remove `use_summary`, `ChunkSummary`, `GetChunkSummaryResponse`)

Source plan: `plans/20260716-131559_plan.md`

Note: distinct from `implementations/20260716-131845_mdq_models_search_mode.py.md`
(plan 04, `mode`/`EmbeddingResult`). Both touch `models.py` but different,
non-overlapping classes/fields — apply both.

## Goal

Remove `GetChunkRequest.use_summary`, and the `ChunkSummary` TypedDict /
`GetChunkSummaryResponse` BaseModel — both confirmed to have zero importers
anywhere in the repo.

## Scope

**In:**
- Remove `use_summary: bool = False` from `GetChunkRequest`
  (`scripts/mcp_servers/mdq/models.py:108`).
- Delete `ChunkSummary` (`TypedDict`, lines 44-49).
- Delete `GetChunkSummaryResponse` (`BaseModel`, lines 160-166).

**Out:**
- `GetChunkRequest.chunk_id`, `.with_neighbors`, `.max_chars_per_chunk` —
  unchanged.
- `GetChunkResponse` (lines 155-157, immediately above
  `GetChunkSummaryResponse`) — a distinct, still-used class; do not confuse
  the two by name similarity.
- `ParsedSectionRequest` (lines 52-53, immediately below `ChunkSummary`) —
  unrelated, unchanged.

## Assumptions

1. `ChunkSummary` and `GetChunkSummaryResponse` have zero importers
   anywhere in `scripts/` or `tests/` — verified via
   `rg -n "ChunkSummary|GetChunkSummaryResponse" scripts/ tests/` showing
   only the two definition sites in `models.py`.
2. This change must land in the same commit as the companion `service.py`
   doc (removes the `req.use_summary` read inside `get_chunk()`) —
   otherwise `service.py` references a field this doc removes from the
   model.
3. `GetChunkRequest` has no explicit `model_config` setting `extra=` in
   this file (confirmed via `grep -n "model_config" models.py` returning
   no matches) — pydantic v2's default (`extra="ignore"`) applies, meaning
   a caller that still sends `use_summary=True` after this field is
   removed will have it silently ignored, not rejected with a
   `ValidationError`. This resolves the source plan's Unknowns table
   second row: the companion `tests/test_mdq_get_chunk_behavior.py` doc
   must test for silent-ignore behavior, not for a raised validation
   error.

## Implementation

### Target file

`scripts/mcp_servers/mdq/models.py`

### Procedure

1. Open `scripts/mcp_servers/mdq/models.py`.
2. Delete `ChunkSummary` in full (current lines 44-49):
   ```python
   class ChunkSummary(TypedDict):
       chunk_id: str
       summary: str
       summary_model: str
       content_hash: str
       created_at: str
   ```
3. Locate `GetChunkRequest` (current lines 104-108):
   ```python
   class GetChunkRequest(BaseModel):
       chunk_id: str
       with_neighbors: bool | None = False
       max_chars_per_chunk: int | None = None
       use_summary: bool = False
   ```
   Remove the `use_summary: bool = False` line, leaving:
   ```python
   class GetChunkRequest(BaseModel):
       chunk_id: str
       with_neighbors: bool | None = False
       max_chars_per_chunk: int | None = None
   ```
4. Delete `GetChunkSummaryResponse` in full (current lines 160-166):
   ```python
   class GetChunkSummaryResponse(BaseModel):
       chunk_id: str
       summary: str
       summary_model: str
       content_hash: str
       created_at: str
       headings: list[str]
   ```
5. After deleting `ChunkSummary`, check whether `TypedDict` still has other
   users in the file (`grep -n "TypedDict" scripts/mcp_servers/mdq/models.py`)
   — do not remove the import if other TypedDicts remain (e.g.
   `ParsedSectionRequest`, `SearchResultResult`).

### Method

Three deletions (one field line, two full classes) — no renaming, no
replacement types.

### Details

- Do not touch `GetChunkResponse` (`chunk: str`, `headings: list[str]`) —
  a different, still-used class despite the similar name to
  `GetChunkSummaryResponse`.
- Preserve the two-blank-line-between-classes convention already used in
  this file after each deletion.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Field removed | `grep -n "use_summary" scripts/mcp_servers/mdq/models.py` | 0 matches |
| Classes removed | `grep -n "class ChunkSummary\|class GetChunkSummaryResponse" scripts/mcp_servers/mdq/models.py` | 0 matches |
| `GetChunkResponse` intact | `grep -n "class GetChunkResponse" scripts/mcp_servers/mdq/models.py` | 1 match, unchanged |
| Extra-field behavior confirmed | `PYTHONPATH=scripts uv run python -c "from mcp_servers.mdq.mdq_models import GetChunkRequest; r = GetChunkRequest(chunk_id='x', use_summary=True); print(hasattr(r, 'use_summary'))"` | prints `False` (field silently ignored, no error) |
| Lint | `uv run ruff check scripts/mcp_servers/mdq/models.py` | 0 errors |
| Type check | `uv run mypy scripts/mcp_servers/mdq/models.py` | no new errors |
