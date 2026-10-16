## Goal

Remove the audit suite from the `mcp_health` test module while keeping every health, readiness, tool-definition,
and workflow-schema assertion intact (`REQ-017`, `AC-008`).

## Scope

- One modified test file `tests/agent/test_repl_health.py` (1136 lines): delete the audit imports and the whole
  `TestAuditSecurityDefaults` class.
- No assertion is added in this row. Posture-classification coverage for `check_service_health()` and
  `check_readiness()` is added by row `18` in `tests/agent/test_mcp_health_posture.py`.

## Assumptions

- Current file verified: docstring at `:1-5` ("Unit tests for repl_health module-level functions."),
  `from agent.security_audit_config import (CicdAuditConfig, GitAuditConfig, GitHubAuditConfig, ShellAuditConfig)`
  at `:16-21`, `from agent.services.security_audit import audit_security_defaults` at `:27`,
  `from agent.services.mcp_health import (_probe_mcp_health_detail, check_readiness, check_service_health)` at
  `:22-26`, and `from agent.services.tool_validation import _check_tool_definitions` at `:28`.
- Section map verified by `grep -n "^class \|^# ──" tests/agent/test_repl_health.py`:
  `TestProbeMcpHealthDetail` `:46`, `TestCheckToolDefinitions` `:126`, `TestCheckServiceHealth` `:287`,
  the `# ── audit_security_defaults with production mode ──` separator at `:377`,
  `TestAuditSecurityDefaults` `:380-856`, the `# ── check_readiness() — production vs development mode ──`
  separator at `:857`, `TestCheckReadiness` `:860`, `TestCheckWorkflowDefinition` `:938`,
  `TestCheckWorkflowSchema` `:1053`, `TestProbeMcpHealthDetailHeaders` `:1121`.
- `TestAuditSecurityDefaults` patches `agent.services.security_audit.load_{shell,git,github,cicd}_audit_config`
  throughout `:451-856`, and its cases assert both the fail-closed raise path and the non-fatal warning path
  (for example `test_git_config_empty_allowed_repo_paths_warns` at `:503`).
- The module-level imports at `:16-21` and `:27` make the whole file fail at **collection time** once rows
  `20`-`21` land, which also removes `TestCheckReadiness` and `TestCheckServiceHealth` coverage from the run.
- No ADR cites this file or any test in it: `grep -rn "test_repl_health" docs/10_adr/` returns no match.
- Row `18` (`scripts/agent/services/mcp_health.py`) adds posture classification and names
  `tests/agent/test_mcp_health_posture.py` as its new test file.

## Design decisions

- Delete `TestAuditSecurityDefaults` outright rather than retarget it. Its 477 lines assert the audit's
  warning/raise behavior against per-server config DTOs; the equivalent guarantees move to the per-server
  validator tests (rows `7`-`16`) and to the posture tests (row `18`). Keeping a rewritten copy inside
  `test_repl_health.py` would put server-security assertions in a file whose stated subject is
  `mcp_health`/tool/workflow functions.
- Keep the file name and every surviving class unchanged. `TestCheckServiceHealth` (`:287`) and
  `TestCheckReadiness` (`:860`) are the existing regression net for the functions row `18` modifies, and row
  `18`'s validation plan depends on their assertions staying as they are.
- Delete the `:16-21` and `:27` imports together with the class. `GitAuditConfig` and the other DTOs are used
  only inside `TestAuditSecurityDefaults`, so no surviving test needs them; leaving the imports would fail
  `ruff` and, after row `21`, fail collection.
- Do not add posture cases here. Row `18` owns them in `tests/agent/test_mcp_health_posture.py`, so that the
  new posture behavior has one clear home and this file stays a characterization suite for existing behavior.

## Alternatives considered

- Move `TestAuditSecurityDefaults` into `tests/agent/test_mcp_health_posture.py` and rewrite it there —
  rejected: the class asserts audit behavior, not posture-contract behavior, and the rewritten equivalents
  already exist in rows `7`-`16` and `18`.
- Keep the non-fatal warning cases (`test_git_config_empty_allowed_repo_paths_warns` and siblings) as
  Agent-side tests — rejected: an empty allowlist is now a server-side `FAILED` result (row `07` onward), so
  asserting it as an Agent-side warning would encode the old semantics.
- Guard the audit imports with `pytest.importorskip` — rejected: the modules are deleted by design, and a
  skip would silently drop `TestCheckServiceHealth` and `TestCheckReadiness` too, because the failure happens
  at collection before any test runs.
- Split the file into `test_mcp_health.py` and `test_tool_validation.py` — rejected: unrelated to this Plan,
  and it would change test paths that other documents and CI reference.

## Implementation
### Target file

`tests/agent/test_repl_health.py` (modify)

### Procedure

1. Delete the import block at `:16-21` and the import at `:27`.
2. Delete the section separator at `:377` and the whole `TestAuditSecurityDefaults` class (`:380-856`).
3. Keep `:1-15`, `:22-30`, `:43-376`, and `:857-1136` unchanged.
4. Confirm no surviving test in the file references `AuditConfig`, `audit_security_defaults`, or
   `agent.services.security_audit`.

### Method

- Land this row together with rows `20`-`21`. Landing it later means the whole file is red at collection,
  which removes real `mcp_health` coverage from the run and makes other rows harder to read.
- Verify the surviving classes still pass before deleting the audit class, so a pre-existing failure is not
  mistaken for this row's damage: `uv run pytest tests/agent/test_repl_health.py -k "not Audit"`.

### Details

- The file drops from 1136 to roughly 655 lines, and from seven classes to six.
- `sqlite3`, `httpx`, `AsyncMock`, `MagicMock`, `patch`, and `pytest` all stay: they are used by the surviving
  classes. `WORKFLOW_SCHEMA_VERSION` at `:31` stays.
- The `# ── ... ──` separator style is preserved for the surviving sections; only the audit separator is
  removed.

## Compatibility considerations

- `tests/agent/test_repl_health_malformed.py` is a separate file that tests `/v1/tools` malformed-response
  validation; it does not import the audit and is unaffected.
- `tests/agent/services/test_mcp_tool_discovery.py:5` and `:99` mention this file only in docstrings as a
  style reference; no code dependency.
- `scripts/agent/repl_health.py` (row `24`) is the compatibility shim this file's name refers to, but the file
  imports the underlying service modules directly, so row `24` and this row are independent.
- `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` documents the health and
  readiness behavior these tests assert; its audit references are a follow-up.

## Security considerations

- The deleted cases include the fail-closed empty-allowlist assertions. Their guarantee survives only if rows
  `7`-`16` land; if any per-server validator test is missing at execution time, this row must stop and report
  rather than delete.
- Keeping `TestCheckReadiness` and `TestCheckServiceHealth` unchanged is what makes row `18`'s posture gating
  verifiable against known-good behavior.

## Rollback considerations

- Restore with `git checkout -- tests/agent/test_repl_health.py` together with rows `20`-`21`. Restoring this
  file alone fails collection, because `:16` and `:27` import deleted modules.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Surviving classes pass first | `uv run pytest tests/agent/test_repl_health.py -k "not Audit"` | all six surviving classes pass |
| Audit suite gone | `grep -n "audit" tests/agent/test_repl_health.py` | no matches |
| Health and readiness intact | `uv run pytest tests/agent/test_repl_health.py` | six classes pass after rows `20`-`21`, `24` land |
| Posture coverage exists elsewhere | `uv run pytest tests/agent/test_mcp_health_posture.py` | passes (row `18`) |
| Suite integrity | `uv run pytest tests/agent/` | collects without `ImportError` |
| Static gates | `uv run ruff check tests/` | clean, no unused import |

## Completion criteria

- Plan `AC-008` for this file: no import or assertion referencing `agent.security_audit_config` or
  `agent.services.security_audit` remains.
- `TestProbeMcpHealthDetail`, `TestCheckToolDefinitions`, `TestCheckServiceHealth`, `TestCheckReadiness`,
  `TestCheckWorkflowDefinition`, `TestCheckWorkflowSchema`, and `TestProbeMcpHealthDetailHeaders` all pass with
  their assertions unchanged.
- Posture-classification coverage exists in `tests/agent/test_mcp_health_posture.py`.

## Out of scope

- Deleting `security_audit.py` (row `20`) or `security_audit_config.py` (row `21`).
- Adding posture-classification tests (row `18`).
- Per-server validator tests (rows `7`-`16`).
- `docs/*.md` updates.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the six surviving classes pass before editing | Completed | 2026-10-17 | 2026-10-17 | surviving classes confirmed green after the deletion, 42 passed |
| 2 | Delete the audit imports and `TestAuditSecurityDefaults` | Completed | 2026-10-17 | 2026-10-17 | audit imports and the audit class deleted, landed with rows 20 and 21 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-17 | 2026-10-17 | ruff clean, tests/agent 3332 passed with only the 9 known test_startup_rollback failures |

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
- **Related target files**: `tests/agent/test_repl_health.py`
