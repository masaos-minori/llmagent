## Goal
Add a regression test to `tests/agent/test_import_smoke.py` that fails if any of the twelve removed names is restored on the `agent` package, or if importing `agent.context` loads `agent.repl` through a package-level import (REQ-002).

## Scope
- In: `tests/agent/test_import_smoke.py` only; two new test functions.
- Out: `scripts/agent/__init__.py` (row 01), the Glossary row (row 03), any other test.

## Assumptions
- Row 01 is applied first, so the new tests pass; before it they must fail (they lock the removal).
- The module is 28 lines and already holds import smoke tests using `# noqa: F401 — ...` justifications.

## Design decisions
- The side-effect check runs in a subprocess (`sys.executable -I -c ...`): within the pytest process other tests may already have imported `agent.repl`, which would make an in-process `sys.modules` check meaningless.
- The name-absence check is in-process (`hasattr`) and parametrized over the twelve names, so a restored name is reported by name.

## Alternatives considered
N/A: an in-process `sys.modules` check was rejected for the reason above.

## Implementation
### Target file
`tests/agent/test_import_smoke.py`

### Procedure
1. Append a module-level constant listing the twelve names.
2. Append `test_agent_package_does_not_reexport_components` (new) (parametrized over the names): `import agent` then assert `not hasattr(agent, name)`; also assert `getattr(agent, "__all__", ())` contains none of them.
3. Append `test_importing_agent_context_does_not_load_agent_repl` (new): run a subprocess with `PYTHONPATH` set to the repository `scripts/` directory that imports `agent.context` and exits non-zero when `"agent.repl"` is in `sys.modules`; assert return code 0.

### Method
- `scripts/` path: derive from `Path(__file__).resolve().parents[2] / "scripts"`.
- Subprocess: `subprocess.run([sys.executable, "-I", "-c", code], env={**os.environ, "PYTHONPATH": str(scripts)}, capture_output=True, text=True, check=False)`; the assertion message includes `stderr`.
- Use the existing `from __future__ import annotations` header; add `import os, subprocess, sys`, `from pathlib import Path`, and `import pytest` at the top.
- If any `# noqa`/`# nosec` is needed for `subprocess`, include a rule code and an em-dash justification (`tools/check_suppression_justification.py`).

### Details
- Names: `AuditEventEmitter`, `BgTaskMonitor`, `ConversationStateManager`, `LlmTurnExecutor`, `AgentREPL`, `ReplInputLoop`, `ResourceShutdownCoordinator`, `SessionPersister`, `SignalHandler`, `StartupBanner`, `WalCheckpointManager`, `WorkflowEngineAdapter`.
- Update the module docstring to mention the new lock, keeping the existing text.

## Compatibility considerations
N/A: test-only change.

## Security considerations
N/A: the subprocess runs a fixed code string with no external input.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_import_smoke.py -v` passes after row 01; with row 01 reverted (stash) the new tests fail.
- `uv run ruff format tests/agent/test_import_smoke.py`, `uv run ruff check tests/agent/test_import_smoke.py`, `uv run python tools/check_suppression_justification.py`.
- Full `uv run pytest` still passes.

## Completion criteria
- The twelve-name test and the side-effect test exist and pass on the current tree (AC-2).
- Restoring any one re-export makes the matching test fail (demonstrated once by temporarily restoring one import).

## Out of Scope
- Changing existing tests in the file; adding tests elsewhere.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the parametrized name-absence test and the subprocess side-effect test (REQ-002) | Completed | 20261021-094624 | 20261021-095312 | Changed: tests/agent/test_import_smoke.py (+13 tests: 12 parametrized names, 1 subprocess side-effect test) |
| 2 | Run the new tests, demonstrate failure with a temporarily restored import, then the validation sequence (`rules/toolchain.md`) | Completed | 20261021-094624 | 20261021-095312 | ruff/suppression check pass; test_import_smoke 17 passed; with the old __init__ restored 13 failed (restored after); full suite 9678 passed 14 skipped. bandit on the test file reports only Low-severity B101/B603 (scripts/ is the gate scope). |

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
- **Requirement ID**: `REQ-002` (locking regression test)
- **Source issue**: `issues/20261020-122918_compat003_remove-the-agent-package-re-exports-kept-for-backward-compatibility.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261020-235040_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-093528
- **Related target files**: `tests/agent/test_import_smoke.py`