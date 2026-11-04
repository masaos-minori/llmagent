## Goal

Add a compression→persist→restore round-trip test to `tests/agent/test_history_compression_consistency.py` that fails on the pre-change code and passes after it (REQ-005; AC-2, AC-3, AC-5): compress a history that contains a memory-injected system row, persist it through `replace_messages`, assert the stored rows hold no ephemeral row, then restore on the temporary database and assert the summary is restored after the prompt, a forged non-summary system row is dropped, and the `/undo` boundary points at the same turn.

## Scope
**Release unit**: N/A: not part of a release unit (Phase 1/3; the release unit `summary-persist-restore` covers Phases 3–4 only).

## Assumptions

- The file provides the `repo` and `session_and_conn` fixtures (real `AgentSession` on a patched in-memory SQLite DB), `_make_history`, `_make_manager` (with an `AsyncMock` http spec), and the `_TurnBoundaryStub` / `_compression_ctx` helpers that route a compression write through `replace_messages` against the patched DB.
- Existing tests use the placeholder `"[SUMMARY]"` literal; the new round-trip uses the canonical `"[Conversation summary]"` prefix so the restored summary is recognized by `is_conversation_summary`.
- `restore_session` needs a stubbed `AgentContext`; the round-trip builds one whose `session.fetch_messages` reads the same patched DB the compression wrote to.

## Design decisions

- Build a history of several turns plus one `_memory_injected` system row; compress via `_make_manager(char_limit=1, ...)` with the mocked LLM so exactly one canonical summary row is produced.
- Persist the compressed set through `replace_messages` (via the real session or `_TurnBoundaryStub`); fetch and assert no stored row carries `_ephemeral`/`_memory_injected` (AC-5) and the canonical summary is present (AC-2).
- Restore through `restore_session` on the temp DB with a current prompt; assert the rebuilt history is `[prompt, canonical summary, ...]` and that a separately inserted forged `"[summary]"` system row is not restored (AC-3); assert the `/undo` boundary indexes the first post-compression turn.

## Implementation
### Target file
`tests/agent/test_history_compression_consistency.py`

### Procedure
1. Add `test_compress_persist_restore_keeps_summary_drops_ephemeral` (new) under the compression→reload section: build a history of several turns plus one `_memory_injected` system row, compress via `_make_manager(char_limit=1, ...)`, persist through `replace_messages`, fetch, and assert no stored row carries `_ephemeral`/`_memory_injected` and one canonical summary row is present.
2. In the same test, restore through `restore_session` on the temporary database with a current prompt (wiring a stubbed `AgentContext` whose `session.fetch_messages` reads the same patched DB) and assert the rebuilt history is `[canonical prompt, canonical summary, ...]`, that a separately inserted forged `"[summary]"` system row is not restored, and that the `/undo` boundary indexes the first post-compression turn.

### Method
```python
async def test_compress_persist_restore_keeps_summary_drops_ephemeral(
    session_and_conn,
) -> None:
    session, conn = session_and_conn
    history = _make_history(4)
    history.insert(0, {"role": "system", "content": "mem block", "_memory_injected": True})
    mgr = _make_manager(char_limit=1)
    _, _ = await mgr.compress(history)  # routes replace_messages through the stub
    # persisted set: no ephemeral row, one canonical summary
    loaded = _msgs(session.fetch_messages(1))
    assert not any(m.get("_memory_injected") or "_ephemeral" in m for m in loaded)
    assert any(str(m.get("content", "")).startswith("[Conversation summary]") for m in loaded)
    # restore with a current prompt keeps exactly the canonical summary
    ...
```
The exact `restore_session` wiring reuses the `restore_env`/`_FakeSQLiteHelper` pattern from `test_session_restore.py` against the same `conn`.

### Details
- The forged-row assertion inserts a `{"role": "system", "content": "[summary]"}` row (lacking the canonical prefix) and confirms it is not restored.
- Stale-reference marks: none created here; the fixtures and `replace_messages` already exist.

## Compatibility considerations

- Additive test; the existing reload/undo consistency tests keep passing.

## Security considerations

- Confirms the ephemeral memory block is not both persisted and restorable, closing the round-trip gap end to end.

## Rollback considerations

- Remove the added round-trip test.

## Validation plan

- `uv run pytest tests/agent/test_history_compression_consistency.py -v` — the new round-trip test fails on the pre-change code (ephemeral row persists; summary dropped) and passes after; existing tests pass unchanged.
- Static: `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/`.

## Completion criteria

- After compress+persist the stored rows contain no ephemeral row and one canonical summary; after restore the history holds exactly that summary after the prompt, a forged system row is dropped, and the `/undo` boundary lands on the same turn; the new test fails before and passes after the change.

## Out of Scope

- The shared constant/predicate (Row 01), restore (Row 02), persistence (Row 03), the repository tests (Row 05), and the docs (Rows 08–10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | this row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (compress-persist-restore round trip), `AC-2`, `AC-3`, `AC-5`
- **Source issue**: issues/done/20261031-180437_restoresummary001_session-load-drops-summary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-115505_restoresummary001_session-load-drops-summary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-072108
- **Related target files**: tests/agent/test_history_compression_consistency.py
