# Implementation: tests/test_mdq_get_chunk_behavior.py (new — normal `get_chunk` behavior + removed-field regression tests)

Source plan: `plans/20260716-131559_plan.md`

## Goal

Add a new test module covering `get_chunk()`'s post-cleanup behavior:
normal chunk retrieval, truncation at `max_chars_per_chunk`,
chunk-not-found error, and confirmation that `use_summary` is silently
ignored (not accepted, not raising a validation error) per the resolved
Unknown in the source plan.

## Scope

**In:**
- Create `tests/test_mdq_get_chunk_behavior.py` covering:
  1. Normal chunk retrieval — index a small Markdown file, call
     `get_chunk()` with its `chunk_id`, assert the heading and content are
     returned verbatim with no `[Summary — ...]` or cache-related text.
  2. Truncation at `max_chars_per_chunk` — index a large chunk (content
     exceeding `max_chars_per_chunk`), call `get_chunk()`, assert the
     result is truncated and contains the
     `"[Truncated — {len}/{max_chars} chars. Use a narrower chunk_id or
     reduce max_chars_per_chunk.]"` suffix (matching `service.py`'s exact
     wording post-simplification).
  3. Chunk-not-found — call `get_chunk()` with a nonexistent `chunk_id`,
     assert `MdqNotFoundError` is raised.
  4. `use_summary` no longer accepted — construct
     `GetChunkRequest(chunk_id=..., use_summary=True)` and assert the
     resulting object has no `use_summary` attribute (`not hasattr(req,
     "use_summary")`), confirming pydantic's default `extra="ignore"`
     behavior silently drops the field rather than raising — per the
     source plan's resolved Unknown (no explicit `model_config` sets
     `extra=` in `models.py`, so pydantic v2's default applies).

**Out:**
- Any summary-cache-related test — fully removed functionality, nothing to
  test.
- `with_neighbors` behavior — not part of this plan's scope (that field is
  untouched by this plan; if it is not actually implemented anywhere, that
  is a pre-existing, separate concern outside this plan).

## Assumptions

1. The `service` fixture pattern already used in
   `tests/test_mdq_service.py:36-47` (temp DB path via `mkstemp`,
   `tmp_path` in `_allowed_dirs`) is reusable here — this new file should
   follow the same fixture convention.
2. `GetChunkRequest` has no explicit `model_config` in `models.py` (per the
   companion `models.py` doc's Assumption 3) — pydantic v2 defaults to
   `extra="ignore"`, so `use_summary=True` passed as a kwarg is silently
   dropped, not rejected. The test in this doc's Scope item 4 directly
   verifies this specific behavior rather than assuming it.
3. To index a chunk for tests 1-2, this file needs to call `index_paths`
   (or the lower-level `_index_directory`/`_index_single_file` helpers)
   against a `tmp_path`-based Markdown file — mirror the setup pattern
   already used in `tests/test_mdq_service.py` for tests that exercise
   `get_chunk` today (check that file for an existing `md_file`/`md_dir`
   fixture pattern to reuse, per the fixtures already read:
   `tests/test_mdq_service.py:50-60` defines `md_file`/`md_dir` fixtures
   usable as a reference).

## Implementation

### Target file

`tests/test_mdq_get_chunk_behavior.py` (new file)

### Procedure

1. Create `tests/test_mdq_get_chunk_behavior.py` with a module docstring
   describing its purpose (regression coverage for `get_chunk()` after
   summary-cache removal).
2. Add imports:
   ```python
   from __future__ import annotations

   import asyncio
   from pathlib import Path
   from tempfile import mkstemp

   import pytest
   from mcp_servers.mdq.mdq_models import GetChunkRequest, MdqNotFoundError
   from mcp_servers.mdq.mdq_service import MdqService
   ```
3. Add a `service` fixture matching `tests/test_mdq_service.py`'s existing
   pattern (temp DB, `tmp_path` in `_allowed_dirs`).
4. Add a helper or fixture to index a known Markdown file and obtain its
   `chunk_id` (either by querying the DB directly after `index_paths`, or
   by reusing whatever helper `tests/test_mdq_service.py` already uses for
   this — check that file for a `get_chunk`-focused existing test to
   mirror its setup exactly, to keep both files' conventions consistent).
5. Add test functions, e.g.:
   ```python
   @pytest.mark.asyncio
   async def test_get_chunk_returns_raw_content(service: MdqService, ...) -> None:
       ...
       result = await service.get_chunk(GetChunkRequest(chunk_id=chunk_id))
       assert "[Summary" not in result
       assert "content here" in result  # or whatever the fixture's known content is


   @pytest.mark.asyncio
   async def test_get_chunk_truncates_large_content(service: MdqService, ...) -> None:
       ...
       result = await service.get_chunk(
           GetChunkRequest(chunk_id=chunk_id, max_chars_per_chunk=10)
       )
       assert "[Truncated —" in result


   @pytest.mark.asyncio
   async def test_get_chunk_raises_not_found(service: MdqService) -> None:
       with pytest.raises(MdqNotFoundError):
           await service.get_chunk(GetChunkRequest(chunk_id="nonexistent"))


   def test_use_summary_field_silently_ignored() -> None:
       req = GetChunkRequest(chunk_id="x", use_summary=True)
       assert not hasattr(req, "use_summary")
   ```
   (Adjust `@pytest.mark.asyncio` usage to match this test suite's existing
   async-test convention — check `tests/test_mdq_service.py` for whether it
   uses `pytest-asyncio` markers or `asyncio.run()` wrapping directly, and
   follow the same pattern for consistency.)

### Method

New pytest module using plain `assert`/`pytest.raises`, reusing this test
suite's existing fixture conventions (temp DB via `mkstemp`, `tmp_path`,
Markdown fixtures) rather than introducing new test infrastructure.

### Details

- Match the docstring and typing style of sibling `tests/test_mdq_*.py`
  files (return-type `-> None` on every test function).
- Do not test `with_neighbors` — out of scope for this plan.
- If this test suite has no existing async-test convention documented,
  check `tests/test_mdq_service.py`'s existing `get_chunk`-exercising
  tests (if any) for the exact async invocation pattern used, to avoid
  introducing a second, inconsistent convention.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| New tests pass | `uv run pytest tests/test_mdq_get_chunk_behavior.py -v` | all pass |
| Lint | `uv run ruff check tests/test_mdq_get_chunk_behavior.py` | 0 errors |
| Type check | `uv run mypy tests/test_mdq_get_chunk_behavior.py` | no new errors |
| Full MDQ suite | `uv run pytest tests/test_mdq_*.py -v` | all pass |
| Coverage | `uv run diff-cover coverage.xml --compare-branch=master` | new file contributes to ≥ 90% changed-line coverage for this plan |
