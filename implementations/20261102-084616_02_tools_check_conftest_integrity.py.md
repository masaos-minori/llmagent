## Goal

Require the new session fixture in the conftest integrity checker so removing the detection cannot pass silently (`REQ-003`: checker fails when the detection is removed).

## Scope

- Add one name to `REQUIRED_AUTOUSE_FIXTURES` in `tools/check_conftest_integrity.py`.
- Checker tests are procedure 03; the fixture itself is procedure 01.

## Assumptions

- Plan overlaps: `tools/check_plan_target_overlaps.py` (2026-11-02) names no overlap for this Plan; no sibling Plan targets this file: compatible.
- Verified 2026-11-02: `REQUIRED_AUTOUSE_FIXTURES` currently holds the three names `_reset_tool_registry`, `_reset_web_search_health_and_metrics`, `_forbid_production_paths`; `extract_autouse_fixture_names` matches any `@pytest.fixture(..., autouse=True)` call, so a session-scoped autouse fixture is recognized.
- The name `_guard_production_db_files` is created by procedure 01 (earlier `seq`); it exists when `code-implementation` executes this row.
- `tools/TOOL_DESCRIPTIONS.md` describes the manifest generically (example only), so it needs no change and no tool is added or removed.

## Design decisions

- Append the name to the tuple (a hardcoded manifest by design, see the module docstring); no logic change.

## Alternatives considered

- N/A: the manifest is the checker's established mechanism (hook-based detection was rejected in the Plan Design).

## Implementation
### Target file
`tools/check_conftest_integrity.py`

### Procedure
1. Append `"_guard_production_db_files"` as the fourth entry of `REQUIRED_AUTOUSE_FIXTURES`.

### Method
- Keep the comment above the tuple; it already tells authors to extend the list for a new load-bearing fixture.

### Details
- Order the entry after `_forbid_production_paths`; the fixture name must match procedure 01 exactly.

## Compatibility considerations

- N/A: the checker runs as a pre-commit hook and reports a finding if `tests/conftest.py` lacks the name, so procedures 01 and 02 must land together.

## Security considerations

- N/A: read-only checker, no new input handling.

## Rollback considerations

- N/A: revert the commit (together with procedure 01).

## Validation plan

- `uv run python tools/check_conftest_integrity.py` (no findings once procedure 01 is applied).
- `uv run ruff format tools/check_conftest_integrity.py`; `uv run ruff check tools/check_conftest_integrity.py`; `uv run mypy tools/check_conftest_integrity.py`; `uv run bandit tools/check_conftest_integrity.py`.

## Completion criteria

- `REQUIRED_AUTOUSE_FIXTURES` contains `_guard_production_db_files`, and the checker reports no finding on the updated `tests/conftest.py`.

## Out of Scope

- Hook inspection in the checker (only the UNK-01 fallback would need it); changes to `tools/TOOL_DESCRIPTIONS.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_guard_production_db_files` to `REQUIRED_AUTOUSE_FIXTURES` | Pending | — | — | |
| 2 | Run the checker, ruff, mypy, and bandit on the file | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (checker requires the new detection)
- **Source issue**: issues/20261030-191351_flowimp006_suite-production-guard.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-075648_flowimp006_suite-production-guard.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-084616
- **Related target files**: `tools/check_conftest_integrity.py`
