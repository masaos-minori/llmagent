## Goal
- Add an explicit test that the exemption table does not contain `/memory`; the existing live-docs test then covers `/memory`.

## Scope
- `tests/tools/test_check_command_contracts.py` only: one added test.

## Assumptions
- `test_live_agent_docs_match_the_registry` compares the real registry with the real chapters; once `/memory` is not exempt it covers `/memory` automatically.
- The module is imported as `mod` and `_CONTRACT_EXEMPT_COMMANDS` is read through it; the test must not rely on the monkeypatched copy used by the temporary-docs helper.

## Design decisions
- A short test reads `mod._CONTRACT_EXEMPT_COMMANDS` directly and asserts `/memory` is absent.

## Alternatives considered
N/A: relying only on the live test was rejected because it would still pass if `/memory` were re-exempted together with a drifting chapter.

## Implementation
### Target file
`tests/tools/test_check_command_contracts.py`

### Procedure
- Add `test_memory_command_is_not_exempt` (new) after `test_live_agent_docs_match_the_registry`: assert `"/memory" not in mod._CONTRACT_EXEMPT_COMMANDS`.

### Method
- No fixtures; the test reads the module constant (the helper's `monkeypatch.setitem` is undone at teardown).

### Details
- Run it before the tool row's change to confirm it fails, then after to confirm it passes.

## Compatibility considerations
N/A: one added test.

## Security considerations
N/A: test only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_check_command_contracts.py -v`
- `uv run ruff check tests/tools/test_check_command_contracts.py`, `uv run mypy tests/tools/test_check_command_contracts.py`

## Completion criteria
- The new test fails with the exemption present and passes after the tool row's change; the live-docs test passes against the real registry and chapter.

## Out of scope
- The tool source, the registry, and the chapter.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the exemption guard test | Completed | 20261016-223121 | 20261016-223121 | Added test_memory_command_is_not_exempt asserting /memory absent from the exemption table |
| 2 | Run the validation sequence (`rules/toolchain.md`) after the tool change | Completed | 20261016-223121 | 20261016-223121 | Proved sensitivity via temporary reintroduce (fails), restored {}; ruff/mypy clean; 41 tool tests pass; consistency check clean |

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
- **Requirement ID**: REQ-006 (guard the removal)
- **Source issue**: issues/20261014-155503_mem001_implement-memory-command-spec.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261016-143248_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-145841
- **Related target files**: tests/tools/test_check_command_contracts.py