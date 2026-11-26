## Goal
- Make `health_timeout` strictly greater than 0 in `mcp_config.py`, remove the zero-means-unlimited behavior, and document the single-token health authentication model on `auth_headers()` (REQ-001 timeout rule, REQ-003 one auth path).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: validation rule, resolver return type, one docstring note, plus the test companion.
- Out of scope: applying the timeout at the five request sites (seq 03-07).

## Assumptions
- Verified in Step 3a: `health_timeout` is at `mcp_config.py:122`; validation at `:220-223` currently accepts 0 (`must be >= 0`); `get_effective_health_timeout()` (`:281-298`) returns `None` for 0. No `config/*.toml` sets the key, so rejecting 0 breaks no production configuration.
- D-1: no new config key; `auth_token` stays the single credential already covered by `register_secret`.

## Design decisions
- D-3: zero is rejected rather than kept as unlimited; the resolver always returns a positive float, so no consumer needs a `None` branch.
- Direct construction must be rejected too, not only config load: the resolver raises on `<= 0` as it already raises on negatives.

## Alternatives considered
- Keep zero as unlimited and cap by the deadline (rejected by D-3: contradicts the deadline rule).

## Implementation
### Target file
`scripts/shared/mcp_config.py`

### Procedure
1. Change the validation at `:220-223` to reject `health_timeout <= 0`, with the error message naming the field and the accepted range.
2. Change `get_effective_health_timeout()` to return `float` (drop the `None`/zero branch); the default when unset stays 5.0.
3. Add one sentence to `auth_headers()` stating it is the only health-auth header path and `auth_token` is the health credential (D-1).

### Method
- Keep the existing default-5.0 fallback for unset values; only the explicit-zero case changes behavior.

### Details
- Consumers `mcp_status.py` and `mcp_tool_discovery_fetch.py` already call the resolver; the narrowed return type removes their `None` handling without editing those files (they are separate rows).

### Companion test files
- `tests/shared/test_mcp_config_validation.py`
  - Procedure: assert 0 and a negative `health_timeout` are rejected at load and at direct construction; assert the effective timeout is a positive float for unset and positive values (T-01).
  - Validation: `uv run pytest tests/shared/test_mcp_config_validation.py tests/shared/test_mcp_config.py`.

## Compatibility considerations
- No repository config sets `health_timeout`; tests asserting the zero behavior change (seq 24). The resolver signature narrows from `float | None` to `float`.

## Security considerations
- `auth_token` remains a registered secret; no new secret surface (D-1).

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/shared/test_mcp_config_validation.py tests/shared/test_mcp_config.py`; `uv run ruff format` and `uv run ruff check`; `uv run mypy`; `wc -c scripts/shared/mcp_config.py` below 24576 (current size 19605 B); then the sequence in `rules/toolchain.md`.

## Completion criteria
- 0 and negatives are rejected on both paths; the resolver returns a positive float; the auth docstring states the single model; all validation commands pass.

## Out of Scope
- Request-site timeout application, docs updates (seq 36).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the validation, resolver, and docstring change | Completed | 20261126-154613 | 20261126-154613 | Changed: scripts/shared/mcp_config.py (validation rejects <=0, resolver returns float, auth_headers docstring states the single auth path). File size 19677 B < 24576. |
| 2 | Update the companion tests | Completed | 20261126-154613 | 20261126-154613 | tests/shared/test_mcp_config_validation.py: zero-rejection test replaced the zero-is-valid test; added positive-float invariant test (T-01). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-154613 | 20261126-154613 | ruff/mypy pass; targeted tests 138 passed. Full suite pending at end of batch. Docs: N/A, docs update is seq 36's target row. |

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
- **Requirement ID**: `REQ-001` (positive per-server health timeout), `REQ-003` (single documented auth model)
- **Source issue**: issues/20261119-145306_cliplc008_mcp-health-capability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-111451_cliplc008_mcp-health-capability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-135614
- **Related target files**: `scripts/shared/mcp_config.py`, `tests/shared/test_mcp_config_validation.py`