# Implementation procedure: `scripts/mcp_servers/web_search/web_search_models.py` (browser_fetch merge)

Source plan: `plans/20260720-135137_plan.md`, Implementation step 2 (Design section, Affected areas row
for `web_search_models.py`).

Prior docs targeting this filename (`implementations/done/20260720-080006_web_search_models.py.md`,
`implementations/done/20260720-101313_web_search_models.py.md`, plus
`implementations/done/20260720-080108_test_web_search_models.py.md`) all belong to today's earlier,
separate web-search-mcp requirement batch (config validation / `search_timeout_sec` /
`max_results` schema work) — read in full, confirmed no mention of `browser`, `BrowserConfig`, or
`BrowserFetchRequest`/`BrowserFetchResponse`. No overlap. This is a new document.

## Goal

Add the Browser-mcp domain model surface (exceptions, config, request/response schemas) into
`web_search_models.py`, ported verbatim in shape from `scripts/mcp_servers/browser/browser_models.py`
(88 lines, read in full), so `browser_fetch` can be served from the merged `web_search` package
without a second models module.

## Scope

**In scope**: additive changes only to `scripts/mcp_servers/web_search/web_search_models.py`
(current: 172 lines).
**Out of scope**: `SearchRequest`/`SearchResult`/`SearchResponse`/`WebSearchConfig`'s existing
fields and `WebSearchUpstreamError` hierarchy — untouched. Deletion of
`scripts/mcp_servers/browser/browser_models.py` is handled by the separate browser-directory-deletion
doc.

## Assumptions

1. Current `WebSearchConfig` (lines 57-106) is a `@dataclasses.dataclass` with a `from_dict`
   classmethod using `d.get(key, default)` / `int()`/`float()` casts and explicit `ValueError`
   invariant checks (`default_max_results <= max_results_limit`, hard ceilings, etc.). The ported
   `browser_*` fields must follow the same `from_dict` idiom, not `browser_models.py`'s bare
   `d.get(...) or default` idiom, for internal consistency — but preserve `browser_models.py`'s
   `or` guard specifically for `auth_token` (empty string default) since `int(None)`/`str(None)`
   pitfalls the source file's own docstring warns about apply identically here.
2. `browser_models.BrowserConfig.load()` calls `ConfigLoader().load("browser_mcp_server.toml")` —
   after the merge, config lives in `web_search_mcp_server.toml` instead; `BrowserConfig` as a
   separate loadable dataclass is retired in favor of `browser_*` fields living directly on
   `WebSearchConfig` (per Design section: "`BrowserConfig` constructed from those fields at server
   startup, as a thin sub-view, not a separately-loaded TOML file").
3. `BrowserFetchRequest`/`BrowserFetchResponse` (Pydantic `BaseModel`, lines 66-89 of the source)
   are ported with field-for-field parity: `url: str`, `max_response_kb: int | None` (ge=1, le=65536)
   on the request; `text: str`, `truncated: bool`, `url: str`, `status_code: int`,
   `elapsed_sec: float` on the response.

## Implementation

### Target file

`scripts/mcp_servers/web_search/web_search_models.py`

### Procedure

1. Add two new exception classes near the existing `WebSearchUpstreamError` family (own hierarchy,
   NOT a subclass of `WebSearchUpstreamError` — kept separate per plan Assumption 2 / Design section
   "two error models coexist"):
   - `class BrowserAuthorizationError(RuntimeError)` — domain-allowlist/IP-literal failures (403).
   - `class BrowserValidationError(ValueError)` — malformed input (422).
2. Extend `WebSearchConfig`:
   - Add fields: `browser_allowed_domains: list[str] = dataclasses.field(default_factory=list)`,
     `browser_max_response_kb: int = 256`, `browser_timeout_sec: int = 15`,
     `browser_auth_token: str = ""`.
   - Extend `from_dict()` to read `d.get("browser_allowed_domains") or []`,
     `int(d.get("browser_max_response_kb") or 256)`, `int(d.get("browser_timeout_sec") or 15)`,
     `d.get("browser_auth_token") or ""`. No new `ValueError` invariant checks are required (source
     `BrowserConfig` had none beyond type coercion) — keep parity, don't invent new validation.
3. Add a small `BrowserConfig`-equivalent **view** — either (a) keep a nested
   `@dataclasses.dataclass class BrowserConfig` with the same 4 fields as the source file, plus a
   `classmethod from_web_search_config(cls, cfg: WebSearchConfig) -> BrowserConfig` that projects
   the four `browser_*` fields out of `WebSearchConfig`, or (b) drop the separate `BrowserConfig`
   type entirely and have `search_provider.fetch_browser`/`service.fetch_browser` accept the four
   scalar values or the whole `WebSearchConfig` directly. Prefer (a): it keeps
   `search_provider.py`'s ported `_check_domain`/`fetch_browser` signature unchanged from the
   source file (still takes a `BrowserConfig`-shaped object), minimizing the diff in the provider
   layer. Construct the instance once at server startup in `web_search_server.py` (see that doc).
4. Add `BrowserFetchRequest(BaseModel)` and `BrowserFetchResponse(BaseModel)`, field-for-field
   identical to `browser_models.py` lines 66-89 (see Assumptions §3).

### Method

Pure additive dataclass/Pydantic model definitions; no changes to existing class bodies except the
`WebSearchConfig` dataclass field list and its `from_dict` body. No new imports needed beyond what
`web_search_models.py` already has (`dataclasses`, `pydantic.BaseModel`/`Field`) — `ipaddress`/
`httpx`/`bs4` stay in `search_provider.py` only, not in this models module (mirrors the existing
`search_provider.py`/`web_search_models.py` split: no HTTP or parsing logic in the models file).

### Details

- Pseudocode sketch of the new `BrowserConfig` view and its constructor:
  ```
  @dataclasses.dataclass
  class BrowserConfig:
      allowed_domains: list[str]
      max_response_kb: int
      timeout_sec: int
      auth_token: str

      @classmethod
      def from_web_search_config(cls, cfg: WebSearchConfig) -> BrowserConfig:
          return cls(cfg.browser_allowed_domains, cfg.browser_max_response_kb,
                      cfg.browser_timeout_sec, cfg.browser_auth_token)
  ```
- Do not add a `BrowserConfig.load()` classmethod (source file's own TOML-loading entry point) —
  there is no longer a standalone `browser_mcp_server.toml` to load from after the merge; the only
  construction path is `from_web_search_config()`.
- `SearchRequest`/`SearchResult`/`SearchResponse` classes and the module-level `_cfg` singleton
  stay byte-for-byte unchanged.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format/lint | `uv run ruff format scripts/mcp_servers/web_search/web_search_models.py && uv run ruff check scripts/mcp_servers/web_search/web_search_models.py` | 0 errors |
| Type check | `uv run mypy scripts/mcp_servers/web_search/web_search_models.py` | no new errors |
| Unit tests | `uv run pytest tests/test_web_search_models.py -v` (extend with new `BrowserConfig`/`from_dict` cases) | passes |
| Import layer | `PYTHONPATH=scripts uv run lint-imports` | 0 violations (no new inbound edges from this leaf-ish models module) |
