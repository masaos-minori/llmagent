## Goal
Merge the dedup store metrics block into the mdq-mcp `/health` `details`, keeping the row counts mdq already publishes (REQ-004, the health payload reports dedup store metrics and capacity status).
## Scope
**Release unit**: health exposure
- One change confined to the existing `/health` handler in `scripts/mcp_servers/mdq/mdq_server.py`.
## Assumptions
- `dedup_health_details()` (new) is added by the row-09 sibling document in `scripts/mcp_servers/health_response.py`; it reads the dispatcher's `_dedup_store` / `_dedup_config` module globals and returns `{}` — never an exception — when the store is absent or the read fails (REQ-002 degradation path, the default in existing tests).
- mdq's `details` (including the `service` key and the index row counts) is built inside `scripts/mcp_servers/mdq/health_check.py::_collect_dependencies()`, which is not a target row and is not modified.
## Design decisions
- The handler currently delegates wholesale to `check_health()`; it composes the response itself from the already-imported parts so the handler owns `details` and can merge the block, replicating `check_health()`'s degraded/posture branches verbatim so the payload is otherwise byte-identical.
## Alternatives considered
- N/A: editing `scripts/mcp_servers/mdq/health_check.py` would add a second target file; the confined handler composition is the Plan's design.
## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_server.py`
### Procedure
- Add `from mcp_servers.health_response import dedup_health_details, make_health_response` (the module has no `mcp_servers.health_response` import today) and change `from mcp_servers.mdq.health_check import _collect_dependencies, check_health` (line 34) to import `_collect_dependencies, _degraded_response` instead (`check_health` has no other use in the file).
- In `health()` (line 445-449): call `_collect_dependencies()` for `deps` and `details`, add `details.update(dedup_health_details())` before building the response, rebuild the posture with the already-imported `build_mdq_posture()`, and return `_degraded_response(deps, details, posture)` when `deps` is non-empty, else `make_health_response(deps, details, security=posture)` — the same branch order `check_health()` uses.
- No other change in the file.
### Method
- Additive merge of the single new `details` key `"dedup"`, present only when the server's dedup store is open; existing mdq `details` content (`service`, `database`, `allowed_dirs_count`, `deny_all`, the index row counts) stays as built by `_collect_dependencies()`.
### Details
- The block carries the REQ-004 metrics fields: per-status counts, growth, WAL size, lock wait, lease health, and threshold status.
## Compatibility considerations
- `tests/mcp_servers/mdq/test_mdq_health_endpoint.py` asserts mdq `details` by key membership (`"database"`, `"document_count"`, ...) rather than equality, so it keeps passing unchanged; `details` is unchanged when no store is configured.
## Security considerations
- The block exposes counts and paths only, never row payloads or results.
## Rollback considerations
- N/A: revert the commit.
## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_health_endpoint.py`: unchanged reference test, pass.
- `uv run python tools/run_validation_gates.py` for the diff: pass.
## Completion criteria
- mdq-mcp `/health` publishes the `"dedup"` block when the dedup store is open, and its payload is otherwise identical to `check_health()`'s today, including the 503 degraded branch.
## Out of Scope
- `scripts/mcp_servers/mdq/health_check.py` (reference only), `make_health_response()` itself (row 09), and the metrics module internals (rows 05-06).
## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the handler change per Procedure/Method/Details | Completed | 20261123-223506 | 20261123-223506 | Changed: scripts/mcp_servers/mdq/mdq_server.py (added the health_response import, changed the health_check import from check_health to _degraded_response since check_health has no other use in the file, and health() now composes the response itself from _collect_dependencies plus the already-imported build_mdq_posture and _degraded_response so it owns details and can merge the block; the degraded branch is checked before the healthy branch, in the same order check_health() uses). mdq details content stays as _collect_dependencies() builds it. The reference test test_mdq_health_endpoint.py is unchanged and passes in the combined run of the per-server health test files. |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261123-230806 | 20261123-230806 | This member Step 3e: ruff format and check pass, run_validation_gates.py fast mode all applicable gates Pass, lint-imports 6 contracts kept, mypy clean across scripts/, bandit clean on this file. Validation-plan run of the nine health test files: 248 passed, 1 skipped. Full suite runs once at end of the release unit. End-of-unit run for the health-exposure unit: full suite with coverage 13660 passed 4 skipped, diff-scoped coverage 94 percent, all gates pass. Deviation: the run was executed once for the whole diff. |

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
- **Related target files**: `scripts/mcp_servers/mdq/mdq_server.py`