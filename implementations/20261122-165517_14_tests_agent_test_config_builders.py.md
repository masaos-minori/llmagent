## Goal

Remove the prompt-field assertions and the prompt argument from the section-builder tests (REQ-002, test migration).

## Scope
**Release unit**: RU-1

## Assumptions
- Companion judgement: condition 2 fails — named in the `Related Tests` cell of three rows (04, 05, 06) — so it keeps its own document.
- `_TOOL_DEFAULTS` in this file keeps every entry except the prompt ones; the loop that asserts defaults against `_TOOL_DEFAULTS` stays as the characterisation of the remaining fields.

## Design decisions
- N/A: assertions and one fixture argument are removed; no test-design decision beyond dropping the prompt cases.

## Alternatives considered
- Keeping the prompt assertions against an empty dict: rejected, the field no longer exists.

## Implementation
### Target file
`tests/agent/test_config_builders.py`
### Procedure
Drop the prompt cases and the prompt argument.
### Method
- Remove `cfg.system_prompts` and `cfg.system_prompt_tool` assertions (lines 144-152).
- Remove the `system_prompt_tool=` argument from the `_build_tool_config` calls (lines 168, 171, 174) and the prompt key from the overrides dict.
- Remove the pass-through case `test_system_prompt_tool_propagates` (lines 429-437).
### Details
- The remaining default-assertion loop is the test that proves no prompt field remains (AC-1).

## Compatibility considerations
- N/A: internal test change only.

## Security considerations
- N/A: no trust boundary is involved.

## Rollback considerations
- N/A: revert the commit as part of RU-1.

## Validation plan
- `uv run pytest tests/agent/test_config_builders.py`
- `uv run ruff check tests/agent/test_config_builders.py`

## Completion criteria
- No assertion or fixture in this file references a prompt field, and the remaining builder tests still pass.

## Out of Scope
- The new approval key added by `mcpdl003` to `config_builders.py`; its test changes belong to that plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | RU-1 |
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
- **Requirement ID**: `REQ-002` (remove prompt-field assertions from the section-builder tests)
- **Source issue**: `issues/20261120-114213_agentcfg005_system-prompt-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-162618_agentcfg005_system-prompt-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-165517
- **Related target files**: `tests/agent/test_config_builders.py`
