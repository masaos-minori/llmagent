## Goal
Merge the dedup store metrics block into the github-mcp `/health` `details` (REQ-004, the health payload reports dedup store metrics and capacity status).
## Scope
**Release unit**: health exposure
- One change confined to the existing `/health` handler in `scripts/mcp_servers/github/github_server.py`.
## Assumptions
- `dedup_health_details()` (new) is added by the row-09 sibling document in `scripts/mcp_servers/health_response.py`; it reads the dispatcher's `_dedup_store` / `_dedup_config` module globals and returns `{}` — never an exception — when the store is absent or the read fails (REQ-002 degradation path, the default in existing tests).
## Design decisions
- The merge stays inside the handler so `make_health_response()`'s signature, the payload keys, and the status-code logic stay unchanged; the block is the single new `details` key `"dedup"`.
## Alternatives considered
- N/A: the Plan fixes the wiring point in the existing handler; no alternative for a confined one-key merge.
## Implementation
### Target file
`scripts/mcp_servers/github/github_server.py`
### Procedure
- Extend the existing `from mcp_servers.health_response import make_health_response` (line 59) to also import `dedup_health_details`.
- In `health()` (line 173-183): after `details: dict[str, object] = {"service": "github-mcp"}` (line 179) is built and before the `make_health_response(deps, details, security=_security_posture)` call (line 180), add `details.update(dedup_health_details())`.
- No other change in the file.
### Method
- Additive merge of the single new `details` key `"dedup"`, present only when the server's dedup store is open; `deps` and the `security=_security_posture` argument are untouched.
### Details
- The block carries the REQ-004 metrics fields: per-status counts, growth, WAL size, lock wait, lease health, and threshold status.
### Companion test files
- `tests/mcp_servers/github/test_github_server_endpoints.py`
  - Procedure: keep both exact-equality `assert body["details"] == {"service": "github-mcp"}` assertions (line 188 degraded-token test and line 200 healthy-token test) as the no-store case, and add a store-configured assertion that `body["details"]` then contains a `"dedup"` block whose fields match the REQ-004 metrics fields, following the file's existing `client` / `monkeypatch` health-fixture pattern.
  - Validation: `uv run pytest tests/mcp_servers/github/test_github_server_endpoints.py`
## Compatibility considerations
- `tests/mcp_servers/github/test_github_server_endpoints.py` pins the current `details` shape by exact equality at lines 188 and 200; it stays passing with no store configured and is extended for the configured case.
## Security considerations
- The block exposes counts and paths only, never row payloads or results.
## Rollback considerations
- N/A: revert the commit.
## Validation plan
- `uv run pytest tests/mcp_servers/github/test_github_server_endpoints.py`: pass with and without a configured dedup store.
- `uv run python tools/run_validation_gates.py` for the diff: pass.
## Completion criteria
- github-mcp `/health` publishes the `"dedup"` block when the dedup store is open, and its `details` is unchanged otherwise; the `service` key and `BASE_KEYS` are unchanged.
## Out of Scope
- `make_health_response()` itself (row 09) and the metrics module internals (rows 05-06); the other servers' handlers.
## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the handler change per Procedure/Method/Details | Completed | 20261123-223506 | 20261123-223506 | Changed: scripts/mcp_servers/github/github_server.py (the health_response import also imports dedup_health_details, and details.update(dedup_health_details()) is added in health() after the service key is built and before make_health_response). deps and the security argument are untouched. |
| 2 | Extend the companion test's `details` expectation | Completed | 20261123-223506 | 20261123-223506 | Extended tests/mcp_servers/github/test_github_server_endpoints.py with a DEDUP_FIELDS constant. Both exact-equality assertions (the degraded-token test and the healthy-token test) are kept as the no-store case, and those tests now state the precondition by patching the dispatch store and config globals to None because the session's autouse bootstrap fixture configures a store from the isolated config copy. A store-configured test uses the conftest isolated_dedup fixture and asserts details carries the dedup block with the REQ-004 fields and the service key unchanged. Run: 12 passed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261123-230806 | 20261123-230806 | This member Step 3e: ruff format and check pass, run_validation_gates.py fast mode all applicable gates Pass, lint-imports 6 contracts kept, mypy clean across scripts/, bandit unchanged on this file (the pre-existing B105 finding on the untouched not_set line). Validation-plan run of the nine health test files: 248 passed, 1 skipped. Full suite runs once at end of the release unit. End-of-unit run for the health-exposure unit: full suite with coverage 13660 passed 4 skipped, diff-scoped coverage 94 percent, all gates pass. Deviation: the run was executed once for the whole diff. |

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
- **Related target files**: `scripts/mcp_servers/github/github_server.py`, `tests/mcp_servers/github/test_github_server_endpoints.py`