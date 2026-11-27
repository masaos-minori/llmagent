## Goal

Make bare `/mcp` the formal status-alias contract by removing the redundant usage line it writes
(REQ-005 — bare `/mcp` is the status alias).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Confirmed in Step 3a: `_cmd_mcp` (`scripts/agent/commands/cmd_mcp.py` lines 410-416) accepts `""` as
  the status alias and, for the bare form only, writes `Usage: /mcp [status|tools]` plus an empty line
  before delegating to `_cmd_mcp_status`.
- The alias behavior itself is the user decision recorded as D5; this document removes the display, not
  the alias.
- Overlap with `plans/20261126-210258_cliplc009_redaction-stderr-diagnostics.md` on this file is
  compatible: that Plan's document masks endpoint URLs in the status display, this document changes only
  the bare-`/mcp` dispatch branch.

## Design decisions

- Keep the alias, drop the usage line (Plan D5): the alias is the contract, so a usage hint for the bare
  form is redundant.

## Alternatives considered

- Keeping the usage line for the bare form — rejected by Plan D5 (the user decision).

## Implementation
### Target file
`scripts/agent/commands/cmd_mcp.py`
### Procedure
- Remove the `if not sub:` block inside the status branch so `sub in ("status", "")` calls
  `_cmd_mcp_status()` directly.

### Method
- No signature or control-flow change beyond deleting the two `self._out.write(...)` calls; the `tools`
  branch and the `UnknownSubcommandError` raise stay as they are.

### Details
- The module stays below the 24576 B size gate; no split is required.

### Companion test files
- `tests/agent/commands/test_cmd_mcp.py`
  - Procedure: add the bare-`/mcp` alias contract test — bare input renders the status display and writes
    no usage line; keep the existing `/mcp status` and `/mcp tools` cases.
  - Validation: `uv run pytest tests/agent/commands/test_cmd_mcp.py`.

## Compatibility considerations

- Users who relied on the usage line for bare `/mcp` lose the hint; the output is otherwise unchanged.

## Security considerations

- N/A: no new disclosure surface.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/commands/test_cmd_mcp.py`.
- Sequence: format → lint → type → arch → security.

## Completion criteria

- Bare `/mcp` produces the status display with no usage line, and the unknown-subcommand raise is
  unchanged.

## Out of Scope

- URL masking in the status display (`plans/20261126-210258_cliplc009_redaction-stderr-diagnostics.md`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | done |
| 2 | Add or update tests per Validation plan | Completed | — | — | companion `tests/agent/commands/test_cmd_mcp.py` done |
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
- **Requirement ID**: `REQ-005` (bare `/mcp` is the formal status-alias contract)
- **Source issue**: `issues/20261119-145309_cliplc011_export-command-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-212234_cliplc011_export-command-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-230743
- **Related target files**: `scripts/agent/commands/cmd_mcp.py`, `tests/agent/commands/test_cmd_mcp.py`