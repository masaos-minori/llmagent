## Goal
Remove the unused config-field prompt fixture parameter and its default from the conversation-service test helper (REQ-006, single-function test row).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Companion judgement: condition 2 fails — no other row's `Related Tests` cell names this file — so it keeps its own document.
- `scripts/agent/services/conversation_service.py` reads no prompt config field (`rg` — no match); the helper's prompt fixture has no consumer, and no call site passes the parameter, so removal changes nothing observable.
## Design decisions
- N/A: dead fixture removal.
## Alternatives considered
- Keeping the parameter with an empty dict: rejected, the field no longer exists.

## Implementation
### Target file
`tests/agent/services/test_conversation_service.py`
### Procedure
Delete the `system_prompts: dict | None = None` parameter (line 16) and the `ctx.cfg.tool.system_prompts = ...` assignment (lines 26-29); keep `ctx.conv.system_prompt_name` and `ctx.conv.system_prompt_content`, which the service and the assertions use.

## Compatibility considerations
- N/A: internal test change only.
## Security considerations
- N/A: no trust boundary is involved.
## Rollback considerations
- N/A: revert the commit.
## Validation plan
- `uv run pytest tests/agent/services/test_conversation_service.py`; `uv run ruff check tests/agent/services/test_conversation_service.py`.
## Completion criteria
- No reference to a config-layer prompt field remains in this file and the service assertions still pass (AC-4).
## Out of Scope
- Any change to `scripts/agent/services/conversation_service.py` (not a target row, confirmed not affected).

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
- **Related target files**: `tests/agent/services/test_conversation_service.py`
