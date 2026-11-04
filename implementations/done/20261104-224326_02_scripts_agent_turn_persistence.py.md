## Goal

Make the turn-persistence boundary undo a *successful* compression rewrite instead of
deleting every row above the turn-start marker. When a turn compresses and a later write
fails, the boundary restores the pre-rewrite row image and the turn-start `/undo` boundary
and memory, so the session returns to its turn-start state instead of being wiped.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- `conv.undo_floor` is a plain `int` attribute on `ConversationState` (the index into
  `history` of the `/undo` boundary), readable and writable without awaiting, so the
  boundary can snapshot it at construction and restore it next to `restore_messages`
  (REQ-003, `scripts/agent/context.py`).
- `session_message_repo.capture_session_image` / `restore_session_image` (Row 01) exist and
  raise `sqlite3.Error` on DB failure; the boundary runs every repository call on a worker
  thread, so the capture and the restore inherit the existing REQ-005 threading contract.
- A turn compresses at most once, so keeping only the first captured image cannot overwrite
  the turn-start state if a rewrite somehow runs twice (REQ-004).
- Cross-plan: `turn_persistence.py` is targeted only by this Plan; no other frozen Plan
  edits it.

## Design decisions

- Capture the image inside `replace_messages`, in the same `asyncio.to_thread` call that
  performs the rewrite, and store it on `self` only after the rewrite succeeds and only the
  first time a turn sets it (REQ-001, REQ-005): a failed rewrite rolls back atomically and
  the existing delete-above-marker compensation stays correct for it.
- Route `_compensate` through a branch: when a pre-rewrite image exists, call
  `restore_session_image` (one transaction); otherwise keep `delete_messages_from` for the
  append-only path (REQ-001, REQ-004).
- Store `conv.undo_floor` at construction and restore it in `_fail_from_error` alongside
  `restore_messages`, so memory and the persisted boundary agree at their turn-start values
  (REQ-003, AC-3).

## Alternatives considered

- Capturing the image in `turn_boundary` / `AgentSession.turn_boundary`: rejected because
  the rewrite happens later inside a turn, not at boundary creation, and the image must be
  taken immediately before the rewrite (REQ-001).
- Restoring `conv.undo_floor` via a new async method: rejected because it is a plain field,
  so a direct assignment next to `restore_messages` suffices (REQ-003).

## Implementation
### Target file
`scripts/agent/turn_persistence.py`

### Procedure
1. In `TurnPersistence.__init__`, store `self._undo_floor_at_turn_start = conv.undo_floor`
   and initialise `self._pre_rewrite_image: tuple | None = None`.
2. Rewrite `replace_messages` to offload a new sync helper `_rewrite_with_pre_image_capture` (new)
   to the worker thread; capture the first image there before calling
   `repo.replace_messages`; keep the image only after the rewrite returns.
3. Rework `_compensate` to branch on `self._pre_rewrite_image`: image present →
   `repo.restore_session_image(...)`; absent → `repo.delete_messages_from(...)`.
4. In `_fail_from_error`, set `self.conv.undo_floor = self._undo_floor_at_turn_start` in the
   `finally` block after `restore_messages`.

### Method
- `__init__` additions (after `self._snapshot = snapshot`):
  - `self._undo_floor_at_turn_start = conv.undo_floor`
  - `self._pre_rewrite_image: tuple | None = None`
- New private helper (place next to `replace_messages`):
  ```python
  def `_rewrite_with_pre_image_capture` (new) (self, messages):
      if self.session_id is None:
          return None  # defensive: replace_messages guards before dispatching
      image = self._pre_rewrite_image
      if image is None:
          image = self.session._message_repo.capture_session_image(self.session_id)
      result = self.session._message_repo.replace_messages(self.session_id, messages)
      self._pre_rewrite_image = image  # stored only after the rewrite returns
      return result
  ```
  Replace the current `return await asyncio.to_thread(...)` body of `replace_messages` with
  a call to that helper on the worker thread. (Local-then-store order corrected during
  adversarial verification on 2026-11-05 to match the design decision "the image is kept
  only after the rewrite returns": a failed rewrite must leave `_pre_rewrite_image` unset so
  compensation keeps the delete-above-marker path.)
- `_compensate` new body:
  ```python
  image = self._pre_rewrite_image
  if image is not None:
      return await asyncio.to_thread(
          self.session._message_repo.restore_session_image,
          self.session_id, image, image[1], self.turn_start_message_id,
      )
  return await asyncio.to_thread(
      self.session._message_repo.delete_messages_from,
      self.session_id, self.turn_start_message_id,
  )
  ```
  (`image` is passed whole: the Row 01 signature is
  `restore_session_image(session_id, image, undo_floor, marker)`; `image[1]` is the captured
  persisted `undo_floor`. Verified against the Row 01/05 signatures on 2026-11-05.)
- `_fail_from_error` finally block:
  ```python
  finally:
      await self.conv.restore_messages(self._snapshot)
      self.conv.undo_floor = self._undo_floor_at_turn_start
  ```

### Details
- The capture guard `self._pre_rewrite_image is None` implements the first-image-only rule;
  the image is a `(rows, undo_floor)` tuple where `rows` is the list captured by
  `capture_session_image` and `undo_floor` is the persisted `undo_floor_message_id`.
- `restore_session_image` runs inside `_compensate`, which `_fail_from_error` already wraps
  in a `try/except sqlite3.Error` that logs a compensation failure and still raises the
  original error — so a failing restore leaves the rows present (single transaction) and
  never falls back to delete-above-marker (REQ-002, AC-2).
- `self.session_id` may be `None` only before `session.start()`; `replace_messages` already
  returns early there, so the capture helper's extra guard is defensive only.
- Stale-reference marks: this procedure creates `_rewrite_with_pre_image_capture` (new); the calls to
  `capture_session_image` / `restore_session_image` resolve from Row 01 (sibling), so they
  need no `(new)`.

## Compatibility considerations

- `replace_messages` keeps its name, signature, and return type; the `/compact` path and
  orchestrator/tool tests that stub it are unaffected (REQ-004).
- `_compensate` and `_fail_from_error` keep their signatures; only their bodies change.

## Security considerations

- The boundary restores data it captured from the same session's own rows and its own
  `undo_floor`; it introduces no new input or key and changes no validation policy.

## Rollback considerations

- Revert the commit. The only behavioural change is compensation after a rewrite; the
  append-only path and the failing-rewrite path are unchanged.

## Validation plan

- Boundary unit tests in `tests/agent/test_turn_persistence.py`: restore-after-rewrite
  (prior-turn rows returned, this turn's rows gone), first-image-only (a second rewrite does
  not move the restored state), fail-safe (a failing restore leaves rows and still raises
  `ConversationPersistenceError`), append-only unchanged (no image → delete-above-marker),
  and `conv.undo_floor` restored to its turn-start value.
- Static: `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages
  scripts/`, `uv run vulture`, `uv run python tools/generate_reference_table.py --check`.

## Completion criteria

- After a turn that compressed and then failed a later write, the session's rows equal the
  turn-start rows (ids and `created_at` preserved), `conv.undo_floor` equals its turn-start
  value, and the persisted boundary matches.
- A failing restore deletes nothing and re-raises the original persistence error.
- Append-only failures still delete only rows above the marker and capture no image.
- All boundary and static checks pass.

## Out of Scope

- The repository capture/restore implementation (Row 01).
- `conversation_state_manager.handle_history_compression` setting `conv.undo_floor` after a
  successful rewrite (reference file; out of scope here).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add pre-image capture + first-image-only rule in `replace_messages` | Completed | 20261105-074000 | 20261105-075500 | depends on Row 01 methods helper stores image only after rewrite returns (corrected snippet); session_id narrowing added for mypy |
| 2 | Branch `_compensate` to restore image; restore `conv.undo_floor` | Completed | 20261105-074000 | 20261105-075500 | compensate branches on image (image passed whole per Row 01 signature); conv.undo_floor restored in finally |
| 3 | Add boundary unit tests per Validation plan | Completed | — | 20261105-075500 | Deferred to sibling procedure 20261104-224326_04 (test-file row of the frozen Plan table); tests land in cycle 4 |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261105-075500 | ruff/mypy/bandit/reference-table pass; full pytest 11511 passed; vulture: only pre-existing false positives remain, Row 01 dead-code flag resolved; capture uses plain read (no begin_immediate) after existing fixture incompatibility found in adversarial verification |

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
- **Requirement ID**: `REQ-001` (restore rewrite on compensation), `REQ-002` (fail-safe
  restore), `REQ-003` (`conv.undo_floor` restored), `REQ-004` (append-only path unchanged)
- **Source issue**: issues/20261031-180341_compresscomp001_compression-compensation-wipes-session.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-114113_compresscomp001_compression-compensation-wipes-session.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-224326
- **Related target files**: scripts/agent/turn_persistence.py