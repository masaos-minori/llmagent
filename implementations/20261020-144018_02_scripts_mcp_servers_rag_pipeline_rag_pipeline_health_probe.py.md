## Goal

Provide the bounded, cached reachability probe that `rag_pipeline_server.py` calls
from `_check_health_deps` so a configured-but-unreachable `embed_url` can be
reported as `"unreachable"` (REQ-002).

## Scope

Create `scripts/mcp_servers/rag_pipeline/rag_pipeline_health_probe.py` (new file).
It exposes a single async entry point, e.g.
`probe_embed_reachable(embed_url, *, caller=None, timeout=...) -> "reachable" | "unreachable"`,
and nothing else is required by the plan. It is called only from
`rag_pipeline_server.py` (seq 01).

## Assumptions

- Probe endpoint is `<base>/health` via GET (UNK-01); `build_embed_url`
  (`/embedding`) is reused only if the embeddings endpoint is chosen instead.
- Default timeout is 2.0 s (agent precedent, `mcp_health.py:307`; UNK-02); TTL
  ~5-10 s, operator-tunable via env var.
- The probe may import from `shared` (permitted) but never from `agent`
  (`mcp_servers → db, shared` import contract; `lint-imports`, 6 contracts all KEPT).

## Design decisions

- **Injectable transport.** Accept an optional injected caller (an `httpx.AsyncClient`-like
  `.get` or an awaited callable) so tests supply a stub; default to a real bounded
  `httpx.AsyncClient`. A timeout/transport error resolves to `"unreachable"` (service
  not confirmed reachable), never raises.
- **Bounded + cached.** Explicit timeout constant (covers connect/read, so a hung
  transport cannot block past the timeout) and a short-TTL cache keyed by the embed
  base storing `(state, monotonic_timestamp)`; a fresh cached entry short-circuits
  the request so repeated `/health` polls issue at most one probe (AC-004, AC-005).

## Alternatives considered

- Caching at the call site in `rag_pipeline_server.py` instead of inside the probe.
  Keeping the cache in the probe module localizes the budget and makes it reusable;
  expose a reset for tests (UNK-02).

## Implementation

### Target file

`scripts/mcp_servers/rag_pipeline/rag_pipeline_health_probe.py` (new)

### Procedure

1. Create the module with the timeout constant, the injectable bounded caller, and
   the short-TTL cache.
2. Expose `probe_embed_reachable(embed_url, *, caller=None, timeout=...)`.

### Method

- Package location `scripts/mcp_servers/rag_pipeline/` keeps the import contract
  `mcp_servers must not import from agent` intact. Import `build_embed_url` from
  `shared.llm_client` only if the embeddings endpoint is the chosen probe target.
- Suggested shape:

  ```python
  from __future__ import annotations

  import time
  from collections.abc import Awaitable
  from typing import Any

  PROBE_TIMEOUT_SECONDS: float = 2.0          # UNK-02: agent precedent (mcp_health.py:307)
  CACHE_TTL_SECONDS: float = 5.0              # UNK-02: operator-tunable via env var

  _CACHE: dict[str, tuple[str, float]] = {}

  async def probe_embed_reachable(
      embed_url: str,
      *,
      caller: Any = None,
      timeout: float = PROBE_TIMEOUT_SECONDS,
  ) -> str:
      """Return "reachable" for a GET-able <base>/health, else "unreachable"."""
      base = embed_url.rstrip("/")
      now = time.monotonic()
      cached = _CACHE.get(base)
      if cached is not None and now - cached[1] < CACHE_TTL_SECONDS:
          return cached[0]
      state = await _run_probe(embed_url, caller, timeout)
      _CACHE[base] = (state, now)
      return state

  async def _run_probe(embed_url, caller, timeout) -> str:
      client = caller if caller is not None else _default_client()
      try:
          resp = await client.get(f"{base}/health", timeout=timeout)
      except Exception:
          return "unreachable"
      return "reachable" if resp.status_code == 200 else "unreachable"

  def reset_cache() -> None: ...   # for tests
  ```

- Keep the URL derivation (`<base>/health` vs `build_embed_url`) in one place so
  UNK-01's final choice is a single edit.

### Details

- Return type is the string `"reachable"` / `"unreachable"` (not an enum) so
  `rag_pipeline_server.py` maps it directly onto the `deps` value.
- The cache is module-level keyed by the embed base; expose `reset_cache()` (or
  equivalent) so tests can assert the call counter deterministically (AC-005).
- `httpx` is an existing project dependency; construct the default client lazily
  inside `_default_client()` so importing the module issues no connection.

## Compatibility considerations

N/A: this module is new and imported only by `rag_pipeline_server.py`.

## Security considerations

Issues one timeout-bounded GET to the configured `embed_url` base per cache window;
the transport is injectable for tests. No secret is transmitted.

## Rollback considerations

N/A: revert the commit (deletes the new file).

## Validation plan

- Reachable transport → `"reachable"`; failing transport → `"unreachable"`.
- Hanging transport resolves within the timeout constant (AC-004).
- N calls within the TTL issue one probe request via a call counter (AC-005).
- `reset_cache()` clears the cache.
- Import check: `lint-imports` still passes (no `agent` import).

## Completion criteria

- `probe_embed_reachable` returns `"reachable"` / `"unreachable"` correctly.
- Worst-case latency is bounded by the timeout constant.
- Repeated calls within the TTL issue at most one probe request.

## Out of Scope

- Calling the probe (that is `rag_pipeline_server.py`, seq 01).
- Startup / posture validation.
- Documentation (own rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `rag_pipeline_health_probe.py` (injectable, bounded, cached) | Pending | — | — | REQ-002 |
| 2 | Add reachable/unreachable/timeout/cache unit tests | Pending | — | — | REQ-002 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261019-214637_ragobs003_rag_pipeline_health_misses_embed_outage.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261020-132416_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261020-144018
- **Related target files**: scripts/mcp_servers/rag_pipeline/rag_pipeline_health_probe.py
