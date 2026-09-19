## Goal
Add unit test coverage for `StderrLogManager.get_log_path`, `.forget`, and `.clear`
(added in Step 01 of this pass), consistent with this file's existing one-class-per-
method structure (`REQ-001`).

## Scope
- In scope: three new test classes (`TestGetLogPath`, `TestForget`, `TestClear`),
  appended after the existing `TestRotateLog` class (current lines 120-163, the last
  class in the file).
- Out of scope: any change to `TestReadTail`, `TestStderrLogManagerInit`,
  `TestOpenLog`, or `TestRotateLog` — unchanged.

## Assumptions
- Step 01 of this pass
  (`implementations/20260919-212015_01_scripts_agent_http_lifecycle_stderr_log_manager.py.md`)
  has already added the three methods under test.

## Design decisions
- Follow this file's existing convention exactly: one `Test<MethodName>` class per
  method, each test directly manipulating `mgr._log_paths` as a plain dict to set up
  fixture state (the same pattern `TestReadTail`/`TestRotateLog` already use at lines
  24, 37, 47, 132, 147, 160) rather than going through `open_log` — this keeps the new
  tests focused on the method under test, consistent with the rest of the file.

## Alternatives considered
- Use `open_log` (mocked, per `TestOpenLog`'s pattern) to populate `_log_paths`
  instead of assigning it directly: rejected as unnecessary indirection for these
  three methods, which only read/mutate the dict — direct assignment is what every
  other class in this file already does for the same purpose.

## Implementation
### Target file
tests/agent/test_http_lifecycle_stderr_log_manager.py

### Procedure
1. Append three new test classes after `TestRotateLog` (end of file, current line
   163).

### Method
Append at end of file:
```python
class TestGetLogPath:
    def test_get_log_path_missing_server_key(self):
        mgr = StderrLogManager()
        assert mgr.get_log_path("nonexistent") is None

    def test_get_log_path_returns_tracked_path(self):
        mgr = StderrLogManager()
        mgr._log_paths["server1"] = "/tmp/server1.stderr.log"
        assert mgr.get_log_path("server1") == "/tmp/server1.stderr.log"


class TestForget:
    def test_forget_missing_server_key_is_noop(self):
        mgr = StderrLogManager()
        mgr.forget("nonexistent")  # must not raise
        assert mgr._log_paths == {}

    def test_forget_removes_tracked_path(self):
        mgr = StderrLogManager()
        mgr._log_paths["server1"] = "/tmp/server1.stderr.log"
        mgr.forget("server1")
        assert "server1" not in mgr._log_paths

    def test_forget_leaves_other_entries_intact(self):
        mgr = StderrLogManager()
        mgr._log_paths["server1"] = "/tmp/server1.stderr.log"
        mgr._log_paths["server2"] = "/tmp/server2.stderr.log"
        mgr.forget("server1")
        assert mgr._log_paths == {"server2": "/tmp/server2.stderr.log"}


class TestClear:
    def test_clear_empty_is_noop(self):
        mgr = StderrLogManager()
        mgr.clear()  # must not raise
        assert mgr._log_paths == {}

    def test_clear_removes_all_entries(self):
        mgr = StderrLogManager()
        mgr._log_paths["server1"] = "/tmp/server1.stderr.log"
        mgr._log_paths["server2"] = "/tmp/server2.stderr.log"
        mgr.clear()
        assert mgr._log_paths == {}
```

### Details
No new imports required — `StderrLogManager` is already imported at the top of this
file (current line 9).

## Compatibility considerations
N/A: this is a test-only addition, no production code affected.

## Security considerations
N/A: test file only, no external input or credentials involved.

## Rollback considerations
Revert this file's diff. No other file depends on these new test classes.

## Validation plan
- `uv run pytest tests/agent/test_http_lifecycle_stderr_log_manager.py -v` — all
  existing tests plus the 7 new tests across `TestGetLogPath`/`TestForget`/`TestClear`
  must pass.
- `uv run ruff check tests/agent/test_http_lifecycle_stderr_log_manager.py` — confirm
  lint compliance.

## Completion criteria
- `TestGetLogPath`, `TestForget`, and `TestClear` classes exist with the test methods
  listed above.
- `uv run pytest tests/agent/test_http_lifecycle_stderr_log_manager.py -v` passes with
  7 new tests, 0 failures.

## Out of scope
- Any change to `TestReadTail`, `TestStderrLogManagerInit`, `TestOpenLog`, or
  `TestRotateLog`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | This document's Implementation step 1 is itself the test addition |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: test-only file, no documentation update |

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
- **Requirement ID**: `REQ-001` (unit test coverage for the new StderrLogManager accessor methods)
- **Source issue**: issues/20260919-210241_refactor_003_deduplicate-stderr-path-tracking-and-cleanup-logic-in-http_lifecycle.py.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-211529_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-212015
- **Related target files**: tests/agent/test_http_lifecycle_stderr_log_manager.py
