## Goal
Merge the dedup store metrics block into the web-search-mcp `/health` `details`, alongside its existing metrics keys (REQ-004, the health payload reports dedup store metrics and capacity status).
## Scope
**Release unit**: health exposure
- One change confined to the existing `/health` handler in `scripts/mcp_servers/web_search/web_search_server.py`.
## Assumptions
- `dedup_health_details()` (new) is added by the row-09 sibling document in `scripts/mcp_servers/health_response.py`; it reads the dispatcher's `_dedup_store` / `_dedup_config` module globals and returns `{}` — never an exception — when the store is absent or the read fails (REQ-002 degradation path, the default in existing tests).
## Design decisions
- The merge stays inside the handler so `make_health_response()`'s signature, the payload keys, and the status-code logic stay unchanged; the block is the single new `details` key `"dedup"`.
## Alternatives considered
- N/A: the Plan fixes the wiring point in the existing handler; no alternative for a confined one-key merge.
## Implementation
### Target file
`scripts/mcp_servers/web_search/web_search_server.py`
### Procedure
- Extend the existing `from mcp_servers.health_response import make_health_response` (line 25) to also import `dedup_health_details`.
- In `health_endpoint()` (line 139-155): after `details` has been built — `service`, `provider`, `metrics`, `browser_provider`, `browser_metrics` (line 143-147) — and before the `make_health_response(deps, details, security=_security_posture)` call (line 152), add `details.update(dedup_health_details())`.
- No other change in the file.
### Method
- Additive merge of the single new `details` key `"dedup"`, present only when the server's dedup store is open; the new key sits alongside the existing `metrics` and `browser_metrics` keys without renaming or touching them, and the local `mcp_servers.web_search.metrics` module and the `deps` degradation branches stay as they are.
### Details
- The block carries the REQ-004 metrics fields: per-status counts, growth, WAL size, lock wait, lease health, and threshold status.
## Compatibility considerations
- `tests/mcp_servers/web_search/test_web_search_health.py` asserts web-search-mcp `details` by key membership (`"metrics" in data["details"]`, `"browser_metrics" in data["details"]`) rather than whole-dict equality, so it keeps passing unchanged; `details` is unchanged when no store is configured.
## Security considerations
- The block exposes counts and paths only, never row payloads or results.
## Rollback considerations
- N/A: revert the commit.
## Validation plan
- `uv run pytest tests/mcp_servers/web_search/test_web_search_health.py`: unchanged reference test, pass.
- `uv run python tools/run_validation_gates.py` for the diff: pass.
## Completion criteria
- web-search-mcp `/health` publishes the `"dedup"` block when the dedup store is open, and its `details` is unchanged otherwise; the existing `metrics` and `browser_metrics` keys and `BASE_KEYS` are unchanged.
## Out of Scope
- `scripts/mcp_servers/web_search/metrics.py` (reference, not modified), `make_health_response()` itself (row 09), and the dedup metrics module internals (rows 05-06).
## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the handler change per Procedure/Method/Details | Pending | — | — | |
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
- **Requirement ID**: `REQ-004` (the health payload reports dedup store metrics and capacity status)
- **Source issue**: issues/20261120-115844_mcpdl005_retention-capacity-monitoring.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-120131_mcpdl005_retention-capacity-monitoring.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-144326
- **Related target files**: `scripts/mcp_servers/web_search/web_search_server.py`
