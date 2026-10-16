## Goal

Keep the cross-server configuration-isolation regression suite intact after the cross-config read is
removed, and replace the one audit-specific case with a guard that stops the loader from coming back
(`REQ-017`, `AC-008`, ADR-002 `INV-02`).

## Scope

- One modified test file `tests/agent/test_config_permission_cross_server.py` (76 lines): replace
  `test_security_audit_config_blocked_in_restricted_agent_process` with a loader-absence guard; keep the
  other four tests unchanged.

## Assumptions

- Current file verified: docstring at `:1` ("Verify ConfigLoader.restrict_to() prevents cross-server config
  file access."), `from shared.config_errors import ConfigPermissionError` at `:6`,
  `from shared.config_loader import ConfigLoader` at `:7`, the `reset_config_loader` autouse fixture at
  `:10-13` (clears `ConfigLoader._allowed_files`), `test_cross_server_config_load_raises_config_permission_error`
  at `:16-20`, `test_own_config_load_allowed` at `:23-31`, `test_unrestricted_allows_any_file` at `:34-41`,
  `test_security_audit_config_blocked_in_restricted_agent_process` at `:44-50` (the only audit-dependent
  test; it imports `agent.security_audit_config.load_shell_audit_config` at `:47` and expects
  `RuntimeError, match="not permitted"`), and `test_falsy_own_config_file_blocks_cross_server_access` at
  `:53-76`.
- `docs/10_adr/adr_02_002_config-isolation.md:232` cites
  `tests/agent/test_config_permission_cross_server.py::test_cross_server_config_load_raises_config_permission_error`,
  and `:324` lists the file in an `Implementation References` bullet. `tools/check_adr_preservation.py:148-161`
  makes removing either an ERROR, so both must stay intact.
- `test_security_audit_config_blocked_in_restricted_agent_process` is not cited by any ADR:
  `grep -rn "test_security_audit_config_blocked" docs/` returns no match.
- The Agent-side restriction lives at `scripts/agent/context.py:311` (`ConfigLoader.restrict_to("agent.toml")`)
  and is already asserted by `tests/agent/test_context.py::TestAgentContextConfigRestriction::test_restrict_to_called_unconditionally`
  (`tests/agent/test_context.py:47`).
- The `RuntimeError, match="not permitted"` expectation at `:49` comes from the audit loader's own
  restriction message, not from `ConfigLoader`; `ConfigLoader` raises `ConfigPermissionError`.

## Design decisions

- Replace the audit case with `test_agent_has_no_cross_config_audit_loader()`, which asserts
  `importlib.util.find_spec("agent.security_audit_config") is None`. The removed test's real value was
  "an Agent-restricted process cannot reach a server config file"; after row `21` the stronger and
  directly checkable statement is that the code path no longer exists. This also guards against a future
  change reintroducing a loader module.
- Keep the four surviving tests byte-identical. `test_cross_server_config_load_raises_config_permission_error`
  is an ADR citation, and the other three assert `ConfigLoader` semantics that this Plan does not change.
- Do not merge the replacement into `test_cross_server_config_load_raises_config_permission_error`. They
  assert different things: one asserts the loader rejects an unauthorized file, the other asserts the
  unauthorized code path is absent.
- Keep the `reset_config_loader` fixture unchanged: the replacement test does not load configs, but the
  fixture's job is to keep the class-level allowlist from leaking between tests in the module.

## Alternatives considered

- Delete `:44-50` with no replacement — rejected: the file would lose the only assertion tied to
  `REQ-017`'s end state, and nothing would fail if someone re-added a cross-config loader.
- Rewrite `:44-50` to call `ConfigLoader.load("shell_mcp_server.toml")` under `restrict_to("agent.toml")`
  — rejected: it duplicates `:16-20` exactly.
- Rewrite it to construct `AgentContext` and then attempt a server-config load — rejected: `AgentContext`
  construction is heavy, already covered by `tests/agent/test_context.py:47`, and adds no new guarantee.
- Keep the test and point it at a per-server loader — rejected: the per-server loaders run inside server
  processes and are covered by rows `7`-`16`, not by `tests/agent/`.

## Implementation
### Target file

`tests/agent/test_config_permission_cross_server.py` (modify)

### Procedure

1. Delete `test_security_audit_config_blocked_in_restricted_agent_process` (`:44-50`).
2. Add `test_agent_has_no_cross_config_audit_loader()` in its place, asserting
   `importlib.util.find_spec("agent.security_audit_config") is None`, with a docstring naming `REQ-017`.
3. Add `import importlib.util` at the top of the import block (`:3-7`).
4. Keep `:1`, `:6-7`, `:10-13`, `:16-20`, `:23-31`, `:34-41`, and `:53-76` unchanged.

### Method

- Land this row after row `21`. Before row `21` lands, the new guard fails by design, which is the correct
  ordering signal rather than a reason to defer the change.
- Verify the ADR citation is untouched: `git diff` for this file must show no change to `:16`'s function
  name.

### Details

- The file stays at five tests and roughly 78 lines.
- `importlib.util` must be imported as the module (`import importlib.util`), not as
  `from importlib import util`, to match the repository's import style and keep `ruff`'s isort rules clean.
- The guard is a static existence check and does not import the module, so it cannot raise `ImportError`.

## Compatibility considerations

- `docs/10_adr/adr_02_002_config-isolation.md:232` and `:324` reference this file and one of its test
  names; both remain valid.
- `docs/10_adr/adr_02_002_config-isolation.md:231`'s row is row `37`'s concern, not this row's.
- No production module imports this test file.

## Security considerations

- The replacement guard makes `REQ-017`'s end state testable: a reintroduced Agent-side loader would fail
  the suite instead of passing review unnoticed.
- The four unchanged tests continue to assert that a restricted process cannot read another process's
  configuration file, which is ADR-002 `INV-01`/`INV-02`.

## Rollback considerations

- Restore with `git checkout -- tests/agent/test_config_permission_cross_server.py` together with row `21`.
  Restoring only this file fails, because `:47` imports a module that row `21` deletes.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Guard passes after removal | `uv run pytest tests/agent/test_config_permission_cross_server.py` | five tests pass |
| Guard actually bites | temporarily create `scripts/agent/security_audit_config.py`, run the test, then revert | the guard fails |
| ADR-cited test intact | `uv run pytest "tests/agent/test_config_permission_cross_server.py::test_cross_server_config_load_raises_config_permission_error"` | passes |
| ADR gate | `uv run python tools/check_adr_preservation.py` | no citation-removal ERROR |
| Suite integrity | `uv run pytest tests/agent/` | collects without `ImportError` |
| Static gates | `uv run ruff check tests/` | clean |

## Completion criteria

- Plan `AC-008` for this suite: no test in the file imports `agent.security_audit_config`, and the file
  asserts that the module does not exist.
- The ADR-002-cited test name and the four unchanged assertions are preserved.
- `uv run pytest tests/agent/test_config_permission_cross_server.py` passes.

## Out of scope

- Deleting `security_audit_config.py` (row `21`).
- Rewriting `tests/agent/test_security_audit_config_isolation.py` (row `27`).
- `docs/10_adr/adr_02_002_config-isolation.md` updates (row `37`).
- Any change to `shared/config_loader.py` semantics.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the audit case with the loader-absence guard | Pending | — | — | land after row `21` |
| 2 | Confirm the four unchanged tests are untouched | Pending | — | — | ADR citation |
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
- **Requirement ID**: `REQ-017` (remove Agent-side cross-config audit)
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `tests/agent/test_config_permission_cross_server.py`
