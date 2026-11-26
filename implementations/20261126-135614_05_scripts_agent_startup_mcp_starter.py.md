## Goal
- Make the post-startup verification in `startup_mcp_starter.py` use the per-server effective timeout and report-based readiness instead of `liveness`-only acceptance (REQ-001, REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the two health-request sites in this file plus the test companion.
- Out of scope: the poll path (seq 03); the contract module (seq 01).

## Assumptions
- Verified in Step 3a: `timeout=5.0` hard-coded at `startup_mcp_starter.py:149` and `:209`; headers already come from `cfg.auth_headers()` (no second path here); a non-200 body with `liveness == true` is accepted as ready (`:202`).
- Readiness rule is the same as seq 03: required capability proven `ok`, or legacy body with `ready=true` (D-6).

## Design decisions
- Reuse the readiness helper introduced by seq 03 rather than duplicating the predicate here.

## Alternatives considered
- N/A: confined to two call sites, no public-contract change.

## Implementation
### Target file
`scripts/agent/startup_mcp_starter.py`

### Procedure
1. Replace the hard-coded `timeout=5.0` at both health requests with `get_effective_health_timeout(cfg)`.
2. Replace the `liveness`-only acceptance with the report-based readiness check from seq 03.

### Method
- Parse the body through `shared.mcp_health_contract.parse_health_body()` and evaluate the server's `required_capability` from `config/tool_catalog.toml` (catalog load stays in seq 09; here only the readiness decision changes).

### Details
- The startup failure message should name the capability that was not proven when a 503 body fails readiness.

### Companion test files
- `tests/agent/test_startup_mcp_starter.py`
  - Procedure: replace the `is_degraded_but_live` patch (`:250`) with report-based cases — liveness-only 503 fails, required-capability-ok 503 passes, legacy body falls back to `ready`; assert the effective timeout reaches both requests (T-01, T-05).
  - Validation: `uv run pytest tests/agent/test_startup_mcp_starter.py`.

## Compatibility considerations
- The replaced predicate is pinned by the companion test only; no other consumer.

## Security considerations
- Auth path unchanged (`auth_headers()` already used).

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_startup_mcp_starter.py`; `uv run ruff format` and `uv run ruff check`; `uv run mypy`; then the sequence in `rules/toolchain.md`.

## Completion criteria
- Both requests use the effective timeout; a liveness-only 503 no longer passes post-startup verification; tests pass.

## Out of Scope
- The poll path and the contract module.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the timeout and readiness changes | Pending | — | — | |
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
- **Requirement ID**: `REQ-001` (per-server timeout at post-startup verification), `REQ-005` (report-based readiness)
- **Source issue**: issues/20261119-145306_cliplc008_mcp-health-capability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-111451_cliplc008_mcp-health-capability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-135614
- **Related target files**: `scripts/agent/startup_mcp_starter.py`, `tests/agent/test_startup_mcp_starter.py`
