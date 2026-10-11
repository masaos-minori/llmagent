## Goal

Replace the placeholder LLM startup stub in `deploy/setup_services.sh` with remote
health validation against the configured embed-llm / agent-llm URLs, and correct the
misleading local-subprocess comment, so deploy-time readiness of the remote LLM
services is actually gated rather than echoed (REQ-001, REQ-002, REQ-004).

## Scope

- Modify only `deploy/setup_services.sh`: fix the line 7 comment; replace the
  duplicate placeholder echo loops (lines 74-83) with a config-driven, retry-bounded
  reachability check of the remote `/health` endpoints.
- No other file is a modification target. `config/agent.toml`,
  `config/rag_pipeline_mcp_server.toml`, `deploy/deploy.sh`, and `deploy/start_agent.sh`
  are read-only references / verification dependencies.

## Assumptions

- The embed-llm (`embed_url`, :8081) and agent-llm (`llm_url`, :8080) services are
  remote (defined in `config/agent.toml` and `config/rag_pipeline_mcp_server.toml`)
  and expose a `/health` endpoint; this repository reaches and validates them, it does
  not spawn them.
- `curl` is available on the deploy host.
- The exact retry count / timeout / backoff is not yet fixed (REQ-002 open item); the
  procedure specifies fail-closed defaults and flags the values for confirmation.

## Design decisions

- **Read URLs from config, not literals.** `embed_url` / `llm_url` come from the
  existing TOML config so a URL/port change is a one-line config edit, not a script
  edit (mirrors the plan's risk mitigation).
- **Fail-closed.** If a URL is unset, unreachable, or not HTTP 200 after the retry
  budget, the script aborts with a non-zero exit and an error naming the configured
  URL; it never proceeds to start the agent against possibly-unready LLM services.
- **Reuse the existing `uv run python -c` config-read pattern.** The script already
  reads Python values via
  `PYTHONPATH=/opt/llm/scripts UV_SYSTEM_CERTS=true uv run python -c "..."` (schema
  version, lines 56-57); reading the TOML URLs the same way avoids adding a TOML
  parser dependency.
- **One retry loop covering both endpoints.** A single bounded poll loop keeps the
  gate atomic — the agent starts only when BOTH services respond.

## Alternatives considered

- **Hardcode the remote IPs/ports.** Rejected: the plan marks this a risk; config
  driven reads win.
- **Validate only liveness (TCP connect) instead of `/health` HTTP 200.** Rejected:
  `/health` 200 is the readiness signal the plan requires; a TCP connect alone reports
  "process up", not "ready".
- **Separate loops per service.** Rejected: a single combined loop gives one
  all-or-nothing gate and simpler failure output.

## Implementation
### Target file
`deploy/setup_services.sh`

### Procedure
1. **REQ-004** — Correct the line 7 comment. It currently states the LLM services are
   started as agent-managed local subprocesses; reword it to state they are remote
   services that this script validates (does not spawn). Keep the file's existing
   Japanese comment style.
2. **REQ-001** — Replace the duplicate placeholder echo loops at lines 74-83
   (`for svc in embed-llm agent-llm; do echo "  起動: ${svc}" done`, written twice)
   with a reachability check that curls the remote `/health` endpoints read from config.
3. **REQ-002** — Wrap the reachability check in a bounded retry loop that polls until
   both endpoints return HTTP 200 or the retry budget is exhausted, then proceed or
   abort accordingly.

### Method
- Read the base URLs once, before the LLM section, using the existing
  `uv run python -c` pattern against the config TOML, printing `embed_url` and
  `llm_url` from `config/agent.toml` (which carries both keys;
  `config/rag_pipeline_mcp_server.toml` is a cross-check). Strip any trailing path so
  the health URL is `<base>/health`.
- Build health URLs as `${embed_url}/health` and `${llm_url}/health`.
- Retry loop (bash): iterate a fixed number of attempts with a fixed sleep between
  them; use `curl -fsS -o /dev/null -w '%{http_code}' --max-time <sec>` and treat
  `200` as ready. After the last failed attempt, print a `[FATAL]` error naming the
  offending URL and `exit 1`.
- Keep the existing Event Bus section (lines 85-91) and its localhost eventbus health
  line as-is; the new LLM gate replaces only the lines 74-83 stubs. Reconcile the
  trailing localhost curl hints (lines 95-96, 107-108) with the new remote check — do
  not leave contradictory localhost assertions next to a remote-only gate.

### Details
- Evidence (adversarial verification against current source): lines 74-83 are two
  identical placeholder `echo` loops; line 7 comment claims local subprocess startup;
  `config/agent.toml` line 10 `embed_url = "http://192.168.11.238:8081"` and line 23
  `llm_url = "http://192.168.11.197:8080"`, mirrored in
  `config/rag_pipeline_mcp_server.toml` lines 7/10; no `embed_llm` / `agent_llm`
  module exists under `scripts/` (only `scripts/agent/services/mcp_health.py` matches,
  which is an MCP health service, not an LLM service).
- Suggested (unconfirmed) retry budget — **needs confirmation (REQ-002)**: e.g. 30
  attempts x 5 s ~= 150 s, since the existing doc text says model load takes "数十秒".
  Final count / timeout / backoff must be confirmed with the operator before merge.
- `shellcheck` must pass with no errors (REQ-001 test).
- Comment language: the file uses Japanese comments throughout; keep new comments
  Japanese to match the surrounding file. The English-only comment rule in
  `rules/coding.md` is enforced by ruff / mypy / ast-grep for Python, not this shell
  script.

## Compatibility considerations

- `set -euo pipefail` (line 12) stays in force; the retry loop must not trip
  `pipefail` on transient curl failures — guard each curl with explicit status capture
  (`|| true` / `|| echo`) so a single failed attempt does not abort the script early.
- Behavior change: the script now BLOCKS until remote LLM health passes (previously it
  returned immediately after echoing). This is the intended deploy-time readiness gate,
  but it changes script runtime on hosts where the LLM services are down.

## Security considerations

- Fail-closed: an unset / empty config URL aborts. Do not log full curl responses
  (may contain server detail); log only status code / reachability.
- The URLs contain internal IPs only, not secrets; do not print token-bearing config.
- No new credentials or network exposure beyond the already-configured remote health
  endpoints.

## Rollback considerations

- Revert `deploy/setup_services.sh` to the previous committed version (single file;
  `git checkout -- deploy/setup_services.sh` or revert the commit). No schema or
  config impact.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `deploy/setup_services.sh` | Lint | `shellcheck deploy/setup_services.sh` | No errors |
| `deploy/setup_services.sh` | Integration | Run against a live remote LLM (or a local mock serving `/health` 200) | Script blocks until both `/health` return 200, then proceeds; aborts with a named-URL error when an endpoint is down after the budget |
| `deploy/setup_services.sh` | Fail-closed | Point config at an unreachable URL | Script exits non-zero with an error naming the URL |

## Completion criteria

- Line 7 no longer claims local subprocess startup (REQ-004).
- Lines 74-83 placeholder loops are replaced by a config-driven, retry-bounded
  `/health` reachability check (REQ-001 / REQ-002).
- `shellcheck` passes with no errors.
- Script aborts (non-zero, named URL) when a remote endpoint is unreachable after the
  retry budget.

## Out of scope

- Starting / spawning the LLM services (they are remote; outside the repository,
  tracked as DEPLOY-001).
- Creating repo-local systemd units for the remote hosts (UNK-01; confirm topology
  with the operator).
- Changing the LLM services' own `/health` endpoints.
- Editing LLM configuration files.
- Any file other than `deploy/setup_services.sh`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-004
- **Source issue**: issues/done/20261007-154048_llmsvc01_provide-reproducible-startup-for-llm-services.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-162838_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261011-105208
- **Related target files**: deploy/setup_services.sh
