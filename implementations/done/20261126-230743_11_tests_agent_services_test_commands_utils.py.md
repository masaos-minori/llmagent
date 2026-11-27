## Goal

Add adaptive-fence and metadata-escaping coverage on the commands-utils test surface, where the pinned
fence assertion is the one that D1 can change (REQ-001 — export remains valid for arbitrary tool text).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Confirmed in Step 3a: this file imports `render_history_md`, `render_export`, and `write_export` from
  `agent.services.export_formatter`, so it exercises the same formatter as document 01.
- The only fence assertion is line 49 (`assert "```" in result`) for content with no backtick run; under
  D1 it still passes, so this row's work is added coverage, not a repaired assertion. The Plan's
  "assertions change under D1" is recorded as the reason for the row; the change is the new cases.
- This row keeps its own document because no other target row names it in its `Related Tests` cell, so the
  companion rule does not apply.
- The file's module docstring header still names `tests/test_commands_utils.py` and `commands/utils.py`;
  that stale header is not part of this row's scope.

## Design decisions

- Assert the fence length relative to the content's longest backtick run rather than a fixed triple
  backtick, so the test expresses D1's rule instead of one instance of it.

## Alternatives considered

- Leaving the file unchanged — rejected: the Plan records it as the pinned-assertion surface for D1, and the
  coverage would then exist only in `tests/test_export_formatter.py`.

## Implementation
### Target file
`tests/agent/services/test_commands_utils.py`
### Procedure

- Add a tool-message case whose content contains a triple-backtick run and assert the emitted fence is
  longer than that run and closes the block.
- Add a tool-call-id case that begins with a Markdown heading marker and assert the heading is escaped.

### Method

- Keep the existing assertions, including line 49, unchanged; add two cases in the
  `TestRenderHistoryMd` class.

### Details

- No import changes; the file stays under the test-file size convention.

### Companion test files

- N/A: this row is itself a test row and has no companion.

## Compatibility considerations

- The existing pinned assertion remains valid; the new cases are additive.

## Security considerations

- N/A: no new disclosure surface.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/services/test_commands_utils.py`.
- Sequence: format → lint → type → arch → security.

## Completion criteria

- Both new cases pass, and the existing fence assertion is unchanged.

## Out of Scope

- The formatter implementation (document 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | done |
| 2 | Add or update tests per Validation plan | Completed | — | — | this row is the test itself done |
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
- **Requirement ID**: `REQ-001` (exported Markdown remains valid for arbitrary tool text)
- **Source issue**: `issues/20261119-145309_cliplc011_export-command-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-212234_cliplc011_export-command-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-230743
- **Related target files**: `tests/agent/services/test_commands_utils.py`