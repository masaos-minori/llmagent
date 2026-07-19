# Implementation procedure: `config/browser_mcp_server.toml` (new file)

Source plan: `plans/20260719-101501_plan.md`, Implementation step 2 (Design/Affected areas).

No existing implementations doc under `implementations/` or `implementations/done/` matches
`browser_mcp_server.toml` — `grep`/`ls` across both directories found no hit at all for this
exact filename (unlike the generic `server.py`/`service.py`/`tools.py`/`models.py` names, this
filename is server-specific and not reused elsewhere in the repo's history). Not a genuine
overlap concern.

## Goal

Create `config/browser_mcp_server.toml` — the self-contained, per-server config file for
Browser MCP (per the canonical checklist,
`docs/04_mcp_06_15_new-mcp-server-addition-checklist.md:20-28`, verified: "create the per-server
TOML (self-contained — does not read `agent.toml`)") — with a fail-closed empty
`allowed_domains` default, matching every other server's empty-allowlist convention.

## Scope

**In scope**
- `allowed_domains = []` (fail-closed default; empty = deny all, per plan Design step 1 and
  Risks).
- `max_response_kb` (int; response-body size cap).
- `timeout_sec` (int; HTTP request timeout).
- `auth_token = ""` (Bearer token; empty = auth disabled, matching
  `git_mcp_server.toml`'s convention, verified).
- Inline comments explaining each key's semantics and fail-closed behavior, matching the
  comment-per-key style of `config/shell_mcp_server.toml` and `config/git_mcp_server.toml`
  (both verified directly).

**Out of scope**
- No `[mcp_servers.browser]` transport block — that lives in `config/agent.toml` (per every
  existing server's split: the per-server TOML holds only the server's own operational config,
  never transport/routing metadata; verified by inspecting `shell_mcp_server.toml`,
  `web_search_mcp_server.toml`, and `git_mcp_server.toml`, none of which contain a `[mcp_servers.*]`
  table).

## Assumptions

1. Verified directly (`cat config/git_mcp_server.toml`): the fail-closed-empty-list convention
   is stated explicitly in-file: `# allowed_repo_paths: ... Empty list = deny all (fail-closed).`
   Browser's `allowed_domains` comment should use the same "Empty list = deny all (fail-closed)"
   phrasing for consistency.
2. Verified directly (`cat config/shell_mcp_server.toml`): numeric limit keys (`max_timeout_sec`,
   `max_output_kb`, `max_memory_mb`) are documented inline with a one-line comment stating what
   the value bounds (e.g. `# max_output_kb: total stdout+stderr output cap (KB)`). Browser's
   `max_response_kb`/`timeout_sec` follow the same one-line style.
3. `auth_token = ""` (verified in `config/git_mcp_server.toml`: `# auth_token: Bearer token;
   empty string = auth disabled.`) is the standard key name and default across every server that
   has one; Browser reuses it verbatim (not a new field name).
4. This file must **not** contain a `[mcp_servers.browser]` section or any `agent.toml`-owned
   key — verified: none of the three sampled per-server TOMLs (`shell`, `web_search`, `git`)
   contain transport/routing keys; that separation is enforced by
   `docs/04_mcp_06_15_...md`'s checklist wording "per-server TOML (self-contained — does not
   read `agent.toml`)", confirmed to describe the *reverse* direction too (per-server TOML is
   not read *by* `agent.toml`, and does not itself declare transport).
5. Default numeric values are implementation judgment calls (not specified by the plan) —
   `max_response_kb = 256` and `timeout_sec = 15` are reasonable, conservative starting values
   consistent with `shell_mcp_server.toml`'s `max_output_kb = 4096`/`max_timeout_sec = 300` being
   generous for a trusted local sandbox vs. Browser's outbound, less-trusted target; confirm with
   a reviewer at implementation time if a different default is preferred — these are not
   security-critical (the allowlist is the primary control), only DoS/resource-usage knobs.

## Implementation

### Target file

`config/browser_mcp_server.toml` (new file).

### Procedure

1. Create the file with a header comment: `# browser-mcp server configuration` (matching
   `# shell-mcp server configuration` / `# git-mcp server configuration` header style).
2. Add:
   ```toml
   # browser-mcp server configuration

   # allowed_domains: hostnames permitted for browser_fetch (exact match against the URL's
   # hostname). Empty list = deny all (fail-closed). IP-literal, loopback, and link-local
   # targets are always rejected regardless of this list (defense in depth).
   allowed_domains = []

   # max_response_kb: extracted-text response size cap (KB); truncated (not rejected) beyond
   # this limit, with a truncated=true flag on the response.
   max_response_kb = 256

   # timeout_sec: HTTP request timeout in seconds for the outbound fetch.
   timeout_sec = 15

   # auth_token: Bearer token; empty string = auth disabled.
   auth_token = ""
   ```
3. Do not add any `[mcp_servers.browser]` table here (belongs in `config/agent.toml`; see the
   paired `agent.toml` doc).

### Method

New-file creation; plain TOML, no logic.

### Details

No code; this is a data file consumed by `BrowserConfig.load()`
(`scripts/mcp_servers/browser/models.py`, per the paired doc) via
`ConfigLoader().load("browser_mcp_server.toml")`.

## Validation plan

| Check | Command | Target |
|---|---|---|
| TOML syntax | `uv run python -c "import tomllib; tomllib.load(open('config/browser_mcp_server.toml','rb'))"` | parses without error |
| Config-load round-trip | `PYTHONPATH=scripts uv run python -c "from mcp_servers.browser.models import BrowserConfig; import shared.config_loader as cl; cl.ConfigLoader.restrict_to('browser_mcp_server.toml'); print(BrowserConfig.load())"` | prints a `BrowserConfig` with `allowed_domains=[]`, confirming fail-closed default loads correctly |
| Deploy copy-list | `grep -n "browser_mcp_server.toml" deploy/deploy.sh` | present (see paired `deploy.sh` doc) |
| MCP docs consistency | `uv run check-mcp-docs` | passes; no fail-open wording introduced for `allowed_domains` |
