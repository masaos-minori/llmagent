## Goal
- Emit `health_schema_version`, `degraded_reasons`, and `capabilities` additively from `make_health_response()` in `scripts/mcp_servers/health_response.py`, the producer side of the shared contract (REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the response payload construction in this file, plus the test companion.
- Out of scope: the contract module (seq 01); the GitHub capability values (seq 16).

## Assumptions
- Verified in Step 3a: `make_health_response()` (`health_response.py:31-65`) emits `status`, `ready`, `liveness`, `restart_recommended`, `operator_action_required`, `dependencies`, `details`, `security`; no capability or reason field exists.
- The new keys are additive only — no existing key is removed (REQ-004); servers other than GitHub keep the legacy body path through the contract's legacy branch (D-6).

## Design decisions
- The producer builds the new fields through the contract module (seq 01) so the emitted shape and the parsed shape cannot drift.

## Alternatives considered
- N/A: additive payload change, no signature change beyond optional parameters.

## Implementation
### Target file
`scripts/mcp_servers/health_response.py`

### Procedure
1. Add optional parameters for the capability map and degraded reason codes to `make_health_response()` (default empty, so existing callers are unchanged).
2. Emit `health_schema_version` (1), `degraded_reasons`, and `capabilities` in the payload while keeping every existing key.

### Method
- Use the contract's vocabulary constants for the states and codes; do not hardcode strings here.

### Details
- A server that passes no capabilities emits an empty/absent block, which the Agent reads as a legacy body (D-6).

### Companion test files
- `tests/mcp_servers/test_health_response.py`
  - Procedure: assert the new fields are emitted, every previous key stays, and a no-capability call keeps the legacy shape (T-04).
  - Validation: `uv run pytest tests/mcp_servers/test_health_response.py`.

## Compatibility considerations
- Additive keys only; existing consumers of the health body are unaffected (Plan Risk mitigation: one deploy of both sides).

## Security considerations
- N/A: no secrets in the health body.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/test_health_response.py tests/mcp_servers/test_tool_schema.py`; `uv run ruff format` and `uv run ruff check`; `uv run mypy`; then the sequence in `rules/toolchain.md`.

## Completion criteria
- The three new keys appear when supplied, all old keys remain, and the producer test passes.

## Out of Scope
- The contract module and the GitHub capability reporting.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the additive payload fields | Pending | — | — | |
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
- **Requirement ID**: `REQ-004` (producer side of the shared health contract)
- **Source issue**: issues/20261119-145306_cliplc008_mcp-health-capability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-111451_cliplc008_mcp-health-capability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-135614
- **Related target files**: `scripts/mcp_servers/health_response.py`, `tests/mcp_servers/test_health_response.py`
