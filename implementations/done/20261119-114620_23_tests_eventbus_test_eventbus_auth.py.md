## Goal
- Drop the plain assignment to `_ENVELOPE_SCHEMA_PATH` from the local-app fixture of the auth tests (REQ-003: no test sets the removed constant).

## Scope
**Release unit**: eventbus-supervision-and-cleanup

- In scope: one line in `tests/eventbus/test_eventbus_auth.py`. This file keeps its own document because both the `app.py` row and the `auth.py` row name it in `Related Tests`, so it is no one's companion.

## Assumptions
- The fixture assigns `eb_app._ENVELOPE_SCHEMA_PATH = schema_path` directly and then also sets `eb_app.get_schema_path`; the assignment does not fail after the constant is removed, but it would create a stale attribute (verified in Step 3a).
- The `get_schema_path` assignment is what the lifespan reads and stays.

## Design decisions
- Remove only the assignment line; keep the `get_schema_path` line and the rest of the fixture.

## Alternatives considered
N/A: a one-line removal.

## Implementation
### Target file
`tests/eventbus/test_eventbus_auth.py`

### Procedure
1. In the local-app fixture builder, delete the line `eb_app._ENVELOPE_SCHEMA_PATH = schema_path`.

### Method
- Leave every other line, including the `get_schema_path` lambda, unchanged.

### Details
- After this document and the seq 03 document, `rg "_ENVELOPE_SCHEMA_PATH" scripts tests` MUST find nothing.

## Compatibility considerations
N/A: test only.

## Security considerations
N/A: test only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run ruff format --check tests/eventbus/test_eventbus_auth.py` and `uv run ruff check tests/eventbus/test_eventbus_auth.py`; `uv run pytest tests/eventbus/test_eventbus_auth.py -q`; `rg "_ENVELOPE_SCHEMA_PATH" scripts tests`.

## Completion criteria
- The assignment is gone, the auth tests pass, and no reference to the constant remains in `scripts` or `tests`.

## Out of Scope
- Any other change to the auth tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the assignment line | Completed | 20261119-120211 | 20261119-120241 | Step 2 stale check clean; Step 3a: plain assignment verified; file clean at baseline Changed: tests/eventbus/test_eventbus_auth.py (assignment line removed). rg _ENVELOPE_SCHEMA_PATH scripts tests: none; mypy clean (571 files); 50 passed |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261119-120241 | 20261119-121150 | ruff, mypy pass; full suite once at end of unit End of unit: full suite 12918 passed 7 skipped 0 failed (not integration/production_paths_allowed/repo_scan); diff-cover 100% (37 lines); ADR-cited tests 52 passed; validation gates pass; ruff, mypy (571 files), lint-imports (6 kept), bandit, radon, vulture, suppression, compat shims, db separation clean |

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
- **Requirement ID**: `REQ-003` (no test references the removed constant)
- **Source issue**: issues/20261117-123017_adrchk017_eventbus-task-supervision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-113711_adrchk017_eventbus-task-supervision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-114620
- **Related target files**: `tests/eventbus/test_eventbus_auth.py`