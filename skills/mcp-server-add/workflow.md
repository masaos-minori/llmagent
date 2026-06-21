# MCP Server Add — Detailed Workflow

## Prerequisites

- For Option A: agent REPL must be running (`ps aux | grep agent.py`)
- Next free port: `grep -r '\-\-port' init.d/ | grep -oP '\d{4,}' | sort -n | tail -1` → use next integer ≥ 8011

## Idempotency note

The wizard does NOT check for existing files and will overwrite them.
Before re-running: confirm no server already uses the same name or port.

```bash
ls scripts/mcp/<name>/ config/<name>_mcp_server.toml init.d/<name> 2>/dev/null
```

---

## Option A: Use the agent REPL wizard (preferred)

From the running agent REPL:

```
/mcp install <name>
```

This calls the MCP installer and generates:
- `scripts/mcp/<name>/server.py` — skeleton server module
- `scripts/mcp/<name>/service.py` — service logic
- `scripts/mcp/<name>/models.py` — Pydantic request/response models
- `config/<name>_mcp_server.toml` — server config
- `init.d/<name>` — optional startup script (subprocess management)

After the wizard completes, continue from Step 1 below.

### Failure recovery (partial wizard run)

If `/mcp install` fails partway through:

1. Check which files were created:
   ```bash
   ls scripts/mcp/<name>/ config/<name>_mcp_server.toml init.d/<name> 2>/dev/null
   ```
2. Remove partially created files before retrying:
   ```bash
   rm -rf scripts/mcp/<name>/ config/<name>_mcp_server.toml init.d/<name>
   ```
3. Retry the wizard or switch to Option B

---

## Option B: Manual creation

If the agent is not running, create the files manually following the models / service / server
split pattern in `mcp/file/` (`mcp/file/models.py`, `mcp/file/service.py`, `mcp/file/read_server.py`)
and the init script in `init.d/file-mcp`.

---

## Step 1: Verify generated files

Confirm:

- `scripts/mcp/<name>/server.py` follows the module structure:
  - Inherits from `MCPServer` base class (`mcp/server.py`)
  - Uses models defined in `scripts/mcp/<name>/models.py` (Pydantic `BaseModel` subclasses)
  - Uses `ConfigLoader().load('<name>_mcp_server.toml')` (not `json.load()`)
  - Uses `logger = logging.getLogger(__name__)` (standard library logging)
  - Comments and log messages in English
- `config/<name>_mcp_server.toml` is valid TOML: `python3 -c "import tomllib; tomllib.load(open('config/<name>_mcp_server.toml','rb'))"`
- `init.d/<name>` includes the correct `--port` argument
- Syntax check: `python3 -m compileall -q scripts/mcp/<name>/`

---

## Step 2: Update deploy.sh

`deploy/deploy.sh` uses explicit `cp` entries — new files are NOT automatically picked up.
Add `cp` lines for each new file:

```bash
# In deploy/deploy.sh, add:
cp scripts/mcp/<name>/server.py  /opt/llm/scripts/mcp/<name>/server.py
cp scripts/mcp/<name>/service.py /opt/llm/scripts/mcp/<name>/service.py
cp scripts/mcp/<name>/models.py  /opt/llm/scripts/mcp/<name>/models.py
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

```bash
# MCP servers are managed as subprocesses by the agent
```

For subsequent deploys after code changes:

```bash
# Restart via agent REPL or direct process management
```

---

## Step 7: Add API key (if required)

API keys can be passed via environment variables or config files.

---

## Step 8: Verify end-to-end

```bash
curl -s http://localhost:<PORT>/health

# From agent REPL:
/mcp
```

Check logs:

```bash
tail -20 /opt/llm/logs/agent.log
```

---

## Step 9: Completion checklist

- `scripts/mcp/<name>/server.py` syntax check passes (`python3 -m compileall -q scripts/mcp/<name>/`)
- `deploy/deploy.sh` updated with `cp` lines for all new files
- `config/agent.toml mcp_servers.<name>` entry added (verified with `rg`)
- service running and reachable (verify port health)
- `/mcp` in agent REPL shows the new server as healthy
- no errors in `agent.log` during tool invocation
