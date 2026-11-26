## Goal
- Report GitHub token loss as the degraded optional capability `github.api` while the required capability `github.operations` stays `ok`, in `scripts/mcp_servers/github/github_server.py` (REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the `/health` endpoint capability block in this file, plus the test companion.
- Out of scope: the producer helper (seq 15); the catalog declaration (seq 17).

## Assumptions
- Verified in Step 3a: the health endpoint (`github_server.py:181-196`) reports token loss only as a `dependencies` entry (`github_token: not_set`, `:185-186`); all GitHub tools are `config_dependent: True` gated on `_GITHUB_TOKEN` (`:135-139`).
- GitHub is a subprocess server and therefore always `required=true` (`mcp_config.py:208-212`), so token loss must be modelled as an optional capability, not server loss (Plan Assumption).
- Capability identifiers follow `docs/22_mcp/mcp_08_tool_capability_naming_convention.md`: `github.api` next to the existing required `github.operations`.

## Design decisions
- `github.operations` is proven `ok` when the server itself is up (the required capability is the server's own operation capability); `github.api` is `degraded` when `_GITHUB_TOKEN` is unset.

## Alternatives considered
- Report token loss as required-capability loss (rejected: it would block startup for an optional dependency, contradicting REQ-006).

## Implementation
### Target file
`scripts/mcp_servers/github/github_server.py`

### Procedure
1. In the `/health` endpoint, build the capability block: `github.operations` = `ok`, `github.api` = `ok` when the token is set and `degraded` (reason code for missing configuration) when it is not.
2. Pass the block through `make_health_response()` (seq 15); keep the existing `dependencies` entry unchanged for compatibility.

### Method
- Use the contract vocabulary constants (seq 01); the reason code for token loss must be one of the documented codes in `mcp_06_10` (seq 34).

### Details
- Tool availability gating (`_github_tool_availability`) stays as is; the capability state is the report-side signal.

### Companion test files
- `tests/mcp_servers/github/test_github_health_posture.py`
  - Procedure: with `GITHUB_TOKEN` unset, assert `github.api` degraded and `github.operations` ok; with the token set, both `ok` (T-06).
  - Validation: `uv run pytest tests/mcp_servers/github/test_github_health_posture.py`.

## Compatibility considerations
- Additive block; existing `dependencies` consumers are unaffected.

## Security considerations
- The health body names the capability state, never the token value.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/github/test_github_health_posture.py`; `uv run ruff format` and `uv run ruff check`; `uv run mypy`; then the sequence in `rules/toolchain.md`.

## Completion criteria
- Token loss reports `github.api` degraded without blocking readiness; the companion test passes.

## Out of Scope
- The producer helper and the catalog.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the capability block | Pending | — | — | |
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
- **Requirement ID**: `REQ-006` (GitHub token loss as degraded optional capability `github.api`)
- **Source issue**: issues/20261119-145306_cliplc008_mcp-health-capability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-111451_cliplc008_mcp-health-capability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-135614
- **Related target files**: `scripts/mcp_servers/github/github_server.py`, `tests/mcp_servers/github/test_github_health_posture.py`
