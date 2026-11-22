## Goal
Remove the explicit prompt-key exception so the removed keys are rejected as unknown keys by the same path that rejects any other unknown key (REQ-004, single-function row).

## Scope
**Release unit**: RU-1

## Assumptions
- `system_prompts` is already accepted only through the dataclass-derived keys, so row 04 removes it from the valid set; this row removes only the explicit exception for `system_prompt_tool` (line 172).
- Cross-plan overlap with `plans/20261121-172154_mcpdl003_dedup-config-isolation.md` on this row is judged compatible: that plan adds a new Agent key to this set, this row removes one.
- The startup and `/reload` paths share this validator, so one change covers both.
## Design decisions
- No special-cased handling remains: the removed keys are unknown keys like any other, per the Plan's Implementation Intent and the `Current-Specification-Only` policy.
## Alternatives considered
- Keeping the exception with a migration or alias message: rejected by the Plan's Out-of-Scope (no alias, no compatibility reader).

## Implementation
### Target file
`scripts/agent/production_config_validator.py`
### Procedure
Delete `valid_keys.add("system_prompt_tool")` (line 172) and the comment naming `build_agent_config()` direct keys if it becomes empty after the removal; no change to the error reporting or the other key sources.

## Compatibility considerations
- The real-file integration test passes because row 01 removes the key from `config/agent.toml`; its assertions are updated by row 17.
## Security considerations
- N/A: no trust boundary beyond the existing config validation contract.
## Rollback considerations
- N/A: revert the commit as part of RU-1.
## Validation plan
- `uv run pytest tests/agent/test_production_config_validator.py` (row 17), including the existing real-config integration case; `uv run ruff check .`, `uv run mypy scripts/`.
## Completion criteria
- Both prompt keys are reported as unknown keys at startup and at `/reload` with the same result (AC-2).
## Out of Scope
- The per-server `[dedup]` table coverage `mcpdl003` adds to this validator.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure | Pending | — | — | RU-1 |
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
- **Requirement ID**: `REQ-004` (removed keys reported as unknown keys at startup and at `/reload`)
- **Source issue**: `issues/20261120-114213_agentcfg005_system-prompt-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-162618_agentcfg005_system-prompt-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-165517
- **Related target files**: `scripts/agent/production_config_validator.py`
