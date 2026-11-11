## Goal

Read `pending_timeout_minutes` from the Agent's own configuration instead of `load_dedup_config()` (`REQ-004`), so the Agent process no longer reads the dispatcher's `config/mcp_dedup.toml`.

## Scope
**Release unit**: N/A: not part of a release unit (config isolation is independent of the empty-store fail-closed unit per the Plan).

## Assumptions
- `pending_timeout_minutes` moves from `config/mcp_dedup.toml` to `config/agent.toml` (seq 05) as a top-level scalar consistent with the existing `agent_memory_max_startup_snippets` (`config_dataclasses.py` L392).
- `workflow_engine.py` currently imports `load_dedup_config` (`workflow_engine.py` L18) and reads `load_dedup_config().pending_timeout_minutes * 60` in `build_turn_control_message` (`workflow_engine.py` L167).
- The retry-class used for replay vs unreplayable classification in `build_turn_control_message` (`workflow_engine.py` L176-177) comes from the stored `ToolCallState.retry_class` (via `classify_stale_pending`, `tool_call_state_ops.py` L104-140), NOT from `load_dedup_config` — so only the timeout read needs to move.
- Open (flag, do not fabricate): how `WorkflowEngine` obtains the value. It has no `cfg` param (`WorkflowEngine.__init__`, `workflow_engine.py` L128-137 takes `workflow_def, store, tracer=None`).

## Design decisions
- **RESOLVED (UNK-03, maintainer-approved 2026-11-11): constructor param fed from `AgentConfig`.** Path 1 was chosen over the dedicated-reader path (path 2) because it integrates with the existing config pipeline (type-checked, validated) rather than introducing a second config reader. This requires touching three non-frozen files beyond the frozen table — approved as a scope expansion by the maintainer:
  1. `scripts/agent/config_dataclasses.py` — add `pending_timeout_minutes: int = 10` to `AgentConfig` (top-level scalar, next to `agent_memory_max_startup_snippets`, L392).
  2. `scripts/agent/production_config_validator.py` — register `"pending_timeout_minutes"` in `_get_valid_production_keys()` (`_check_unknown_production_keys`, L174-182); **required**, because `build_agent_config()` runs the validator unconditionally (`config_builders.py` L156) and would reject the key as unknown. No bypass exists.
  3. `scripts/agent/config_builders.py` — read the key via `_get_or_default(cfg, "pending_timeout_minutes", _get_int, 10)` in `_assemble_agent_config()` (L116-145).
  4. `scripts/agent/orchestrator.py` — pass `pending_timeout_minutes=self._ctx.cfg.pending_timeout_minutes` at the `WorkflowEngine(...)` construction site (L137-145).
- `WorkflowEngine.__init__` takes the value as a **defaulted** param (`pending_timeout_minutes: int = _DEFAULT_PENDING_TIMEOUT_MINUTES`) so the ~40 existing `WorkflowEngine(wdef, store)` call sites in `tests/agent/workflow/test_workflow_engine.py` stay green; only `orchestrator.py` supplies the real config value.

## Alternatives considered
- **Keep `load_dedup_config()` here.** Rejected: it reads the dispatcher's `mcp_dedup.toml`, violating REQ-004 config isolation (ADR-002).

## Implementation
### Target file
`scripts/agent/workflow/workflow_engine.py`

### Procedure
1. Remove `from shared.mcp_dedup import load_dedup_config` (`workflow_engine.py` L18) once the value is sourced elsewhere.
2. Replace the timeout read at `workflow_engine.py` L167 with the Agent-config-sourced value, using whichever wiring mechanism is chosen in Design (constructor param fed from `orchestrator.py`, or a dedicated `agent.toml` reader). Do NOT reintroduce any import of `shared.mcp_dedup`.
3. Leave `build_turn_control_message`'s retry-class split (`workflow_engine.py` L176-177, from stored `ToolCallState.retry_class`) untouched.

### Method
- If constructor param: store `self._pending_timeout_seconds = pending_timeout_minutes * 60` in `__init__`; use it at L167. Wire the value in `orchestrator.py` from `ctx.cfg.<source>` (seq 05 defines the source).
- If shared loader: call the dedicated reader at L167.

### Details
- Preserve the fail-open guard around the whole block (`workflow_engine.py` L169-175): on store/config error, proceed without a control message (the dispatcher dedup still guards execution).
- `DEFAULT_PENDING_TIMEOUT_MINUTES = 10` (`mcp_dedup.py` L35) is the current value; the new default (in `agent.toml` / `AgentConfig`) should match unless a maintainer re-decides.

## Compatibility considerations
- Behaviour is identical if the value equals the previous 10 minutes; only the config source changes.
- `orchestrator.py` construction site must pass the new arg if a constructor param is adopted.

## Security considerations
- Reading the value from the Agent's own config removes a cross-process coupling; no new secret exposure.

## Rollback considerations
Revert the commit. If a constructor param was added, revert the `orchestrator.py` call site too.

## Validation plan
- `uv run pytest tests/agent/test_tool_runner.py -v` and the workflow/engine suites.
- Confirm `workflow_engine.py` no longer imports `shared.mcp_dedup` and that `build_turn_control_message` reads the Agent-config value.
- Config-loader checker + full validation sequence (`rules/toolchain.md`).

## Completion criteria
- `workflow_engine.py` does not import `shared.mcp_dedup`.
- `build_turn_control_message` reads `pending_timeout_minutes` from the Agent's own config.
- No `mcp_dedup.toml` is read by the Agent process (REQ-004).

## Out of Scope
- The `tool_runner.py` `retry_class` refactor (seq 04).
- Adding `pending_timeout_minutes` to `agent.toml` / `AgentConfig` (seq 05) — referenced as the source.
- Config reduction in `mcp_dedup.toml` (seq 06) and documentation (seq 10-14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read `pending_timeout_minutes` from Agent config instead of `load_dedup_config()` | In progress | 20261111 | UNK-03 RESOLVED: constructor param + AgentConfig (scope expansion approved). Additional targets: config_dataclasses.py, production_config_validator.py, config_builders.py, orchestrator.py |
| 2 | Update `tests/agent/test_tool_runner.py` / workflow suites | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | UNK-03 RESOLVED 2026-11-11 (maintainer-approved scope expansion): constructor param fed from `AgentConfig`. Chosen over dedicated-reader path for pipeline integration. Requires registering `pending_timeout_minutes` in `production_config_validator.py` (unavoidable — `build_agent_config()` validates every top-level key) plus `AgentConfig` field, `config_builders.py` read, and `orchestrator.py` wiring. | yes | 20261111 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-004` — per-process config isolation; Agent reads its own `pending_timeout_minutes`
- **Source issue**: `issues/20261109-112844_adrrev008_mcp-dedup-ownership.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261110-230633_adrrev008_mcp-dedup-ownership.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-111905
- **Related target files**: `scripts/agent/workflow/workflow_engine.py`
