## Goal

Remove the test file whose entire subject is the deleted audit API, while keeping its fail-closed
invariant covered elsewhere (`REQ-017`, `AC-008`).

## Scope

- Delete `tests/agent/test_audit_security_failures.py` (162 lines): four tests that patch
  `agent.services.security_audit.load_*_audit_config` and assert `audit_security_defaults()` re-raises.
- No replacement test is added in this row; the invariant is re-based by row `29` and by the per-server
  validator tests from rows `7`-`16`.

## Assumptions

- Current file verified: `tests/agent/test_audit_security_failures.py` (162 lines) — docstring at `:1`
  ("Tests for audit_security_defaults() fail-closed exception handling."), `from unittest.mock import patch`
  at `:3`, `import pytest` at `:5`, `from agent.security_audit_config import (...)` at `:6-10`, the
  `_SHELL_OK`/`_GIT_OK`/`_GITHUB_OK` fixtures, and the four tests
  `test_shell_config_failure_production_raises` at `:38`, `test_git_config_failure_production_raises` at
  `:55`, `test_github_config_failure_production_raises` at `:76`, `test_cicd_config_failure_production_raises`
  at `:101`. Each patches `agent.services.security_audit.load_*_audit_config` with a `RuntimeError` whose
  message starts `"Security audit: failed to load ... config: ..."` and asserts the call re-raises.
- Every test in the file imports `audit_security_defaults` inside the test body
  (`:39`, `:56`, `:77`, `:102`), and the module-level import at `:6-10` imports the audit DTOs, so the
  file fails at **collection time** once row `21` deletes `agent/security_audit_config.py`.
- No ADR cites this file: `grep -rn "test_audit_security_failures" docs/` returns no match, so
  `tools/check_adr_preservation.py`'s citation rule is not engaged by deleting it.
- The invariant the file encodes is ADR-004 `INV-01`/`INV-02`/`INV-07`
  (`docs/10_adr/adr_02_004_environment-failure-handling-policy.md:215-221`): a config-load failure is
  Fail-Closed, not downgraded by environment.
- `tests/agent/test_failure_handling_policy_cross_cutting.py` (row `29`) encodes the same ADR-004
  invariants and is the surviving home for them.

## Design decisions

- Delete the file rather than rewrite it. Its four tests assert the exception behavior of a function that
  no longer exists; a rewritten file would contain tests for a symbol, which is what `REQ-017` removes.
- The Plan's frozen table lists this row's action as `Modify`; the correct action is `Delete`, and the
  Plan row is amended before execution.
- Land the replacement coverage before this deletion. Row `29`'s retargeted ADR-004 tests and the
  per-server validator tests must exist first, so the tree never has a window where the fail-closed
  invariant has no test.
- Do not move these four cases into `tests/agent/test_failure_handling_policy_cross_cutting.py` as
  audit-shaped copies. The replacement asserts the same invariant through surviving mechanisms
  (`ConfigLoader` restriction errors, `ProductionConfigValidator`, posture validation), not through the
  removed API.

## Alternatives considered

- Keep the file and rewrite each test against a per-server loader — rejected: the four loaders are
  Agent-side constructs; the equivalent server-side behavior is already tested by the new per-server
  validator suites in rows `7`-`16`, and duplicating it in `tests/agent/` would re-create an Agent-side
  view of server config.
- Keep the file as an empty placeholder with a skip marker — rejected: a skipped file reports coverage it
  does not provide.
- Convert the four tests into `xfail` markers during Phase 2 — rejected: `xfail` hides a removed
  capability instead of removing it, and the module-level import at `:6-10` fails collection before any
  marker is evaluated.

## Implementation
### Target file

`tests/agent/test_audit_security_failures.py` (delete)

### Procedure

1. Confirm row `29`'s retargeted ADR-004 tests exist and pass.
2. Confirm no other file imports this test module: `grep -rn "test_audit_security_failures" tests/`
   returns no match.
3. Delete the file.

### Method

- Delete in the same commit as rows `20`-`21`, or after them. Deleting earlier leaves tests that still
  pass against a still-present module, which is harmless; deleting later is blocked only by collection
  errors, which is the expected signal.
- No test is moved into this file.

### Details

- The file has no `conftest` dependency and no shared fixture other than its own module-level DTO
  constants, so deleting it cannot affect another test module.
- `tests/agent/test_repl_health.py` (row `31`) contains a larger, overlapping audit suite
  (`TestAuditSecurityDefaults` at `:380-856`); removing it is row `31`'s job, not this row's.

## Compatibility considerations

- Collection-time `ImportError` is the failure mode if this row lands after row `21` and before this
  deletion: `tests/agent/test_audit_security_failures.py:6` imports a deleted module, which fails the
  whole test run rather than a single test.
- `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` documents the startup
  severity table that these tests cross-reference; the audit row there is a follow-up.
- No ADR or `docs/*.md` file cites this test file, so no documentation citation breaks.

## Security considerations

- Deleting tests is only acceptable because the invariant survives: ADR-004 `INV-01`/`INV-02`/`INV-07`
  remain asserted by row `29`, and the per-server fail-closed behaviors are asserted by rows `7`-`16`.
- If at execution time any of those replacements is missing, this row must stop and report rather than
  delete.

## Rollback considerations

- Restore with `git checkout -- tests/agent/test_audit_security_failures.py` together with rows `20`-`21`,
  which restore the module the tests import. Restoring this file alone fails collection.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Replacement coverage present first | `uv run pytest tests/agent/test_failure_handling_policy_cross_cutting.py` | passes with the retargeted cases (row `29`) |
| File gone | `ls tests/agent/test_audit_security_failures.py` | no such file |
| No dangling reference | `grep -rn "test_audit_security_failures" tests/ docs/` | no matches |
| Suite integrity | `uv run pytest tests/agent/` | passes after rows `20`-`21`, `26`-`29` land together |
| ADR gate | `uv run python tools/check_adr_preservation.py` | no citation-removal ERROR |

## Completion criteria

- Plan `AC-008` for tests: no test module imports `agent.security_audit_config` or
  `agent.services.security_audit`.
- ADR-004 `INV-01`/`INV-02`/`INV-07` remain asserted by a surviving test module.
- `uv run pytest tests/agent/` collects without `ImportError`.

## Out of scope

- Deleting `security_audit.py` (row `20`) or `security_audit_config.py` (row `21`).
- Rewriting `tests/agent/test_failure_handling_policy_cross_cutting.py` (row `29`),
  `tests/agent/test_security_audit_config_isolation.py` (row `27`),
  `tests/agent/test_config_permission_cross_server.py` (row `28`), or
  `tests/agent/test_repl_health.py` (row `31`).
- `docs/*.md` updates.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Amend the Plan row action from `Modify` to `Delete` | Pending | — | — | required before execution |
| 2 | Confirm row `29` replacement coverage passes | Pending | — | — | gate for deletion |
| 3 | Delete `tests/agent/test_audit_security_failures.py` | Pending | — | — | land with rows `20`-`21` |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Related target files**: `tests/agent/test_audit_security_failures.py`
