# Implementation Procedure: config/agent.toml — restore `subprocess` startup_mode for cicd/rag_pipeline

Source plan: `plans/20260711-200907_plan.md` — Phase 2 (Core Logic Implementation)

## Goal

Restore automatic startup and watchdog recovery for the RAG Pipeline and CICD MCP servers by changing `startup_mode` from `"none"` to `"subprocess"` for both `[mcp_servers.cicd]` and `[mcp_servers.rag_pipeline]` in `config/agent.toml`, and removing the now-stale comments that explained why `"none"` was chosen.

## Scope

**In:**
- `config/agent.toml:359-371` (`[mcp_servers.cicd]`): remove the comment block explaining `startup_mode = "none"`; change to `"subprocess"`.
- `config/agent.toml:373-383` (`[mcp_servers.rag_pipeline]`): remove the comment block explaining `startup_mode = "none"`; change to `"subprocess"`.

**Out:**
- No change to server internal logic or API contracts (any server code).
- No conditional startup based on token presence — a longer-term improvement, not this fix.
- No standardization of `startup_mode` across all MCP servers — separate initiative.
- `GITHUB_TOKEN`/`github_token` provisioning for the CICD server — handled in a separate, companion doc (`20260711-...cicd_mcp_server_github_token_config.md`) since it is a different target file (`config/cicd_mcp_server.toml`).

## Assumptions

1. `startup_timeout_sec` defaults to 30s (`scripts/shared/mcp_config.py:61`, confirmed resolved as non-blocking per the plan's UNK-02) — no custom override is needed for this change; if a server fails to become healthy within 30s, the agent logs an error and continues rather than hanging.
2. The lifecycle manager checks port availability before starting a subprocess-mode server (plan Assumption 3) — no new port-conflict handling is needed.
3. Both servers' dependencies are installed (`uv sync --dev` already run) — a deployment-environment precondition, not something this config change itself verifies.
4. Per the plan's UNK-01 (marked **Blocking: True** in the plan's own Unknowns & Gaps table): a valid GitHub PAT for CICD operations must be confirmed/obtained before this change is fully effective for the `cicd` server specifically — `rag_pipeline`'s `startup_mode` change has no such dependency and is unblocked. This procedure document does not itself resolve UNK-01 (obtaining/confirming the token is a credential-provisioning action outside the scope of writing implementation procedure documents) — flag this explicitly to whoever executes this procedure: **do not mark the `cicd` portion of this change as complete/verified until a valid `GITHUB_TOKEN`/`github_token` is confirmed available**, per the companion doc for `config/cicd_mcp_server.toml`.
5. `/opt/llm` and `/home/sugimoto/llmagent` (or this repo's equivalent working tree) are confirmed separate, non-git-linked file systems (plan UNK-03) — this change must be applied and deployed to both independently, via the standard `deploy/deploy.sh` workflow that copies `config/agent.toml` to `/opt/llm/config/`.

## Implementation

### Target file

`config/agent.toml`

### Procedure

1. Read the current file to confirm exact current line numbers/content for `[mcp_servers.cicd]` and `[mcp_servers.rag_pipeline]` sections (the plan's line numbers, 359-371 and 373-383, may have shifted since the plan was written — re-verify before editing).
2. In `[mcp_servers.cicd]`:
   - Remove the comment block (originally lines 362-365) explaining why `startup_mode = "none"` was chosen.
   - Change `startup_mode = "none"` to `startup_mode = "subprocess"`.
3. In `[mcp_servers.rag_pipeline]`:
   - Remove the comment block (originally lines 376-377) explaining why `startup_mode = "none"` was chosen.
   - Change `startup_mode = "none"` to `startup_mode = "subprocess"`.
4. Do not touch any other `[mcp_servers.*]` section or unrelated config keys in this file.

### Method

Two independent, single-key TOML value changes (`"none"` → `"subprocess"`) plus removal of their now-inapplicable explanatory comments. No schema/structure change to the TOML file.

### Details

- Apply this change identically to both `/opt/llm/config/agent.toml` (production) and this repository's `config/agent.toml` (development/source), per Assumption 5 — two independent edits, two independent deploys.
- Sequence relative to the companion `github_token` doc: the `rag_pipeline` half of this change has no blocking dependency and can be verified independently; the `cicd` half should be verified together with (or after) the `github_token` companion doc, since a `cicd` server with `startup_mode = "subprocess"` but no valid token will start but its tools will fail at call time (per the plan's Blast Radius note).

## Validation plan

Filtered from the plan's Validation Plan table to checks relevant to this file:

| Check | Tool | Target |
|---|---|---|
| Config validation | `uv run --directory /opt/llm python -c "from shared.config_loader import AgentConfig; c = AgentConfig.load(); print(c.mcp_servers['cicd'].startup_mode)"` | Returns `"subprocess"` |
| Config validation | Same command with `rag_pipeline` key | Returns `"subprocess"` |
| Startup test | `cd /opt/llm && uv run python scripts/mcp_servers/cicd/server.py &` | Server starts without crash |
| Startup test | `cd /opt/llm && uv run python scripts/mcp_servers/rag_pipeline/server.py &` | Server starts without crash |
| Health endpoints | `curl http://127.0.0.1:8010/health` + `curl http://127.0.0.1:8012/health` | HTTP 200 for both |
| `/mcp status` | Agent REPL command | Both servers show as started, no `startup_mode="none"`-related warnings |
| Watchdog recovery | Kill process, wait ~30s, check health | Server restarts automatically |
