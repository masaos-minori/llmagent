## Goal

Close the fail-closed gap in the Shell server's sandbox validation and expose Shell's own security
validation results as the common posture (`REQ-005`, `AC-005`).

## Scope

- One modified module `scripts/mcp_servers/shell/shell_service_static_helpers.py`:
  `init_sandbox()` becomes fail-closed for every backend value, and a new posture-producing entry
  point for Shell's self-validation is added here.
- Wiring the produced posture into Shell's `/health` uses `make_health_response(..., security=...)`
  from row `06`; the Shell `/health` handler itself (`scripts/mcp_servers/shell/shell_server.py`) is
  not a target row of this Plan.

## Assumptions

- `init_sandbox(backend)` at `scripts/mcp_servers/shell/shell_service_static_helpers.py:32-38`
  validates only `backend == "firejail"` binary presence at `:34-37` and returns every other value
  unchanged at `:38`. Verified against current source.
- Its only call site is `scripts/mcp_servers/shell/shell_service.py:67`
  (`self._sandbox_backend = init_sandbox(policy.sandbox_backend)`). Verified.
- `ShellConfig.shell_sandbox_backend` defaults to `"firejail"` and a missing config key also
  resolves to `"firejail"` (`scripts/mcp_servers/shell/shell_models.py:60`, `:86-87`).
- The rules the removed Agent audit enforced for Shell are the ones this server must now enforce
  itself (`scripts/agent/services/security_audit.py:89-117`): `backend == "none"` is a hard error
  "regardless of environment", a non-`firejail` backend is a warning, `firejail` with a missing
  binary is a hard error, and an empty `command_allowlist` is a DENY-ALL warning.
- **Needs confirmation**: the Shell check ids and the reason-code assignment below are finalized
  here from `REQ-005`; `memo2.md`'s original list is unrecoverable (Plan `UNK-03` covers RAG/MDQ
  granularity, and the same derivation applies to Shell).

## Design decisions

- Keep `init_sandbox(backend) -> str` with the same signature and the same "returns the backend
  name unchanged" contract, but make it raise for every backend value it cannot prove safe:
  - `"firejail"` and `shutil.which("firejail") is None` -> `RuntimeError` (existing behavior, `:34-37`).
  - `"none"`, empty string, or any unrecognized value -> `RuntimeError`. This is the gap fix: the
    current silent `return backend` at `:38` is what lets an unsandboxed Shell start.
- Add `validate_shell_security(backend: str, command_allowlist: Sequence[str]) -> list[SecurityCheckResult]`
  (new) as the posture-producing entry point. It never raises for a policy violation; it returns
  `SecurityCheckResult` values (row `02`) so the failure is reportable in the posture instead of
  only in an exception message.
- Check ids (finalized here, Needs confirmation): `server.sandbox_backend` (configured value is a
  known, sandboxing backend), `server.sandbox_binary` (the backend's binary is present),
  `server.command_allowlist` (non-empty; empty is `FAILED` with reason code `allowlist_empty`),
  `server.resource_limits` (the `set_resource_limits` constants are internally consistent).
- `init_sandbox()` and `validate_shell_security()` share one private helper `_sandbox_backend_error()`
  so the hard-error rule and the posture check cannot drift apart.
- Empty `command_allowlist` is reported as `FAILED`, not as a warning-only state, and no lockdown
  suppression exists: the Plan `Assumptions` state the retired `security_lockdown_enabled` key no
  longer suppresses validation. Shell already refuses all commands when the allowlist is empty
  (`scripts/mcp_servers/shell/shell_server.py:59-60`), so `FAILED` matches observable behavior.

## Alternatives considered

- Move the validation into `ShellService.__init__` (`shell_service.py:67`) — rejected: this row's
  target is the static helper module, and `ShellService` is constructed after the server has already
  loaded its config, which is later in the `REQ-003` ordering than the security-validation stage.
- Return a bool from `init_sandbox()` and let the caller decide — rejected: the current call site
  ignores any non-raise outcome, so a bool would be silently dropped exactly like the current
  pass-through.
- Delete `init_sandbox()` and call `validate_shell_security()` from `shell_service.py` instead —
  rejected: it changes `shell_service.py`, which is not a row in the Plan's frozen table.

## Implementation
### Target file

`scripts/mcp_servers/shell/shell_service_static_helpers.py` (modify)

### Procedure

1. Import `SecurityCheckResult` (and the reason-code vocabulary) from `shared.security.result_dto`
   (row `02`).
2. Add `_sandbox_backend_error(backend: str) -> str | None` (new): returns the failure reason for a
   backend value, or `None` when the backend is acceptable and its binary is present.
3. Rewrite `init_sandbox()` (`:32-38`) to raise `RuntimeError(_sandbox_backend_error(backend))` when
   the helper reports a reason, and keep `return backend` otherwise.
4. Add `validate_shell_security()` (new) that maps each rule to one `SecurityCheckResult`.
5. Keep `set_resource_limits()` (`:41-62`) and `make_preexec()` (`:65-85`) unchanged.

### Method

- `_sandbox_backend_error()` covers three distinct reasons so the Agent can classify them without
  parsing text: unknown/`none`/empty backend -> reason code `sandbox_backend_unsupported`; `firejail`
  with a missing binary -> reason code `sandbox_backend_missing`; acceptable backend -> reason code
  `ok`. Both codes are already in `SECURITY_REASON_CODES` (row `02`).
- `validate_shell_security()` runs the rules in the fixed order
  `server.sandbox_backend`, `server.sandbox_binary`, `server.command_allowlist`,
  `server.resource_limits`, so the posture check list is deterministic for row `05`'s CHECKSET
  comparison.
- Messages carry the backend name only (`backend="none"`), never the allowlist contents. The
  command allowlist is a raw sensitive value under `REQ-002`/`REQ-004`, so its length may be
  reported but its entries may not.
- `server.resource_limits` is a self-consistency check on the module constants
  (`_CPU_LIMIT_SAFETY_MULTIPLIER`, `_MIN_CPU_LIMIT_SEC`, `_MAX_OPEN_FILE_DESCRIPTORS`,
  `_MAX_SUBPROCESS_COUNT`, `_MAX_WRITTEN_FILE_MB` at `:21-29`): a non-positive limit is `FAILED`.
  It is a technical-safety check, which `REQ-005` requires the server to own.

### Details

- The module docstring (`:2-7`) states these helpers have no instance state; `validate_shell_security()`
  must stay a pure function of its arguments to keep that contract.
- `init_sandbox()`'s docstring (`:33`) must be updated: it no longer "returns the backend name
  unchanged" for unvalidated values.
- The `import shutil as _shutil` trick used by the removed audit (`security_audit.py:87`) is not
  needed here: `shutil` is already imported at `:14`.
- Shell's own `/health` already reports `command_allowlist` emptiness as a disabled reason
  (`shell_server.py:59-60`); after this row the same condition also appears in the posture, which is
  the intended duplication (one is availability, one is security validation).

## Compatibility considerations

- Behavior change: a config with `shell_sandbox_backend = "none"` or a typo'd backend now fails at
  `ShellService` construction instead of starting unsandboxed. This is the intended `REQ-005` fix,
  and it matches what the Agent audit already made a hard error (`security_audit.py:89-91`), so no
  configuration that previously started successfully is newly blocked.
- `init_sandbox()`'s signature and return type are unchanged, so `shell_service.py:67` needs no edit.
- `tests/mcp_servers/shell/*` that assert `/health` status codes
  (`tests/mcp_servers/shell/test_shell_server_auth.py:40-42`,
  `tests/mcp_servers/shell/test_shell_mcp_service.py:750`) are unaffected unless they configure a
  non-`firejail` backend; any such test must be updated to expect the fail-closed outcome.
- No `docs/*.md` change is in scope for this row.

## Security considerations

- `REQ-005` / Plan `INV-05`: Shell must not reach Ready with an unsandboxed or unvalidated backend.
  The silent pass-through at `:38` is the exact defect.
- `REQ-004`: no Secret and no allowlist contents appear in the new messages or in the posture.
- Fail-closed on empty allowlist is preserved: Shell refuses all commands (`shell_server.py:59-60`)
  and now also reports `FAILED` in its posture.

## Rollback considerations

- Revert this commit. `shell_service.py:67` keeps working against the pre-change `init_sandbox()`.
- Rolling back restores the unsandboxed pass-through, so a rollback must be recorded as a known-good
  version rollback (Plan `Risks`: no implicit runtime fallback), not as a config toggle.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Fail-closed backend values | `uv run pytest tests/mcp_servers/shell/test_shell_security_validation.py` (new test file) | `"none"`, `""`, and an unknown backend each raise / report `FAILED` |
| Missing binary | same new test file | `firejail` without the binary reports `server.sandbox_binary` `FAILED` with reason `sandbox_backend_missing` |
| Empty allowlist | same new test file | `server.command_allowlist` `FAILED` with reason `allowlist_empty`, no suppression flag |
| Posture shape | same new test file | `validate_shell_security()` returns only `SecurityCheckResult` values with the four finalized check ids |
| Existing Shell suite | `uv run pytest tests/mcp_servers/shell/` | passes |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean; `mcp_servers -> shared` allowed |

## Completion criteria

- Plan `AC-005` for Shell: Shell validates its own configuration and technical safety and returns the
  common posture, and fails closed on a bad config.
- No backend value can reach `return backend` without being proven safe.
- The four finalized check ids are emitted in a deterministic order.

## Out of scope

- Editing `scripts/mcp_servers/shell/shell_service.py` or `shell_server.py` (not Plan rows).
- Publishing the posture on `/health` (row `06` supplies the builder; Shell's handler wiring is not a
  row in this Plan's frozen table).
- Agent-side classification (rows `17`-`18`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `init_sandbox` fail-closed change + `validate_shell_security()` | Pending | — | — | check ids are Needs-confirmation |
| 2 | Add `tests/mcp_servers/shell/test_shell_security_validation.py` | Pending | — | — | |
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
- **Requirement ID**: `REQ-005` (Shell self-validation; `init_sandbox` fail-closed gap)
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/mcp_servers/shell/shell_service_static_helpers.py`
