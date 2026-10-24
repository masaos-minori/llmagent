## Goal
- Update the `masked_fields` bullet in `docs/23_agent/agent_08_03_configuration-tools-memory.md` to state the new default key names and what they name (`REQ-006`: document the default).

## Scope
- Edit the single bullet at line 32 only.

## Assumptions
- The bullet already states any-depth masking, the masked sinks, and that the interactive approval preview is the one deliberate unmasked exception (read 2026-10-24); that wording stays as written (Plan REQ-006, corrected at Step 3a).
- `docs/23_agent/agent_13_reference-api-generated.md` needs no edit (`mask_args` signature unchanged).
- The default key names are the documented default behavior, so naming them is allowed under the docs content policy; if `tools/check_docs_content_policy.py` flags it, reword without literal names but keep the meaning.
- The document is English only.

## Design decisions
- Append one sentence: the default masks the argument keys `content`, `old_text`, `new_text`, which name the `write_file`/`edit_file` (and GitHub file-write) tool arguments; an explicit `masked_fields` replaces the default.

## Alternatives considered
N/A: documentation-only row.

## Implementation
### Target file
`docs/23_agent/agent_08_03_configuration-tools-memory.md`

### Procedure
1. Add the sentence to the end of the line-32 bullet; do not alter its existing text.

### Method
- Edit in place; add no heading, table, or Related section.

### Details
- Rows `01` to `03` land first so the statement matches shipped defaults.

## Compatibility considerations
N/A: documentation-only.

## Security considerations
N/A: documentation-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py "docs/**/*.md"`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_consistency.py --domain agent`
- `uv run python tools/check_docs_japanese.py`

## Completion criteria
- The bullet names the new default keys and their meaning; all checkers report no findings.

## Out of Scope
- The approval-preview sentence, `agent_13`, `docs/00_index.md` (unless a gate demands it, per Plan UNK-01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend the `masked_fields` bullet at line 32 | Pending | — | — | |
| 2 | Run the docs checkers named in Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (document the default key names)
- **Source issue**: `issues/20261024-124138_tool005_default-masked-fields-names-match-no-real-tool-argument.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-221904_default-masked-fields-names-match-no-real-tool-argument.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-235437
- **Related target files**: `docs/23_agent/agent_08_03_configuration-tools-memory.md`
