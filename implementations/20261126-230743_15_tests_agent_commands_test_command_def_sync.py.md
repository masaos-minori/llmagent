## Goal

Extend the command-definition sync test with documentation-set and completion-set equality so the CI check
covers the whole command surface, not only definitions and handlers (REQ-007 — help, completion,
registry, and documentation list the same command set).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Confirmed in Step 3a: the file's docstring scope is definitions, handlers, and `/help` output; it has no
  documentation or completion comparison.
- This row keeps its own document because no other target row names it in its `Related Tests` cell, and
  the equality rule is a design decision of its own (Plan D7), so the companion rule does not apply.
- The documentation source is the Built-in Command Index table in
  `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md` (reference file, edited by document
  19); the completion source is `scripts/agent/repl.py` `SLASH_COMMANDS` via
  `completion_command_names()` (reference file).
- `/exit` is REPL-reserved and appears in the completion set through `reserved_repl_command_names()`, so
  the completion comparison must include the reserved set, not only `_COMMANDS`.

## Design decisions

- Compare sets, not counts (Plan D7): a count check would pass when one command is missing and another is
  extra.
- Read the documentation table as Markdown rows and take the first cell of each row; no new parser
  helper.

## Alternatives considered

- A separate CI script outside `tests/` — rejected: the Plan names this test file as the check, and the
  existing file already runs in CI.

## Implementation
### Target file
`tests/agent/commands/test_command_def_sync.py`
### Procedure
- Add a documentation-set equality test: parse the Built-in Command Index table rows in
  `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md` and assert the command names equal the
  names in `_COMMANDS`.
- Add a completion-set equality test: assert `completion_command_names()` equals the `_COMMANDS` names
  plus `reserved_repl_command_names()`.

### Method

- Read the doc with a relative path from the repository root; select lines matching
  `^\| \`/` and take the first cell.
- Import `completion_command_names` and `reserved_repl_command_names` from `agent.commands.command_defs`
  and `agent.repl`; keep the existing tests unchanged.

### Details

- The docstring's "Verifies" list gains the two new comparisons.
- The file stays under the test-file size convention; no split.

### Companion test files

- N/A: this row is itself a test row and has no companion.

## Compatibility considerations

- The check fails until document 19 corrects the documentation table, so run it after that row's change;
  the Plan sequences both in Phase 4.

## Security considerations

- N/A: no new disclosure surface.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/commands/test_command_def_sync.py`.
- Documentation gate — `uv run python tools/check_docs_consistency.py --domain agent` confirms the table
  the check reads is current.
- Sequence: format → lint → type → arch → security.

## Completion criteria

- Both equality tests pass, and the check fails on a deliberately renamed command name.

## Out of Scope

- The documentation corrections themselves (document 19).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | this row is the test itself |
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
- **Requirement ID**: `REQ-007` (CI check comparing the command sets)
- **Source issue**: `issues/20261119-145309_cliplc011_export-command-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-212234_cliplc011_export-command-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-230743
- **Related target files**: `tests/agent/commands/test_command_def_sync.py`
