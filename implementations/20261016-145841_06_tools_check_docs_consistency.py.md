## Goal
- Remove `/memory` from `_CONTRACT_EXEMPT_COMMANDS` so `GV-023` checks `/memory` like every other command.

## Scope
- The `_CONTRACT_EXEMPT_COMMANDS` constant and its comment in `tools/check_docs_consistency.py`.

## Assumptions
- The table becomes empty; the machinery for exempting a command stays, because the tests add temporary entries (`test_check_command_contracts.py` monkeypatches it).
- The exemption is removed only after the registry, handlers, and chapter agree (the other rows); before then the check reports errors.

## Design decisions
- Make the constant an empty `dict[str, str]` and reword the comment to say a command may be listed only while a Known Issue tracks its drift, and that the table is currently empty.

## Alternatives considered
Deleting the constant and the skip logic: rejected, because the tests and future drift handling still use the mechanism.

## Implementation
### Target file
`tools/check_docs_consistency.py`

### Procedure
- Replace `_CONTRACT_EXEMPT_COMMANDS: dict[str, str] = {"/memory": "AGENT-013"}` with an empty dict of the same type and adjust the comment above it.
- Leave `check_command_contracts` and its docstring mention of the table as they are.

### Method
- One-line change plus the comment; keep type annotations (`mypy` must stay clean).

### Details
- Run `uv run python tools/check_docs_consistency.py --domain agent` after the registry and docs rows are applied; it must report no `/memory` finding.
- This is a docs gate: run the checker for the touched tool (`tools/TOOL_DESCRIPTIONS.md` needs no row change because no tool is added or removed).

## Compatibility considerations
- The `GV-023` gate becomes stricter for `/memory`; no other command is affected.

## Security considerations
N/A: documentation tooling.

## Rollback considerations
N/A: revert the commit (restores the exemption).

## Validation plan
- `uv run pytest tests/tools/test_check_command_contracts.py tests/tools/test_check_docs_consistency_checks.py tests/tools/test_check_agent_docs_consistency.py -q`
- `uv run ruff check tools/check_docs_consistency.py`, `uv run mypy tools/check_docs_consistency.py`, `uv run python tools/check_tool_descriptions_sync.py`
- `uv run python tools/check_docs_consistency.py --domain agent`

## Completion criteria
- The exemption table is empty and the agent-domain check reports no `/memory` finding.
- The tool tests pass; lint and type checks report no new findings.

## Out of scope
- Other commands' contracts, the check logic, and the registry.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Empty the exemption table and update its comment | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-006 (remove the /memory exemption)
- **Source issue**: issues/20261014-155503_mem001_implement-memory-command-spec.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261016-143248_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-145841
- **Related target files**: tools/check_docs_consistency.py
