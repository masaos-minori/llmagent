## Goal

Remove the module that becomes empty after the `/compact` handler move (REQ-003 — single-owner
normalization).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Confirmed in Step 3a: `cmd_rag_export.py` contains only `_RagExportMixin._cmd_compact` (lines 19-58),
  so after document 03 the file holds nothing.
- Consumer scan found exactly two consumers: the registry wiring (document 05) and one test import
  (companion).

## Design decisions

- Delete the file rather than leaving an empty mixin (Plan D3).

## Alternatives considered

- Keeping the mixin as an alias — rejected: it would preserve a second owner for one command.

## Implementation
### Target file
`scripts/agent/commands/cmd_rag_export.py` (removed by this procedure)
### Procedure
- Delete the module once the handler exists in `scripts/agent/commands/cmd_context.py`.

### Method
- `git rm scripts/agent/commands/cmd_rag_export.py`; no replacement file is created.

### Details
- The module-size gate and the generated reference table both drop the row after regeneration
  (document 20).

### Companion test files
- `tests/agent/test_history_compression_consistency.py`
  - Procedure: change the `_RagExportMixin` import at line 21 and the instantiation at line 382 to
    `_ContextMixin`.
  - Validation: `uv run pytest tests/agent/test_history_compression_consistency.py`.

## Compatibility considerations

- Any import of `_RagExportMixin` outside the scanned consumers would break; the scan found none.

## Security considerations

- N/A: no new disclosure surface.

## Rollback considerations

- N/A: restore the file from the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/test_history_compression_consistency.py`.
- Sequence: lint → type → arch (`uv run lint-imports` confirms no dangling import).

## Completion criteria

- The file no longer exists, no module imports it, and the compression tests pass.

## Out of Scope

- The handler move itself (document 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | file removal |
| 2 | Add or update tests per Validation plan | Pending | — | — | companion `tests/agent/test_history_compression_consistency.py` |
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
- **Related target files**: `scripts/agent/commands/cmd_rag_export.py`, `tests/agent/test_history_compression_consistency.py`
