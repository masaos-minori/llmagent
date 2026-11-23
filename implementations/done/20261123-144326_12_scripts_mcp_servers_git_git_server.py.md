## Goal
Merge the dedup store metrics block into the git-mcp `/health` `details` (REQ-004, the health payload reports dedup store metrics and capacity status).
## Scope
**Release unit**: health exposure
- One change confined to the existing `/health` handler in `scripts/mcp_servers/git/git_server.py`.
## Assumptions
- `dedup_health_details()` (new) is added by the row-09 sibling document in `scripts/mcp_servers/health_response.py`; it reads the dispatcher's `_dedup_store` / `_dedup_config` module globals and returns `{}` — never an exception — when the store is absent or the read fails (REQ-002 degradation path, the default in existing tests).
## Design decisions
- The merge stays inside the handler so `make_health_response()`'s signature, the payload keys, and the status-code logic stay unchanged; the block is the single new `details` key `"dedup"`.
## Alternatives considered
- N/A: the Plan fixes the wiring point in the existing handler; no alternative for a confined one-key merge.
## Implementation
### Target file
`scripts/mcp_servers/git/git_server.py`
### Procedure
- Extend the existing `from mcp_servers.health_response import make_health_response` (line 52) to also import `dedup_health_details`.
- In `health()` (line 373-389): after `details: dict[str, object] = {"service": "git-mcp", "audit_failure_count": _audit_failure_count}` (line 382-385) is built and before the `make_health_response(deps, details, security=_security_posture)` call (line 386), add `details.update(dedup_health_details())`.
- No other change in the file.
### Method
- Additive merge of the single new `details` key `"dedup"`, present only when the server's dedup store is open; `deps`, the existing `audit_failure_count` key, and the `security=_security_posture` argument are untouched.
### Details
- The block carries the REQ-004 metrics fields: per-status counts, growth, WAL size, lock wait, lease health, and threshold status.
## Compatibility considerations
- The per-server git health tests assert the payload by key membership, not whole-dict equality — `tests/mcp_servers/git/test_git_health_posture.py` reads `body` keys by subscript and `tests/mcp_servers/git/test_git_security_compliance.py` asserts `details.get("audit_failure_count")` — so both keep passing unchanged; `details` is unchanged when no store is configured.
## Security considerations
- The block exposes counts and paths only, never row payloads or results.
## Rollback considerations
- N/A: revert the commit.
## Validation plan
- `uv run pytest tests/mcp_servers/git/test_git_health_posture.py tests/mcp_servers/git/test_git_security_compliance.py`: unchanged reference tests, pass.
- `uv run python tools/run_validation_gates.py` for the diff: pass.
## Completion criteria
- git-mcp `/health` publishes the `"dedup"` block when the dedup store is open, and its `details` is unchanged otherwise; the reference tests keep passing without edits.
## Out of Scope
- `make_health_response()` itself (row 09), the metrics module internals (rows 05-06), and the git reference tests, which are reference rows.
## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the handler change per Procedure/Method/Details | Completed | 20261123-223506 | 20261123-223506 | Changed: scripts/mcp_servers/git/git_server.py (the health_response import also imports dedup_health_details, and details.update(dedup_health_details()) is added in health() after the service and audit_failure_count keys are built and before make_health_response). The existing audit_failure_count key is untouched. |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261123-230806 | 20261123-230806 | This member Step 3e: ruff format and check pass, run_validation_gates.py fast mode all applicable gates Pass, lint-imports 6 contracts kept, mypy clean across scripts/, bandit unchanged on this file (the pre-existing B101 finding on the untouched line 366). The reference tests are unchanged and pass: tests/mcp_servers/git/test_git_health_posture.py and tests/mcp_servers/git/test_git_security_compliance.py are green in the combined run of the per-server health test files. Full suite runs once at end of the release unit. End-of-unit run for the health-exposure unit: full suite with coverage 13660 passed 4 skipped, diff-scoped coverage 94 percent, all gates pass. Deviation: the run was executed once for the whole diff. |

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
- **Related target files**: `scripts/mcp_servers/git/git_server.py`