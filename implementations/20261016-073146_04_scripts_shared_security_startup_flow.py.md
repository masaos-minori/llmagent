## Goal

Implement the common startup-validation flow every MCP server runs in the same order, so that a
server which fails validation never binds HTTP and never reports Ready (`REQ-003`).

## Scope

- One new module `scripts/shared/security/startup_flow.py`: the ordered flow and its stage
  identifiers.
- Each server supplies its own stage callables; wiring a server to the flow belongs to that
  server's row (`07`-`16`). HTTP bind itself stays in `scripts/mcp_servers/server.py` (reference
  file, not modified).

## Assumptions

- `scripts/mcp_servers/server.py:225-246` already enforces the two preconditions the flow depends
  on: loopback-only bind, and `ConfigLoader.restrict_to(self.own_config_file)` with a
  `ConfigPermissionError` when `own_config_file` is falsy. Verified against current source.
- The flow cannot read configs itself: `shared` must stay a leaf (`.importlinter:19-28`).

## Design decisions

- `StartupStage` (new) is a `StrEnum` of the `REQ-003` stages in order: `CONFIG_LOAD`,
  `SCHEMA_VALIDATION`, `COMMON_SECURITY_VALIDATION`, `SERVER_SECURITY_VALIDATION`,
  `DEPENDENCY_VALIDATION`, `TOOL_CAPABILITY_VALIDATION`, `RUNTIME_STATE_INSTALLATION`,
  `HTTP_BIND`, `READY`.
- `run_startup_validation()` (new) takes the server key plus one callable per stage the server
  owns, runs them in the enum order, and returns a `SecurityPosture` (row `03`). It never binds
  HTTP: `HTTP_BIND` and `READY` are recorded as stages the caller must reach only when the
  returned posture has `ready=True`.
- A stage that raises is converted into a `SecurityCheckResult` with status `FAILED` and reason
  code `config_invalid` (schema stage) or `dependency_unreachable` (dependency stage); the flow
  stops at the first failed security stage and returns a posture with `validated=False`,
  `ready=False`. Stopping rather than continuing keeps a partially-validated server from ever
  reaching `RUNTIME_STATE_INSTALLATION`.
- Common security checks (own-config-only, auth token present, published-tool sanity) live here
  so every server runs the same ones; server-specific checks are supplied by the server callable.

## Alternatives considered

- Put the flow in `scripts/mcp_servers/server.py` as a `MCPServer` method — rejected: the Agent
  side (row `17`) and the Shadow Validation harness (row `05`) need the same ordering, and
  `mcp_servers` cannot be imported by `agent` (`.importlinter:49-55`).
- Let each server implement its own ordering and only share the DTO — rejected: `REQ-003` requires
  one ordering, and per-server orderings cannot be asserted by one test.

## Implementation
### Target file

`scripts/shared/security/startup_flow.py` (new)

### Procedure

1. Define `StartupStage` (new) and `FLOW_VERSION` (new).
2. Define `StageOutcome` (new): the stage, its `SecurityCheckResult` list, and a `fatal` flag.
3. Define `run_startup_validation()` (new) that executes the stages in order and assembles the
   posture.
4. Define the built-in common checks the flow always runs: `check_own_config_only()` (new),
   `check_auth_token_present()` (new), `check_published_tools_declared()` (new).
5. Return the posture; do not raise for a failed check — the caller decides whether to bind.

### Method

- Each stage callable returns `Iterable[SecurityCheckResult]`; the flow appends them in stage
  order so the posture's check list is deterministic and comparable across servers (needed by
  row `05`'s CHECKSET comparison).
- `check_own_config_only()` verifies the caller passed a config view produced under
  `ConfigLoader.restrict_to(...)` by requiring the view to carry the restricted file name and
  comparing it to the server key's expected own-config file; a mismatch yields reason code
  `config_invalid`.
- `check_auth_token_present()` mirrors the Agent-side rule already present at
  `scripts/agent/startup_validation.py:70-81` (`mcp_auth`), so the same condition is enforced on
  both sides after `REQ-017` removes the audit. Its status is `WARNING` with reason code
  `auth_token_missing` and `validated` stays `true` (Plan `UNK-06`, resolved 2026-10-16): the Agent-side
  `mcp_auth` FATAL is the production control, and `tests/conftest.py:27-29` deliberately sets
  `MCP_GIT_AUTH_TOKEN=""`, `MCP_CICD_AUTH_TOKEN=""`, and `MCP_WEB_SEARCH_AUTH_TOKEN=""`, which a `FAILED`
  status would turn into 503 responses and break `tests/mcp_servers/git/test_git_security_compliance.py:2342-2346`
  and `tests/mcp_servers/cicd/test_mcp_server_health_status.py:25-33`.

### Details

- The flow records the stage name into each check id namespace (for example
  `common.auth_token`, `server.sandbox_backend`) so `REQUIRED_CHECK_IDS` (row `03`) can be
  asserted per server.
- Keep the module under 200 lines; if it grows, split the built-in common checks into a sibling
  module and add it to the Plan as an additional target row rather than folding it in here.

## Compatibility considerations

- New module; no existing call site changes in this row.
- Servers adopt it in rows `07`-`16`; until then the current per-server startup paths are
  unchanged, so the flow can land before any server consumes it.

## Security considerations

- `REQ-003` / Plan `INV-05`: validation failure blocks HTTP bind and Ready. The flow enforces this
  by refusing to produce a posture with `ready=True` when any security stage failed.
- `REQ-004`: stage failures are reported as reason codes; the flow must not include the raised
  exception's config-derived text in the posture message.

## Rollback considerations

- Revert the commit. No server depends on it until rows `07`-`16` land.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Stage ordering | `uv run pytest tests/shared/test_security_startup_flow.py -v` (new test file) | checks appear in `StartupStage` order |
| Fail-closed posture | same test file | a failing security stage yields `validated=False`, `ready=False` |
| Common checks present | same test file | every posture contains the three built-in common check ids |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean; `shared-is-leaf` keeps |

## Completion criteria

- Plan `AC-003`: one shared ordering exists, and a posture produced from a failing validation run
  cannot report `ready=True`.
- The flow is importable from both `agent` and `mcp_servers` without a new import-linter
  exception.

## Out of scope

- Changing `scripts/mcp_servers/server.py` `run_http()` (reference file only).
- Per-server check bodies (rows `07`-`16`).
- Agent-side classification (rows `17`-`18`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `startup_flow.py` per Procedure/Method/Details | Pending | — | — | |
| 2 | Add `tests/shared/test_security_startup_flow.py` per Validation plan | Pending | — | — | |
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
- **Requirement ID**: `REQ-003` (one shared startup ordering; validation failure blocks bind/Ready)
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/shared/security/startup_flow.py`
