## Goal

Replace the ad-hoc export token loop with a formal argument parser that rejects unknown formats and
multiple output files as usage errors (REQ-002 — export arguments have one contract).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Confirmed in Step 3a: `_session_export` (lines 194-211) treats any non-format token as an output
  filename, last wins, and splits on whitespace so quoted filenames with spaces break.
- `scripts/agent/commands/utils.py` `parse_command_args` already supports `--flag value` pairs and is a
  reference file, not a target (Plan D2).
- `tests/agent/commands/test_command_arg_parsing.py` is the Plan's test row for this change and is the
  companion of this document.
- `_cmd_session` is radon grade C (14); the parser stays a separate helper so this function does not
  grow further.

## Design decisions

- Use `shlex.split` for tokens so quoted filenames survive, then `parse_command_args` for flags (Plan
  D2); no new parser module.
- The positional filename stays accepted for compatibility; only unknown formats and duplicate outputs
  are rejected.
- Step 3b correction (user decision, 2026-11-27): the format slot is positional, so the first
  positional token must be one of `markdown|md|json`; a filename without a format is a usage error. The
  positional filename stays accepted in the second slot. A repeated `--output` flag is also a usage
  error, since `parse_command_args` would otherwise overwrite the flag value silently.

## Alternatives considered

- A dedicated parser module — rejected by Plan D2 as unnecessary.

## Implementation
### Target file
`scripts/agent/commands/cmd_session.py`
### Procedure
- Add `_parse_export_args` (new) that returns `(fmt, outfile)` and raises
  `CommandValidationError` on an unknown format or a second output file.
- Call it from `_session_export` instead of the token loop.

### Method
- `tokens = shlex.split(args)`; format tokens are `markdown|md|json`; `--output` is the canonical flag;
  a second output token raises a usage error.

### Details
- UTF-8 and newlines in the written file are unaffected: `write_export` keeps its behavior.

### Companion test files
- `tests/agent/commands/test_command_arg_parsing.py`
  - Procedure: add unknown-format, duplicate-output, quoted-filename, and `--output` cases.
  - Validation: `uv run pytest tests/agent/commands/test_command_arg_parsing.py`.

## Compatibility considerations

- Behavior that "worked by accident" (an unknown token as a filename) now fails as a usage error; this
  is the intended contract change.
- Step 3b correction (user decision, 2026-11-27): `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`
  claims the arguments may appear in either order and that any non-format argument is taken as the
  output file. That claim and the usage cell are updated to the parser contract even though the file is
  not a row of the Plan's Implementation Target Files table.

## Security considerations

- N/A: no new disclosure surface.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/commands/test_command_arg_parsing.py`.
- Sequence: format → lint → type → arch → security.

## Completion criteria

- Unknown formats and duplicate outputs raise usage errors, and a quoted filename with spaces is
  preserved.

## Out of Scope

- The canonical `ArgSpec` definition in `scripts/agent/commands/command_defs_list.py` (document 08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | done |
| 2 | Add or update tests per Validation plan | Completed | — | — | companion `tests/agent/commands/test_command_arg_parsing.py` done |
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
- **Requirement ID**: `REQ-002` (export uses a formal argument parser)
- **Source issue**: `issues/20261119-145309_cliplc011_export-command-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-212234_cliplc011_export-command-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-230743
- **Related target files**: `scripts/agent/commands/cmd_session.py`, `tests/agent/commands/test_command_arg_parsing.py`