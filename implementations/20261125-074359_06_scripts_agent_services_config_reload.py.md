## Goal

Make the reload entry point build its candidate through the startup parser, drive the commit through
the transaction, and stop touching MCP lifecycle state (REQ-002, shared candidate; REQ-005, stage
reporting; REQ-007, no live lifecycle call; REQ-008, restart-only MCP; REQ-013, dead code).

## Scope
**Release unit**: R3-shared-candidate

## Assumptions
- Verified against current source: `apply_config_dict` (`config_reload.py:107`) prepares the four
  validated sections, then `for section_path in ("mcp",)` at `config_reload.py:127` runs the direct
  path, and the commit phase calls `cleanup_server_resources`.
- `_classify_mcp_server_changes` duplicates the module-level `classify_mcp_server_changes` and is
  reached only from tests (`tests/agent/services/test_config_reload.py:92`, `:139`, `:551`, `:1003`,
  `:1024`, `:1288`).
- `_sync_services` (`config_reload.py:200`) accepts `llm_service`, `hist_mgr_service`, and
  `runtime_tools_service` without using them; `ServiceSyncer.__init__` already takes only `ctx`.
- The candidate is built by `build_agent_config(cfg_override=...)` (row 13), which already runs
  `ProductionConfigValidator` (OD-01).

## Design decisions
- The service keeps `apply_config` and `apply_config_dict` as the public entry points; the candidate
  phase and the commit phase are separated so the transaction can own the commit (OD-05).
- MCP definition changes produce pending records only (OD-03); the service records them through
  `PendingConfigState` (new) (row 8) instead of acting on live state.

## Alternatives considered
- Keeping the live `cleanup_server_resources` call for removed servers — rejected: it removes tracking
  data without terminating the process, which is the orphan-process risk AC-4 removes.

## Implementation
### Target file
`scripts/agent/services/config_reload.py`

### Procedure
Build the candidate through `build_agent_config(cfg_override=...)`, prepare with the typed candidate,
drive `ReloadTransaction` (new), record `stage`, stop calling `lifecycle.cleanup_server_resources`, delete
`_classify_mcp_server_changes`, and drop the unused `_sync_services` parameters.

### Method
- The candidate phase performs no mutation; the commit phase runs only after every section and the
  prompt source are prepared.
- `apply_config_dict` returns the outcome with `stage` and `pending` (row 11).

### Details
- `masked_fields` stays a non-registry field handled by the `extra_changed_fields` path
  (`config_reload.py:116-119`); its non-list rejection at `config_reload.py:85-87` is unchanged.
- A removed or moved key such as `tool_safety_tiers` or `approval_risk_rules` is rejected by the
  shared candidate build instead of being silently ignored.

## Compatibility considerations
- Blast radius: this is the only `/reload` entry point; `cmd_config.py` (row 19) reads the outcome,
  and `tests/agent/services/test_config_reload.py` (1327 lines) pins today's behavior and is
  retargeted in row 34.

## Security considerations
- No raw configuration value appears in the outcome or in an error message.

## Rollback considerations
- Revert the Phase 3 commit; the service holds no state beyond the context reference.

## Validation plan
- `uv run pytest tests/agent/services/test_config_reload.py tests/agent/services/test_config_reload_transaction.py -q`
- `uv run pytest tests/agent/test_removed_config_keys_rejected.py -q` (row 39)
- `uv run vulture scripts/agent/services/ --min-confidence 60`
- `uv run ruff check scripts tests`, `uv run mypy scripts`

## Completion criteria
- No live mutation happens before every candidate is prepared; the outcome reports the stage; no
  lifecycle call occurs during reload; the deleted private method has no remaining reference.

## Out of Scope
- The transaction implementation (row 7) and the pending-state model (row 8).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | candidate phase is Phase 3, commit drive is Phase 4 |
| 2 | Add or update tests per Validation plan | Pending | — | — | rows 26, 34, 39 |
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
- **Requirement ID**: REQ-002 (reload candidate through the startup parser), REQ-005 (stage reporting), REQ-007 (no live lifecycle call), REQ-008 (restart-only MCP), REQ-013 (dead reload code removed); AC-1 to AC-6
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `scripts/agent/services/config_reload.py`
