## Goal

Resolve the inconsistency between the docstring claim ("All required services are non-None") and the defensive null checks in ReadinessReporter by enforcing the invariant via assertion.

## Scope

- Modify `scripts/agent/startup_reporter.py`: add assertion in `AgentContext.services_required` property OR remove redundant defensive null checks
- Modify `scripts/agent/context.py`: read-only verification of services_required property

## Assumptions

- Option A (enforce invariant) aligns with Issue 10's approach of validating at construction time
- The invariant can realistically be guaranteed since factory.py always provides non-None values for required services
- Removing defensive null checks is safe because the invariant will be enforced at construction time

## Design decisions

- Enforce the invariant via assertion in `AgentContext.services_required` property (Option A preferred)
- Remove redundant defensive null checks in `report_readiness()` after invariant enforcement
- Use AssertionError which is caught by test suites but not pro

## Alternatives considered

- Using `unittest.TestCase.assertRaises` — pytest's `raises` is more concise
- Testing via integration with real service injection — too brittle, slow

## Implementation

### Target file

`tests/agent/test_startup_reporter.py`

### Procedure

Create a new test file with regression tests locking the CURRENT behaviour of
`ReadinessReporter.report_readiness()` after the ReadinessReporter refactor
(`bdd64049`). See Source-verified outcome below for why the originally proposed
assertion-based / defensive-check design was superseded.

### Method

1. Create `tests/agent/test_startup_reporter.py`
2. Add regression test: `report_readiness(pipeline)` emits a single "Readiness Summary:" warning (REQ-003)
3. Add regression test: invariant enforced at access time — `RuntimeError` propagates when services unset (REQ-003)

### Details

```python
"""Regression tests for ReadinessReporter.report_readiness().

Locks the current behaviour after the ReadinessReporter refactor (bdd64049):
report_readiness(pipeline) aggregates pipeline outcomes and emits a single
"Readiness Summary:" warning. It returns None (never a dict) and performs no
defensive null handling — the invariant is enforced at access time by the
AgentContext.services_required property, which raises RuntimeError.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from agent.startup_reporter import ReadinessReporter


def _empty_pipeline() -> MagicMock:
    pipeline = MagicMock()
    pipeline.outcomes = []
    return pipeline


class _CtxWithRaisingServices:
    """Context whose services_required property enforces the invariant."""

    def __init__(self) -> None:
        self.cfg = SimpleNamespace(mcp=SimpleNamespace(mcp_servers={}))

    @property
    def services_required(self) -> object:
        raise RuntimeError(
            "AgentContext.services not initialized — call build_agent_context() first"
        )


def test_report_readiness_emits_readiness_summary() -> None:
    """REQ-003: report_readiness aggregates the pipeline and warns once."""
    ctx = MagicMock()
    ctx.cfg.mcp.mcp_servers = {}
    ctx.services_required = MagicMock()
    ctx.services_required.runtime_tools.unavailable_servers = frozenset()

    view = MagicMock()
    reporter = ReadinessReporter(ctx, view)

    reporter.report_readiness(_empty_pipeline())

    assert view.write_warning.call_count == 1
    message = str(view.write_warning.call_args[0][0])
    assert "Readiness Summary:" in message
    assert "Service readiness:" in message


def test_report_readiness_propagates_when_services_uninitialized() -> None:
    """REQ-003: invariant enforced at access time — RuntimeError propagates."""
    ctx = _CtxWithRaisingServices()
    view = MagicMock()
    reporter = ReadinessReporter(ctx, view)

    with pytest.raises(RuntimeError, match="not initialized"):
        reporter.report_readiness(_empty_pipeline())
```

### Source-verified outcome

Adversarial verification (workflow Step 3a) found the originally proposed design
does not match current source and was superseded before this workflow ran:

- `startup_reporter.py` was refactored into the `ReadinessReporter` class
  (`bdd64049`). `report_readiness(self, pipeline)` now aggregates pipeline
  outcomes and emits ONE `"Readiness Summary:"` warning via
  `view.write_warning(...)`. It returns `None` (never a dict) and performs NO
  defensive null handling.
- The invariant is enforced at **access time** by
  `AgentContext.services_required` (context.py:336), which raises `RuntimeError`
  (not `AssertionError`) when unset, and at **construction time** by
  `AppServices.__init__` (context.py:270-280, commit `10308ed7`).
- Therefore the two originally proposed tests were wrong against current source:
  - `test_readiness_with_invariant_enforced` called `report_readiness()` with no
    args → TypeError (missing `pipeline`); the `patch.object(..., side_effect=AssertionError)`
    target does not exist.
  - `test_readiness_with_defensive_checks_present` asserted
    `result["status"] == "unavailable"` / `"No services configured"`, but
    `report_readiness` returns `None` and no such graceful path exists.
- Import path corrected: `from scripts.agent.startup_reporter` →
  `from agent.startup_reporter` (per `tests/conftest.py`, which prepends
  `scripts/` to `sys.path`; existing tests import `from agent.*`).

Corrected implementation locks the single surviving scenario (invariant
enforced) with the two tests above. REQ-003 is satisfied by verifying consistent
current behaviour.

## Compatibility considerations

N/A: This is a new test file, no compatibility concerns.

## Security considerations

N/A: Tests do not introduce security risks.

## Rollback considerations

Delete the test file if the startup_reporter change is reverted.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/agent/test_startup_reporter.py | Unit test — verify readiness reporting consistency | uv run pytest tests/agent/test_startup_reporter.py | New tests pass |

## Completion criteria

- [ ] Test verifies consistent behavior under both scenarios (REQ-003)
- [ ] All new tests pass when run individually

## Out of scope

- Modifying `startup_reporter.py` (handled in separate document)
- Modifying `context.py` (handled in separate document)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261005-232402 | 20261005-232402 | Created tests/agent/test_startup_reporter.py (2 tests) locking CURRENT report_readiness behaviour; original assertion-based design was superseded by bdd64049 refactor (see Source-verified outcome). |
| 2 | Add or update tests per Validation plan | Completed | 20261005-232402 | 20261005-232402 | New file tests/agent/test_startup_reporter.py added (2 tests). 52 passed/1 skipped alongside test_startup.py + test_context.py. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261005-232402 | 20261005-232402 | pytest 52 passed/1 skipped; ruff clean on new file. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261005-232402 | 20261005-232402 | N/A: docs out of scope per Compatibility/Out of scope. |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261004-143010_rr011_services_invariant_uncertainty.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-182818_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-195948
- **Related target files**: tests/agent/test_startup_reporter.py