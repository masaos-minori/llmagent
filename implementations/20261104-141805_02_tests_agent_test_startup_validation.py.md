## Goal
- Add tests, driving the real `check_services()`, for the `mcp_auth` exemption: a disabled token-less server passes, an enabled token-less server is fatal and named, and a mix names only the enabled offender (`REQ-003`: new tests fail on the pre-change code and pass after the change).

## Scope
**Release unit**: N/A: not part of a release unit

- New test code and one optional keyword parameter on the file's existing `_run_check_services` helper, in `tests/agent/test_startup_validation.py`. No production code.

## Assumptions
- Execution order: this procedure needs no name created by the others, so the executor SHOULD run it first (Plan Phase 1) to record the new tests failing on the pre-change code, then run the release-unit procedures.
- The file's `_run_check_services(rag_service, *, wait_for_side_effect=None)` drives the real `check_services()` with every check but RAG patched to a clean pass; its `_make_ctx()` leaves `ctx.cfg.mcp.mcp_servers` a `MagicMock` (iterating it yields nothing), so the new tests must supply a real dict (checked in Step 3a).
- A real `McpServerConfig(transport=TransportType.HTTP, url=..., startup_mode=StartupMode.NONE, auth_token="")` is valid configuration, because `_validate_auth_token` exempts disabled servers; an enabled token-less server cannot be built as a real config, so it is a `MagicMock` with `is_disabled=False`.
- `check_services()` builds its own `Logger`; the helper already patches `shared.logger.Logger`, so no log file is touched.
- Step 2 start conditions held: the Plan is not gated, has no blocking Unknown, and the overlap with the configuration-only validation Plan is a recorded sequencing dependency.

## Design decisions
- Extend the existing helper with an optional keyword `mcp_servers` (new) rather than copy it: when given, it sets `ctx.cfg.mcp.mcp_servers` and also patches `agent.startup_validation._check_component_mandatoriness` with a `MagicMock`, so the mandatoriness check does not add unrelated fatals; callers that omit it behave as before.
- Assert on the `mcp_auth` outcomes only (filter by `source == "mcp_auth"`), as the severity tests do.

## Alternatives considered
N/A: the cases are fixed by the Plan's Tests section; a second helper would duplicate the patch list.

## Implementation
### Target file
`tests/agent/test_startup_validation.py`

### Procedure
1. Add the optional `mcp_servers` (new) keyword to `_run_check_services` and the conditional patch of `_check_component_mandatoriness`.
2. Add `McpServerConfig`, `StartupMode`, and `TransportType` to the existing `from shared.mcp_config import SecurityProfile` import.
3. Append a class `TestMcpAuthDisabledServers` (new) with three async tests.

### Method
- `test_disabled_server_without_token_passes_mcp_auth` (new): `mcp_servers = {"optional_srv": <real disabled McpServerConfig with auth_token="">}`; the `mcp_auth` outcomes are exactly one, with status `StartupCheckStatus.OK`; there is no `StartupCheckStatus.FATAL` among them.
- `test_enabled_server_without_token_is_fatal_and_named` (new): `mcp_servers = {"web": MagicMock(auth_token="", is_disabled=False)}`; one `mcp_auth` outcome with status `FATAL` whose message contains `web`.
- `test_message_lists_only_enabled_offenders` (new): `mcp_servers = {"optional_srv": <disabled real config>, "web": MagicMock(auth_token="", is_disabled=False)}`; the single `mcp_auth` outcome is `FATAL`, its message contains `web`, and does not contain `optional_srv`.
- Reuse the file's clean RAG service mock (a `MagicMock` whose `consistency()` returns an object with `is_consistent=True` and no findings) as the `rag_service` argument.

### Details
- Keep the existing `TestRagConsistencyTimeout` tests and the posture-gate test unchanged; the helper change must not alter them.
- Use no real token or environment value; the server keys are synthetic.

## Compatibility considerations
N/A: test-only change; the helper keeps its old behavior when `mcp_servers` is omitted.

## Security considerations
N/A: synthetic keys and empty tokens only; nothing is read from the environment.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Before the production procedures run: `uv run pytest tests/agent/test_startup_validation.py -k TestMcpAuthDisabledServers -q` shows the first and third tests failing (the second passes on both versions); record the output in the Failure Log.
- After them: the same command passes with three tests collected, and `uv run pytest tests/agent/test_startup_validation.py -q` passes in full.
- `uv run ruff format --check`, `uv run ruff check`, and `uv run python tools/check_mock_patch_targets.py` report no findings.

## Completion criteria
- The three tests exist and pass after the production change; at least the disabled-server and mixed tests were seen failing on the pre-change code (`AC-1`, `AC-2`, `AC-3`).
- The existing tests of the file still pass.

## Out of Scope
- Production code and the existing `MagicMock` tests of the two sibling test files (separate procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the helper change and the three tests as described in Implementation > Procedure/Method | Pending | — | — | |
| 2 | Run the new tests before the production change and record the failures, then run them after | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (new tests fail before and pass after the change)
- **Source issue**: `issues/20261031-135522_disabledauth001_disabled-server-auth-fatal.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261104-095503_disabledauth001_disabled-server-auth-fatal.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-141805
- **Related target files**: `tests/agent/test_startup_validation.py`
