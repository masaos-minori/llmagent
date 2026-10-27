# Implementation Procedure: Add `DeletedRow` (new) dataclass and extend `UndoResult` with `deleted_rows` (new)

## Goal

Carry the exact set of rows the DB undo step deletes across the service boundary so the memory side can trim by tail-matching row identity instead of an independent index computation. (`REQ-001`, `REQ-005`)

## Scope

One production file, `scripts/agent/services/models.py`. Two additive changes:

1. A new frozen `DeletedRow` (new) dataclass (`message_id`, `role`, `content`, `tool_call_id`).
2. A new `deleted_rows: list[DeletedRow]` field on `UndoResult` (default empty).

No change to any other dataclass, field, or the ordering/existence of existing `UndoResult` fields.

## Assumptions

- `models.py` uses stdlib `dataclasses` `@dataclass(frozen=True)` (see the adjacent `SessionRestoreResult` L111-117 and `UndoResult` L119-128); `DeletedRow` (new) follows the same pattern.
- `session_message_repo.py` will import `DeletedRow` (new) from `agent.services.models` — consistent with the repo already importing `LLMMessage` from `shared.types` (L12). If an import cycle appears (repo → services), the dataclass stays in `models.py` and the repo constructs plain tuples; this doc does not resolve that mechanic (implementation procedure confirms). `models.py` has no agent-layer imports today.
- `UndoResult` is a frozen dataclass with a required `n_removed` and optional `block_reason`; adding a trailing field with a default keeps every existing construction site valid.

## Design decisions

- `DeletedRow` (new) mirrors the columns the repo SELECTs for a deleted row (`message_id, role, content, tool_call_id`) — exactly what the memory tail-match needs (role + tool_call_id exact; content when present). Frozen so callers cannot mutate the returned identity.
- `UndoResult.deleted_rows` defaults to `[]` (empty list) so the DB-blocked path (`_undo_blocked()`) and any caller that does not populate it keep working unchanged; `n_removed`/`block_reason` semantics are untouched.

## Alternatives considered

- Returning raw tuples `(message_id, role, content, tool_call_id)` — rejected: a typed dataclass documents the shape at the call site and survives mypy; the Plan names `DeletedRow` (new) as the boundary type (REQ-001).
- Adding the field without a default — rejected: would break `_undo_blocked()` and the command-layer consumer (`cmd_context.py` L128-136 builds `UndoResult` positionally by name); the default preserves REQ-005 backward compatibility.

## Implementation

### Target file
`scripts/agent/services/models.py`

### Procedure
1. Insert a new frozen dataclass `DeletedRow` (new) immediately before `UndoResult` (L119), matching the surrounding `@dataclass(frozen=True)` style.
2. Add `deleted_rows: list[DeletedRow] = field(default_factory=list)` to `UndoResult`, after `block_reason`.

### Method
Two edits in one file: add one dataclass, add one field with a default. No other symbol touched.

### Details
- New dataclass (new):
  ```python
  @dataclass(frozen=True)
  class DeletedRow:
      """A single row deleted by the row-returning DB undo step (REQ-001).

      Carries the identity the memory side needs to tail-match: message id,
      role, content, and tool_call_id. Content is stored as-is (None when the
      DB column is NULL); the memory match treats content as optional.
      """

      message_id: int
      role: str
      content: str | None
      tool_call_id: str | None
  ```
- `UndoResult` becomes:
  ```python
  @dataclass(frozen=True)
  class UndoResult:
      """Result of undoing a conversation action.

      `block_reason` is set when the undo was refused because the last turn is at or
      before the compression boundary; otherwise it is `None`. `deleted_rows` (new) holds
      the exact rows the DB step removed (ascending `message_id`) so the memory side
      can trim by identity; empty when blocked or nothing was removed (REQ-001, REQ-005).
      """

      n_removed: int
      block_reason: str | None = None
      deleted_rows: list[DeletedRow] = field(default_factory=list)
  ```
- `field` must be imported from `dataclasses` if not already (the module already uses `field(default_factory=...)` on L104/106/107, so the import is present).

## Compatibility considerations

- `UndoResult` gains a field with a default; every existing construction (`UndoResult(n_removed=removed)`, `UndoResult(n_removed=0, block_reason=...)`) remains valid. `cmd_context.py` reads only `block_reason`/`n_removed` (L128-136), unaffected.
- `DeletedRow` (new) is additive and frozen; no existing code references it until the repo populates it (row 02).

## Security considerations

- `DeletedRow` (new) carries only row identity (id/role/content/tool_call_id) already read from the DB; no new injection or untrusted-execution surface. Content is echoed verbatim into the log only on the fallback path (row 04), subject to the same logging controls as today.

## Rollback considerations

- Single logical commit touching `models.py` and its tests; rollback is `git revert`. No config, schema, or deployed-state change.

## Validation plan

- Static: `uv run ruff check scripts/agent/services/models.py` and `uv run mypy --no-namespace-packages scripts/agent/services/models.py` — clean.
- Consumers: `uv run pytest tests/agent/ -q -k "undo"` — `UndoResult` construction sites still pass with the new default field.
- Full suite: `uv run pytest tests/` green.

## Completion criteria

- `DeletedRow` (new) exists as a frozen dataclass with `message_id`, `role`, `content`, `tool_call_id`.
- `UndoResult.deleted_rows` (new) exists with a default of `[]`; existing `n_removed`/`block_reason` fields and their semantics are unchanged.
- mypy/ruff clean.

## Out of Scope

- Populating `deleted_rows` (new) (row 02, repo).
- Trimming memory by the returned set (row 04, undo_service).
- Any caller update beyond keeping `UndoResult` backward compatible (REQ-005).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `DeletedRow` (new) dataclass and `UndoResult.deleted_rows` (new) field with default `[]` | Pending | — | — | |
| 2 | Run the validation sequence (static + undo consumers) | Pending | — | — | |

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
- **Related target files**: scripts/agent/services/models.py
