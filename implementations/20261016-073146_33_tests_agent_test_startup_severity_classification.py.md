## Goal

Keep the startup severity matrix accurate after the audit step is removed, and preserve the ADR-cited
`mcp_auth` test unchanged (`REQ-017`, `AC-008`, ADR-007 `INV-09`).

## Scope

- One modified test file `tests/agent/test_startup_severity_classification.py` (599 lines): delete the two
  `security_audit` severity cases and the audit entry in the clean-pass mock set, and re-base the documented
  check list in the module docstring.
- No other test in the file changes.

## Assumptions

- Current file verified: docstring at `:1-7` states "for all 8 checks run by `_check_services()`:
  security_audit, embedding_dimensions, readiness, tool_definitions, routing_drift, routing_safety_tiers,
  routing_drift_live, rag_consistency"; the clean-pass mock set contains
  `"audit_security_defaults": MagicMock(return_value=[])` at `:53`; the patch-namespace comment at `:91-93`
  uses `agent.services.security_audit` as its example; `TestCheckServicesSeverityClassification` starts at
  `:115`; the `# ── security_audit ──` separator is at `:120` with
  `test_security_audit_fatal_when_audit_raises` at `:123-137` and
  `test_security_audit_warning_and_ok_both_recorded_when_non_fatal` at `:138-154`; the `# ── mcp_auth ──`
  separator is at `:156` with `test_mcp_auth_fatal_when_any_server_missing_token` at `:165`,
  `test_mcp_auth_ok_when_all_servers_have_token` at `:178`, and
  `test_mcp_auth_fatal_lists_all_offending_servers` at `:190`.
- `docs/10_adr/adr_02_007_http-mcp-adoption-and-stdio-non-support.md:261` cites
  `tests/agent/test_startup_severity_classification.py::TestCheckServicesSeverityClassification::test_mcp_auth_fatal_when_any_server_missing_token`.
  `tools/check_adr_preservation.py:156-161` reports a removed citation as ERROR with no override flag, so the
  class name and that test name must survive.
- The tests patch by name at `agent.startup_validation.<name>` (patch loop at `:98`), so the audit entry at
  `:53` raises `AttributeError` once row `22` removes the import.
- The `readiness` cases at `:206-255` mock `agent.startup_validation.check_readiness` directly, so row `18`'s
  posture gating inside the real `check_readiness()` does not change their assertions.
- No ADR cites the two `security_audit` tests: `grep -rn "test_security_audit_fatal_when_audit_raises" docs/`
  returns no match.

## Design decisions

- Delete the two `security_audit` cases with the pipeline step. They assert how the pipeline classifies an
  audit `RuntimeError` and an audit warning list; after row `22` neither input exists, and a rewritten case
  would assert a source name that no longer appears in `pipeline.outcomes`.
- Do not rename or repurpose the ADR-cited test. Its name, class, and assertions stay byte-identical, which
  is what keeps `docs/10_adr/adr_02_007_*:261` valid.
- Re-base the docstring check list at `:5-6` to the post-removal set produced by row `22`, and state the
  count as the number of checks the pipeline actually runs. The list is the human-readable index into the
  file's sections; leaving `security_audit` in it would advertise a section that no longer exists.
- Update the `:91-93` comment example to a surviving module (`agent.services.mcp_health`). The comment's point
  is about patch namespace, not about the audit, so the example must simply name a module that still exists.
- Do not add a posture-specific `readiness` case here. Row `18` adds posture coverage in
  `tests/agent/test_mcp_health_posture.py`; this file's role is the severity mapping of the pipeline, and its
  existing `readiness` cases already cover FATAL-by-raise and WARNING-by-issues.

## Alternatives considered

- Convert the two audit cases into `readiness` cases — rejected: `test_readiness_fatal_via_production_mode_raise`
  at `:206` already asserts FATAL-by-raise for `readiness`, so the conversion would duplicate it and remove
  the only record that the audit source ever had a documented severity.
- Keep the audit cases and add a permanent `security_audit` no-op source to the pipeline — rejected: row `22`
  removes the source, and a no-op source would make the severity matrix assert a placeholder.
- Rename the ADR-cited test to a posture-oriented name — rejected: renaming removes an ADR citation and fails
  `tools/check_adr_preservation.py`, and the tool exposes no override flag (`tools/check_adr_preservation.py:260-268`).
- Leave the docstring list unchanged — rejected: the file's own docstring would claim coverage of a check it
  no longer runs, which is a stale claim of the kind `tools/check_docs_consistency.py` is meant to catch.

## Implementation
### Target file

`tests/agent/test_startup_severity_classification.py` (modify)

### Procedure

1. Delete `"audit_security_defaults": MagicMock(return_value=[])` at `:53`.
2. Delete the `# ── security_audit ──` separator at `:120` and both tests at `:123-154`.
3. Update the docstring list at `:5-6` to the post-removal check set and its count.
4. Replace `agent.services.security_audit` in the comment at `:92` with `agent.services.mcp_health`.
5. Keep `:156-599` unchanged, including the class name at `:115` and the test at `:165`.

### Method

- Land this row in the same commit as row `22`. Before row `22` the audit entry still matches a real import;
  after row `22` without this row the whole class fails with `AttributeError`.
- Confirm the ADR citation still resolves after the edit: `uv run pytest "tests/agent/test_startup_severity_classification.py::TestCheckServicesSeverityClassification::test_mcp_auth_fatal_when_any_server_missing_token"`.

### Details

- The file drops from 599 to roughly 560 lines, and the class from 27 tests to 25.
- The section separator style (`# ── name ──`) is preserved for the surviving sections; only the audit
  separator is removed, so the `mcp_auth` separator at `:156` becomes the first section.
- `AsyncMock`, `MagicMock`, `patch`, `ExitStack`, `HealthCheckResult`, and `StartupCheckStatus` all stay in use.

## Compatibility considerations

- `docs/10_adr/adr_02_007_http-mcp-adoption-and-stdio-non-support.md:261` stays valid. Row `40` updates that
  ADR's prose about the audit, not this citation.
- `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`'s severity table is the
  document this file cross-references; its `security_audit` row is a follow-up, not this row's edit.
- `tests/agent/test_startup.py` (row `30`) contains near-duplicate audit severity cases; both must land in the
  same phase so the two files describe the same pipeline.

## Security considerations

- The ADR-007 `INV-09` guarantee (startup is fatal when any MCP server lacks an auth token) is asserted by the
  preserved test, and row `18`'s posture gating adds a second layer rather than replacing it.
- Removing the audit severity cases does not remove fail-closed coverage: `mcp_auth`, `readiness`,
  `mcp_tool_discovery`, `routing_drift`, and `routing_safety_tiers` cases all remain.

## Rollback considerations

- Revert this commit together with row `22`. Reverting row `33` alone fails with `AttributeError` on
  `agent.startup_validation.audit_security_defaults`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Severity matrix passes | `uv run pytest tests/agent/test_startup_severity_classification.py` | all remaining cases pass after row `22` lands |
| ADR-cited test intact | `uv run pytest "tests/agent/test_startup_severity_classification.py::TestCheckServicesSeverityClassification::test_mcp_auth_fatal_when_any_server_missing_token"` | passes |
| Audit cases gone | `grep -n "security_audit" tests/agent/test_startup_severity_classification.py` | no matches |
| Docstring matches reality | compare the docstring list at `:5-6` with the sources row `22` emits | identical set |
| ADR gate | `uv run python tools/check_adr_preservation.py` | no citation-removal ERROR for `adr_02_007_*` |
| Static gates | `uv run ruff check tests/` | clean |

## Completion criteria

- Plan `AC-008` for this file: no `security_audit` source or `audit_security_defaults` mock remains.
- The ADR-007 citation resolves to an existing, passing test.
- The docstring's documented check list matches the pipeline that row `22` produces.

## Out of scope

- Removing the pipeline step (row `22`).
- Posture gating tests (row `18`).
- The pipeline-aggregation file (row `35`).
- `docs/10_adr/adr_02_007_http-mcp-adoption-and-stdio-non-support.md` updates (row `40`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the audit entry from the mock set | Pending | — | — | land with row `22` |
| 2 | Delete the two `security_audit` cases and their separator | Pending | — | — | |
| 3 | Re-base the docstring check list and the comment example | Pending | — | — | |
| 4 | Confirm the ADR-007 citation still resolves | Pending | — | — | ERROR-level constraint |
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
- **Related target files**: `tests/agent/test_startup_severity_classification.py`
