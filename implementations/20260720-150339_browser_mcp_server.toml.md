# Implementation procedure: `config/browser_mcp_server.toml` (deletion)

Source plan: `plans/20260720-135137_plan.md`, Implementation step 8 (config half); Affected areas
row for `config/browser_mcp_server.toml`.

The one prior doc for this filename, `implementations/done/20260719-111833_browser_mcp_server.toml.md`,
is the file's original **creation** doc (from `plans/done/20260719-101501_plan.md`, the original
Browser MCP registration work) — opposite direction, no overlap. New document.

## Goal

Delete the standalone `config/browser_mcp_server.toml` (16 lines, read in full), now that its 4
keys have been folded into `config/web_search_mcp_server.toml` with a `browser_` prefix (per that
doc).

## Scope

**In scope**: delete `config/browser_mcp_server.toml`.
**Out of scope**: `config/web_search_mcp_server.toml` — receiving side, separate doc.
`config/agent.toml`'s `[mcp_servers.browser]` block (which references `browser_mcp_server.toml` only
indirectly, via `BrowserConfig.load()`'s hardcoded filename in the now-deleted
`browser_models.py` — not via any `agent.toml` field) — separate doc.

## Assumptions

1. This file is loaded only via `scripts/mcp_servers/browser/browser_models.py`'s
   `BrowserConfig.load()` classmethod (`ConfigLoader().load("browser_mcp_server.toml")`), which is
   itself deleted as part of the `scripts/mcp_servers/browser/` directory-deletion doc — no other
   code path references this filename by string literal (confirmed: this filename does not appear in
   `config/agent.toml`, which references servers by `[mcp_servers.<key>]` section name, not by TOML
   filename).
2. Any live production deployment with non-default values in this file (a real `allowed_domains`
   list or non-empty `auth_token`) must have those values copied into
   `config/web_search_mcp_server.toml`'s new `browser_*` keys **before** this file is deleted — a
   manual, deploy-time step (same note as the companion `web_search_mcp_server.toml` doc; repeated
   here since deletion is irreversible without a git revert).

## Implementation

### Target file

`config/browser_mcp_server.toml`

### Procedure

1. Confirm (or perform, as a deploy-time checklist item, out of scope for this design-only
   repository change) that any non-default `allowed_domains`/`auth_token` values from this file have
   been copied into `config/web_search_mcp_server.toml`'s `browser_*` keys.
2. Delete the file (`git rm config/browser_mcp_server.toml`).
3. Sequence this deletion after `scripts/mcp_servers/browser/browser_models.py`'s removal (i.e.
   after the directory-deletion step) so no live code path attempts to load a now-missing file.

### Method

Single-file `git rm` — no content migration performed by this repository-side change itself beyond
what the companion `web_search_mcp_server.toml` doc already adds; this doc only covers the removal
of the now-redundant source file.

### Details

- `ConfigLoader().load(...)` (per its existing fail-fast contract, used throughout this codebase)
  raises if the named file is missing — after this deletion, any leftover code path still calling
  `ConfigLoader().load("browser_mcp_server.toml")` would fail loudly at startup, which is the
  correct fail-fast signal if step 1 (repo-wide grep for remaining references) in the
  directory-deletion doc missed an importer.

## Validation plan

| Check | Command | Target |
|---|---|---|
| No remaining references | `rg -l "browser_mcp_server\.toml" scripts/ config/ deploy/ docs/ tests/` | 0 matches after this + the `deploy.sh`/directory-deletion docs land |
| Full suite | `uv run pytest -v` | no failures from a missing config file |
| Manual/integration | server startup (`web-search-mcp` process) | starts cleanly, loads `browser_*` keys from `web_search_mcp_server.toml` only |
