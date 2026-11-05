## Goal

Add restore tests to `tests/agent/test_session_restore.py` that fail on the pre-change code and pass after it (REQ-005; AC-2, AC-3, AC-4, AC-6): the canonical summary is restored once after the system prompt, a forged non-summary system row is still dropped, two summary-shaped rows keep only the last with a warning, the `/undo` boundary with a summary in the snapshot lands on the same turn, and a second restore reproduces the same history.

## Scope
**Release unit**: N/A: not part of a release unit (Phase 1; the release unit `summary-persist-restore` covers Phases 3–4 only).

## Assumptions

- The file already provides `_make_ctx` (stubbed `AgentContext`, `fetch_messages` returns the `(messages, found, undo_floor_id)` 3-tuple) and the `restore_env` / `_FakeSQLiteHelper` real-DB fixtures (lines ~21, ~461).
- Existing tests pin the behaviors this Plan must not regress: `test_system_message_appears_exactly_once_when_db_also_has_system` (non-summary system row dropped), `test_memory_injected_messages_not_carried_into_restored_history`, and `test_undo_floor_converts_boundary_to_index` (a forged `"[summary]"` row stays dropped because it lacks the canonical prefix).
- Tests use the literal prefix text `"[Conversation summary]"` (the public constant value); they do not import the name, matching the existing compressed-set tests and the Plan's consumer-scan finding.

## Design decisions

- New summary-restored test: persist `[system prompt row dropped from DB, summary row with the canonical prefix, user row]` with `system_prompt_content` set; assert the rebuilt history is `[canonical prompt, canonical summary, user]` and the summary is the only summary-shaped row.
- Multi-summary test: persist two canonical summary rows plus a user row; assert only the last is restored and one warning naming the dropped count and session id is logged (exercise via `caplog`).
- Boundary test: mirror `test_undo_floor_converts_boundary_to_index` but with a canonical summary in the snapshot; assert the floor lands on the first post-compression turn, i.e. one index further than the forged-row case because the summary now occupies a slot.

## Alternatives considered

- Round-trip through the real DB here: rejected; the round-trip lives in the compression-consistency file (Row 06); this file exercises `restore_session` directly with the stubbed API.
- Import `CONVERSATION_SUMMARY_PREFIX`: rejected; the Plan keeps tests on the literal prefix, and the value is stable under the rename.

## Implementation
### Target file
`tests/agent/test_session_restore.py`

### Procedure
1. In `TestRestoreSession`, add `test_summary_restored_after_canonical_prompt` (new): build a ctx with a canonical-summary persisted row and a current prompt; assert `ctx.conv.history` is `[prompt, summary, ...]` with exactly one summary-shaped row.
2. Add `test_extra_summary_rows_drop_last_with_warning` (new): two canonical-summary rows + user row; assert the last is restored, extras dropped, and a warning is captured.
3. Add `test_undo_floor_counts_restored_summary` (new): canonical summary in the snapshot with `undo_floor_id` set; assert the floor indexes the first post-compression turn.
4. Add `test_restore_with_summary_is_idempotent` (new): two restores over the same summary-bearing rows produce equal histories.

### Method
```python
def _summary_row(content: str) -> dict:
    return {"role": "system", "content": f"[Conversation summary]\n{content}"}

async def test_summary_restored_after_canonical_prompt(self) -> None:
    ctx = _make_ctx(
        messages=[
            {"role": "system", "content": "old prompt from DB"},
            _summary_row("prior turns"),
            {"role": "user", "content": "q1"},
        ],
        system_prompt_content="Current canonical prompt.",
    )
    await restore_session(ctx, session_id=3)
    assert [m["role"] for m in ctx.conv.history][:2] == ["system", "system"]
    assert ctx.conv.history[0]["content"] == "Current canonical prompt."
    assert ctx.conv.history[1]["content"].startswith("[Conversation summary]")
    assert sum(1 for m in ctx.conv.history if m["role"] == "system") == 2

async def test_extra_summary_rows_drop_last_with_warning(self, caplog) -> None:
    ctx = _make_ctx(
        messages=[
            _summary_row("first"),
            _summary_row("second"),
            {"role": "user", "content": "q1"},
        ],
        system_prompt_content="Canonical.",
    )
    with caplog.at_level(logging.WARNING, logger="agent.services.session_restore"):
        await restore_session(ctx, session_id=17)
    summaries = [m for m in ctx.conv.history if m["content"].startswith("[Conversation summary]")]
    assert len(summaries) == 1
    assert summaries[0]["content"].startswith("[Conversation summary]\nsecond")
    assert any("extra summary" in r.getMessage() for r in caplog.records
               if r.levelno == logging.WARNING)
```
The boundary and idempotency tests follow the shape of `test_undo_floor_converts_boundary_to_index` and `test_restore_is_idempotent_for_orphan_session`, substituting a canonical summary for the forged `"[summary]"` row.

### Details
- The new tests are additive; the existing forged-row and no-prompt tests stay and keep passing, confirming only the canonical shape is newly restored.
- Stale-reference marks: none created here; `restore_session` and `_make_ctx` already exist.

## Compatibility considerations

- Purely additive tests; no existing test is modified, so the regression set (`test_session_restore.py`) keeps its pinned behaviors.

## Security considerations

- The forged-row assertion re-confirms that a system row without the canonical prefix cannot become an instruction through restore.

## Rollback considerations

- Remove the added tests.

## Validation plan

- `uv run pytest tests/agent/test_session_restore.py -v` — the four new tests fail on the pre-change code and pass after; the existing restore tests pass unchanged (AC-6).
- Static: `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/`.

## Completion criteria

- The four new tests exist, fail before the Phase 3–4 changes, and pass after; the existing restore tests pass unchanged; the restored history holds exactly one canonical summary right after the current prompt.

## Out of Scope

- The shared constant/predicate (Row 01), restore (Row 02), persistence (Row 03), the round-trip test (Row 06), and the docs (Rows 08–10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261105-134431 | 20261105-135519 | red demo on HEAD worktree (4 failed, 23 passed pre-change); added 4 tests + _summary_row helper in test_session_restore.py |
| 2 | Add or update tests per Validation plan | Completed | — | 20261105-135519 | this row 4 new tests pass after change; 27 total passed; existing restore tests unchanged |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261105-135519 | full suite 11547 passed; diff-cover 88% shortfall is Row 03's untested branches (174,182), covered at Row 05 cycle |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261105-135519 | N/A: no test-file docs in scope |

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
- **Requirement ID**: `REQ-005` (restore, forged-row, multi-summary, undo-boundary, idempotency tests), `AC-2`, `AC-3`, `AC-4`, `AC-6`
- **Source issue**: issues/done/20261031-180437_restoresummary001_session-load-drops-summary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-115505_restoresummary001_session-load-drops-summary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-072108
- **Related target files**: tests/agent/test_session_restore.py