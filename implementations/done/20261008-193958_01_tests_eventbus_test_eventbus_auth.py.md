## Goal
Cut the two 60-second waits in `TestSubscribeAuth` by setting a 1-second SSE idle timeout, and tighten the first test's bound (REQ-001 to REQ-003 of the Plan).

## Scope
- Only `tests/eventbus/test_eventbus_auth.py`; no other file is modified by this procedure.

## Assumptions
- UNK-02 resolved: `cls.cfg` is the configuration the route reads; both tests dropped from about 60 s to 1.02 s.
- UNK-01: the first test asserts only that the stream closes, so the shortened timeout does not change what it proves.

## Design decisions
- `object.__setattr__(cls.cfg, "sse_idle_timeout", 1.0)` in `setup_class()`, after construction, because the cross-field validation runs only in the constructor; the existing pattern is in `tests/eventbus/test_eventbus_restart_resume.py`.
- The first test's bound moves from 120 s to 10 s, about ten times the timeout.

## Alternatives considered
- Passing the timeout through the shared helper: not possible, this class builds its own application.

## Implementation
### Target file
tests/eventbus/test_eventbus_auth.py

### Procedure
1. Record the baseline durations (60.38 s and 60.23 s).
2. Add the idle-timeout assignment with an explanatory comment to `TestSubscribeAuth.setup_class()`.
3. Lower the bound in `test_subscribe_with_timeout_disconnect_detection` from 120 to 10 seconds.
4. Run the module, then the full suite with a duration report.

### Method
Test-only edit in one file.

### Details
No assertion about authorization changes.

## Compatibility considerations
- Test only.

## Security considerations
- None.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_auth.py -q --timeout=60 --durations=4`; full suite with `--durations=8`; ruff check and format.

## Completion criteria
- Both tests finish in about 1 second, the module passes (37 passed) and the full suite passes (REQ-001 to REQ-003).

## Out of scope
- Any file other than `tests/eventbus/test_eventbus_auth.py`; production code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write or update tests first (Validation plan) | Completed | 20261008-193958 | 20261008-193958 |  |
| 2 | Implement the change in Implementation > Procedure | Completed | 20261008-193958 | 20261008-193958 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261008-193958 | 20261008-193958 |  |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: issues/done/20261008-155824_ebauthidle01_shorten-the-60-second-idle-waits-in-two-eventbus-auth-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-193004_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-193958
- **Related target files**: tests/eventbus/test_eventbus_auth.py