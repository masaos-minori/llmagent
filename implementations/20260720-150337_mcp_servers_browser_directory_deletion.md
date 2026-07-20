# Implementation procedure: `scripts/mcp_servers/browser/` (directory deletion)

Source plan: `plans/20260720-135137_plan.md`, Implementation step 9 (cleanup); Affected areas row
for the whole `scripts/mcp_servers/browser/` package.

No prior implementation doc targets a deletion of this directory — the prior
`implementations/done/20260719-111829_browser_models.py.md` through
`.../20260719-111832_browser_server.py.md` docs (plus `20260719-111833_browser_mcp_server.toml.md`,
`20260719-111838_test_browser_mcp_service.py.md`, `20260719-111839_04_mcp_04_06_browser.md.md`) are
all from the **creation** of the browser MCP server (`plans/done/20260719-101501_plan.md` —
confirmed by content, e.g. `implementations/done/20260719-111834_agent.toml.md`'s own text: "Register
Browser MCP in config/agent.toml"). Opposite direction from this deletion; no overlap. New document.

## Goal

Delete the standalone `scripts/mcp_servers/browser/` package in its entirety, now that its one tool
(`browser_fetch`) has been fully ported into `scripts/mcp_servers/web_search/` (per the 8 companion
docs for that package) and the standalone port-8016 process is retired.

## Scope

**In scope**: delete `scripts/mcp_servers/browser/__init__.py`, `browser_models.py`,
`browser_server.py`, `browser_service.py`, `browser_tools.py` (confirmed current contents: 3, 88,
150, 162, 39 lines respectively — read in full during this design cycle's research).
**Out of scope**: `scripts/mcp_servers/web_search/` — receiving side, covered by 8 separate docs.
`config/browser_mcp_server.toml` deletion and `config/agent.toml`'s `[mcp_servers.browser]` removal
— separate docs (config layer). `deploy/deploy.sh`'s `browser_mcp_server.toml` cp-line removal —
separate doc.

## Assumptions

1. Per the plan's Implementation step 1 ("Preparation": grep the full repo for
   `mcp_servers.browser` imports before deletion) and this design cycle's own verification, the only
   in-repo importers of `mcp_servers.browser.*` are: `scripts/mcp_servers/browser/__init__.py`
   itself (`from . import browser_server as server`), and
   `tests/test_runtime_tool_routing_integration.py`'s `TestBrowserToolsConfigDependentMigration`
   class (imports `from mcp_servers.browser.browser_tools import TOOL_LIST` at 3 call sites) —
   the latter is relocated to import from `mcp_servers.web_search.web_search_tools` instead, per the
   companion test-file doc. At implementation time, re-run
   `rg -l "mcp_servers\.browser|mcp_servers/browser"` across the full repo (not just the files this
   design cycle inspected) as a final safety net before deleting, per the plan's own Risk mitigation.
2. `scripts/` is deployed via a wholesale rsync with `--delete` (per plan's Design section and
   `implementations/done/20260719-111836_deploy.sh.md`'s own confirmation of this rsync mechanism)
   — no separate `deploy/deploy.sh` line references individual `.py` files under
   `mcp_servers/browser/`, so deleting the directory needs no corresponding deploy.sh edit beyond
   the config-file cp-line (handled by the separate `deploy.sh` doc).
3. `__pycache__/` under this directory is a build artifact, not tracked — deleted along with its
   parent directory as a side effect of directory removal, not a separate concern (and out of scope
   per `02_design.md`'s "do not touch files under `__pycache__/`" — no explicit action needed on it
   beyond letting the directory removal take it along).

## Implementation

### Target file

`scripts/mcp_servers/browser/` (whole directory: `__init__.py`, `browser_models.py`,
`browser_server.py`, `browser_service.py`, `browser_tools.py`)

### Procedure

1. Re-run `rg -l "mcp_servers\.browser|mcp_servers/browser"` across the full repository
   (`scripts/`, `tests/`, `config/`, `docs/`, `deploy/`) to confirm no importer beyond the ones
   already identified and handled by companion docs remains.
2. Confirm the companion docs for `web_search_models.py`, `search_provider.py`, `service.py`,
   `formatters.py`, `web_search_tools.py`, and `web_search_server.py` have landed (i.e. all
   `browser_fetch` behavior has a home in `web_search`) before deleting — this doc's deletion step
   should be the **last** step of the whole merge's implementation sequence (matches the plan's own
   Implementation step ordering: step 9 "Cleanup" comes after steps 2-8).
3. Confirm the companion `tests/test_runtime_tool_routing_integration.py` doc's import-path
   rewrite (away from `mcp_servers.browser.browser_tools`) has also landed, so no test imports the
   soon-to-be-deleted module.
4. Delete the 5 files (`git rm` each, or `git rm -r scripts/mcp_servers/browser/`).

### Method

Directory removal via `git rm -r`, not a manual filesystem delete, so the removal is tracked as a
diff (deleted-file lines) reviewable via `git diff --staged` before commit, consistent with
`rules/toolchain.md`'s "Diff review" step.

### Details

- Deletion must be sequenced **after** every other file in this merge that depends on
  `browser_fetch` continuing to work (the 8 `web_search`-package docs, the config docs, the
  tool_constants.py doc, and the test-file doc) — deleting first would break `browser_fetch` between
  implementation steps with no replacement path yet wired.
- No re-export shim is created at the old import path — the plan's Scope explicitly treats this as
  a full removal, not a deprecate-then-remove migration (single-repo, no external consumers of
  `mcp_servers.browser` per the plan's confirmed absence of docker-compose/.env files referencing
  port 8016).

## Validation plan

| Check | Command | Target |
|---|---|---|
| No remaining importers | `rg -l "mcp_servers\.browser\|mcp_servers/browser" scripts/ tests/ config/ docs/ deploy/` | 0 matches |
| Full suite | `uv run pytest -v` | no failures from missing `mcp_servers.browser` imports |
| Import layer | `PYTHONPATH=scripts uv run lint-imports` | 0 violations (one fewer module, cannot newly violate) |
| Syntax check | `uv run python -m compileall -q scripts/` | passes (no dangling references) |
| Manual/integration | confirm no process listening on 8016 post-deploy | `lsof -i :8016` empty |
