## Goal

Add a regression test to `tests/agent/services/test_session_title.py` that drives `SessionTitleService.generate` past the HTTP path to success and then makes `ctx.session.set_title(...)` raise `sqlite3.Error`, asserting that `generate` converts it into `SessionTitleGenerationError` chained from the original `sqlite3.Error` (via `from e`). This locks the source change in `scripts/agent/services/session_title.py` (companion doc) and the AC-1 contract: a DB write failure degrades to the wrapped error instead of escaping.

## Scope

- **In scope:**
  - Add one async test function to `tests/agent/services/test_session_title.py`.
  - Add `import sqlite3` to the test file.
- **Out of scope:**
  - Modifying any existing test in `tests/agent/services/test_session_title.py` (all existing cases must still pass unchanged — AC-3).
  - Modifying `scripts/agent/services/session_title.py` (covered by the companion doc).

## Assumptions

- The test uses the same mocking style as the existing cases: a top-level `ctx = MagicMock()` with `ctx.services_required.http.post` replaced by an `AsyncMock`.
- To reach `ctx.session.set_title(title)` inside `generate`, the mocked HTTP response must pass `raise_for_status()` and return valid JSON whose `extract_llm_content` yields a non-empty title — mirroring `test_generate_success_returns_title` (lines 93-107).
- `sqlite3.Error` is importable from stdlib (`import sqlite3`) with no side effects.
- `pytest.raises(...).__cause__` exposes the chained cause set by `... from e`.

## Design decisions

- **Drive the real HTTP path, then fail only `set_title`.** Rather than mocking `post` to raise, succeed the HTTP path so execution actually reaches `ctx.session.set_title(title)` (line 58 of `session_title.py`), then set `ctx.session.set_title.side_effect = sqlite3.Error(...)`. This exercises the genuine new `except sqlite3.Error` handler rather than a stubbed path.
- **Assert both the type and the chaining.** Use `pytest.raises(SessionTitleGenerationError) as exc_info` and then assert `exc_info.value.__cause__` is a `sqlite3.Error`, verifying the `from e` chain (AC-1).
- **Match existing style.** Keep the function at module level with `@pytest.mark.asyncio`, importing the classes inside the body exactly as the other six tests do.

## Alternatives considered

- **Mock `post` to raise `sqlite3.Error` directly.** Would not exercise the `set_title`-inside-try path (the DB error would originate from `post`, not `set_title`), so it would not specifically cover the new clause's intent ("a database error ... during generation" via `set_title`). Rejected; the failing call site matters.
- **Assert only the exception type.** Weaker — does not prove the `from e` chaining required by AC-1. Rejected; assert `__cause__` explicitly.

## Implementation

### Target file

`tests/agent/services/test_session_title.py` (modify).

### Procedure

1. **Add the import.** At the top of the file, after `from unittest.mock import AsyncMock, MagicMock`, add `import sqlite3`:
   ```python
   from unittest.mock import AsyncMock, MagicMock

   import sqlite3
   ```
   (Keep the existing `import httpx`, `import orjson`, `import pytest` below.)
2. **Append the regression test.** Add the following function at the end of the file (after `test_generate_success_returns_title`, lines 93-107):
   ```python
   @pytest.mark.asyncio
   async def test_generate_sqlite_error_wrapped_as_title_error() -> None:
       from agent.services.exceptions import SessionTitleGenerationError
       from agent.services.session_title import SessionTitleService

       ctx = MagicMock()
       # Succeed the HTTP path so generate reaches ctx.session.set_title(...).
       mock_resp = MagicMock()
       mock_resp.raise_for_status = MagicMock()
       mock_resp.content = orjson.dumps(
           {"choices": [{"message": {"content": "My Session Title"}}]}
       )
       ctx.services_required.http.post = AsyncMock(return_value=mock_resp)
       # Fail the DB write performed by set_title.
       ctx.session.set_title.side_effect = sqlite3.Error("disk I/O error")
       with pytest.raises(SessionTitleGenerationError) as exc_info:
           await SessionTitleService().generate(ctx, "hello")
       # The DB error must be converted AND chained from the original cause.
       assert isinstance(exc_info.value.__cause__, sqlite3.Error)
   ```
3. **Verify the mock shape matches `generate`.** `generate` calls `resp.raise_for_status()`, then `parse_http_json(resp)` (which reads `resp.content` via orjson), then `extract_llm_content(data)`. The mock above satisfies all three: `raise_for_status` is a no-op `MagicMock`, and `content` returns valid JSON with a non-empty message content, so `title` is `"My Session Title"` and `set_title` is reached.

### Details

- `ctx.session.set_title.side_effect` is set on the same `ctx` used by `generate`; because `ctx` is a `MagicMock`, `ctx.session.set_title` is already an auto-child mock, so `.side_effect = sqlite3.Error(...)` makes the call raise.
- The assertion `isinstance(exc_info.value.__cause__, sqlite3.Error)` confirms the `from e` chaining introduced in the source clause. If the source instead swallowed the cause, this assertion fails.
- No existing test is altered; this is purely additive (AC-3).

## Compatibility considerations

- The new test is additive and self-contained; it does not depend on or alter the other six cases. It requires `orjson` (already imported) and `sqlite3` (added).

## Security considerations

- No security impact: the test constructs a synthetic `sqlite3.Error` and asserts wrapping behavior. No real database, credentials, or user data involved.

## Rollback considerations

- To remove the regression test, delete the appended function and the `import sqlite3` line. No other file is touched.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/agent/services/test_session_title.py` (new regression test) | Unit: `set_title` raises `sqlite3.Error`; assert `SessionTitleGenerationError` raised and chained. | `uv run pytest tests/agent/services/test_session_title.py` | New test passes; existing 7 cases still pass. |
| Touched file (lint/type) | Static: `ruff` + `mypy` on `tests/agent/services/test_session_title.py`. | `uv run ruff check` / `uv run mypy` | Clean (zero findings). |

## Completion criteria

- `tests/agent/services/test_session_title.py` contains `import sqlite3` and a new `test_generate_sqlite_error_wrapped_as_title_error` that succeeds the HTTP path, sets `ctx.session.set_title.side_effect = sqlite3.Error(...)`, and asserts `SessionTitleGenerationError` is raised with `__cause__` being a `sqlite3.Error`.
- All pre-existing cases in the file still pass unchanged (AC-3).
- `ruff check` and `mypy` pass cleanly on the test file.

## Out of Scope

- `scripts/agent/services/session_title.py` (source change — companion doc).
- Any other test file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261020-121334 | 20261020-121334 | Add `import sqlite3` + regression test Added import sqlite3 + regression test test_generate_sqlite_error_wrapped_as_title_error. |
| 2 | Add or update tests per Validation plan | Completed | 20261020-121334 | 20261020-121334 | This document New regression test passes; existing 7 cases pass unchanged (AC-3). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261020-121334 | 20261020-121334 | ruff/mypy on `test_session_title.py` ruff/mypy(scripts/438)/lint-imports(6/6)/bandit clean; combined Plan C suite 9614 passed. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261020-121334 | 20261020-121334 | N/A N/A. |

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
- **Source issue**: `issues/20261019-202210_sess003_sessiontitleservice-primary-path-lets-sqlite3.error-from-set_title-propagate-uncaught-instead-of-triggering-fallback.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261019-221335_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-233224
- **Related target files**: `tests/agent/services/test_session_title.py`