## Goal

Give the LLM config handler a snapshot and restore pair around `apply_one`, so the transaction can
undo an LLM change during a failed commit (REQ-006, service snapshot and restore).

## Scope
**Release unit**: R4-transaction-and-restore

## Assumptions
- Verified against current source: `LlmHotConfigHandler.apply_one` (`llm_hot_config.py:22`) is a
  `setattr` on the passed instance and keeps nothing to restore; `apply_config`
  (`llm_hot_config.py:27`) is the restart-time entry and is unchanged here.
- The handler mutates the live `LLMClient` instance through the private attributes named by
  `HOT_CONFIG_FIELDS` (`llm_hot_config.py:10`), so restore must write values back into the same object
  rather than replace it (Plan `Assumptions`). `snapshot()` and `restore()` take the instance, matching
  the existing `@staticmethod` shape.
- Verified against current source: `apply_one` has no caller in `scripts/`; the production hot-reload
  entry is `LLMClient.apply_config` (`llm_client.py:83`), which delegates to
  `LlmHotConfigHandler.apply_config` (`llm_client.py:96`). `apply_one` is reached only from
  `tests/shared/test_llm_hot_config.py`.
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
  unaffected. `apply_one` has no production caller today, so the token is consumed by the new callers:
  `ServiceSyncer` (row 10) collects it and the transaction (row 7) replays it.
- `LLMClient.apply_config` and `LlmHotConfigHandler.apply_config` keep their current signatures; the
  snapshot and restore pair is added alongside them, not in place of them.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-194130 | 20261125-194130 | R4-transaction-and-restore 20261125: implemented as recorded in this procedure's Blocker Log |
| 2 | Add or update tests per Validation plan | Completed | 20261125-194130 | 20261125-194130 | companion test file R4 20261125: targeted run tests/agent/services tests/agent/commands tests/shared tests/agent/test_history_manager.py = 2821 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-194130 | 20261125-194130 | R4 gate 20261125: full suite 14722 passed 5 skipped, diff-cover 100 percent over 482 lines, integration 146 passed 1 skipped, mypy 466 files clean, lint-imports 6 kept, ruff format and check clean, check_module_size OK, generate_reference_table --check no drift, check_docs_structure OK |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | R4 execution (2026-11-25): `ServiceSnapshot` and `UndoToken` are imported from the new leaf module `scripts/shared/config_undo.py`, because `.importlinter`'s `shared-is-leaf` contract forbids `shared` importing `agent`. `snapshot` and `restore` cover exactly `HOT_CONFIG_FIELDS`, and `apply_one` returns the token that undoes only the field it wrote | Yes | 2026-11-25 |

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