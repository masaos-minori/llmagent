# Deploy — Detailed Workflow

## Phase 1: Pre-deploy check

**Gate: syntax check passes; deploy.sh copy list is current**

```bash
python3 -m compileall -q scripts/
```

If any file reports `SyntaxError`: fix the error before proceeding. Do not deploy with syntax errors.

Confirm `deploy/deploy.sh` copy list is up to date if any script or config file was added or removed:

```bash
diff <(find scripts/ -name '*.py' | sort) \
     <(grep -oP 'scripts/\S+\.py' deploy/deploy.sh | sort)
```

---

## Phase 2: Deploy

**Gate: `bash deploy/deploy.sh` exits 0**

Run from the repository root:

```bash
bash deploy/deploy.sh
```

### Failure recovery

If `deploy/deploy.sh` fails:

1. Check which file caused the error (the script prints the failing `cp` command)
2. Verify the file exists: `ls scripts/<module>.py`
3. Fix the missing file or update the copy list in `deploy/deploy.sh`
4. Re-run `bash deploy/deploy.sh`

---

## Phase 3: Service restart

**Gate: port health check returns OK**

Restart **only** the services whose code or config changed.

### Agent restart decision criteria

Restart `llama-agent` ONLY if changes are in:
- `agent/repl.py`, `agent/context.py`, `agent/config.py`, or any file under `agent/commands/`
- `config/agent.toml` with a new `mcp_servers` entry (requires full restart)

Do NOT restart `llama-agent` if:
- Only MCP server files changed → restart the MCP server instead
- Only hot-reloadable `agent.toml` fields changed → use `/reload` in the REPL instead

### Service restart commands

For service names and ports, see `rules/env.md`.

```bash
# Agent (stops REPL session — apply restart decision criteria above first)
# Restart via subprocess management

# MCP servers (safe to restart; tool calls will retry)
# Restart via subprocess management

# LLM inference servers (10–30 seconds to load model)
# Restart via subprocess management
```

Check status after restart:

```bash
curl -s http://127.0.0.1:<PORT>/health
```

### Failure recovery (service fails to start)

If a service fails to start:

1. Check logs immediately:
   ```bash
   tail -50 /opt/llm/logs/<name>.log
   ```
2. Common causes: syntax error in a newly deployed file; missing dependency; port conflict
3. If a syntax error slipped through: fix the file, re-run `bash deploy/deploy.sh`, restart the service
4. If port conflict: `lsof -i :<PORT>` to identify the conflicting process

---

## Phase 4: Verify deployment

**Gate: service is running; no new errors in logs**

```bash
curl -s http://127.0.0.1:<PORT>/health

tail -20 /opt/llm/logs/agent.log
tail -20 /opt/llm/logs/file-mcp.log
```

If the agent was restarted, verify basic operation:

```bash
source /opt/llm/venv/bin/activate
python3 /opt/llm/scripts/agent.py
# In the REPL: /mcp   (verify all MCP servers show healthy)
```

---

## First-run only (new environment)

Run in this order:

```bash
bash deploy/deploy.sh
bash deploy/init_db.sh         # creates SQLite schema (IF NOT EXISTS — safe to re-run)
bash deploy/setup_services.sh  # starts services via subprocess management
```
