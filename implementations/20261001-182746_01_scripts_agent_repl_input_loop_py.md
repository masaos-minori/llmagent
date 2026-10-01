# Implementation Procedure: repl_input_loop.py — cancel pending input coroutine on shutdown-during-input path

## Goal

Cancel the pending `input_coro` on the shutdown-during-input path in `ReplInputLoop._read_input` so no dangling `input("> ")` task persists in the default executor after the REPL loop exits. Implements `REQ-001` (short purpose: explicit cancellation of pending input coroutine).

## Scope

- **In scope**: Add guarded `input_coro.cancel()` + `await input_coro` under `try/except asyncio.CancelledError` on the shutdown-done branch of `_read_input`; correct the misleading comment on that branch.
- **Out of scope**: Per-turn exception containment (`repl001`); startup `session.start()` exception translation in `run()`; the shutdown-racing logic in `_repl_loop`; `_shutdown_watcher`'s flag-setting responsibility; success-path EOF/Error/_InputAborted handling.

## Assumptions

- Cancelling `input_coro` while `input("> ")` is blocked in the default `ThreadPoolExecutor` releases the block and marks the task cancelled; awaiting it raises `asyncio.CancelledError`, which the handler swallows. This is standard asyncio task-cancellation semantics.
- No caller depends on the in-flight input coroutine surviving past the shutdown abort — the loop exits immediately after the shutdown-done path, so the dropped reference is never used again.
- `shutdown_event` remains the single authoritative shutdown signal; making cancellation explicit in `_read_input` does not introduce a second source of truth.

## Design decisions

- **Cancellation location**: perform the cancellation in `_read_input` itself, at the point where the read is aborted, rather than in `_shutdown_watcher`. Rationale: `_shutdown_watcher` only knows about the flag and does not hold a clean handle to cancel without reaching into `_read_input` locals; keeping it flag-only preserves its single responsibility.
- **Guarded await**: wrap `await input_coro` in `try/except asyncio.CancelledError: pass` to swallow the expected cancellation exception and prevent it from propagating out of `_read_input`.
- **Complexity budget**: `_read_input` already has cyclomatic complexity B (radon score 10). The added branch is two lines plus a guarded await; it stays well within the current budget, so no helper extraction is required unless the implementer judges the `try/except` block reads poorly inline.

## Alternatives considered

- **Cancellation in `_shutdown_watcher`**: would require threading a cancel callback through the watcher or passing `input_coro` as a closure variable, which complicates the watcher's single-responsibility design. Rejected in favor of local cancellation in `_read_input`.
- **No-op (leave as-is)**: the dangling executor thread persists until user submits input or process exits; there is no correctness bug during normal shutdown, but the stale comment invites future readers to assume cancellation happens when it does not. Rejected because the fix removes ambiguity and closes the lifecycle gap.

## Implementation

### Target file

`scripts/agent/repl_input_loop.py`

### Procedure

1. Read `scripts/agent/repl_input_loop.py` (`_read_input`, `_shutdown_watcher`, `_abort_input`) and confirm the exact shutdown-done branch and that `input_coro` is a local owned by `_read_input`. Confirm via `scripts/agent/repl.py` how `ReplInputLoop` and `shutdown_event` are wired, so shutdown-state ownership is preserved.
2. On the shutdown-done branch of `_read_input` (line ~156), add `input_coro.cancel()` followed by `await input_coro` guarded by `try/except asyncio.CancelledError: pass` before `_abort_input()`/`return None`.
3. Correct the misleading comment on the shutdown-done branch (currently "Cancellation handled by shutdown watcher — do not cancel here") to state that `_read_input` performs the cancellation.

### Method

- Keep the change minimal and localized to the shutdown-done branch; do not alter `_shutdown_watcher`, `_abort_input`, or any other method.
- Preserve the existing success-path branches (EOF, Error, _InputAborted) unchanged.
- Do not introduce blocking I/O in the async handler; the cancellation is synchronous and the await is guarded.

### Details

- Current code at the shutdown-done branch (lines 155-158):
  ```python
  # Cancellation handled by shutdown watcher — do not cancel here
  if shutdown_done or shutdown_coro in done:
      self._abort_input()
      return None
  ```
- New code should be:
  ```python
  if shutdown_done or shutdown_coro in done:
      input_coro.cancel()
      try:
          await input_coro
      except asyncio.CancelledError:
          pass
      self._abort_input()
      return None
  ```
- The comment must be removed or replaced with one stating that `_read_input` performs the cancellation.

## Compatibility considerations

- Shutdown behavior is unchanged: a shutdown request still terminates the loop, and the read returns `None` as before (AC-2).
- The existing success-path branches (EOF, Error, _InputAborted) are untouched.
- Existing REPL tests (`tests/agent/test_repl*.py`) must continue to pass (AC-3).

## Security considerations

- N/A: this change involves coroutine lifecycle management only; no secrets, credentials, or sensitive data are introduced.

## Rollback considerations

- Single-file, localized change; reverting the commit restores the original `_read_input` behavior with no data migration or config change. `deploy.sh` impact is limited to the interactive session; no deploy/config change.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/repl_input_loop.py` | Format + lint | `uv run ruff format scripts/agent/repl_input_loop.py` then `uv run ruff check scripts/agent/repl_input_loop.py` | Clean (no diffs, no errors) |
| `scripts/agent/repl_input_loop.py` | Type check | `uv run mypy scripts/agent/repl_input_loop.py` | Pass |
| `scripts/agent/repl_input_loop.py` | Security lint | `uv run bandit scripts/agent/repl_input_loop.py` | No new findings |
| `scripts/agent/repl_input_loop.py` | Complexity | `uv run radon cc scripts/agent/repl_input_loop.py -s` | Complexity did not worsen beyond the existing B grade |
| `tests/agent/test_repl*.py` | Regression: shutdown-during-input cancels `input_coro`; success-path reads unaffected | `uv run pytest tests/agent/test_repl*.py` | All pass; new regression test present |
| Whole affected lifecycle suite | Full regression + diff-scoped coverage | `uv run coverage run -m pytest tests/` → `uv run coverage xml` → `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | diff-cover >= 90% on changed lines |

## Completion criteria

- After a shutdown fires during an in-progress input read, the pending `input_coro` is cancelled (`input_coro.cancelled()` is True), not merely abandoned (AC-1).
- The read returns `None` and the loop proceeds to shutdown as before; the shutdown-done comment reflects that `_read_input` performs the cancellation (AC-2).
- Success-path input reads (line returned, EOF, error, aborted) are unaffected; existing `tests/agent/test_repl*.py` tests still pass (AC-3).

## Out of scope

- Per-turn exception containment (`repl001`).
- Startup `session.start()` exception translation in `run()`.
- The shutdown-racing logic in `_repl_loop`.
- `_shutdown_watcher`'s flag-setting responsibility.
- Success-path EOF/Error/_InputAborted handling.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read `_read_input`/`_shutdown_watcher`; confirm shutdown-done branch and `input_coro` ownership; verify wiring via `repl.py` | In Progress | 20261001-182959 | — | REQ-001, REQ-002 |
| 2 | Add guarded `input_coro` cancellation on shutdown-done path; fix stale comment | Pending | — | — | REQ-001, REQ-002 |
| 3 | Run validation sequence (`rules/toolchain.md`): ruff/mypy/bandit/radon/pytest/diff-cover | Pending | — | — | REQ-001, REQ-002 |

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
- **Requirement ID**: `REQ-001` — explicit cancellation of pending input coroutine on shutdown-during-input path
- **Source issue**: issues/20260930-231626_repl002_replinputloop-does-not-cancel-pending-input-coroutine-on-shutdown-during-input-path.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-092325_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-182746
- **Related target files**: scripts/agent/repl_input_loop.py