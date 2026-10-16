## Goal

Keep the memory-failure severity tests running after the audit step is removed from the startup pipeline
(`REQ-017`, `AC-008`).

## Scope

- One modified test file `tests/agent/test_startup_memory_failures.py` (243 lines): delete one entry from the
  clean-pass mock set and correct the check count in the helper docstring.
- No assertion changes.

## Assumptions

- Current file verified: docstring at `:1` ("Behavior-lock tests proving each memory-failure path's documented
  severity is produced under its condition."); the `_run_check_services` helper docstring at `:39-41` says
  "clean-pass mocks for all 8 checks, overridden per-test via kwargs (named after the
  `agent.startup_validation` import site)"; the mock set at `:45-56` contains
  `"audit_security_defaults": MagicMock(return_value=[])` at `:46`; `mocks.update(overrides)` at `:57` lets
  each test replace an entry.
- The mocks are applied as `patch(f"agent.startup_validation.{name}")`. Once row `22` removes the
  `audit_security_defaults` import from `scripts/agent/startup_validation.py`, `unittest.mock.patch` raises
  `AttributeError` for every test in this file.
- This file imports no audit symbol directly, so it fails at patch time rather than at collection time.
- No ADR cites this file or any test in it: `grep -rn "test_startup_memory_failures" docs/` returns no match.
- The file's subject is the memory/embedding-dimension failure paths, which this Plan does not change.

## Design decisions

- Delete only the mock-set entry at `:46`. The memory-failure assertions are unrelated to `REQ-017`; the audit
  entry exists only so the real `check_services()` body can run with everything else neutralized.
- Update the "all 8 checks" phrase at `:39` to the count row `22` produces. The phrase is a claim about the
  pipeline, and a stale count is the kind of drift that makes a behavior-lock file misleading when it is read
  next to `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`.
- Keep the `overrides` mechanism unchanged. Tests that override `check_readiness` continue to work, because
  row `18` changes the real function and these tests replace it with a mock.

## Alternatives considered

- Leave the entry in place and patch with `create=True` — rejected: `create=True` hides the drift between the
  mock set and the pipeline, which is the exact signal this file relies on.
- Delete the file — rejected: its subject is memory-failure severity, which survives this Plan unchanged.
- Add a posture override case here — rejected: posture coverage belongs to row `18`'s
  `tests/agent/test_mcp_health_posture.py`; this file asserts memory paths only.

## Implementation
### Target file

`tests/agent/test_startup_memory_failures.py` (modify)

### Procedure

1. Delete `"audit_security_defaults": MagicMock(return_value=[])` at `:46`.
2. Update the check count in the helper docstring at `:39` to the post-removal count.
3. Keep `:1-38` and `:40-45`, `:47-243` unchanged.

### Method

- Land this row in the same commit as row `22`, together with rows `30`, `32`, `33`, and `35`, which use the
  same patch-by-name pattern.
- Confirm the failure mode: after row `22` without this row, every test in the file fails with
  `AttributeError` naming `audit_security_defaults`.

### Details

- The file drops from 243 to 242 lines and the mock set from six entries to five.
- `AsyncMock`, `MagicMock`, `patch`, `ExitStack`, `HealthCheckResult`, `ServiceWarning`,
  `StartupCheckOutcome`, and `pytest` all stay in use.

## Compatibility considerations

- `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` documents the memory-check
  severity this file locks; unchanged by this row.
- `tests/agent/test_startup.py` (row `30`), `tests/agent/test_startup_validation.py` (row `32`),
  `tests/agent/test_startup_severity_classification.py` (row `33`), and
  `tests/agent/shared/test_startup_validation_pipeline.py` (row `35`) must land in the same phase.

## Security considerations

- No security guarantee changes in this row. The memory checks are non-security checks; the fail-closed
  security paths remain asserted by rows `29`, `33`, and `35`.

## Rollback considerations

- Revert this commit together with row `22`. Reverting row `34` alone fails with `AttributeError` on
  `agent.startup_validation.audit_security_defaults`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Memory severity tests pass | `uv run pytest tests/agent/test_startup_memory_failures.py` | all cases pass after row `22` lands |
| No stale patch target | `grep -n "audit" tests/agent/test_startup_memory_failures.py` | no matches |
| Docstring count matches the pipeline | compare the helper docstring at `:39` with the sources row `22` emits | identical count |
| Suite integrity | `uv run pytest tests/agent/` | collects without `ImportError` |
| Static gates | `uv run ruff check tests/` | clean |

## Completion criteria

- Plan `AC-008` for this file: the mock set contains no `audit_security_defaults` entry.
- Every memory-failure severity assertion passes unchanged.
- The helper docstring's check count matches the post-removal pipeline.

## Out of scope

- Removing the pipeline step (row `22`).
- Posture gating tests (row `18`).
- The severity matrix file (row `33`).
- `docs/*.md` updates.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the audit entry from the mock set | Pending | — | — | land with row `22` |
| 2 | Correct the check count in the helper docstring | Pending | — | — | |
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
- **Related target files**: `tests/agent/test_startup_memory_failures.py`
