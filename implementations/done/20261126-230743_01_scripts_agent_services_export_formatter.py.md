## Goal

Make exported Markdown valid for arbitrary tool text: the code fence is longer than the longest
backtick run in the content, and tool call ids and structural metadata are escaped (REQ-001 — export
valid for arbitrary content).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Line 40 emits a fixed triple-backtick fence for tool messages; confirmed in Step 3a.
- `render_history_md` is radon grade B (8); the fence rule must not push it above B, so the length
  calculation stays a single expression or a small helper.
- Overlap with `plans/20261126-223853_cliplc014_cli-docs-consolidation.md` on the generated reference
  domain is compatible: both regenerate the table; this Plan's row is the docstring change itself.

## Design decisions

- Fence length = longest backtick run in the content plus one, minimum three (Plan D1).
- Escaping applies to `tool_call_id` and structural metadata only, not to the tool content itself, so
  the content stays readable.

## Alternatives considered

- Indented code blocks — rejected by Plan D1 (loses language semantics and the Issue requires
  fence-based export).

## Implementation
### Target file
`scripts/agent/services/export_formatter.py`
### Procedure
- Compute the fence length from the content's longest backtick run before emitting the tool block.
- Escape tool call ids and structural metadata so they cannot form a Markdown heading.

### Method
- Add `fence_for` (new) returning `max(3, longest_backtick_run(text) + 1)` and use it in the tool
  branch; escape `tc_id` through a small `escape_md` (new) helper that neutralises leading `#` and
  backtick sequences.

### Details
- The docstring's first line changes (the generated reference table reflects it, document 20).

### Companion test files
- `tests/test_export_formatter.py`
  - Procedure: write the nested-fence test first, then fence-length, injection, Unicode, and newline
    variants.
  - Validation: `uv run pytest tests/test_export_formatter.py`.
- N/A for the other test row named by this Plan: the pinned fence assertions in
  tests/agent/services/test_commands_utils.py are not named by this row's Related Tests cell, so that row
  keeps its own procedure document.

## Compatibility considerations

- Pinned fence assertions in tests/agent/services/test_commands_utils.py change under D1; that row is not
  named by this row's Related Tests cell, so it keeps its own procedure document.

## Security considerations

- Markdown injection through tool content is the disclosure/interpretation risk this change closes.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/test_export_formatter.py` (companion); the pinned assertions in
  tests/agent/services/test_commands_utils.py are validated by that row's own document.
- Sequence: format → lint → type → arch → security.

## Completion criteria

- Content containing a triple-backtick run still produces a closed fence, and an id that begins with a
  Markdown heading marker is escaped.

## Out of Scope

- The export argument parser (document 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | done |
| 2 | Add or update tests per Validation plan | Completed | — | — | companion `tests/test_export_formatter.py` done |
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
- **Related target files**: `scripts/agent/services/export_formatter.py`, `tests/test_export_formatter.py`