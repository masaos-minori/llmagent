## Goal

Give `HistoryManager` a config snapshot and restore pair covering the context limits and the derived
selection policy, so a failed commit can put the manager back to its pre-commit values (REQ-006,
service snapshot and restore; REQ-003, startup-only fields stay pending).

## Scope
**Release unit**: R4-transaction-and-restore

## Assumptions
- Verified against current source: `apply_config` (`history.py:121`) mutates `_char_limit`,
  `_compress_turns`, `_token_limit`, `_tokenize_url` and rebuilds `_selection_policy` from
  `_compress_turns` and `_protect_turns`; nothing captures the previous values.
- The module is 21501 B against the 24576 B `tools/check_module_size.py` gate, so the additions stay
  minimal and the snapshot type lives in the transaction module (row 7).
- Restore writes into the same `HistoryManager` instance, which is the object `ServiceSyncer` and the
  display commands hold (Plan `Assumptions`).

## Design decisions
- The snapshot covers the derived `_selection_policy` as well as the four limits, because restoring the
  limits alone would leave a policy built from the old `compress_turns`.
- `apply_config` stays the restart-time entry and is not converted into a commit-side call; the
  transaction calls the prepare path (row 10) instead.

## Alternatives considered
- Rebuilding the manager from the previous config — rejected: the manager owns conversation state that a
  rebuild would lose.

## Implementation
### Target file
`scripts/agent/history.py`

### Procedure
Add `snapshot_config()` and `restore_config(snapshot)` covering the context limits and the derived
`_selection_policy`.

### Method
- `snapshot_config()` (new) returns the snapshot type defined by row 7.
- `restore_config(snapshot)` (new) writes the values back into the same instance and rebuilds
  `_selection_policy` from the restored `compress_turns`.

### Details
- No other attribute is captured; the plan's UNK-02 applies to `RuntimeToolRegistry` (row 18), not here.

## Compatibility considerations
- Blast radius: `HistoryManager` is the live conversation-state owner; restore must not touch message
  history, only the config-derived fields.

## Security considerations
- No configuration value appears in the snapshot's reporting text.

## Rollback considerations
- Revert the Phase 4 commit.

## Validation plan
- `uv run pytest tests/agent/test_history_manager.py -q`
- `uv run pytest tests/agent/services/test_config_reload_transaction.py -q` (row 26)
- `uv run python tools/check_module_size.py`
- `uv run ruff check scripts tests`, `uv run mypy scripts`

## Completion criteria
- A restore after a failed commit leaves the same `HistoryManager` instance with the pre-commit limits
  and a selection policy consistent with the restored `compress_turns`.

## Out of Scope
- The transaction and the reverse-order rollback (row 7).
- The sync-layer restriction to hot-reloadable values (row 10).

### Companion test files
- `tests/agent/test_history_manager.py`
  - Procedure: assert config snapshot and restore, including that the derived selection policy matches
    the restored `compress_turns`.
  - Validation: `uv run pytest tests/agent/test_history_manager.py -q`

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | module-size gate applies |
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
- **Requirement ID**: REQ-003 (startup-only fields stay pending), REQ-006 (service snapshot and restore); AC-2, AC-3
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `scripts/agent/history.py`, `tests/agent/test_history_manager.py`
