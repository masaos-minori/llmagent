## Goal

Fix `tests/mcp_servers/file/test_read_service.py::TestGetFileInfo::test_get_file_info_os_error_raises_file_validation_error`'s `Path.stat` call-counting mock so it reliably triggers `get_file_info`'s `OSError`-to-`FileValidationError` conversion (REQ-002).

## Scope

In scope: this one test's `boom()` mock function and its `monkeypatch.setattr(Path, "stat", boom)` setup. Out of scope: `scripts/mcp_servers/file/read_business.py::get_file_info`'s `try/except OSError` structure (confirmed already correct via Read).

## Assumptions

- The exact cause of the current mock's failure to trigger at the intended call site is not yet confirmed (Plan's UNK-01) — Implementation step 1 below performs the tracing needed to resolve it before finalizing the fix.

## Design decisions

- Add temporary tracing first (per the Plan's Unknown resolution path) rather than guessing at a call-count adjustment — the exact number/identity of `Path.stat` calls between `_resolve_safe`, `.exists()`, and `get_file_info`'s own explicit `stat()` must be observed directly.

## Alternatives considered

- Blindly incrementing the `call_count > 1` threshold to `> 2` or `> 3` without tracing: rejected — per `skills/python-test-and-fix/SKILL.md` Core Testing Rules, do not guess at a fix without understanding the actual failure mechanism; an incorrect guess could mask the real cause or introduce new fragility.

## Implementation

### Target file

`tests/mcp_servers/file/test_read_service.py`

### Procedure

1. Add temporary tracing inside `boom()` (e.g. `print(f"stat() call {call_count} on {self}")` before the `if self == target_path` check, or an unconditional call-log regardless of path match) and reproduce `test_get_file_info_os_error_raises_file_validation_error` once with `-s` (disable output capture) to observe the actual sequence and identity of every `Path.stat` call during the test.
2. Based on the trace, determine why the intended `OSError` never reaches `get_file_info`'s own explicit `try: st = target.stat()` call — likely candidates (confirm via the trace, do not assume): (a) `self._resolve_safe(req.path)` calls `.stat()` one or more times before `.exists()`, shifting which call is "the second" one; (b) the `self == target_path` equality check fails for the actual resolved `Path` object passed at the relevant call (e.g. due to path resolution producing a differently-constructed-but-equal, or subtly unequal, `Path`); (c) some other call path entirely.
3. Adjust `boom()`'s call-counting/matching logic to correctly target `get_file_info`'s own explicit `stat()` call based on the trace's findings, then remove the temporary tracing.

### Method

Investigative tracing first (Procedure step 1), root-cause determination (step 2), then a fix scoped to the confirmed cause (step 3) — not a blind adjustment.

### Details

- `get_file_info`'s confirmed-correct structure (`scripts/mcp_servers/file/read_business.py:287-307`): `target = self._resolve_safe(req.path); if not target.exists(): raise FileNotFoundError(...); try: st = target.stat() except OSError as e: raise FileValidationError(str(e))`.
- The test's own comment already documents the intended call-order assumption ("let the first stat() call from .exists() succeed normally, and only fail the second") — the trace must confirm whether `_resolve_safe` inserts an additional, unaccounted-for call before `.exists()`'s own call, which would explain why the intended target (`get_file_info`'s own `stat()`) is never the one that fails.

## Compatibility considerations

- No production code changes; test-only fix.

## Security considerations

N/A: test-only fix, no security-relevant behavior change.

## Rollback considerations

- `git revert` the commit, or manually restore the prior `boom()` implementation.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/mcp_servers/file/test_read_service.py` | Unit | `uv run pytest tests/mcp_servers/file/test_read_service.py -q` | All tests pass, including the previously-failing one |

## Completion criteria

- `uv run pytest tests/mcp_servers/file/test_read_service.py::TestGetFileInfo::test_get_file_info_os_error_raises_file_validation_error -q` passes.
- The fix is confirmed to genuinely exercise `get_file_info`'s `OSError`-to-`FileValidationError` conversion (via the trace's confirmation, not merely a passing assertion).

## Out of scope

- `scripts/mcp_servers/file/read_security.py` (covered by its own implementation procedure document from this same Plan).
- `scripts/mcp_servers/file/read_business.py::get_file_info` (confirmed already correct).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260927-140518 | 20260927-140518 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260927-140518 | 20260927-140518 | N/A: fixing the existing mock is itself the fix |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260927-140518 | 20260927-140518 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260927-140518 | 20260927-140518 | N/A: no docs/00_index.md task-scope mapping for this test file |

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
- **Requirement ID**: REQ-002: fix `test_get_file_info_os_error_raises_file_validation_error`'s call-counting mock
- **Source issue**: issues/20260927-075249_mcp001_mcp-file-server-read-tests-size-limit-and-missing-exception.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-084210_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-092759
- **Related target files**: tests/mcp_servers/file/test_read_service.py