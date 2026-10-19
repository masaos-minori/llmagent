# Deploy — Detailed Workflow

## Phase 1: Pre-deploy check

**Gate: syntax check passes; deploy.sh config and binary lists are current**

```bash
python3 -m compileall -q scripts/
```

If any file reports `SyntaxError`: fix it before proceeding (see `SKILL.md` Required behavior).

**Completed when**: `compileall` reports no `SyntaxError`, `check_db_separation.py` exits 0, and the config and binary list diffs below are empty or fully explained.
**On a repeat `SyntaxError` after a fix**: per `AGENTS.md` Loop Prevention > Attempt Limit,
at most 3 fix-and-recheck attempts for the same file; if it still fails after 3 attempts,
stop and report `Blocked: {file} still has a syntax error after 3 attempts`.

Verify the SQLite 4DB separation (ADR-008); a non-zero exit blocks the deploy:

```bash
uv run python tools/check_db_separation.py
```

Report the freshness of the compiled binaries. Production runs the agent and the MCP servers as
binaries, so a `scripts/` change reaches them only after a rebuild (Phase 1b); the report lists, per
binary, `ok`, `stale` (an embedded source path changed since its build), `unknown` (no build info yet),
`mismatch`, or `invalid` (integrity problems, which always fail):

```bash
python3 tools/manage_binaries.py check --bin-dir /opt/llm/bin --rev auto --repo .
```

`deploy/deploy.sh` syncs `scripts/` as a whole with `rsync -av --delete`, so added or removed
`scripts/**/*.py` files need no copy-list entry. Only `config/*.toml` and the 11 binaries are
listed explicitly. If a config file or an MCP server was added or removed, confirm those lists
are up to date:

```bash
# config/*.toml files copied by deploy.sh (any diff line must be explained, e.g. a dev-only file)
diff <(ls config/*.toml | sort) \
     <(grep -oP '\$\{REPO_ROOT\}/\Kconfig/\S+\.toml' deploy/deploy.sh | sort -u)

# binary names: build_binaries.sh ENTRIES vs deploy.sh BINARY_NAMES (must be empty)
diff <(grep -oP '^\s+"\K[a-z_.]+:[a-z_]+(?=:)' deploy/build_binaries.sh | cut -d: -f2 | sort) \
     <(sed -n '/BINARY_NAMES=(/,/^)/p' deploy/deploy.sh | grep -oE '\b(agent|mcp_[a-z_]+)\b' | sort)
```

---

## Phase 1b: Build affected binaries

**Gate: `tools/manage_binaries.py check` lists no stale or unknown binary**

Rebuild only the binaries Phase 1 reported as stale, unknown, mismatch, or invalid. The tool prints
their names so they can be passed to `BUILD_ONLY`; the path table that decides staleness lives in
`tools/manage_binaries.py` (`BINARY_SOURCES`), not here:

```bash
STALE="$(python3 tools/manage_binaries.py check --bin-dir /opt/llm/bin --rev auto --repo . --list-stale)"
BUILD_ONLY="${STALE}" bash deploy/build_binaries.sh
```

`build_binaries.sh` builds into a staging directory, writes build info next to each binary, and swaps
the whole set into `/opt/llm/bin/` only after every requested binary passes the structural check, so a
failed build leaves the previous binaries in place. The previous set stays in `/opt/llm/bin.prev/`.
An empty `STALE` means nothing needs rebuilding (do not run the build with an empty `BUILD_ONLY`, which
builds all 11). The Event Bus and ingestion run from the deployed `scripts/` source and have no binary.

**Completed when**: `check` lists no stale or unknown binary.
**Stop and report to the user when**: a build fails; do not retry the same build a third time (`AGENTS.md`
Loop Prevention > Attempt Limit). The build host must have the Nuitka prerequisites described in
`deploy/build_binaries.sh`.

---

## Phase 2: Deploy

**Gate: `bash deploy/deploy.sh` exits 0**

Run from the repository root:

```bash
bash deploy/deploy.sh
```

`deploy.sh` re-runs the freshness check and writes the deployed revision to `/opt/llm/DEPLOYED_REV`. It
warns about stale or unknown binaries by default; set `DEPLOY_STRICT_BINARIES=1` to fail on them once
every binary has build info. Integrity problems (`mismatch`, `invalid`) always fail.

### Failure recovery

If `deploy/deploy.sh` fails:

1. Check which file caused the error (the script prints the failing `cp` command)
2. Verify the file exists: `ls scripts/<module>.py`
3. Fix the missing file or update the config/binary list in `deploy/deploy.sh`
4. Re-run `bash deploy/deploy.sh`

**Completed when**: `bash deploy/deploy.sh` exits 0.
**Stop and report to the user when**: the re-run at step 4 fails with the same error as the
first attempt. Per `AGENTS.md` Loop Prevention > Attempt Limit, MUST NOT repeat this recovery loop a third time.

---

## Phase 3: Service restart

**Gate: port health check returns OK**

Restart **only** the services whose code or config changed. Sub-steps: identify (3a) → restart (3b) → verify (3c) → recover on failure (3d).

### Step 3a: Identify affected services (decision criteria)

Restart `llama-agent` ONLY if:
- the `agent` binary was rebuilt in Phase 1b (it embeds `scripts/agent/`, `scripts/db/`, `scripts/shared/`, and `scripts/mcp_servers/`)
- `config/agent.toml` with a new `mcp_servers` entry (requires full restart)
- `config/agent.toml` with an existing `[mcp_servers.*]` entry's `cmd`/`url`/`transport`/
  `startup_mode`/`env` value changed (e.g. package rename affecting launch paths) —
  `/reload` does not apply these fields; see the MCP configuration doc's Reload vs. restart section

Do NOT restart `llama-agent` if:
- Only MCP server binaries were rebuilt → restart that MCP server instead (Step 3b)
- Only hot-reloadable `agent.toml` fields changed → use `/reload` in the REPL instead

The Event Bus runs from the deployed `scripts/` source, not a binary. If `scripts/eventbus/` changed,
restart its process: stop it (`lsof -ti :8015 | xargs -r kill`), then run `bash deploy/setup_services.sh`,
which checks the remote LLM health and starts the Event Bus. A repeated run without stopping the old
process starts a second Event Bus.

**Completed when**: every changed file/config key has been matched against the criteria
above and assigned to exactly one outcome — restart agent, restart one MCP server,
restart an LLM inference server, or `/reload` only.

### Step 3b: Restart

Service names and ports: see `rules/env.md`.

```bash
# MCP servers (startup_mode="subprocess"; safe to restart, tool calls will retry) —
# there is no dedicated restart command: kill the process by its port and
# ensure_ready() (agent/factory.py) restarts it automatically on the next tool call
# to that server (see docs/22_mcp/mcp_06_07_mcp-failure-diagnosis.md).
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
5. If a rebuilt binary is the cause: `bash deploy/build_binaries.sh --rollback` restores the previous binary set (no Nuitka needed); restart the affected service afterwards

**Completed when**: the service's `/health` endpoint returns OK after recovery.
**Stop and report to the user when**: none of the three common causes above explain the
failure, or the same failure recurs after applying the matching fix. Per
`AGENTS.md` Loop Prevention > Attempt Limit, MUST NOT retry the same restart command a third time.

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

Confirm the deployed revision matches what was intended: `/opt/llm/DEPLOYED_REV` records the commit
and, per binary, the checksum and the source commit it was built from.

**Completed when**: every restarted service's `/health` endpoint returns OK, the log
tail shows no new error timestamped after the restart, `/opt/llm/DEPLOYED_REV` records the
deployed commit, and (if the agent was restarted) `/mcp` shows every MCP server healthy.
**If any check fails**: return to Phase 3d's failure-recovery procedure for the
affected service rather than repeating ad hoc troubleshooting here.

---

## First-run only (new environment)

Run in this order:

```bash
bash deploy/deploy.sh
bash deploy/init_db.sh         # creates SQLite schema (IF NOT EXISTS — safe to re-run)
bash deploy/setup_services.sh  # starts services via subprocess management
```
