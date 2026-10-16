## Goal

Add rejection tests for the four removed command names (`/diff`, `/system`, `/audit`,
`/workflow`) to `tests/agent/commands/test_agent_cmd_context.py` and drop the tests of the
deleted `_cmd_diff`/`_cmd_system` behavior (`REQ-002`, `REQ-006`, command-surface
reduction).

## Scope

In scope: delete tests of the removed `_cmd_diff`/`_cmd_system` handlers from
`tests/agent/commands/test_agent_cmd_context.py` and add one rejection test per removed
name. Out of scope: the handler deletion (`cmd_context.py`, `REQ-002`), the `CommandDef`
entries (`command_defs_list.py`, `REQ-001`), the `/audit` mixin module
(`cmd_audit.py` + `registry.py`, `REQ-003`), and documentation (`REQ-007`).

## Assumptions

- The removed commands are rejected by the shared unknown-command path, so a single
  parametrized test can cover all four names.
- Existing context-mixin handler tests provide the fixture/setup pattern to mirror.

## Design decisions

- **One parametrized rejection test.** A single test iterating over the four names asserts
  the unknown-command result, no state mutation, and absence from `/help` — rather than
  four near-duplicate tests.
- **Drop, don't stub.** Remove the deleted-handler tests entirely; do not leave them
  failing or converted to skip markers.

## Alternatives considered

`N/A`: the goal mandates removal with no shim or forwarding path; leaving stubbed tests
would contradict it.

## Implementation

### Target file

`tests/agent/commands/test_agent_cmd_context.py`

### Procedure

1. Locate the tests of `_cmd_diff`/`_cmd_system` behavior and remove them.
2. Add one parametrized rejection test per removed name (`/diff`, `/system`, `/audit`,
   `/workflow`): assert the unknown-command result, that no session/workflow/audit/prompt/
   file/config state is mutated, and that the name is absent from `/help`.
3. For `/workflow` (which had no `CommandDef`), the rejection test still asserts it fails
   like any unknown command.
4. Keep the existing context-mixin handler tests unchanged.

### Method

Mirror the existing fixture/setup style in the file; parametrize the removed-name list.

### Details

- `/workflow` was never a registered command, so its rejection test asserts the same
  unknown-command outcome as the other three — there is no CommandDef to route it.
- The `/audit` rejection test covers the mixin-backed command too; since `cmd_audit.py` is
  deleted in a sibling document, the rejection must be observable purely through dispatch.

## Compatibility considerations

Test-only change; production behavior is unaffected. The four names now fail like unknown
commands, which these tests lock in.

## Security considerations

`N/A`: test addition; no secret, permission, or data path is introduced.

## Rollback considerations

Revert the commit.

## Validation plan

- `pytest tests/agent/commands/test_agent_cmd_context.py` — the four rejection tests pass;
  deleted-handler tests are gone.
- `pytest` full suite — no missing-import or fixture failures.
- `ruff` / `mypy --no-namespace-packages tests/` — clean.

## Completion criteria

No test references the deleted `_cmd_diff`/`_cmd_system` behavior, and a rejection test for
each of `/diff`, `/system`, `/audit`, `/workflow` exists and passes.

## Out of scope

`cmd_context.py` (`REQ-002`), `command_defs_list.py` (`REQ-001`),
`cmd_audit.py`/`registry.py` (`REQ-003`), documentation (`REQ-007`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete deleted-handler tests; add four rejection tests in `tests/agent/commands/test_agent_cmd_context.py` (`REQ-002`, `REQ-006`) | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-002`, `REQ-006`
- **Source issue**: `issues/20261016-162117_cli001_remove-diff-system-audit-slash-commands.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261016-233542_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-071828
- **Related target files**: `tests/agent/commands/test_agent_cmd_context.py`
