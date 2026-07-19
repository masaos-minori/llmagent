# Implementation: tests/test_mdq_search_modes.py (new — mode/limit validation tests)

Source plan: `plans/20260716-131500_plan.md`

## Goal

Add a new test module covering `search_docs`'s post-cleanup behavior:
default mode, explicit `mode="bm25"`, rejection of unsupported modes,
`max_results_limit` default/override/cap behavior, and confirmation that
the removed `max_search_results` alias is no longer accepted.

## Scope

**In:**
- Create `tests/test_mdq_search_modes.py` with test coverage for:
  1. Default mode behavior — `SearchDocsRequest(query=...)` with no `mode`
     specified defaults to `"bm25"` and search executes normally.
  2. Explicit `mode="bm25"` — accepted, behaves identically to default.
  3. Unsupported mode rejected — `SearchDocsRequest(query=..., mode="hybrid")`
     (or any non-`"bm25"` string) raises `pydantic.ValidationError` at
     construction time.
  4. `max_results_limit` default behavior — no override in the request,
     config's `max_results_limit` (default 100) is enforced.
  5. `max_results_limit` override behavior — a request-level
     `max_results_limit` smaller than the config cap is honored.
  6. `max_results_limit` cap behavior — a request-level
     `max_results_limit` larger than the config cap is capped at the
     config value (per `search.py`'s existing
     `min(request_results, config_results)` logic — this doc adds
     regression coverage for already-correct behavior, not new logic).
  7. `max_search_results` alias no longer accepted — confirm
     `SearchDocsRequest` has no `max_search_results` field at all (it was
     never a model field in the first place — it was only a `service.py`
     config key; if there truly is no model-level field to test, replace
     this with a service-level test: `not hasattr(service,
     "max_search_results")`, mirroring the pattern used in the companion
     `audit_log_path` regression test).

**Out:**
- `mode="grep"` acceptance — explicitly not implemented per the source
  plan's Assumption 4/Unknowns resolution; do not test for acceptance of a
  mode that is deliberately rejected.
- Any hybrid/vector-search behavior — fully removed, nothing to test.
- Direct testing of `_search_vector`/`_merge_hybrid`/`_RRF_K` — these no
  longer exist after the companion `search.py` doc lands.

## Assumptions

1. `SearchDocsRequest` is a pydantic `BaseModel` (confirmed by direct read
   of `models.py`) — invalid literal values raise
   `pydantic.ValidationError` automatically once `mode` is typed as
   `Literal["bm25"] | None` (companion `models.py` doc); this test module
   should import `pydantic` only for the `ValidationError` exception type
   in the rejection test, matching how other MDQ test files
   (`tests/test_mdq_error_taxonomy.py`) verify exception types via
   `pytest.raises`.
2. The `service` fixture pattern already used in
   `tests/test_mdq_service.py:36-47` (temp DB path, `tmp_path` in
   `_allowed_dirs`) is reusable here — this new file should follow the same
   fixture convention rather than inventing a new one, for consistency
   across `tests/test_mdq_*.py`.
3. `max_search_results` was never a `SearchDocsRequest` model field (it was
   only ever a `MdqService` config attribute, per direct read of both
   `models.py` and `service.py`) — so "no alias accepted anymore" is best
   tested at the service-construction level (`not hasattr(service,
   "max_search_results")`), not by passing `max_search_results` as a
   request kwarg (which was never valid pydantic model usage to begin
   with — passing an unrecognized kwarg to a pydantic model either raises
   or is silently ignored depending on model config; verify
   `SearchDocsRequest`'s `model_config` extra-fields setting before writing
   this specific assertion, since the correct test shape depends on it).

## Implementation

### Target file

`tests/test_mdq_search_modes.py` (new file)

### Procedure

1. Create `tests/test_mdq_search_modes.py` with a module docstring
   describing its purpose (search mode restriction and result-limit
   behavior regression coverage, replacing removed hybrid-search tests).
2. Add imports:
   ```python
   from __future__ import annotations

   from pathlib import Path
   from tempfile import mkstemp

   import pytest
   from pydantic import ValidationError

   from mcp_servers.mdq.mdq_models import SearchDocsRequest
   from mcp_servers.mdq.mdq_service import MdqService
   ```
3. Add a `service` fixture matching `tests/test_mdq_service.py`'s existing
   pattern (temp DB, `tmp_path` in `_allowed_dirs`) — reuse or duplicate as
   needed given pytest fixture scoping across files (duplicating a small
   fixture per-file is the existing convention in this test suite; do not
   attempt to share fixtures across files via a `conftest.py` change
   unless one already exists for this purpose — check `tests/conftest.py`
   first).
4. Add test functions, e.g.:
   ```python
   def test_default_mode_is_bm25() -> None:
       req = SearchDocsRequest(query="test")
       assert req.mode == "bm25"


   def test_explicit_bm25_mode_accepted() -> None:
       req = SearchDocsRequest(query="test", mode="bm25")
       assert req.mode == "bm25"


   def test_unsupported_mode_rejected() -> None:
       with pytest.raises(ValidationError):
           SearchDocsRequest(query="test", mode="hybrid")


   def test_max_search_results_field_does_not_exist(service: MdqService) -> None:
       """max_search_results was a dead config duplicate; must not remain."""
       assert not hasattr(service, "max_search_results")
   ```
5. Add the `max_results_limit` default/override/cap tests by driving
   `search_docs()` end-to-end against the `service` fixture with indexed
   test documents (mirror the setup pattern already used in
   `tests/test_mdq_service.py` for `search_docs`-exercising tests — index a
   handful of Markdown files via `index_paths`, then call `search_docs`
   with varying `max_results_limit` request values and assert on the
   returned result count/truncation message).

### Method

New pytest module using plain `assert`/`pytest.raises` — reuses this test
suite's existing fixture conventions (temp DB via `mkstemp`, `tmp_path`)
rather than introducing new test infrastructure.

### Details

- Keep this file's scope to `search_docs`/`SearchDocsRequest` behavior only
  — do not add coverage for other tools/methods.
- Match the docstring and typing style of sibling `tests/test_mdq_*.py`
  files (return-type `-> None` on every test function, module-level
  docstring).
- If `SearchDocsRequest`'s pydantic `model_config` is strict about extra
  fields (`extra="forbid"`), a direct
  `SearchDocsRequest(query="x", max_search_results=5)` call would itself
  raise `ValidationError` — in that case, add this as an explicit
  additional test (`test_max_search_results_kwarg_rejected`) rather than
  relying solely on the service-level `hasattr` check; determine the
  correct behavior by inspecting `SearchDocsRequest`'s base class /
  `model_config` before finalizing.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| New tests pass | `uv run pytest tests/test_mdq_search_modes.py -v` | all pass |
| Lint | `uv run ruff check tests/test_mdq_search_modes.py` | 0 errors |
| Type check | `uv run mypy tests/test_mdq_search_modes.py` | no new errors |
| Full MDQ suite | `uv run pytest tests/test_mdq_*.py -v` | all pass |
| Coverage | `uv run diff-cover coverage.xml --compare-branch=master` | new file contributes to ≥ 90% changed-line coverage for this plan |
