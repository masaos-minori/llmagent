# `config/agent.toml` launches all 8 renamed MCP servers via a `server.py` path that no longer exists

## Severity

Critical — every MCP server affected by the `ca6b7bfe` rename (8 of them) will fail to start on the
next deploy or restart. This is a currently-live regression on `master` (introduced by commit
`abcf0820`), not a hypothetical risk.

## Context

This issue supersedes the "not yet verified" / "unmitigated risk" sections of two prior planning-cycle
issue files:

- `issues/20260719-193357_risks.md` (web_search)
- `issues/20260719-205532_risks.md` (mdq)

Both of those issues flagged that commit `ca6b7bfe` ("refactor: rename MCP server files to eliminate
duplicate filenames") left old-named files (`models.py`, `server.py`, `service.py`, `tools.py`) behind
as orphaned duplicates alongside the new `<server>_*.py` files, across 8 subpackages: `browser`,
`cicd`, `git`, `github`, `mdq`, `rag_pipeline`, `shell`, `web_search`.

Commit `abcf0820` ("chore: clean up stale MCP server file references after rename"), which landed on
`origin/master` after those two issues were filed, **deleted** the old-named `models.py`/`server.py`/
`service.py`/`tools.py` in all 8 subpackages, keeping only the `<server>_*.py`-prefixed files. This
resolves the "dead duplicate code" concern the two prior issues raised.

**However, `config/agent.toml` was not updated in that same commit.** Every one of the 8 affected
servers' `[mcp_servers.<name>]` `cmd` entry still launches the now-deleted bare `server.py`:

```
config/agent.toml:293  scripts/mcp_servers/shell/server.py        (deleted; live file: shell_server.py)
config/agent.toml:305  scripts/mcp_servers/git/server.py          (deleted; live file: git_server.py)
config/agent.toml:314  scripts/mcp_servers/web_search/server.py   (deleted; live file: web_search_server.py)
config/agent.toml:358  scripts/mcp_servers/github/server.py       (deleted; live file: github_server.py)
config/agent.toml:367  scripts/mcp_servers/cicd/server.py         (deleted; live file: cicd_server.py)
config/agent.toml:376  scripts/mcp_servers/rag_pipeline/server.py (deleted; live file: rag_pipeline_server.py)
config/agent.toml:388  scripts/mcp_servers/mdq/server.py          (deleted; live file: mdq_server.py)
config/agent.toml:397  scripts/mcp_servers/browser/server.py      (deleted; live file: browser_server.py)
```

(`file/delete_server.py`, `file/write_server.py`, `file/read_server.py` are a different, unaffected
naming convention — not part of the `ca6b7bfe` rename — and are unaffected.)

## Evidence

- `ls scripts/mcp_servers/<name>/*.py` for all 8 subpackages: no bare `server.py` exists in any of
  them; only `<name>_server.py` exists (confirmed for all 8 directly).
- `grep -n 'cmd\s*=' config/agent.toml`: all 8 entries above still reference the bare path.
- `deploy/deploy.sh:69-73`: `rsync -av --delete "${REPO_ROOT}/scripts/" "${DEPLOY_SCRIPTS}/"` mirrors
  the repo's `scripts/` tree onto `/opt/llm/scripts/` with `--delete`, so the next deploy will remove
  any previously-deployed bare `server.py` from `/opt/llm` as well — this is not just a repo-state
  issue, it will propagate to the running system on next deploy.

## Impact

Any `[mcp_servers.<name>]` entry using `startup_mode = "subprocess"` (verify per-server in
`config/agent.toml`) will fail to launch — `python /opt/llm/scripts/mcp_servers/<name>/server.py` is a
`FileNotFoundError` at process spawn. For `persistent`/`ondemand` modes backed by the same `cmd`, the
same failure applies whenever the process is (re)started. This affects all 8 servers simultaneously,
not one in isolation.

## Recommended action

1. For each of the 8 `cmd` entries listed above, change the path from `<name>/server.py` to
   `<name>/<name>_server.py`.
2. After editing, grep `config/agent.toml` for any other lingering bare-name reference
   (`models.py`, `service.py`, `tools.py`) in case other keys (not just `cmd`) reference them.
3. Re-run `uv run check-mcp-docs` and the MCP server startup healthcheck (see
   `docs/05_agent_10_01_operations-and-observability-startup-and-health.md`) for all 8 servers after
   the fix, before the next deploy.
4. Treat this as a prerequisite blocking step for any of the in-flight plans below that touch these
   servers, so implementers don't build new functionality on top of a server that cannot start.

## Affected in-flight plans

`plans/20260719-193357_plan.md`, `plans/20260719-195330_plan.md`, `plans/20260719-202346_plan.md`
(web_search); `plans/20260719-205532_plan.md`, `plans/20260719-210826_plan.md`,
`plans/20260719-211216_plan.md`, `plans/20260719-211521_plan.md`, `plans/20260719-212007_plan.md`,
`plans/20260719-212210_plan.md` (mdq) — each cross-references this issue where relevant; none of them
included this fix directly since it was discovered after they were written, and it is a distinct,
higher-severity concern than the "dead duplicate code" issue those plans deferred.

## Status

Open — not fixed. This is a planning-cycle finding; per current task instructions, no source or config
file has been modified. `config/agent.toml` is a production configuration file, not a plan/issue
document, so fixing it is out of scope for this documentation-only pass and requires explicit
implementation approval.
