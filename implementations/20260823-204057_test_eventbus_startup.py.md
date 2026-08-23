# Implementation Procedure: tests/eventbus/test_eventbus_startup.py

## Goal

Fix the identical broken import found in the sibling `test_eventbus_config.py`, which
also prevents this file's tests from running.

## Scope

**In-Scope**
- Change `from scripts.eventbus.config import (...)` to `from eventbus.config import
  (...)`, preserving the exact same imported names.

**Out-of-Scope**
- Any change to test logic, assertions, or test names.
- `scripts/eventbus/config.py` — not touched by this procedure.

## Assumptions

- **Added during implementation-procedure review**: this file was not named in the
  source plan's original Related target files/Affected areas, but was found to have
  the identical defect as `test_eventbus_config.py` via `grep -n "from scripts\."
  tests/eventbus/*.py`, which returns exactly these two files. The source plan has been
  corrected to add this file to Scope/Affected areas.
- `from eventbus.config import (...)` (no `scripts.` prefix) is the correct form —
  confirmed the same way as the sibling procedure: it matches every other
  `tests/eventbus/*.py` file's working convention under `PYTHONPATH=scripts`.

## Design decisions

- Single-line import fix, identical pattern to the sibling `test_eventbus_config.py`
  procedure — no broader change needed.

## Alternatives considered

- See the sibling `test_eventbus_config.py` procedure's Alternatives considered
  (adding `scripts/__init__.py` instead) — rejected for the same reason here.

## Implementation

### Target file
`tests/eventbus/test_eventbus_startup.py`

### Procedure
1. Locate the import block: `from scripts.eventbus.config import (...)`.
2. Change it to: `from eventbus.config import (...)`, keeping the same imported names
   unchanged.
3. Run `PYTHONPATH=scripts uv run pytest tests/eventbus/test_eventbus_startup.py -v`
   and confirm all tests in the file now collect and pass.

### Method
Single-line (or single-block) text substitution; no other line in the file changes.

### Details
- No fixture or test-body change needed — the existing tests (e.g.
  `test_is_public_host_0000`) already correctly exercise the imported names; they were
  simply never able to run due to the import error.

## Compatibility considerations

N/A: test-only file, no compatibility impact.

## Security considerations

N/A: test-only file, no security-relevant logic changed.

## Rollback considerations

- Trivially revertable: a single import-line change, independent of the sibling
  `test_eventbus_config.py` fix, though both should land together (same root cause,
  same source plan's acceptance criteria).

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/eventbus/test_eventbus_startup.py | Unit (collection + execution) | `PYTHONPATH=scripts uv run pytest tests/eventbus/test_eventbus_startup.py -v` | All tests collect and pass (0 collection errors) |

## Out of scope

- `tests/eventbus/test_eventbus_config.py` — covered by its own implementation
  procedure document.

## Execution Status

##### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| — | — | Pending | — | — | |

##### Blocker Log

| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

##### Work Items Created

| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A: not applicable in this phase
- Source requirement: N/A: not applicable in this phase
- Source plan: plans/20260820-103959_plan.md
- Source implementation procedure: N/A: not applicable in this phase
- Generated at: 20260823-204057
- Related target files: tests/eventbus/test_eventbus_startup.py
