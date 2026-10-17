## Goal

Remove the startup security-audit step from the validation pipeline, so the Agent's security input is
the postures published by the servers rather than an Agent-side audit of their configuration
(`REQ-017`, `AC-008`).

## Scope

- One modified module `scripts/agent/startup_validation.py`: delete the `security_audit` import and the
  `# 1. Security audit` step, and update the two docstrings that name the audit.
- No new step is added here: posture validation reaches the pipeline through `check_readiness()`
  (row `18`), which this module already calls at `:81-91`.

## Assumptions

- Current module verified: `scripts/agent/startup_validation.py` (172 lines) — module docstring
  `:1-7` names "security audit"; `from agent.services.security_audit import audit_security_defaults` at
  `:19`; `from agent.services.mcp_health import check_readiness` at `:16`; `check_services()` at `:48`
  with docstring "Probe LLM/Embed health, validate tool definitions, and audit security defaults.";
  the audit step at `:57-68` (`audit_security_defaults(ctx)` call at `:59`, `add_warning("security_audit", ...)`
  at `:61`, `add_ok("security_audit")` at `:62`, `add_fatal("security_audit", str(exc), remediation=...)`
  at `:64-68` with the remediation string at `:67`); the `mcp_auth` step at `:71-81`; the `readiness`
  step at `:84-93`; MCP tool discovery at `:99-121`.
- The local `logger` (`:50-52`) is still used at `:162` and `:167`, so it stays.
- Startup ordering requirement from the issue
  (`issues/done/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md:100-112`): security
  posture validation must complete before Tool Discovery registers tools. The existing order already
  satisfies it once row `18` puts posture validation inside `check_readiness()`, because `readiness`
  (`:84-93`) runs before `mcp_tool_discovery` (`:99-121`).
- `tests/agent/test_startup.py:878` asserts the exact remediation string
  `"Fix MCP server auth_token or sandbox config."`, and `tests/agent/shared/test_startup_validation_pipeline.py`
  patches `agent.services.startup_validation.audit_security_defaults` in four places (row `35`).

## Design decisions

- Delete the step rather than replace it with a posture step in this module. Row `18` makes
  `check_readiness()` raise on Safety/Integrity failures, and the existing `except Exception` at
  `:92-93` already converts that into `pipeline.add_fatal("readiness", ...)`. Adding a second posture
  step here would create two pipeline sources reporting the same fact.
- The `security_audit` source name disappears from `StartupValidationResult` entirely. No suppression
  or alias is introduced: `startup_reporter.py:75` and `:83` are row `23`'s targets, and re-mapping
  `security_audit` onto another source would keep a name that no longer describes a check.
- The remediation string at `:67` disappears with the step. Its replacement is row `18`'s
  `check_readiness()` message, which names the server key, the failure class, and the reason code.
  `tests/agent/test_startup.py:878` is updated by row `30`.
- The `mcp_auth` step (`:71-81`) is kept unchanged. It is the Agent's own `agent.toml`-based check that
  every configured MCP server has a token, which is not a cross-config read and is not part of the
  audit API.
- The `# 1.` numbering in the step comments becomes a gap (`1b`, `2`, `4`, `5`, `5b`, `6` already skip).
  Comments are renumbered only if that stays a comment-only change; otherwise the existing gaps are
  left as they are. **Needs confirmation**: whether the project wants the comments renumbered.

## Alternatives considered

- Add a `mcp_posture` step here that calls `collect_server_postures()` directly — rejected: it would
  duplicate the `readiness` probe, and `startup_reporter.py` would then print two lines for one set of
  servers. Recorded as a follow-up if a separate Readiness Summary line is wanted.
- Keep the step but make it consume postures — rejected: that is row `17` plus row `18`, and this
  module is the pipeline assembler, not a validator.
- Keep the step as a no-op placeholder so `startup_reporter.py` needs no change — rejected: `REQ-017`
  removes the audit, and a placeholder source that always reports `ok` would make the Readiness Summary
  claim a check that does not run.

## Implementation
### Target file

`scripts/agent/startup_validation.py` (modify)

### Procedure

1. Delete the import at `:19`.
2. Delete the audit step at `:57-68`, including its `# 1. Security audit` comment.
3. Update the module docstring (`:3`) and the `check_services()` docstring (`:48`) so neither names
   the audit.
4. Keep `mcp_auth`, `readiness`, `mcp_tool_discovery`, `routing_drift`, `routing_safety_tiers`,
   `rag_consistency`, and the `logger` unchanged.
5. Add the posture-gate wiring at the discovery step: collect gates with `collect_server_postures(ctx)`
   (row `18`) before `McpToolDiscoveryService(ctx).discover_all()` (`:100`) and pass them as
   `McpToolDiscoveryService(ctx, posture_gates=gates)`. This is the only production construction site of
   `McpToolDiscoveryService`, so it is where `REQ-014`'s gate reaches `RuntimeToolRegistry` (row `50`).

### Method

- Land this row together with rows `20` and `24`; a leftover import of a deleted module fails at import
  time, before any test runs.
- The deletion changes no control flow around the remaining steps: the audit step had no dependency on
  or effect on later steps except through `pipeline`.
- The posture-gate wiring is additive: `posture_gates` defaults to `None` (row `50`), so the step's
  finding routing (`:104-112`) and every existing test of it are untouched until gates are passed.
- Gates are collected in their own call rather than read from `check_readiness()`'s result, because
  `check_readiness()` raises when posture errors exist (`agent/services/mcp_health.py:118-126`) and the
  discovery step still runs after that `except` (`:91-92`); the gate must be available on the failure
  path, which is exactly the path `REQ-014` exists to cover. **Needs confirmation**: whether the project
  accepts the second `/health` probe pass this adds, or prefers carrying gates on `ServiceHealthResult`
  (row `18`) and reading them here.

### Details

- The module drops from 172 to about 158 lines.
- `StartupCheckStatus` (`:20`) is still used by the discovery step (`:108-112`), so the import stays.
- `tests/agent/shared/test_startup_validation_pipeline.py` patches `check_readiness`
  (`:133-137` and siblings) and `audit_security_defaults`; only the audit patches are removed (row `35`).

## Compatibility considerations

- Removing the `security_audit` source changes `StartupValidationResult` contents, which
  `startup_reporter.py:75` (`_count_by_status(pipeline, "security_audit")`) and the `Security audit:`
  summary line at `:83` read. Without row `23`, that line always reports `FAIL` for a source that never
  exists, so rows `22` and `23` must land together.
- Test impact (row `30`, `32`, `35`): `tests/agent/test_startup.py` audit cases (`:860-918` region,
  including the remediation assertion at `:878`), `tests/agent/test_startup_validation.py` audit cases,
  and the four `audit_security_defaults` patches in `tests/agent/shared/test_startup_validation_pipeline.py`.
- `tests/agent/test_startup_severity_classification.py` keeps its `readiness` cases; the severity
  mapping for `readiness` is unchanged, only the messages it receives change (row `33`).
- No `docs/*.md` change is in scope for this row; `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`
  severity table is a follow-up.

## Security considerations

- `REQ-017` / Plan `INV-06`: the pipeline stops running a cross-config audit, and the fail-closed
  security gate moves to posture validation in `readiness`.
- The removal must not weaken startup gating: `mcp_auth` stays, and posture failures become `readiness`
  fatals through row `18`. If row `18` has not landed, this row leaves the startup path with no security
  validation, so the Plan's phase order (Phase 1 servers, then Phase 2 Agent) is a hard prerequisite.

## Rollback considerations

- Revert this commit together with rows `20`, `21`, `23`, `24`, `25`, and the test rows `26`-`35`.
  Reverting row `22` alone fails, because the module it imports is deleted by row `20`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Audit source absent | `uv run pytest tests/agent/test_startup.py` | no `security_audit` source in the pipeline result |
| Pipeline step order preserved | `uv run pytest tests/agent/shared/test_startup_validation_pipeline.py` | `readiness` still runs before `mcp_tool_discovery` |
| Readiness fatal path | same existing test file | a `check_readiness()` failure still produces a `readiness` FATAL |
| MCP auth check intact | `uv run pytest tests/agent/test_startup.py` | `mcp_auth` FATAL cases unchanged |
| Severity mapping | `uv run pytest tests/agent/test_startup_severity_classification.py` | `readiness` severity rows unchanged |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean, no unused import |

## Completion criteria

- Plan `AC-008`: the pipeline contains no `security_audit` source and no Agent-side audit call.
- `readiness` still runs before `mcp_tool_discovery`, preserving the issue's ordering requirement.
- `mcp_auth` behavior is unchanged.

## Out of scope

- Deleting `security_audit.py` (row `20`) or `security_audit_config.py` (row `21`).
- Posture collection and classification (row `18`).
- Readiness Summary rendering (row `23`).
- Test updates (rows `30`, `32`, `35`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the import and the audit step | Completed | 2026-10-17 | 2026-10-17 | audit import and the security audit step removed, mcp_auth step kept |
| 2 | Update the two docstrings | Completed | 2026-10-17 | 2026-10-17 | — |
| 3 | Confirm step-comment renumbering decision | Completed | 2026-10-17 | 2026-10-17 | user decision: keep the existing step-comment numbering gaps |
| 4 | Pass posture gates into `McpToolDiscoveryService` at `:100` | Completed | 2026-10-17 | 2026-10-17 | posture_gates = await collect_server_postures(ctx) inside the existing discovery try |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-17 | 2026-10-17 | ruff clean, mypy 423 files, lint-imports 6 kept 0 broken, tests/agent 3332 passed with only the 9 known test_startup_rollback failures, validated only after rows 30 to 35 landed |

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
- **Source issue**: `issues/done/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/agent/startup_validation.py`
