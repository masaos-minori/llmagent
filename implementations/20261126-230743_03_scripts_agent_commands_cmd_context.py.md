## Goal

Make `_ContextMixin` the single implementation owner of `/compact` (REQ-003 — one implementation owner
per command).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Confirmed in Step 3a: the handler uses only `hist_mgr` and `conv.history`
  (`scripts/agent/commands/cmd_rag_export.py` lines 32-58), so it has no RAG-export dependency and
  belongs with the context mixin commands.
- The handler name `_cmd_compact` is unchanged, so `scripts/agent/commands/command_defs_list.py` needs
  no rename (Plan Assumptions).
- `cmd_rag_export.py` becomes empty after the move and is removed by document 04; the registry wiring is
  updated by document 05.

## Design decisions

- Move the handler as-is (Plan D3); no behavior change, only ownership.

## Alternatives considered

- Keeping the handler in the RAG export mixin — rejected by Plan D3 (the user decision names
  `cmd_context.py` as the owner).

## Implementation
### Target file
`scripts/agent/commands/cmd_context.py`
### Procedure
- Add `_cmd_compact` (new in this file) with the body copied from `_RagExportMixin`.
- Update the module docstring's command list to include `_cmd_compact`.

### Method
- Copy the handler unchanged; add the `HistoryCompressionError` import that the body needs.

### Details
- `cmd_context.py` is below the 24576 B module-size gate, so no split is required.

### Companion test files
- N/A: the test named by this row's Related Tests cell is not a row of the Plan's Implementation Target
  Files table, so it is a validation reference only and gets no modification instructions here; the Plan's
  Validation plan runs it unchanged.

## Compatibility considerations

- Dispatch resolves the handler through the registry class list, so the handler name and signature stay
  the same.

## Security considerations

- N/A: no new disclosure surface.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/commands/test_agent_cmd_context.py`.
- Sequence: format → lint → type → arch → security.

## Completion criteria

- `/compact` dispatches to `_ContextMixin` and the existing compression behavior is unchanged.

## Out of Scope

- Removal of `scripts/agent/commands/cmd_rag_export.py` (document 04) and the registry wiring (document
  05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | no companion row; existing coverage |
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
- **Requirement ID**: `REQ-003` (one implementation owner per command)
- **Source issue**: `issues/20261119-145309_cliplc011_export-command-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-212234_cliplc011_export-command-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-230743
- **Related target files**: `scripts/agent/commands/cmd_context.py`
