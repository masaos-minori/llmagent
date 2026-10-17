## Goal

Keep the RAG-consistency timeout regression tests running after the audit step is removed from the startup
pipeline (`REQ-017`, `AC-008`).

## Scope

- One modified test file `tests/agent/test_startup_validation.py` (104 lines): delete one entry from the
  clean-pass mock set.
- No assertion changes.

## Assumptions

- Current file verified: docstring at `:1-6` ("Regression tests for REQ-002, REQ-003: Verify the RAG
  consistency check inside `StartupValidationPipeline.check_services()` ..."), `_make_ctx()` at `:23-28`
  (sets `ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION`, `ctx.cfg.memory.memory_embed_dim = 768`,
  `ctx.cfg.tool.tool_definitions_strict = False`), `_run_check_services()` at `:31-71` whose mock set at
  `:45-52` contains `"audit_security_defaults": MagicMock(return_value=[])` at `:46`, `_rag_outcomes()` at
  `:74-75`, and `TestRagConsistencyTimeout` at `:78` with `test_rag_check_timeout_enforced` at `:82` and
  `test_rag_check_succeeds_within_timeout` at `:96`.
- The mocks are applied as `patch(f"agent.startup_validation.{name}")` at `:55`. Once row `22` removes the
  `audit_security_defaults` import from `scripts/agent/startup_validation.py`, `unittest.mock.patch` raises
  `AttributeError: <module 'agent.startup_validation'> does not have the attribute 'audit_security_defaults'`
  for every test in this file.
- This file imports no audit symbol directly, so it does not fail at collection time; it fails at patch time,
  which is why it can land in the same commit as row `22` rather than before it.
- No ADR cites this file or any test in it: `grep -rn "test_startup_validation.py::" docs/` returns no match,
  and `docs/10_adr/adr_02_004_environment-failure-handling-policy.md:358` lists
  `tests/agent/shared/test_startup_validation_pipeline.py`, not this file.

## Design decisions

- Delete only the mock-set entry at `:46`. The two tests assert RAG timeout behavior, which this Plan does not
  change; the audit entry exists solely to let the real `check_services()` body run without touching real
  config files.
- Keep `ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION` at `:25`. It is read by surviving checks
  and by `SecurityProfile` typing at `:20`, not only by the audit, and removing it would change the profile
  the RAG assertions run under.
- Keep the mock set's remaining six entries unchanged, including `check_readiness`. Row `18` changes what
  `check_readiness()` does in production, but these tests replace it with a clean-pass `AsyncMock`, so the
  RAG assertions stay isolated from posture behavior.

## Alternatives considered

- Delete the file and re-add RAG timeout coverage elsewhere — rejected: `REQ-002`/`REQ-003` timeout behavior
  is unrelated to this Plan, and the file is the only place that drives the real `check_services()` body for
  the RAG path.
- Replace the audit entry with a posture mock so the file also exercises posture gating — rejected: that is
  row `18`'s test scope (`tests/agent/test_mcp_health_posture.py`), and mixing it here would make a RAG
  regression file depend on the new contract.
- Patch with `create=True` so the missing attribute is tolerated — rejected: `create=True` hides real drift
  between the mock set and the pipeline, which is exactly the failure this file is meant to surface.

## Implementation
### Target file

`tests/agent/test_startup_validation.py` (modify)

### Procedure

1. Delete `"audit_security_defaults": MagicMock(return_value=[])` at `:46`.
2. Keep `:1-45` and `:47-104` unchanged.

### Method

- Land this row in the same commit as row `22`. Landing it earlier is harmless (the entry still matches a
  real import); landing it later leaves the file failing with `AttributeError`.
- Confirm the failure mode before and after: before row `22` the suite passes with the entry; after row `22`
  without this row it fails with `AttributeError` naming `audit_security_defaults`.

### Details

- The file drops from 104 to 103 lines and the mock set from six entries to five.
- `MagicMock`, `AsyncMock`, `patch`, `ExitStack`, `HealthCheckResult`, `StartupCheckStatus`,
  `StartupValidationResult`, `SecurityProfile`, and `pytest` all stay in use.

## Compatibility considerations

- `tests/agent/test_startup.py` (row `30`), `tests/agent/test_startup_severity_classification.py` (row `33`),
  `tests/agent/test_startup_memory_failures.py` (row `34`), and
  `tests/agent/shared/test_startup_validation_pipeline.py` (row `35`) use the same patch-by-name pattern and
  must land in the same phase.
- `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` documents the RAG check's
  timeout behavior; unchanged by this row.

## Security considerations

- No security guarantee changes in this row. Keeping the RAG timeout assertions intact preserves `REQ-002`'s
  rule that a timed-out non-mandatory check is skipped rather than fatal, which is the counterpart of the
  fail-closed rules this Plan strengthens.

## Rollback considerations

- Revert this commit together with row `22`. Reverting row `32` alone fails with `AttributeError` on
  `agent.startup_validation.audit_security_defaults`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| RAG timeout regression | `uv run pytest tests/agent/test_startup_validation.py` | two tests pass after row `22` lands |
| No stale patch target | `grep -n "audit" tests/agent/test_startup_validation.py` | no matches |
| Patch targets match the pipeline | `uv run pytest tests/agent/test_startup_validation.py -x` | no `AttributeError` |
| Suite integrity | `uv run pytest tests/agent/` | collects without `ImportError` |
| Static gates | `uv run ruff check tests/` | clean |

## Completion criteria

- Plan `AC-008` for this file: the mock set contains no `audit_security_defaults` entry.
- Both `REQ-002`/`REQ-003` assertions pass unchanged against the post-removal pipeline.

## Out of scope

- Removing the pipeline step (row `22`).
- Posture gating tests (row `18`).
- The pipeline-aggregation file (row `35`).
- `docs/*.md` updates.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the audit entry from the mock set | Completed | 2026-10-17 | 2026-10-17 | landed with row 22 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-17 | 2026-10-17 | ruff clean, tests/agent 3332 passed with only the 9 known test_startup_rollback failures |

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
- **Related target files**: `tests/agent/test_startup_validation.py`
