## Goal

Give the LLM config handler a snapshot and restore pair around `apply_one`, so the transaction can
undo an LLM change during a failed commit (REQ-006, service snapshot and restore).

## Scope
**Release unit**: R4-transaction-and-restore

## Assumptions
- Verified against current source: `LlmHotConfigHandler.apply_one` (`llm_hot_config.py:22`) is a
  `setattr` on the passed instance and keeps nothing to restore; `apply_config`
  (`llm_hot_config.py:27`) is the restart-time entry and is unchanged here.
- The handler mutates the live `ctx.cfg.llm` section instance, so restore must write values back into
  the same object rather than replace it (Plan `Assumptions`).
- The snapshot type is defined by the transaction module (row 7); this module returns an instance of
  it, it does not define it.

## Design decisions
- `snapshot()` captures only the fields `apply_one` can change, not the whole instance, so the snapshot
  stays small and the restore cannot overwrite unrelated handler state.
- `apply_one` returns the `UndoToken` the transaction records, which keeps the commit and the rollback
  in one place (row 7).

## Alternatives considered
- Snapshotting every attribute of the handler — rejected as unmaintainable (OD-05 option c).

## Implementation
### Target file
`scripts/shared/llm_hot_config.py`

### Procedure
Add `snapshot()` and `restore(snapshot)` around `apply_one`, and make `apply_one` return the undo token.

### Method
- `snapshot()` (new) returns the current values of the hot-reloadable LLM fields.
- `restore(snapshot)` (new) writes those values back into the same instance.
- `apply_one` keeps its signature and returns `UndoToken` (row 7) instead of `None`.

### Details
- The undo token names the field path, which is what the rollback reporting prints; it does not carry
  the value beyond the snapshot reference.

## Compatibility considerations
- Blast radius: `apply_one` currently returns `None`; callers that ignore the return value are
  unaffected, and the only caller that needs the token is the transaction (row 6).

## Security considerations
- No configuration value appears in the undo token's message.

## Rollback considerations
- Revert the Phase 4 commit; the handler holds no persisted state.

## Validation plan
- `uv run pytest tests/shared/test_llm_hot_config.py -q`
- `uv run pytest tests/agent/services/test_config_reload_transaction.py -q` (row 26)
- `uv run ruff check scripts tests`, `uv run mypy scripts`

## Completion criteria
- A restore after a failed commit leaves the same LLM section instance with the pre-commit values, and
  every `apply_one` call produces an undo token the transaction can replay.

## Out of Scope
- The transaction and the reverse-order rollback (row 7).

### Companion test files
- `tests/shared/test_llm_hot_config.py`
  - Procedure: assert snapshot and restore around `apply_one`, and assert the undo token `apply_one`
    returns names the field it changed.
  - Validation: `uv run pytest tests/shared/test_llm_hot_config.py -q`

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | companion test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-006 (service snapshot and restore); AC-3
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `scripts/shared/llm_hot_config.py`, `tests/shared/test_llm_hot_config.py`
