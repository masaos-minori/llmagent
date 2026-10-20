> **Superseded**: the anchor-path tests described here were not adopted; the clamp
> fix replaced the anchor approach. Canonical test procedure:
> `implementations/done/20261020-093004_02_tests_agent_test_session_restore.py.md`.
> See the superseded note in `20261019-231619_01_scripts_agent_services_session_restore.py.md`
> for the reason.

## Goal

Add unit tests to `tests/agent/test_session_restore.py` covering the two previously-uncovered `/undo` boundary paths introduced by `plans/20261019-210940_plan.md` (REQ-003): (a) the `count_messages_up_to` raise path, and (b) the dropped-snapshot-row path.

## Scope

Modify `tests/agent/test_session_restore.py` only: add two tests to the existing `TestRestoreSession` class. Reference Files are read-only and not modification targets.

## Assumptions

- The existing `_make_ctx` helper builds a `MagicMock` `ctx` whose `ctx.conv` is a real `ConversationState`, so `replace_history()` actually runs and populates `ctx.conv.history`; only `ctx.session` is mocked.
- `count_messages_up_to` is mocked via `ctx.session.count_messages_up_to.return_value`; a raise is expressed via `.side_effect`.
- The success path is already locked by `test_undo_floor_converts_boundary_to_index` (asserts `undo_floor == 2`); the new tests must not regress it.

## Design decisions

- **Raise-path test asserts propagate-before-mutate.** Set `ctx.session.count_messages_up_to.side_effect = sqlite3.Error(...)` and assert that after the raise the session is left unmutated (`ctx.session.session_id` unchanged from its `_make_ctx` default, and `reset_session_stats` not called) — directly verifying AC-1.
- **Dropped-row test anchors to the rebuilt history.** Craft a snapshot row that `replace_history()` drops and assert the resulting `undo_floor` indexes within the rebuilt (`ctx.conv.history`) length rather than the pre-sanitization `messages` count — verifying AC-2.

## Alternatives considered

- Mocking `replace_history` to simulate a drop: rejected — `ctx.conv` is already a real `ConversationState`, so exercising the real sanitize/drop path is more faithful and also covers the `_append_message_locked` logic the defect is about.

## Implementation

### Target file

`tests/agent/test_session_restore.py` (modify)

### Procedure

1. Add `import sqlite3` at the top of the file (alongside the existing imports).
2. Add a raise-path test to `TestRestoreSession` (see Method).
3. Add a dropped-row test to `TestRestoreSession` (see Method).

### Method

**Harness facts (from the current file):** `_make_ctx(messages, system_prompt_content, extra_history, session_found, undo_floor_id)` returns a `MagicMock` with `ctx.session.fetch_messages` set to the `(messages, found, undo_floor_id)` 3-tuple, a real `ctx.conv = ConversationState()`, and `ctx.session.session_id = 0`. `count_messages_up_to` is controlled via `ctx.session.count_messages_up_to.return_value`.

**Raise-path test (REQ-001 / AC-1):**
- Build ctx with `undo_floor_id` non-zero (so the boundary block runs) and `system_prompt_content` set (so `replace_history` runs before the boundary call).
- Set `ctx.session.count_messages_up_to.side_effect = sqlite3.Error("db down")`.
- Patch `agent.services.session_restore.reset_session_stats` and assert it is not called.
- Assert `pytest.raises(sqlite3.Error)` around `await restore_session(ctx, session_id=<nonzero>)`.
- After the raise assert `ctx.session.session_id` still equals its `_make_ctx` default (`0`) — proving `session_id` was not reassigned before the raise — and `mock_reset.assert_not_called()`.

**Dropped-row test (REQ-002 / AC-2):**
- Determine a concrete drop trigger by reading `_append_message_locked` (`context.py:139-163`) with `validate_message` (`scripts/agent/message_schema.py:46`) and `_sanitize_message` (`context.py:68`): a row is dropped when `validate_message` fails AND `_sanitize_message` returns `None` (the sanitized result is missing `role` or `content`). Choose such a row (e.g. a row that fails validation and loses `content` during sanitization).
- Build ctx with `undo_floor_id` non-zero and `count_messages_up_to.return_value` set to a snapshot count; include the drop-triggering row among the fetched `messages`.
- After `await restore_session(...)`, assert `0 <= ctx.conv.undo_floor <= len(ctx.conv.history)` and that `undo_floor` equals the index derived from the rebuilt `ctx.conv.history` (not the pre-sanitization `messages` length) — e.g. recompute `_boundary_to_index(n_snapshot, ctx.conv.history, system_prompt_set=bool(ctx.conv.system_prompt_content))` and assert equality, or assert the bound above holds where the pre-sanitization anchor would exceed it.

### Details

- Both tests live in `TestRestoreSession` and are `async` methods, matching the existing cases.
- Keep the new tests independent of each other and of `test_undo_floor_converts_boundary_to_index`.

## Compatibility considerations

N/A: test-only addition; existing cases are unaffected and must keep passing.

## Security considerations

N/A: no trust-policy change; the test exercises the real `replace_history` sanitize/drop path but does not alter it.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `test_session_restore.py` (new + existing) | New raise-path and dropped-row tests pass; all existing cases still pass | `uv run pytest tests/agent/test_session_restore.py` | All cases pass |
| Touched file (lint/type) | Static checks | `uv run ruff check tests/agent/test_session_restore.py` and `uv run mypy tests/agent/test_session_restore.py` | Clean (zero findings) |

## Completion criteria

- `test_session_restore.py` contains a raise-path test asserting the session is not left with `undo_floor == 0` (session_id unchanged / `reset_session_stats` not called) and a dropped-row test asserting `undo_floor` indexes within the rebuilt `ctx.conv.history`.
- All existing `test_session_restore.py` cases still pass; `ruff`/`mypy` clean on the test file.

## Out of Scope

- Any change to `session_restore.py` logic (covered by `20261019-231619_01_scripts_agent_services_session_restore.py.md`).
- `context.py` sanitization/drop policy (read-only reference; validation policy out of scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add raise-path unit test (propagate-before-mutate) (REQ-003) | Completed | 20261020 | 20261020 | Added `test_raise_in_count_messages_up_to_leaves_state_unmutated`: sqlite3 raise in count_messages_up_to propagates before any session-state mutation; session_id unchanged, reset_session_stats not called (AC-1). |
| 2 | Add dropped-row unit test (anchor to rebuilt history) (REQ-003) | Completed | 20261020 | 20261020 | Added `test_undo_floor_anchors_to_rebuilt_history_after_dropped_row`: content-less restored row dropped by replace_history(); undo_floor anchors to shorter rebuilt ctx.conv.history, not pre-sanitization row count (AC-2). |
| 3 | Run ruff/mypy and full `test_session_restore.py` | Completed | 20261020 | 20261020 | ruff format/check clean; targeted 15 passed; full suite 9612 passed, 20 skipped. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261020 | 20261020 | N/A: no docs/00_index.md task-scope mapping for test_session_restore.py. |

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
- **Requirement ID**: REQ-003 (add raise-path and dropped-snapshot-row unit tests to `test_session_restore.py`)
- **Source issue**: `issues/20261019-202042_sess001_restore_session-undo_floor-boundary-breaks-when-boundary-computation-fails-or-snapshot-rows-are-dropped.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261019-210940_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-231619
- **Related target files**: `tests/agent/test_session_restore.py`
