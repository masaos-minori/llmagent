## Goal
Add the new guard fixture to the required-fixture manifest so a silent removal of it is detected (`REQ-004`).

## Scope
- One tuple entry in `REQUIRED_AUTOUSE_FIXTURES`.

## Assumptions
- `tests/conftest.py` defines `_forbid_production_paths` (new) as an `@pytest.fixture(autouse=True)` function (sibling procedure), which is what `extract_autouse_fixture_names` detects.

## Design decisions
- Add only the new load-bearing fixture; do not retrofit other fixtures (out of scope).

## Alternatives considered
N/A: one entry.

## Implementation
### Target file
`tools/check_conftest_integrity.py`

### Procedure
1. Append `"_forbid_production_paths"` to `REQUIRED_AUTOUSE_FIXTURES`.
2. Run the checker and its test.

### Method
- Edit the tuple that currently lists `_reset_tool_registry` and `_reset_web_search_health_and_metrics`; keep the comment above it unchanged.

### Details
- Apply `routing.md` Adding a new tool validation: ruff format and check, `uv run mypy tools/check_conftest_integrity.py`, `uv run bandit tools/check_conftest_integrity.py`.

## Compatibility considerations
The checker fails if the conftest no longer defines the fixture, which is the intent.

## Security considerations
N/A: static check only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_conftest_integrity.py`
- `uv run pytest tests/tools/test_check_conftest_integrity.py -q`
- `uv run ruff check tools/check_conftest_integrity.py` and `uv run mypy tools/check_conftest_integrity.py`

## Completion criteria
- The manifest lists the new fixture and the checker and its test pass against the updated conftest.

## Out of scope
- Other fixtures
- Changing the checker's logic

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the manifest entry | Completed | 20261019-140621 | 20261019-140621 |  |
| 2 | Run the checker, its test, and the tool validation sequence | Completed | 20261019-140621 | 20261019-140621 |  |

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
- **Requirement ID**: `REQ-004` (register the new autouse fixture)
- **Source issue**: issues/20261019-131051_testiso001_tests-write-to-production-state.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-131444_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-132033
- **Related target files**: tools/check_conftest_integrity.py