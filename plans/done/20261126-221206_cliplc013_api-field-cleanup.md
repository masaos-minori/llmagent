## Goal
- Remove the confirmed unused public surface in the MCP configuration module and correct stale docstrings, after adversarial verification against current source; the remaining field decisions wait for the open stderr-log plan.

## Priority
Low

## Scope
- **In-Scope**:
  - Remove the four unused public properties of `scripts/shared/mcp_config.py` (`StartupMode.is_persistent`, `StartupMode.requires_subprocess`, `McpServerConfig.needs_health_check`, `McpServerConfig.requires_cmd`), each confirmed to have zero callers.
  - Correct the stale docstring in `scripts/agent/http_lifecycle.py` (documented stderr log location does not match the actual location).
  - Keep `max_stderr_log_size_mb` / `max_stderr_log_files`; the decision is resolved to keep because the open stderr plan's REQ-006 gives each field documented runtime effect (see Dependencies).
- **Out-of-Scope**:
  - New features and the behavior changes of the earlier backlog issues.
  - Stderr rotation enforcement: already assigned to the open stderr plan (REQ-006 there); this Plan must not duplicate it.
  - `scripts/shared/runtime_tool_registry.py`: no confirmed unused surface (see Reference Files); the Issue's claim is disconfirmed.
  - `scripts/agent/session_persister.py`: resolved this cycle — no storage/display constant exists; REQ-004 is N/A and the file is a reference row, not a target.
  - Pass-through facades (`scripts/agent/workflow/state_store.py`, `scripts/agent/services/config_reload.py`): documented as intentional, not duplicate implementations.
- **Dependencies**:
  - Depends on the cliplc005, cliplc006, cliplc007, cliplc008 plans: implementation rows all `Completed` (only deploy hand-offs remain, the user's decision) — closed for implementation purposes.
  - Depends on the cliplc009 plan (open, every Execution Status row `Pending`): its REQ-006 enforcement defines the runtime effect of the stderr rotation fields; the keep decision here is resolved from that plan's frozen design, and only the post-landing AC-3 confirmation waits for it.
  - Related: the agentcfg002 plan removed `McpServerConfig.tool_names`; the current dataclass has no `tool_names` field, so this Plan must not reintroduce it.
  - **Depends on**: `plans/20261126-210258_cliplc009_redaction-stderr-diagnostics.md` | phase 3 | the stderr rotation fields' runtime effect is defined by that Plan's REQ-006 enforcement; the keep-or-remove decision here cannot precede it.

## Background
Source: consolidated CLI REPL and MCP lifecycle backlog (`memo-issue.md`, Issue 13). The Issue's claims were backlog claims marked `Needs confirmation`; this cycle verified each against current source.

## Problem
Public fields and parameters imply capabilities that do not exist or are duplicated. Adversarial verification found the problem is smaller than the Issue states: most claims are already resolved or disconfirmed; what remains is four unused public properties, one stale docstring, and one field decision pending an open dependency.

Disconfirmed claims (verified this cycle):
- `McpServerConfig.fields` does not exist; the cited line 77 is the end of the `_MCP_SERVER_KEYS` tuple. The comment in `scripts/agent/services/config_outcome_classification.py` refers to `dataclasses.fields` rendering exclusion, not an attribute.
- The health timeout helper `get_effective_health_timeout` is used by 7 production call sites (`scripts/agent/http_lifecycle.py`, `scripts/agent/http_lifecycle_health_checker.py`, `scripts/agent/startup_mcp_starter.py`, `scripts/agent/services/mcp_health.py`, `scripts/agent/services/mcp_status.py`, `scripts/agent/services/mcp_tool_discovery_fetch.py`).
- No unused lifecycle constructor arguments: every argument of `ProcessTerminator.__init__` and `SubprocessLauncher.__init__` is stored and used.
- No duplicate classification implementations: `classify_stale_pending` in `scripts/agent/workflow/state_store.py` is a documented pass-through facade to `scripts/agent/workflow/tool_call_state_ops.py`; `_detect_diagnostics_live_fields` in `scripts/agent/services/config_reload.py` delegates to the module function. The duplicate helper was already removed by the cliplc005 plan's dead-code phase.
- `scripts/shared/runtime_tool_registry.py`: every vulture-flagged method has production callers; `posture_excluded_servers` has zero production callers but is test-facing (`tests/agent/services/test_mcp_tool_discovery_posture_gate.py`).
- Every public configuration field named in the Issue has a runtime consumer (`role` display, `call_timeout_sec` invoker, `startup_timeout_sec` health checker, `startup_stagger_delay_sec` starter, `required` discovery/validation, `health_timeout` helper), except the stderr rotation pair, whose enforcement is the open plan's scope.

Confirmed claims:
- The stderr rotation settings (`max_stderr_log_size_mb`, `max_stderr_log_files`) are validated at parse time but never read in production; `StderrLogManager` is constructed without them and `rotate_log` has no production caller.
- `scripts/agent/http_lifecycle.py` docstring states the stderr log path as `/opt/llm/logs/mcp_servers/{server_key}.stderr.log`; the actual path is `tempfile.gettempdir()/mcp_server_logs/{server_key}/stderr.log` (`scripts/agent/http_lifecycle_stderr_log_manager.py`).
- Four public properties in `scripts/shared/mcp_config.py` have zero callers in `scripts/` and `tests/`.

## Reason for Change
Cleanup only; it follows stabilization of the configuration and lifecycle contracts. Not time-sensitive.

## Implementation Intent
Every public field and parameter has one documented effect; confirmed-unused surface is removed; signatures and docstrings match the final runtime model. Remove only what is confirmed unused; stop and report any field that still has an external consumer.

## Requirements
- `REQ-001`: Remove the four unused public properties of `scripts/shared/mcp_config.py` (`StartupMode.is_persistent`, `StartupMode.requires_subprocess`, `McpServerConfig.needs_health_check`, `McpServerConfig.requires_cmd`).
- `REQ-002`: Correct the stale docstring in `scripts/agent/http_lifecycle.py` so the documented stderr log location matches the actual location, and align field descriptions in `scripts/shared/mcp_config.py`.
- `REQ-003`: Keep `max_stderr_log_size_mb` and `max_stderr_log_files` in `scripts/shared/mcp_config.py`; the decision is resolved to keep because the frozen stderr plan's REQ-006 gives each field documented runtime effect (configured size and generation limits). Confirm at implementation time that the enforcement landed before AC-3 is evaluated.
- `REQ-004`: N/A: resolved this cycle — no concrete storage or display constant exists in `scripts/agent/session_persister.py` (module-level names: `logger` only; every symbol has production callers). No modification target.

## Implementation Target Files
**Freeze status**: Frozen (Step 8 validation passed on the re-entry — all rows `Verified`, no blocking Unknown remains; see this Plan's Step 8 report in the workflow run).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/shared/mcp_config.py` | Modify | Remove four unused public properties; keep the stderr rotation pair (decision resolved: the frozen stderr plan's REQ-006 gives each field documented runtime effect) | REQ-001; REQ-003 | Zero callers for the four properties in `scripts/` and `tests/` (checked in Step 2/3, re-confirmed by `tools/scan_change_consumers.py` this cycle); rotation fields read only by tests until the open plan's enforcement lands (checked in Step 2) | `tests/shared/test_mcp_config_validation.py` | Verified |
| `scripts/agent/http_lifecycle.py` | Modify | Correct stale docstring: documented stderr log path does not match the actual location | REQ-002; AC-2 | Docstring vs `scripts/agent/http_lifecycle_stderr_log_manager.py` log path (checked in Step 2) | `tests/agent/test_http_lifecycle.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/http_lifecycle_stderr_log_manager.py` | Actual stderr log location and rotation behavior; modification target of the open stderr plan, must not be modified here | REQ-002; REQ-003 |
| `scripts/agent/services/config_outcome_classification.py` | Confirms the `McpServerConfig.fields` claim is disconfirmed and no duplicate helper remains | REQ-001 |
| `scripts/agent/workflow/state_store.py` | Documents the pass-through facade; disconfirms the duplicate-helper claim | Out-of-Scope |
| `scripts/agent/workflow/tool_call_state_ops.py` | The implementation behind the `classify_stale_pending` facade | Out-of-Scope |
| `scripts/agent/services/config_reload.py` | The pass-through wrapper `_detect_diagnostics_live_fields`; disconfirms the duplicate-helper claim | Out-of-Scope |
| `scripts/shared/runtime_tool_registry.py` | Confirms every flagged method has production callers; no modification target | Out-of-Scope |
| `scripts/agent/session_persister.py` | Confirms REQ-004 is N/A: no module-level constant besides `logger`; every symbol has production callers (full read + `tools/scan_change_consumers.py` this cycle) | REQ-004 (N/A) |
| `tests/agent/services/test_mcp_tool_discovery_posture_gate.py` | Shows `posture_excluded_servers` is test-facing, not dead surface | Out-of-Scope |

## Acceptance Criteria
- AC-1 (REQ-001): `uv run vulture scripts/shared/mcp_config.py --min-confidence 60` reports no unused public property in the file after removal.
- AC-2 (REQ-002): the `scripts/agent/http_lifecycle.py` docstring states the actual stderr log location; docstrings and field descriptions match runtime behavior.
- AC-3 (REQ-003): every retained public configuration field changes documented runtime behavior — the decision is `keep`; evaluated when the open stderr plan's enforcement lands.
- AC-4 (REQ-004): N/A: resolved — no concrete storage/display constant exists in `scripts/agent/session_persister.py`; no modification, no acceptance criterion.

## Tests
- REQ-001: no test changes expected — no test references the removed properties (verified by search this cycle); the full suite must still pass.
- REQ-002: docstring check per `rules/tool-gates.md` documentation gate.
- REQ-003: no test changes; AC-3 is evaluated after the open plan's enforcement lands.
- REQ-004: N/A: resolved — no modification; `tests/agent/test_session_persister.py` must still pass unchanged.
- Whole Issue Testing Expectations: vulture, ruff, mypy, and the full test suite.

## Documentation Impact
Yes. Corrected docstrings and field descriptions (REQ-002, REQ-003). Target doc via `docs/00_index.md` "Document References by Task": MCP server spec (field descriptions). The stderr log location doc is already a modification target of the open stderr plan; this Plan does not add a `docs/` row.

## Assumptions
- The cliplc005–cliplc008 plans are closed for implementation purposes: every implementation row is `Completed`; only deploy hand-offs remain, which are the user's decision.
- `McpServerConfig.tool_names` is already removed (agentcfg002); this Plan must not reintroduce it.
- Documented pass-through facades are intentional design, not duplicates to consolidate.
- `scripts/` files are rsynced by deploy.sh; no `cp` line change.
- Step 3a findings (2026-11-26, adversarial verification): all Problem and Requirements claims reconfirmed against
  current source — the four properties are defined at `scripts/shared/mcp_config.py:99,109,150,166` with no call
  site in `scripts/` or `tests/`; the rotation fields are validated at `:275-282` and `rotate_log` has no
  production caller; the docstring path at `scripts/agent/http_lifecycle.py:71-72` does not match the actual path
  built at `scripts/agent/http_lifecycle_stderr_log_manager.py:67`; `scripts/agent/session_persister.py` has no
  module-level constant besides `logger` (`:47`). REQ-002's clause "align field descriptions in
  `scripts/shared/mcp_config.py`" resolves to no change: the field comments at `:140-141` already match runtime
  behavior, so the actionable part of REQ-002 is the docstring in `scripts/agent/http_lifecycle.py`. No stale
  claim found in this Plan.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Which of the Issue's listed unused items still exist after the earlier issues land (the Issue's own Unresolved Question). Resolved for `fields`, the health helper, constructor arguments, and duplicate helpers; resolved this cycle for the session_persister constants: none exist, so REQ-004 is N/A. | None remaining — resolved by a full read of `scripts/agent/session_persister.py` plus `tools/scan_change_consumers.py` (no module-level constant besides `logger`; no direct consumers of the four properties) | Resolved this cycle | False |
| UNK-02 | The stderr rotation field decision (`max_stderr_log_size_mb`, `max_stderr_log_files`). Resolved this cycle to **keep**: the frozen stderr plan's REQ-006 defines the documented runtime effect for both fields (configured size and generation limits with purge). Only the post-landing confirmation of AC-3 remains, which is execution sequencing, not an open question. | None remaining for the decision itself — resolved from the frozen plan's REQ-006; the enforcement landing is tracked in Execution Status, not as an Unknown | Enforcement lands with the open plan's Phase 3; confirm AC-3 then | False |
| UNK-03 | Whether the documented pass-through facades count as "duplicate helpers" to consolidate. Resolved this cycle on repository evidence: they are documented as intentional pass-throughs, so no consolidation; recorded as Out-of-Scope. If the owner later decides to consolidate, that is a new issue, not this Plan. | None remaining for this Plan — evidence-based decision; an owner override would open a new issue | Resolved this cycle (evidence-based); owner may override | False |

## Affected areas
Per `rules/skill-runtime.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` (Path B, from the historical analysis; `git-fame` not installed, bus factor from author counts).

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/shared/mcp_config.py` | Modify | Medium (12 importing modules) | 11 | High (single author) | not applicable (rsynced) |
| `scripts/agent/http_lifecycle.py` | Modify | Medium (lifecycle callers and tests) | 6 | High (single author) | not applicable (rsynced) |

## Design
Path B analysis (this cycle):
- Architecture: `import-linter` reports 6 contracts kept, 0 broken; `shared/mcp_config.py` sits below `agent/` so tool_executor can reference it without depending on agent/ (module docstring). Removing properties does not cross the "No agent module imports MCP server config models" contract boundary because no consumer imports the removed properties.
- Dependency graph: `scripts/shared/mcp_config.py` has 12 importers in `scripts/`; none reference the four removed properties. `scripts/agent/http_lifecycle_stderr_log_manager.py` is imported only by `scripts/agent/http_lifecycle.py` and tests — its modification belongs to the open plan.
- Historical: churn and bus factor recorded in Affected areas; high-churn `scripts/shared/mcp_config.py` is the riskiest row.
- Operational: no port, DB, or persisted-schema change; lock check not applicable. `pip-audit` not run (no dependency upgrade).
- Design decision: keep the stderr rotation fields pending the open plan; do not wire them here — enforcement is that plan's REQ-006, and wiring it in this Plan would duplicate it.

## Implementation steps
1. **Phase 1: Remove confirmed unused public properties**
   - [ ] Remove `StartupMode.is_persistent`, `StartupMode.requires_subprocess`, `McpServerConfig.needs_health_check`, `McpServerConfig.requires_cmd` from `scripts/shared/mcp_config.py` (REQ-001); run vulture to confirm no remaining unused public property (AC-1).
2. **Phase 2: Correct stale docstrings**
   - [ ] Fix the stderr log location docstring in `scripts/agent/http_lifecycle.py` to state the actual location (REQ-002; AC-2).
3. **Phase 3: Keep the stderr rotation fields (decision resolved)**
   - [ ] Keep `max_stderr_log_size_mb` / `max_stderr_log_files` in `scripts/shared/mcp_config.py` (REQ-003; AC-3). No code change in this Plan; confirm AC-3 after the open stderr plan's enforcement lands.
4. **Phase 4: Validation and deployment hand-off**
   - [ ] Run the full validation sequence (`rules/toolchain.md`): format, lint, type, arch, security, test, coverage (REQ-001, REQ-002).
   - [ ] Deploy hand-off to `skills/deploy/SKILL.md`: the change must be committed and pushed first; deploying is the user's decision (approval gate).

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/mcp_config.py` | Static analysis + full suite | `uv run vulture scripts/shared/mcp_config.py --min-confidence 60`; `uv run pytest tests/shared/test_mcp_config_validation.py` | No unused public property; tests pass unchanged |
| `scripts/agent/http_lifecycle.py` | Docstring check + targeted tests | `uv run pytest tests/agent/test_http_lifecycle.py`; `rules/tool-gates.md` doc gate | Docstring matches actual log path |
| Whole suite | Regression | `uv run pytest` | No failures |

## Risks
- **Risk**: Removing a public property that a dynamic-dispatch or external consumer uses → **Mitigation**: zero callers confirmed by search across `scripts/` and `tests/`; stop and report if any consumer appears (the Issue's AI Implementation Instruction).
- **Risk**: Scope overlap with the open stderr plan on stderr log management → **Mitigation**: that file is excluded from this Plan's targets; recorded as a sequencing dependency.
- **Risk**: `scripts/agent/http_lifecycle.py` is targeted by two Frozen Plans at once (`check_plan_target_overlaps.py`) → **Mitigation**: verified this cycle — the designs do not contradict each other. The open plan changes the snapshot builder to emit a logical identifier; this Plan only corrects the module docstring's stderr log location, and both state the same actual location (`tempfile.gettempdir()/mcp_server_logs/{server_key}/stderr.log`).
- **Risk**: High bus factor (single author) on all target files → **Mitigation**: each phase is independently revertable; targeted tests before removal.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Remove confirmed unused public properties (`scripts/shared/mcp_config.py`) | In Progress | — | — |  |
| 2 | Phase 2: Correct stale docstrings (`scripts/agent/http_lifecycle.py`) | In Progress | — | — |  |
| 3 | Phase 3: Keep the stderr rotation fields, confirm AC-3 after the open plan lands (`scripts/shared/mcp_config.py`) | In Progress | — | — | Decision resolved to keep; confirmation waits for the open plan's enforcement |
| 4 | Phase 4: Validation and deployment hand-off | In Progress | — | — | Deploy is the user's decision |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 3 | Open stderr plan (UNK-02): the field decision was blocking; resolved this cycle to keep per the frozen plan's REQ-006. Only the post-landing AC-3 confirmation remains (sequencing, not a blocker) | Yes | 20261126 |
| 4 | No concrete storage/display constant confirmed in `scripts/agent/session_persister.py` (UNK-01): resolved this cycle — none exist; REQ-004 is N/A and the row was removed from the targets | Yes | 20261126 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261126-235847_01_scripts_shared_mcp_config.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261126-235847_02_scripts_agent_http_lifecycle.py.md` | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261119-145311_cliplc013_api-field-cleanup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261126-221206
- **Evidence revision**: ade9a2c378a43c9210f9ff2de9373440ad685345
- **Related target files**: `scripts/shared/mcp_config.py`, `scripts/agent/http_lifecycle.py`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes; zero-caller search this cycle | `scripts/shared/mcp_config.py` | Phase 1 | AC-1 | `tests/shared/test_mcp_config_validation.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes; docstring vs actual log path this cycle | `scripts/agent/http_lifecycle.py` | Phase 2 | AC-2 | `tests/agent/test_http_lifecycle.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes; fields exist but unenforced; decision resolved to keep via the frozen plan's REQ-006 | `scripts/shared/mcp_config.py` | Phase 3 | AC-3 | `tests/shared/test_mcp_config_validation.py` (unchanged) | Confirmed by repository evidence |
| REQ-004 | Required Changes; resolved this cycle — no concrete constant found in `scripts/agent/session_persister.py` (full read + `tools/scan_change_consumers.py`) | N/A: no target file (moved to Reference Files) | N/A: REQ resolved to N/A | AC-4 (N/A) | `tests/agent/test_session_persister.py` (unchanged) | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261126-235847 -->