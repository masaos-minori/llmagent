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
- Verified against current source: the four values `ServiceSyncer` passes today are
  `context_char_limit`, `context_compress_turns`, `context_token_limit` — all `hot_reloadable=False`
  (`config_field_registry.py:45-50`) — and `tokenize_url`, which is not a registry entry at all. After
  row 10 restricts the sync to hot-reloadable registry entries, no value reaches
  `HistoryManager.apply_config` from the reload path. Whether `tokenize_url` stays syncable is 不明 and
  must be decided in row 10; the snapshot and restore pair here covers the commit step the Plan's commit
  order names regardless of that decision.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-194130 | 20261125-194130 | module-size gate applies R4-transaction-and-restore 20261125: implemented as recorded in this procedure's Blocker Log |
| 2 | Add or update tests per Validation plan | Completed | 20261125-194130 | 20261125-194130 | companion test file R4 20261125: targeted run tests/agent/services tests/agent/commands tests/shared tests/agent/test_history_manager.py = 2821 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-194130 | 20261125-194130 | R4 gate 20261125: full suite 14722 passed 5 skipped, diff-cover 100 percent over 482 lines, integration 146 passed 1 skipped, mypy 466 files clean, lint-imports 6 kept, ruff format and check clean, check_module_size OK, generate_reference_table --check no drift, check_docs_structure OK |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | R4 execution (2026-11-25): `snapshot_config` and `restore_config` rebuild `_selection_policy` from the restored `compress_turns` and leave the session counters alone; the token and snapshot types come from `scripts/shared/config_undo.py` | Yes | 2026-11-25 |
| 1 | R4 execution (2026-11-25): no reload step calls them today. Every value the manager reads from a reload (`context_char_limit`, `context_compress_turns`, `context_token_limit`, `tokenize_url`) is registry startup-only, so `CommitPhase.HISTORY` stays in the commit order with no prepared step (REQ-003, AC-2) | Yes | 2026-11-25 |
| 1 | R4 execution (2026-11-25): the file is 23115 B against the 24576 B module-size gate, so the pair had to stay two methods; `tools/check_module_size.py` reports no new violation | Yes | 2026-11-25 |

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