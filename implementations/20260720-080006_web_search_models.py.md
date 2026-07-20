# Implementation Procedure: web_search_models.py

Source plan: `plans/20260719-192933_plan.md` ("Validate WebSearchConfig and align search_web input schema")

## Goal

Make `WebSearchConfig` fail fast on invalid configuration values (instead of silently
constructing an invalid instance), and add a query-normalization policy to
`SearchRequest` so that whitespace-padded, empty-after-trim, or control-character
queries are rejected/normalized consistently before they reach the search provider,
audit log, or metrics.

## Scope

**In scope**
- `WebSearchConfig.from_dict()` validation of the four invariants below.
- New `HARD_MAX_RESULTS_LIMIT` module constant.
- A Pydantic `field_validator` on `SearchRequest.query` for normalization.

**Out of scope**
- `web_search_tools.py` schema changes (separate target file/doc).
- `search_provider.py` / DuckDuckGo integration logic.
- `web_search_server.py` dispatch mechanics.

## Assumptions

1. `HARD_MAX_RESULTS_LIMIT = 100` per the plan's Assumption 1 (falsifiable — change one
   constant if product/ops wants a different cap).
2. Control-character rejection uses `unicodedata.category(ch) == "Cc"` on the
   post-strip string (plan Assumption 3) — covers NUL and other control chars
   uniformly.
3. Normalization is "reject", not "silently mutate": trim leading/trailing whitespace
   is the only mutation; anything else invalid raises rather than being coerced
   (plan Assumption 4 / UNK-02 default).
4. Validation lives in `from_dict()` (not a separate `validate()` method) so that
   `load()` (which calls `from_dict()`) stays fail-fast at process/import time,
   consistent with `load()`'s existing docstring.

## Implementation

### Target file

`scripts/mcp_servers/web_search/web_search_models.py`

Current shape (verified by reading the live file):
- L1-16: module docstring, imports (`dataclasses`, `logging`, `Any`, `pydantic.BaseModel`/`Field`,
  `shared.config_loader.ConfigLoader`), `logger`.
- L23-24: `WebSearchUpstreamError(RuntimeError)`.
- L32-33: `DEFAULT_MAX_RESULTS: int = 5`, `MAX_RESULTS_LIMIT: int = 20`.
- L36-49: `@dataclasses.dataclass class WebSearchConfig` with `default_max_results`,
  `max_results_limit` fields; `from_dict()` (classmethod, L43-49) does unchecked
  `int(d.get(...))` conversion and returns `cls(...)` with no invariant checks;
  `load()` (classmethod, L51-54) calls `ConfigLoader().load("web_search_mcp_server.toml")`
  then `from_dict`.
- L65: module-level singleton `_cfg: WebSearchConfig = WebSearchConfig.load()`.
- L68-82: `class SearchRequest(BaseModel)` — `query: str = Field(..., min_length=1, max_length=500, ...)`,
  `max_results: int = Field(_cfg.default_max_results, ge=1, le=_cfg.max_results_limit, ...)`.
  No `field_validator` currently defined on this class.
- L85-99: `SearchResult`, `SearchResponse` (unaffected).

### Procedure

1. Add `import unicodedata` to the import block (L9-14) and `from pydantic import BaseModel, Field, field_validator`
   (extend the existing `pydantic` import at L13).
2. Add `HARD_MAX_RESULTS_LIMIT: int = 100` immediately after `MAX_RESULTS_LIMIT` (L33),
   with a one-line comment explaining it is a safety ceiling independent of any
   configured `max_results_limit`.
3. Rewrite `WebSearchConfig.from_dict()` (L43-49) to validate before constructing:
   - Parse `default_max_results` and `max_results_limit` as `int` (unchanged).
   - Raise `ValueError` if `default_max_results < 1`.
   - Raise `ValueError` if `max_results_limit < 1`.
   - Raise `ValueError` if `default_max_results > max_results_limit`.
   - Raise `ValueError` if `max_results_limit > HARD_MAX_RESULTS_LIMIT`.
   - Each message must be actionable, e.g. an f-string naming the field, its value,
     and the violated bound.
   - Only construct `cls(...)` after all four checks pass.
4. Add a `field_validator` on `SearchRequest.query`:
   - Mode `"after"` (runs after Pydantic's own `min_length`/`max_length` checks) or
     `"before"` — pick `"before"` only if trimming must happen before length
     constraints are evaluated (plan leaves this as an implementer's call); `"after"`
     is simpler if empty-after-trim is enforced as its own explicit check rather than
     relying on `min_length=1` (which validates the *raw*, untrimmed string).
   - Steps inside the validator: `stripped = value.strip()`; raise `ValueError` if
     `not stripped`; raise `ValueError` if any `unicodedata.category(ch) == "Cc"` for
     `ch` in `stripped`; return `stripped`.
5. Do not alter `SearchResult`, `SearchResponse`, or the `_cfg` singleton
   initialization pattern.

### Method

Pseudocode only (per `skills/python-design/SKILL.md` — no production code blocks):

```
HARD_MAX_RESULTS_LIMIT: int = 100  # safety ceiling, independent of config

class WebSearchConfig:
    @classmethod
    def from_dict(cls, d) -> WebSearchConfig:
        default_max_results = int(d.get("default_max_results", DEFAULT_MAX_RESULTS))
        max_results_limit = int(d.get("max_results_limit", MAX_RESULTS_LIMIT))
        if default_max_results < 1: raise ValueError(...)
        if max_results_limit < 1: raise ValueError(...)
        if default_max_results > max_results_limit: raise ValueError(...)
        if max_results_limit > HARD_MAX_RESULTS_LIMIT: raise ValueError(...)
        return cls(default_max_results=default_max_results, max_results_limit=max_results_limit)

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, ...)
    max_results: int = Field(_cfg.default_max_results, ge=1, le=_cfg.max_results_limit, ...)

    @field_validator("query")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped: raise ValueError("query must not be empty after trimming whitespace")
        if any(unicodedata.category(ch) == "Cc" for ch in stripped):
            raise ValueError("query must not contain control characters")
        return stripped
```

### Details

- `_cfg = WebSearchConfig.load()` (L65) runs at module-import time — an invalid
  `config/web_search_mcp_server.toml` will now raise `ValueError` during import,
  which is the intended fail-fast behavior per `load()`'s existing docstring. The
  current TOML values (`default_max_results=5`, `max_results_limit=20`) already
  satisfy all four invariants, so this is not expected to break startup today.
- Because `max_results`'s `Field(..., le=_cfg.max_results_limit)` bound is
  evaluated once at class-definition time (module import), the new `from_dict()`
  validation is the only enforcement point for the TOML values themselves;
  `SearchRequest`'s own `Field` bound simply inherits whatever `_cfg` already
  validated.
- No other module in the repo imports `MAX_RESULTS_LIMIT`/`DEFAULT_MAX_RESULTS`
  from this file today (per the plan's Phase 1 grep-confirmation step), so adding
  `HARD_MAX_RESULTS_LIMIT` is additive and does not require touching other files.

## Validation plan

Reference commands only (do not run as part of this design-only task; see
`rules/toolchain.md` for the authoritative sequence):

```bash
uv run ruff format scripts/
uv run ruff check scripts/
uv run mypy scripts/
PYTHONPATH=scripts uv run lint-imports
ast-grep --pattern 'except: $$$' --lang python scripts/
uv run bandit -r scripts/ -c pyproject.toml
uv run pytest tests/test_web_search_models.py -v
uv run pytest -v
uv run pytest tests/test_mdq_rag_boundary.py -v
uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=main --fail-under=90
uv run pre-commit run --all-files
```

Expected outcome: all invalid-config cases (`default_max_results=0`,
`max_results_limit=0`, `default_max_results > max_results_limit`, excessive
`max_results_limit`) raise `ValueError`; normalization cases (whitespace-only,
leading/trailing whitespace, NUL, other control chars) are rejected or trimmed as
specified; no regression in existing `tests/test_web_search_models.py` cases
(see `TestWebSearchConfig`, `TestSearchRequest`, `TestSearchRequestBoundsWiredToConfig`
classes in the current file).
