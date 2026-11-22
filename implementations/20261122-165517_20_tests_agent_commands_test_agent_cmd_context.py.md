## Goal
Remove the config-field prompt fixture from the context-command test (REQ-006, single-line test row).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Companion judgement: condition 2 fails — no other row's `Related Tests` cell names this file — so it keeps its own document.
- The command under test displays `ctx.conv.system_prompt_name` only (`scripts/agent/commands/cmd_context.py` line 75), so this fixture has no consumer and its removal changes nothing the test asserts.
## Design decisions
- N/A: one fixture line removed.
## Alternatives considered
- Keeping the fixture as harmless noise: rejected, it keeps a reference to a field that no longer exists.

## Implementation
### Target file
`tests/agent/commands/test_agent_cmd_context.py`
### Procedure
Delete `ctx.cfg.tool.system_prompts = {...}` at line 51; the `ctx.conv` fixtures at lines 40-41 stay because those are the runtime values the command reads.

## Compatibility considerations
- N/A: internal test change only.
## Security considerations
- N/A: no trust boundary is involved.
## Rollback considerations
- N/A: revert the commit.
## Validation plan
- `uv run pytest tests/agent/commands/test_agent_cmd_context.py`; `uv run ruff check tests/agent/commands/test_agent_cmd_context.py`.
## Completion criteria
- No reference to `ctx.cfg.tool.system_prompts` remains and the command output assertions still pass (AC-4).
## Out of Scope
- Prompt-name selection features (Plan UNK-04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure | Pending | — | — | |
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
- **Requirement ID**: `REQ-006` (startup prompt fixtures migrated to the typed source)
- **Source issue**: `issues/20261120-114213_agentcfg005_system-prompt-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-162618_agentcfg005_system-prompt-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-165517
- **Related target files**: `tests/agent/commands/test_agent_cmd_context.py`
