## Goal
Make `test_failed_reindex_does_not_record_the_new_mtime` deterministic by giving the rewritten file an explicitly newer modification time, keeping the test fast and its assertions unchanged (`REQ-001`, `REQ-002`), and show by 200 repeated runs that it no longer fails (`REQ-003`).

## Scope
- One import line and three statements inside `test_failed_reindex_does_not_record_the_new_mtime`; nothing else in the module changes.

## Assumptions
- The refresh logic only compares the stored `st_mtime_ns` string with the current one for equality (`_refresh_changed_file` in `scripts/mcp_servers/mdq/indexer.py`), so any strictly later value triggers a re-index attempt.
- Verified on 2026-10-19 with a throwaway test: a tie of the two writes' mtimes gives counters `(0, 1, 0)`, a later mtime gives `(0, 0, 1)`.

## Design decisions
- Derive the new mtime from the first write's (`first + 1_000_000_000` ns) so it is strictly greater by construction, independent of timestamp granularity; unlike a sleep it does not just lower the probability of a tie.
- Keep both assertions exactly as they are.

## Alternatives considered
Adding `time.sleep(0.05)` as the sibling tests do was rejected for this test: it only reduces the chance of a tie, while `os.utime` removes it.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_incremental_refresh.py`

### Procedure
1. Add `import os` to the module imports, between `import logging` and `import sqlite3`.
2. After the first refresh and before the second write, read `first_mtime_ns = target.stat().st_mtime_ns`.
3. After `target.write_text("# A\n\nTwo")`, set `later_ns = first_mtime_ns + 1_000_000_000` and call `os.utime(target, ns=(later_ns, later_ns))`, with a one-line comment that coarse timestamps can tie with the first write.
4. Run the file, then the repeated-run check.

### Method
- Edit only `test_failed_reindex_does_not_record_the_new_mtime`; the two assertions on `_counters(result)` and `_index_state_keys(service)` stay unchanged.
- Repeated-run check: a shell loop of 200 runs of `uv run pytest -q -p no:randomly tests/mcp_servers/mdq/test_mdq_incremental_refresh.py::TestRefreshIncrementalBranches::test_failed_reindex_does_not_record_the_new_mtime`, counting non-zero exits; for part of the loop run a CPU-bound background load (for example a few `python3 -c "while True: pass"` processes), and stop the load afterwards.

### Details
- No other test in the module needs the change: the only other test that rewrites a file after a refresh either sleeps or waits (`test_directory_refresh_reindexes_changed`, `test_reindexes_changed_file`), as scanned on 2026-10-19.
- The test runs under `tmp_path`; nothing under `/opt/llm` is touched (the suite is isolated by `tests/conftest.py`).
- Remove any background load processes started for the check.

## Compatibility considerations
N/A: test-only change.

## Security considerations
N/A: tests only; the background load is local and removed afterwards.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_incremental_refresh.py -q`
- The 200-run loop described under Method (expected: 0 failures)
- `uv run ruff format tests/mcp_servers/mdq/test_mdq_incremental_refresh.py && uv run ruff check tests/mcp_servers/mdq/test_mdq_incremental_refresh.py`, `uv run mypy tests/mcp_servers/mdq/test_mdq_incremental_refresh.py`
- `uv run python tools/check_suppression_justification.py` and `uv run python tools/check_mock_patch_targets.py`

## Completion criteria
- The test sets a strictly later mtime with `os.utime`, has no sleep and unchanged assertions, the module's tests pass, and 200 consecutive runs pass with part of them under CPU load.

## Out of scope
- Changing the indexer or `index_state`
- Other tests in the module
- A characterization test for same-mtime behavior

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `import os` and the `os.utime` step to the test | Pending | — | — | |
| 2 | Run the module's tests and the validation sequence (`rules/toolchain.md`) for it | Pending | — | — | |
| 3 | Run the single test 200 times with partial CPU load and confirm 0 failures | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003` (newer mtime, unchanged assertions, repeated-run check)
- **Source issue**: issues/20261019-143959_testfix002_flaky-mdq-mtime-test.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-161023_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-161550
- **Related target files**: tests/mcp_servers/mdq/test_mdq_incremental_refresh.py
