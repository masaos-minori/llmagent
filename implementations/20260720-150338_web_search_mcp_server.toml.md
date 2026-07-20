# Implementation procedure: `config/web_search_mcp_server.toml` (add `browser_*` keys)

Source plan: `plans/20260720-135137_plan.md`, Implementation step 8 (config half); Affected areas
row for `config/web_search_mcp_server.toml`.

The one prior doc for this filename, `implementations/done/20260720-080957_web_search_mcp_server.toml.md`,
belongs to today's earlier requirement batch (`search_timeout_sec` key addition) — read in full, no
mention of `browser_*`. No overlap. New document.

## Goal

Add the 4 `browser_*` config keys (currently living in the standalone `config/browser_mcp_server.toml`,
16 lines, read in full) into `config/web_search_mcp_server.toml` (current: 10 lines, 3 keys), so
`WebSearchConfig.from_dict()` (per the `web_search_models.py` doc) can load them from the single
merged config file.

## Scope

**In scope**: add `browser_allowed_domains`, `browser_max_response_kb`, `browser_timeout_sec`,
`browser_auth_token` keys with explanatory comments to `config/web_search_mcp_server.toml`.
**Out of scope**: the 3 existing keys (`default_max_results`, `max_results_limit`,
`search_timeout_sec`) — untouched. Deletion of `config/browser_mcp_server.toml` — separate doc.

## Assumptions

1. Source `browser_mcp_server.toml`'s 4 keys and their comments (lines 3-16) are ported with the
   `browser_` prefix applied to each bare key name (`allowed_domains` → `browser_allowed_domains`,
   etc.), matching `WebSearchConfig.from_dict()`'s expected dict keys per the `web_search_models.py`
   doc's Procedure step 2.
2. Production deployments with a live, non-empty `allowed_domains`/`auth_token` in the current
   standalone `browser_mcp_server.toml` need a **manual value migration** at deploy time (copy the
   live values across before deleting the old file) — this is a deployment/ops concern already
   flagged by the plan's Affected-areas note for `config/browser_mcp_server.toml`'s deletion, not
   something this design-only doc can automate; call it out explicitly here too since both docs
   touch the same data.

## Implementation

### Target file

`config/web_search_mcp_server.toml`

### Procedure

1. Append, after the existing `search_timeout_sec` key (end of file, line 10):
   ```toml

   # browser_allowed_domains: hostnames permitted for browser_fetch (exact match against the URL's
   # hostname). Empty list = deny all (fail-closed). IP-literal, loopback, and link-local
   # targets are always rejected regardless of this list (defense in depth).
   browser_allowed_domains = []

   # browser_max_response_kb: extracted-text response size cap (KB) for browser_fetch; truncated
   # (not rejected) beyond this limit, with a truncated=true flag on the response.
   browser_max_response_kb = 256

   # browser_timeout_sec: HTTP request timeout in seconds for the outbound browser_fetch request.
   browser_timeout_sec = 15

   # browser_auth_token: Bearer token for browser_fetch's auth middleware; empty string = auth
   # disabled.
   browser_auth_token = ""
   ```
   (Comment text ported verbatim from `browser_mcp_server.toml`, only the key names get the
   `browser_` prefix and a `browser_fetch`-specific mention added for clarity in a shared file.)

### Method

Pure TOML content addition — a flat top-level key list, matching this file's existing style (no
nested tables needed, same as the existing 3 keys).

### Details

- If any live/production deployment currently has non-default values in
  `config/browser_mcp_server.toml` (i.e. an actual configured `allowed_domains` list or
  non-empty `auth_token`), those values must be copied into this file's new keys **before** the old
  file is deleted — this is a manual production-config migration step, not automatable from a
  design doc; flag it in the implementation PR description.

## Validation plan

| Check | Command | Target |
|---|---|---|
| TOML parses | `uv run python -c "import tomllib; tomllib.load(open('config/web_search_mcp_server.toml','rb'))"` | no parse error |
| Config load | `uv run pytest tests/test_web_search_models.py -v -k browser` (post that doc's `from_dict` extension) | `WebSearchConfig.load()` picks up all 4 new keys with correct defaults |
| Full suite | `uv run pytest -v` | no new failures |
