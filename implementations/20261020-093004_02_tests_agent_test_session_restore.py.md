## Goal

Add regression coverage for the two `restore_session()` failure paths fixed in seq 01: a raised
`count_messages_up_to()` must leave session state untouched, and a snapshot row dropped by history
validation must leave `undo_floor` clamped to the live rebuilt history length.

## Scope

- Add three tests to `TestRestoreSession` in `tests/agent/test_session_restore.py`.
- Extend the module's `_make_ctx()` helper with the two new inputs the tests need (a raise side
  effect and a pre-existing `undo_floor`), without changing existing helper behavior.

## Assumptions

- The repo idiom for a row that `replace_history()` DROPS (not merely sanitizes) is a row missing
  `content`; `validate_message()` fails with `Missing 'content' field` and `_sanitize_message()`
  returns `None` (`scripts/agent/message_schema.py` L46-84, `scripts/agent/context.py` L68-87,
  L143-161). `tests/agent/test_context_append_message.py` L94-107 already asserts that drop path.
- Measured on the current, unfixed source (`/tmp/opencode/probe_drop_row.py`): with
  `messages = [system, {role: user, no content}, assistant, user]`, `system_prompt_content` set,
  `undo_floor_id = 4`, `n_snapshot = 4` → `len(ctx.conv.history) == 3` while the unclamped index is
  `4`. That out-of-range value is what the new test must pin down as clamped.
- Measured success path (no drops, 4 rows, `n_snapshot = 2`, `undo_floor_id = 2`):
  `len(ctx.conv.history) == 4`, `undo_floor == 2` — identical to the existing
  `test_undo_floor_converts_boundary_to_index`, so the clamp is a no-op there.
- `caplog` capture for these modules uses `caplog.at_level(logging.WARNING, logger="agent.<module>")`
  (`tests/agent/test_context_append_message.py` L58, L103), because the module loggers are
  `logging.getLogger(__name__)` with `propagate=True`.
- Async tests in this file need no marker (repo `asyncio_mode=auto`).

## Design decisions

- Pin the failure path by pre-seeding state, not by asserting defaults: `_make_ctx` sets
  `undo_floor = 0` and `session_id = 0`, so a half-restore would be indistinguishable from an
  untouched session. Seed `ctx.conv.undo_floor = 7` and pre-existing history, then assert both are
  still intact after the raise.
- Assert the invariant (`undo_floor <= len(ctx.conv.history)`) alongside the exact clamped value,
  so the test documents the rule rather than only one arithmetic result.
- Keep the existing tests byte-identical: they are the behavior-lock for the reorder (`AC-3`).

## Alternatives considered

- Drive the dropped-row case through a real SQLite session database. Rejected: `restore_session()`
  reaches the DB only through `ctx.session`, which this file mocks throughout; a DB-backed test
  would add state-isolation surface for no additional coverage (`tests/agent/test_session_restore.py`
  L16-40).
- Assert only `undo_floor != 0` on the raise path, as the Plan's text allows. Rejected: with the
  reordered code the stronger assertion (prior floor retained, history not replaced, stats not
  reset, `session_id` unchanged) is directly observable and cheaper than reasoning about defaults.
- Assert no warning at all in the non-clamping case. Kept as a narrow assertion on the clamp
  message only, so unrelated `agent.context` sanitization warnings (emitted for every restored row)
  cannot make the test brittle.

## Implementation
### Target file
`tests/agent/test_session_restore.py`

### Procedure
1. Add `import logging` and `import sqlite3` to the import block (L6-13); `caplog` is a pytest
   fixture argument, not an import.
2. Extend `_make_ctx()` (L16-40) with two keyword-only parameters, both defaulted so the 13 existing
   call sites are untouched: `count_raises: bool = False` and `prior_undo_floor: int = 0`. Set
   `ctx.conv.undo_floor = prior_undo_floor` in place of the hard-coded `0`, and when
   `count_raises` is true set
   `ctx.session.count_messages_up_to.side_effect = sqlite3.OperationalError("disk I/O error")`.
3. Add the three tests to `TestRestoreSession` (after L186, keeping the existing tests above them).

### Method
```python
    async def test_count_failure_leaves_session_state_untouched(self) -> None:
        msgs = [
            {"role": "system", "content": "[summary]"},
            {"role": "user", "content": "q1"},
        ]
        ctx = _make_ctx(
            messages=msgs,
            system_prompt_content="Canonical.",
            extra_history=[{"role": "user", "content": "live turn"}],
            undo_floor_id=2,
            prior_undo_floor=7,
            count_raises=True,
        )
        with pytest.raises(sqlite3.OperationalError):
            await restore_session(ctx, session_id=77)
        # nothing mutated: history not rebuilt, session not switched, floor not reset to 0
        assert ctx.conv.history == [{"role": "user", "content": "live turn"}]
        assert ctx.session.session_id == 0
        assert ctx.conv.undo_floor == 7
        assert ctx.stats.stat_turns == 0  # MagicMock attribute untouched, not assigned

    async def test_undo_floor_clamped_when_snapshot_row_is_dropped(self, caplog) -> None:
        dropped = cast(LLMMessage, {"role": "user", "_memory_injected": True})  # no content -> dropped
        msgs = [
            {"role": "system", "content": "[summary]"},
            dropped,
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "q2"},
        ]
        ctx = _make_ctx(
            messages=msgs,
            system_prompt_content="Canonical.",
            undo_floor_id=4,
        )
        ctx.session.count_messages_up_to.return_value = 4  # snapshot covers all four rows
        with caplog.at_level(logging.WARNING, logger="agent.services.session_restore"):
            await restore_session(ctx, session_id=43)
        # unclamped index would be 1 + 4 - 1 = 4 against a 3-element live history
        assert len(ctx.conv.history) == 3
        assert ctx.conv.undo_floor == 3
        assert ctx.conv.undo_floor <= len(ctx.conv.history)
        assert any(
            "undo_floor clamped" in record.getMessage()
            for record in caplog.records
            if record.levelno == logging.WARNING
        )

    async def test_drop_outside_snapshot_leaves_index_unchanged(self, caplog) -> None:
        dropped = cast(LLMMessage, {"role": "assistant", "_memory_injected": True})  # no content -> dropped
        msgs = [
            {"role": "system", "content": "[summary]"},
            {"role": "user", "content": "q1"},
            dropped,
            {"role": "user", "content": "q2"},
        ]
        ctx = _make_ctx(
            messages=msgs,
            system_prompt_content="Canonical.",
            undo_floor_id=2,
        )
        ctx.session.count_messages_up_to.return_value = 2  # snapshot is rows 1-2 only
        with caplog.at_level(logging.WARNING, logger="agent.services.session_restore"):
            await restore_session(ctx, session_id=44)
        # index 1 + 2 - 1 = 2 against a 3-element live history: no clamp, no warning
        assert len(ctx.conv.history) == 3
        assert ctx.conv.undo_floor == 2
        assert not any(
            "undo_floor clamped" in record.getMessage() for record in caplog.records
        )
```

Also add `from typing import cast` to the import block if `typing` is not already imported there.

### Details
- The `_memory_injected` key is what makes `validate_message()` fail for an otherwise complete row,
  and the missing `content` is what makes `_sanitize_message()` return `None`; together they are the
  repo's existing way to construct a dropped row without bypassing the type checker
  (`tests/agent/test_context_append_message.py` L101).
- `prior_undo_floor=7` is deliberately out of range for the seeded history: the point is only that
  the raise must not reset it to the fully-undoable default.
- `ctx.stats` remains a plain `MagicMock` attribute, so `ctx.stats.stat_turns == 0` compares against
  an auto-created child mock only if `reset_session_stats()` ran. Assert it stays `0` — the value
  `_make_ctx` never sets — and additionally assert `reset_session_stats` was not called via
  `unittest.mock.patch("agent.services.session_restore.reset_session_stats")`, the same patch target
  the existing `test_reset_session_stats_called` uses (L150-157).
- Expected outcome after seq 01 lands: all 16 tests pass (13 existing + 3 new). Running them before
  seq 01 lands is the red state that proves the tests bite: `test_count_failure_...` fails because
  history is already replaced, and the clamp test observes `undo_floor == 4` with
  `len(ctx.conv.history) == 3`.

## Compatibility considerations

- Existing helper call sites and test bodies are unchanged; only additive keyword parameters are
  introduced, so `AC-3` (existing cases pass unchanged) stays verifiable.
- No `MagicMock` patch targets change, so `tools/check_mock_patch_targets.py` stays clean.

## Security considerations

- The tests construct a forged persisted row on purpose. It stays in the in-memory mock; nothing is
  written to a real session database.

## Rollback considerations

- N/A: revert the commit; the file addition is self-contained.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| New tests fail before seq 01 | `uv run pytest tests/agent/test_session_restore.py -q -p no:randomly -k "count_failure or clamped or outside_snapshot"` | 3 failed (documents that the tests bite) |
| New tests pass after seq 01 | same command | 3 passed |
| Whole file | `uv run pytest tests/agent/test_session_restore.py -q -p no:randomly` | 16 passed |
| Lint/format | `uv run ruff check tests/agent/test_session_restore.py` and `uv run ruff format --check tests/agent/test_session_restore.py` | Clean |
| Types | `uv run mypy --no-namespace-packages --no-incremental tests/agent/test_session_restore.py` (per repo test-typing policy) | Clean |
| Mock-target checker | `uv run python tools/check_mock_patch_targets.py` | No findings |

## Completion criteria

- Three new tests exist in `TestRestoreSession`, each named for the behavior it pins.
- They fail against the pre-fix source and pass after seq 01, with the clamp test asserting both
  the exact clamped value and the `undo_floor <= len(ctx.conv.history)` invariant.
- The 13 pre-existing tests pass unchanged.

## Out of Scope

- `scripts/agent/services/session_restore.py` itself (seq 01).
- `scripts/agent/context.py` sanitization behavior and its existing tests.
- DB-backed integration coverage for the restore path.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend `_make_ctx()` with `count_raises` and `prior_undo_floor` | Completed | — | 20261020-095800 | additive defaults only helper gained count_raises and prior_undo_floor (additive defaults) |
| 2 | Add the three tests to `TestRestoreSession` | Completed | — | 20261020-095800 | confirm the red state before seq 01 lands 3 tests added; 2 fail against the pre-fix source (undo_floor 4 out of range; history already replaced) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261020-095800 | pytest, ruff, mypy, mock-target checker 16 passed; ruff/format clean; check_mock_patch_targets no findings |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261020-095800 | N/A: test-only row N/A: test-only row |

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
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261019-202042_sess001_restore_session-undo_floor-boundary-breaks-when-boundary-computation-fails-or-snapshot-rows-are-dropped.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261019-210940_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261020-093004
- **Related target files**: `tests/agent/test_session_restore.py`