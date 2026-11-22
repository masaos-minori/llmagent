## Goal

Remove the prompt parameter and its pass-through from the agent config builders (REQ-002, builder plumbing).

## Scope
**Release unit**: RU-1

## Assumptions
- Cross-plan overlap with `plans/20261121-172154_mcpdl003_dedup-config-isolation.md` on this row is judged compatible, not a conflict: that plan adds a read for a new approval key here, this row deletes the prompt read; different lines, no contradiction.
- `build_agent_config()` keeps its public signature and the override-vs-file resolution behaviour; only the prompt read and the pass-through disappear.

## Design decisions
- N/A: parameter deletion inside two private functions; no public contract change beyond removing one internal argument.

## Alternatives considered
- Passing an empty string through the builders to keep the shape: rejected, it keeps a prompt value travelling through the config layer for no consumer.

## Implementation
### Target file
`scripts/agent/config_builders.py`
### Procedure
Delete the prompt read and the parameter that carries it.
### Method
- Remove `system_prompt_tool = cfg.get("system_prompt_tool", "")` (line 160).
- Remove the `system_prompt_tool` parameter of `_assemble_agent_config` (line 119) and the argument passed to `_build_tool_config` (line 126); update the call at line 162.
- No change to `_resolve_config_source_and_registry` or `_run_production_validation`.
### Details
- After this change no builder path can produce prompt content, which is what AC-1 requires.
- `tests/agent/test_config_builders.py` line 429-437 is the pass-through case removed by row 14.

## Compatibility considerations
- The real-file integration test that calls `build_agent_config` through `ConfigLoader` must still pass after row 01 deletes the key; the pass-through test itself is removed in row 14.

## Security considerations
- N/A: no trust boundary is involved.

## Rollback considerations
- N/A: revert the commit as part of RU-1.

## Validation plan
- `uv run pytest tests/agent/test_config_builders.py` (row 14), plus `uv run pytest tests/agent/test_config_effective_snapshot.py -m integration` (row 13).
- `uv run ruff check .`, `uv run mypy scripts/`.

## Completion criteria
- No builder function accepts or returns prompt content, and the remaining builder behaviour is unchanged (AC-1).

## Out of Scope
- The new approval key that `mcpdl003` adds to this file; that row belongs to the other plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | RU-1, paired with row 05 |
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
- **Requirement ID**: `REQ-002` (remove the builder parameter and its pass-through)
- **Source issue**: `issues/20261120-114213_agentcfg005_system-prompt-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-162618_agentcfg005_system-prompt-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-165517
- **Related target files**: `scripts/agent/config_builders.py`
