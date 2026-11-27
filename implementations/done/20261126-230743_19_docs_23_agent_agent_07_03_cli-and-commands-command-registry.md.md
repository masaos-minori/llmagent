## Goal

Make the command index table the canonical specification: `/stats` documented as aggregate counts, bare
`/mcp` documented as the status alias, and `/compact` documented with its implementation owner
(REQ-007 — one canonical specification per command).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Confirmed in Step 3a: line 48 still says `/stats` is "not yet implemented, SHARED-003" while
  `scripts/agent/commands/cmd_config_stats.py:106` implements it as aggregate counts.
- The SHARED-003 citation in that row is removed because the command exists; the marker stays open in
  `docs/00_governance/governance_03_issue-and-uncertainty-management.md` for the retired memory model and
  is cited by other documents, so no governance inventory change is needed here.
- The table is the source the CI documentation-set equality check reads (document 15), so command names
  must not change — only the Purpose cells.

## Design decisions

- Keep the table shape and the command names; edit Purpose cells only (Plan D7), so the equality check
  compares names against `_COMMANDS` without a name-mapping exception.

## Alternatives considered

- Moving the specification into a new chapter — rejected: `docs/00_index.md` maps this task to the command
  registry document, and the CI check reads the existing table.

## Implementation
### Target file
`docs/23_agent/agent_07_03_cli-and-commands-command-registry.md`
### Procedure

- `/stats` row: state that it shows session statistics as aggregate counts, including Repository Context
  and Episodic Memory aggregate state; remove the "not yet implemented, SHARED-003" claim.
- `/mcp` row: state that bare `/mcp` is the status alias (`/mcp status`).
- `/compact` row: name the implementation owner, `_ContextMixin` in
  `scripts/agent/commands/cmd_context.py` (document 03).

### Method

- Three Purpose-cell edits in the Built-in Command Index table; the "Adding New Commands" paragraph is
  unchanged.

### Details

- Run `check_docs_consistency.py --domain agent` after the edit: the `/stats` claim is checked against
  `scripts/`.

### Companion test files

- N/A: documentation gate per rules/tool-gates.md.

## Compatibility considerations

- The `/memory` row's SHARED-003 citation is unaffected: that command is still registered in code.

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Documentation gates (`rules/tool-gates.md`): `check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_docs_consistency.py --domain agent`, `check_docs_japanese.py`.
- Cross-check — `uv run pytest tests/agent/commands/test_command_def_sync.py` (document 15) reads this
  table.

## Completion criteria

- The table lists the implemented command set with the corrected `/stats` scope, the bare `/mcp` alias,
  and the `/compact` owner.

## Out of Scope

- The `/set` reference in `docs/23_agent/agent_05_llm-and-streaming.md` (document 18).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | done |
| 2 | Add or update tests per Validation plan | N/A | — | — | documentation gate |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | documentation gates done |

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
- **Requirement ID**: `REQ-007` (canonical command specification)
- **Source issue**: `issues/20261119-145309_cliplc011_export-command-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-212234_cliplc011_export-command-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-230743
- **Related target files**: `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md`