## Goal

Stop the Agent from importing the dispatcher's dedup config for `retry_class` and obtain the retry classification from the Agent's own stored state instead (`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit (config isolation is independent of the empty-store fail-closed unit per the Plan).

## Assumptions
- `tool_runner.py` imports `retry_class` from the dispatcher (`from shared.mcp_dedup import retry_class`, `tool_runner.py` L24) and CONSUMES it: `_record_pending_state` calls `recorder.record_tool_call(task_id, key, pc.name, retry_class(pc.name))` (`tool_runner.py` L177) with **no** `config` arg, so `retry_class()` falls through to `load_dedup_config()` → reads the dispatcher's `config/mcp_dedup.toml`. UNK-03 is therefore RESOLVED: the Agent does read the dispatcher config transitively, and the refactor is required.
- `record_tool_call` writes the classification into `workflow.sqlite` (`tool_call_state.retry_class`, `tool_call_state_ops.py` L49-70, L31 column), where `build_turn_control_message` later reads it (`workflow_engine.py` L176-177).
- Moving the classification MUST NOT default any tool to a weaker class: unknown tools stay `non_retryable` (`mcp_dedup.py` L166-170).
- Open (flag, do not fabricate): the exact Agent-side SOURCE of the classification (UNK-03 resolution).

## Design decisions
- **RESOLVED (UNK-03, maintainer-approved 2026-11-11): canonical set in `tool_constants.py`.** A new `RETRYABLE_TOOLS: frozenset[str]` is added to `scripts/shared/tool_constants.py` as the single source of truth for the retry classification, populated verbatim from the dispatcher's current `[retry_class]` map in `config/mcp_dedup.toml` (verified 2026-11-11: `write_file/edit_file/create_directory/move_file`, `delete_file/delete_directory`, `git_add/.../git_push`, `github_*` (8), `index_paths/refresh_index`, `rag_delete_document`). `tool_runner.py` resolves the classification from `RETRYABLE_TOOLS` (`retryable` if the name is in the set, else `non_retryable`) and stops importing `shared.mcp_dedup` (REQ-004).
- **Dispatcher ownership (do not fabricate a further resolution here).** The dispatcher continues to own its classification via `config/mcp_dedup.toml` `[retry_class]` (ADR-008 / seq 06 keeps that map). `RETRYABLE_TOOLS` and the `[retry_class]` map are therefore two *mirrored* definitions that must stay consistent; true single-source (dispatcher reading `tool_constants.py`) is a separate follow-on, deferred to avoid conflicting with seq 06's explicit "keep the `[retry_class]` map" design. The two currently match exactly, so there is no drift today.

## Alternatives considered
- **Keep the import.** Rejected: it makes the Agent process read the dispatcher's `mcp_dedup.toml`, violating REQ-004 (ADR-002 config isolation).

## Implementation
### Target file
`scripts/agent/tool_runner.py`

### Procedure
1. Remove `from shared.mcp_dedup import retry_class` (`tool_runner.py` L24).
2. Replace `retry_class(pc.name)` in `_record_pending_state` (`tool_runner.py` L177) with an Agent-local classifier that returns `retryable`/`non_retryable` WITHOUT importing `shared.mcp_dedup`. Preserve the unknown-tool default of `non_retryable`.
3. Keep the surrounding fail-open guard (`tool_runner.py` L178-180): a recording failure is logged, never fatal.

### Method
- Add a module-local function such as `agent_retry_class(tool_name) -> str` (new) implementing the Agent-side rule (Design, option 1), or read from an Agent-owned config if the maintainer prefers option 2. Do not reference `shared.mcp_dedup` anywhere in this file.

### Details
- `tool_runner.py` still imports only Agent/shared-non-dedup symbols. Verify no other `mcp_dedup` symbol creeps in.
- The stored value flows to `classify_stale_pending` → `build_turn_control_message` unchanged (seq 03).

## Compatibility considerations
- Behaviour is identical if the local classifier reproduces the dispatcher's current classifications; add a test asserting unknown tools stay `non_retryable`.
- If option 2 (second config copy) is chosen, document the drift risk; prefer option 1.

## Security considerations
- Removing the cross-process config read tightens the dispatcher/agent boundary (ADR-008). No new secret exposure.

## Rollback considerations
Revert the commit. No schema or state changes.

## Validation plan
- `uv run pytest tests/agent/test_tool_runner.py -v`:
  - `retry_class` is resolved from the Agent's own state/classifier, not the dispatcher config.
  - Unknown tool stays `non_retryable`.
- Grep confirms `tool_runner.py` no longer imports `shared.mcp_dedup`.
- Config-loader checker + full validation sequence (`rules/toolchain.md`).

## Completion criteria
- `tool_runner.py` does not import `shared.mcp_dedup`.
- `record_tool_call` receives an Agent-local classification; unknown tools default to `non_retryable`.
- No `mcp_dedup.toml` is read by the Agent process (REQ-004).

## Out of Scope
- The `workflow_engine.py` timeout read (seq 03).
- Reducing `mcp_dedup.toml` (seq 06) and documentation (seq 10-14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Stop importing dispatcher `retry_class`; source it Agent-locally | In progress | 20261111 | UNK-03 RESOLVED: canonical `RETRYABLE_TOOLS` in tool_constants.py (scope expansion approved). Dispatcher keeps owning its `[retry_class]` map (seq 06); the two mirror each other. |
| 2 | Update `tests/agent/test_tool_runner.py` | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | UNK-03 RESOLVED 2026-11-11 (maintainer-approved scope expansion): canonical `RETRYABLE_TOOLS` added to `scripts/shared/tool_constants.py`, populated verbatim from the dispatcher's `[retry_class]` map. `tool_runner.py` resolves from it and drops the `shared.mcp_dedup` import. Dispatcher keeps owning its map (ADR-008 / seq 06); the two mirror each other — true single-source for the dispatcher is a deferred follow-on. | yes | 20261111 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-004` — per-process config isolation; `retry_class` no longer imported from the dispatcher
- **Source issue**: `issues/20261109-112844_adrrev008_mcp-dedup-ownership.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261110-230633_adrrev008_mcp-dedup-ownership.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-111905
- **Related target files**: `scripts/agent/tool_runner.py`

### Companion test files
- `tests/agent/test_tool_runner.py`
  - Procedure: assert `retry_class` comes from the Agent's own state/classifier, not the dispatcher config; unknown tool stays `non_retryable`.
  - Validation: `uv run pytest tests/agent/test_tool_runner.py -v` passes; grep confirms no `shared.mcp_dedup` import.
