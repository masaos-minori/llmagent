## Goal
Remove the `ctx.cfg.tool.system_prompts` fixture from the reload-classification test (REQ-003, test migration).

## Scope
**Release unit**: RU-1

## Assumptions
- Companion judgement: condition 2 fails — no other row's `Related Tests` cell names this file — so it keeps its own document.
- The classification test asserts startup-only classification driven by the registry `hot_reloadable` flags; with no prompt entry (row 07) there is no prompt case left here.
## Design decisions
- N/A: one fixture reference is removed; no test-design decision.
## Alternatives considered
- Keeping the fixture with an empty dict: rejected, the config field no longer exists.

## Implementation
### Target file
`tests/agent/services/test_config_reload_classification.py`
### Procedure
Delete the `ctx.cfg.tool.system_prompts` assignment at line 22; no assertion is replaced, because none references the prompt field.

## Compatibility considerations
- `scripts/agent/services/config_outcome_classification.py` holds no prompt reference, so the classification behaviour asserted here is unchanged; the expected field set is covered by row 15.
## Security considerations
- N/A: no trust boundary is involved.
## Rollback considerations
- N/A: revert the commit as part of RU-1.
## Validation plan
- `uv run pytest tests/agent/services/test_config_reload_classification.py`; `uv run ruff check tests/agent/services/test_config_reload_classification.py`.
## Completion criteria
- The file contains no prompt-field reference and the classification assertions still pass (AC-2).
## Out of Scope
- The expected tool-section field set, covered by row 15.

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
- **Requirement ID**: `REQ-003` (remove the prompt fixture from the reload-classification test)
- **Source issue**: `issues/20261120-114213_agentcfg005_system-prompt-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-162618_agentcfg005_system-prompt-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-165517
- **Related target files**: `tests/agent/services/test_config_reload_classification.py`
