# Implementation Procedure: tests/test_web_search_models.py

Source plan: `plans/20260719-192933_plan.md` ("Validate WebSearchConfig and align search_web input schema")

## Goal

Add test coverage for the new `WebSearchConfig.from_dict()` invariant checks and the
new `SearchRequest.query` normalization validator, so the behavior added to
`web_search_models.py` (see `implementations/20260720-080006_web_search_models.py.md`)
is locked in and regressions are caught by `uv run pytest`.

## Scope

**In scope**
- New test cases inside the existing `TestWebSearchConfig` class (or a new class)
  for the four invalid-config invariants.
- New test cases inside `TestSearchRequest` (or a new class) for query
  normalization: whitespace-only, leading/trailing whitespace, NUL, other
  control characters.

**Out of scope**
- Modifying `web_search_models.py` itself (separate doc).
- `tests/test_web_search_tool_schema.py` (separate new file/doc).

## Assumptions

1. New cases are additive — no existing test in this file is renamed or removed.
2. Reuse the existing import block (`WebSearchConfig`, `SearchRequest`,
   `DEFAULT_MAX_RESULTS`, `MAX_RESULTS_LIMIT`, `pytest`, `ValidationError`) and add
   `HARD_MAX_RESULTS_LIMIT` to the import from `mcp_servers.web_search.web_search_models`
   once it exists.
3. Invalid-config cases test `WebSearchConfig.from_dict()` directly (not
   `WebSearchConfig.load()`, which requires a real TOML file) — consistent with the
   existing `TestWebSearchConfig` pattern (`test_from_dict_defaults`,
   `test_from_dict_custom`, `test_from_dict_type_coercion` all call `from_dict`
   directly).
4. Normalization cases construct `SearchRequest(query=...)` directly and assert
   either the normalized `.query` value (for the trim case) or `pytest.raises(ValidationError)`
   (for the reject cases) — consistent with the existing `TestSearchRequest` pattern.

## Implementation

### Target file

`tests/test_web_search_models.py`

Current shape (verified by reading the live file):
- L1-20: module docstring, imports — `importlib`, `pytest`, and from
  `mcp_servers.web_search.web_search_models`: `DEFAULT_MAX_RESULTS`,
  `MAX_RESULTS_LIMIT`, `SearchRequest`, `SearchResponse`, `SearchResult`,
  `WebSearchConfig`, `WebSearchUpstreamError`; `from pydantic import ValidationError`.
- L23-45: `class TestWebSearchConfig` — `test_defaults`, `test_from_dict_defaults`,
  `test_from_dict_custom`, `test_from_dict_type_coercion`. None currently test
  invalid input; `from_dict` today has no validation to test.
- L55-83: `class TestSearchRequest` — `test_valid_request`, `test_custom_max_results`,
  `test_query_too_short_raises` (empty string, relies on existing `min_length=1`),
  `test_query_too_long_raises`, `test_max_results_below_min_raises`,
  `test_max_results_above_limit_raises`, `test_max_results_at_limit_ok`. No
  normalization cases exist yet (no trimming/control-char tests).
- L86-119: `class TestSearchRequestBoundsWiredToConfig` — monkeypatches
  `ConfigLoader.load` and reloads the module to verify `SearchRequest`'s bounds are
  wired to config, not hardcoded; not directly relevant to the new cases but shows
  the module-reload pattern available if invalid-config cases need it (they do not
  — `from_dict` is tested directly and does not require a reload).

### Procedure

1. Add new methods to `TestWebSearchConfig` (after `test_from_dict_type_coercion`,
   L45):
   - `test_from_dict_default_max_results_zero_raises` — `from_dict({"default_max_results": 0})`
     → `pytest.raises(ValueError)`.
   - `test_from_dict_max_results_limit_zero_raises` — `from_dict({"max_results_limit": 0})`
     → `pytest.raises(ValueError)`.
   - `test_from_dict_default_exceeds_limit_raises` — `from_dict({"default_max_results": 20, "max_results_limit": 10})`
     → `pytest.raises(ValueError)`.
   - `test_from_dict_limit_exceeds_hard_max_raises` — `from_dict({"max_results_limit": HARD_MAX_RESULTS_LIMIT + 1})`
     → `pytest.raises(ValueError)`. Requires importing `HARD_MAX_RESULTS_LIMIT`
     from `mcp_servers.web_search.web_search_models` (add to the existing import
     at L11-19 once it exists in the source module).
2. Add new methods to `TestSearchRequest` (after `test_max_results_at_limit_ok`,
   L83):
   - `test_query_whitespace_only_raises` — `SearchRequest(query="   ")` →
     `pytest.raises(ValidationError)`.
   - `test_query_trims_leading_trailing_whitespace` — `SearchRequest(query="  hello  ")`
     → assert `req.query == "hello"`.
   - `test_query_nul_raises` — `SearchRequest(query="hello\x00world")` →
     `pytest.raises(ValidationError)`.
   - `test_query_control_char_raises` — `SearchRequest(query="hello\nworld")`
     (or another `Cc`-category char) → `pytest.raises(ValidationError)`.
3. Do not modify `TestWebSearchUpstreamError`, `TestSearchRequestBoundsWiredToConfig`,
   `TestSearchResult`, or `TestSearchResponse`.

### Method

Pseudocode only (per `skills/python-design/SKILL.md` — no production code blocks):

```
class TestWebSearchConfig:
    ...  # existing methods unchanged

    def test_from_dict_default_max_results_zero_raises(self) -> None:
        with pytest.raises(ValueError):
            WebSearchConfig.from_dict({"default_max_results": 0})

    def test_from_dict_max_results_limit_zero_raises(self) -> None:
        with pytest.raises(ValueError):
            WebSearchConfig.from_dict({"max_results_limit": 0})

    def test_from_dict_default_exceeds_limit_raises(self) -> None:
        with pytest.raises(ValueError):
            WebSearchConfig.from_dict({"default_max_results": 20, "max_results_limit": 10})

    def test_from_dict_limit_exceeds_hard_max_raises(self) -> None:
        with pytest.raises(ValueError):
            WebSearchConfig.from_dict({"max_results_limit": HARD_MAX_RESULTS_LIMIT + 1})


class TestSearchRequest:
    ...  # existing methods unchanged

    def test_query_whitespace_only_raises(self) -> None:
        with pytest.raises(ValidationError):
            SearchRequest(query="   ")

    def test_query_trims_leading_trailing_whitespace(self) -> None:
        req = SearchRequest(query="  hello  ")
        assert req.query == "hello"

    def test_query_nul_raises(self) -> None:
        with pytest.raises(ValidationError):
            SearchRequest(query="hello\x00world")

    def test_query_control_char_raises(self) -> None:
        with pytest.raises(ValidationError):
            SearchRequest(query="hello\nworld")
```

### Details

- These tests depend on `web_search_models.py` already implementing
  `HARD_MAX_RESULTS_LIMIT` and the `query` normalization `field_validator`
  (see `implementations/20260720-080006_web_search_models.py.md`) — implement that
  file's changes before or together with these test additions, otherwise
  `test_from_dict_limit_exceeds_hard_max_raises` will fail on `ImportError`, the
  other three new `from_dict` cases will fail because no validation exists yet, and
  the normalization cases will fail because no validator exists yet.
- `pytest.raises(ValueError)` is correct for `from_dict` (a plain dataclass
  classmethod, not a Pydantic model) — do not use `ValidationError` there.
  `pytest.raises(ValidationError)` is correct for `SearchRequest` construction
  (Pydantic `BaseModel`), consistent with the existing `test_query_too_short_raises`
  pattern (L65-67).

## Validation plan

Reference commands only (do not run as part of this design-only task; see
`rules/toolchain.md` for the authoritative sequence):

```bash
uv run ruff format scripts/ tests/
uv run ruff check scripts/ tests/
uv run mypy scripts/
uv run pytest tests/test_web_search_models.py -v
uv run pytest -v
uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=main --fail-under=90
uv run pre-commit run --all-files
```

Expected outcome: all new cases pass once `web_search_models.py`'s validation and
normalization changes are in place; all pre-existing cases in this file continue to
pass unchanged.
