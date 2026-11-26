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
- Resolve `required_capability` through the shared leaf reader `scripts/shared/tool_catalog.py`
  (`load_tool_catalog()` + `required_capability_for()`), the same reader seq 04 and seq 09 use, so the
  catalog path and entry shape are defined once. A missing catalog resolves to `None` here with a
  warning, which keeps the legacy `ready` fallback (D-6); the fail-closed FATAL stays at discovery.

## Alternatives considered
- N/A: confined to two call sites, no public-contract change.

## Implementation
### Target file
`scripts/agent/startup_mcp_starter.py`

### Procedure
1. Replace the hard-coded `timeout=5.0` at both health requests with `get_effective_health_timeout(cfg)`.
2. Replace the `liveness`-only acceptance with the report-based readiness check from seq 03.

### Method
- Parse the body through `shared.mcp_health_contract.parse_health_body()` (via `HealthChecker.parse_report`)
  and evaluate the server's `required_capability` through the shared catalog reader. Corrected in Step 3b:
  the reader is `scripts/shared/tool_catalog.py`, shared with seq 04 and seq 09, so this file does not read
  the catalog itself.
- Both call sites share one private helper, `_readiness_failure(server_key, resp)`, which returns the
  failure reason or None; `_verify_single_health` and the `verify_health` loop raise `RuntimeError(reason)`.

### Details
- The startup failure message should name the capability that was not proven when a 503 body fails readiness.
- Corrected in Step 3b: the status code is no longer the proof, so the companion test's 200 fixture body
  must carry `ready: true` (`_auth_handler`), and the capability-ok case needs a catalog entry for the test
  server key, which has none and would otherwise take the legacy fallback.

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
| 1 | Implement the timeout and readiness changes | Completed | 20261126-171605 | 20261126-171605 | Changed: both health requests use get_effective_health_timeout(cfg); the liveness-only acceptance is replaced by _readiness_failure() (parse_report + is_ready) and _resolve_required_capability() through the shared reader scripts/shared/tool_catalog.py. File size 11671 B < 24576. |
| 2 | Update the companion tests | Completed | 20261126-171605 | 20261126-171605 | tests/agent/test_startup_mcp_starter.py: the is_degraded_but_live patch replaced by report-based cases (liveness-only 503 fails, required-capability-ok 503 passes with a catalog entry, legacy body falls back to ready), plus the T-01 test that the effective timeout reaches both the post-startup and the retry probe and that the header comes from auth_headers(). 20 tests passed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-171605 | 20261126-171605 | ruff format/check, mypy (repo-wide: no issues in 622 files), lint-imports (6 contracts kept), bandit pass. Targeted tests 20 passed. Full suite pending at end of batch. Docs: N/A, docs update is seq 33/37's target row. |

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