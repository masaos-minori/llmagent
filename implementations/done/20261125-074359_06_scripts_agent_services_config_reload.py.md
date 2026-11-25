## Goal

Make the reload entry point build its candidate through the startup parser, drive the commit through
the transaction, and stop touching MCP lifecycle state (REQ-002, shared candidate; REQ-005, stage
reporting; REQ-007, no live lifecycle call; REQ-008, restart-only MCP; REQ-013, dead code).

## Scope
**Release unit**: R3-shared-candidate

## Assumptions
- Verified against current source: `apply_config_dict` (`config_reload.py:92`) prepares the four
  validated sections, then `for section_path in ("mcp",)` at `config_reload.py:127` runs the direct
  path, and the commit phase calls `cleanup_server_resources` (`config_reload.py:164`).
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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-205000 | 20261125-210919 | candidate phase is Phase 3, commit drive is Phase 4 R3 run 20261125-184431: Phase 3 candidate build (agent_config_payload + build_agent_config override) and pre-mutation classification in place; Phase 4 transaction drive, Phase 5 stop lifecycle.cleanup_server_resources, Phase 6 delete _classify_mcp_server_changes remain in R4/R5/R6 R6 run 20261125: Phase 6 deletion done (_sync_services, _classify_startup_only_fields, ServiceSyncer.sync_all and SyncResult); vulture reports no reload dead code; unit gate green: full suite 14768 passed 5 skipped, diff-cover 100 percent over 660 lines, integration 146 passed 1 skipped, mypy 467 files clean, lint-imports 6 kept |
| 2 | Add or update tests per Validation plan | Completed | 20261125-205000 | 20261125-210919 | rows 26, 34, 39 R3: rows 34 and 39 green (test_config_reload.py 81 passed, test_removed_config_keys_rejected.py 11 passed); row 26 transaction test is the R4 run R6 run 20261125: Phase 6 deletion done (_sync_services, _classify_startup_only_fields, ServiceSyncer.sync_all and SyncResult); vulture reports no reload dead code; unit gate green: full suite 14768 passed 5 skipped, diff-cover 100 percent over 660 lines, integration 146 passed 1 skipped, mypy 467 files clean, lint-imports 6 kept |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-205000 | 20261125-210919 | R3 unit gate: full suite 14667 passed 5 skipped, diff-cover 100 percent, integration 146 passed 1 skipped, mypy and lint-imports clean; final gate runs after the R6 run R6 run 20261125: Phase 6 deletion done (_sync_services, _classify_startup_only_fields, ServiceSyncer.sync_all and SyncResult); vulture reports no reload dead code; unit gate green: full suite 14768 passed 5 skipped, diff-cover 100 percent over 660 lines, integration 146 passed 1 skipped, mypy 467 files clean, lint-imports 6 kept |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | R5 execution (2026-11-25): the live `lifecycle.cleanup_server_resources` call for a removed MCP server is deleted (OD-03). MCP definition changes now only produce pending records, so no reload path touches lifecycle state | Yes | 2026-11-25 |
| 1 | R5 execution (2026-11-25): `_classify_mcp_server_changes` is deleted; `diff_mcp_definitions` in `config_outcome_classification.py` is the single MCP diff, and the service records its result through `PendingConfigState` | Yes | 2026-11-25 |
| 1 | R5 execution (2026-11-25): `apply_config_dict` reached radon D(21) once the degraded guard, the section loop and the pending recording were added. Resolved by extracting `_prepare_section_candidates`, `_refuse_if_degraded` and `_record_pending_candidate`: the function is C(11), below its C(16) baseline | Yes | 2026-11-25 |
| 1 | R6 execution (2026-11-25): the Phase 6 deletion removes `_sync_services` and the `_classify_startup_only_fields` wrapper from this class, and with them the `LLMClient`, `HistoryManager` and `RuntimeToolRegistry` imports the scalar parameters required. `ServiceSyncer.prepare_llm` and `prepare_runtime_tools` are now the only service-apply path (REQ-013) | Yes | 2026-11-25 |
| 1 | R6 execution (2026-11-25): `ServiceSyncer.sync_all` and its `SyncResult` were dead for the same reason — nothing applied a service outside the transaction steps — so they are deleted with the caller rather than left as an unused report type | Yes | 2026-11-25 |
| 2 | R6 execution (2026-11-25): `check_docs_quality.py` flagged the generated API reference because `diff_mcp_definitions` carried its requirement id in the summary line. Resolved by moving `REQ-008` into the docstring body and regenerating the artifact | Yes | 2026-11-25 |

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