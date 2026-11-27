## Goal

Align the canonical usage definition of `/session export` with the parser contract: the `ArgSpec` list
gains `--output` so help and completion show the same set of arguments the parser accepts (REQ-002,
REQ-007 — one canonical specification per command).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Confirmed in Step 3a: the export `SubcommandSpec` at lines 118-121 declares
  `(ArgSpec("markdown|md|json", default="markdown"), ArgSpec("file"))` and has no `--output` entry.
- `ArgSpec` (`scripts/agent/commands/command_defs.py`, reference file) has no flag field: `token` is the
  literal argument text, so the flag is declared as `ArgSpec("--output <file>")`. No change to the data
  class is needed.
- `tests/agent/commands/test_command_defs.py` is named by this row but is not a target row, so it is a
  validation reference only and gets no modification instructions here.

## Design decisions

- Declare the flag as a token string rather than extending `ArgSpec` (Plan D2 keeps the parser in
  `scripts/agent/commands/utils.py` and adds no new vocabulary).

## Alternatives considered

- Adding a `flag: bool` field to `ArgSpec` — rejected: `token` already carries the literal text including
  `--`, and the reference-file row for `command_defs.py` is `not affected`.

## Implementation
### Target file
`scripts/agent/commands/command_defs_list.py`
### Procedure
- Add `ArgSpec("--output <file>")` to the `/session export` `SubcommandSpec` argument tuple.
- Keep the help text as the canonical one-line purpose; the argument list is what must match the parser.

### Method
- Single tuple change; the `/compact` entry at lines 83-86 is unchanged because the handler name
  `_cmd_compact` is unchanged (Plan Assumptions).

### Details
- Help and completion are derived from `_COMMANDS`, so this row is what makes the displayed usage match
  the parser; no separate help text source is edited.

### Companion test files
- N/A: the test named by this row's Related Tests cell is not a row of the Plan's Implementation Target
  Files table, so it is a validation reference only (existing coverage of ArgSpec rendering).

## Compatibility considerations

- `/help` output for `/session export` gains the `--output` argument; existing format and positional
  filename usage is unchanged.

## Security considerations

- N/A: no new disclosure surface.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/commands/test_command_defs.py`.
- Sequence: format → lint → type → arch → security.

## Completion criteria

- The export definition lists `--output` and the CI documentation/completion equality check (document 15)
  passes against it.

## Out of Scope

- The parser implementation (document 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | done |
| 2 | Add or update tests per Validation plan | Completed | — | — | no companion row; existing coverage done |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | done |

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
- **Requirement ID**: `REQ-002` (export argument contract) and `REQ-007` (one canonical specification)
- **Source issue**: `issues/20261119-145309_cliplc011_export-command-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-212234_cliplc011_export-command-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-230743
- **Related target files**: `scripts/agent/commands/command_defs_list.py`