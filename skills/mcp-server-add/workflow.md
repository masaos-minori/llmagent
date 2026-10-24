# MCP Server Add — Detailed Workflow

## Prerequisites

See `SKILL.md` Prerequisites.

## Toolchain

| Tool | Step | Role |
|---|---|---|
| `Bash` (`ls`) | Idempotency note, Step 1 | check for existing files before creating |
| `Write`/`Edit` | Steps 1-4 | create the server files, deploy.sh, agent.toml, and registration entries |
| `Bash` (`uv run python -m compileall -q`, `tomllib`) | Step 1 | syntax/TOML validity check |
| `Bash` (`uv run pytest`, `ruff`, `mypy`, `bandit`, `lint-imports`) | Step 5 | tests and validation (`rules/toolchain.md`) |
| `Bash` (`uv run python tools/generate_reference_table.py`) | Step 5 | refresh and check the generated MCP reference table |
| `Bash` (`bash deploy/deploy.sh`) | Step 6 | deploy (delegates to `deploy` skill, after user approval) |
| `Bash` (`curl`) | Step 9a | health endpoint check |
| `Bash` (`rg`) | Steps 2-4, Step 8 | confirm config sections and entries exist |
| `Bash` (`tail`) | Step 9d | log inspection |

Apply `rules/ai-execution.md` Tool Usage's idempotent-command rule throughout: MUST NOT
re-run the same `rg`/`curl`/`tail` check against an unchanged target; re-run only after the
specific fix it depends on.

## Idempotency note

Before creating anything, confirm no server already uses the same name or port. MUST NOT
overwrite an existing server directory or config file.

```bash
ls scripts/mcp_servers/<name>/ config/<name>_mcp_server.toml 2>/dev/null
```

---

## Step 1: Create and verify the server files

Create the files by hand, following the models / service / server split of the closest
existing server (for example `scripts/mcp_servers/web_search/`, `scripts/mcp_servers/mdq/`,
or `scripts/mcp_servers/file/`):

- `scripts/mcp_servers/<name>/<name>_server.py`, `<name>_service.py`, `<name>_models.py`,
  `<name>_tools.py`, and `__init__.py`
- `config/<name>_mcp_server.toml`
- an init script under `init.d/` only if the server needs separate process management;
  most servers need none, because the agent starts them

Confirm each item below. On failure, apply the fix in the same row, then re-check only that
row before moving to the next. Per `AGENTS.md` Loop Prevention > Attempt Limit, at most 3
fix-and-recheck attempts per row; if a row still fails after 3 attempts, stop and report
`Blocked: {row} still failing after 3 attempts — {last error}`.

| Check | On failure |
|---|---|
| `<name>_server.py` subclasses `MCPServer` (`scripts/mcp_servers/server.py`) and overrides `dispatch()` | Add the missing base class and override |
| The `MCPServer` subclass declares `own_config_file = "<name>_mcp_server.toml"` | Add the declaration (`run_http()` then restricts `ConfigLoader` to it) |
| `GET /v1/tools` returns `server_key` plus every tool with the schema-2.0 fields (`mcp_03_05`) | Add the missing fields; a tool absent or invalid there is not routable |
| `/health` is built with `make_health_response` (`scripts/mcp_servers/health_response.py`) | Use the shared builder |
| Uses models defined in `scripts/mcp_servers/<name>/<name>_models.py` (Pydantic `BaseModel` subclasses) | Move inline request/response types into `<name>_models.py` |
| Uses `ConfigLoader().load('<name>_mcp_server.toml')` (not `json.load()`) | Replace the `json.load()` call — see `SKILL.md` Required behavior |
| Uses `logger = logging.getLogger(__name__)` (standard library logging) | Add the standard logger declaration |
| Comments and log messages are in English | Translate non-English comments/log messages |
| `config/<name>_mcp_server.toml` is valid TOML and holds every setting the server needs (it does not refer to `agent.toml`) | Run `uv run python -c "import tomllib; tomllib.load(open('config/<name>_mcp_server.toml','rb'))"`; add the missing setting or fix the syntax error |
| `config/<name>_mcp_server.toml` carries `auth_token` as a `"${ENV:MCP_<NAME>_AUTH_TOKEN}"` reference (`mcp_06_14`) | Add it; the server refuses to start with an empty token |
| If an `init.d/` script exists, its `--port` matches the assigned port (`SKILL.md` Prerequisites) | Correct the `--port` argument |
| Syntax check passes | Run `uv run python -m compileall -q scripts/mcp_servers/<name>/`; fix the reported file |

Per `rules/ai-execution.md` Repository Tool Usage #8, `compileall -q`'s empty stdout is
evidence of success only together with exit code 0 — check both.

**Completed when**: every row above passes.

---

## Step 2: Register the config copy and the binary

Production runs every MCP server as a compiled binary (`skills/deploy/SKILL.md` Binary
layout), so a new server needs these registrations, not only a config copy. The server's
Python files under `scripts/mcp_servers/<name>/` need no `deploy.sh` copy entry (see
`rules/env.md` Architecture).

- Config copy — add a `cp` line in `deploy/deploy.sh` alongside the other MCP server config
  lines:

  ```bash
  cp config/<name>_mcp_server.toml /opt/llm/config/<name>_mcp_server.toml
  ```

- Binary build — add an entry to `ENTRIES` in `deploy/build_binaries.sh`, in the format of
  the existing ones (`<module path>:<binary name>:<server class>:<config file>`):

  ```
  "mcp_servers.<name>.<name>_server:mcp_<name>:<ServerClass>:<name>_mcp_server.toml"
  ```

- Binary list — add `mcp_<name>` to `BINARY_NAMES` in `deploy/deploy.sh`.
- Staleness table — add `"mcp_<name>": ("scripts/mcp_servers/<name>/", *_MCP_COMMON)` to
  `BINARY_SOURCES` in `tools/manage_binaries.py`, plus every other source directory the
  server imports (as `mcp_mdq` adds `scripts/db/`, and `mcp_rag_pipeline` adds
  `scripts/db/` and `scripts/rag/`). Without it a change to the server is never reported
  stale.

**Completed when**: `deploy/deploy.sh` contains the `cp` line for the file actually created,
and the two list checks in `skills/deploy/workflow.md` Phase 1 (config files and binary
names) print no difference.

---

## Step 3: Update config/agent.toml

Add the server section to `config/agent.toml`:

```toml
[mcp_servers.<name>]
transport    = "http"
url          = "http://127.0.0.1:<PORT>"
startup_mode = "subprocess"
auth_token   = "${ENV:MCP_<NAME>_AUTH_TOKEN}"
role         = "<label>"
cmd          = ["/opt/llm/bin/mcp_<name>"]
```

`role` is a display label shown in `/mcp status` (`mcp_06_02`); reuse an existing value
where one fits. `cmd` points at the binary registered in Step 2.

Then, for every new tool:

- add a `[[tool_definitions]]` entry (OpenAI function-calling format) so the LLM can call it
- add a `tool_safety_tiers` entry; every tool must declare its safety tier
- optionally list the tool in the section's `tool_names` — drift-validation metadata only,
  never required for routing (`mcp_03_05`)

**Completed when**: `config/agent.toml` has the `[mcp_servers.<name>]` section including
`auth_token` and `cmd`, a `[[tool_definitions]]` entry and a `tool_safety_tiers` entry for
each new tool.

---

## Step 4: Register the tools

Routing is built from the live `GET /v1/tools` responses (`RuntimeToolRegistry`), not from
`tool_names` or a prefix rule (`mcp_03_05`, ADR-003), so Step 1's `/v1/tools` row is the
routing registration. Also:

- add each tool name to the matching frozenset in `shared/tool_constants.py` — the static
  seed for drift detection, not a routing input
- update `routing.md` if the new server needs documentation the Documentation guide does
  not yet route to (per the checklist in `mcp_06_12`)
- update any `docs/22_mcp/` document the checklist requires, without stating the assigned
  port (`skills/DESIGN.md` Docs content policy — remove)

**Completed when**: every new tool name appears in `shared/tool_constants.py` (confirmed
with `rg`), and the docs the checklist requires are updated or recorded as not required.

---

## Step 5: Tests and validation (before any deployment)

- Add tests for the new server under `tests/mcp_servers/<name>/`, following an existing
  server's tests and `tests/mcp_servers/conftest.py` (tests MUST NOT touch production
  state; the suite's isolation guard is in `tests/conftest.py`).
- Run `uv run pytest tests/mcp_servers/<name>/ -q` and confirm at least one test was
  collected.
- Run the validation sequence in `rules/toolchain.md` on the new files (pass `scripts/` and
  `tests/` paths explicitly).
- Run the `routing.md` Tools → "When to run which tool" checkers the change triggers:
  `uv run python tools/generate_reference_table.py --type mcp` to refresh the MCP table,
  then `uv run python tools/generate_reference_table.py --check`;
  `uv run python tools/check_module_size.py` for the new modules; and, when docs were edited,
  the docs checkers including `uv run python tools/check_docs_consistency.py --domain mcp`.

**Completed when**: the new tests pass with a non-zero collected count, the validation
sequence passes, and every checker above exits 0.

---

## Step 6: Deploy

Delegate to the `deploy` skill's Phases 1, 1b, and 2. The new server has no binary yet, so
Phase 1's freshness report lists `mcp_<name>` as `unknown` and Phase 1b builds it. The
approval gate (`skills/deploy/workflow.md` Phase 2, "Approval gate") belongs to the
`deploy` skill: do not duplicate it here and do not bypass it. If the user does not
approve, that skill reports `Blocked: awaiting deployment approval`; stop there.

**Completed when**: the `deploy` skill's Phase 1b and Phase 2 Gates are met (no stale or
unknown binary; the user approved and `bash deploy/deploy.sh` exits 0) — not a separate
check.

---

## Step 7: Start the service (first time)

`startup_mode = "subprocess"` MCP servers are spawned by the agent itself — no separate start
command exists. Starting the agent (`bash deploy/start_agent.sh`) starts every configured
MCP server, including the one just added. A running agent MUST be restarted, not reloaded:
`/reload` does not apply changes to `[mcp_servers.*]` (`mcp_06_14`); a new `mcp_servers`
entry needs a full restart (`skills/deploy/workflow.md` Phase 3 Step 3a). This is
`deploy` Phase 3, and the restart was covered by the approval given before Phase 2.

For subsequent deploys after code changes to an already-running server, use the restart
command in `skills/deploy/workflow.md` Phase 3 Step 3b.

**Completed when**: the process for the new server's port is running (first time), or has
been killed and the next `/mcp status` check (Step 9) shows it respawned (subsequent deploys).

---

## Step 8: Authentication token and API keys

Every HTTP MCP server needs a non-empty token (`mcp_06_14`). Set `MCP_<NAME>_AUTH_TOKEN` in
the agent's environment: the agent's `[mcp_servers.<name>].auth_token` and the server's own
`auth_token` resolve this same variable. A server refuses to start when it is empty or
unset, so deploy the binaries and the configuration together. Follow the deployment
document's section on MCP authentication tokens for how the token is provisioned in
production. MUST NOT hardcode a token or key in any config file or in this repository.

If the new server also calls an external API that needs a key, provide it the same way: an
environment variable referenced from the server's own config file with `${ENV:<NAME>_API_KEY}`,
read through `ConfigLoader().load(...)`.

**Completed when**: the server starts with the token set, and `rg` shows no hardcoded
token or key and no `os.environ[...]` or `json.load()` access to it in the new server's
files. Per `rules/ai-execution.md` Repository Tool Usage #8, a zero-match `rg` result is
evidence only after confirming `rg` searched the new server's files (the path exists and
`rg` exited 0 or 1 for "no match", not 2 for an error).

---

## Step 9: Verify end-to-end

Four checks, in order — stop at the first that fails and fix it before continuing. Each
fix routes back only to the earlier step named below, not to Step 1 or a full restart;
after the fix, re-run only the failed Step 9a-9d.

### Step 9a: Health endpoint

```bash
curl -s http://localhost:<PORT>/health
```
On failure: go to Step 7's restart command, then re-check 9a only.

### Step 9b: Agent-side discovery

```
/mcp status
/mcp tools
```
in the agent REPL. `/mcp status` shows the new server `OK`; `/mcp tools` lists each new
tool in the runtime registry. On failure (server missing or unhealthy, or a tool missing):
re-verify Step 3's `[mcp_servers.<name>]` section and Step 1's `/v1/tools` row, then
re-check 9b only.

### Step 9c: Call a tool

Have the agent call one tool of the new server — prefer a read-only tier tool — and
confirm the result is correct. On failure: diagnose from the error, fix the earlier step
it points to, then re-check 9c only.

### Step 9d: Logs

```bash
tail -20 /opt/llm/logs/agent.log
```
On any new error mentioning `<name>`: diagnose from the error message before proceeding to
Step 10.

Per `AGENTS.md` Loop Prevention > Attempt Limit, at most 3 fix-and-recheck round-trips
across 9a-9d combined for the same server; if verification still fails after 3 rounds, stop
and report `Blocked: <name> failed end-to-end verification after 3 rounds —
{last failing check and error}`.

**Completed when, and only when**: 9a, 9b, 9c, and 9d all pass with no unresolved error, or
the cycle above ended in a `Blocked` report.

---

## Step 10: Completion checklist

See `SKILL.md` Completion checklist.
