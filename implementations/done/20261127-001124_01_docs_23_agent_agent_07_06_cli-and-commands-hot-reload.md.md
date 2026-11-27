## Goal

Replace the unregistered `/config show` usage with the registered `/config` form in the Pending Restart Display
section (REQ-001; AC-1).

## Scope
**Release unit**: N/A: no release unit

## Assumptions

- Confirmed in Step 3a: `/config show` appears at `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md:73`,
  and the registered surface defines `/config` with no subcommands (`scripts/agent/commands/command_defs_list.py:40-45`).
- `/config show` is the only occurrence of that usage in `docs/`; no other document needs the same correction.
- The pending-restart list itself is behavior owned by the closed hot-reload issues; only the usage name is wrong.

## Design decisions

- The corrected line names the registered command form only; no subcommand is invented, since the registry has none.

## Alternatives considered

- Documenting `/config show` as a planned subcommand — rejected: REQ-001 requires every documented usage to exist
  in the registered surface, and no test proves a `show` subcommand.

## Implementation
### Target file
`docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md`
### Procedure

- In the bullet at `:73`, replace `/config show` with `/config`.

### Method

- Text-only substitution of the usage name; the sentence's claim about the pending-restart list is unchanged.

### Details

- Keep the surrounding wording about pending startup-only fields and the `Pending restart (not applied to the running
  process)` heading as it is.

## Compatibility considerations

- No code or test reads this line as a contract; the docs gates and the command-contract test are the only checks
  affected.
- `tests/tools/test_check_command_contracts.py` is a validation reference, not a modification target: it is not a row
  of the Plan's target table.

## Security considerations

- N/A: documentation-only change.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Docs gate — `uv run python tools/check_docs_consistency.py --domain agent`: no finding.
- Contract — manual comparison of the corrected usage against `scripts/agent/commands/command_defs_list.py`, because
  the checker's command-contract scan covers only `agent_07_07` to `agent_07_10` (UNK-01), so this file is not caught
  automatically.
- Unit — `uv run pytest tests/tools/test_check_command_contracts.py`.
- Sequence: format → lint → type → arch → security → test → coverage (`rules/toolchain.md`).

## Completion criteria

- The file contains no usage absent from the registered command surface, the docs gate reports no finding, and the
  manual contract comparison records the registered `/config` form.

## Out of Scope

- Extending `tools/check_docs_consistency.py`'s chapter set (UNK-01, maintainer decision).
- Any behavior change to the pending-restart display.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the usage name per Procedure/Method/Details | Completed | 20261127-120618 | 20261127-120618 | Plan Phase 1 Plan Phase 1 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-120618 | 20261127-120618 | Plan Phase 7 Plan Phase 7 |

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
- **Requirement ID**: `REQ-001` (documented usage must exist in the registered command surface)
- **Source issue**: `issues/20261119-145312_cliplc014_cli-docs-consolidation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-223853_cliplc014_cli-docs-consolidation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-001124
- **Related target files**: `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md`