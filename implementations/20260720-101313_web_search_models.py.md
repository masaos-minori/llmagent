# Implementation procedure: `scripts/mcp_servers/web_search/web_search_models.py` (exception taxonomy + `search_timeout_sec`)

Source plan: `plans/done/20260719-193357_plan.md` (requirement 22 — provider execution semantics,
empty-result handling, timeout, error classification), Design §1 / Implementation Phase 1.

**Gap-fill document (2026-07-20).** This is a second implementation doc for `web_search_models.py`,
alongside the existing `implementations/20260720-080006_web_search_models.py.md` (requirement 21 —
config validation + query normalization). During the `02_design.md` cycle for requirement 22's plan,
that existing doc was incorrectly treated as already covering requirement 22's needs (filename-only
match, scope not verified). A later cross-check (background sequencing analysis, 2026-07-20) confirmed
`080006`'s Scope explicitly excludes exception classes and `search_timeout_sec` — this document closes
that gap. Verified against the current file (read in full, reproduced above in the discovery step):
neither the 4 new exception classes nor `search_timeout_sec` exist yet in `WebSearchConfig`.

## Goal

`web_search_models.py` gains four classified domain exceptions
(`WebSearchTimeoutError`/`WebSearchNetworkError`/`WebSearchProviderError`/`WebSearchParseError`, all
subclassing the existing `WebSearchUpstreamError`) and a validated `search_timeout_sec: float` field on
`WebSearchConfig`, so `search_provider.py` (see sibling doc `implementations/20260720-081016_search_provider.py.md`)
and `formatters.py` (`implementations/20260720-081048_formatters.py.md`) have the types/config value
they need to classify provider failures and enforce a timeout.

## Scope

**In scope**
- Four new exception classes, defined directly below the existing `WebSearchUpstreamError` (currently
  lines 22-24).
- `search_timeout_sec: float = 10.0` added to the `WebSearchConfig` dataclass (currently lines 36-41)
  and validated in `from_dict()` (currently lines 43-49).

**Out of scope**
- Requirement 21's validation (`HARD_MAX_RESULTS_LIMIT`, query normalization) — already covered by
  `implementations/20260720-080006_web_search_models.py.md`; this doc does not duplicate it, but an
  implementer applying both docs to the same file must merge both sets of changes (see Implementation
  Order note below).
- Any change to `search_provider.py`, `formatters.py`, or `web_search_server.py` themselves — covered
  by their own sibling docs.

## Assumptions

1. This doc's changes and `080006`'s changes are additive and non-overlapping within the file (new
   exception classes go below the existing `WebSearchUpstreamError`; `search_timeout_sec` is a new
   dataclass field alongside `080006`'s new `HARD_MAX_RESULTS_LIMIT`-based validation in the same
   `from_dict()` method) — an implementer doing both must combine them into one edited `from_dict()`
   body rather than picking one doc and discarding the other.
2. `search_timeout_sec`'s validation follows the same fail-fast `ValueError`-on-invalid style
   `from_dict()` already uses today (plain `int(...)`/`float(...)` coercion, no try/except swallowing) —
   consistent with `080006`'s validation additions.
3. Upper bound `60.0` and default `10.0` per the plan's own Assumption 3 / UNK-03 resolution (no
   stronger evidence found; these are the plan's recommended defaults, not independently re-derived
   here).

## Implementation

### Target file

`scripts/mcp_servers/web_search/web_search_models.py` (currently 100 lines, read in full at design
time — see file dump in the discovery notes above this document was generated from).

### Procedure

1. Immediately after the existing `WebSearchUpstreamError` class (currently lines 22-24), add:
   `WebSearchTimeoutError`, `WebSearchNetworkError`, `WebSearchProviderError`, `WebSearchParseError`,
   each subclassing `WebSearchUpstreamError` with a one-line docstring (see Method below).
2. Add `search_timeout_sec: float = 10.0` as a new field on the `WebSearchConfig` dataclass (currently
   lines 36-41, alongside `default_max_results`/`max_results_limit`).
3. In `from_dict()` (currently lines 43-49), add: coerce `d.get("search_timeout_sec", 10.0)` to `float`,
   then raise `ValueError` with an actionable message if the result is `<= 0` or `> 60.0`. If
   `implementations/20260720-080006_web_search_models.py.md`'s validation has already landed in this
   method, insert this check alongside its existing invariant checks rather than replacing them.
4. No change needed to `load()` (lines 51-53) — it already calls `from_dict()`, which is where all
   validation lives.

### Method

Pseudocode (signatures only, no full production bodies):

```python
class WebSearchUpstreamError(RuntimeError):
    """Raised when all search providers fail."""


class WebSearchTimeoutError(WebSearchUpstreamError):
    """Raised when the provider call exceeds search_timeout_sec."""


class WebSearchNetworkError(WebSearchUpstreamError):
    """Raised on a network-level provider failure (connection, DNS, etc.)."""


class WebSearchProviderError(WebSearchUpstreamError):
    """Raised on a non-network provider-side failure."""


class WebSearchParseError(WebSearchUpstreamError):
    """Raised when provider response data cannot be parsed into SearchResult."""


@dataclasses.dataclass
class WebSearchConfig:
    default_max_results: int = DEFAULT_MAX_RESULTS
    max_results_limit: int = MAX_RESULTS_LIMIT
    search_timeout_sec: float = 10.0

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> WebSearchConfig:
        # ... existing/080006's invariant checks ...
        timeout = float(d.get("search_timeout_sec", 10.0))
        if not (0 < timeout <= 60.0):
            raise ValueError(f"search_timeout_sec ({timeout}) must be in (0, 60.0]")
        return cls(..., search_timeout_sec=timeout)
```

### Details

- No new imports required — `dataclasses`, `Any`, and the existing exception base are already imported.
- No circular import risk: these are pure additions to an already-imported module.
- `search_provider.py`'s doc (`081016`) reads `cfg.search_timeout_sec` and catches the four new
  exception types by name — both must exist before that file's changes can type-check.
- **Implementation order note**: land this doc's changes together with (or immediately after)
  `implementations/20260720-080006_web_search_models.py.md`'s changes in the same commit/PR for this
  file, since both touch `from_dict()`. Do not implement one and skip the other.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format/lint | `uv run ruff format scripts/mcp_servers/web_search/web_search_models.py && uv run ruff check scripts/mcp_servers/web_search/web_search_models.py` | 0 errors |
| Type check | `uv run mypy scripts/mcp_servers/web_search/web_search_models.py` | 0 new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Unit tests | `uv run pytest tests/test_web_search_models.py -v` | all pass, including new invalid-`search_timeout_sec` cases (add alongside `080006`'s new test cases per `implementations/20260720-080108_test_web_search_models.py.md`) |
| Downstream | `uv run pytest tests/test_web_search_provider.py -v` (once `081016` lands) | provider tests import and catch the 4 new exception types successfully |
