# Deploy — Detailed Workflow

## Phase 1: Pre-deploy check

**Gate: the revision to deploy is clean, pushed, and validated; syntax check passes; deploy.sh config and binary lists are current**

Confirm what will be deployed. `deploy.sh` copies the working tree and records only the
commit (`DEPLOYED_REV`), so a dirty tree or an unpushed commit makes that record not
describe `/opt/llm/`:

```bash
git status --short          # must print nothing
git rev-parse HEAD @{u}     # the two values must match (HEAD is pushed)
```

If the tree is dirty or `HEAD` is not pushed, stop and ask the user; deploy a dirty tree
only on their explicit instruction, and report it as such. Also confirm the validation
sequence in `rules/toolchain.md` passed for this `HEAD` (in this session or in CI); if not,
run it before Phase 2.

```bash
python3 -m compileall -q scripts/
```

If any file reports `SyntaxError`: fix it before proceeding (see `SKILL.md` Required behavior).

**Completed when**: the working tree is clean and `HEAD` is pushed and validated (or the user explicitly accepted otherwise), `compileall` reports no `SyntaxError`, `check_db_separation.py` exits 0, and the config and binary list diffs below are empty or fully explained.
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
`scripts/**/*.py` files need no copy-list entry. Only `config/*.toml` and the binaries
(`BINARY_NAMES`) are listed explicitly. If a config file or an MCP server was added or removed, confirm those lists
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
builds every binary). The Event Bus and ingestion run from the deployed `scripts/` source and have no binary.

The build exports `UV_SYSTEM_CERTS=true` by default so `uv` can fetch nuitka on hosts whose certificates are only in the
system store; set `UV_SYSTEM_CERTS=false` to turn it off.

**Completed when**: `check` lists no stale or unknown binary.
**Stop and report to the user when**: a build fails; do not retry the same build a third time (`AGENTS.md`
Loop Prevention > Attempt Limit). The build host must have the Nuitka prerequisites described in
`deploy/build_binaries.sh`.

---

## Phase 2: Deploy

**Gate: the user approved, and `bash deploy/deploy.sh` exits 0**

### Preview the sync

`deploy.sh` has no dry-run mode and syncs `scripts/`, `tests/`, and `docs/` with
`rsync --delete`, which removes anything under those `/opt/llm/` directories that is not in
the repository. Preview the three syncs from the repository root; each line starting with
`deleting` is a removal:

```bash
rsync -avn --delete --exclude="__pycache__/" --exclude="*.pyc" --exclude="*.pyo" scripts/ /opt/llm/scripts/
rsync -avn --delete --exclude="__pycache__/" --exclude="*.pyc" --exclude="*.pyo" tests/ /opt/llm/tests/
rsync -avn --delete docs/ /opt/llm/docs/
```

### Approval gate

Run Phase 3 Step 3a's identification first (it only reads), so the approval covers the
restarts. Then tell the user and obtain explicit approval of: the commit to deploy
(`git rev-parse --short HEAD`), the paths the preview shows as changed or deleted, the
binaries Phase 1b rebuilt, and the services Step 3a selected for restart (restarting the
agent ends the current REPL session). MUST NOT run `deploy/deploy.sh`, kill a service, or
start the agent without it. If the user does not approve, stop and report
`Blocked: awaiting deployment approval`. An instruction that already approves this
specific deploy counts; an earlier deploy's approval does not carry over, and a rollback
deploy needs its own.

### Run the deploy

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

**Completed when**: the user approved and `bash deploy/deploy.sh` exits 0.
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
restart its process: stop its listening process (identify it as in Step 3b, using the Event Bus
port from `rules/env.md`), then run `bash deploy/setup_services.sh`, which checks the remote LLM
health and starts the Event Bus. A repeated run without stopping the old process starts a second
Event Bus.

The LLM inference servers (`agent-llm`, `embed-llm`) are remote services (`rules/env.md`);
`deploy/setup_services.sh` only checks their health. This skill never restarts them, so they
are not a Step 3a outcome.

**Completed when**: every changed file/config key has been matched against the criteria
above and assigned to exactly one outcome — restart agent, restart one MCP server,
restart the Event Bus, or `/reload` only.

### Step 3b: Restart

Service names and ports: see `rules/env.md`.

```bash
# MCP servers (startup_mode="subprocess"; safe to restart, tool calls will retry) —
# there is no dedicated restart command: kill the process by its port and
# ensure_ready() (agent/factory.py) restarts it automatically on the next tool call
# to that server (see docs/22_mcp/mcp_06_07_mcp-failure-diagnosis.md).
# Identify the LISTENING process and confirm its name is the expected service first.
# MUST NOT pick the process with `lsof -ti :<PORT>`: it also matches clients connected to
# the port, and the agent holds a connection to every MCP port.
ss -ltnpH 'sport = :<PORT>'     # the pid is the `pid=` value in the `users:` column
kill <pid>

# LLM inference servers (agent-llm / embed-llm) are remote services (`rules/env.md`):
# this skill does not restart them, and `bash deploy/setup_services.sh` only checks their health.

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
4. If port conflict: `ss -ltnp 'sport = :<PORT>'` to identify the conflicting process
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
