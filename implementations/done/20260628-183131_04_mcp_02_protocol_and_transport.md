# Implementation: MCP /health status, ready, and dependency semantics consistency

## Goal

Define and enforce consistent semantics for MCP `/health` response fields: `status`, `ready`, and `dependencies`. Ensure operators can determine readiness from `/health`, watchdog behavior is documented and matches implementation, and dependency failures are not silently treated as healthy.

## Scope

- **In-Scope**:
  - Define canonical semantics for `status`, `ready`, `dependencies` fields
  - Apply semantics consistently across all MCP server health endpoints
  - Document HTTP status code behavior (200 vs non-200)
  - Clarify watchdog behavior (HTTP response status vs body `status` vs body `ready`)
  - Update `/mcp` status display logic if needed
  - Add health tests for each server category

## Assumptions

- HTTP status code should reflect `status` field (200 for ok, 503 for non-ok) — consistent with EventBus behavior
- Watchdog uses HTTP response status code only (`resp.status_code == HTTPStatus.OK`), NOT body fields
- `/mcp` status uses HTTP status code for availability + health_registry state for health status
- Dependency failures that can be resolved by configuration should set `ready=false`, `status="degraded"`, and return **HTTP 503** (watchdog will restart)

## Implementation

### Target files

1. `scripts/mcp/server.py` — base health() method, HTTP status code logic
2. `scripts/mcp/shell/server.py` — health endpoint with shell dependency
3. `scripts/mcp/github/server.py` — health endpoint with github_token dependency
4. `scripts/mcp/file/read_server.py` — health endpoint with filesystem dependency
5. `scripts/mcp/file/write_server.py` — health endpoint with filesystem dependency
6. `scripts/mcp/file/delete_server.py` — health endpoint with filesystem dependency
7. `scripts/mcp/rag_pipeline/server.py` — health endpoint with embed_url dependency
8. `scripts/mcp/git/server.py` — health endpoint with git dependency
9. `scripts/mcp/mdq/server.py` — health endpoint with stale_document_count
10. `scripts/mcp/cicd/server.py` — health endpoint with github_token dependency
11. `scripts/mcp/web_search/server.py` — health endpoint (no dependencies)
12. `scripts/mcp/installer_templates.py` — health template for new servers
13. `docs/04_mcp_02_protocol_and_transport.md` — protocol docs
14. `docs/04_mcp_06_configuration_and_operations.md` — ops docs with examples
15. `agent/repl_health.py` — watchdog logic (verify behavior)
16. New test file: `tests/test_mcp_server_health_status.py`

### Procedure

#### Phase 1: Define canonical semantics

No code changes needed. Document the canonical semantics in `docs/04_mcp_02_protocol_and_transport.md`:

- `status` values: "ok", "degraded", "unhealthy"
- `ready` semantics: true when no dependency failures, false when any dependency failure
- HTTP status code behavior: **200 for ok, 503 for degraded/unhealthy**
- Watchdog behavior: HTTP status only, body fields NOT checked

#### Phase 2: Update base health() method

Update `scripts/mcp/server.py`:

1. Add `status_code` parameter to `MCPServer.health()` method signature
2. Update base method to return HTTP status code based on `ready` field:
   ```python
   def health(self) -> tuple[dict[str, object], int]:
       """Return health dict and HTTP status code."""
       deps: dict[str, str] = {}
       ready = len(deps) == 0
       status_code = 200 if ready else 503
       return {
           "status": "ok" if ready else "degraded",
           "ready": ready,
           "dependencies": deps,
           "details": {},
       }, status_code
   ```

#### Phase 3: Apply consistently across MCP servers

For each MCP server health endpoint:

1. Update the override method to return `(health_dict, status_code)` tuple
2. When dependencies fail, set `status="degraded"`, `ready=false`, and return HTTP 503
3. Update `scripts/mcp/installer_templates.py` template to reflect new return type

Example for each server:
```python
def health(self) -> tuple[dict[str, object], int]:
    deps = {}
    if not self._check_dependency():
        deps["dependency_name"] = "not_set" or "check failed"
    ready = len(deps) == 0
    return {
        "status": "ok" if ready else "degraded",
        "ready": ready,
        "dependencies": deps,
        "details": {},
    }, 200 if ready else 503
```

#### Phase 4: Update documentation

Update `docs/04_mcp_02_protocol_and_transport.md`:

1. Add canonical semantics section for `/health` response fields
2. Document HTTP status code behavior (200 vs 503)
3. Clarify watchdog behavior (HTTP status only, body fields NOT checked)

Update `docs/04_mcp_06_configuration_and_operations.md`:

1. Add `/health` response examples for each server category (ok, degraded)
2. Document HTTP status code behavior with curl examples

#### Phase 5: Add tests

Create `tests/test_mcp_server_health_status.py`:

1. Test default health returns ok/200
2. Test degraded health returns degraded/503
3. Test each server category (ok, degraded) with pytest parameterization
4. Verify watchdog behavior uses HTTP status code only

### Method

- Add `status_code` return value to `health()` method signature — backward compatible via tuple unpacking in callers
- Each server override returns `(dict, int)` instead of just `dict`
- Watchdog already checks `resp.status_code == HTTPStatus.OK`, so no watchdog changes needed
- `/mcp` status display already uses HTTP status code for availability

### Details

**Breaking change note**: The `health()` method return type changes from `dict[str, object]` to `tuple[dict[str, object], int]`. All callers must update:

1. HTTP endpoint handlers — extract tuple and use both values
2. Any other code that calls `health()` — update to unpack tuple

**HTTP status code mapping**:
- `status="ok"` → HTTP 200
- `status="degraded"` → HTTP 503 (Service Unavailable)
- `status="unhealthy"` → HTTP 503 (Service Unavailable)

**Watchdog behavior**: Watchdog checks `resp.status_code == HTTPStatus.OK` only. Body fields (`status`, `ready`) are NOT checked by the watchdog. This means:
- HTTP 200 → watchdog considers server healthy regardless of body `status` field
- HTTP 503 → watchdog considers server unhealthy and will restart

**/mcp status display**: Already uses HTTP status code for availability + health_registry state for health status. No changes needed.

## Validation plan

| Check | Tool | Target | Expected Outcome |
|---|---|---|---|
| Default health returns ok/200 | pytest | `test_default_health_returns_ok` | Passes |
| Degraded health returns degraded/503 | pytest | New test | Passes |
| All MCP servers return consistent semantics | pytest | All server health tests | All pass |
| HTTP status codes correct (200 vs 503) | curl + jq | Each server /health endpoint | Correct HTTP status for each state |
| Watchdog behavior unchanged | pytest | Existing watchdog tests | Passes |
| /mcp status display unchanged | curl + jq | /mcp endpoint | Readiness correctly determined |
| No stale issue IDs remain | rg | `rg "BUG-[1-3]|OQ-[1-7]" docs/03_rag_*.md` | 0 matches |
| use_rrf routing exists | rg | `rg "use_rrf" docs/03_rag_00_document-guide.md` | 1 match |

## Risks

- **Risk**: Breaking changes to existing health check consumers (load balancers, orchestration tools) → **Mitigation**: Document breaking changes clearly, provide migration notes
- **Risk**: Watchdog now restarts servers on dependency failures (new behavior vs current) → **Mitigation**: Document this change explicitly; operators should be aware of auto-restart on degraded state
- **Risk**: Inconsistent HTTP status code across servers during transition → **Mitigation**: Update all servers simultaneously in single commit
