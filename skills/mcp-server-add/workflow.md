# MCP Server Add — Detailed Workflow

## Prerequisites

- For Option A: agent REPL must be running (`rc-service llama-agent status`)
- Next free port: `grep -r '\-\-port' init.d/ | grep -oP '\d{4,}' | sort -n | tail -1` → use next integer ≥ 8007

## Idempotency note

The wizard does NOT check for existing files and will overwrite them.
Before re-running: confirm no server already uses the same name or port.

```bash
ls scripts/<name>_mcp_server.py config/<name>_mcp_server.json init.d/<name> 2>/dev/null
```

---

## Option A: Use the agent REPL wizard (preferred)

From the running agent REPL:

```
/mcp install <name>
```

This calls `mcp_installer.py:install_mcp_server(name, port)` and generates:
- `scripts/<name>_mcp_server.py` — skeleton server module
- `config/<name>_mcp_server.json` — server config
- `init.d/<name>` — OpenRC init script

After the wizard completes, continue from Step 1 below.

### Failure recovery (partial wizard run)

If `/mcp install` fails partway through:

1. Check which files were created:
   ```bash
   ls scripts/<name>_mcp_server.py config/<name>_mcp_server.json init.d/<name> 2>/dev/null
   ```
2. Remove partially created files before retrying:
   ```bash
   rm -f scripts/<name>_mcp_server.py config/<name>_mcp_server.json init.d/<name>
   ```
3. Retry the wizard or switch to Option B

---

## Option B: Manual creation

If the agent is not running, create the three files manually following the patterns in
`fileop_mcp_server.py` (models / service / server split) and `init.d/file-mcp`.

---

## Step 1: Verify generated files

Confirm:

- `scripts/<name>_mcp_server.py` follows the module structure:
  - Uses `mcp_models.py` (`CallToolRequest` / `CallToolResponse`)
  - Uses `ConfigLoader().load('<name>_mcp_server.json')` (not `json.load()`)
  - Uses `logger = logging.getLogger(__name__)` (standard library logging)
  - Comments and log messages in English
- `config/<name>_mcp_server.json` is valid JSON: `python3 -c "import json; json.load(open('config/<name>_mcp_server.json'))"`
- `init.d/<name>` includes the correct `--port` argument

---

## Step 2: Update deploy.sh

```bash
# Add to the scripts copy block in deploy/deploy.sh:
cp "${REPO_ROOT}/scripts/<name>_mcp_server.py"  "${DEPLOY_SCRIPTS}/"

# Add to the config copy block if a config file was added:
cp "${REPO_ROOT}/config/<name>_mcp_server.json" "${DEPLOY_CONFIG}/"
```

---

## Step 3: Update agent_repl.py

Find `_MCP_SERVICE_MAP` and add the new entry:

```bash
rg "_MCP_SERVICE_MAP" scripts/agent_repl.py   # locate the dict definition
```

Add: `"http://localhost:<PORT>": "<name>"` to the dict.

This map is used by the watchdog and `/mcp` health checks.

---

## Step 4: Update tool routing (if needed)

In `tool_executor.py`, routing resolves: exact name → prefix → default (`file`).
If the new server's tools do not use a unique prefix, add an explicit mapping.

---

## Step 5: Deploy

Delegate to the `deploy` skill (Phase 2 only — code change deploy):

```bash
bash deploy/deploy.sh
```

---

## Step 6: Register and start the service (first time)

```bash
rc-update add <name> default
rc-service <name> start
rc-service <name> status
```

For subsequent deploys after code changes:

```bash
rc-service <name> restart
```

---

## Step 7: Add API key (if required)

```bash
# Create /etc/conf.d/<name> with:
MY_API_KEY="..."
```

Reference it from the init.d script via the `source` or `export` mechanism
matching the pattern in `init.d/github-mcp` or `init.d/web-search-mcp`.

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

- `scripts/<name>_mcp_server.py` syntax check passes
- `deploy/deploy.sh` updated with new file
- `_MCP_SERVICE_MAP` in `agent_repl.py` updated (verified with `rg`)
- service registered and running (`rc-service <name> status`)
- `/mcp` in agent REPL shows the new server as healthy
- no errors in `agent.log` during tool invocation
