# Deploy — Detailed Workflow

## Phase 1: Pre-deploy check

**Gate: syntax check passes; deploy.sh copy list is current**

```bash
python3 -m compileall -q scripts/
```

If any file reports `SyntaxError`: fix the error before proceeding (see `SKILL.md` Required behavior).

**Completed when**: `compileall` reports no `SyntaxError` and the copy-list diff below is empty.

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

**Completed when**: `bash deploy/deploy.sh` exits 0.
**Stop and report to the user when**: the re-run at step 4 fails with the same error as the
first attempt — a repeat failure means steps 1–3 did not address the actual cause. Per
`AGENTS.md` Loop Prevention > Attempt Limit, do not repeat this recovery loop a third time.

---

## Phase 3: Service restart

**Gate: port health check returns OK**

Restart **only** the services whose code or config changed. This phase runs in four
sub-steps: identify (3a) → restart (3b) → verify (3c) → recover on failure (3d).

### Step 3a: Identify affected services (decision criteria)

Restart `llama-agent` ONLY if changes are in:
- `agent/repl.py`, `agent/context.py`, `agent/config.py`, or any file under `agent/commands/`
- `config/agent.toml` with a new `mcp_servers` entry (requires full restart)
- `config/agent.toml` with an existing `[mcp_servers.*]` entry's `cmd`/`url`/`transport`/
  `startup_mode`/`env` value changed (e.g. package rename affecting launch paths) —
  `/reload` does not apply these fields; see the MCP configuration doc's Reload vs. restart section

Do NOT restart `llama-agent` if:
- Only MCP server files changed → restart the MCP server instead (Step 3b)
- Only hot-reloadable `agent.toml` fields changed → use `/reload` in the REPL instead

**Completed when**: every changed file/config key has been matched against the criteria
above and assigned to exactly one outcome — restart agent, restart one MCP server,
restart an LLM inference server, or `/reload` only.

### Step 3b: Restart

For service names and ports, see `rules/env.md`.

```bash
# MCP servers (startup_mode="subprocess"; safe to restart, tool calls will retry) —
# there is no dedicated restart command: kill the process by its port and
# ensure_ready() (agent/factory.py) restarts it automatically on the next tool call
# to that server (see docs/04_mcp_06_12_watchdog-configuration-monitoring.md).
lsof -ti :<PORT> | xargs -r kill

# LLM inference servers (embed-llm :8081 / agent-llm :8080; 10-30 seconds to load model) —
# deploy/setup_services.sh's own startup commands for these are not yet implemented
# (placeholder `echo` lines as of this writing); confirm the script actually starts the
# process before relying on it, then:
lsof -ti :<PORT> | xargs -r kill
bash deploy/setup_services.sh

# Agent (stops the current REPL session — apply the restart decision criteria above first).
# start_agent.sh runs the REPL in the foreground: stop the running process
# (Ctrl+C in its terminal, or `kill <pid>` if run detached), then:
bash deploy/start_agent.sh
```

**Completed when**: the restart command for every service identified in Step 3a has been run.

### Step 3c: Verify health

```bash
curl -s http://127.0.0.1:<PORT>/health

# For deploys that changed cmd paths (e.g. package rename):
# /mcp status must show every MCP server's PID updated to the post-restart value
```

**Completed when**: every restarted service's `/health` endpoint returns OK.
**If a service does not return OK within 30 seconds of restart**: proceed to Step 3d.

### Step 3d: Failure recovery (service fails to start)

If a service fails to start:

1. Check logs immediately:
   ```bash
   tail -50 /opt/llm/logs/<name>.log
   ```
2. Common causes: syntax error in a newly deployed file; missing dependency; port conflict
3. If a syntax error slipped through: fix the file, re-run `bash deploy/deploy.sh`, restart the service
4. If port conflict: `lsof -i :<PORT>` to identify the conflicting process

**Completed when**: the service's `/health` endpoint returns OK after recovery.
**Stop and report to the user when**: none of the three common causes above explain the
failure, or the same failure recurs after applying the matching fix. Per `AGENTS.md`
Loop Prevention > Attempt Limit, do not retry the same restart command a third time.

---

## Phase 4: Verify deployment

**Gate: service is running; no new errors in logs**

```bash
curl -s http://127.0.0.1:<PORT>/health   # see rules/env.md for the port of each restarted service

tail -20 /opt/llm/logs/<service>.log     # see rules/env.md for log locations
```

If the agent was restarted, verify basic operation: start the agent REPL per `rules/env.md`
(see `rules/toolchain.md`, section 'Environment setup'), then in the REPL run `/mcp` and
confirm all MCP servers show healthy.

---

## First-run only (new environment)

Run in this order:

```bash
bash deploy/deploy.sh
bash deploy/init_db.sh         # creates SQLite schema (IF NOT EXISTS — safe to re-run)
bash deploy/setup_services.sh  # starts services via subprocess management
```
