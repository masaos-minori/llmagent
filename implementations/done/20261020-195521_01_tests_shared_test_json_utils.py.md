## Goal

Make the `now_iso` and `now_iso_raw` tests in `tests/shared/test_json_utils.py` independent of the wall clock, so a second boundary or UTC midnight inside a test cannot fail CI (REQ-001, REQ-002, REQ-003, REQ-004).

## Scope

Only `tests/shared/test_json_utils.py`, classes `TestNowIso` and `TestNowIsoRaw`:

- Rewrite the two same-second tests and the midnight test against a frozen clock (REQ-001, REQ-002, REQ-003).
- Add one second-boundary test per function (REQ-001, REQ-002).
- Replace the two 1.1 s real sleeps with frozen-clock advances (REQ-004).

Production code, other test files, and format-only tests in the same classes are unchanged.

## Assumptions

- `freezegun>=1.5` is already in the `dev` dependency group and is used in `tests/tools/test_check_workitem_traceability.py`, so no dependency change is needed.
- `freeze_time` reaches `shared.json_utils` although it does `from datetime import UTC, datetime`; this was verified with a frozen-clock probe during planning, together with each old failure shape.
- The module already has `import datetime`, so `datetime.timedelta` needs no new import; only the `freeze_time` import is added.

## Design decisions

- **Context managers only.** Each test uses `with freeze_time(...) as frozen:` and `frozen.tick(delta=...)`, so the real clock is restored when the test ends and no frozen clock can leak into another test.
- **Two start instants.** Same-second tests start well inside a second (`.100`) so they are deterministic; boundary tests start at `.995` so a 10 ms advance crosses the boundary.

## Alternatives considered

N/A: a fixture or decorator-based freeze would also work but risks leaking the frozen clock; per-test context managers are the smallest, safest form.

## Implementation

### Target file

`tests/shared/test_json_utils.py`

### Procedure

1. Add `from freezegun import freeze_time` to the module imports and let `ruff` place it.
2. Rewrite `test_now_iso_consistent_across_calls_same_second` and add `test_now_iso_changes_across_a_second_boundary` (new).
3. Rewrite `test_now_iso_raw_consistent_across_calls_same_second` and add `test_now_iso_raw_prefix_changes_across_a_second_boundary` (new).
4. Rewrite `test_now_iso_date_changes_at_midnight`.
5. Rewrite `test_now_iso_time_changes_over_time` and `test_now_iso_raw_time_changes_over_time` without `time.sleep`; drop their local `import time`.

### Method

- Same-second (`now_iso`): start `"2026-10-20 10:22:49.100"`, read, `frozen.tick(delta=datetime.timedelta(milliseconds=10))`, read again; assert both equal `"2026-10-20T10:22:49Z"`.
- Boundary (`now_iso`): start `"2026-10-20 10:22:49.995"`, read, tick 10 ms, read again; assert the first is `"2026-10-20T10:22:49Z"`, the second is `"2026-10-20T10:22:50Z"`, and they differ.
- `now_iso_raw` twins: same instants; compare the first 19 characters of each result (`[:19]`), equal within the second and different across the boundary.
- Midnight (keep the name): start `"2026-10-20 23:59:59.999"`, read, tick 2 ms, read again; assert the first starts with `"2026-10-20T"` and the second with `"2026-10-21T"`.
- Time-changes tests: start `"2026-10-20 10:22:49.000"`, read, tick 1.1 s, read again; assert the values differ.

### Details

- Keep every test that asserts only format (suffix, length, absence of an offset) as it is.
- Keep existing test names; the midnight test's name now matches its body, which checks the rollover.
- After the edits no `time.sleep` and no local `import time` should remain in the file.
- Use `datetime.timedelta(...)` through the existing `import datetime`; do not add a `timedelta` import.

## Compatibility considerations

N/A: test-only change; `shared.json_utils` and its behavior are unchanged.

## Security considerations

N/A: no credential, path, or network access; the tests do not touch `/opt/llm`.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/shared/test_json_utils.py -v` passes, collects the two new tests, and runs faster than the 3.66 s baseline for 160 tests.
- Repeat the file 20 times in a row with no failure.
- `ruff`, `mypy` (CI invocation, plus the test file), `tools/check_mock_patch_targets.py`, and `tools/check_suppression_justification.py` are clean.
- Full suite passes once.
- Optional ad hoc evidence, not committed: show the old assertion shapes fail at a frozen `:49.995` while the new tests pass.

## Completion criteria

- No rewritten or added test reads the real clock for its assertion, and no `time.sleep` remains in the file.
- A second-boundary difference and a midnight rollover are asserted explicitly.
- The file passes 20 consecutive runs and the full suite, and `shared.json_utils` is unchanged.

## Out of Scope

- Changing `now_iso`, `now_iso_raw`, or `scripts/eventbus/json_utils.py`.
- Auditing other tests for time dependence.
- CI configuration, retries, or quarantine.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the import and rewrite or add the clock-dependent tests in `tests/shared/test_json_utils.py` | Completed | 20261020-200457 | 20261020-200457 | REQ-001, REQ-002, REQ-003, REQ-004 changed: tests/shared/test_json_utils.py (5 tests rewritten, 2 added; no time.sleep left) |
| 2 | Run the file, the 20-run stability loop, and the optional old-shape evidence | Completed | 20261020-200457 | 20261020-200457 | AC-001..AC-005 targeted 162 passed in 1.39s (baseline 160 in 3.58s); 20/20 consecutive runs pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the full suite | Completed | 20261020-200457 | 20261020-200457 | ruff, mypy (scripts + file), mock-patch, suppression pass; full suite 9665 passed, 14 skipped; docs N/A: no docs mapping |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: issues/20261020-194610_testflaky001_clock-boundary-assertions-in-shared-json_utils-tests-make-ci-flaky.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261020-195002_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261020-195521
- **Related target files**: tests/shared/test_json_utils.py