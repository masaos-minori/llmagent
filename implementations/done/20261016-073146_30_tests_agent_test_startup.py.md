## Goal

Keep the startup-pipeline assertions that transitively depend on the audit working after the audit step is
removed, without weakening any severity or remediation guarantee (`REQ-017`, `AC-008`).

## Scope

- One modified test file `tests/agent/test_startup.py` (892 lines): drop the audit entry from the clean-pass
  mock set, delete the two `security_audit` severity cases, re-base the remediation test onto a surviving
  FATAL source, and update the two comments that name the audit.
- No production behavior changes in this row; row `22` removes the pipeline step.

## Assumptions

- Current file verified: the severity cross-reference comment block at `:136-141` states "for all 8 checks
  run by `_check_services()`: security_audit, embedding_dimensions, readiness, tool_definitions,
  routing_drift, routing_safety_tiers, routing_drift_live, rag_consistency"; the clean-pass mock set
  contains `"audit_security_defaults": MagicMock(return_value=[])` at `:171`; the patch-namespace comment at
  `:208-211` uses `agent.services.security_audit` as its example; the `security_audit` severity cases are
  `test_security_audit_fatal_when_audit_raises` at `:240-254` and
  `test_security_audit_warning_and_ok_both_recorded_when_non_fatal` at `:256-271`;
  `TestCheckServicesFatalErrorMessageWithRemediation` starts at `:862`, and
  `test_fatal_error_message_includes_remediation` at `:866-878` drives a FATAL through
  `audit_security_defaults=MagicMock(side_effect=RuntimeError(...))` at `:871-873` and asserts
  `"Fix MCP server auth_token or sandbox config." in str(exc)` at `:878`.
- The remediation string it asserts is produced at `scripts/agent/startup_validation.py:67`, which row `22`
  deletes.
- Surviving FATAL-with-remediation sources after row `22`: `mcp_auth`
  (`scripts/agent/startup_validation.py:71-81`, remediation "Set a non-empty auth_token (via environment
  variable) for every MCP server before startup.") and `readiness` (row `18` posture failures).
- `test_fatal_error_message_format_with_multiple_outcomes` at `:880-892` already drives its FATAL through
  `mcp_auth` and needs no change.
- `docs/10_adr/adr_02_004_environment-failure-handling-policy.md:358` lists
  `tests/agent/test_startup.py` in an `Implementation References` bullet; `tools/check_adr_preservation.py:148-154`
  makes changing that bullet an ERROR, so the file must keep its path and name.
- No ADR cites a test name in this file: `grep -rn "test_startup.py::" docs/` returns no match.

## Design decisions

- Delete the two `security_audit` severity cases rather than rewrite them. They assert how the pipeline
  classifies an audit raise and an audit warning list; after row `22` neither input exists. The severity
  classification itself remains covered by `tests/agent/test_startup_severity_classification.py` (row `33`)
  and `tests/agent/shared/test_startup_validation_pipeline.py` (row `35`) for the surviving sources.
- Re-base `test_fatal_error_message_includes_remediation` onto `mcp_auth` instead of deleting it. The test's
  purpose is REQ-001's guarantee that a FATAL carries a remediation string; keeping it against a surviving
  source preserves that guarantee, and `mcp_auth` is the closest surviving analogue (it is the check that
  already covers the missing-auth-token case the audit case simulated).
- Update the asserted remediation text to the `mcp_auth` string rather than matching a substring that could
  disappear. Matching the full literal is deliberate: the test's value is that the exact operator-facing
  text is present.
- Update the `:136-141` check list to the post-removal set and the `:208-211` comment to a surviving module
  example (`agent.services.mcp_health`). Leaving either comment naming the audit would make the file
  describe a pipeline that no longer exists.
- Keep the mock-set pattern (`patch(f"agent.startup_validation.{name}")`) unchanged; only the audit entry is
  removed. Patching a name that no longer exists raises `AttributeError`, which is the failure mode this row
  prevents.

## Alternatives considered

- Rewrite the two audit severity cases as `readiness` cases — rejected: `tests/agent/test_startup_severity_classification.py`
  already owns the per-source severity matrix, and duplicating `readiness` cases here would create two
  places that must be kept in sync.
- Keep the audit cases and add a `security_audit` shim to the pipeline — rejected: row `22` removes the
  source, and a shim that always reports `ok` would make the severity tests assert a placeholder.
- Delete `test_fatal_error_message_includes_remediation` — rejected: it is the only test that proves FATAL
  messages carry remediation text, which is a REQ-001 guarantee unrelated to the audit.
- Match the remediation assertion with a looser predicate such as `assert "auth_token" in str(exc)` —
  rejected: a loose match stops detecting an operator-facing message change, which is what the test exists
  to detect.

## Implementation
### Target file

`tests/agent/test_startup.py` (modify)

### Procedure

1. Delete `"audit_security_defaults": MagicMock(return_value=[])` from the mock set at `:171`.
2. Delete `test_security_audit_fatal_when_audit_raises` (`:240-254`) and
   `test_security_audit_warning_and_ok_both_recorded_when_non_fatal` (`:256-271`), including the
   `# ── security_audit ──` section comment at `:238`.
3. Rewrite `test_fatal_error_message_includes_remediation` (`:866-878`) to drive the FATAL through
   `mcp_auth` (a server entry with `auth_token=""`) and assert the `mcp_auth` remediation string.
4. Update the check list in the comment at `:140-141` and the module example in the comment at `:210`.
5. Keep every other test in the file unchanged.

### Method

- Land this row together with row `22`. Landing it earlier leaves an audit entry in a mock set that still
  matches a real import; landing it later produces `AttributeError` from patching a removed name.
- Verify the re-based remediation test against the real string in `scripts/agent/startup_validation.py`,
  not against a copy pasted from this document.

### Details

- The file drops from 892 to roughly 855 lines.
- `_run_check_services`'s docstring at `:166-169` says "clean-pass mocks for all 8 checks"; update the
  count with the comment at `:140-141` so the two statements agree.
- The `security_audit` section separator style (`# ── name ──`) is reused by the surviving sections, so
  removing one separator must not disturb the neighbors.

## Compatibility considerations

- `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`'s severity table is the
  document this file cross-references; its `security_audit` row is a follow-up, not this row's edit.
- `tests/agent/test_startup_severity_classification.py` (row `33`) and
  `tests/agent/test_startup_memory_failures.py` (row `34`) carry the same mock-set pattern and must land in
  the same phase.
- `docs/10_adr/adr_02_004_environment-failure-handling-policy.md:358` must remain unchanged.

## Security considerations

- The remediation guarantee is a security-operations property: an operator seeing a FATAL must be told how
  to fix it. Re-basing rather than deleting keeps that property tested.
- Removing the audit severity cases does not remove fail-closed coverage, because `mcp_auth` and `readiness`
  cases remain and row `29` re-bases the policy-level assertions.

## Rollback considerations

- Revert this commit together with row `22`. Reverting row `30` alone fails with `AttributeError` on
  `agent.startup_validation.audit_security_defaults`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Mock set matches the pipeline | `uv run pytest tests/agent/test_startup.py` | passes after row `22` lands, no `AttributeError` |
| Remediation guarantee intact | `uv run pytest tests/agent/test_startup.py::TestCheckServicesFatalErrorMessageWithRemediation` | passes against the `mcp_auth` remediation string |
| Audit cases gone | `grep -n "security_audit" tests/agent/test_startup.py` | no matches |
| Multiple-FATAL formatting | `uv run pytest tests/agent/test_startup.py::TestCheckServicesFatalErrorMessageWithRemediation::test_fatal_error_message_format_with_multiple_outcomes` | passes unchanged |
| ADR gate | `uv run python tools/check_adr_preservation.py` | no finding for `adr_02_004_*` |
| Static gates | `uv run ruff check tests/` | clean |

## Completion criteria

- Plan `AC-008` for this file: no reference to `audit_security_defaults` or the `security_audit` source
  remains.
- The FATAL-remediation guarantee is still asserted against a surviving source.
- The documented check list in the comments matches the pipeline row `22` produces.

## Out of scope

- Removing the pipeline step (row `22`).
- The severity matrix file (row `33`) and the pipeline-aggregation file (row `35`).
- `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` updates (follow-up).
- `docs/10_adr/adr_02_004_*` updates (row `39`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the audit entry from the mock set | Completed | 2026-10-17 | 2026-10-17 | landed with row 22 |
| 2 | Delete the two `security_audit` severity cases | Completed | 2026-10-17 | 2026-10-17 | — |
| 3 | Re-base the remediation test onto `mcp_auth` | Completed | 2026-10-17 | 2026-10-17 | re-based onto mcp_auth, the remediation string read from scripts/agent/startup_validation.py |
| 4 | Update the two audit-naming comments and the check count | Completed | 2026-10-17 | 2026-10-17 | comment list restated to the 6 pipeline sources the file actually asserts, embedding_dimensions and routing_drift_live are stale names that no longer exist |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-17 | 2026-10-17 | ruff clean, tests/agent 3332 passed with only the 9 known test_startup_rollback failures |

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
- **Related target files**: `tests/agent/test_startup.py`
