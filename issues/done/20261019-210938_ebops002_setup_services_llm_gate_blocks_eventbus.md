# `setup_services.sh` aborts on a remote LLM health check, so the Event Bus is never started and one down service blocks the whole script

## Priority
High

## Summary
Make `deploy/setup_services.sh` classify the remote `embed-llm` / `agent-llm` health result the way
the agent's own startup pipeline classifies it (warning versus fatal), so that an unreachable remote
embedding service does not prevent the Event Bus from starting, and make the script's failure message
state which services were left unstarted.

## Background
- Found on 2026-10-19 while trying to start the Event Bus (`127.0.0.1:8015`) on the production host.
- `deploy/setup_services.sh` lines 76-129 implement a health gate before the Event Bus block: it reads
  `embed_url` and `llm_url` from `config/agent.toml`, retries `GET /health` on both
  (`LLM_HEALTH_RETRIES="${LLM_HEALTH_RETRIES:-30}"`, line 82, five-second interval), and exits with
  `[FATAL] LLM services did not become ready within ${LLM_HEALTH_RETRIES} attempts` (line 123), or
  `[FATAL] LLM base URL(s) not configured in config/agent.toml (embed_url/llm_url)` (line 101).
- The Event Bus block is lines 132-137 and has no dependency on either remote service.
- Measured on 2026-10-19: `embed_url = "http://192.168.11.238:8081"` (line 10) is unreachable
  (`All connection attempts failed`) while `llm_url = "http://192.168.11.197:8080"` (line 23) returns
  healthy. `192.168.11.238` is this host's own `enp3s0` address, so the embedding service is expected
  on this machine; `/opt/llm/llama.cpp` exists, but the embedding server's command and model are not
  in this repository — `setup_services.sh` line 76 states these are remote services the repository only
  health-checks. The gate therefore waits 30 attempts (about 150 s) and then aborts.
- The same condition is treated as non-fatal by the agent: the production startup at 2026-10-19 20:00
  logged `WARNING [check_service_health] [non-fatal] embed-llm unreachable at
  http://192.168.11.238:8081/health` and still completed startup, tool discovery, and RAG consistency.
- `config/agent.toml` declares no Event Bus URL or token, and `deploy/start_agent.sh` does not start the
  Event Bus; `setup_services.sh` is the only path that starts it. `/opt/llm/logs/eventbus.log` does not
  exist, so that path has never completed.

## Problem
- One unavailable remote service makes the whole service-setup script fail, including the part of the
  deployment that does not depend on it. `set -euo pipefail` (line 12) means the Event Bus lines are
  never reached.
- The two deployment entry points disagree about the severity of the same condition:
  `setup_services.sh` treats it as fatal, `start_agent.sh` plus `scripts/agent/startup_validation.py`
  treat it as a warning. An operator who follows the documented order gets a hard stop, then finds that
  the agent starts anyway.
- The failure message does not say that the Event Bus was left unstarted, and the retry loop prints only
  `embed-llm=---, agent-llm=200` style progress lines, which does not distinguish "service down" from
  "wrong health path".
- Related observability gap: `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py::_check_health_deps`
  (lines 208-220) only records `embed_url` as "not configured" when the key is missing or not a string.
  A configured but unreachable `embed_url` passes the rag_pipeline `/health` check, so this gate is the
  only place in the deployment path that notices an embedding-service outage.

## Reason for Change
- Deployment failure: the documented service startup sequence cannot complete on the current host state.
- Consistency: one host condition has two different severities across two scripts in `deploy/`.
- operability: the abort hides which services were started and which were skipped, and burns 150 s before
  reporting it.
- Correctness of the health story: the component that should surface an embedding outage
  (`rag_pipeline` `/health`) does not, and the component that does notice stops the deployment instead.

## Implementation Intent
- Keep the health probe (it is the deployment path's only embedding-outage check) but classify it the way
  `StartupValidationPipeline` does: an unreachable remote LLM service is a warning that the operator can
  opt into as fatal. Concretely: report both statuses, continue to the Event Bus block, and make strict
  behavior an explicit, documented switch (for example `LLM_GATE_STRICT=1`), with the current abort kept as
  the strict-mode behavior.
- Report what was started and what was skipped in the script's final summary, so an operator can tell that
  the Event Bus is up while `embed-llm` is down.
- Keep the fail-closed parts intact: the workflow definition and schema pre-flight checks (lines 24-70)
  stay fatal.
- Record the rag_pipeline observability gap as a separate follow-up rather than fixing the MCP health
  contract inside this issue.

## Target Files or Areas
- `deploy/setup_services.sh` (health gate lines 76-129, Event Bus block lines 132-137, final summary lines 139-145)
- `docs/90_deployment/deployment_01_deployment.md` (the `setup_services.sh` section and its failure-mode table)
- `docs/24_eventbus/eventbus_07_configuration-and-operations.md` (how the Event Bus is started, and that it does
  not depend on the remote LLM services)
- Related, out of scope for the fix: `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`
  (`_check_health_deps` does not probe reachability)

## Required Changes
- Split the gate into a check that always runs and a severity decision: warning by default, fatal under a
  documented strict switch.
- Move or reorder the script so the Event Bus is started before the script can abort on a non-fatal remote
  LLM result, or make the abort happen only after the Event Bus block and the summary.
- Print both health statuses with the URLs and the last HTTP status or error, and state explicitly which
  services were started and which were skipped.
- Document the strict switch and the operator action for a down `embed-llm` in the deployment document.

## Constraints
- Do not start, configure, or assume ownership of `embed-llm` or `agent-llm`: the repository only verifies
  their health (`setup_services.sh` line 76).
- Keep `set -euo pipefail`; do not silence real failures to make the script exit zero.
- Keep the workflow definition and schema pre-flight checks fatal and in the same order relative to each other.
- Do not change `config/agent.toml`'s `embed_url` or `llm_url` values as a way to make the gate pass.
- Do not weaken `scripts/eventbus/config.py`'s fail-closed token validation while reordering the script.

## Acceptance Criteria
- With `embed-llm` unreachable and `agent-llm` healthy, `bash deploy/setup_services.sh` reaches the Event Bus
  block, starts it, exits 0, and its summary shows `embed-llm` as degraded/unreachable and the Event Bus as started.
- With `LLM_GATE_STRICT=1` (or the documented equivalent) the same state still fails with the existing
  `[FATAL] LLM services did not become ready ...` behavior.
- With both services healthy the script's behavior and output are unchanged apart from the clearer summary.
- The final summary names every service it started and every service it skipped, with the reason.
- The Event Bus does not start when its own token is missing (fail-closed behavior preserved).

## Testing Expectations
- Script-level test driving `setup_services.sh` with stubbed health endpoints (healthy / unreachable) and a
  temporary log directory, asserting exit code, the summary lines, and that the strict switch reproduces the
  abort. No real remote service and no writes to `/opt/llm`.
- Keep the existing workflow pre-flight assertions intact and add a case where the pre-flight failure still
  aborts before the Event Bus block.
- `rules/toolchain.md` sequence; documentation checkers from `routing.md` for the changed documents.

## Documentation Impact
Expected. `docs/90_deployment/deployment_01_deployment.md` must describe the gate's severity classification,
the strict switch, and the failure-mode row for an unreachable remote LLM service.
`docs/24_eventbus/eventbus_07_configuration-and-operations.md` must state that the Event Bus startup does not
depend on the remote LLM services. Remove any wording implying that a down embedding service blocks the whole
service-setup step.

## Out of Scope
- Supplying a startup command, model, or systemd unit for `embed-llm`.
- Changing `embed_url` / `llm_url` values, or adding new health endpoints.
- Adding a reachability probe to `rag_pipeline`'s `/health` or changing its health contract (record as a
  separate follow-up issue).
- Wiring a publisher or consumer into the agent (see `issues/20261019-210937_ebsec001_eventbus_auth_token_startup_block.md`,
  Out of Scope).
- The `Service readiness: FAIL (0 fatal, 1 warnings)` labeling in `scripts/agent/startup_reporter.py`.

## Dependencies
- Related: `issues/20261019-210937_ebsec001_eventbus_auth_token_startup_block.md`. Both are required for an
  Event Bus to actually come up, but each is independently implementable and independently reviewable; they
  touch different parts of the same script.
- Context: `scripts/agent/startup_validation.py` (warning versus fatal classification) and
  `scripts/agent/startup_reporter.py::report_readiness` are the existing severity vocabulary to align with.
- No open issue under `issues/` overlaps; sibling check recorded 2026-10-19.

## Unresolved Questions
- Whether a production deployment is expected to require both remote LLM services healthy before any local
  service starts (assumption: no, because the agent startup already tolerates the same condition as a warning).
- Whether `embed-llm` being down should make the `rag_pipeline` MCP tools unavailable-but-configured or
  report a degraded health state. Unknown: not stated in `docs/22_mcp/` for the rag_pipeline server.
- Whether the Event Bus is mandatory for a production deployment. Unknown.

## AI Implementation Instruction
- Reuse the existing severity vocabulary (`StartupCheckStatus` warning versus fatal) instead of inventing a
  third classification inside the shell script.
- Keep the diff to `deploy/setup_services.sh` and the two documents named above.
- Do not reorder the workflow pre-flight checks; they are fatal on purpose.
- Stop and report if making the gate non-fatal would allow a deployment to report success while a required
  service was never started; the summary must make any skipped service explicit.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261019-210938
- **Related target files**: `deploy/setup_services.sh`,
  `docs/90_deployment/deployment_01_deployment.md`,
  `docs/24_eventbus/eventbus_07_configuration-and-operations.md`
