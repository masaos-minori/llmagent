## Goal

Stop delivering a late line to the newest pending request: bind delivery to the waiter captured before the blocking read starts and drop results of cancelled or timed-out requests (REQ-002).

## Scope
**Release unit**: input-controller-cutover

In scope: `scripts/agent/stdin_reader.py` and its companion test. The controller that sits above the reader is a separate row.

## Assumptions

- Verified: the worker re-reads `self._waiter` after `input()` returns (`scripts/agent/stdin_reader.py:104-109`), which is the newest-request delivery the Issue describes.
- Existing invariants stay: one daemon thread, at most one outstanding read, `read()` refuses a second concurrent request with `RuntimeError`.

## Design decisions

- Capture the waiter in a local before calling the read function and deliver only to it; `_deliver` already skips a finished future, so a cancelled or timed-out waiter drops the line.
- Add a read-only property `orphaned_read`(new): true while the worker is blocked in a read whose waiter is finished or no longer current. The controller uses it to refuse destructive confirmation.

## Alternatives considered

Rejected: delivering a late line to the next waiter when the prompt text matches (still crosses requests); rejected: dropping the worker thread on timeout (a second reader on the same stdin).

## Implementation
### Target file
`scripts/agent/stdin_reader.py`

### Procedure
1. In `StdinReader._run`, keep the `waiter` local through delivery and remove the post-read re-read of `self._waiter` as the delivery target.
2. Record the waiter that started the current read in a private field and expose `orphaned_read`(new) from it, under `self._lock`.
3. After a read returns, if a different, still-pending waiter is registered, set the wake event so the worker starts a fresh read for it instead of waiting for a wake that never comes.
4. Rewrite the class docstring sentence about the newest pending request (lines 39-43 today) and the `read` docstring to describe discard semantics.

### Method
Minimal change inside `_run` and one new property; no new thread, no change to `get_stdin_reader` or `reset_stdin_reader`.

### Details
- A finished waiter is one whose future is done (cancelled, timed out through cancellation, or set).
- The existing closed-loop `RuntimeError` guard around `call_soon_threadsafe` stays.

### Companion test files
- `tests/agent/test_stdin_reader.py`
  - Procedure: Replace `test_line_after_cancel_goes_to_the_newest_request_without_a_second_read` (line 89) with a test that the line is dropped and the next request gets a fresh read; add `orphaned_read`(new) tests; keep the single-reader, daemon-thread, and closed-loop tests.
  - Validation: `uv run pytest tests/agent/test_stdin_reader.py -q`

## Compatibility considerations

`read(prompt)` keeps its signature and exceptions; only the late-line behavior changes (a documented specification removed by the docs rows).

## Security considerations

Removes the path by which a stale `y` could answer a later prompt (AC-1).

## Rollback considerations

N/A: revert the commit (release unit `input-controller-cutover` with the CLIView and loop rows).

## Validation plan

- `uv run pytest tests/agent/test_stdin_reader.py -q`
- `uv run ruff check scripts/agent/stdin_reader.py && uv run mypy scripts/agent/stdin_reader.py`

## Completion criteria

- A line arriving after its request ended is never delivered to another request.
- `orphaned_read`(new) is true exactly while such a read is blocked; existing reader tests that do not assert hand-off still pass.

## Out of Scope

Controller logic, CLIView and loop changes, docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261122-212457 | 20261122-213733 | Changed: scripts/agent/stdin_reader.py (and companions) |
| 2 | Add or update tests per Validation plan (companion test files included) | Completed | 20261122-212457 | 20261122-213733 | targeted tests pass (647 in the affected directories) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261122-212457 | 20261122-213733 | ruff, mypy, lint-imports, bandit clean; full suite 13377 passed; diff-cover 91% |

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
- **Requirement ID**: `REQ-002` (delivery bound to the waiter captured at read start)
- **Source issue**: issues/20261119-145259_cliplc001_repl-input-controller.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261122-210208_cliplc001_repl-input-controller.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-210644
- **Related target files**: `scripts/agent/stdin_reader.py`, `tests/agent/test_stdin_reader.py`
