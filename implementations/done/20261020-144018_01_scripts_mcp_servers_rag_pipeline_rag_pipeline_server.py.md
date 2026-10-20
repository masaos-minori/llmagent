## Goal

Give `rag-pipeline-mcp` `/health` a real reachability signal for `embed_url`: a
configured-but-unreachable embedding service is reported as a distinct
`"unreachable"` dependency state (HTTP 503, `ready: false`, `liveness: true`)
instead of only reporting the key as absent, so an embedding outage is visible in
the MCP health layer rather than invisible while the two embedding tools fail at
call time (REQ-001, REQ-003).

## Scope

Only `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`:

- Extend `_check_health_deps` (current lines 208-220) to run a bounded reachability
  probe for a configured `embed_url` and add the `"unreachable"` state.
- Wire the probe result into `GET /health` (current lines 223-231) through the
  unchanged `make_health_response` call.
- Keep the presence check (`"not configured"`) and the config-failure branch
  (`"check failed"`, early return before any probe) byte-for-byte equivalent.

The probe helper itself lives in its own target file
(`scripts/mcp_servers/rag_pipeline/rag_pipeline_health_probe.py`, seq 02) — this
document only calls it.

## Assumptions

- Probe endpoint is `<base>/health` via GET (UNK-01 decision, belongs to
  implementation); `build_embed_url` (`/embedding`) is reused only if the
  embeddings endpoint is chosen instead.
- Default probe timeout is 2.0 s (agent precedent, `mcp_health.py:307`; UNK-02);
  cache TTL ~5-10 s, operator-tunable via env var.
- The probe is injectable (transport/callable parameter) so tests need no network.
- `make_health_response` keeps `restart_recommended: false` and `liveness: true`;
  the agent already treats a `503` with `liveness: true` as degraded-but-live
  (`http_lifecycle_health_checker.py::is_degraded_but_live`, lines 79-96).

## Design decisions

- **Three-state model in `_check_health_deps`.** absent / non-string →
  `"not configured"` (unchanged); config load error → `"check failed"` (unchanged,
  returned early before any probe); configured but reachability probe fails →
  `"unreachable"` (new). The probe runs only on the success path (config loaded and
  `embed_url` a non-empty string), so the config-failure characterization test
  (`test_rag_pipeline_server_endpoints.py::test_config_load_failure_reports_degraded`,
  which expects exactly `{"config": "check failed"}` with no probe) stays green.
- **Lazy, injectable call.** `_check_health_deps` imports and calls the probe
  lazily (local import, matching the existing lazy `ConfigLoader` import) after the
  presence check passes. The probe result becomes a `deps` entry; `make_health_response`
  is invoked unchanged, so the response shape (`liveness:true`, `restart_recommended:false`,
  HTTP 503, `ready:false`, `operator_action_required:true`) is preserved (REQ-003).

## Alternatives considered

- Probing the embeddings endpoint (`build_embed_url(...)` → `/embedding`) instead of
  `<base>/health`. Preferring `<base>/health` mirrors the agent's own probe
  (`mcp_health.py:303-307`), needs no request payload, and is already proven
  reachable for the embed base (UNK-01).

## Implementation

### Target file

`scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`

### Procedure

1. In `_check_health_deps`, after the presence check passes, run the bounded probe
   for the configured `embed_url` and record `"unreachable"` when it is not
   reachable.
2. Make `_check_health_deps` `async` and `await` it in `GET /health`; confirm `deps` is still forwarded to `make_health_response` unchanged.

### Method

- Current `_check_health_deps` (lines 208-220):

  ```python
  def _check_health_deps() -> dict[str, str]:
      """Return dependency problems, if any, for the health check."""
      deps: dict[str, str] = {}
      try:
          from shared.config_loader import ConfigLoader

          cfg = ConfigLoader().load("rag_pipeline_mcp_server.toml")
          embed_url = cfg.get("embed_url")
          if not embed_url or not isinstance(embed_url, str):
              deps["embed_url"] = "not configured"
      except Exception:  # noqa: BLE001 — health check must not fail on config errors
          deps["config"] = "check failed"
      return deps
  ```

- `probe_embed_reachable` is `async`, so `_check_health_deps` becomes `async def` and
  `GET /health` (already `async def`) calls it as `deps = await _check_health_deps()`.
  Its only caller is `health()`; no test calls it directly (verified with `rg`).
- After the `if not embed_url ...` block (i.e. on the success path where
  `embed_url` is a non-empty string), import the probe and call it:

  ```python
  from mcp_servers.rag_pipeline.rag_pipeline_health_probe import (
      probe_embed_reachable,
  )

  ...
  probe_state = await probe_embed_reachable(embed_url)
  if probe_state != "reachable":
      deps["embed_url"] = "unreachable"
  ```

- Make the probe call fault-tolerant: a probe timeout/exception must resolve to
  `"unreachable"` (service not confirmed reachable), never raise out of
  `_check_health_deps`. Either the probe itself catches and returns
  `"unreachable"`, or wrap the call so any exception maps to `"unreachable"`. Do
  **not** let a probe failure escape into the `except Exception` branch that sets
  `deps["config"] = "check failed"`.
- `GET /health` (lines 223-231) changes only by awaiting the now-async
  `_check_health_deps()`; it still passes the result to `make_health_response`
  unchanged and simply carries the new `"unreachable"` value when present.

### Details

- `make_health_response` (`scripts/mcp_servers/health_response.py`, lines 26-57)
  derives `ready = len(deps) == 0 and (security is None or security.validated)`
  (line 43); any non-empty `deps` yields HTTP 503 with
  `status:"degraded"`, `ready:false`, `liveness:true`, `restart_recommended:false`,
  `operator_action_required:true`. Adding `deps["embed_url"]="unreachable"` therefore
  produces exactly the AC-001 body without touching `make_health_response`.
- Keep the probe call on the success path only. The config-failure branch returns
  `{"config": "check failed"}` before the probe is ever imported/called, so
  `test_config_load_failure_reports_degraded` stays locked to that exact body.
- Import direction: `rag_pipeline_server.py` already imports from `shared` and
  `mcp_servers.*`; the probe lives in the same package, so no new architecture
  boundary is crossed. `lint-imports` (6 contracts, all KEPT) stays green.

## Compatibility considerations

`/health` now issues one bounded outbound HTTP request per cache window
(AC-004, AC-005). With the shipped unreachable `embed_url`
(`config/rag_pipeline_mcp_server.toml:10`), `/health` returns 503
`{"embed_url":"unreachable"}` where it previously returned 200 `ok`. The agent's
`is_degraded_but_live` treats such a `503` with `liveness:true` as ready, so there
is no restart loop; verify `tests/agent/test_http_lifecycle_health_check.py`
stays green rather than assuming it (REQ-003).

## Security considerations

The health endpoint now performs a single, timeout-bounded GET to the configured
`embed_url` base. The transport is injectable (tests stub it); no credential or
secret is sent or logged. `operator_action_required` follows the existing
`not ready` derivation unchanged.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- Reachable: configured `embed_url` + passing probe → current 200 `ok` shape
  unchanged (AC-002).
- Unreachable: configured `embed_url` + failing probe → HTTP 503 with
  `dependencies={"embed_url":"unreachable"}`, `ready:false`, `liveness:true`,
  `restart_recommended:false` (AC-001, AC-003).
- Missing/non-string `embed_url` → `"not configured"` unchanged and the probe is
  **not** attempted (AC-003).
- Timeout: a transport that would hang resolves within the timeout constant
  (AC-004).
- Cache: N `/health` calls within the TTL issue at most one probe request
  (AC-005).
- Existing `test_config_load_failure_reports_degraded` still expects exactly
  `{"config": "check failed"}` (no probe on the config-failure path).

## Completion criteria

- Configured + unreachable → HTTP 503 with
  `dependencies={"embed_url":"unreachable"}`, `ready:false`, `liveness:true`,
  `restart_recommended:false`.
- Configured + reachable → HTTP 200 `ok` unchanged.
- Absent or non-string `embed_url` → `"not configured"` unchanged and no probe
  request issued.

## Out of Scope

- The probe helper module (`rag_pipeline_health_probe.py`, seq 02).
- Startup / security-posture behavior (`rag_pipeline_security.py` stays
  presence-only).
- Tool availability gating (`_rag_pipeline_tool_availability`).
- Documentation updates (own rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend `_check_health_deps` with the bounded probe and the `"unreachable"` state; wire into `GET /health` | Completed | 20261020-181626 | 20261020-181626 | REQ-001, REQ-003 changed: scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py; procedure corrected: _check_health_deps made async (user-approved); first attempt reverted on cicd health test failure, reapplied after plan amendment |
| 2 | Add reachable/unreachable/missing-key/timeout/cache unit tests | Completed | 20261020-181626 | 20261020-181626 | REQ-001, REQ-002 N/A: tests are seq 03/04/09 target files |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261020-181626 | 20261020-181626 | ruff, mypy, lint-imports, bandit, module-size pass; full suite 9652 passed, 14 skipped |

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
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: issues/20261019-214637_ragobs003_rag_pipeline_health_misses_embed_outage.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261020-132416_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261020-144018
- **Related target files**: scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py