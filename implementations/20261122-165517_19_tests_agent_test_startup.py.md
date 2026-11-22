## Goal

Remove the config-field prompt fixtures from the startup tests (REQ-006, test migration).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Companion judgement: condition 2 is met (named by row 11 only), but condition 3 fails because the five fixture sites must be re-sourced through row 18's helper; it keeps its own document.
- Each assignment exists only so the startup path can read the prompt from the config layer; after row 11 the path reads the typed source, so the fixtures have no purpose.

## Design decisions
- N/A: fixture removal only; no test-design decision.

## Alternatives considered
- Keeping the assignments with an empty dict: rejected, the field no longer exists on the mock config object either.

## Implementation
### Target file
`tests/agent/test_startup.py`
### Procedure
Delete the five prompt fixture assignments.
### Method
- Remove `ctx.cfg.tool.system_prompts = {...}` at lines 50, 72, 90, 106, 127.
- Where a case asserts the initial prompt content, assert it through the typed-source fixture used by row 18's helper rather than through `ctx.cfg.tool`.
### Details
- No assertion is deleted; only the input source of the prompt changes.

## Compatibility considerations
- N/A: internal test change only.

## Security considerations
- N/A: no trust boundary is involved.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_startup.py`
- `uv run ruff check tests/agent/test_startup.py`

## Completion criteria
- No reference to `ctx.cfg.tool.system_prompts` remains, and the startup prompt assertions still pass through the typed source (AC-4).

## Out of Scope
- The shared helper change, covered by row 18.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
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
- **Related target files**: `tests/agent/test_startup.py`
