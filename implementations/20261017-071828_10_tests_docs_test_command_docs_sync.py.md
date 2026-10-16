## Goal

Remove the assertion that `/audit` is a registered command from
`tests/docs/test_command_docs_sync.py` (`REQ-007`, command-surface reduction).

## Scope

In scope: remove the `/audit` registration assertion from `tests/docs/test_command_docs_sync.py`.
Out of scope: the command/handler/mixin deletions (`REQ-001`–`REQ-003`), the
`/diff`/`/system` handler deletion (`REQ-002`), the `GV-017` pattern additions
(`REQ-005`), and the other docs-consistency test change (`test_check_docs_consistency_checks.py`,
`REQ-007`, separate document).

## Assumptions

- The `/audit` assertion is the only place in the file that pins a now-unregistered name.

## Design decisions

- **Delete only the `/audit` assertion.** Leave every other assertion in the file intact;
  do not rewrite the surrounding test.

## Alternatives considered

`N/A`: the goal mandates removal with no shim or forwarding path; leaving the assertion
would fail once `/audit` is unregistered.

## Implementation

### Target file

`tests/docs/test_command_docs_sync.py`

### Procedure

1. Confirm the `/audit` assertion with `rg`: docstring mention (L110) and
   `assert "/audit" in registered` (L112).
2. Confirm nothing else in the file references `/audit` as a registered command.
3. Remove the `/audit` assertion (and its docstring line if it exists solely for it).

### Method

Delete the two lines/blocks as whole lines, preserving surrounding syntax.

### Details

- If step 2 finds other `/audit` references, evaluate each individually rather than
  removing them wholesale.

## Compatibility considerations

Test-only change; production behavior is unaffected.

## Security considerations

`N/A`: test change; no secret, permission, or data path is introduced.

## Rollback considerations

Revert the commit.

## Validation plan

- `pytest tests/docs/test_command_docs_sync.py` — passes without the `/audit` assertion.
- `pytest` full suite — no missing-import or fixture failures.
- `ruff` / `mypy --no-namespace-packages tests/` — clean.

## Completion criteria

No assertion in `test_command_docs_sync.py` pins `/audit` as a registered command, and the
rest of the file is unchanged.

## Out of scope

`command_defs_list.py` (`REQ-001`), `cmd_context.py` (`REQ-002`), `cmd_audit.py`/`registry.py`\n(`REQ-003`), `tools/check_compat_shims.py` (`REQ-005`),
`test_check_docs_consistency_checks.py` (`REQ-007`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the `/audit` registration assertion from `tests/docs/test_command_docs_sync.py` (`REQ-007`) | Pending | — | — | |
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
- **Requirement ID**: `REQ-007`
- **Source issue**: `issues/20261016-162117_cli001_remove-diff-system-audit-slash-commands.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261016-233542_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-071828
- **Related target files**: `tests/docs/test_command_docs_sync.py`
