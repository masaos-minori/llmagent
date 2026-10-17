## Goal

Delete the `TestSwitchSystemPrompt` class from
`tests/agent/services/test_conversation_service.py` (`REQ-004`, command-surface reduction).

## Scope

In scope: delete the `TestSwitchSystemPrompt` class from
`tests/agent/services/test_conversation_service.py`. Out of scope: removing
`switch_system_prompt()` itself (`scripts/agent/services/conversation_service.py`,
`REQ-004`, separate document), the `/system` handler (`cmd_context.py`, `REQ-002`), the
`CommandDef` entry (`command_defs_list.py`, `REQ-001`), and documentation (`REQ-007`).

## Assumptions

- The file holds only the `TestSwitchSystemPrompt` class (per the plan's row
  classification).
- No other file imports from `test_conversation_service.py`.

## Design decisions

- **Whole-file deletion when the file holds only the class.** If step 1 confirms the file
  contains only `TestSwitchSystemPrompt`, delete the file; otherwise delete only the class.
- **Verify before deleting the whole file.** Confirm no other classes exist before deleting
  the file rather than just the class.

## Alternatives considered

`N/A`: the goal mandates removal with no shim or forwarding path; keeping an empty test
file would contradict it.

## Implementation

### Target file

`tests/agent/services/test_conversation_service.py`

### Procedure

1. Confirm the file holds only the `TestSwitchSystemPrompt` class (L112) via Read.
2. Confirm nothing outside the file imports from `test_conversation_service`.
3a. If the file holds only that class, delete the file (`git rm` / equivalent).
3b. Otherwise, delete only the `TestSwitchSystemPrompt` class.

### Method

Delete the file (or the class block) from the working tree and stage the removal with git.

### Details

- This must land together with the `switch_system_prompt()` deletion (separate document) so
  no test references the removed function between the two changes.

## Compatibility considerations

Test-only change; production behavior is unaffected. `/system` now fails like an unknown
command.

## Security considerations

`N/A`: test deletion; no secret, permission, or data path is touched.

## Rollback considerations

`git restore --staged <file> && git checkout -- <file>` (or revert the commit) to recover
the file.

## Validation plan

- `pytest` full suite — no missing-import failures from other test files.
- `lint-imports` — no dangling caller.
- `ruff` / `mypy --no-namespace-packages tests/` — clean.

## Completion criteria

`TestSwitchSystemPrompt` is gone from `test_conversation_service.py`, the surviving
`clear_conversation`/config tests pass, and the full suite passes.

## Out of scope

`conversation_service.py` (`REQ-004`), `cmd_context.py` (`REQ-002`),
`command_defs_list.py` (`REQ-001`), documentation (`REQ-007`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete `TestSwitchSystemPrompt` from `tests/agent/services/test_conversation_service.py` (`REQ-004`) | Completed | 20261017-100006 | 20261017-100006 | Confirm the file holds only this class before deleting the file |
| 2 | Add or update tests per Validation plan | Completed | 20261017-100006 | 20261017-100006 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261017-100006 | 20261017-100006 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261017-100006 | 20261017-100006 |  |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: `issues/20261016-162117_cli001_remove-diff-system-audit-slash-commands.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261016-233542_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-071828
- **Related target files**: `tests/agent/services/test_conversation_service.py`