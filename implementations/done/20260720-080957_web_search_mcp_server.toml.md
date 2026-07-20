# Implementation Procedure: config/web_search_mcp_server.toml

Source plan: `plans/20260719-193357_plan.md` (Phase 1, Implementation steps item
"Add `search_timeout_sec = 10.0` to `config/web_search_mcp_server.toml`").

## Goal

Add a `search_timeout_sec` key to the web-search MCP server's TOML config so that
`WebSearchConfig` (in `web_search_models.py`) can load an explicit, configurable
MCP-level timeout for the DuckDuckGo provider call, instead of the timeout being
hardcoded in Python.

## Scope

**In scope:**
- Add one new top-level key, `search_timeout_sec`, with value `10.0` and an
  explanatory comment, to `config/web_search_mcp_server.toml`.

**Out of scope:**
- Any change to `WebSearchConfig.from_dict()` parsing/validation logic (covered by
  the separate `web_search_models.py` procedure document).
- Any change to `deploy/deploy.sh` — this file is already in the deploy copy list
  (confirmed at `deploy/deploy.sh:80`); no path/list change needed since the file
  itself is not new, only a key is being added.

## Assumptions

1. Current file content (verified by direct read) is exactly:
   ```toml
   # web-search-mcp server configuration

   # default_max_results: default result count when max_results is omitted in request
   default_max_results = 5

   # max_results_limit: server-side cap on result count
   max_results_limit = 20
   ```
   No `search_timeout_sec` key exists yet.
2. `10.0` (seconds) is the accepted default per the plan's Assumption 3 / UNK-03
   resolution: fail-fast validation (reject `<= 0` or `> 60.0`) happens in
   `WebSearchConfig.from_dict()`, not in this file; this file only supplies the
   raw value.
3. TOML key ordering/grouping in this file follows a simple flat `key = value`
   style with a one-line `#` comment above each key (see existing
   `default_max_results` / `max_results_limit` pairs) — the new key should match
   this convention exactly, not introduce a `[section]` table.

## Implementation

### Target file

`config/web_search_mcp_server.toml`

### Procedure

1. Append a new commented key-value pair at the end of the file (after
   `max_results_limit`), following the existing convention: one `#`-prefixed
   explanatory comment line, then `key = value`.
2. Leave `default_max_results` and `max_results_limit` untouched.
3. No section headers needed — this file has no `[section]` tables today.

### Method

Direct text addition to a 7-line TOML file; no code generation, no schema
migration. The corresponding Python-side consumer (`WebSearchConfig.from_dict()`
in `web_search_models.py`) must read this key via
`float(d.get("search_timeout_sec", 10.0))`-style coercion — this document
covers only the config file change itself.
**Corrected 2026-07-20, gap closed:** this originally deferred the Python-side parsing to
"that file's separate procedure document," but no such document existed at the time
(`implementations/20260720-080006_web_search_models.py.md` covers only `from_dict()` invariant
validation and query normalization, not `search_timeout_sec`). The gap is now closed:
`implementations/20260720-101313_web_search_models.py.md` adds the `search_timeout_sec` field +
validation to `WebSearchConfig`, plus the 4 exception classes `search_provider.py`/`formatters.py`
need. Implement `080006` and `101313` together against `web_search_models.py` (both touch
`from_dict()`) before `search_provider.py`/`formatters.py`.

### Details

Resulting file content (illustrative, not production code — plain TOML):

```toml
# web-search-mcp server configuration

# default_max_results: default result count when max_results is omitted in request
default_max_results = 5

# max_results_limit: server-side cap on result count
max_results_limit = 20

# search_timeout_sec: MCP-level timeout (seconds) wrapped around the DuckDuckGo provider call
search_timeout_sec = 10.0
```

No other file needs to change as a direct consequence of this edit; `ConfigLoader().load("web_search_mcp_server.toml")` (used by `WebSearchConfig.load()`) picks up the new key automatically via its generic dict-loading path — no loader code change needed.

## Validation plan

- `uv run pytest tests/test_web_search_models.py -v` — confirm `WebSearchConfig.load()` picks up the new key without error once the corresponding Python-side field/parsing exists (tracked in the `web_search_models.py` procedure document).
- Manual/test-level check: a test asserting `WebSearchConfig.load().search_timeout_sec == 10.0` after this change (part of the `web_search_models.py` test additions, not a new test file of its own).
- `uv run check-mcp-docs` — confirm no doc/config consistency regressions.
- Full standard validation sequence per `rules/toolchain.md` is run once at the end of Phase 3 for the whole plan, not per file.
