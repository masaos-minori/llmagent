# MCP Server Add — Detailed Workflow

## Prerequisites

See `SKILL.md` Prerequisites.

## Idempotency note

The wizard does NOT check for existing files and will overwrite them.
Before re-running: confirm no server already uses the same name or port.

```bash
ls scripts/mcp_servers/<name>/ config/<name>_mcp_server.toml init.d/<name> 2>/dev/null
```

---

## Option A: Use the agent REPL wizard (preferred)

From the running agent REPL:

```
/mcp install <name>
```

This calls the MCP installer and generates:
- `scripts/mcp_servers/<name>/server.py` — skeleton server module
- `scripts/mcp_servers/<name>/service.py` — service logic
- `scripts/mcp_servers/<name>/models.py` — Pydantic request/response models
- `config/<name>_mcp_server.toml` — server config
- `init.d/<name>` — optional startup script (subprocess management)

After the wizard completes, continue from Step 1 below.

### Failure recovery (partial wizard run)

If `/mcp install` fails partway through:

1. Check which files were created:
   ```bash
   ls scripts/mcp_servers/<name>/ config/<name>_mcp_server.toml init.d/<name> 2>/dev/null
   ```
2. Remove partially created files before retrying:
   ```bash
   rm -rf scripts/mcp_servers/<name>/ config/<name>_mcp_server.toml init.d/<name>
   ```
3. Retry the wizard or switch to Option B

---

## Option B: Manual creation

If the agent is not running, create the files manually following the models / service / server
split pattern in `mcp/file/` (`mcp/file/models.py`, `mcp/file/service.py`, `mcp/file/read_server.py`)
and the init script in `init.d/file-mcp`.

---

## Step 1: Verify generated files

Confirm each item below. On failure, apply the fix in the same row, then re-check that row
before moving to the next.

| Check | On failure |
|---|---|
| `server.py` inherits from `MCPServer` base class (`mcp/server.py`) | Add the missing base class import and inheritance |
| Uses models defined in `scripts/mcp_servers/<name>/models.py` (Pydantic `BaseModel` subclasses) | Move inline request/response types into `models.py` |
| Uses `ConfigLoader().load('<name>_mcp_server.toml')` (not `json.load()`) | Replace the `json.load()` call — see `SKILL.md` Required behavior |
| Uses `logger = logging.getLogger(__name__)` (standard library logging) | Add the standard logger declaration |
| Comments and log messages are in English | Translate non-English comments/log messages |
| `config/<name>_mcp_server.toml` is valid TOML | Run `python3 -c "import tomllib; tomllib.load(open('config/<name>_mcp_server.toml','rb'))"`; fix the reported syntax error |
| `init.d/<name>` includes the correct `--port` argument | Add or correct the `--port` argument to match Prerequisites' assigned port |
| Syntax check passes | Run `python3 -m compileall -q scripts/mcp_servers/<name>/`; fix the reported file |

**Completed when**: every row above passes.

---

## Step 2: Update deploy.sh

The new server's Python files under `scripts/mcp_servers/<name>/` need no `deploy.sh` change
(see `rules/env.md` Architecture). Only `config/*.toml` files are copied individually — add a
`cp` line for the new server's config:

```bash
# In deploy/deploy.sh, add alongside the other MCP server config cp lines:
cp config/<name>_mcp_server.toml /opt/llm/config/<name>_mcp_server.toml
```

---

## Step 3: Update config/agent.toml

Add a new entry to the `mcp_servers` section:

```toml
[mcp_servers.<name>]
transport = "http"
url = "http://127.0.0.1:<PORT>"
# Optional: explicit tool routing (falls back to prefix rules if omitted)
# tool_names = ["my_tool_a", "my_tool_b"]
```

Also add tool definitions to the `tool_definitions` array so the agent knows about the new tools.

---

## Step 4: Update tool routing (if needed)

`ToolRouteResolver` (`shared/route_resolver.py`) resolves: `tool_names` config-map → static prefix fallback.
If the new server's tools do not use a unique prefix, add them to `tool_names` in `config/agent.toml`.

---

## Step 5: Deploy

Delegate to the `deploy` skill (Phase 2 only — code change deploy):

```bash
bash deploy/deploy.sh
```

---

## Step 6: Start the service (first time)

`startup_mode="subprocess"` MCP servers are spawned by the agent itself — no separate start
command exists. Starting the agent (`bash deploy/start_agent.sh`, see `skills/deploy/workflow.md`
Phase 3 Step 3b) starts every configured MCP server, including the one just added.

For subsequent deploys after code changes to an already-running server: there is no
dedicated restart command — kill the process by its port and the agent's `ensure_ready()`
(`agent/factory.py`) restarts it automatically on the next tool call to that server (see
`docs/04_mcp_06_12_watchdog-configuration-monitoring.md`):

```bash
lsof -ti :<PORT> | xargs -r kill
```

**Completed when**: the process for the new server's port is running (first time), or has
been killed and the next `/mcp` check (Step 8) shows it respawned (subsequent deploys).

---

## Step 7: Add API key

Run this step only when the new server calls an external API that requires authentication;
otherwise skip directly to Step 8.

Check whether an existing MCP server config uses a `[secrets]` section
(`rg '\[secrets\]' config/*.toml`). If one does, follow that same pattern for consistency.
If none does, read the key from an environment variable via `ConfigLoader().load(...)`,
named `<NAME>_API_KEY` (uppercase server name).

**Completed when**: the new server can read its API key through `ConfigLoader().load(...)` —
confirmed by `rg` showing no `os.environ[...]` or `json.load()` access to the key.

---

## Step 8: Verify end-to-end

Three checks, in order — stop at the first that fails and fix it before continuing.

### Step 8a: Health endpoint

```bash
curl -s http://localhost:<PORT>/health
```
On failure: go to Step 6's restart command, then re-check.

### Step 8b: Agent-side discovery

```
/mcp
```
in the agent REPL. On failure (server missing or unhealthy in the listing): re-verify
Step 3's `[mcp_servers.<name>]` section with `rg`.

### Step 8c: Logs

```bash
tail -20 /opt/llm/logs/agent.log
```
On any new error mentioning `<name>`: diagnose from the error message before proceeding to
Step 9.

**Completed when**: 8a, 8b, and 8c all pass with no unresolved error.

---

## Step 9: Completion checklist

See `SKILL.md` Completion checklist.
