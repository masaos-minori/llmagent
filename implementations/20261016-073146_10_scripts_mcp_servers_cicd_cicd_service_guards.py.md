## Goal

Extend the CI/CD server's allowlist guards into a self-validation entry point that returns the
common Security Posture, so cicd-mcp validates its own configuration instead of being audited by
the Agent (`REQ-008`, `AC-005`).

## Scope

- One modified module `scripts/mcp_servers/cicd/cicd_service_guards.py`: add a CI/CD self-validation
  function that produces `SecurityCheckResult` values from the allowlist rules this mixin already
  enforces at call time.
- Existing guard methods and their `CicdAuthorizationError` behavior are unchanged.
- Publishing on `/health` is row `45` (`scripts/mcp_servers/cicd/cicd_server.py`).

## Assumptions

- Current mixin verified: `CiCdGuards` at
  `scripts/mcp_servers/cicd/cicd_service_guards.py:19`, `__init__(backend, repo_allowlist,
  workflow_allowlist)` at `:22-42` with empty-allowlist warnings at `:35-42`,
  `_assert_allowed_repo()` at `:44-56` (empty allowlist denies all at `:49-52`),
  `_assert_allowed_workflow()` at `:58-75` (empty allowlist denies all at `:63-67`, path-separator
  rejection at `:68-71`).
- The rule the removed Agent audit enforced for CI/CD is the empty `workflow_allowlist` DENY-ALL
  warning (`scripts/agent/services/security_audit.py:185-195`), read through
  `load_cicd_audit_config()` (`scripts/agent/security_audit_config.py:95`).
- Plan `Assumptions`: the retired `security_lockdown_enabled` suppression no longer applies, so an
  empty allowlist is a validation failure in every profile.
- **Needs confirmation**: the CI/CD check ids below are finalized here from `REQ-008`; `memo2.md`'s
  original list is unrecoverable (Plan `UNK-01`).

## Design decisions

- Add `validate_cicd_security(backend: CiBackend, repo_allowlist: Sequence[str], workflow_allowlist: Sequence[str]) -> list[SecurityCheckResult]`
  (new module-level function). It is a pure function of the values the constructor already receives,
  so it can run in the `SERVER_SECURITY_VALIDATION` stage before HTTP bind (`REQ-003`).
- Check ids (finalized here, Needs confirmation):
  - `server.repo_allowlist` — empty is `FAILED` with reason `allowlist_empty`.
  - `server.workflow_allowlist` — empty is `FAILED` with reason `allowlist_empty`.
  - `server.workflow_pattern_valid` — a configured entry containing `/` or `\` is `FAILED` with
    reason `config_invalid`, because `_assert_allowed_workflow()` rejects such a value on every
    call (`:68-71`), so the entry is unreachable configuration.
  - `server.backend_available` — `NOT_APPLICABLE` with reason `not_applicable` when the injected
    `CiBackend` exposes no availability probe; otherwise `FAILED` with reason
    `dependency_unreachable` when the backend reports itself unavailable.
- Both empty allowlists are `FAILED`, not `WARNING`: the mixin already denies every operation in
  that state (`:49-52`, `:63-67`), so a server that can do nothing must not report Ready. This is
  the same fail-closed-empty-allowlist rule the Plan's `Assumptions` state.
- The existing `logger.warning` calls at `:35-42` are kept. They are the operator-facing
  availability signal; the posture is the machine-readable security-validation result. Removing the
  warnings would change observable log output, which this row does not intend.
- `server.backend_available` is deliberately weak: `CiBackend` is a duck-typed injected object
  (`:14`, `:24`), and this row must not add a new protocol to it. A backend without a probe is
  reported `NOT_APPLICABLE` rather than silently skipped.

## Alternatives considered

- Validate inside `CiCdGuards.__init__` by raising on empty allowlists — rejected: raising in a
  constructor cannot produce the posture, and `REQ-002` requires the failure to be visible on
  `/health`, not only as an exception. It would also change `CiCdService` construction behavior for
  tests that construct guards with empty allowlists on purpose.
- Report empty allowlists as `WARNING` to match the old audit's warning — rejected: the old audit
  only warned because lockdown could suppress it; the Plan retires that suppression, and the server
  is functionally dead in that state.
- Add a `server.github_token` check — rejected: `auth_token` and backend tokens are Secrets, and
  `REQ-002` forbids carrying them or their values; token presence is already enforced by the
  server's own auth middleware and by the Agent's `mcp_auth` check
  (`scripts/agent/startup_validation.py:70-81`).

## Implementation
### Target file

`scripts/mcp_servers/cicd/cicd_service_guards.py` (modify)

### Procedure

1. Import `SecurityCheckResult`, `SecurityCheckStatus`, and the reason-code constants from
   `shared.security.result_dto` (row `02`).
2. Add `validate_cicd_security()` (new) after the class (`:75`).
3. Keep `__init__`, `_assert_allowed_repo()`, `_assert_allowed_workflow()` unchanged.

### Method

- Fixed check order: `server.repo_allowlist`, `server.workflow_allowlist`,
  `server.workflow_pattern_valid`, `server.backend_available`.
- The path-separator rule is expressed once: the validator reuses the same `"/" in value or
  "\\" in value` test as `:68` so the startup check and the runtime rejection cannot diverge.
- Messages report counts and setting names only (`workflow_allowlist is empty`,
  `workflow_allowlist contains 1 entry with a path separator`). Allowlist entries are raw allowlist
  values under `REQ-002` and must not be echoed.
- `server.backend_available` calls `getattr(backend, "is_available", None)` and only evaluates the
  result when it is callable; anything else yields `NOT_APPLICABLE`.

### Details

- The module is 75 lines; the addition is roughly 40 lines and stays well under the 200-line
  convention.
- `CiCdGuards` is a mixin without a `self._allowed_dirs`-style shared contract, so the module-level
  function does not need an instance; the server row (`45`) calls it with the same values it passes
  to the constructor.
- The `U-3` fail-closed comment (`:30`, `:47`) stays; the new checks are the startup-time view of
  the same rule.

## Compatibility considerations

- Additive change: no signature or exception-type changes, so `tests/mcp_servers/cicd/*` that
  assert `CicdAuthorizationError` messages keep passing.
- Behavior change is limited to startup: cicd-mcp with an empty `repo_allowlist` or empty
  `workflow_allowlist` now reports a failed posture and cannot report `ready=true` (row `06` / row
  `45`). Its runtime denial behavior was already fail-closed.
- No `docs/*.md` change is in scope for this row; `docs/22_mcp/mcp_05_01_access-control-and-allowlists.md:226`
  describes the Agent-side CI/CD allowlist warning and is listed as a follow-up in the Plan.

## Security considerations

- `REQ-008` / Plan `INV-05`: cicd-mcp validates its own configuration before Ready; the Agent stops
  reading `cicd_mcp_server.toml` (row `21` removes `load_cicd_audit_config()`).
- `REQ-002` / Plan `INV-09`: allowlist entries are raw allowlist values and must not appear in the
  posture or messages.
- Fail-closed semantics are preserved and strengthened: empty allowlists stay deny-all at runtime
  and become a startup failure.

## Rollback considerations

- Revert this commit together with row `45`, which imports the new function. No config or data
  migration is involved.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Empty repo allowlist | `uv run pytest tests/mcp_servers/cicd/test_cicd_security_validation.py` (new test file) | `server.repo_allowlist` `FAILED`, reason `allowlist_empty` |
| Empty workflow allowlist | same new test file | `server.workflow_allowlist` `FAILED`, reason `allowlist_empty`, no lockdown suppression |
| Separator in an allowlist entry | same new test file | `server.workflow_pattern_valid` `FAILED`, reason `config_invalid` |
| Backend without probe | same new test file | `server.backend_available` `NOT_APPLICABLE`, never an omitted check |
| Deterministic check set | same new test file | the same four check ids appear for every configuration |
| Existing CI/CD suite | `uv run pytest tests/mcp_servers/cicd/` | passes, `CicdAuthorizationError` assertions unchanged |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean |

## Completion criteria

- Plan `AC-005` for CI/CD: cicd-mcp validates its own configuration and returns the common posture.
- The four finalized check ids are always present, with `NOT_APPLICABLE` used instead of omission.
- No allowlist entry appears in any posture field or message.

## Out of scope

- Editing `scripts/mcp_servers/cicd/cicd_server.py` (row `45`) or `cicd_service.py`.
- Changing runtime denial behavior or `CicdAuthorizationError` message text.
- Agent-side validation and classification (rows `17`-`18`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `validate_cicd_security()` | Pending | — | — | check ids are Needs-confirmation |
| 2 | Add `tests/mcp_servers/cicd/test_cicd_security_validation.py` | Pending | — | — | |
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
- **Requirement ID**: `REQ-008` (CI/CD self-validation)
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/mcp_servers/cicd/cicd_service_guards.py`
