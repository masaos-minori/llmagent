## Goal
- Reorder discovery in `mcp_tool_discovery.py` so the catalog is loaded before registry construction, prove the required capability from the health report, and pass degraded optional capabilities to the registry (REQ-005, REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `discover_all()`, `_check_required_tools()`, and the capability hand-off in this file, plus the test companion.
- Out of scope: the registry builder internals (seq 11); the classification helper (seq 06); the catalog content itself (seq 17).

## Assumptions
- Verified in Step 3a: `discover_all()` builds the registry at `:107` before loading the catalog at `:112`; `_check_required_tools()` (`:260`) is inert because no tool declares `capabilities` (`:280` guard, `docs/22_mcp/mcp_08...md:86`); the missing-catalog path is already FATAL (`:113-123`).
- Required-versus-optional rule (D-6): required only when the capability equals the catalog `required_capability` of a `required=true` server; the GitHub server is always `required=true` (`mcp_config.py:208-212`).

## Design decisions
- D-9: load the catalog first, then build the registry with the degraded-capability map so dependent tools are excluded at construction (one publication, no post-construction mutation).
- The health report (from the gate, seq 06) is the proof of the required capability; the catalog supplies the identifier.

## Alternatives considered
- Keep the check inert until servers declare capabilities (rejected by REQ-005: required loss must block startup).

## Implementation
### Target file
`scripts/agent/services/mcp_tool_discovery.py`

### Procedure
1. Move `_load_tool_catalog()` before `_dedupe_and_build()`; keep the missing-catalog FATAL message.
2. Replace the inert `capabilities` guard in `_check_required_tools()` with the report-based proof: for each `required=true` server, the parsed health report must prove its catalog `required_capability` `ok` (legacy bodies fall back to `ready`, D-6); otherwise FATAL.
3. Collect the degraded/unavailable optional capabilities per server from the report and pass the map to `_dedupe_and_build()` → the registry builder (seq 11).

### Method
- The gate map (`self._posture_gates`) already carries the parsed report (seq 06); read the capability states from it rather than re-parsing.

### Details
- A tool's capability dependency is the catalog `capabilities` of its owning server unless the discovery entry declares `capabilities` (Plan Assumption); the exclusion itself happens in the registry (seq 13).

### Companion test files
- `tests/agent/services/test_mcp_tool_discovery_posture_gate.py`
  - Procedure: cover the gate-plus-capability interaction — required capability degraded/unavailable produces FATAL, legacy body falls back to `ready`, optional degraded passes the map through (T-05).
  - Validation: `uv run pytest tests/agent/services/test_mcp_tool_discovery_posture_gate.py`.

## Compatibility considerations
- The reorder changes the FATAL path order only; the existing missing-catalog message and status stay (Plan Risk mitigation).

## Security considerations
- N/A: no credential handling in this file.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/services/test_mcp_tool_discovery.py tests/agent/services/test_mcp_tool_discovery_posture_gate.py`; `uv run ruff format` and `uv run ruff check`; `uv run mypy`; `wc -c scripts/agent/services/mcp_tool_discovery.py` below 24576 (current size 14858 B); then the sequence in `rules/toolchain.md`.

## Completion criteria
- Catalog loads before registry construction; required capability loss produces FATAL; degraded optional capabilities reach the registry; tests pass.

## Out of Scope
- The registry builder, the catalog content, and the standalone discovery test file (seq 26).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the reorder, capability proof, and map hand-off | Pending | — | — | |
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
- **Requirement ID**: `REQ-005` (required capability proof blocks startup), `REQ-006` (degraded optional capabilities reach the registry)
- **Source issue**: issues/20261119-145306_cliplc008_mcp-health-capability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-111451_cliplc008_mcp-health-capability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-135614
- **Related target files**: `scripts/agent/services/mcp_tool_discovery.py`, `tests/agent/services/test_mcp_tool_discovery_posture_gate.py`
