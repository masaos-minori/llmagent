## Goal

Restore `tests/mcp_servers/shell/test_shell_mcp_service.py` to a passing state after row `07` makes
`init_sandbox()` fail-closed, without weakening what any of its tests assert.

## Scope

- One modified test module `tests/mcp_servers/shell/test_shell_mcp_service.py`: the shared policy
  fixture, the `TestInitSandbox` cases, and the one test that relied on a `"none"` backend reaching
  `ShellService`.
- No production module is changed here; row `07` owns the behavior change.

## Assumptions

- Row `07`'s fail-closed rule is the intended behavior, so the tests must follow it rather than the
  reverse. Verified: 40 tests in this file fail with `RuntimeError: configured shell sandbox backend
  is not a sandboxing backend (backend='none')` after the row `07` change.
- `_make_policy()` sets `sandbox_backend="none"` at `tests/mcp_servers/shell/test_shell_mcp_service.py:55`
  and `_make_service()` (`:61-75`) passes it to `ShellService`, which calls `init_sandbox()` at
  `scripts/mcp_servers/shell/shell_service.py:67`. Verified.
- `TestInitSandbox` (`:198-216`) asserts `_init_sandbox("none") == "none"` at `:199-200`, which is the
  pass-through row `07` removes. Verified.
- The host must not be a test dependency: `.github/workflows/ci.yml:11,40` run on `ubuntu-latest` with
  no firejail install step, so a fixture that configures `firejail` must not require the real binary.
  Verified against the workflow file.
- Patching `mcp_servers.shell.shell_service_static_helpers.shutil.which` is the established pattern in
  this file (`:203-206`, `:211-214`). Verified.

## Design decisions

- Add one module-scoped autouse fixture that patches `shutil.which` in the helpers module to a fixed
  fake firejail path, so `init_sandbox("firejail")` succeeds for every test in the file regardless of
  the host.
- `_make_policy()` configures `sandbox_backend="firejail"`: the fixture keeps testing command
  execution, cwd resolution, kill policy, truncation, and dry-run behavior exactly as before.
- `TestInitSandbox` asserts refusal instead of pass-through: `"none"`, `""`, and an unrecognized
  backend each raise `RuntimeError`, `firejail` with the binary present returns `"firejail"`, and
  `firejail` with the binary missing raises.
- `TestBuildArgv::test_none_sandbox_returns_argv_unchanged` (`:222-226`) keeps covering
  `SubprocessRunner`'s non-`firejail` branch (`scripts/mcp_servers/shell/subprocess_runner.py:38-40`)
  by injecting `_sandbox_backend` on the runner directly, the pattern already used at `:228-235`,
  because `ShellService` can no longer be constructed with `"none"`.
- No assertion about command behavior is changed or removed.

## Alternatives considered

- Rely on the host's firejail binary — rejected: CI installs no firejail, and a missing binary would
  fail 40 tests that have nothing to do with sandboxing.
- Patch `init_sandbox` itself in the fixture — rejected: it hides the exact behavior row `07` changes
  and would let a regression in that rule pass unnoticed.
- Delete the `"none"` argv test — rejected: the non-`firejail` branch still exists in
  `SubprocessRunner.build_argv` and must stay covered.

## Implementation
### Target file

`tests/mcp_servers/shell/test_shell_mcp_service.py` (modify)

### Procedure

1. Add an autouse fixture `_firejail_present` that patches
   `mcp_servers.shell.shell_service_static_helpers.shutil.which` to a fixed fake path for the whole
   module.
2. Change `_make_policy()`'s `sandbox_backend="none"` (`:55`) to `sandbox_backend="firejail"`.
3. Rewrite `TestInitSandbox` (`:198-216`) to assert the fail-closed outcomes and keep the
   missing-binary case by overriding the fixture inside that test.
4. Update `TestBuildArgv::test_none_sandbox_returns_argv_unchanged` (`:222-226`) to inject
   `svc._subprocess_runner._sandbox_backend = "none"` before calling `build_argv`.
5. Leave every other test in the file unchanged.

### Method

- The fixture patches the same attribute path the existing explicit patches use, so a test that needs
  the binary missing overrides it with its own `with patch(...)` block for its own duration only.
- Refusal assertions match on the message text the helper produces (`_sandbox_backend_message`), not
  on a reason code: `init_sandbox()` reports through an exception, and the reason code travels only in
  the posture results that row `07`'s `validate_shell_security()` returns.
- The fake path is a constant, not a repository path, so no test asserts against a real binary location.

### Details

- The fixture is autouse and module-scoped in effect (it wraps every test in the file); it must yield
  rather than return so the patch is active for the whole test body.
- `TestInitSandbox` keeps its existing name so the mapping from the old pass-through tests to the new
  refusal tests stays visible in the diff.
- The `firejail`-present case no longer needs its own `patch` block once the fixture exists; keeping
  the explicit patch there is harmless but redundant, so it is removed.

## Compatibility considerations

- Only this test module changes. `tests/mcp_servers/shell/test_shell_server_endpoints.py:37` and
  `tests/mcp_servers/shell/test_subprocess_runner.py:30` build their own fakes and never construct
  `ShellService` through `_make_policy()`; both pass unchanged.
- `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py` also constructs `ShellService` with
  a `"none"` backend; that file is row `54`, not this row.
- No `docs/*.md` change is in scope for this row.

## Security considerations

- No command-allowlist entry, config path, or token appears in any new assertion or fixture value.
- The fixture's fake binary path is a constant placeholder and is never written to disk.

## Rollback considerations

- Revert this file together with row `07`. Reverting only this file restores tests that assert the
  removed pass-through, which then fail against the fail-closed helper.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Shell suite green | `uv run pytest tests/mcp_servers/shell/` | 0 failures |
| Fail-closed assertions | same command | `"none"`, `""`, and an unrecognized backend each raise `RuntimeError` |
| Host independence | same command | no test depends on a real firejail binary being installed |
| New row `07` tests | `uv run pytest tests/mcp_servers/shell/test_shell_security_validation.py` | passes |
| Static gates | `uv run ruff check tests/`, `uv run python tools/check_mock_patch_targets.py` | clean |

## Completion criteria

- `uv run pytest tests/mcp_servers/shell/` exits 0.
- No test in the file asserts the removed `init_sandbox()` pass-through.
- No test in the file depends on the host having firejail installed.

## Out of scope

- Changing `ShellService`, `SubprocessRunner`, or any other production module (row `07` owns the rule).
- `tests/mcp_servers/shell/test_shell_server_auth.py`, `test_shell_server_endpoints.py`, and
  `test_subprocess_runner.py` (verified unaffected).
- Agent-side posture classification (rows `17`-`19`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the fixture, `TestInitSandbox`, and the `"none"` argv test per Procedure/Method/Details | Completed | 20261016-201939 | 20261016-201939 | added by Plan amendment after row `07` broke 40 tests Added by Plan amendment after row 07 broke 40 tests. The autouse fixture _firejail_present patches mcp_servers.shell.shell_service_static_helpers.shutil.which to a fake path for the whole module. _make_policy and the three inline ShellPolicy constructions now configure sandbox_backend firejail. TestInitSandbox now asserts refusal for none, empty, and an unrecognized backend and keeps the missing-binary case by overriding the fixture. test_none_sandbox_returns_argv_unchanged injects _sandbox_backend none on the runner because ShellService can no longer be constructed with none. The missing-binary message wording was kept identical to the pre-change text so test_firejail_not_found_raises_runtime_error needed no regex change. |
| 2 | Confirm the Shell suite and the new row `07` test file pass | Completed | 20261016-201939 | 20261016-201939 | uv run pytest tests/mcp_servers/shell/ reports 95 passed and 0 failures: 76 pre-existing tests plus the 19 new row 07 tests. tests/mcp_servers/shell/test_shell_security_validation.py also passes on its own. No test in this file depends on a host firejail binary. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261016-201939 | 20261016-201939 | Full validation sequence: ruff clean, mypy clean on 421 source files, lint-imports 6 kept 0 broken, check_mock_patch_targets no findings, no bare except. Full suite: 8635 passed, 19 skipped, 9 failed, and all 9 are the pre-existing tests/agent/test_startup_rollback.py schema-version failures. Coverage and diff-cover are deferred to the end of the procedure batch. |

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
- **Requirement ID**: `REQ-005` (Shell self-validation; tests for the fail-closed `init_sandbox`)
- **Source issue**: `issues/done/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `tests/mcp_servers/shell/test_shell_mcp_service.py`