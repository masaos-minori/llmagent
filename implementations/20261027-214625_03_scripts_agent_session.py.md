# Implementation Procedure: Re-point `session.undo_last_turn` to the repo method and return `list[DeletedRow]`

## Goal

Remove the inline SQL from `AgentSession.undo_last_turn` and delegate to the new repo method (`session_message_repo.undo_deleted_rows`), changing its return type from `int` to `list[DeletedRow]` (`[]` when blocked) so the deleted-row identity crosses to the service layer. (`REQ-001`, `REQ-005`)

## Scope

One production file, `scripts/agent/session.py`. Rewrite the body of `undo_last_turn` (L224-269) to delegate. No other method changed.

## Assumptions

- `session.py` currently owns the undo SQL inline (L235-263). The repo method (row 02) now owns that SQL; `session.undo_last_turn` becomes a thin facade.
- The only production caller is `undo_service.undo_last_turn` (undo_service.py L48), which will consume `deleted_rows` (new) (row 04). `cmd_context.py` never calls `session.undo_last_turn` directly (it consumes `UndoResult`), so the return-type change does not reach it.
- `session.py` constructs its own `SessionMessageRepository` (or has one available) the same way other facade methods do; confirm the existing instantiation pattern at the top of the class before editing.
- Overlap with `sess007` on `session.py`: sess007 edits `set_title` (L170-180); this row edits `undo_last_turn` (L224-269). Disjoint members and edit sites → Compatible.

## Design decisions

- `undo_last_turn` keeps its public contract of "gated by the `/undo` boundary, returns nothing-undoable signal" but now expresses "nothing undoable" as an empty list instead of `0`. The boundary gate and DB-first ordering move entirely into the repo method (row 02); this method just forwards `self.session_id` and returns the result.
- Return type annotation changes to `list[DeletedRow]`.

## Alternatives considered

- Keeping a count-returning wrapper that also returns `len(rows)` — rejected: the Plan requires the return type itself to become `list[DeletedRow]` (REQ-001, REQ-005); callers must see identity, not a derived count.
- Moving the gate into the service layer — rejected: DB-first ordering and the boundary gate must stay with the delete (REQ-006); the repo is the correct owner.

## Implementation

### Target file
`scripts/agent/session.py`

### Procedure
1. Replace the body of `undo_last_turn` (L224-269) with a delegation that forwards `self.session_id` to the repo method and returns its result.
2. Update the return-type annotation to `list[DeletedRow]` and import `DeletedRow` (new) from `agent.services.models` (guarded against a cycle; a local import inside the method is acceptable).
3. Update the docstring to describe the `list[DeletedRow]` return and `[]` = blocked.

### Method
One method rewrite + one import. No new members beyond the return type.

### Details
- New `undo_last_turn`:
  ```python
  def undo_last_turn(self) -> list["DeletedRow"]:
      """Delete the last turn, gated by the /undo compression boundary.

      Delegates to SessionMessageRepository.undo_deleted_rows (row 02): the repo
      reads the boundary, finds the last user row, deletes every row at/after it
      in one transaction, and returns those rows ascending by message_id. Returns
      [] when nothing is undoable (no user message, or the last user turn is
      at/before the boundary). Callers update atomically (REQ-005).
      """
      repo = SessionMessageRepository(session_id=self.session_id)
      return repo.undo_deleted_rows(self.session_id)
  ```
- If the class already holds a repository instance, reuse it instead of constructing one per call (match the surrounding facade style).
- `DeletedRow` (new) is referenced only in the annotation; with `from __future__ import annotations` (confirm present at top of session.py) the string form `"DeletedRow"` needs no runtime import. If the module lacks that import, add a guarded local import in the method body.

## Compatibility considerations

- Return-type change is confined to `undo_last_turn`; the sole production caller (undo_service) is updated in row 04, and the two test modules (rows 05/06) in the same atomic pass (REQ-005). No other caller exists repo-wide.
- Behavior preserved: still `[]`/blocked at the boundary, still DB-first, still one turn-sized tail.

## Security considerations

- No new DB surface: the query is identical to the removed inline SQL, now owned by the repo. Parameterized by `session_id` + `message_id`.

## Rollback considerations

- Single logical commit across `session.py`, `session_message_repo.py` (row 02), `models.py` (row 01), `undo_service.py` (row 04), and the two test modules; rollback is `git revert`. No schema/migration.

## Validation plan

- Unit: `uv run pytest tests/agent/test_agent_session.py -q -k "undo"` — updated cases assert row lists (row 05).
- Regression: `uv run pytest tests/agent/test_regression_undo_artifact.py -q` — updated assertions (row 06).
- Static: `uv run ruff check scripts/agent/session.py` and `uv run mypy --no-namespace-packages scripts/agent/session.py` — clean.
- Full suite: `uv run pytest tests/` green.

## Completion criteria

- `session.undo_last_turn()` returns `list[DeletedRow]` (`[]` when blocked), delegated to the repo method.
- Inline SQL removed; boundary gate and DB-first ordering retained in the repo. mypy/ruff clean.

## Out of Scope

- Adding the repo method (row 02).
- Consuming the returned rows in the service (row 04).
- Test updates (rows 05/06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite `undo_last_turn` to delegate to the repo method, return `list[DeletedRow]` | Pending | — | — | |
| 2 | Run the validation sequence (static + undo tests) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-005`
- **Source issue**: issues/20261026-224959_undo002_undo-db-memory-set-consistency.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-074657_undo002_undo-db-memory-set-consistency.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-214625
- **Related target files**: scripts/agent/session.py
