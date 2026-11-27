## Goal

Show only the unknown command token in the dispatch-miss message instead of the full input line, so
arguments are not echoed back (REQ-006 — unknown-command output does not echo arguments).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Confirmed in Step 3a: `scripts/agent/repl_input_loop.py` line 290 writes
  `f"Unknown command: {line}  (type /help for commands)"` with the whole line.
- Overlap with `plans/20261126-211240_cliplc010_strict-turn-persistence.md` on this file is compatible:
  that Plan changes the persistence-error branch, this document changes the dispatch-miss display branch.
- `self._view.write_warning` and the `/help` hint stay; only the interpolated value changes.
- Step 3b correction (2026-11-27): the pinned assertion at line 313 already expects the token only
  (`startswith(f"Unknown command: {removed_name}")`) because the parametrized names carry no arguments,
  so it needs no change; the added case with an argument is the new coverage.

## Design decisions

- Echo the first whitespace-delimited token (Plan D6); the command name is what the user needs, the
  arguments may contain sensitive values.

## Alternatives considered

- Echoing the token plus a truncated argument — rejected: any argument echo keeps the disclosure path
  this requirement closes.

## Implementation
### Target file
`scripts/agent/repl_input_loop.py`
### Procedure
- In the `if not matched:` branch, interpolate the first token of the line rather than the line itself.

### Method
- `token = line.split(None, 1)[0]` before the write, then
  `f"Unknown command: {token}  (type /help for commands)"`.

### Details
- The branch is radon grade A; the added split keeps it within A.

### Companion test files
- `tests/agent/test_repl.py`
  - Procedure: update the pinned assertion at line 313 to expect the token only, and add a case with an
    argument that must not appear in the message.
  - Validation: `uv run pytest tests/agent/test_repl.py`.

## Compatibility considerations

- The pinned full-line echo assertion in `tests/agent/test_repl.py` changes under D6; that row is covered
  as the companion of this document.

## Security considerations

- This is the disclosure change: an argument that carries a secret or a path is no longer written to the
  terminal or to any log the view forwards.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/test_repl.py`.
- Sequence: format → lint → type → arch → security.

## Completion criteria

- An unknown command with arguments prints only the command name, and the `/help` hint is still present.

## Out of Scope

- Command definitions and the documentation equality check (documents 08 and 15).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | done |
| 2 | Add or update tests per Validation plan | Completed | — | — | companion `tests/agent/test_repl.py` done |
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
- **Requirement ID**: `REQ-006` (unknown-command output shows only the command token)
- **Source issue**: `issues/20261119-145309_cliplc011_export-command-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-212234_cliplc011_export-command-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-230743
- **Related target files**: `scripts/agent/repl_input_loop.py`, `tests/agent/test_repl.py`