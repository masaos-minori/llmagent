# `rag-pipeline-mcp` reports `ok` while the embedding service is unreachable, so an `embed-llm` outage is invisible in MCP health

## Priority
Medium

## Summary
Extend the `rag-pipeline-mcp` `/health` dependency check so that a configured but unreachable
`embed_url` is reported as a degraded dependency, instead of only reporting the key as absent. Today
the check proves the key exists and never looks at the service, so the server answers `200 ok /
ready: true` for the whole duration of an embedding outage while the two embedding tools fail at call
time.

## Background
- Found on 2026-10-19 while investigating why `deploy/setup_services.sh` aborts on an unreachable
  `embed-llm` (`http://192.168.11.238:8081`, `All connection attempts failed`) even though the rest of
  the stack is healthy. `192.168.11.238` is this host's own `enp3s0` address.
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py:208-221` (`_check_health_deps`) loads
  `rag_pipeline_mcp_server.toml` and records `deps["embed_url"] = "not configured"` only when the value
  is falsy or not a `str`. It issues no request and never observes the service.
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py:224-234` (`GET /health`) passes those deps to
  `scripts/mcp_servers/health_response.py:26-57`, where `ready = len(deps) == 0 and security.validated`
  and any non-empty `deps` yields `503` with `operator_action_required: true`.
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_security.py:37,46` states the posture check is
  presence-only by design ("validation cannot issue an outbound request or touch a database") and
  contributes check id `server.embed_url_configured` (see
  `tests/mcp_servers/rag_pipeline/test_rag_pipeline_health_posture.py:24`).
- The documented contract matches the code, so this is a contract extension rather than a code-versus-doc
  defect: `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md:64`,
  `docs/22_mcp/mcp_02_02_startup-modes-and-health.md:166`,
  `docs/21_rag/rag_01_system_overview.md:153-157`,
  `docs/22_mcp/mcp_06_04_verification-methods.md:84` all define `dependencies` as
  `embed_url: "not configured"` / `config: "check failed"` only.
- Tool availability uses the same presence-only signal: `rag_pipeline_server.py:129-130` disables
  `rag_run_pipeline` and `rag_debug_pipeline` only when `cfg.embed_url` is empty
  (`"embed_url is not configured"`), so with the key configured the tools stay enabled and fail only
  inside `call_tool`.

## Problem
- Measured on 2026-10-19: `embed_url = "http://192.168.11.238:8081"` is configured
  (`config/rag_pipeline_mcp_server.toml:10`) and the service is unreachable, while
  `llm_url = "http://192.168.11.197:8080"` is healthy. The agent logged `WARNING [check_service_health]
  [non-fatal] embed-llm unreachable at http://192.168.11.238:8081/health` and its readiness line read
  `Service readiness: FAIL (0 fatal, 1 warnings, 0 skipped)`.
- Code-derived consequence (not measured live, because no MCP server was running at the time): with that
  configuration `rag-pipeline-mcp` `/health` returns `status: "ok"`, `ready: true`, `dependencies: {}`,
  HTTP 200. An operator following `docs/22_mcp/mcp_06_04_verification-methods.md:28` (curl `/health` and
  read `dependencies.embed_url`) sees a healthy server.
- Consequence for monitoring: `deploy/setup_services.sh`'s LLM gate is currently the only place in the
  deployment path that notices an embedding outage, and it reacts by aborting the whole script
  (`issues/20261019-210938_ebops002_setup_services_llm_gate_blocks_eventbus.md`). Once that gate is made
  non-fatal, nothing in the MCP health layer would report the outage at all.
- Sibling precedent shows the pattern is available: `mdq` records real observed state in its health input
  (`scripts/mcp_servers/mdq/health_check.py::_collect_dependencies` → db file presence, schema error,
  index stats, fed into `build_mdq_posture`). No MCP server probes a remote URL in its health input today
  (a search for `_check_health_deps` / `health_deps` finds only `rag_pipeline_server.py` and
  `scripts/mcp_servers/file/common.py:194`, and no `httpx` use in any `*security*.py` or `*health*.py`
  MCP module). So this introduces a new health-probe pattern and must be scoped deliberately.

## Reason for Change
- Production reliability: the only embedding-dependent MCP server cannot distinguish "configured" from
  "working", which is exactly the state an operator needs during an outage.
- Public API behavior: `/health` is the documented readiness surface for MCP servers, and its `ready`
  claim is currently weaker than operators reasonably read it.
- Consistency: `mdq` reports observed dependency state while `rag_pipeline` reports configured-only state,
  even though embedding availability is the rag_pipeline server's single hard runtime dependency.
- Safety of the current signal: the outage is currently visible only as one non-fatal agent warning plus
  a hard abort in `setup_services.sh`; the MCP layer adds a contradicting healthy signal.

## Implementation Intent
- Keep the presence check (`"not configured"`) exactly as it is, and add a distinct second state for
  reachability, for example `deps["embed_url"] = "unreachable"`, so the two failure modes stay
  distinguishable in the response body and in tests.
- Keep the posture check presence-only. `scripts/mcp_servers/rag_pipeline/rag_pipeline_security.py:37` is a
  deliberate design property (startup validation must not issue outbound requests); changing startup
  behavior is not part of this issue.
- Put the probe in the health path only, with a hard request timeout and a short-lived cache, so `/health`
  stays fast and does not multiply load on the embedding service. Reuse `scripts/shared/llm_client.py:37-42`
  (`build_embed_url`) for URL derivation, and follow how the agent derives its probe URL by stripping the
  path from the endpoint (`scripts/agent/services/mcp_health.py:281-290`).
- Respect the import contract `mcp_servers must not import from agent` (`uv run lint-imports`, 6 contracts):
  the probe helper belongs in `scripts/shared/` or inside `scripts/mcp_servers/rag_pipeline/`, not in the
  agent package.
- Preserve the agent's tolerance: `make_health_response` keeps `restart_recommended: false`, and the agent
  already treats a `503` with `liveness: true` as degraded-but-live
  (`scripts/agent/http_lifecycle_health_checker.py:79-90,165-171`), so a remote outage must degrade the
  server without causing a restart loop. Verify this instead of assuming it.

## Target Files or Areas
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` (`_check_health_deps`, `GET /health`)
- `scripts/mcp_servers/rag_pipeline/` new probe helper module (naming to match the package's existing
  modules) or a shared helper under `scripts/shared/`
- `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py` and
  `tests/mcp_servers/rag_pipeline/test_rag_pipeline_health_posture.py`
- Documentation: `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` (Health contract, line 64),
  `docs/22_mcp/mcp_02_02_startup-modes-and-health.md:166` (per-server `dependencies` table),
  `docs/21_rag/rag_01_system_overview.md:153-157` (health check and remediation guidance),
  `docs/22_mcp/mcp_06_04_verification-methods.md:84` (dependency reason table)

## Required Changes
- Report a third dependency state for a configured `embed_url` that fails a bounded reachability probe.
- Keep the probe bounded (explicit short timeout, no retry storm) and cached for a short TTL so repeated
  `/health` polls do not hammer the embedding service.
- Keep `restart_recommended: false` and `liveness: true` for the unreachable case so the agent keeps
  treating the server as degraded-but-live.
- Update the four documents listed above so the documented `dependencies` values include the new state and
  the remediation guidance distinguishes "not configured" from "unreachable".
- Confirm `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`'s exact response-shape sentences are updated in
  the same commit as the code, so `tools/check_docs_consistency.py` stays meaningful.

## Constraints
- Do not change startup validation or the Security Posture contract: `server.embed_url_configured` stays a
  presence check and startup must not require the embedding service to be reachable.
- Do not make the embedding service a fatal startup dependency for `rag-pipeline-mcp`: `llm_url` is the
  required service and `embed-llm` is optional (agent-side documented behavior,
  `scripts/agent/services/mcp_health.py:283-286`).
- Do not start, configure, or take ownership of `embed-llm` in this issue.
- Keep `mcp_servers must not import from agent`; add no new cross-package dependency.
- Do not let `/health` block longer than the probe timeout under any circumstance, including DNS stalls.
- No network access in tests: drive the probe through an injectable transport or a local stub, and do not
  read or write `/opt/llm`.

## Acceptance Criteria
- With `embed_url` configured and the probe failing, `GET /health` returns HTTP 503 with
  `status: "degraded"`, `ready: false`, `liveness: true`, `restart_recommended: false`, and
  `dependencies: {"embed_url": "unreachable"}`.
- With `embed_url` configured and reachable, `/health` returns the current `200 ok` shape unchanged.
- With `embed_url` absent or not a string, the existing `"not configured"` state and its 503 response are
  unchanged, and the new probe is not attempted.
- The `/health` handler's worst-case latency is bounded by the probe timeout (asserted in a test with a
  transport that would otherwise hang).
- Repeated `/health` calls within the cache TTL issue at most one probe request (asserted by a call counter).
- Startup succeeds with the embedding service unreachable, with `server.embed_url_configured` still passing
  posture validation.
- The four documents state the new state and the distinction from `"not configured"`, and
  `uv run python tools/check_docs_consistency.py --domain mcp` and `--domain rag` pass.

## Testing Expectations
- Unit tests in `tests/mcp_servers/rag_pipeline/`: reachable, unreachable, missing-key, non-string value,
  probe timeout, and cache behavior (one probe for N health calls).
- An agent-side regression test that a `503` with `liveness: true` from rag_pipeline is still accepted as
  degraded-but-live at startup (no restart, no fatal).
- No real embedding service, no `/opt/llm` access, and no dependence on wall-clock timing beyond the stubbed
  transport.
- Full `rules/toolchain.md` sequence, plus the `routing.md` documentation checkers for the changed documents.

## Documentation Impact
Expected. The documented `/health` contract changes for one server, so the four documents named in Target
Files must be updated in the same commit: the response-shape sentence in
`docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md:64`, the `dependencies` table row in
`docs/22_mcp/mcp_02_02_startup-modes-and-health.md:166`, the health-check and remediation paragraphs in
`docs/21_rag/rag_01_system_overview.md:153-157`, and the reason-code table row in
`docs/22_mcp/mcp_06_04_verification-methods.md:84`. Wording that implies `dependencies.embed_url` only ever
means "not configured" must be corrected.

## Out of Scope
- Startup-time reachability validation or any change to Security Posture semantics.
- Adding reachability probes to other MCP servers or a shared health-probe framework.
- Making `embed-llm` a required service, or supplying its startup command, model, or service unit.
- `deploy/setup_services.sh`'s gate severity (covered by
  `issues/20261019-210938_ebops002_setup_services_llm_gate_blocks_eventbus.md`).
- The `Service readiness: FAIL (0 fatal, 1 warnings)` labeling in `scripts/agent/startup_reporter.py`.

## Dependencies
- Related: `issues/20261019-210938_ebops002_setup_services_llm_gate_blocks_eventbus.md`. That issue removes
  the only current outage signal (the aborting gate); this issue supplies the replacement signal. Each is
  independently implementable, but the deployment story is only complete with both.
- Context: `scripts/shared/llm_client.py::build_embed_url` and
  `scripts/agent/services/mcp_health.py::check_service_health` (the existing probe-URL derivation pattern to
  mirror without importing the agent package).
- No open issue under `issues/` overlaps; sibling check recorded 2026-10-19.

## Unresolved Questions
- Which endpoint to probe: the `<base>/health` path the agent uses, or the embeddings endpoint produced by
  `build_embed_url` (`/v1/embeddings`). The repository currently probes `/health` for both LLM services and
  does not define which one an MCP server should use.
- Cache TTL and timeout values: nothing in the repository defines a health-probe budget for MCP servers.
  Unknown: the intended worst-case `/health` latency the operator tooling can tolerate.
- Whether `operator_action_required: true` is the right signal for a transient embedding outage, or whether
  the outage should appear only under `details` to keep `ready` reserved for configuration faults.
- Whether `rag_debug_pipeline` and `rag_run_pipeline` should report `disabled_reason`
  `"embed_url unreachable"` when the cached probe is failing, which would change `/v1/tools` output too.

## AI Implementation Instruction
- Keep the diff inside `scripts/mcp_servers/rag_pipeline/`, its tests, and the four documents named above;
  do not touch the agent package or the shared Security Posture modules.
- Make the probe injectable (transport or callable parameter) so tests need no network, and keep the default
  path bounded by an explicit timeout constant.
- Do not convert the unreachable state into a startup failure, a posture failure, or a `restart_recommended`
  signal.
- Stop and report if making `/health` depend on a remote service would change how the agent's startup poll
  treats the server (verify against `scripts/agent/http_lifecycle_health_checker.py::is_degraded_but_live`).

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261019-214637
- **Related target files**: `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`,
  `scripts/mcp_servers/rag_pipeline/rag_pipeline_security.py`,
  `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py`,
  `tests/mcp_servers/rag_pipeline/test_rag_pipeline_health_posture.py`,
  `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`,
  `docs/22_mcp/mcp_02_02_startup-modes-and-health.md`,
  `docs/21_rag/rag_01_system_overview.md`,
  `docs/22_mcp/mcp_06_04_verification-methods.md`
