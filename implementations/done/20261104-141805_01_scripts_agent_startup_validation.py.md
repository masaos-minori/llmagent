## Goal
- Exclude disabled MCP servers from the `missing_auth` computation of the "MCP authentication check" in `StartupValidationPipeline.check_services`, so a disabled server with an empty `auth_token` no longer aborts startup while an enabled server with an empty token stays a fatal `mcp_auth` outcome (`REQ-001`: a configuration whose only token-less server is disabled passes; `REQ-002`: enabled offenders stay fatal and are the only ones named).

## Scope
**Release unit**: mcp-auth-filter

- One list comprehension in `scripts/agent/startup_validation.py`. The source name `mcp_auth`, the message format, and the remediation text are not changed.

## Assumptions
- `McpServerConfig.is_disabled` is a property equal to `startup_mode == StartupMode.NONE` (checked in Step 3a against `scripts/shared/mcp_config.py`), and `_validate_auth_token` accepts an empty token for a disabled server, so a disabled server with an empty token is valid configuration.
- The current code is `missing_auth = [key for key, srv in ctx.cfg.mcp.mcp_servers.items() if not srv.auth_token]` with no `is_disabled` filter (checked in Step 3a).
- Token-less `MagicMock` servers in the existing tests have a truthy `is_disabled`, so the filter would exempt them; the sibling procedures for `tests/agent/test_startup_severity_classification.py` and `tests/agent/test_startup.py` (later `seq`, same release unit) set `is_disabled=False` on them.
- The new tests of the sibling procedure for `tests/agent/test_startup_validation.py` fail on the pre-change code; the executor SHOULD run that procedure first (Plan Phase 1) to record the failing state.
- Observation, non-blocking `Needs confirmation`: the remediation text still says "for every MCP server" although disabled servers are now exempt. It stays unchanged because `REQ-002` keeps the remediation wording and `tests/agent/test_startup.py` asserts the exact text.
- Step 2 start conditions held: the Plan is not gated and has no blocking Unknown; the overlap with the Plan for configuration-only validation (it moves this check later, after this change) is a sequencing dependency, recorded in the Plan.

## Design decisions
- Filter inside the existing comprehension with `not srv.is_disabled and not srv.auth_token`; no second pass and no new function, so the radon grade of `check_services` (already D) does not worsen by more than the one boolean condition.
- Add a one-line WHY comment, because the exemption follows from the configuration contract and is not obvious from the code.

## Alternatives considered
- A separate pre-pass over the servers, or removing the check: rejected by the Plan (a second code path for no gain; removal is out of scope).

## Implementation
### Target file
`scripts/agent/startup_validation.py`

### Procedure
In `StartupValidationPipeline.check_services`, under the comment `# 1b. MCP authentication check`, replace the `missing_auth` comprehension.

### Method
Before:

```python
        missing_auth = [
            key for key, srv in ctx.cfg.mcp.mcp_servers.items() if not srv.auth_token
        ]
```

After:

```python
        # A disabled server needs no credential; its empty token is valid config.
        missing_auth = [
            key
            for key, srv in ctx.cfg.mcp.mcp_servers.items()
            if not srv.is_disabled and not srv.auth_token
        ]
```

### Details
- Leave the `if missing_auth:` branch, the message `MCP server(s) missing auth_token: ...`, the remediation string, and `add_ok("mcp_auth")` exactly as they are.
- Do not change the other steps of `check_services` (readiness, mandatoriness, discovery, drift, safety tiers, RAG).

## Compatibility considerations
- Outcome source, message format, and remediation wording are unchanged, so reporting consumers need no change.
- The only visible change: a disabled server with an empty token no longer produces a fatal. Tests that use token-less `MagicMock` servers must set `is_disabled=False` (sibling procedures).

## Security considerations
Enabled servers stay fail-closed (ADR-004 Decision 14: safety failures stay unconditional): only `startup_mode = none` servers are exempt, and a test pins that an enabled token-less server is still fatal. No token value is read, logged, or copied.

## Rollback considerations
Revert the commit; the release unit (this filter and the two mock adjustments) is reverted together, otherwise the adjusted mocks and the filter disagree.

## Validation plan
- `uv run ruff format --check` and `uv run ruff check` on `scripts/agent/startup_validation.py`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus`; `uv run bandit -r scripts/ -c pyproject.toml -ll`; `PYTHONPATH=scripts uv run lint-imports`; `uv run python tools/check_module_size.py`.
- `uv run pytest tests/agent/test_startup_validation.py -q` passes with the new tests.
- `uv run pytest tests/agent/test_startup_severity_classification.py tests/agent/test_startup.py tests/agent/shared/test_startup_validation_pipeline.py tests/agent/test_startup_rollback.py tests/agent/test_startup_memory_failures.py -q`: the tests that build token-less `MagicMock` servers are an allowed red state until their sibling procedures set `is_disabled=False` (release unit); record each in the Failure Log. Every other test passes.

## Completion criteria
- A configuration whose only token-less server is disabled yields an OK `mcp_auth` outcome and no fatal from that step (`AC-1`).
- An enabled token-less server still yields a fatal naming it, and disabled servers are not named (`AC-2`).
- `check_services` has no other change.

## Out of Scope
- Whether the check should exist for enabled servers, config-layer validation, token resolution, and `_check_component_mandatoriness` handling of disabled servers (Plan UNK-01).
- The test and documentation rows (separate procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261104-165352 | 20261104-165352 |  |
| 2 | Run the targeted tests of the Validation plan and record the allowed red states | Completed | 20261104-165352 | 20261104-165352 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the Validation plan | Completed | 20261104-165352 | 20261104-165352 |  |

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
- **Requirement ID**: `REQ-001` (disabled token-less server passes), `REQ-002` (enabled offenders stay fatal)
- **Source issue**: `issues/20261031-135522_disabledauth001_disabled-server-auth-fatal.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261104-095503_disabledauth001_disabled-server-auth-fatal.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-141805
- **Related target files**: `scripts/agent/startup_validation.py`