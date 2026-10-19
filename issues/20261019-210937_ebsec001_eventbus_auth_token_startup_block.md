# Event Bus cannot start as shipped: `auth_token` has no environment indirection and `setup_services.sh` starts it with bare `python`

## Priority
High

## Summary
Make the shipped Event Bus configuration startable without writing a secret into a
deployed TOML file, and make `deploy/setup_services.sh` actually able to launch
`eventbus.app`. Wire `auth_token` to an environment reference like every other service
credential, load `.env` in `setup_services.sh` the way `deploy/start_agent.sh` does, and
start the Event Bus with the same `uv run` invocation the rest of the script uses.

## Background
- Found on 2026-10-19 while investigating why `deploy/setup_services.sh` never produced an
  Event Bus process. `/opt/llm/logs/eventbus.log` does not exist, so the Event Bus has never
  been started successfully by the deployment path.
- `config/eventbus.toml` ships `auth_token = ""` (line 13) and every per-role token as `""`
  (lines 24-28). It contains no `${ENV:...}` reference, unlike every MCP server config, which
  uses `auth_token = "${ENV:MCP_*_AUTH_TOKEN}"` (for example `config/agent.toml` `[mcp_servers.mdq]`).
- `scripts/eventbus/config.py::load_config` rejects the empty value: line 308-309 raise
  `ValueError("eventbus config 'auth_token' must not be empty.")`, and
  `EventBusConfig.__post_init__` (line 126-127) raises `ValueError("auth_token is required but not
  configured")`. `docs/24_eventbus/eventbus_07_configuration-and-operations.md` states this is
  intended behavior: "Startup fails unless `auth_token` is configured".
- `deploy/setup_services.sh` lines 133-135 start the Event Bus as
  `PYTHONPATH=/opt/llm/scripts python -m eventbus.app >> /opt/llm/logs/eventbus.log 2>&1 &`.
  Every other Python step in the same script uses `uv run "${UV_PROD_FLAGS[@]}"` (lines 31, 59, 88).
- `deploy/setup_services.sh` contains no `.env` handling at all (a search for `env` in the file
  returns no match), while `deploy/start_agent.sh` parses `/opt/llm/.env` (lines 82-97) and
  pre-checks required variables collected from `agent.toml` plus `*_mcp_server.toml`
  (lines 102-108). `eventbus.toml` is not in that list, so the agent startup gate does not see
  an Event Bus token.

## Problem
- Measured on 2026-10-19 against the deployed configuration:
  `load_config(get_config_path())` with `get_config_path() == /opt/llm/config/eventbus.toml`
  raises `ValueError: eventbus config 'auth_token' must not be empty.` The service cannot load
  its own shipped configuration.
- Even if a token were written into `/opt/llm/config/eventbus.toml`, line 134's bare `python`
  resolves to `/usr/bin/python`, which has no FastAPI or uvicorn
  (`ModuleNotFoundError: No module named 'fastapi'`). The production venv is
  `/opt/llm/venv/bin/python`. The background process would die before binding 127.0.0.1:8015.
- The only documented ways to supply the token are "its environment or configuration file"
  (`eventbus_07_configuration-and-operations.md`, Token Distribution). Because
  `setup_services.sh` loads no `.env`, the environment path is not reachable from the
  deployment script, so the practical path left to the operator is writing a secret into a
  deployed TOML file, which the repository's other services deliberately avoid.
- Current blast radius is limited: no production module publishes to or subscribes from the
  Event Bus. `scripts/agent/eventbus_client.py`, `scripts/agent/eventbus_subscriber.py`, and
  `scripts/agent/eventbus_topic_admin_client.py` are imported only by their own tests, and no
  file under `scripts/` references port 8015. `scripts/db/rotation.py` and `scripts/db/recovery.py`
  touch only `eventbus.sqlite`. So this issue blocks the service, not a currently used feature.

## Reason for Change
- Deployment failure: the documented service-startup script cannot start a service it claims to start.
- Configuration consistency: every other control-plane credential in the repository is injected
  through `${ENV:...}`; this one is a literal empty string in a deployed file.
- Security posture: the current workaround (edit `/opt/llm/config/eventbus.toml`) puts a secret in
  a file that `deploy.sh` re-rsyncs from the repository on every deploy, so it is silently lost.
- Usability: `scripts/agent/eventbus_*.py` clients exist and are tested, but no startable service
  exists to point them at.

## Implementation Intent
- Follow the existing convention rather than inventing one: `auth_token = "${ENV:EVENTBUS_AUTH_TOKEN}"`
  in `config/eventbus.toml`. `scripts/eventbus/config.py::_load_config_from_path` already builds
  config through `shared.config_loader.ConfigLoader` (line 16-19), so `${ENV:...}` expansion is
  available without new code in the Event Bus package.
- Give `deploy/setup_services.sh` the same `.env` load and required-variable pre-check that
  `deploy/start_agent.sh` implements, scoped to the variables this script actually needs, and
  keep the existing failure style (`[FATAL]` plus an `openssl rand -hex 32` example, no secret values).
- Start the Event Bus with the script's own production invocation
  (`uv run "${UV_PROD_FLAGS[@]}"` with `PYTHONPATH=/opt/llm/scripts`) so the process uses the
  production venv instead of the system interpreter.
- Keep the fail-closed behavior: an unset `EVENTBUS_AUTH_TOKEN` must still stop the Event Bus with
  the existing actionable error, not start it unauthenticated.

## Target Files or Areas
- `config/eventbus.toml` (`auth_token`, and the per-role token block if the owner wants the same
  indirection for `publisher_token` / `consumer_token` / `operator_token` / `monitoring_token` / `admin_token`)
- `deploy/setup_services.sh` (Event Bus start block, lines 132-137; `.env` load and pre-check to add)
- `scripts/eventbus/config.py` (expected: no change needed; confirm `${ENV:...}` expansion reaches
  `data["auth_token"]` before line 308's emptiness check)
- `tests/eventbus/test_eventbus_config.py` (regression that an environment reference resolves)
- Documentation: `docs/24_eventbus/eventbus_07_configuration-and-operations.md` (Token Distribution),
  `docs/90_deployment/deployment_01_deployment.md` (pre-flight checklist item about Event Bus tokens)

## Required Changes
- Replace the literal `auth_token = ""` with an environment reference and document the variable name.
- Make `setup_services.sh` load `/opt/llm/.env` (or `<repo>/.env`) without overriding already-exported
  variables, and fail fast with a clear message when the Event Bus token is missing.
- Replace the bare `python -m eventbus.app` with the script's production `uv run` invocation.
- Add a test that a configuration whose `auth_token` is `${ENV:EVENTBUS_AUTH_TOKEN}` loads
  successfully when the variable is set and fails with the existing non-empty-token error when it is not.
- Confirm no secret value is written into any file under `config/`.

## Constraints
- Do not commit or generate a real token value anywhere in the repository.
- Do not weaken `scripts/eventbus/config.py`'s fail-closed validation or the loopback-bind checks.
- Keep the import-layer contract: `eventbus` must not import from `agent`, `mcp_servers`, `rag`, or `db`.
- Do not change `deploy/start_agent.sh`'s MCP token gate semantics; adding an Event Bus variable to
  `eventbus.toml` must not make the agent refuse to start (verify: `start_agent.sh` scans only
  `agent.toml` and `*_mcp_server.toml`).
- Reuse `start_agent.sh`'s `.env` parsing approach rather than writing a second parser dialect.

## Acceptance Criteria
- A fresh `bash deploy/setup_services.sh` on a host where `EVENTBUS_AUTH_TOKEN` is defined in
  `/opt/llm/.env` reaches `--- Event Bus 起動 ---` and `curl -s http://127.0.0.1:8015/health`
  returns a health response (with `monitoring_token` or `auth_token` as the documented probe credential).
- With `EVENTBUS_AUTH_TOKEN` unset, the script stops with an actionable message that names the
  variable and shows how to generate a value; no Event Bus process is left listening.
- No file under `config/` contains a literal token value.
- The Event Bus process runs from the production venv (`uv run`), verified by the script's own command line.
- `tests/eventbus/` passes, and the new environment-reference test fails if `${ENV:...}` support is removed.

## Testing Expectations
- Unit test in `tests/eventbus/` for environment-reference resolution through
  `shared.config_loader.ConfigLoader`, and for the fail-closed path with the variable unset.
- A script-level check: run the Event Bus start block with the variable unset and assert a non-zero,
  actionable failure (no network dependency).
- `rules/toolchain.md` sequence; the documentation checkers listed in `routing.md` if any document changes.
- Do not read or write `/opt/llm` during tests.

## Documentation Impact
Expected, narrow. `docs/24_eventbus/eventbus_07_configuration-and-operations.md` must state that the
shipped configuration supplies `auth_token` through an environment reference and name the variable.
`docs/90_deployment/deployment_01_deployment.md`'s pre-flight checklist (Event Bus token item) must
state where the token is set. Remove any wording that implies the operator must edit the deployed
TOML file directly.

## Out of Scope
- Starting or configuring `embed-llm` (see `issues/20261019-210938_ebops002_setup_services_llm_gate_blocks_eventbus.md`).
- Wiring a publisher or consumer into the agent, and the `agent/eventbus_*.py` clients' unused
  `publish_url` / `subscribe_url` configuration keys.
- Changing Event Bus roles, token semantics, `consumer_authorization` mappings, or the envelope schema.
- Running the Event Bus as a systemd unit or any supervisor outside `deploy/`.

## Dependencies
- Related: `issues/20261019-210938_ebops002_setup_services_llm_gate_blocks_eventbus.md` (the LLM health
  gate aborts `setup_services.sh` before the Event Bus block is reached). Neither fix requires the other
  to be implemented first.
- Context: `deploy/start_agent.sh` lines 35-69 (`.env` parser) and 100-135 (token pre-check) are the
  pattern to reuse.
- No open issue under `issues/` overlaps; sibling check recorded 2026-10-19.

## Unresolved Questions
- Whether the per-role tokens should also move to `${ENV:...}`, or stay operator-set in the file
  because role mapping is deployment-specific (assumption: `auth_token` only, per the reported blocker).
- Whether `deploy/setup_services.sh` should require only the Event Bus token or the full MCP token set
  (the MCP tokens are already enforced by `start_agent.sh`).
- Whether the Event Bus is intended to be mandatory for a production deployment or optional until a
  publisher exists. Unknown: not stated in `docs/90_deployment/deployment_01_deployment.md`.

## AI Implementation Instruction
- Change the configuration value and the script; do not add new validation logic to
  `scripts/eventbus/config.py` — its fail-closed behavior is correct.
- Keep the diff to `config/eventbus.toml`, `deploy/setup_services.sh`, the Event Bus config test, and
  the two documents named above.
- Reuse `start_agent.sh`'s `.env` parsing semantics: existing exported variables win, unsafe lines are
  skipped with a warning, permissions are warned about, secrets are never printed.
- Stop and report if `${ENV:...}` expansion does not reach `auth_token` before line 308's check.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261019-210937
- **Related target files**: `config/eventbus.toml`, `deploy/setup_services.sh`, `scripts/eventbus/config.py`,
  `tests/eventbus/test_eventbus_config.py`, `docs/24_eventbus/eventbus_07_configuration-and-operations.md`,
  `docs/90_deployment/deployment_01_deployment.md`
