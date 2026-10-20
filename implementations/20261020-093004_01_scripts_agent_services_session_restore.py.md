## Goal

Make `restore_session()` compute the `/undo` compression boundary (`ctx.conv.undo_floor`) so
that (a) a failing `count_messages_up_to()` propagates before any session state is mutated,
and (b) a snapshot row dropped by history validation cannot leave `undo_floor` pointing past
the end of the live rebuilt history.

## Scope

- Reorder the boundary computation in `restore_session()` so `count_messages_up_to()` and
  `_boundary_to_index()` run before `ctx.conv.replace_history()`, before
  `ctx.session.session_id` is reassigned, and before `reset_session_stats(ctx)`.
- Clamp the resulting index to `len(ctx.conv.history)` after `replace_history()` and log a
  warning naming the drift when the clamp binds.
- `_boundary_to_index()` keeps its signature and arithmetic unchanged.

## Assumptions

- `replace_history()` can drop a restored row: `_append_message_locked()` appends nothing when
  `_sanitize_message()` returns `None` (`scripts/agent/context.py` L143-161, L68-87).
- `reset_session_stats()` writes only `ctx.stats` fields and never touches `ctx.conv`
  (`scripts/agent/commands/mixin_base.py` L19-27), so moving the boundary ahead of it cannot
  clobber `undo_floor`.
- `count_messages_up_to()` raises `sqlite3.Error` on DB failure and its docstring says so
  (`scripts/agent/session_message_repo.py` L180-194); it reads only its own connection and its
  `session_id`/`message_id` arguments, so it does not depend on `ctx.session.session_id`.
- `restore_session()` has exactly one caller (`scripts/agent/commands/cmd_session.py` L247),
  confirmed by `rg 'restore_session(' scripts/`.
- The module logger is `logging.getLogger(__name__)` (L23). `logger.info` is currently dropped
  by this host's handler configuration, but a `logger.warning` still reaches stderr through
  `logging.lastResort`, so the new warning is observable without changing logger wiring.

## Design decisions

- Split the boundary work into a pre-mutation part and a post-replace part. `AC-1` requires the
  raise to leave the session untouched, and `replace_history()` is itself a mutation
  (`self.history = []` then append). Computing the count and index first, and clamping plus
  assigning `undo_floor` after the replace, satisfies both requirements with no rollback
  bookkeeping.
- Clamp instead of re-anchoring the arithmetic. `count_messages_up_to()` is a DB `COUNT(*)` over
  the boundary range, so the index does not come from the list passed to `_boundary_to_index()`;
  clamping its result bounds the drift without changing the success path. Clamping is exact when
  the snapshot covers the whole boundary range, and conservative otherwise: with
  `undo_floor = len(history)` the `/undo` scan in `scripts/agent/services/undo_service.py` L33
  (`range(len(history) - 1, undo_floor - 1, -1)`) yields nothing, so a clamp can only withhold
  extra turns, never expose a row below the boundary.
- Log at `WARNING` with the pre-clamp value, the clamped value, and the drop delta; no message
  content is included.

## Alternatives considered

- Pass `ctx.conv.history` to `_boundary_to_index()` instead of `messages` (the originally frozen
  wording). Measured against the current source and rejected: the index comes from the DB count, so
  the swap changed success-path values (case C: index 3 becomes 2 with `len(ctx.conv.history) == 4`)
  and still produced an out-of-range index for a dropped row (case A: `n_snapshot = 3`,
  `len(ctx.conv.history) == 2`, index stays 3) — `/tmp/opencode/probe_boundary_math.py`. See the Plan
  revision note in `plans/done/20261019-210940_plan.md`.
- Recompute the index from the surviving rows only, matching the Issue's literal "compute it from
  the messages that survive `replace_history`". Rejected: surviving rows are a subsequence of the
  injected list with no position mapping back to fetched rows, so the mapping needs a helper in
  `scripts/agent/context.py` — a second target file outside the frozen Plan table. The clamp
  achieves the same safety bound with a conservative, fail-safe error direction.
- Capture the previous `session_id` and roll back on failure. Rejected: with the pre-mutation
  ordering nothing needs rolling back.
- Route the new log through `scripts/shared/logger.py`. Rejected: out of scope here; the
  agent-wide stdlib-logger wiring gap is a separate item and is not a dependency of this change.

## Implementation
### Target file
`scripts/agent/services/session_restore.py`

### Procedure
1. Keep the `fetch_messages()` call and the two guard raises (`SessionNotFoundError`,
   `SessionNoMessagesError`) exactly as they are (L53-57).
2. Insert the pre-mutation boundary block between the guards and the system-prompt rebuild block:
   compute `boundary_index: int | None` from `undo_floor_id`, `count_messages_up_to()`, and
   `_boundary_to_index()`.
3. Leave the `replace_history()` rebuild block (L58-66) unchanged.
4. After `replace_history()` and before `ctx.session.session_id = session_id` (L67), assign
   `ctx.conv.undo_floor`: `0` when `boundary_index is None`, otherwise the clamped value with a
   `logger.warning` when the clamp binds.
5. Keep `reset_session_stats(ctx)`, the `logger.info("Session %s loaded: ...")` line, the
   existing implementation-note comment, and the `SessionRestoreResult` return unchanged.

### Method
Replace the region from L58 through L79 with:

```python
    # Compute the boundary before any session state is mutated (REQ-001): a raised
    # count_messages_up_to() must leave history, session_id, and stats untouched.
    boundary_index: int | None = None
    if undo_floor_id:
        n_snapshot = ctx.session.count_messages_up_to(session_id, undo_floor_id)
        boundary_index = _boundary_to_index(
            n_snapshot,
            messages,
            system_prompt_set=bool(ctx.conv.system_prompt_content),
        )
    if ctx.conv.system_prompt_content:
        system_msgs: list[LLMMessage] = cast(
            "list[LLMMessage]",
            [{"role": "system", "content": ctx.conv.system_prompt_content}],
        )
        non_system = [m for m in messages if m["role"] != "system"]
        await ctx.conv.replace_history(system_msgs + non_system)
    else:
        await ctx.conv.replace_history(messages)
    # convert the persisted boundary row ID into a rebuilt-history index
    # (rows 02/04): nothing in the compressed snapshot is undoable after load.
    if boundary_index is None:
        ctx.conv.undo_floor = 0
    else:
        live_len = len(ctx.conv.history)
        if boundary_index > live_len:
            # replace_history() dropped snapshot rows: clamp to the live history so the
            # floor can never point past its end. Conservative: withholds extra turns
            # from /undo, never exposes a row below the boundary.
            logger.warning(
                "Session %s undo_floor clamped %d -> %d (%d row(s) dropped by history validation)",
                session_id,
                boundary_index,
                live_len,
                boundary_index - live_len,
            )
            boundary_index = live_len
        ctx.conv.undo_floor = boundary_index
    ctx.session.session_id = session_id
    reset_session_stats(ctx)
```

`_boundary_to_index()` (L26-44) is not modified.

### Details
- `boundary_index` is `None` (not `0`) for the no-boundary case so the clamp is skipped when no
  boundary exists; the assignment still writes `ctx.conv.undo_floor = 0`.
- Clamp arithmetic: with a system prompt set, `_boundary_to_index()` returns
  `1 + non-system rows in the snapshot slice`; `len(ctx.conv.history)` equals
  `1 + surviving non-system rows`. The clamp binds only when dropped rows exceed the non-system
  rows lying outside the snapshot slice.
- Case table the implementation must satisfy:

  | Case | `undo_floor` before | after |
  |---|---|---|
  | no boundary row (`undo_floor_id == 0`) | 0 | 0 (unchanged) |
  | success path, no drops | `1 + n_snapshot - system_count` | identical (clamp is a no-op) |
  | drop inside a snapshot that covers all rows | `1 + n_snapshot - system_count` (> `len(history)`) | clamped to `len(history)`, warning logged |
  | drop outside the snapshot | unchanged index (`<= len(history)`) | unchanged, no warning |
  | `count_messages_up_to()` raises | history/session_id/stats already mutated | nothing mutated, exception propagates |

- Line-count impact: the file grows by roughly 10 lines, far below the 16384 B module-size gate
  (current file 3 KB).

## Compatibility considerations

- Public contract unchanged: same signature, same `SessionRestoreResult`, same exception types
  raised from the same guards; `n_messages` still reports the fetched row count (the existing
  L81-83 note about that overstatement stays).
- Import-layer contract unchanged: no new imports, no new cross-layer references, so
  `PYTHONPATH=scripts uv run lint-imports` is unaffected.
- `cmd_session._load_session` continues to catch only `SessionNotFoundError`; `sqlite3.Error`
  propagation behavior is unchanged, only earlier.

## Security considerations

- No change to validation policy: restored rows are still validated as untrusted via
  `_UNTRUSTED_RESTORE_SOURCE`. The clamp runs after validation and cannot re-admit a dropped row.
- The new warning logs only `session_id` and integer counts — no message content, no user data.

## Rollback considerations

- One commit per Plan target; revert that commit restores the previous ordering and index math.
  No schema, config, or deployment artifact is involved.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Targeted tests | `uv run pytest tests/agent/test_session_restore.py -q -p no:randomly` | All existing cases pass unchanged, including `test_undo_floor_converts_boundary_to_index` (`undo_floor == 2`); the new cases from seq 02 pass |
| Wider agent regression | `uv run pytest tests/agent -q -p no:randomly` | No regressions in `cmd_session` / undo / conversation-state tests |
| Lint and format | `uv run ruff check scripts/agent/services/session_restore.py` and `uv run ruff format --check scripts/agent/services/session_restore.py` | Clean |
| Types | `uv run mypy --no-namespace-packages --no-incremental scripts/agent/services/session_restore.py` | Clean (`boundary_index: int | None` flow) |
| Import contract | `PYTHONPATH=scripts uv run lint-imports` | Contracts kept |
| Module-size gate | `uv run python tools/check_module_size.py` | rc 0 |
| Full suite (at stream end) | `timeout 1700 uv run pytest tests/ -q -p no:randomly` | No regressions |

## Completion criteria

- `restore_session()` computes `count_messages_up_to()` and `_boundary_to_index()` before
  `replace_history()`, the session_id switch, and `reset_session_stats()`.
- `ctx.conv.undo_floor <= len(ctx.conv.history)` holds on every restore path, and the clamp path
  logs one warning naming the drift.
- The seq 02 tests and all pre-existing `test_session_restore.py` cases pass; ruff/mypy/import
  checks are clean.

## Out of Scope

- `scripts/agent/context.py` sanitization/drop policy.
- The compression path that persists `sessions.undo_floor_message_id`, and `undo_last_turn`
  deletion logic.
- Agent-wide stdlib-logger handler wiring (separate work item).
- Docs under `docs/`: no task-scope mapping in `docs/00_index.md` covers `/undo` boundary
  arithmetic; verify with `rg -l "undo_floor" docs/` before assuming otherwise, and update only a
  mapped file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261020-095800 | boundary block split + clamp clamp + pre-mutation boundary block committed in 5aca07409 |
| 2 | Run the new raise-path and dropped-row tests from seq 02 against this file | Completed | — | 20261020-095800 | `tests/agent/test_session_restore.py` 16 passed in tests/agent/test_session_restore.py |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261020-095800 | targeted pytest, ruff, mypy, lint-imports, module-size gate ruff/format clean; mypy clean; lint-imports 6 kept; module-size gate rc 0; tests/agent 3451 passed, 10 skipped |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261020-095800 | expected N/A — confirm with `rg -l "undo_floor" docs/` N/A: rg -l undo_floor docs/ returns 5 files, none states the restore boundary derivation this change alters; no docs/00_index.md task-scope mapping applies |

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
- **Requirement ID**: `REQ-001`, `REQ-002`
- **Source issue**: `issues/20261019-202042_sess001_restore_session-undo_floor-boundary-breaks-when-boundary-computation-fails-or-snapshot-rows-are-dropped.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261019-210940_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261020-093004
- **Related target files**: `scripts/agent/services/session_restore.py`