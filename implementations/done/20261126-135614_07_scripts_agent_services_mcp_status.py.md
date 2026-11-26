## Goal
- Make the `/mcp status` probe in `mcp_status.py` use the per-server effective timeout at the request and display the parsed health report fields (REQ-001, REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the probe call path and the status display in this file, plus the test companion.
- Out of scope: the probe function itself (seq 06); the tool-row rendering in `cmd_mcp.py` (seq 14).

## Assumptions
- Verified in Step 3a: `mcp_status.py:104` already builds the client with `get_effective_health_timeout(cfg)`, but the actual request goes through `_probe_mcp_health_detail` (`mcp_health.py:52`), which overrides it with 5.0 — fixed in seq 06; this row passes the effective timeout into the probe path and renders report fields.
- The companion test's `health_timeout=0` case (`test_agent_mcp_status.py:145-151`) asserts the removed zero-means-unlimited behavior and becomes a rejection case after seq 02.
- Corrected in Step 3b (owner decision, 2026-11-26): the report-field display is seq 14's scope. This
  procedure does not add fields to `McpProbeResult` — `scripts/agent/services/models.py` is outside the
  Plan's frozen target table, and the display chain reads the capability state from
  `RuntimeToolRegistry.diagnostics()` (seq 13). The report fields this file already carries
  (`self_reported_status`, `dependency_summary`, `details_summary`, `parse_failure_reason`) come from
  the contract parse added by seq 08, so no display change is made here.
- Corrected in Step 3b: the effective timeout is passed as an optional keyword (`timeout_sec`) through
  the probe call path, so the existing direct `_get_http_status()` test call sites keep working without
  a value and the probe falls back to the client's own timeout.

## Design decisions
- Display only fields the contract guarantees: `health_schema_version`, `liveness`, `ready`, `degraded_reasons`, capability states; no inference from status text (REQ-007).

## Alternatives considered
- N/A: confined to the probe call and display, no public-contract change.

## Implementation
### Target file
`scripts/agent/services/mcp_status.py`

### Procedure
1. Pass `get_effective_health_timeout(cfg)` into the probe call as the optional `timeout_sec` keyword,
   threaded through `_probe_single_server_with_interpretation()` and both `_get_http_status*()` helpers,
   so the request uses the per-server timeout (seq 06 made the probe accept it).
2. No display change in this file: the report-field rendering belongs to seq 14, which reads it from
   `diagnostics()` (seq 13). Recorded as a Step 3b correction above.

### Method
- No new parse path in this file: `interpret_health_body()` (seq 08) is the contract-based path that
  produces the report fields already carried by `McpProbeResult`.

### Details
- Tool rows in this view come from `RuntimeToolRegistry.diagnostics()` explicit fields (seq 13); this file only displays them.

### Companion test files
- `tests/agent/services/test_agent_mcp_status.py`
  - Procedure: the zero-timeout class became `TestProbeAllHealthTimeout` with two cases —
    `health_timeout=0` rejected at config load, and the per-server effective value reaching the
    `/mcp status` request site (both the client construction and the `get()` call). The existing
    auth-header assertion is kept (T-01, REQ-003).
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
- The request uses the effective timeout; the zero-timeout test asserts rejection at load; tests pass.
  Report-field rendering is verified in seq 14, not here.

## Out of Scope
- The probe signature change (seq 06) and the diagnostics rendering (seq 14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the probe-timeout pass-through and display | Completed | 20261126-174944 | 20261126-174944 | get_effective_health_timeout(cfg) is passed as the optional timeout_sec keyword through _probe_single_server_with_interpretation() and both _get_http_status*() helpers. Display: no change in this file; report-field rendering delegated to seq 14 (owner decision, 2026-11-26), which reads it from diagnostics() (seq 13). File size 15095 B < 24576. |
| 2 | Update the companion tests | Completed | 20261126-174944 | 20261126-174944 | tests/agent/services/test_agent_mcp_status.py: the zero-timeout class replaced by TestProbeAllHealthTimeout with two cases — health_timeout=0 rejected at load, and the effective value reaching both the client construction and the get() call; the auth-header assertion kept. 24 tests passed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-174944 | 20261126-174944 | ruff format/check pass; mypy clean on the target file; lint-imports 6 contracts kept; bandit pass; check_mock_patch_targets, check_module_size, check_docstrings pass. Full suite pending at end of batch. |

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