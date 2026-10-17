## Goal

Keep the cross-server tool-layer guardrail test green after row `07` makes `init_sandbox()`
fail-closed, without weakening what that test compares.

## Scope

- One modified test module `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py`:
  `_shell_dispatch()`'s policy backend and its `ShellService` construction.
- No production module is changed here; row `07` owns the behavior change.

## Assumptions

- `_shell_dispatch()` sets `sandbox_backend="none"` at
  `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py:107` and passes that policy to
  `ShellService(policy)` at `:111`, which calls `init_sandbox()` at
  `scripts/mcp_servers/shell/shell_service.py:67`. Verified.
- Row `07`'s fail-closed rule is the intended behavior. Verified: the two `[shell]` parametrized
  cases fail with `RuntimeError: configured shell sandbox backend is not a sandboxing backend
  (backend='none')` after the row `07` change.
- The test only reads `get_dispatch_table()` keys and launches no command, so configuring a
  sandboxing backend changes nothing it asserts. Verified: 62 tests pass after the change.
- The host must not be a test dependency: `.github/workflows/ci.yml:11,40` run on `ubuntu-latest`
  with no firejail install step. Verified against the workflow file.

## Design decisions

- Configure `sandbox_backend="firejail"` and wrap only the `ShellService(policy)` construction in a
  `patch` of `mcp_servers.shell.shell_service_static_helpers.shutil.which` returning a fixed fake
  path, the same patch target row `53` uses.
- Patch the construction rather than the whole module: this file builds service instances for eight
  servers, and only the Shell one reaches `shutil.which`.
- Extend the existing `unittest.mock` import line instead of adding a second import block.

## Alternatives considered

- An autouse fixture like row `53`'s — rejected: the other seven constructors never touch
  `shutil.which`, so a module-wide patch would be unnecessary coverage of a stdlib function.
- Keep `"none"` and patch `init_sandbox` itself — rejected: it hides the exact rule row `07` adds.
- Drop the `[shell]` parametrization — rejected: the guardrail exists to catch Shell tool drift.

## Implementation
### Target file

`tests/mcp_servers/cicd/test_tool_server_layer_consistency.py` (modify)

### Procedure

1. Add `patch` to `from unittest.mock import AsyncMock, MagicMock` (`:32`).
2. Change `_shell_dispatch()`'s `sandbox_backend="none"` (`:107`) to `sandbox_backend="firejail"`.
3. Wrap `svc = ShellService(policy)` (`:111`) in the `patch(...)` block that makes the firejail
   binary present.
4. Leave every other constructor, parametrization, and assertion unchanged.

### Method

- The patch is scoped to the construction only, so no assertion runs while a stdlib function is
  patched.
- The fake path is a constant placeholder, not a repository path, and is never written to disk.
- A comment at the construction states why the patch exists so a later reader does not remove it.

### Details

- `ShellPolicy` still accepts `"none"` as a protocol value (`scripts/shared/protocols/shell.py:41`,
  validated at `:56`); row `07` enforces the rule at `init_sandbox()`, so what changes here is the
  test's policy value, not the DTO contract.
- `get_dispatch_table()` is read after the patch block exits, which keeps the guardrail's own
  behavior unpatched.

## Compatibility considerations

- Only `_shell_dispatch()` changes; the `[shell]` cases and the other seven servers' cases are
  otherwise unchanged.
- No `docs/*.md` change is in scope for this row.

## Security considerations

- No command-allowlist entry, config path, or token appears in the new code.
- The fail-closed rule stays enforced: nothing in this file patches `init_sandbox` itself.

## Rollback considerations

- Revert this file together with row `07`. Reverting only this file leaves two tests failing against
  the fail-closed helper.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Guardrail suite green | `uv run pytest tests/mcp_servers/cicd/test_tool_server_layer_consistency.py` | 0 failures |
| Fail-closed rule still enforced | `uv run pytest tests/mcp_servers/shell/test_shell_security_validation.py` | passes |
| Static gates | `uv run ruff check tests/`, `uv run python tools/check_mock_patch_targets.py` | clean |

## Completion criteria

- `uv run pytest tests/mcp_servers/cicd/test_tool_server_layer_consistency.py` exits 0.
- No test in the file patches `init_sandbox` itself.
- No test in the file depends on the host having firejail installed.

## Out of scope

- `ShellPolicy`'s accepted backend values in `scripts/shared/protocols/shell.py` (row `07` enforces
  the rule at `init_sandbox()`).
- Any production module.
- The other seven servers' dispatch constructors.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update `_shell_dispatch()` per Procedure/Method/Details | Completed | 20261016-201939 | 20261016-201939 | added by Plan amendment after row `07` broke the two `[shell]` cases _shell_dispatch now configures sandbox_backend firejail and wraps only the ShellService construction in a patch of mcp_servers.shell.shell_service_static_helpers.shutil.which, so no assertion runs under a patched stdlib function. patch was added to the existing unittest.mock import line. No other constructor, parametrization, or assertion changed. |
| 2 | Confirm the guardrail suite and the new row `07` test file pass | Completed | 20261016-201939 | 20261016-201939 | uv run pytest tests/mcp_servers/cicd/test_tool_server_layer_consistency.py reports 62 passed and 0 failures, including both shell parametrized cases. tests/mcp_servers/shell/test_shell_security_validation.py also passes. |
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
- **Requirement ID**: `REQ-005` (Shell self-validation; guardrail test for the fail-closed `init_sandbox`)
- **Source issue**: `issues/done/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py`