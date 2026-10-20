## Goal

Add unit tests for the new `"unreachable"` `/health` state and the probe's bounded/cached
behavior, driven through the injectable transport so no real network is used, and stub
the probe so the existing `/health` tests in this file stay network-free (REQ-001, REQ-002).

## Scope

Modify `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py` only:

- Add reachable / unreachable / missing-key / non-string / timeout / cache cases.
- Stub the probe in the existing `/health`-reading tests so they read a deterministic
  body without issuing an outbound request.

The probe helper is created in its own target file (seq 02); this file only exercises
it via the injectable transport.

## Assumptions

- The probe entry point is `probe_embed_reachable(embed_url, *, caller=None, timeout=...)`
  returning `"reachable"` / `"unreachable"` (see seq 02).
- `_check_health_deps` imports the probe lazily (local import), so stubbing the probe
  module attribute is observed on each call.
- The shipped `config/rag_pipeline_mcp_server.toml:10` sets a configured `embed_url`, so
  the success path (probe attempted) is taken unless the config is patched to omit it.

## Design decisions

- **Stub via the injectable transport.** Tests set
  `monkeypatch.setattr("mcp_servers.rag_pipeline.rag_pipeline_health_probe.probe_embed_reachable",
  stub)` to control the result, and use a call-counting stub to assert the cache
  (AC-004, AC-005).
- **Config control via `ConfigLoader`.** Missing-key / non-string cases patch
  `shared.config_loader.ConfigLoader` to return a config without (or with a non-string)
  `embed_url`, so the presence check fires and the probe is not attempted.

## Alternatives considered

- Patching a module-level binding on `server` instead of the probe module attribute.
  The local-import design (seq 01) makes the probe-module attribute the correct,
  single stub target.

## Implementation

### Target file

`tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py`

### Procedure

1. Stub the probe for the existing health test so it stays deterministic:

   ```python
   def test_config_load_failure_reports_degraded(self, client, monkeypatch):
       monkeypatch.setattr(
           "mcp_servers.rag_pipeline.rag_pipeline_health_probe.probe_embed_reachable",
           stub_probe("reachable"),
       )
       ...  # unchanged _BoomLoader body → {"config": "check failed"}
   ```

   (The `_BoomLoader` still raises before the probe is reached; the stub is harmless
   documentation that the config-failure path never probes.)

2. Add a `TestHealthEndpoint` cases for the new states (below).

### Method

- Reachable (configured `embed_url`, probe `"reachable"`): `GET /health` → HTTP 200,
  `dependencies == {}`, `ready == True` (AC-002).
- Unreachable (probe `"unreachable"`): `GET /health` → HTTP 503,
  `dependencies == {"embed_url": "unreachable"}`, `ready == False`,
  `liveness == True`, `restart_recommended == False` (AC-001, AC-003).
- Missing key: patch `ConfigLoader` to return `{}` (no `embed_url`) →
  `dependencies == {"embed_url": "not configured"}`, probe stub's `assert_not_called()`
  (AC-003).
- Non-string: patch `ConfigLoader` to return `{"embed_url": 123}` →
  `dependencies == {"embed_url": "not configured"}`, probe not called (AC-003).
- Timeout: inject a `caller` whose `.get` awaits forever; the call resolves within the
  timeout constant and reports `"unreachable"` (AC-004). Drive it through the probe
  directly (pass `caller=`) rather than through the endpoint.
- Cache: two probe calls within the TTL issue exactly one request — use a counting
  `caller` and assert `call_count == 1` on the second call (AC-005). Call
  `reset_cache()` between sub-cases.

### Details

- Keep `test_config_load_failure_reports_degraded` asserting exactly
  `body["dependencies"] == {"config": "check failed"}` — the probe must not run on
  the config-failure path.
- These tests use the existing `client` fixture (auth header + patched `_service`);
  `/health` does not touch `_service`, so no extra fixture work is needed.
- Do not introduce any real network access; every probe path is stubbed.

## Compatibility considerations

N/A: test-only additions; existing characterization tests are preserved.

## Security considerations

N/A: test-only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py`:
  reachable → 200, unreachable → 503 `{"embed_url":"unreachable"}` with
  `liveness:true`/`restart_recommended:false`, missing/non-string → `"not configured"`
  with no probe, timeout bounded, cache = one probe per TTL window, and
  `test_config_load_failure_reports_degraded` still `{"config": "check failed"}`.

## Completion criteria

- All new `/health` cases pass with a stubbed probe and no network.
- The unreachable case carries `liveness:true` and `restart_recommended:false`.
- The timeout case resolves within the probe timeout; the cache case issues one probe
  for N calls.

## Out of Scope

- Creating the probe module (seq 02).
- Posture tests (seq 04).
- Documentation (own rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add reachable/unreachable/missing-key/non-string/timeout/cache unit tests | Pending | — | — | REQ-001, REQ-002 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20261019-214637_ragobs003_rag_pipeline_health_misses_embed_outage.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261020-132416_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261020-144018
- **Related target files**: tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py
