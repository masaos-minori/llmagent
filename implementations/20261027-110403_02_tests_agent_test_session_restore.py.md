## Goal

Extend `tests/agent/test_session_restore.py` with regression coverage for the load-time orphan-tool-call repair introduced by this Plan: an orphaned assistant `tool_calls` row becomes paired after `restore_session` (`AC-001`), the repair is idempotent across two loads (`AC-003`), the `undo_floor` index accounts for synthesized rows inserted before the compression boundary (`AC-004`), and the repair emits a warning carrying the session id and synthesized-row count (`AC-002`). Existing tests and the real-DB persistence class are left intact.

## Scope

- **In-Scope** (`tests/agent/test_session_restore.py` only):
  - Add four test methods to the existing `TestRestoreSession` class (mock-based), covering orphan→paired, idempotency, `undo_floor` adjustment, and the warning log.
  - Add one real-DB assertion under `TestRestorePersistenceRealDB` confirming the DB row count is unchanged after restoring an orphaned session (memory-only repair).
- **Out-of-Scope**:
  - Any change to `scripts/agent/session_message_repo.py` or the service under test (covered by Row 01; `AC-005`).
  - Modifying existing test methods (they must pass unchanged, `AC-005`).

## Assumptions

- The mock-based `_make_ctx` helper (lines 20-53) already seeds `fetch_messages` with a `(messages, found, undo_floor_id)` tuple and a `ConversationState`, so orphan fixtures are built by passing an orphaned `messages` list.
- `count_messages_up_to` is mocked via `ctx.session.count_messages_up_to.return_value` to supply `n_snapshot`, exactly as the existing boundary tests do.
- The module logger is `agent.services.session_restore`, matching the existing `caplog.at_level(..., logger="agent.services.session_restore")` pattern.

## Design decisions

- **Reuse `_make_ctx`.** New tests construct their orphan fixtures through the existing helper rather than a new fixture, keeping the additions localized to `TestRestoreSession`.
- **Assert the repaired sequence, not internal state.** Each test drives `restore_session` and asserts on `ctx.conv.history` (paired roles / ids) so the contract — not the implementation — is pinned.
- **Idempotency via two independent restores.** Two fresh mocks over the same orphan input yield equal histories with the synthesized rows present exactly once.
- **Boundary offset asserted numerically.** The `undo_floor` test pins the exact post-repair index so an off-by-N regression fails loudly.

## Alternatives considered

- **A dedicated real-DB orphan fixture.** Rejected as the primary case: the mock path exercises detection/synthesis/log directly and deterministically; a real-DB case is added only for the memory-only (no row-count change) claim.

## Implementation

### Target file

`tests/agent/test_session_restore.py` (existing; extended)

### Procedure

1. Insert four `async def` test methods into `TestRestoreSession`, immediately after `test_drop_outside_snapshot_leaves_index_unchanged` (lines 258-282) and before the class closes at line 283.
2. Add `test_orphan_assistant_tool_calls_repaired_at_load` (new): build an orphan fixture (assistant row with two `tool_calls`, zero following tool rows) via `_make_ctx`, call `restore_session`, and assert the returned history ends with the assistant row followed by two synthesized `role="tool"` rows whose `tool_call_id`s match and whose content is the interrupted-marker text.
3. Add `test_restore_is_idempotent_for_orphan_session` (new): run `restore_session` over two independently-built mocks of the same orphan input and assert the two `ctx.conv.history` lists are equal and each synthesized tool row appears exactly once (no duplicates).
4. Add `test_undo_floor_accounts_for_synthesized_rows` (new): set `undo_floor_id` with an orphan assistant row located before the boundary snapshot, mock `count_messages_up_to` to return the snapshot count, and assert `ctx.conv.undo_floor` equals the pre-repair index plus the number of synthesized rows that landed before the boundary (never past history end).
5. Add `test_orphan_repair_logs_warning_with_session_id_and_count` (new): wrap the restore in `caplog.at_level(logging.WARNING, logger="agent.services.session_restore")` and assert at least one record message contains the session id and the synthesized-row count.
6. Add one real-DB method under `TestRestorePersistenceRealDB` (for example `test_restore_of_orphan_session_keeps_db_row_count` (new)) that seeds an orphaned assistant row, restores, and asserts the `messages` table row count is unchanged (memory-only).
7. Run the validation sequence (`routing.md`).

### Method

The existing `TestRestoreSession.test_undo_floor_converts_boundary_to_index` (lines 178-195) shows the established shape: an orphan variant sets `undo_floor_id`, mocks `count_messages_up_to`, and asserts `ctx.conv.undo_floor`. The new boundary test follows the same shape but injects an orphaned assistant row before the snapshot so synthesis shifts the floor by the synthesized count.

Illustrative reference for the orphan→paired and warning tests (adapt, do not copy verbatim):

```
async def test_orphan_assistant_tool_calls_repaired_at_load(self) -> None:
    assistant = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {"id": "call_a", "type": "function", "function": {"name": "f", "args": {}}},
            {"id": "call_b", "type": "function", "function": {"name": "g", "args": {}}},
        ],
    }
    ctx = _make_ctx(messages=[{"role": "user", "content": "q"}, assistant])
    await restore_session(ctx, session_id=11)
    roles = [m["role"] for m in ctx.conv.history]
    assert roles[-3:] == ["assistant", "tool", "tool"]
    tool_ids = {m["tool_call_id"] for m in ctx.conv.history if m["role"] == "tool"}
    assert tool_ids == {"call_a", "call_b"}
    assert all(
        "interrupted" in m["content"]
        for m in ctx.conv.history
        if m["role"] == "tool"
    )


async def test_orphan_repair_logs_warning_with_session_id_and_count(self, caplog) -> None:
    assistant = {"role": "assistant", "tool_calls": [{"id": "call_x", "type": "function", "function": {"name": "f", "args": {}}}]}
    ctx = _make_ctx(messages=[assistant], session_id=21)
    with caplog.at_level(logging.WARNING, logger="agent.services.session_restore"):
        await restore_session(ctx, session_id=21)
    joined = " ".join(r.getMessage() for r in caplog.records)
    assert "21" in joined
    assert "1" in joined
```

### Details

- **`REQ-001` / `AC-001`:** `test_orphan_assistant_tool_calls_repaired_at_load` (new) asserts the paired sequence and matching `tool_call_id`s.
- **`REQ-003` / `AC-002`:** `test_orphan_repair_logs_warning_with_session_id_and_count` (new) asserts the warning carries the session id and count.
- **`REQ-004` / `AC-003`:** `test_restore_is_idempotent_for_orphan_session` (new) asserts equal histories with each synthesized row once; the real-DB method asserts the DB row count is unchanged.
- **`REQ-005` / `AC-004`:** `test_undo_floor_accounts_for_synthesized_rows` (new) pins the exact shifted floor index.
- **`REQ-006` / `AC-005`:** existing tests are unmodified and pass unchanged; `session_message_repo.py` is untouched.

## Compatibility considerations

- Purely additive methods; no existing method signature or body changes, so the whole existing class keeps passing.

## Security considerations

- Test-only additions; no new input surface or secret handling.

## Rollback considerations

- Revert the file edit (`git checkout`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/agent/test_session_restore.py` | New + regression | `uv run pytest tests/agent/test_session_restore.py` | Four new methods pass; all existing methods pass |
| `scripts/agent/session_message_repo.py` (unchanged) | Regression | `uv run pytest tests/agent/test_session_message_repo.py` | Passes with zero changes |
| Static | mypy / ruff | `uv run mypy scripts/`, `uv run ruff check scripts/` | Clean |

## Completion criteria

- Four new `TestRestoreSession` methods cover orphan→paired, idempotency, `undo_floor` adjustment, and the warning log; the real-DB method asserts unchanged row count.
- All existing tests pass unchanged; `mypy` / `ruff` pass.

## Out of Scope

- `scripts/agent/session_message_repo.py` (`REQ-006`, `AC-005`).
- Service-under-test changes (Row 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement repair (Row 01) | Pending | — | — | Dependency |
| 2 | Add regression tests | In Progress | — | — | This row |
| 3 | Run validation sequence | Pending | — | — | pytest/mypy/ruff |
| 4 | Update doc (Row 03) | Pending | — | — | This row |

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
- **Requirement ID**: `REQ-001`..`REQ-005`
- **Source issue**: `issues/20261026-224729_turn002_repair-orphan-tool-call-rows.md`
- **Source plan**: `plans/20261027-071546_turn002_repair-orphan-tool-call-rows.md`
- **Generated at**: 20261027-110403
- **Related target files**: `tests/agent/test_session_restore.py`
