## Goal

Replace the `/audit` fixture command with a currently-registered command in
`tests/tools/test_check_docs_consistency_checks.py` so the consistency-checker fixture
still exercises a real command (`REQ-007`, command-surface reduction).

## Scope

In scope: replace the `/audit` fixture command (L112) and update the assertions at L115-116
that reference `'/audit'` in `tests/tools/test_check_docs_consistency_checks.py`. Out of
scope: the command/handler/mixin deletions (`REQ-001`–`REQ-003`), the
`/diff`/`/system` handler deletion (`REQ-002`), the `GV-017` pattern additions
(`REQ-005`), and the other docs test change (`test_command_docs_sync.py`, `REQ-007`,
separate document).

## Assumptions

- The fixture builds a command repo from a list of names; swapping `/audit` for a live
  command keeps the fixture valid.

## Design decisions

- **Swap to a live command.** Replace `/audit` with a command that is still registered after
  this plan (e.g. `/help` or another surviving slash command), so the fixture exercises a
  real command.
- **Update the matching assertions** at L115-116 to reference the new command name.

## Alternatives considered

`N/A`: leaving `/audit` would fail once it is unregistered; the fixture must reference a
live command.

## Implementation

### Target file

`tests/tools/test_check_docs_consistency_checks.py`

### Procedure

1. Confirm the `/audit` fixture command (L112: `repo = _command_repo(tmp_path, ["/help",
   "/audit"])`) and the assertions at L115-116 referencing `'/audit'`.
2. Replace `/audit` with a currently-registered command (keep `/help` in the list).
3. Update the L115-116 assertions to reference the new command name.

### Method

Edit the fixture line and the two assertions as whole lines, preserving syntax.

### Details

- Choose a command that survives this plan (verify against `command_defs_list.py`); do not
  introduce a brand-new command.

## Compatibility considerations

Test-only change; production behavior is unaffected.

## Security considerations

`N/A`: test change; no secret, permission, or data path is introduced.

## Rollback considerations

Revert the commit.

## Validation plan

- `pytest tests/tools/test_check_docs_consistency_checks.py` — passes with the swapped
  command.
- `pytest` full suite — no missing-import or fixture failures.
- `ruff` / `mypy --no-namespace-packages tests/` — clean.

## Completion criteria

`test_check_docs_consistency_checks.py` no longer references `/audit`; the fixture and its
assertions use a currently-registered command, and all pass.

## Out of scope

`command_defs_list.py` (`REQ-001`), `cmd_context.py` (`REQ-002`), `cmd_audit.py`/`registry.py`\n(`REQ-003`), `tools/check_compat_shims.py` (`REQ-005`),
`test_command_docs_sync.py` (`REQ-007`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the `/audit` fixture command in `tests/tools/test_check_docs_consistency_checks.py` (`REQ-007`) | Pending | — | — | |
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
- **Related target files**: `tests/tools/test_check_docs_consistency_checks.py`
