# Implementation Procedure: Drive the memory trim from the deleted-row set with a reload fallback

## Goal

Make `/undo` restore memory/DB parity (REQ-007): trim memory by tail-matching the exact rows the DB deleted (row 02), with a documented reload-from-DB fallback when the deleted rows cannot be matched contiguously, and log the same `message_id`s on both sides (REQ-002, REQ-003, REQ-004).

## Scope

One production file, `scripts/agent/services/undo_service.py`. Rewrite `undo_last_turn`'s reconciliation logic and add one matching helper. No other function changed.

## Assumptions

- After row 03, `ctx.session.undo_last_turn()` returns `list[DeletedRow]` (ascending `message_id`, `[]` when blocked), not an `int`.
- `ctx.conv.history` is a list of `LLMMessage` dicts; memory-only `_memory_injected`/`_ephemeral` markers are dict keys present on some entries but never stored in the DB (`scripts/agent/message_schema.py` L20).
- `ctx.conv.fetch_messages` / the session load boundary builds `LLMMessage` dicts from the DB — the fallback reuses that builder rather than reconstructing dicts by hand. Confirm the exact accessor on `ctx.conv` before editing (e.g. `ctx.conv.history = <fetched remaining rows>`).
- Overlap with `sess007` on `session.py`: sess007 touches `set_title`; this row touches `undo_service.py` (a different module). Disjoint.
- `stat_turns` decrement and `UndoResult` reporting semantics stay as today (Plan Assumptions).

## Design decisions

- Keep the existing boundary gate unchanged: search memory for the last user message at index >= `ctx.conv.undo_floor`; `None` → blocked (unchanged).
- Replace the independent `cut_idx` computation (L30-52) with tail-matching against `deleted_rows` (new):
  - `_match_deleted_tail(history, deleted_rows)` (new) walks the memory tail backwards, matching `deleted_rows` (new) in reverse by `(role, tool_call_id, content)` (content optional when the DB row is NULL), tolerating memory-only artifacts. Returns the cut index (everything after it equals the deleted set) or `None` when the match is ambiguous/non-contiguous.
  - A full match trims `ctx.conv.history = history[:cut]`, extended by the existing artifact walk-back.
- On `None` (ambiguous — e.g. the DB tail has orphan rows absent from memory, T-003): reload the remaining conversation from the DB (`ctx.conv.history = fetched remaining rows`) and log a warning with the deleted `message_id`s. Marker loss on surviving rows is an accepted, logged consequence of the fallback only (REQ-003).
- Single parity log line listing the deleted ids and the memory side's matched/reloaded state (REQ-004).

## Alternatives considered

- Keeping the independent `cut_idx` (today's behavior) — rejected: it cannot converge on a diverged state (REQ-007); identity-based matching is required.
- Always reloading from the DB — rejected: the Plan adopts match-first, reload-fallback (issue AI instruction tie-breaker); matching preserves `_memory_injected`/`_ephemeral` markers on the primary path, whereas reload drops them.

## Implementation

### Target file
`scripts/agent/services/undo_service.py`

### Procedure
1. Add `_match_deleted_tail(history, deleted_rows) -> int | None` (new) next to `_undo_blocked`.
2. Rewrite `undo_last_turn`: replace the `cut_idx` walk-back (L42-52) with the identity-match + reload-fallback flow; change the `removed == 0` guard to `not deleted_rows`.
3. Update the module docstring to reflect the parity contract.

### Method
Add one helper; rewrite one function body. No new public symbols.

### Details
- New helper (new):
  ```python
  def _match_deleted_tail(
      history: list[dict], deleted_rows: list["DeletedRow"]
  ) -> int | None:
      """Return the cut index whose tail equals *deleted_rows*, else None.

      Walks the memory tail backwards, matching deleted_rows in reverse by
      (role, tool_call_id, content) with content optional when the DB row is
      NULL. Memory-only _memory_injected/_ephemeral artifacts are tolerated
      (skipped). Returns the index at which the matched suffix begins (after
      stripping any trailing artifacts), or None when the deleted rows do not
      form a contiguous matchable tail (ambiguous -> caller reloads, REQ-003).
      """
      if not deleted_rows:
          return None
      j = len(deleted_rows) - 1
      i = len(history) - 1
      while j >= 0 and i >= 0:
          msg = history[i]
          if msg.get("_memory_injected") or msg.get("_ephemeral"):
              i -= 1  # tolerate a memory-only artifact in the walk-back
              continue
          dr = deleted_rows[j]
          if msg.get("role") != dr.role:
              return None
          if msg.get("tool_call_id") != dr.tool_call_id:
              return None
          if dr.content is not None and msg.get("content") != dr.content:
              return None
          j -= 1
          i -= 1
      if j < 0:
          cut = i + 1
          while cut > 0 and (
              history[cut - 1].get("_memory_injected")
              or history[cut - 1].get("_ephemeral")
          ):
              cut -= 1
          return cut
      return None
  ```
- Rewritten `undo_last_turn`:
  ```python
  def undo_last_turn(ctx: AgentContext) -> UndoResult:
      """Roll back the last turn, gated by the compression boundary, restoring
      memory/DB parity by trimming memory from the exact rows the DB deletes.
      """
      last_user_idx = next(
          (
              i
              for i in range(len(ctx.conv.history) - 1, ctx.conv.undo_floor - 1, -1)
              if ctx.conv.history[i]["role"] == "user"
          ),
          None,
      )
      if last_user_idx is None:
          return _undo_blocked()
      deleted_rows = ctx.session.undo_last_turn()  # DB first (row 03); list[DeletedRow]
      if not deleted_rows:  # blocked by the DB boundary
          return _undo_blocked()
      cut = _match_deleted_tail(ctx.conv.history, deleted_rows)
      if cut is None:
          # Ambiguous match (e.g. orphan DB rows absent from memory): reload the
          # remaining conversation from the DB and log the decision (REQ-003).
          remaining = <fetched remaining rows from DB via ctx.conv>
          ctx.conv.history = remaining
          logger.warning(
              "Undo: ambiguous match for %d deleted row(s) (%s); reloaded memory "
              "from DB to restore parity",
              len(deleted_rows),
              ", ".join(str(r.message_id) for r in deleted_rows),
          )
          return UndoResult(n_removed=len(deleted_rows), deleted_rows=deleted_rows)
      ctx.conv.history = ctx.conv.history[:cut]
      ctx.stats.stat_turns = max(0, ctx.stats.stat_turns - 1)
      logger.info(
          "Undo: removed %d messages (ids %s); memory trimmed to parity",
          len(deleted_rows),
          ", ".join(str(r.message_id) for r in deleted_rows),
      )
      return UndoResult(n_removed=len(deleted_rows), deleted_rows=deleted_rows)
  ```
- `UndoResult(n_removed=..., deleted_rows=deleted_rows)`: `n_removed` now equals `len(deleted_rows)` (the DB deleted exactly these). `models.py` (row 01) gives `UndoResult` its `deleted_rows` (new) field.
- `<fetched remaining rows from DB via ctx.conv>`: resolve the exact accessor at implementation time (confirm how the session load boundary exposes fetched `LLMMessage` dicts); do not invent a method.

## Compatibility considerations

- `_undo_blocked()` is unchanged; the blocked path still returns `block_reason` set, `n_removed=0` (REQ-005). `cmd_context.py` consumes only `block_reason`/`n_removed`, unaffected.
- Artifact walk-back behavior is preserved on the primary path (`test_regression_undo_artifact.py` passes after its return-type adaptation, row 06; AC-005).
- The `deleted_rows` (new) field on the returned `UndoResult` is new but additive (row 01).

## Security considerations

- No new injection surface: matching compares values already in memory/DB; the reload path reads via the existing DB fetch. The warning log lists `message_id`s (non-sensitive identifiers) only.

## Rollback considerations

- Single logical commit touching `undo_service.py`, `session.py` (row 03), `session_message_repo.py` (row 02), `models.py` (row 01), the test modules (rows 05-07); rollback is `git revert`. No schema/migration.

## Validation plan

- Unit (new parity): `uv run pytest tests/agent/test_undo_db_memory_parity.py -q` — T-001..T-004 pass (row 07).
- Regression: `uv run pytest tests/agent/test_agent_session.py tests/agent/test_regression_undo_artifact.py tests/agent/test_session_memory_boundary.py tests/agent/test_history_compression_consistency.py -q` — gates pass (AC-003, AC-005).
- Command layer: `uv run pytest tests/agent/commands/test_agent_cmd_context.py -q` — `UndoResult` consumption unchanged (AC-002).
- Static: `uv run ruff check scripts/agent/services/undo_service.py` and `uv run mypy --no-namespace-packages scripts/agent/services/undo_service.py` — clean.
- Full suite: `uv run pytest tests/` green.

## Completion criteria

- On a healthy session, memory trims to exactly the deleted-row set (roles/contents/tool rows match `fetch_messages`).
- On injected divergence (orphan DB tail), undo reloads memory from the DB and logs the decision (AC-001, AC-004).
- Artifact walk-back unchanged (AC-005); boundary gate and `UndoResult.block_reason`/`n_removed` semantics unchanged (AC-002, AC-003).
- mypy/ruff clean.

## Out of Scope

- Adding `DeletedRow` (new) / `UndoResult.deleted_rows` (row 01).
- The repo undo method (row 02).
- Re-pointing `session.undo_last_turn` (row 03).
- Test and doc updates (rows 05-08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_match_deleted_tail` (new); rewrite `undo_last_turn` for identity-match trim + reload fallback + parity log | Completed | 20261028-094316 | 20261028-094316 |  |
| 2 | Run the validation sequence (parity + regression gates + static) | Completed | 20261028-094316 | 20261028-094316 |  |

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
- **Requirement ID**: `REQ-002`, `REQ-003`, `REQ-004`, `REQ-007`
- **Source issue**: issues/20261026-224959_undo002_undo-db-memory-set-consistency.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-074657_undo002_undo-db-memory-set-consistency.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-214625
- **Related target files**: scripts/agent/services/undo_service.py