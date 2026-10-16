## Goal

Delete `tests/agent/commands/test_cmd_audit.py`, which tests only the deleted
`_AuditMixin._cmd_audit()` handler (`REQ-003`, command-surface reduction).

## Scope

In scope: delete `tests/agent/commands/test_cmd_audit.py`. Out of scope: deleting
`cmd_audit.py` itself (`REQ-003`, separate document), the `CommandDef` entry
(`command_defs_list.py`, `REQ-001`), the `/diff`/`/system` handlers (`cmd_context.py`,
`REQ-002`), the `registry.py` import/composition removal (`REQ-003`, separate document),
and documentation (`REQ-007`).

## Assumptions

- The file contains only tests of `_AuditMixin._cmd_audit()`, which is deleted with
  `cmd_audit.py`.
- No other file imports from `test_cmd_audit.py`.

## Design decisions

- **Whole-file deletion.** The file's sole purpose is testing the removed handler; deleting
  the file is one coherent removal.
- **Verify before deleting the whole file.** Confirm the file holds only the audit tests;
  if other classes exist, delete only the affected class instead.

## Alternatives considered

`N/A`: the goal mandates removal with no shim or forwarding path; keeping an empty test
file would contradict it.

## Implementation

### Target file

`tests/agent/commands/test_cmd_audit.py`

### Procedure

1. Confirm the file contains only tests of `_AuditMixin._cmd_audit()` via `rg`/Read.
2. Confirm nothing outside the file imports from `test_cmd_audit` (`rg test_cmd_audit tests/`).
3. Delete the file (`git rm` / equivalent).

### Method

Delete the file from the working tree and stage the removal with git.

### Details

- This must land together with the `cmd_audit.py` deletion (separate document) so no test
  references a deleted handler between the two changes.
- If step 1 finds other test classes, delete only the audit tests rather than the whole
  file.

## Compatibility considerations

Test-only change; production behavior is unaffected. The `/audit` command now fails like an
unknown command.

## Security considerations

`N/A`: test deletion; no secret, permission, or data path is touched.

## Rollback considerations

`git restore --staged <file> && git checkout -- <file>` (or revert the commit) to recover
the file.

## Validation plan

- `pytest` full suite — no missing-import failures from other test files.
- `lint-imports` — no dangling `from agent.commands.cmd_audit import`.
- `ruff` / `mypy --no-namespace-packages tests/` — clean.

## Completion criteria

`tests/agent/commands/test_cmd_audit.py` no longer exists, no other file references it, and
the full suite passes.

## Out of scope

`cmd_audit.py` (`REQ-003`), `command_defs_list.py` (`REQ-001`), `cmd_context.py`
(`REQ-002`), `registry.py` (`REQ-003`), documentation (`REQ-007`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete `tests/agent/commands/test_cmd_audit.py` (`REQ-003`) | Pending | — | — | |
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
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261016-162117_cli001_remove-diff-system-audit-slash-commands.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261016-233542_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-071828
- **Related target files**: `tests/agent/commands/test_cmd_audit.py`
