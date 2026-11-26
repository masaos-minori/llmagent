## Goal
- Make the `/mcp status` probe in `mcp_status.py` use the per-server effective timeout at the request and display the parsed health report fields (REQ-001, REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the probe call path and the status display in this file, plus the test companion.
- Out of scope: the probe function itself (seq 06); the tool-row rendering in `cmd_mcp.py` (seq 14).

## Assumptions
- Verified in Step 3a: `mcp_status.py:104` already builds the client with `get_effective_health_timeout(cfg)`, but the actual request goes through `_probe_mcp_health_detail` (`mcp_health.py:52`), which overrides it with 5.0 — fixed in seq 06; this row passes the effective timeout into the probe path and renders report fields.
- The companion test's `health_timeout=0` case (`test_agent_mcp_status.py:145-151`) asserts the removed zero-means-unlimited behavior and becomes a rejection case after seq 02.

## Design decisions
- Display only fields the contract guarantees: `health_schema_version`, `liveness`, `ready`, `degraded_reasons`, capability states; no inference from status text (REQ-007).

## Alternatives considered
- N/A: confined to the probe call and display, no public-contract change.

## Implementation
### Target file
`scripts/agent/services/mcp_status.py`

### Procedure
1. Pass `get_effective_health_timeout(cfg)` into the probe call so the request uses the per-server timeout (after seq 06 changes the probe signature).
2. Render the parsed report fields in the status output where the health body is shown.

### Method
- Parse the body through `shared.mcp_health_contract.parse_health_body()` (seq 01) rather than the legacy `interpret_health_body` path for the new fields.

### Details
- Tool rows in this view come from `RuntimeToolRegistry.diagnostics()` explicit fields (seq 13); this file only displays them.

### Companion test files
- `tests/agent/services/test_agent_mcp_status.py`
  - Procedure: change the `health_timeout=0` case to assert rejection at load; assert the probe receives the per-server effective timeout (T-01).
  - Validation: `uv run pytest tests/agent/services/test_agent_mcp_status.py`.

## Compatibility considerations
- Display-only additions; existing status consumers are unaffected.

## Security considerations
- N/A: no token handling change.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/services/test_agent_mcp_status.py`; `uv run ruff format` and `uv run ruff check`; `uv run mypy`; then the sequence in `rules/toolchain.md`.

## Completion criteria
- The request uses the effective timeout; report fields appear; the zero-timeout test asserts rejection; tests pass.

## Out of Scope
- The probe signature change (seq 06) and the diagnostics rendering (seq 14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the probe-timeout pass-through and display | Pending | — | — | |
| 2 | Update the companion tests | Pending | — | — | |
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
- **Requirement ID**: `REQ-001` (per-server timeout at `/mcp status`), `REQ-007` (display from explicit metadata)
- **Source issue**: issues/20261119-145306_cliplc008_mcp-health-capability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-111451_cliplc008_mcp-health-capability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-135614
- **Related target files**: `scripts/agent/services/mcp_status.py`, `tests/agent/services/test_agent_mcp_status.py`
