## Goal

Restrict the service sync to hot-reloadable values so startup-only context limits never reach the live
`HistoryManager`, and expose the per-service prepare calls the transaction drives (REQ-003,
startup-only fields stay pending; REQ-006, service restore; REQ-013, dead code).

## Scope
**Release unit**: R2-typed-registry

## Assumptions
- Verified against current source: `config_service_sync.py:62-68` passes `context_char_limit`,
  `context_compress_turns`, and `context_token_limit` to `HistoryManager.apply_config`, and
  `ServiceSyncer.__init__` (`config_service_sync.py:28-29`) already takes only `ctx`. The unused
  `llm_cfg` and `tool_cfg` constructor parameters the Issue names were already removed, so REQ-013 has
  no target here.
- `HistoryManager.apply_config` (`scripts/agent/history.py:121`) stays the restart-time entry; the
  sync path must not call it with startup-only values.
- Verified against current source: the three startup-only limits are the only registry-backed values the
  history sync passes; the fourth argument, `tokenize_url` (`config_service_sync.py:66`), is not a
  registry entry. Whether it stays synced after this change is 不明 and must be decided during
  implementation — the Plan's commit order names a `HistoryManager` commit step, which is empty unless a
  hot-reloadable history value exists.

## Design decisions
- The sync layer calls each service's prepare method and returns the undo tokens to the transaction
  (row 7) rather than applying values itself, so commit and rollback live in one place.
- Only entries `registry_for(section)` returns are synced, which is the same set the registry declares
  hot-reloadable (row 4).

## Alternatives considered
- Keeping the sync layer as the applier and giving the transaction a per-service undo — rejected: the
  sync layer would then hold a second commit path with no snapshot.

## Implementation
### Target file
`scripts/agent/services/config_service_sync.py`

### Procedure
Sync only hot-reloadable values, stop passing the three startup-only context limits to
`HistoryManager.apply_config`, and expose the service prepare calls the transaction uses.

### Method
- `sync_all` returns the undo tokens row 7 records instead of a `SyncResult` of applied names alone.
- The LLM sync keeps the values `LlmHotConfigHandler.apply_one` already accepts.

### Details
- `RuntimeToolRegistry.apply_policy` is still called for the tool policy fields, which are
  hot-reloadable; only the three context limits are removed from the call.

## Compatibility considerations
- `tests/agent/services/test_config_reload.py` asserts that startup-only limits reach the live
  `HistoryManager`; those assertions are retargeted in row 34 before this change lands.

## Security considerations
- No configuration value appears in the sync result or in error text.

## Rollback considerations
- Revert the Phase 2 commit; the syncer holds no state beyond the context reference.

## Validation plan
- `uv run pytest tests/agent/services/test_config_reload.py -q`
- `uv run ruff check scripts tests`, `uv run mypy scripts`

## Completion criteria
- A startup-only payload leaves `HistoryManager` unchanged, and every applied service change has an
  undo token recorded by the transaction.

## Out of Scope
- The transaction itself (row 7) and the per-service snapshot APIs (rows 16, 17, 18).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-154000 | 20261125-163000 | no constructor parameter removal: already done hist_mgr.apply_config block removed; ServiceSyncer syncs only llm and runtime_tools; undo-token return deferred to row 7 (R4) |
| 2 | Add or update tests per Validation plan | Completed | 20261125-154000 | 20261125-163000 | row 34 tests/agent/commands/test_agent_cmd_config.py retargeted: test_startup_only_history_limits_are_not_synced asserts apply_config is never called |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-154000 | 20261125-163000 | tokenize_url stays restart-required and outside the registry: the docs key table marks it RESTART and it is not a registry entry |

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
- **Requirement ID**: REQ-003 (startup-only fields stay pending), REQ-006 (service snapshot and restore), REQ-013 (dead reload code removed); AC-2, AC-3
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `scripts/agent/services/config_service_sync.py`