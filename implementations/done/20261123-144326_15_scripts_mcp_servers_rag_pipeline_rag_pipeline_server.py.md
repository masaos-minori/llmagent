## Goal
Merge the dedup store metrics block into the rag-pipeline-mcp `/health` `details` (REQ-004, the health payload reports dedup store metrics and capacity status).
## Scope
**Release unit**: health exposure
- One change confined to the existing `/health` handler in `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`.
## Assumptions
- `dedup_health_details()` (new) is added by the row-09 sibling document in `scripts/mcp_servers/health_response.py`; it reads the dispatcher's `_dedup_store` / `_dedup_config` module globals and returns `{}` — never an exception — when the store is absent or the read fails (REQ-002 degradation path, the default in existing tests).
## Design decisions
- The merge stays inside the handler so `make_health_response()`'s signature, the payload keys, and the status-code logic stay unchanged; the block is the single new `details` key `"dedup"`.
## Alternatives considered
- N/A: the Plan fixes the wiring point in the existing handler; no alternative for a confined one-key merge.
## Implementation
### Target file
`scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`
### Procedure
- Extend the existing `from mcp_servers.health_response import make_health_response` (line 30) to also import `dedup_health_details`.
- In `health()` (line 202-210): after `details: dict[str, object] = {"service": "rag-pipeline-mcp"}` (line 206) is built and before the `make_health_response(deps, details, security=_security_posture)` call (line 207), add `details.update(dedup_health_details())`.
- No other change in the file.
### Method
- Additive merge of the single new `details` key `"dedup"`, present only when the server's dedup store is open; `deps = await _check_health_deps()` and the `security=_security_posture` argument are untouched.
### Details
- The block carries the REQ-004 metrics fields: per-status counts, growth, WAL size, lock wait, lease health, and threshold status.
## Compatibility considerations
- `tests/mcp_servers/rag_pipeline/test_rag_pipeline_health_posture.py` asserts the health payload keys and the `security` block by subscript/key membership rather than whole-`details` equality, so it keeps passing unchanged; `details` is unchanged when no store is configured.
## Security considerations
- The block exposes counts and paths only, never row payloads or results.
## Rollback considerations
- N/A: revert the commit.
## Validation plan
- `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_health_posture.py`: unchanged reference test, pass.
- `uv run python tools/run_validation_gates.py` for the diff: pass.
## Completion criteria
- rag-pipeline-mcp `/health` publishes the `"dedup"` block when the dedup store is open, and its `details` is unchanged otherwise; the `service` key and `BASE_KEYS` are unchanged.
## Out of Scope
- `make_health_response()` itself (row 09), the metrics module internals (rows 05-06), and the rag-pipeline posture test, which is a reference row.
## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the handler change per Procedure/Method/Details | Completed | 20261123-223506 | 20261123-223506 | Changed: scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py (the health_response import also imports dedup_health_details, and details.update(dedup_health_details()) is added in health() after the service key is built and before make_health_response). deps = await _check_health_deps() and the security argument are untouched. The reference test test_rag_pipeline_health_posture.py is unchanged and passes in the combined run of the per-server health test files. |
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
- **Related target files**: `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`