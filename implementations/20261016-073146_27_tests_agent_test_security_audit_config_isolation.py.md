## Goal

Keep the configuration-isolation regression test alive after the audit loader is deleted, and strengthen it
so it asserts that **no** Agent module imports MCP server config models (`REQ-017`, `AC-008`, ADR-002
`INV-01`).

## Scope

- One modified test file `tests/agent/test_security_audit_config_isolation.py` (198 lines): rewrite two
  tests in place, delete twelve loader-specific tests.
- The file is not deleted, because `docs/10_adr/adr_02_002_config-isolation.md:231` cites two of its tests
  and citation removal is an ERROR in `tools/check_adr_preservation.py:156-161`.

## Assumptions

- Current file verified: `_FORBIDDEN_SECURITY_IMPORTS` at `:10-15` (four `from mcp_servers.<server>.<models>`
  patterns), `_AUDIT_MODULE = "security_audit_config.py"` at `:16`, `_AGENT_DIR = pathlib.Path("scripts/agent")`
  at `:17`, `test_only_audit_module_imports_security_server_config` at `:20-32` (scans `scripts/agent/**/*.py`
  and skips `_AUDIT_MODULE`), twelve loader tests at `:38-181`
  (`test_load_{shell,git,github,cicd}_audit_config_{returns_none_on_import_error,raises_on_load_failure,success}`),
  and `test_audit_dtos_hold_no_secret_fields` at `:184-198` (asserts none of the four audit DTOs carry
  `auth_token`, `github_token`, `token`, `api_key`, `password`).
- ADR citation constraint: `docs/10_adr/adr_02_002_config-isolation.md:231` cites
  `tests/agent/test_security_audit_config_isolation.py::test_only_audit_module_imports_security_server_config`
  and `::test_audit_dtos_hold_no_secret_fields`. `tools/check_adr_preservation.py` reports
  `test citation removed` as ERROR with no override flag, and `tests/agent/test_security_audit_config_isolation.py`
  does not appear in that ADR's `Implementation References` bullet at `:324`, so the file may be rewritten
  as long as both test names remain.
- The twelve loader tests import `agent.security_audit_config` inside their bodies (`:40`, `:50`, `:57`,
  `:65`, `:78`, `:88`, `:95`, `:102`, `:113`, `:123`, `:132`, `:154`, `:164`, `:175`), so they raise
  `ImportError` at call time once row `21` deletes the module.
- `test_audit_dtos_hold_no_secret_fields` imports `agent.security_audit_config` at `:189`, so it also breaks
  unless rewritten.
- The new DTOs that replace the audit DTOs are `shared.security.result_dto.SecurityCheckStatus` (row `02`)
  and `shared.security.posture_contract.SecurityPosture` (row `03`).

## Design decisions

- Keep both cited test names and rewrite their bodies. Renaming either one removes an ADR citation and
  fails `tools/check_adr_preservation.py`, and there is no override flag in that tool
  (`tools/check_adr_preservation.py:260-268` exposes only `files`, `--base`, `--dir`).
- `test_only_audit_module_imports_security_server_config` becomes "no Agent module imports MCP server
  config models": delete the `_AUDIT_MODULE` exemption (`:16`, `:23-24`) so the scan covers every file
  under `scripts/agent/`. The name is retained as a stable citation anchor; a comment in the test body
  records that the exemption is gone. **Needs confirmation**: whether the project accepts the stale name,
  or prefers to change `tools/check_adr_preservation.py` to allow a citation rewrite, which is a tooling
  change outside this Plan.
- `test_audit_dtos_hold_no_secret_fields` is retargeted to the replacement DTOs: it enumerates the fields of
  `shared.security.result_dto` and `shared.security.posture_contract` dataclasses and asserts none of them
  is in the same secret-name set. The invariant ("the Agent's security DTOs carry posture fields only,
  never secrets") is unchanged; only the types under test change.
- Delete the twelve loader tests rather than rewrite them: each asserts a behavior of a deleted function
  (`ImportError -> None`, `RuntimeError` wrapping, field mapping), and the equivalent server-side behavior
  is asserted by the per-server validator tests in rows `7`-`16`.
- Keep `_FORBIDDEN_SECURITY_IMPORTS` aligned with the four modules listed in `.importlinter:74-77`, which
  row `25` keeps as a contract. Widening the scan to every `mcp_servers.*` model is recorded as a
  follow-up so the test and the contract stay in step. **Needs confirmation**.

## Alternatives considered

- Delete the whole file — rejected: it would remove two ADR citations and fail
  `tools/check_adr_preservation.py`, and it would delete the only regression test for the isolation
  invariant this Plan strengthens.
- Keep the twelve loader tests with `pytest.importorskip` guards — rejected: skipped tests assert nothing,
  and the module they skip on is deleted by design.
- Move the two cited tests into a new file and delete this one — rejected: the citation strings include the
  file path, so moving them is still a citation removal.
- Assert the invariant only through `lint-imports` and drop the test — rejected: `docs/10_adr/adr_02_002_config-isolation.md:231`
  marks this row `Blocking: Yes`, and a source-text scan catches imports that a contract scoped to four
  modules would miss.

## Implementation
### Target file

`tests/agent/test_security_audit_config_isolation.py` (modify)

### Procedure

1. Delete `_AUDIT_MODULE` (`:16`) and the `if py_file.name == _AUDIT_MODULE: continue` exemption
   (`:23-24`).
2. Update the assertion message in `test_only_audit_module_imports_security_server_config` so it names the
   rule as "no agent module imports MCP server config models", and add a one-line comment that the test
   name is retained for the ADR-002 citation.
3. Delete the twelve loader tests (`:38-181`) and the `MagicMock`/`patch` imports they alone use.
4. Rewrite `test_audit_dtos_hold_no_secret_fields` to enumerate the dataclasses exported by
   `shared.security.result_dto` and `shared.security.posture_contract` and assert no field name is in the
   secret-name set.
5. Keep `_FORBIDDEN_SECURITY_IMPORTS` and `_AGENT_DIR` unchanged.

### Method

- Land this row after rows `20`-`21` and `25`, so the scan passes against the post-removal tree rather
  than failing on the module being deleted mid-phase.
- Verify the ADR gate after the change: `uv run python tools/check_adr_preservation.py` must report no
  `test citation removed` finding for `adr_02_002_config-isolation.md`.

### Details

- The file drops from 198 lines to roughly 60 lines and from 14 tests to 2.
- `pathlib` stays (used by `_AGENT_DIR`); `dataclasses` moves from a function-local import (`:187`) to a
  module-level import; `MagicMock`/`patch`/`pytest` become unused once the loader tests are gone and their
  imports must be removed to keep `ruff` clean.
- The scan is CWD-relative (`pathlib.Path("scripts/agent")`), which matches how the suite is run from the
  repository root; do not convert it to an absolute path.

## Compatibility considerations

- `docs/10_adr/adr_02_002_config-isolation.md:231` prose ("Only the security audit loader imports MCP
  server configuration models, and the audit DTOs hold no secret fields") becomes stale; row `37` updates
  that table row's prose while keeping both citations. Removing the backtick token
  `` `agent/security_audit_config.py` `` from that ADR yields a WARNING
  (`tools/check_adr_preservation.py:181-185`) that needs a sentence-level mapping in the change report.
- `tests/agent/test_config_permission_cross_server.py` (row `28`) covers the neighboring `ConfigPermissionError`
  behavior; this row does not change it.
- No production code depends on this test file.

## Security considerations

- This row converts a permissive rule ("only the audit loader may import these models") into a prohibitive
  one ("no Agent module may"), which is the test-side expression of `INV-06`.
- Keeping the no-secret-field assertion matters: the new posture DTOs are the Agent's only view of server
  security state, and a token or secret path field entering one of them would leak server secrets into
  Agent logs and the posture payload.

## Rollback considerations

- Restore this file with `git checkout -- tests/agent/test_security_audit_config_isolation.py` together
  with rows `20`-`21` and `25`. Restoring it alone fails, because its loader tests import a deleted module.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Isolation scan passes post-removal | `uv run pytest tests/agent/test_security_audit_config_isolation.py` | both tests pass, no exemption in the scan |
| Scan actually bites | temporarily add `from mcp_servers.git.git_models import GitConfig` to any `scripts/agent/*.py`, run the test, then revert | test fails with the offending path in the message |
| No-secret DTO check | `uv run pytest tests/agent/test_security_audit_config_isolation.py::test_audit_dtos_hold_no_secret_fields` | passes against the row `02`/`03` DTOs |
| ADR citation gate | `uv run python tools/check_adr_preservation.py` | no `test citation removed` ERROR |
| Suite integrity | `uv run pytest tests/agent/` | collects without `ImportError` |
| Static gates | `uv run ruff check tests/` | clean, no unused import |

## Completion criteria

- Plan `AC-008` for the isolation regression: the test asserts that no module under `scripts/agent/`
  imports the four MCP server config models, and it passes.
- Both ADR-002 citations still resolve to existing tests.
- The no-secret-field invariant is asserted against the replacement posture DTOs.

## Out of scope

- Deleting `security_audit_config.py` (row `21`) or the `.importlinter` grant (row `25`).
- `docs/10_adr/adr_02_002_config-isolation.md` prose updates (row `37`).
- Widening `_FORBIDDEN_SECURITY_IMPORTS` beyond the four contract-listed modules (Needs-confirmation
  follow-up).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the `_AUDIT_MODULE` exemption | Pending | — | — | land after rows `20`-`21`, `25` |
| 2 | Delete the twelve loader tests | Pending | — | — | |
| 3 | Retarget `test_audit_dtos_hold_no_secret_fields` to the posture DTOs | Pending | — | — | depends on rows `02`, `03` |
| 4 | Confirm the stale-name decision with the user | Pending | — | — | Needs-confirmation |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Related target files**: `tests/agent/test_security_audit_config_isolation.py`
